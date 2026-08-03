from app import db
from app.models.base import TimestampMixin, gen_uuid

AUDIT_EVENT_TYPES = [
    "login_success", "login_failed", "logout", "account_locked", "account_unlocked",
    "mfa_enabled", "mfa_disabled", "password_changed",
    "lead_exported", "lead_deleted", "leads_bulk_exported",
    "admin_created", "role_changed", "session_revoked",
    "security_setting_changed", "recovery_codes_viewed",
]


class AuditLog(db.Model, TimestampMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    user_email = db.Column(db.String(255), nullable=True)  # denormalized so it survives user deletion

    event_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    resolved = db.Column(db.Boolean, default=True)  # False for events needing admin review
