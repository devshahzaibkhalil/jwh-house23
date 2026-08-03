from flask import request
from app import db
from app.models.audit_log import AuditLog


def log_event(event_type: str, description: str = None, user=None, resolved: bool = True):
    entry = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        event_type=event_type,
        description=description,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get("User-Agent", "")[:255] if request else None,
        resolved=resolved,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
