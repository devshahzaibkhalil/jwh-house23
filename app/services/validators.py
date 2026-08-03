"""
Server-side validation for lead-qualification fields.
Every rule here must ALSO be enforced server-side (never trust client JS alone).
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

from flask import current_app

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_MIN_LETTERS = 2

US_STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}

COMMON_DOMAIN_TYPOS = {
    "gmial.com": "gmail.com",
    "gmal.com": "gmail.com",
    "yaho.com": "yahoo.com",
    "outlok.com": "outlook.com",
    "hotmal.com": "hotmail.com",
    "hotmial.com": "hotmail.com",
}

DISPOSABLE_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com",
    "tempmail.com", "yopmail.com", "trashmail.com",
}

REJECTED_NAME_TOKENS = {"test", "unknown", "n/a", "na", "asdf", "xxx"}
REJECTED_CITY_TOKENS = {
    "usa", "us", "u.s.", "united states", "united states of america", "america",
    "city", "state", "unknown", "test", "n/a", "na", "none", "all usa", "anywhere",
}

US_STATE_CODES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}


class ValidationResult:
    def __init__(self, valid, value=None, message=None, suggestion=None):
        self.valid = valid
        self.value = value
        self.message = message
        self.suggestion = suggestion

    def to_dict(self):
        return {
            "valid": self.valid,
            "value": self.value,
            "message": self.message,
            "suggestion": self.suggestion,
        }


def validate_name(raw: str) -> ValidationResult:
    name = (raw or "").strip()
    if not name:
        return ValidationResult(False, message="Please enter your first and last name.")

    letters_only = re.sub(r"[^A-Za-z]", "", name)
    if len(letters_only) < NAME_MIN_LETTERS:
        return ValidationResult(False, message="Please enter your first and last name.")

    if any(ch.isdigit() for ch in name):
        return ValidationResult(False, message="Names cannot contain numbers.")

    if re.search(r"https?://|www\.|@", name):
        return ValidationResult(False, message="Please enter your name, not a link or email address.")

    if re.search(r"(.)\1{3,}", name):  # repeated symbol/char run
        return ValidationResult(False, message="Please enter a valid name.")

    if name.lower().strip() in REJECTED_NAME_TOKENS:
        return ValidationResult(False, message="Please enter your full name.")

    if not re.match(r"^[A-Za-z' \-.]+$", name):
        return ValidationResult(False, message="Please enter a valid name using letters only.")

    if len(name.split()) < 2:
        return ValidationResult(False, message="Please enter both first and last name.")

    return ValidationResult(True, value=name.title() if name.islower() else name)


def validate_email(raw: str) -> ValidationResult:
    email = (raw or "").strip().lower()
    if not EMAIL_RE.match(email):
        return ValidationResult(
            False, message="Please enter a valid email address, such as name@example.com."
        )

    domain = email.split("@")[-1]

    if domain in COMMON_DOMAIN_TYPOS:
        corrected = email.rsplit("@", 1)[0] + "@" + COMMON_DOMAIN_TYPOS[domain]
        return ValidationResult(False, value=email, suggestion=corrected,
                                 message=f"Did you mean {corrected}?")

    if domain in DISPOSABLE_DOMAINS:
        return ValidationResult(
            False,
            message="Please provide an email address where the team can reliably "
                    "contact you about your real estate enquiry.",
        )

    return ValidationResult(True, value=email)


def validate_us_phone(raw: str) -> ValidationResult:
    digits = re.sub(r"\D", "", raw or "")

    # Accept 10-digit, or 1 + 10-digit
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) != 10:
        return ValidationResult(False, message="Please enter a valid 10-digit US telephone number.")

    area_code = digits[:3]
    if area_code[0] in "01":
        return ValidationResult(False, message="Please enter a valid 10-digit US telephone number.")

    if len(set(digits)) == 1:  # all identical digits, e.g. 1111111111
        return ValidationResult(False, message="Please enter a valid 10-digit US telephone number.")

    if digits in {"1234567890", "0123456789", "9876543210"}:
        return ValidationResult(False, message="Please enter a valid 10-digit US telephone number.")

    e164 = f"+1{digits}"
    display = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    return ValidationResult(True, value=e164, message=display)


def validate_state(state_code: str) -> ValidationResult:
    code = (state_code or "").strip().upper()
    if code not in US_STATE_CODES:
        return ValidationResult(False, message="Please select a valid US state.")
    return ValidationResult(True, value=code)


def validate_zip(zip_code: str) -> ValidationResult:
    z = (zip_code or "").strip()
    if not re.match(r"^\d{5}(-\d{4})?$", z):
        return ValidationResult(False, message="Please enter a valid 5-digit ZIP or ZIP+4 code.")
    return ValidationResult(True, value=z)


def validate_price_range(min_raw, max_raw, allow_zero_min=False, kind="budget") -> ValidationResult:
    """
    kind: 'budget' (buying) or 'range' (selling) — only affects error copy.
    """
    try:
        min_val = Decimal(re.sub(r"[^\d.]", "", str(min_raw))) if min_raw not in (None, "") else None
        max_val = Decimal(re.sub(r"[^\d.]", "", str(max_raw))) if max_raw not in (None, "") else None
    except InvalidOperation:
        return ValidationResult(False, message="Please enter numeric dollar amounts.")

    if min_val is None or max_val is None:
        return ValidationResult(False, message="Please enter both minimum and maximum values.")

    if min_val < 0 or max_val < 0:
        return ValidationResult(False, message="Negative amounts are not allowed.")

    if kind == "budget" and min_val == 0:
        return ValidationResult(False, message="Zero is not accepted as a buying budget.")

    if max_val <= min_val:
        label = "buying budget" if kind == "budget" else "expected selling price"
        return ValidationResult(
            False, message=f"The maximum {label} must be greater than the minimum {label}."
        )

    needs_confirmation = max_val >= Decimal("5000000")  # configurable threshold
    return ValidationResult(True, value={"min": float(min_val), "max": float(max_val),
                                          "needs_confirmation": needs_confirmation})


def validate_funding_numbers(purchase_price, renovation_budget, estimated_arv, requested_funding) -> ValidationResult:
    """
    Doc 2 §18: purchase price > 0; renovation budget >= 0; ARV should require
    confirmation when lower than purchase price + repairs; unrealistic
    combinations are flagged for human review rather than rejected outright.
    """
    def to_decimal(v):
        if v in (None, ""):
            return None
        try:
            return Decimal(re.sub(r"[^\d.]", "", str(v)))
        except InvalidOperation:
            return None

    price = to_decimal(purchase_price)
    reno = to_decimal(renovation_budget)
    arv = to_decimal(estimated_arv)
    requested = to_decimal(requested_funding)

    if price is None or price <= 0:
        return ValidationResult(False, message="Purchase price must be greater than zero.")

    if reno is not None and reno < 0:
        return ValidationResult(False, message="Renovation budget cannot be negative.")

    if requested is not None and requested < 0:
        return ValidationResult(False, message="Requested funding amount cannot be negative.")

    flagged = False
    flag_reason = None
    if arv is not None and reno is not None:
        combined = price + reno
        if arv < combined:
            flagged = True
            flag_reason = "Estimated ARV is lower than purchase price plus renovation budget."

    return ValidationResult(True, value={
        "purchase_price": float(price),
        "renovation_budget": float(reno) if reno is not None else None,
        "estimated_arv": float(arv) if arv is not None else None,
        "requested_funding": float(requested) if requested is not None else None,
        "flagged": flagged,
        "flag_reason": flag_reason,
    })


def is_us_state(city: str, state: str) -> bool:
    """Placeholder for a real city/state/ZIP gazetteer lookup (e.g. USPS or Zippopotam.us API)."""
    return state.upper() in US_STATE_CODES


def lookup_us_zip(zip_code: str) -> ValidationResult:
    """Look up a US ZIP code and return official city/state suggestions.

    The public API is used only as an enhancement. If it is temporarily
    unavailable, the lead flow can continue with manual-review status.
    """
    zip_result = validate_zip(zip_code)
    if not zip_result.valid:
        return zip_result
    normalized_zip = zip_result.value[:5]
    if normalized_zip == "00000":
        return ValidationResult(False, message="Please enter a valid US ZIP code.")

    if not current_app.config.get("REMOTE_ZIP_VALIDATION", True):
        return ValidationResult(
            True,
            value={
                "zip": zip_result.value, "state": None, "state_name": None,
                "places": [], "validation_status": "Requires Manual Review",
            },
        )

    url = f"https://api.zippopotam.us/us/{urllib.parse.quote(normalized_zip)}"
    try:
        with urllib.request.urlopen(
            url, timeout=current_app.config.get("ZIP_VALIDATION_TIMEOUT", 4.0)
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        places = payload.get("places", [])
        if not places:
            return ValidationResult(False, message="This ZIP code could not be verified as a valid US ZIP code.")
        state = (places[0].get("state abbreviation") or "").upper()
        names = list(dict.fromkeys(p.get("place name", "").strip() for p in places if p.get("place name")))
        return ValidationResult(
            True,
            value={
                "zip": zip_result.value,
                "state": state,
                "state_name": places[0].get("state"),
                "places": names,
                "validation_status": "Validated",
            },
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return ValidationResult(False, message="This ZIP code could not be verified as a valid US ZIP code.")
        return ValidationResult(
            True,
            value={
                "zip": zip_result.value, "state": None, "state_name": None,
                "places": [], "validation_status": "Requires Manual Review",
            },
            message="The ZIP lookup service is temporarily unavailable. Please enter the city and state manually.",
        )
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return ValidationResult(
            True,
            value={
                "zip": zip_result.value, "state": None, "state_name": None,
                "places": [], "validation_status": "Requires Manual Review",
            },
            message="The ZIP lookup service is temporarily unavailable. Please enter the city and state manually.",
        )


def validate_location(city: str, state_code: str, zip_code: str) -> ValidationResult:
    city_value = re.sub(r"\s+", " ", (city or "").strip())
    city_key = city_value.lower().strip(" .")
    letter_count = len(re.sub(r"[^A-Za-z]", "", city_value))
    if (
        letter_count < 2
        or not re.match(r"^[A-Za-z .'-]+$", city_value)
        or city_key in REJECTED_CITY_TOKENS
    ):
        return ValidationResult(False, message="Please enter a real US city name, not a country or general location.")

    state_result = validate_state(state_code)
    if not state_result.valid:
        return state_result
    if city_key in {state_result.value.lower(), US_STATE_NAMES[state_result.value].lower()}:
        return ValidationResult(False, message="Please enter the city name separately from the state.")

    lookup = lookup_us_zip(zip_code)
    if not lookup.valid:
        return lookup

    normalized_state = state_result.value
    lookup_value = lookup.value or {}
    result = {
        "city": city_value.title(),
        "state": normalized_state,
        "zip": lookup_value.get("zip") or (zip_code or "").strip(),
        "county": None,
        "validated": False,
        "validation_status": lookup_value.get("validation_status", "Requires Manual Review"),
        "matched_places": lookup_value.get("places", []),
    }

    official_state = lookup_value.get("state")
    if official_state and official_state != normalized_state:
        return ValidationResult(False, message="The ZIP code does not appear to match the selected state.")

    names = lookup_value.get("places", [])
    if names:
        exact = next((name for name in names if _city_equivalent(city_value, name)), None)
        if not exact:
            return ValidationResult(
                False,
                message="The ZIP code does not appear to match the entered city and state.",
                suggestion=names[0],
            )
        result["city"] = exact
        result["validated"] = True
        result["validation_status"] = "Validated"

    return ValidationResult(True, value=result, message=lookup.message)


def _city_equivalent(left: str, right: str) -> bool:
    def norm(value):
        value = (value or "").lower().strip()
        replacements = {
            "saint": "st", "fort": "ft", "mount": "mt",
            "township": "twp", "centre": "center",
        }
        for source, target in replacements.items():
            value = re.sub(rf"\b{source}\b", target, value)
        value = re.sub(r"\bcity\b$", "", value).strip()
        return re.sub(r"[^a-z0-9]", "", value)
    return norm(left) == norm(right)


def validate_contact_preference(day: str, time_value: str, time_zone: str) -> ValidationResult:
    allowed_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "No Preference"}
    canonical_times = {
        "9:00 am to 11:00 am": "9:00 AM to 11:00 AM",
        "11:00 am to 1:00 pm": "11:00 AM to 1:00 PM",
        "1:00 pm to 3:00 pm": "1:00 PM to 3:00 PM",
        "3:00 pm to 5:00 pm": "3:00 PM to 5:00 PM",
        "any time during business hours": "Any Time During Business Hours",
        "no preference": "No Preference",
    }
    clean_day = (day or "").strip().title()
    clean_time = re.sub(r"\s+", " ", (time_value or "").strip())
    clean_zone = (time_zone or "").strip()
    if clean_day not in allowed_days:
        return ValidationResult(False, message="Please select an available callback day.")

    # Accept the approved time ranges regardless of text casing. This also keeps
    # older saved sessions valid when they contain uppercase 'TO'.
    canonical_time = canonical_times.get(clean_time.lower())
    if canonical_time is None:
        custom_match = re.fullmatch(r"(0?[1-9]|1[0-2]):([0-5][0-9])\s*(AM|PM)", clean_time, re.I)
        if not custom_match:
            return ValidationResult(False, message="Please select an available callback time or enter a valid time such as 2:30 PM.")
        canonical_time = f"{int(custom_match.group(1))}:{custom_match.group(2)} {custom_match.group(3).upper()}"

    if not clean_zone:
        return ValidationResult(False, message="Please confirm your callback time zone.")
    return ValidationResult(True, value={"day": clean_day, "time": canonical_time, "time_zone": clean_zone})


def validate_url(raw: str) -> ValidationResult:
    value = (raw or "").strip()
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return ValidationResult(False, message="Please enter a valid http or https link.")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ValidationResult(False, message="Please enter a valid link beginning with http:// or https://.")
    if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return ValidationResult(False, message="Local or private links cannot be submitted.")
    return ValidationResult(True, value=value)
