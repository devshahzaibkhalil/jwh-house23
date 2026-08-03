from app import db
from app.models.base import TimestampMixin, gen_uuid


class EmailLog(db.Model, TimestampMixin):
    __tablename__ = "email_logs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=True)

    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    delivery_status = db.Column(db.String(20), default="pending")  # pending | sent | failed
    sent_at = db.Column(db.DateTime, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
