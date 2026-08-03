"""Conversation state definitions for the public real-estate assistant."""
from app.models.property_details import (
    PROPERTY_TYPES_PRIMARY,
    PROPERTY_TYPES_EXTENDED,
    OWNERSHIP_STATUS,
    OCCUPANCY_STATUS,
    CONDITION_STATUS,
)
from app.models.buyer_criteria import FUNDING_METHODS, PURCHASE_TIMELINES, INTENDED_USE
from app.models.funding_details import EXIT_STRATEGIES

WELCOME_BUTTONS = [
    "Sell a Property",
    "Buy a Property",
    "Submit a Funding Deal",
    "Recent Real Estate Projects",
    "Featured Minnesota Locations",
    "Real Estate FAQs",
    "About James Wholesale Homes",
    "Join the Buyers Network",
]

FAQ_MENU_BUTTONS = [
    "About James Wholesale Homes",
    "Selling a House Fast",
    "Buying a Property",
    "Rental and Tenant-Occupied Properties",
    "Off-Market Properties",
    "Wholesale Real Estate",
    "Investor Buyers Network",
    "Property Analysis and Due Diligence",
    "Private Money and Investment Funding",
]

INTENT_TO_FLOW = {
    "Buy a Property": "buy",
    "Sell a Property": "sell",
    "Buy and Sell a Property": "buy_and_sell",
    "Ask a Real Estate Question": "general_enquiry",
    "Submit a Funding Deal": "funding",
    "Join the Buyers Network": "investor_network",
}

CONTACT_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "No Preference"]
CONTACT_TIMES = [
    "9:00 AM to 11:00 AM",
    "11:00 AM to 1:00 PM",
    "1:00 PM to 3:00 PM",
    "3:00 PM to 5:00 PM",
    "Any Time During Business Hours",
    "No Preference",
]
TIME_ZONES = ["Eastern Time", "Central Time", "Mountain Time", "Pacific Time", "Alaska Time", "Hawaii Time"]

STEPS = {
    "welcome": {
        "prompt": "Welcome to James Wholesale Homes. How can we help with your real estate plans today?",
        "input_type": "welcome_menu",
        "options": WELCOME_BUTTONS,
    },
    "faq_menu": {
        "prompt": "Choose a real estate FAQ section.",
        "input_type": "buttons",
        "options": FAQ_MENU_BUTTONS + ["Return to Main Menu"],
    },
    "collect_name": {
        "prompt": "What is your full name?",
        "input_type": "text",
    },
    "collect_email": {
        "prompt": "What is your email address?",
        "input_type": "email",
    },
    "collect_phone": {
        "prompt": "What is the best phone number for contacting you?",
        "input_type": "phone",
    },
    "funding_business_name": {
        "prompt": "What is your business or company name, if applicable? You may enter N/A.",
        "input_type": "text",
    },
    "select_property_type": {
        "prompt": "Select the real estate type.",
        "input_type": "property_cards",
        "options": PROPERTY_TYPES_PRIMARY + ["View All Property Types"],
    },
    "seller_ownership": {
        "prompt": "Are you legally authorised to sell this property?",
        "input_type": "buttons",
        "options": OWNERSHIP_STATUS,
    },
    "seller_occupancy": {
        "prompt": "What is the current occupancy status?",
        "input_type": "buttons",
        "options": OCCUPANCY_STATUS,
    },
    "seller_condition": {
        "prompt": "How would you describe the property's condition?",
        "input_type": "condition_cards",
        "options": CONDITION_STATUS,
    },
    "seller_financials": {
        "prompt": "Provide any known mortgage, lien, property-tax or foreclosure details. You may leave optional fields blank.",
        "input_type": "seller_financials",
    },
    "collect_location": {
        "prompt": "Step 4: Enter the ZIP code, then confirm the suggested city and state.",
        "input_type": "location",
    },
    "collect_price_range": {
        "prompt": None,
        "input_type": "currency_range",
    },
    "buyer_intended_use": {
        "prompt": "How do you plan to use the property?",
        "input_type": "buttons",
        "options": INTENDED_USE,
    },
    "collect_specifications": {
        "prompt": "Tell us the important property requirements you have in mind.",
        "input_type": "property_specifications",
    },
    "buyer_funding_method": {
        "prompt": "How do you expect to fund the purchase?",
        "input_type": "buttons",
        "options": FUNDING_METHODS,
    },
    "collect_timeline": {
        "prompt": "What is your timeline?",
        "input_type": "buttons",
    },
    "buy_sell_target_type": {
        "prompt": "Now select the type of property you want to buy.",
        "input_type": "property_cards",
        "options": PROPERTY_TYPES_PRIMARY + ["View All Property Types"],
    },
    "buy_sell_target_location": {
        "prompt": "Enter your preferred buying location.",
        "input_type": "location",
    },
    "buy_sell_target_budget": {
        "prompt": "What is your buying budget for the next property?",
        "input_type": "currency_range",
    },
    "sale_purchase_dependency": {
        "prompt": "Does purchasing your next property depend on selling your current property first?",
        "input_type": "buttons",
        "options": ["Yes", "No", "Not Sure"],
    },
    "funding_numbers": {
        "prompt": "Provide the purchase price, renovation budget and estimated after-repair value.",
        "input_type": "funding_numbers",
    },
    "funding_requested_amount": {
        "prompt": "How much funding are you requesting, and what is your contribution?",
        "input_type": "funding_amounts",
    },
    "funding_exit_strategy": {
        "prompt": "What is your exit strategy?",
        "input_type": "buttons",
        "options": EXIT_STRATEGIES,
    },
    "funding_experience": {
        "prompt": "Briefly describe your previous real estate project experience, if any.",
        "input_type": "text_optional",
    },
    "funding_closing_date": {
        "prompt": "What is the expected closing date?",
        "input_type": "date",
    },
    "collect_contact_preference": {
        "prompt": "Choose the best day, time and time zone for the team to contact you.",
        "input_type": "contact_preference",
        "days": CONTACT_DAYS,
        "times": CONTACT_TIMES,
        "time_zones": TIME_ZONES,
    },
    "ask_question": {
        "prompt": "What real estate question is on your mind? This is optional.",
        "input_type": "text_optional",
    },
    "upload_files": {
        "prompt": "You may upload supporting files or add a property link. This is optional.",
        "input_type": "attachment_optional",
    },
    "consent": {
        "prompt": "Choose how James Wholesale Homes may contact you about this enquiry.",
        "input_type": "consent",
    },
    "review": {
        "prompt": "Review your information before submitting.",
        "input_type": "review",
    },
    "submit": {
        "prompt": "Your real estate enquiry has been submitted successfully.",
        "input_type": "terminal",
    },
}


def get_step(step_name: str) -> dict:
    return STEPS.get(step_name, STEPS["welcome"])


def resolve_flow_from_intent(intent_label: str) -> str:
    return INTENT_TO_FLOW.get(intent_label, "general_enquiry")


def extended_property_types() -> list:
    return PROPERTY_TYPES_EXTENDED


def budget_prompt_for_flow(flow_type: str) -> str:
    if flow_type in {"sell", "buy_and_sell"}:
        return "What selling price range are you considering?"
    return "What is your property buying budget?"


def timeline_options_for_flow(flow_type: str) -> list:
    if flow_type in {"sell", "buy_and_sell"}:
        return [
            "As Soon as Possible", "Within 14 Days", "Within 30 Days",
            "Within 60 Days", "Within 90 Days", "Flexible", "Researching Only",
        ]
    return PURCHASE_TIMELINES


FLOW_PROGRESS = {
    "collect_name": (1, 8, "Contact"),
    "collect_email": (1, 8, "Contact"),
    "collect_phone": (1, 8, "Contact"),
    "funding_business_name": (2, 8, "Deal"),
    "select_property_type": (2, 8, "Property Type"),
    "seller_ownership": (3, 8, "Property Details"),
    "seller_occupancy": (3, 8, "Property Details"),
    "seller_condition": (3, 8, "Property Details"),
    "seller_financials": (3, 8, "Property Details"),
    "collect_location": (4, 8, "Verify Location"),
    "collect_price_range": (5, 8, "Price Range"),
    "buyer_intended_use": (3, 8, "Requirements"),
    "collect_specifications": (5, 8, "Requirements"),
    "buyer_funding_method": (6, 8, "Funding"),
    "collect_timeline": (6, 8, "Timeline"),
    "buy_sell_target_type": (5, 8, "Next Property"),
    "buy_sell_target_location": (5, 8, "Verify Next Location"),
    "buy_sell_target_budget": (5, 8, "Next Property"),
    "funding_numbers": (4, 8, "Deal Numbers"),
    "funding_requested_amount": (4, 8, "Funding Request"),
    "funding_exit_strategy": (5, 8, "Exit Strategy"),
    "funding_experience": (5, 8, "Experience"),
    "funding_closing_date": (6, 8, "Timeline"),
    "collect_contact_preference": (7, 8, "Contact Time"),
    "ask_question": (7, 8, "Question"),
    "upload_files": (7, 8, "Documents"),
    "consent": (8, 8, "Consent"),
    "review": (8, 8, "Review"),
}


def progress_for_step(step_name: str):
    value = FLOW_PROGRESS.get(step_name)
    if not value:
        return None
    current, total, label = value
    return {"current": current, "total": total, "label": label, "percent": round(current / total * 100)}
