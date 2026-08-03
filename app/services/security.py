"""Password hashing and password-policy helpers for administrator access."""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

# Minimal blocklist stub — in production, check against a real breached-password
# corpus (e.g. Have I Been Pwned k-anonymity API) and reject company-name variants.
COMMON_PASSWORD_SNIPPETS = {
    "password", "letmein", "qwerty", "123456", "iloveyou",
    "jameswholesalehomes", "wholesalehomes",
}


def validate_password_policy(password: str) -> tuple[bool, str | None]:
    """NIST-aligned: length-focused, no forced composition rules."""
    if len(password) < 15:
        return False, "Password must be at least 15 characters long."
    if len(password) > 128:
        return False, "Password must be 128 characters or fewer."

    lowered = password.lower().replace(" ", "")
    for snippet in COMMON_PASSWORD_SNIPPETS:
        if snippet in lowered:
            return False, "This password is too common or too easy to guess. Please choose another."

    return True, None


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _ph.check_needs_rehash(password_hash)


