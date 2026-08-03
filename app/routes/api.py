from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request

from app import db, limiter
from app.models.buyer_criteria import BuyerCriteria
from app.models.conversation import Conversation
from app.models.faq_item import FAQ_CATEGORIES, FaqItem
from app.models.featured_location import FeaturedLocation
from app.models.file import UploadedFile
from app.models.funding_details import FundingDetails
from app.models.lead import Lead
from app.models.message import Message
from app.models.project import Project
from app.models.property_details import PROPERTY_TYPES_PRIMARY, PropertyDetails
from app.models.public_statistic import PublicStatistic
from app.services import file_security, validators
from app.services.chat_engine import (
    FAQ_MENU_BUTTONS,
    budget_prompt_for_flow,
    extended_property_types,
    get_step,
    progress_for_step,
    resolve_flow_from_intent,
    timeline_options_for_flow,
)
from app.services.notifications import send_contact_verification_code

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _step_response(session_id: str, step_name: str, state: dict | None = None, **extra):
    step = get_step(step_name)
    payload = {
        "session_id": session_id,
        "step": step_name,
        "prompt": extra.pop("prompt", step.get("prompt")),
        "input_type": extra.pop("input_type", step.get("input_type")),
        "options": extra.pop("options", step.get("options", [])),
        "progress": progress_for_step(step_name),
    }
    if state is not None:
        payload["state_preview"] = _safe_state_preview(state)
    payload.update(extra)
    return payload


def _get_or_create_conversation(session_id: str) -> Conversation:
    convo = Conversation.query.filter_by(session_id=session_id).first()
    if not convo:
        convo = Conversation(session_id=session_id, current_step="welcome", state_data={})
        db.session.add(convo)
        db.session.commit()
    return convo


def _log_message(convo: Conversation, sender: str, content: str, message_type="text", validation_status=None):
    msg = Message(
        conversation_id=convo.id,
        sender=sender,
        content=content or "",
        message_type=message_type,
        validation_status=validation_status,
    )
    db.session.add(msg)
    db.session.commit()
    return msg


def _validation_error(convo, message, suggestion=None):
    _log_message(convo, "bot", message, "system", validation_status="invalid")
    payload = {"error": message, "step": convo.current_step}
    if suggestion:
        payload["suggestion"] = suggestion
    return jsonify(payload), 422


# ---------------------------------------------------------------------------
# Public overview, projects and locations
# ---------------------------------------------------------------------------

def _public_summary():
    stats = (
        PublicStatistic.query.filter_by(is_public=True)
        .order_by(PublicStatistic.display_order)
        .all()
    )
    return [item.to_public_dict() for item in stats]


def _public_projects(limit=12):
    projects = (
        Project.query.filter(Project.status.in_([
            "Published", "Recently Purchased", "Recently Sold", "Available",
            "Under Contract", "Renovation in Progress", "Completed",
        ]))
        .order_by(Project.featured.desc(), Project.created_at.desc())
        .limit(limit)
        .all()
    )
    return [project.to_public_dict() for project in projects]


def _public_locations(limit=20):
    locations = (
        FeaturedLocation.query.filter_by(is_active=True, is_featured=True)
        .order_by(FeaturedLocation.display_order, FeaturedLocation.city)
        .limit(limit)
        .all()
    )
    return [location.to_public_dict() for location in locations]


@api_bp.route("/public/overview", methods=["GET"])
@limiter.limit("60 per minute")
def public_overview():
    return jsonify({
        "statistics": _public_summary(),
        "locations": _public_locations(6),
        "projects": _public_projects(4),
    })


@api_bp.route("/public/projects", methods=["GET"])
@limiter.limit("60 per minute")
def public_projects():
    return jsonify({"projects": _public_projects(24)})


@api_bp.route("/public/locations", methods=["GET"])
@limiter.limit("60 per minute")
def public_locations():
    return jsonify({"locations": _public_locations(30)})


@api_bp.route("/location/zip/<zip_code>", methods=["GET"])
@limiter.limit("30 per minute")
def lookup_zip_location(zip_code):
    result = validators.lookup_us_zip(zip_code)
    if not result.valid:
        return jsonify({"error": result.message}), 422
    return jsonify({
        "zip": result.value.get("zip"),
        "state": result.value.get("state"),
        "state_name": result.value.get("state_name"),
        "places": result.value.get("places", []),
        "validation_status": result.value.get("validation_status"),
        "message": result.message,
    })


# ---------------------------------------------------------------------------
# FAQ flow
# ---------------------------------------------------------------------------

def _faq_question_batch(category: str, viewed_ids: list, batch_size=5):
    items = (
        FaqItem.query.filter_by(category=category, is_active=True)
        .order_by(FaqItem.display_order)
        .all()
    )
    unviewed = [item for item in items if item.id not in viewed_ids]
    return unviewed[:batch_size]


def _faq_batch_response(session_id, state, first_time=False):
    category = state.get("faq_category")
    viewed_ids = state.get("faq_viewed", [])
    seller_entry = bool(state.get("seller_entry"))
    buyer_entry = bool(state.get("buyer_entry"))
    guided_entry = seller_entry or buyer_entry
    batch_size = 50 if guided_entry else 5
    batch = _faq_question_batch(category, viewed_ids, batch_size=batch_size)
    options = [item.question for item in batch]

    if seller_entry:
        entry_label = "Seller"
        enquiry_button = "Start Seller Enquiry"
        subject = "selling"
    elif buyer_entry:
        entry_label = "Buyer"
        enquiry_button = "Start Buyer Enquiry"
        subject = "buying"
    else:
        entry_label = None
        enquiry_button = None
        subject = None

    if batch:
        if guided_entry:
            prompt = (
                f"Select a {subject} question to view its answer."
                if first_time else f"Choose another unanswered {subject} question."
            )
            options += [enquiry_button, "Return to Main Menu"]
        else:
            prompt = (
                f"Choose a question about {category}."
                if first_time else "Here are more unanswered questions in this section."
            )
            options += ["Ask My Own Question", "Return to FAQ Menu", "Return to Main Menu"]
    else:
        if guided_entry:
            prompt = f"You have viewed all available {subject} questions. Would you like to submit your details?"
            options = [enquiry_button, "Return to Main Menu"]
        else:
            prompt = "You have viewed all available questions in this section."
            options = [
                "Ask My Own Question", "Speak With the Team", "Request a Callback",
                "Send an Email", "Return to FAQ Menu", "Return to Main Menu", "Finish Chat",
            ]
    return {
        "session_id": session_id,
        "step": "faq_questions",
        "prompt": prompt,
        "input_type": "buttons",
        "options": options,
        "progress": None,
    }


def _return_to_menu(convo, session_id, menu="welcome"):
    convo.current_step = menu
    db.session.commit()
    return jsonify(_step_response(session_id, menu, convo.state_data or {}))


def _contact_from_faq(convo, state, session_id, intent):
    state["intent"] = intent
    state["flow_type"] = "general_enquiry"
    convo.flow_type = "general_enquiry"
    convo.state_data = state
    convo.current_step = "collect_name"
    db.session.commit()
    return jsonify(_step_response(
        session_id, "collect_name", state,
        prompt="Please provide your full name so the team can follow up.",
    ))


def _start_seller_enquiry_from_faq(convo, state, session_id):
    state.update({
        "intent": "Sell a Property",
        "flow_type": "sell",
        "journey_stage": "selling",
        "seller_entry": False,
        "buyer_entry": False,
    })
    convo.flow_type = "sell"
    convo.state_data = state
    convo.current_step = "collect_name"
    db.session.commit()
    return jsonify(_step_response(
        session_id, "collect_name", state,
        prompt="Please provide your full name to start the seller enquiry.",
    ))


def _start_buyer_enquiry_from_faq(convo, state, session_id):
    state.update({
        "intent": "Buy a Property",
        "flow_type": "buy",
        "journey_stage": "buying",
        "seller_entry": False,
        "buyer_entry": False,
    })
    convo.flow_type = "buy"
    convo.state_data = state
    convo.current_step = "collect_name"
    db.session.commit()
    return jsonify(_step_response(
        session_id, "collect_name", state,
        prompt="Please provide your full name to start the buyer enquiry.",
    ))


def _handle_faq_step(convo, current_step, user_input, state, session_id):
    if current_step == "faq_menu":
        if user_input == "Return to Main Menu":
            return _return_to_menu(convo, session_id)
        if user_input in FAQ_CATEGORIES:
            state.update({"faq_category": user_input, "faq_viewed": [], "flow_type": "faq", "seller_entry": False, "buyer_entry": False})
            convo.state_data = state
            convo.current_step = "faq_questions"
            db.session.commit()
            return jsonify(_faq_batch_response(session_id, state, first_time=True))
        return jsonify(_step_response(session_id, "faq_menu", state))

    if current_step == "faq_questions":
        category = state.get("faq_category")
        items = FaqItem.query.filter_by(category=category, is_active=True).all()
        matched = next((item for item in items if item.question == user_input), None)
        if matched:
            viewed = list(dict.fromkeys(state.get("faq_viewed", []) + [matched.id]))
            state["faq_viewed"] = viewed
            convo.state_data = state
            convo.current_step = "faq_after_answer"
            db.session.commit()
            seller_entry = bool(state.get("seller_entry"))
            buyer_entry = bool(state.get("buyer_entry"))
            guided_entry = seller_entry or buyer_entry
            if seller_entry:
                guided_options = ["Yes, Show Remaining Questions", "No, Start Seller Enquiry"]
            elif buyer_entry:
                guided_options = ["Yes, Show Remaining Questions", "No, Start Buyer Enquiry"]
            else:
                guided_options = ["Yes, Show More Questions", "No, Continue Another Way"]
            return jsonify({
                "session_id": session_id,
                "step": "faq_after_answer",
                "prompt": matched.answer + (
                    "\n\nAre you interested in moving forward?"
                    if guided_entry else
                    "\n\nWould you like to view more questions in this section?"
                ),
                "input_type": "buttons",
                "options": guided_options,
                "progress": None,
            })
        if user_input == "Start Seller Enquiry" and state.get("seller_entry"):
            return _start_seller_enquiry_from_faq(convo, state, session_id)
        if user_input == "Start Buyer Enquiry" and state.get("buyer_entry"):
            return _start_buyer_enquiry_from_faq(convo, state, session_id)
        if user_input == "Ask My Own Question":
            convo.current_step = "faq_own_question"
            db.session.commit()
            return jsonify({
                "session_id": session_id, "step": "faq_own_question",
                "prompt": "What real estate question is on your mind?",
                "input_type": "text", "options": [], "progress": None,
            })
        if user_input == "Return to FAQ Menu":
            return _return_to_menu(convo, session_id, "faq_menu")
        if user_input == "Return to Main Menu":
            return _return_to_menu(convo, session_id)
        return jsonify(_faq_batch_response(session_id, state))

    if current_step == "faq_after_answer":
        if state.get("seller_entry") or state.get("buyer_entry"):
            if user_input == "Yes, Show Remaining Questions":
                convo.current_step = "faq_questions"
                db.session.commit()
                return jsonify(_faq_batch_response(session_id, state))
            if user_input == "No, Start Seller Enquiry" and state.get("seller_entry"):
                return _start_seller_enquiry_from_faq(convo, state, session_id)
            if user_input == "No, Start Buyer Enquiry" and state.get("buyer_entry"):
                return _start_buyer_enquiry_from_faq(convo, state, session_id)
        if user_input == "Yes, Show More Questions":
            convo.current_step = "faq_questions"
            db.session.commit()
            return jsonify(_faq_batch_response(session_id, state))
        if user_input == "No, Continue Another Way":
            convo.current_step = "faq_continue_menu"
            db.session.commit()
            return jsonify({
                "session_id": session_id, "step": "faq_continue_menu",
                "prompt": "How would you like to continue?",
                "input_type": "buttons",
                "options": [
                    "Ask My Own Question", "Speak With the Team", "Request a Callback",
                    "Send an Email", "Return to FAQ Menu", "Return to Main Menu", "Finish Chat",
                ],
                "progress": None,
            })

    if current_step == "faq_continue_menu":
        if user_input == "Ask My Own Question":
            convo.current_step = "faq_own_question"
            db.session.commit()
            return jsonify({
                "session_id": session_id, "step": "faq_own_question",
                "prompt": "What real estate question is on your mind?",
                "input_type": "text", "options": [], "progress": None,
            })
        if user_input in {"Speak With the Team", "Request a Callback", "Send an Email"}:
            return _contact_from_faq(convo, state, session_id, user_input)
        if user_input == "Return to FAQ Menu":
            return _return_to_menu(convo, session_id, "faq_menu")
        if user_input == "Return to Main Menu":
            return _return_to_menu(convo, session_id)
        if user_input == "Finish Chat":
            convo.status = "completed"
            convo.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return jsonify({
                "session_id": session_id, "step": "submit",
                "prompt": "Thank you for visiting James Wholesale Homes.",
                "input_type": "terminal", "options": [], "progress": None,
            })

    if current_step == "faq_own_question":
        state["user_question"] = user_input
        convo.state_data = state
        convo.current_step = "faq_no_answer"
        db.session.commit()
        return jsonify({
            "session_id": session_id, "step": "faq_no_answer",
            "prompt": (
                "I do not have enough verified information to answer that accurately. "
                "The question can be sent to the James Wholesale Homes team."
            ),
            "input_type": "buttons",
            "options": ["Send My Question", "Request a Callback", "Call the Team", "Return to Main Menu"],
            "progress": None,
        })

    if current_step == "faq_no_answer":
        if user_input in {"Send My Question", "Request a Callback", "Call the Team"}:
            return _contact_from_faq(convo, state, session_id, user_input)
        if user_input == "Return to Main Menu":
            return _return_to_menu(convo, session_id)

    return None


# ---------------------------------------------------------------------------
# Contact-code helpers
# ---------------------------------------------------------------------------

def _otp_digest(session_id: str, code: str) -> str:
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, f"{session_id}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()


def _issue_contact_code(convo: Conversation, state: dict):
    code = f"{secrets.randbelow(1_000_000):06d}"
    ttl = current_app.config.get("CONTACT_OTP_TTL_SECONDS", 600)
    delivery = send_contact_verification_code(state.get("email"), state.get("phone"), code)
    state["otp_hash"] = _otp_digest(convo.session_id, code)
    state["otp_expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()
    state["otp_attempts"] = 0
    state["otp_email_sent"] = delivery.get("email_sent", False)
    state["otp_sms_sent"] = delivery.get("sms_sent", False)
    convo.state_data = state
    db.session.commit()
    return code, delivery


def _verify_contact_code(convo: Conversation, state: dict, raw_code: str):
    code = "".join(ch for ch in (raw_code or "") if ch.isdigit())
    max_attempts = current_app.config.get("CONTACT_OTP_MAX_ATTEMPTS", 5)
    attempts = state.get("otp_attempts", 0) + 1
    state["otp_attempts"] = attempts
    convo.state_data = state
    db.session.commit()

    if attempts > max_attempts:
        return False, "Too many verification attempts. Start a new chat or contact the team directly."
    try:
        expires_at = datetime.fromisoformat(state.get("otp_expires_at"))
    except (TypeError, ValueError):
        return False, "The verification code is no longer available. Please start a new chat."
    if datetime.now(timezone.utc) > expires_at:
        return False, "The verification code has expired. Please start a new chat to request another code."
    if len(code) != 6 or not hmac.compare_digest(state.get("otp_hash", ""), _otp_digest(convo.session_id, code)):
        return False, "The verification code is incorrect. Please check the six-digit code and try again."

    state["email_verified"] = bool(state.get("otp_email_sent")) or current_app.debug
    state["phone_verified"] = bool(state.get("otp_sms_sent")) or current_app.debug
    state.pop("otp_hash", None)
    state.pop("otp_expires_at", None)
    return True, None


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/chat/start", methods=["POST"])
@limiter.limit("30 per minute")
def chat_start():
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id") or str(uuid.uuid4())
    convo = _get_or_create_conversation(session_id)

    if convo.status == "completed":
        return jsonify({
            "session_id": session_id,
            "step": "submit",
            "prompt": "This conversation has been completed. Start a new chat to submit another enquiry.",
            "input_type": "terminal",
            "options": [],
            "progress": None,
        })

    existing_messages = convo.messages[-50:] if convo.messages else []
    response = _step_response(session_id, convo.current_step, convo.state_data or {})
    if convo.current_step == "welcome":
        response["statistics"] = _public_summary()
    if existing_messages:
        response["history"] = [
            {
                "sender": message.sender,
                "content": message.content,
                "validation_status": message.validation_status,
            }
            for message in existing_messages
        ]
    else:
        _log_message(convo, "bot", response.get("prompt", ""), "system")
    return jsonify(response)


@api_bp.route("/chat/message", methods=["POST"])
@limiter.limit("60 per minute")
def chat_message():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    user_input = data.get("input", "")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    convo = _get_or_create_conversation(session_id)
    if convo.status == "completed":
        return jsonify({"error": "This conversation has already been completed."}), 409

    state = convo.state_data or {}
    current_step = convo.current_step
    _log_message(convo, "user", str(user_input))

    faq_steps = {
        "faq_menu", "faq_questions", "faq_after_answer", "faq_continue_menu",
        "faq_own_question", "faq_no_answer",
    }
    if current_step in faq_steps:
        response = _handle_faq_step(convo, current_step, user_input, state, session_id)
        if response is not None:
            return response

    target_step = None
    response_extra = {}

    if current_step == "welcome":
        if user_input == "Real Estate FAQs":
            target_step = "faq_menu"
        elif user_input == "Recent Real Estate Projects":
            return jsonify({
                "session_id": session_id, "step": "public_projects",
                "prompt": "Recent Real Estate Projects",
                "input_type": "projects",
                "options": ["Return to Main Menu"],
                "projects": _public_projects(24), "progress": None,
            })
        elif user_input == "Featured Minnesota Locations":
            return jsonify({
                "session_id": session_id, "step": "public_locations",
                "prompt": "Featured Minnesota Locations",
                "input_type": "locations",
                "options": ["Buy in a Featured Location", "Sell in a Featured Location", "Return to Main Menu"],
                "locations": _public_locations(30), "progress": None,
            })
        elif user_input == "Sell a Property":
            state.update({
                "faq_category": "Selling a House Fast",
                "faq_viewed": [],
                "flow_type": "faq",
                "seller_entry": True,
                "buyer_entry": False,
                "intent": "Sell a Property",
                "journey_stage": "selling",
            })
            convo.flow_type = "faq"
            convo.state_data = state
            convo.current_step = "faq_questions"
            db.session.commit()
            return jsonify(_faq_batch_response(session_id, state, first_time=True))
        elif user_input == "Buy a Property":
            state.update({
                "faq_category": "Buying a Property",
                "faq_viewed": [],
                "flow_type": "faq",
                "seller_entry": False,
                "buyer_entry": True,
                "intent": "Buy a Property",
                "journey_stage": "buying",
            })
            convo.flow_type = "faq"
            convo.state_data = state
            convo.current_step = "faq_questions"
            db.session.commit()
            return jsonify(_faq_batch_response(session_id, state, first_time=True))
        elif user_input in FAQ_CATEGORIES:
            state.update({"faq_category": user_input, "faq_viewed": [], "flow_type": "faq", "seller_entry": False, "buyer_entry": False})
            convo.flow_type = "faq"
            convo.state_data = state
            convo.current_step = "faq_questions"
            db.session.commit()
            return jsonify(_faq_batch_response(session_id, state, first_time=True))
        else:
            flow_type = resolve_flow_from_intent(user_input)
            state.update({"intent": user_input, "flow_type": flow_type})
            state["journey_stage"] = "selling" if flow_type in {"sell", "buy_and_sell"} else "buying"
            convo.flow_type = flow_type
            target_step = "collect_name"

    elif current_step in {"public_projects", "public_locations"}:
        if user_input == "Return to Main Menu":
            target_step = "welcome"
        elif user_input in {"Sell a Similar Property", "Sell in a Featured Location"}:
            state.update({"intent": "Sell a Property", "flow_type": "sell", "journey_stage": "selling"})
            convo.flow_type = "sell"
            target_step = "collect_name"
        else:
            state.update({"intent": "Buy a Property", "flow_type": "buy", "journey_stage": "buying"})
            convo.flow_type = "buy"
            target_step = "collect_name"

    elif current_step == "collect_name":
        result = validators.validate_name(user_input)
        if not result.valid:
            return _validation_error(convo, result.message)
        state["full_name"] = result.value
        target_step = "collect_email"

    elif current_step == "collect_email":
        result = validators.validate_email(user_input)
        if not result.valid:
            return _validation_error(convo, result.message, result.suggestion)
        state["email"] = result.value
        target_step = "collect_phone"

    elif current_step == "collect_phone":
        result = validators.validate_us_phone(user_input)
        if not result.valid:
            return _validation_error(convo, result.message)
        state["phone"] = result.value
        state["phone_display"] = result.message
        # Verification step skipped: contact details are accepted without
        # sending or checking a one-time code.
        state["email_verified"] = False
        state["phone_verified"] = False
        state.pop("otp_hash", None)
        state.pop("otp_expires_at", None)
        state.pop("otp_attempts", None)
        state.pop("otp_email_sent", None)
        state.pop("otp_sms_sent", None)
        flow = state.get("flow_type")
        if flow == "funding":
            target_step = "funding_business_name"
        elif flow == "general_enquiry":
            target_step = "collect_contact_preference"
        else:
            target_step = "select_property_type"

    elif current_step == "funding_business_name":
        state["business_name"] = user_input.strip() or "N/A"
        target_step = "select_property_type"

    elif current_step in {"select_property_type", "buy_sell_target_type"}:
        if user_input == "View All Property Types":
            return jsonify(_step_response(
                session_id, current_step, state,
                options=extended_property_types() + ["Back to Main Property Types"],
            ))
        if user_input == "Back to Main Property Types":
            return jsonify(_step_response(
                session_id, current_step, state,
                options=PROPERTY_TYPES_PRIMARY + ["View All Property Types"],
            ))
        if current_step == "buy_sell_target_type":
            state["target_property_type"] = user_input
            state["journey_stage"] = "buying"
            target_step = "buyer_intended_use"
        else:
            state["property_type"] = user_input
            flow = state.get("flow_type")
            if flow in {"sell", "buy_and_sell"}:
                target_step = "seller_ownership"
            elif flow in {"buy", "investor_network"}:
                target_step = "buyer_intended_use"
            elif flow == "funding":
                target_step = "collect_location"
            else:
                target_step = "collect_contact_preference"

    elif current_step == "seller_ownership":
        state["ownership_status"] = user_input
        target_step = "seller_occupancy"

    elif current_step == "seller_occupancy":
        state["occupancy_status"] = user_input
        target_step = "seller_condition"

    elif current_step == "seller_condition":
        state["condition_status"] = user_input
        target_step = "seller_financials"

    elif current_step == "seller_financials":
        details = data.get("seller_financials", {})
        state["seller_financials"] = details
        target_step = "collect_location"

    elif current_step == "buyer_intended_use":
        key = "target_intended_use" if state.get("flow_type") == "buy_and_sell" and state.get("journey_stage") == "buying" else "intended_use"
        state[key] = user_input
        target_step = "buy_sell_target_location" if key == "target_intended_use" else "collect_location"

    elif current_step in {"collect_location", "buy_sell_target_location"}:
        loc = data.get("location", {})
        result = validators.validate_location(loc.get("city"), loc.get("state"), loc.get("zip"))
        if not result.valid:
            return _validation_error(convo, result.message, result.suggestion)
        value = result.value
        prefix = "target_" if current_step == "buy_sell_target_location" else ""
        state[prefix + "street_address"] = (loc.get("street_address") or "").strip()
        state[prefix + "city"] = value["city"]
        state[prefix + "state"] = value["state"]
        state[prefix + "zip"] = value["zip"]
        state[prefix + "county"] = (loc.get("county") or value.get("county") or "").strip()
        state[prefix + "address_validation_status"] = value["validation_status"]
        if current_step == "buy_sell_target_location":
            target_step = "buy_sell_target_budget"
        elif state.get("flow_type") == "funding":
            target_step = "funding_numbers"
        else:
            target_step = "collect_price_range"

    elif current_step in {"collect_price_range", "buy_sell_target_budget"}:
        is_target = current_step == "buy_sell_target_budget"
        kind = "budget" if is_target or state.get("flow_type") in {"buy", "investor_network"} else "range"
        result = validators.validate_price_range(data.get("min"), data.get("max"), kind=kind)
        if not result.valid:
            return _validation_error(convo, result.message)
        if is_target:
            state["target_price_min"] = result.value["min"]
            state["target_price_max"] = result.value["max"]
        else:
            state["price_min"] = result.value["min"]
            state["price_max"] = result.value["max"]
        target_step = "collect_specifications"

    elif current_step == "collect_specifications":
        specs = data.get("specifications", {})
        if state.get("flow_type") == "buy_and_sell" and state.get("journey_stage") == "buying":
            state["target_specifications"] = specs
            target_step = "buyer_funding_method"
        else:
            state["specifications"] = specs
            target_step = "collect_timeline" if state.get("flow_type") in {"sell", "buy_and_sell"} else "buyer_funding_method"

    elif current_step == "buyer_funding_method":
        key = "target_funding_method" if state.get("flow_type") == "buy_and_sell" else "funding_method"
        state[key] = user_input
        target_step = "collect_timeline"

    elif current_step == "collect_timeline":
        if state.get("flow_type") == "buy_and_sell" and state.get("journey_stage") == "buying":
            state["target_timeline"] = user_input
            target_step = "sale_purchase_dependency"
        else:
            state["timeline"] = user_input
            if state.get("flow_type") == "buy_and_sell":
                target_step = "buy_sell_target_type"
            else:
                target_step = "collect_contact_preference"

    elif current_step == "sale_purchase_dependency":
        state["purchase_depends_on_sale"] = user_input
        target_step = "collect_contact_preference"

    elif current_step == "funding_numbers":
        result = validators.validate_funding_numbers(
            data.get("purchase_price"), data.get("renovation_budget"), data.get("arv"), None
        )
        if not result.valid:
            return _validation_error(convo, result.message)
        state.update({
            "purchase_price": result.value["purchase_price"],
            "renovation_budget": result.value["renovation_budget"],
            "estimated_arv": result.value["estimated_arv"],
            "funding_flagged": result.value["flagged"],
            "funding_flag_reason": result.value["flag_reason"],
        })
        target_step = "funding_requested_amount"

    elif current_step == "funding_requested_amount":
        result = validators.validate_funding_numbers(
            state.get("purchase_price"), state.get("renovation_budget"),
            state.get("estimated_arv"), data.get("requested_funding"),
        )
        if not result.valid:
            return _validation_error(convo, result.message)
        contribution_result = validators.validate_price_range(
            "0", data.get("borrower_contribution") or "1", allow_zero_min=True, kind="range"
        )
        # The range helper is not a natural fit for one value; parse safely here after basic checks.
        try:
            contribution = float(str(data.get("borrower_contribution", "0")).replace("$", "").replace(",", ""))
        except ValueError:
            return _validation_error(convo, "Please enter a valid borrower contribution amount.")
        if contribution < 0:
            return _validation_error(convo, "Borrower contribution cannot be negative.")
        state["requested_funding"] = result.value["requested_funding"]
        state["borrower_contribution"] = contribution
        target_step = "funding_exit_strategy"

    elif current_step == "funding_exit_strategy":
        state["exit_strategy"] = user_input
        target_step = "funding_experience"

    elif current_step == "funding_experience":
        state["experience_summary"] = user_input
        target_step = "funding_closing_date"

    elif current_step == "funding_closing_date":
        try:
            closing = datetime.strptime(user_input, "%Y-%m-%d").date()
        except ValueError:
            return _validation_error(convo, "Please select a valid closing date.")
        if closing < datetime.now().date():
            return _validation_error(convo, "The expected closing date cannot be in the past.")
        state["expected_closing_date"] = user_input
        target_step = "collect_contact_preference"

    elif current_step == "collect_contact_preference":
        pref = data.get("contact_preference", {})
        result = validators.validate_contact_preference(pref.get("day"), pref.get("time"), pref.get("time_zone"))
        if not result.valid:
            return _validation_error(convo, result.message)
        state["contact_day"] = result.value["day"]
        state["contact_time"] = result.value["time"]
        state["time_zone"] = result.value["time_zone"]
        if state.pop("return_to_review_after_contact", False):
            target_step = "review"
        else:
            target_step = "ask_question"

    elif current_step == "ask_question":
        state["user_question"] = user_input.strip()
        target_step = "upload_files"

    elif current_step == "upload_files":
        target_step = "consent"

    elif current_step == "consent":
        consent = data.get("consent", {})
        if not any(consent.get(key) for key in ("call", "text", "email")):
            return _validation_error(convo, "Please select at least one contact method for this enquiry.")
        state["consent_call"] = bool(consent.get("call"))
        state["consent_text"] = bool(consent.get("text"))
        state["consent_email"] = bool(consent.get("email"))
        state["consent_marketing"] = bool(consent.get("marketing"))
        target_step = "review"

    elif current_step == "review":
        if user_input == "edit_callback_time":
            state["return_to_review_after_contact"] = True
            target_step = "collect_contact_preference"
        else:
            # Final re-validation removed: every field was already validated
            # as it was entered in each earlier step, so submission from the
            # review page is no longer blocked by a second check here.
            target_step = "submit"

    else:
        target_step = "welcome"

    convo.state_data = state
    convo.current_step = target_step
    db.session.commit()

    if target_step == "submit":
        lead = _create_lead_from_state(convo, state)
        convo.status = "completed"
        convo.completed_at = datetime.now(timezone.utc)
        convo.lead_id = lead.id
        db.session.commit()
        payload = _submission_response(lead)
        _log_message(convo, "bot", payload["prompt"], "system")
        return jsonify(payload)

    if target_step == "collect_price_range":
        response_extra["prompt"] = budget_prompt_for_flow(state.get("flow_type"))
    if target_step == "collect_timeline":
        flow = "buy" if state.get("flow_type") == "buy_and_sell" and state.get("journey_stage") == "buying" else state.get("flow_type")
        response_extra["options"] = timeline_options_for_flow(flow)
    if target_step == "collect_specifications":
        ptype = state.get("target_property_type") if state.get("flow_type") == "buy_and_sell" and state.get("journey_stage") == "buying" else state.get("property_type")
        response_extra["property_type"] = ptype
    if target_step == "review":
        review_data = _safe_state_preview(state, detailed=True)
        review_data["client_classification"] = _classify_client(state.get("flow_type"), state)
        review_data["service_area_status"] = _service_area_status(state)
        review_data["validation_errors"] = _submission_validation_errors(state, refresh_locations=False)
        review_data["uploaded_files"] = [
            {
                "name": item.original_filename,
                "category": item.document_category or "Other",
                "scan_status": item.scan_status or "pending",
            }
            for item in UploadedFile.query.filter_by(conversation_id=convo.id).order_by(UploadedFile.created_at).all()
        ]
        response_extra["review_data"] = review_data

    payload = _step_response(session_id, target_step, state, **response_extra)
    _log_message(convo, "bot", payload.get("prompt", ""), "system")
    return jsonify(payload)


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------
def _service_area_status(state):
    city = (state.get("city") or state.get("target_city") or "").lower()
    state_code = state.get("state") or state.get("target_state")
    if state_code != "MN":
        return "Outside Current Service Area"
    if city == "saint francis" or city == "st francis":
        return "In Primary Service Area"
    if city:
        return "In Extended Service Area"
    return "Requires Manual Review"


def _classify_client(flow_type: str, state: dict) -> str:
    if flow_type == "sell":
        if state.get("property_type") in {"Vacant Land", "Agricultural Land", "Development Land", "Farm or Ranch"}:
            return "Landowner"
        if state.get("occupancy_status") == "Tenant occupied":
            return "Rental Property Owner"
        return "Property Seller"
    if flow_type == "buy":
        use = state.get("intended_use")
        if use == "Fix and flip":
            return "Fix-and-Flip Investor"
        if use in {"Buy and hold", "Long-term rental"}:
            return "Buy-and-Hold Investor"
        return "Property Buyer"
    return {
        "buy_and_sell": "Buyer and Seller",
        "funding": "Funding Applicant",
        "investor_network": "Cash Investor",
        "general_enquiry": "General Enquiry",
    }.get(flow_type, "General Enquiry")


def _bool_from_form(value):
    if value in {True, "yes", "Yes", "true", "1", 1}:
        return True
    if value in {False, "no", "No", "false", "0", 0}:
        return False
    return None


def _submission_validation_errors(state: dict, refresh_locations: bool = False) -> list[str]:
    """Revalidate the complete enquiry before it is converted into a lead."""
    errors = []

    for validator, value in (
        (validators.validate_name, state.get("full_name")),
        (validators.validate_email, state.get("email")),
        (validators.validate_us_phone, state.get("phone")),
    ):
        result = validator(value)
        if not result.valid:
            errors.append(result.message)

    if not (state.get("email_verified") or state.get("phone_verified")):
        errors.append("Verify at least one contact method.")

    flow = state.get("flow_type", "general_enquiry")
    property_flows = {"sell", "buy", "buy_and_sell", "investor_network", "funding"}
    if flow in property_flows and not state.get("property_type"):
        errors.append("Select a real estate type.")

    def validate_saved_location(prefix: str = ""):
        city = state.get(prefix + "city")
        state_code = state.get(prefix + "state")
        zip_code = state.get(prefix + "zip")
        status_key = prefix + "address_validation_status"
        if not city or not state_code or not zip_code:
            errors.append("Provide a complete city, state and ZIP code.")
            return
        # Always run local checks. Refresh the remote match at final submission when possible.
        if refresh_locations or state.get(status_key) != "Validated":
            result = validators.validate_location(city, state_code, zip_code)
            if not result.valid:
                errors.append(result.message)
                return
            state[prefix + "city"] = result.value["city"]
            state[prefix + "state"] = result.value["state"]
            state[prefix + "zip"] = result.value["zip"]
            state[status_key] = result.value["validation_status"]
        else:
            # These calls enforce strict local format checks without changing the saved values.
            if not validators.validate_state(state_code).valid or not validators.validate_zip(zip_code).valid:
                errors.append("Review the city, state and ZIP code.")
            if str(city).strip().lower() in validators.REJECTED_CITY_TOKENS:
                errors.append("Please enter a real US city name.")

    if flow in property_flows:
        validate_saved_location()

    if flow == "buy_and_sell":
        if not state.get("target_property_type"):
            errors.append("Select the property type you want to buy.")
        validate_saved_location("target_")

    if flow in {"sell", "buy", "investor_network", "buy_and_sell"}:
        kind = "budget" if flow in {"buy", "investor_network"} else "range"
        result = validators.validate_price_range(state.get("price_min"), state.get("price_max"), kind=kind)
        if not result.valid:
            errors.append(result.message)

    if flow == "buy_and_sell":
        result = validators.validate_price_range(
            state.get("target_price_min"), state.get("target_price_max"), kind="budget"
        )
        if not result.valid:
            errors.append(result.message)

    pref = validators.validate_contact_preference(
        state.get("contact_day"), state.get("contact_time"), state.get("time_zone")
    )
    if not pref.valid:
        errors.append(pref.message)

    if not any(state.get(key) for key in ("consent_call", "consent_text", "consent_email")):
        errors.append("Select at least one contact method.")

    # Keep error copy concise and avoid repeating the same issue.
    return list(dict.fromkeys(item for item in errors if item))


def _create_lead_from_state(convo: Conversation, state: dict) -> Lead:
    flow_type = state.get("flow_type", "general_enquiry")
    lead = Lead(
        session_id=convo.session_id,
        lead_type=flow_type,
        client_classification=_classify_client(flow_type, state),
        qualification_level=(
            "Contact Information Verified"
            if state.get("email_verified") or state.get("phone_verified")
            else "Basic Qualification Complete"
        ),
        service_area_status=_service_area_status(state),
        full_name=state.get("full_name", "Not provided"),
        email=state.get("email", ""),
        email_verified=state.get("email_verified", False),
        phone=state.get("phone", ""),
        phone_verified=state.get("phone_verified", False),
        preferred_contact_day=state.get("contact_day"),
        preferred_contact_time=state.get("contact_time"),
        preferred_time_zone=state.get("time_zone"),
        consent_call=state.get("consent_call", False),
        consent_text=state.get("consent_text", False),
        consent_email=state.get("consent_email", False),
        user_question=state.get("user_question"),
        submitted_links=state.get("submitted_links", []),
        status="New",
        priority="High" if state.get("timeline") in {"As Soon as Possible", "Within 14 Days"} else "Normal",
    )
    db.session.add(lead)
    db.session.flush()

    if flow_type in {"sell", "buy_and_sell"}:
        financials = state.get("seller_financials", {})
        specs = state.get("specifications", {})
        pd = PropertyDetails(
            lead_id=lead.id,
            property_type=state.get("property_type"),
            street_address=state.get("street_address"),
            city=state.get("city"),
            state=state.get("state"),
            zip_code=state.get("zip"),
            county=state.get("county"),
            address_validation_status=state.get("address_validation_status"),
            ownership_status=state.get("ownership_status"),
            occupancy_status=state.get("occupancy_status"),
            condition_status=state.get("condition_status"),
            selling_min=state.get("price_min"),
            selling_max=state.get("price_max"),
            has_mortgage=_bool_from_form(financials.get("has_mortgage")),
            mortgage_balance=financials.get("mortgage_balance") or None,
            has_liens=_bool_from_form(financials.get("has_liens")),
            taxes_current=_bool_from_form(financials.get("taxes_current")),
            in_foreclosure=_bool_from_form(financials.get("in_foreclosure")),
            tenants_in_place=state.get("occupancy_status") == "Tenant occupied",
            repairs_needed=state.get("condition_status") not in {"Excellent", "Good", None},
            selling_reason=specs.get("notes") if isinstance(specs, dict) else str(specs),
            selling_timeline=state.get("timeline"),
            transaction_classification="Buy and Sell" if flow_type == "buy_and_sell" else "Wanted to Sell",
        )
        db.session.add(pd)

    if flow_type in {"buy", "buy_and_sell", "investor_network"}:
        target = flow_type == "buy_and_sell"
        specs = state.get("target_specifications", {}) if target else state.get("specifications", {})
        bc = BuyerCriteria(
            lead_id=lead.id,
            property_types=state.get("target_property_type") if target else state.get("property_type"),
            preferred_city=state.get("target_city") if target else state.get("city"),
            preferred_state=state.get("target_state") if target else state.get("state"),
            preferred_zip=state.get("target_zip") if target else state.get("zip"),
            preferred_county=state.get("target_county") if target else state.get("county"),
            budget_min=state.get("target_price_min") if target else state.get("price_min"),
            budget_max=state.get("target_price_max") if target else state.get("price_max"),
            intended_use=state.get("target_intended_use") if target else state.get("intended_use"),
            funding_method=state.get("target_funding_method") if target else state.get("funding_method"),
            purchase_timeline=state.get("target_timeline") if target else state.get("timeline"),
            min_bedrooms=specs.get("min_bedrooms") or None,
            min_bathrooms=specs.get("min_bathrooms") or None,
            min_sqft=specs.get("min_sqft") or None,
            max_repair_level=specs.get("max_repair_level") or None,
            min_acreage=specs.get("min_acreage") or None,
            max_acreage=specs.get("max_acreage") or None,
            zoning_preference=specs.get("zoning") or None,
            min_building_area=specs.get("min_building_area") or None,
            loading_docks_required=_bool_from_form(specs.get("loading_docks")),
        )
        db.session.add(bc)

    if flow_type == "funding":
        closing_date = datetime.strptime(state["expected_closing_date"], "%Y-%m-%d").date() if state.get("expected_closing_date") else None
        fd = FundingDetails(
            lead_id=lead.id,
            business_name=state.get("business_name"),
            property_type=state.get("property_type"),
            street_address=state.get("street_address"),
            city=state.get("city"),
            state=state.get("state"),
            zip_code=state.get("zip"),
            purchase_price=state.get("purchase_price"),
            renovation_budget=state.get("renovation_budget"),
            estimated_arv=state.get("estimated_arv"),
            requested_funding=state.get("requested_funding"),
            borrower_contribution=state.get("borrower_contribution"),
            exit_strategy=state.get("exit_strategy"),
            experience_summary=state.get("experience_summary"),
            expected_closing_date=closing_date,
            flagged_for_review=state.get("funding_flagged", False),
            flag_reason=state.get("funding_flag_reason"),
        )
        db.session.add(fd)
        if fd.flagged_for_review:
            lead.qualification_level = "Human Review Required"
            lead.priority = "High"

    db.session.commit()
    UploadedFile.query.filter_by(conversation_id=convo.id, lead_id=None).update({"lead_id": lead.id})
    db.session.commit()

    from app.services.notifications import send_owner_notification, send_user_confirmation
    send_owner_notification(lead)
    if lead.consent_email:
        send_user_confirmation(lead)
    return lead


def _safe_state_preview(state, detailed=False):
    basic_keys = [
        "intent", "flow_type", "full_name", "email", "phone_display", "email_verified", "phone_verified",
        "property_type", "street_address", "city", "state", "zip", "county", "address_validation_status",
        "price_min", "price_max", "ownership_status", "occupancy_status", "condition_status",
        "intended_use", "funding_method", "timeline",
        "target_property_type", "target_street_address", "target_city", "target_state", "target_zip", "target_county", "target_address_validation_status",
        "target_price_min", "target_price_max", "target_intended_use", "target_funding_method", "target_timeline",
        "purchase_depends_on_sale", "business_name", "purchase_price", "renovation_budget", "estimated_arv",
        "requested_funding", "borrower_contribution", "exit_strategy", "experience_summary", "expected_closing_date",
        "contact_day", "contact_time", "time_zone", "user_question",
    ]
    preview = {key: state.get(key) for key in basic_keys if state.get(key) not in (None, "", [])}
    if detailed:
        preview["specifications"] = state.get("specifications", {})
        preview["target_specifications"] = state.get("target_specifications", {})
        preview["submitted_links"] = state.get("submitted_links", [])
        preview["consent"] = {
            "call": state.get("consent_call", False),
            "text": state.get("consent_text", False),
            "email": state.get("consent_email", False),
        }
    return preview


def _submission_response(lead: Lead) -> dict:
    return {
        "prompt": "Your real estate enquiry has been submitted successfully.",
        "step": "submit",
        "input_type": "terminal",
        "options": [],
        "progress": None,
        "reference_number": lead.reference_number,
        "lead_type": lead.lead_type,
        "preferred_contact_day": lead.preferred_contact_day,
        "preferred_contact_time": lead.preferred_contact_time,
        "masked_email": _mask_email(lead.email),
        "masked_phone": _mask_phone(lead.phone),
    }


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    return f"{name[:2]}{'*' * max(len(name) - 2, 2)}@{domain}"


def _mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"(***) ***-{digits[-4:]}" if len(digits) >= 4 else "****"


# ---------------------------------------------------------------------------
# Attachments and links
# ---------------------------------------------------------------------------
@api_bp.route("/chat/upload", methods=["POST"])
@limiter.limit("15 per minute")
def chat_upload():
    session_id = request.form.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    convo = Conversation.query.filter_by(session_id=session_id).first()
    if not convo:
        return jsonify({"error": "Conversation not found."}), 404
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "No file provided."}), 400

    existing_count = UploadedFile.query.filter_by(conversation_id=convo.id).count()
    max_files = current_app.config["MAX_FILES_PER_SUBMISSION"]
    if existing_count >= max_files:
        return jsonify({"error": f"You may upload a maximum of {max_files} files."}), 422

    file_bytes = uploaded.read()
    result = file_security.validate_upload(
        uploaded.filename,
        file_bytes,
        current_app.config["ALLOWED_EXTENSIONS"],
        current_app.config["MAX_CONTENT_LENGTH"],
    )
    if not result.valid:
        return jsonify({"error": result.message}), 422

    storage_path = file_security.save_upload(file_bytes, result.safe_filename, current_app.config["UPLOAD_FOLDER"])
    scan_status = file_security.run_malware_scan(storage_path)
    file_record = UploadedFile(
        conversation_id=convo.id,
        original_filename=uploaded.filename,
        stored_filename=result.safe_filename,
        file_type=result.extension,
        document_category=request.form.get("document_category") or "Other",
        file_size=len(file_bytes),
        storage_path=storage_path,
        scan_status=scan_status,
    )
    db.session.add(file_record)
    db.session.commit()
    _log_message(convo, "user", f"Uploaded file: {uploaded.filename}", "file")
    return jsonify({
        "file_id": file_record.id,
        "original_filename": file_record.original_filename,
        "scan_status": file_record.scan_status,
        "message": "File received and queued for security scanning.",
    })


@api_bp.route("/chat/link", methods=["POST"])
@limiter.limit("20 per minute")
def chat_link():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    convo = Conversation.query.filter_by(session_id=session_id).first()
    if not convo:
        return jsonify({"error": "Conversation not found."}), 404
    result = validators.validate_url(data.get("url"))
    if not result.valid:
        return jsonify({"error": result.message}), 422
    state = convo.state_data or {}
    links = list(dict.fromkeys(state.get("submitted_links", []) + [result.value]))
    if len(links) > 5:
        return jsonify({"error": "You may add a maximum of five links."}), 422
    state["submitted_links"] = links
    convo.state_data = state
    db.session.commit()
    _log_message(convo, "user", f"Added link: {result.value}", "link")
    return jsonify({"url": result.value, "message": "Link added to your enquiry."})


@api_bp.route("/chat/new", methods=["POST"])
@limiter.limit("20 per minute")
def chat_new():
    session_id = str(uuid.uuid4())
    convo = _get_or_create_conversation(session_id)
    payload = _step_response(session_id, convo.current_step, convo.state_data or {})
    payload["statistics"] = _public_summary()
    return jsonify(payload)
