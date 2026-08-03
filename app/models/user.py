from app import db
from app.models.base import TimestampMixin, gen_uuid


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)

    role = db.Column(
        db.String(30), nullable=False, default="sales_representative"
    )  # owner | administrator | sales_representative | content_manager

    # --- Password security (Argon2id, see app/services/security.py) ---
    password_hash = db.Column(db.String(255), nullable=False)

    # --- Mandatory MFA ---
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(64), nullable=True)  # encrypted at rest in production
    mfa_recovery_codes_hash = db.Column(db.Text, nullable=True)  # JSON list of hashed codes

    account_status = db.Column(db.String(20), default="active")  # active | locked | disabled
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)

    def has_permission(self, action: str) -> bool:
        """Very small RBAC check — extend per section 24 / 35 of the blueprint."""
        permissions = {
            "owner": {"*"},
            "administrator": {
                "leads.view", "leads.edit", "conversations.view",
                "faq.manage", "projects.manage", "tasks.manage", "staff.assign",
            },
            "sales_representative": {
                "leads.view_assigned", "conversations.view_assigned",
                "notes.add", "callbacks.schedule",
            },
            "content_manager": {
                "faq.manage", "projects.manage", "locations.manage", "content.manage",
            },
        }
        allowed = permissions.get(self.role, set())
        return "*" in allowed or action in allowed

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
