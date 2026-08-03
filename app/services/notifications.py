"""Transactional email and optional SMS-webhook notifications.

A lead is always committed before notification delivery is attempted. Delivery
results are written to EmailLog, so an unavailable email provider never loses a
lead submission.

Email is sent over the Resend HTTPS API rather than raw SMTP. Render (and many
other hosts) block outbound SMTP ports 25/465/587 on free instances, and even
port 25 stays blocked on paid instances since Render runs on AWS EC2. An HTTPS
API call is unaffected by that restriction and needs no extra dependency.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import formataddr
from html import escape

from flask import current_app

from app import db
from app.models.email_log import EmailLog

RESEND_API_URL = "https://api.resend.com/emails"


def _clean(value) -> str:
    """Strip whitespace, newlines and stray wrapping quotes from a config value.

    Render's environment editor stores values literally, so a value pasted from
    a .env file as MAIL_SENDER_NAME="James Wholesale Homes" keeps its quotes.
    Those quotes then get re-escaped by formataddr into an invalid From header
    and Resend rejects the whole request with a 422 validation error.
    """
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def _record_log(lead_id, recipient, subject, status, error=None):
    log = EmailLog(
        lead_id=lead_id,
        recipient=recipient or "(unset)",
        subject=subject,
        delivery_status=status,
        sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        error_details=error,
    )
    db.session.add(log)
    db.session.commit()
    return log


def _recipient_list(value: str | None) -> list[str]:
    """Return clean addresses from a comma/semicolon-separated setting."""
    value = _clean(value)
    if not value:
        return []
    return [cleaned for item in value.replace(";", ",").split(",") if (cleaned := _clean(item))]


PROVIDER_ENDPOINTS = {
    "smtp2go": "https://api.smtp2go.com/v3/email/send",
    "mailjet": "https://api.mailjet.com/v3.1/send",
    "brevo": "https://api.brevo.com/v3/smtp/email",
    "sendgrid": "https://api.sendgrid.com/v3/mail/send",
    "resend": "https://api.resend.com/emails",
}

# Providers that let you verify a single SENDER ADDRESS by clicking a link
# emailed to it, requiring no DNS records and no domain ownership.
SINGLE_SENDER_PROVIDERS = {"smtp2go", "mailjet", "brevo", "sendgrid"}


def _active_provider() -> str:
    """Which transport to use.

    Explicit MAIL_PROVIDER wins. Otherwise the provider is inferred from
    whichever API key is present, so an existing Resend-only deployment keeps
    working with no config change.
    """
    chosen = _clean(current_app.config.get("MAIL_PROVIDER")).lower()
    if chosen in PROVIDER_ENDPOINTS:
        return chosen
    for candidate in ("mailjet", "smtp2go", "brevo", "sendgrid", "resend"):
        if _clean(current_app.config.get(f"{candidate.upper()}_API_KEY")):
            return candidate
    # Default. Mailjet verifies a single sender address by emailing it a
    # confirmation link: no DNS records, no domain, no phone number.
    return "mailjet"


def _provider_key(provider: str) -> str:
    generic = _clean(current_app.config.get("MAIL_API_KEY"))
    specific = _clean(current_app.config.get(f"{provider.upper()}_API_KEY"))
    return specific or generic


def _build_request(provider, api_key, sender, sender_name, recipient, subject, text_body, html_body):
    """Return a urllib Request shaped for the chosen provider's API."""
    url = PROVIDER_ENDPOINTS[provider]

    if provider == "smtp2go":
        payload = {
            "sender": formataddr((sender_name, sender)),
            "to": [recipient],
            "subject": subject,
            "text_body": text_body,
        }
        if html_body:
            payload["html_body"] = html_body
        headers = {"Content-Type": "application/json", "X-Smtp2go-Api-Key": api_key}

    elif provider == "mailjet":
        # Mailjet authenticates with an API key plus a secret key over HTTP Basic.
        secret = _clean(current_app.config.get("MAILJET_SECRET_KEY"))
        if not secret:
            raise RuntimeError("MAILJET_SECRET_KEY is not set on this server")
        message = {
            "From": {"Email": sender, "Name": sender_name},
            "To": [{"Email": recipient}],
            "Subject": subject,
            "TextPart": text_body,
        }
        if html_body:
            message["HTMLPart"] = html_body
        payload = {"Messages": [message]}
        basic = base64.b64encode(f"{api_key}:{secret}".encode("utf-8")).decode("ascii")
        headers = {"Content-Type": "application/json", "Authorization": f"Basic {basic}"}

    elif provider == "brevo":
        payload = {
            "sender": {"email": sender, "name": sender_name},
            "to": [{"email": recipient}],
            "subject": subject,
            "textContent": text_body,
        }
        if html_body:
            payload["htmlContent"] = html_body
        headers = {"Content-Type": "application/json", "accept": "application/json", "api-key": api_key}

    elif provider == "sendgrid":
        content = [{"type": "text/plain", "value": text_body}]
        if html_body:
            content.append({"type": "text/html", "value": html_body})
        payload = {
            "personalizations": [{"to": [{"email": recipient}]}],
            "from": {"email": sender, "name": sender_name},
            "subject": subject,
            "content": content,
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    else:  # resend
        payload = {
            "from": formataddr((sender_name, sender)),
            "to": [recipient],
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            payload["html"] = html_body
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    return urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers
    )


def _smtp_send(recipient: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    """Send an email over an HTTPS provider API.

    Kept as ``_smtp_send`` so every call site below is unchanged. Raw SMTP is
    never used: Render blocks outbound ports 25/465/587 on free instances and
    blocks port 25 on every instance, while an HTTPS POST always goes through.

    Brevo (the default) and SendGrid allow a single sender address to be
    verified by clicking a link in a confirmation email, so neither one needs
    access to domain DNS records. Resend remains supported for anyone who has
    already verified a domain there, but it is no longer the default because
    it offers no single-sender option.
    """
    provider = _active_provider()
    api_key = _provider_key(provider)
    sender = _clean(current_app.config.get("MAIL_DEFAULT_SENDER"))
    sender_name = _clean(current_app.config.get("MAIL_SENDER_NAME")) or "James Wholesale Homes"
    recipient = _clean(recipient)
    timeout = current_app.config.get("MAIL_TIMEOUT", 20)

    if not api_key:
        raise RuntimeError(
            f"No API key configured for the '{provider}' mail provider. "
            f"Set {provider.upper()}_API_KEY on the server."
        )
    if not sender:
        raise RuntimeError("MAIL_DEFAULT_SENDER is not set on this server")
    if "@" not in sender:
        raise RuntimeError(f"MAIL_DEFAULT_SENDER is not a valid address: {sender!r}")
    if provider == "resend" and not api_key.startswith("re_"):
        raise RuntimeError(
            "RESEND_API_KEY does not look like a Resend key (it must start with 're_'). "
            "Check for a stray quote, space or newline in the environment variable."
        )
    if provider == "sendgrid" and not api_key.startswith("SG."):
        raise RuntimeError("SENDGRID_API_KEY does not look like a SendGrid key (it must start with 'SG.').")
    if provider == "smtp2go" and not api_key.startswith("api-"):
        raise RuntimeError("SMTP2GO_API_KEY does not look like an SMTP2GO key (it must start with 'api-').")

    req = _build_request(provider, api_key, sender, sender_name, recipient, subject, text_body, html_body)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if not (200 <= response.status < 300):
                raise RuntimeError(f"{provider} API returned status {response.status}")
            body = response.read().decode("utf-8", errors="replace")
            _check_soft_failure(provider, body, sender, recipient)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{provider} API error {exc.code}: {detail} | "
            f"{_explain_provider_error(provider, exc.code, detail, sender, recipient)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{provider} API unreachable: {exc.reason}") from exc


def _check_soft_failure(provider, body: str, sender: str, recipient: str) -> None:
    """Catch providers that answer HTTP 200 while still refusing the message.

    SMTP2GO and Mailjet both do this: the request was well formed, so the status
    is 200, but the message itself was rejected (unverified sender, suppressed
    address). Without this check a refused email would be logged as "sent".
    """
    if not body:
        return
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return

    if provider == "smtp2go":
        payload = data.get("data") or {}
        failures = payload.get("failures") or []
        if data.get("error") or failures or payload.get("succeeded", 1) == 0:
            reason = data.get("error") or "; ".join(str(item) for item in failures) or "unknown reason"
            raise RuntimeError(
                f"smtp2go accepted the request but refused the message: {reason} | "
                f"FIX: confirm '{sender}' is listed and Active under SMTP2GO -> Sending -> Verified Senders."
            )

    elif provider == "mailjet":
        for message in data.get("Messages", []):
            if str(message.get("Status", "success")).lower() != "success":
                errors = "; ".join(
                    str(err.get("ErrorMessage") or err) for err in message.get("Errors", [])
                ) or "unknown reason"
                raise RuntimeError(
                    f"mailjet accepted the request but refused the message: {errors} | "
                    f"FIX: confirm '{sender}' is validated under Mailjet -> Senders & Domains."
                )


def _explain_provider_error(provider, code, detail, sender, recipient) -> str:
    """Turn a raw provider HTTP failure into a plain-English next step."""
    lowered = (detail or "").lower()

    if code in (401, 403) and ("unauthorized" in lowered or "api key" in lowered or "api-key" in lowered):
        if provider == "mailjet":
            return "FIX: the MAILJET_API_KEY / MAILJET_SECRET_KEY pair is wrong. Both are required - copy them from Mailjet -> Account -> API Key Management."
        return f"FIX: the {provider.upper()}_API_KEY is wrong, revoked or mistyped. Generate a fresh key and update it on Render."

    if "sender" in lowered and ("not valid" in lowered or "not verified" in lowered or "does not exist" in lowered):
        return (
            f"FIX: '{sender}' has not been verified as a sender in {provider}. Add it under the provider's "
            "Senders screen and click the confirmation link that arrives in that inbox. No DNS access is needed."
        )

    if provider == "resend":
        if code == 401:
            return "FIX: the RESEND_API_KEY is wrong or revoked. Create a fresh key at resend.com/api-keys."
        if code == 403 or "testing emails" in lowered or "own email" in lowered:
            if sender.endswith("@resend.dev"):
                return (
                    f"FIX: {sender} is Resend's shared sandbox sender and can only deliver to the address that "
                    f"owns the Resend account. '{recipient}' is not that address. Either set OWNER_EMAIL to your "
                    "Resend account address, or switch MAIL_PROVIDER to brevo/sendgrid, which verify a single "
                    "sender by email link and need no DNS access."
                )
            return (
                f"FIX: the domain behind {sender} is not verified in Resend, and Resend has no single-sender "
                "option. Switch MAIL_PROVIDER to brevo or sendgrid to send without DNS access."
            )
        if code == 422:
            return (
                "FIX: Resend rejected a field, almost always the From header. Check MAIL_SENDER_NAME and "
                "MAIL_DEFAULT_SENDER on Render contain no quote characters."
            )

    if code == 400:
        return f"FIX: {provider} rejected the request payload. Check MAIL_DEFAULT_SENDER and MAIL_SENDER_NAME for stray quotes or typos."
    if code == 429:
        return f"FIX: the {provider} sending limit was hit. Wait for the quota to reset or upgrade the plan."
    return "FIX: see the raw provider response above."


def _money(value):
    if value in (None, ""):
        return "Not provided"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _owner_body(lead):
    property_details = lead.property_details
    buyer = lead.buyer_criteria

    # FundingDetails has no direct relationship on Lead in this build.
    from app.models.funding_details import FundingDetails
    funding = FundingDetails.query.filter_by(lead_id=lead.id).first()

    admin_base = current_app.config.get("ADMIN_BASE_URL", "").rstrip("/")
    admin_link = f"{admin_base}/admin/leads/{lead.id}" if admin_base else ""

    lines = [
        "A new real estate enquiry has been submitted.",
        "",
        f"Reference: {lead.reference_number}",
        f"Submitted: {lead.created_at}",
        f"Lead type: {lead.lead_type.replace('_', ' ').title()}",
        f"Classification: {lead.client_classification or 'Not classified'}",
        f"Qualification: {lead.qualification_level or 'New'}",
        f"Priority: {lead.priority}",
        "",
        "Contact information:",
        f"Name: {lead.full_name}",
        f"Email: {lead.email}",
        f"Phone: {lead.phone}",
        f"Email verified: {'Yes' if lead.email_verified else 'No'}",
        f"Phone verified: {'Yes' if lead.phone_verified else 'No'}",
        f"Preferred contact: {lead.preferred_contact_day or 'No preference'} / {lead.preferred_contact_time or 'No preference'}",
        f"Time zone: {lead.preferred_time_zone or 'Not provided'}",
        f"Contact consent: call={'Yes' if lead.consent_call else 'No'}, text={'Yes' if lead.consent_text else 'No'}, email={'Yes' if lead.consent_email else 'No'}",
    ]
    if property_details:
        lines.extend([
            "",
            "Seller property:",
            f"Type: {property_details.property_type or 'Not provided'}",
            f"Location: {property_details.street_address or ''} {property_details.city or ''}, {property_details.state or ''} {property_details.zip_code or ''}".strip(),
            f"Expected range: {_money(property_details.selling_min)} to {_money(property_details.selling_max)}",
            f"Condition: {property_details.condition_status or 'Not provided'}",
            f"Occupancy: {property_details.occupancy_status or 'Not provided'}",
        ])
    if buyer:
        lines.extend([
            "",
            "Buyer criteria:",
            f"Property types: {buyer.property_types or 'Not provided'}",
            f"Preferred location: {buyer.preferred_city or ''}, {buyer.preferred_state or ''} {buyer.preferred_zip or ''}".strip(),
            f"Budget: {_money(buyer.budget_min)} to {_money(buyer.budget_max)}",
            f"Intended use: {buyer.intended_use or 'Not provided'}",
            f"Funding method: {buyer.funding_method or 'Not provided'}",
        ])
    if funding:
        lines.extend([
            "",
            "Funding request:",
            f"Business: {funding.business_name or 'Not provided'}",
            f"Property: {funding.property_type or 'Not provided'}",
            f"Location: {funding.street_address or ''} {funding.city or ''}, {funding.state or ''} {funding.zip_code or ''}".strip(),
            f"Purchase price: {_money(funding.purchase_price)}",
            f"Renovation budget: {_money(funding.renovation_budget)}",
            f"Estimated ARV: {_money(funding.estimated_arv)}",
            f"Requested funding: {_money(funding.requested_funding)}",
            f"Borrower contribution: {_money(funding.borrower_contribution)}",
            f"Exit strategy: {funding.exit_strategy or 'Not provided'}",
            f"Expected closing: {funding.expected_closing_date or 'Not provided'}",
            f"Experience: {funding.experience_summary or 'Not provided'}",
            f"Manual review flag: {'Yes' if funding.flagged_for_review else 'No'}",
            f"Flag reason: {funding.flag_reason or 'None'}",
        ])
    if lead.user_question:
        lines.extend(["", "User question:", lead.user_question])
    if lead.submitted_links:
        lines.extend(["", "Submitted links:", *lead.submitted_links])
    if lead.files:
        lines.extend(["", "Uploaded files:", *[item.original_filename for item in lead.files]])

    lines.extend(["", "Open the secure admin dashboard to review the full conversation and files."])
    if admin_link:
        lines.append(admin_link)
    return "\n".join(lines)


def send_owner_notification(lead):
    recipients = _recipient_list(current_app.config.get("OWNER_EMAIL"))
    city_state = ""
    if lead.property_details:
        city_state = f" - {lead.property_details.city or ''}, {lead.property_details.state or ''}".rstrip(" ,-")
    elif lead.buyer_criteria:
        city_state = f" - {lead.buyer_criteria.preferred_city or ''}, {lead.buyer_criteria.preferred_state or ''}".rstrip(" ,-")
    subject = f"New {lead.lead_type.replace('_', ' ').title()} Lead - {lead.full_name}{city_state}"

    if not recipients:
        _record_log(lead.id, "(unset)", subject, "failed", error="OWNER_EMAIL not configured")
        return False

    body = _owner_body(lead)
    all_sent = True
    for recipient in recipients:
        try:
            _smtp_send(recipient, subject, body)
            _record_log(lead.id, recipient, subject, "sent")
        except Exception as exc:  # noqa: BLE001
            all_sent = False
            _record_log(lead.id, recipient, subject, "failed", error=str(exc))
    return all_sent


def send_test_email(recipient: str | None = None) -> tuple[bool, str]:
    """Send a simple email test without creating a lead."""
    recipients = _recipient_list(recipient or current_app.config.get("OWNER_EMAIL"))
    if not recipients:
        return False, "OWNER_EMAIL is not configured"

    subject = "James Wholesale Homes email test"
    body = (
        "Email delivery is configured correctly. New chatbot leads will be "
        "emailed automatically after they are saved in the admin dashboard."
    )
    errors = []
    for address in recipients:
        try:
            _smtp_send(address, subject, body)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{address}: {exc}")
    if errors:
        return False, "; ".join(errors)
    return True, f"Test email sent to {', '.join(recipients)}"


def send_user_confirmation(lead):
    subject = f"We received your real estate enquiry - {lead.reference_number}"
    if not lead.email:
        _record_log(lead.id, "(unset)", subject, "failed", error="Email address is missing")
        return False

    text = (
        f"Hello {lead.full_name},\n\n"
        "Thank you for contacting James Wholesale Homes. Your enquiry has been received.\n\n"
        f"Reference: {lead.reference_number}\n"
        f"Preferred contact: {lead.preferred_contact_day or 'No preference'} / "
        f"{lead.preferred_contact_time or 'No preference'}\n\n"
        "The team will review your information during business hours. "
        "Submitting an enquiry does not guarantee an offer, property availability or funding approval.\n"
    )
    html = (
        "<div style='font-family:Arial,sans-serif;color:#1f2933;line-height:1.6'>"
        "<div style='background:#16243E;padding:18px'><strong style='color:#fff'>James "
        "<span style='color:#E3562B'>Wholesale Homes</span></strong></div>"
        f"<p>Hello {escape(lead.full_name)},</p>"
        "<p>Thank you for contacting James Wholesale Homes. Your enquiry has been received.</p>"
        f"<p><strong>Reference:</strong> {escape(lead.reference_number)}</p>"
        f"<p><strong>Preferred contact:</strong> {escape(lead.preferred_contact_day or 'No preference')} / "
        f"{escape(lead.preferred_contact_time or 'No preference')}</p>"
        "<p style='font-size:12px;color:#6B7280'>Submitting an enquiry does not guarantee an offer, "
        "property availability or funding approval.</p></div>"
    )
    try:
        _smtp_send(lead.email, subject, text, html)
        _record_log(lead.id, lead.email, subject, "sent")
        return True
    except Exception as exc:  # noqa: BLE001
        _record_log(lead.id, lead.email, subject, "failed", error=str(exc))
        return False


def send_contact_verification_code(email: str, phone: str, code: str) -> dict:
    """Send one code through configured channels.

    SMS is provider-neutral: configure SMS_WEBHOOK_URL to accept a JSON payload
    containing ``to`` and ``message``. The webhook must return a 2xx response.
    """
    result = {"email_sent": False, "sms_sent": False, "errors": []}
    subject = "Your James Wholesale Homes verification code"
    body = (
        f"Your verification code is {code}. It expires in "
        f"{current_app.config.get('CONTACT_OTP_TTL_SECONDS', 600) // 60} minutes. "
        "Do not share this code."
    )

    if email:
        try:
            _smtp_send(email, subject, body)
            result["email_sent"] = True
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"email: {exc}")

    webhook = current_app.config.get("SMS_WEBHOOK_URL")
    if phone and webhook:
        payload = json.dumps({"to": phone, "message": body}).encode("utf-8")
        req = urllib.request.Request(
            webhook,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {current_app.config.get('SMS_WEBHOOK_TOKEN', '')}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                result["sms_sent"] = 200 <= response.status < 300
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"sms: {exc}")

    return result
