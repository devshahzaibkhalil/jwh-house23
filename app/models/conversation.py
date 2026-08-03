from app import db
from app.models.base import TimestampMixin, gen_uuid


class Conversation(db.Model, TimestampMixin):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    session_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=True)

    # --- State-machine tracking ---
    current_step = db.Column(db.String(60), default="welcome")
    flow_type = db.Column(db.String(30), nullable=True)  # buy | sell | buy_and_sell | faq | funding
    state_data = db.Column(db.JSON, default=dict)  # in-progress answers before Lead is created

    faq_category = db.Column(db.String(60), nullable=True)
    questions_viewed = db.Column(db.JSON, default=list)

    status = db.Column(db.String(20), default="active")  # active | completed | abandoned
    completed_at = db.Column(db.DateTime, nullable=True)

    messages = db.relationship(
        "Message", backref="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
