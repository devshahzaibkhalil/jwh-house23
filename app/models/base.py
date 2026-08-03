import uuid
from datetime import datetime, timezone
from app import db


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


def gen_reference(prefix="JWH"):
    """Human-facing submission reference, e.g. JWH-9F3A2C1B"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
