from app import db
from app.models.base import TimestampMixin, gen_uuid


class Message(db.Model, TimestampMixin):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)

    sender = db.Column(db.String(10), nullable=False)  # 'user' | 'bot'
    message_type = db.Column(db.String(20), default="text")  # text | button | file | link | system
    content = db.Column(db.Text, nullable=False)
    validation_status = db.Column(db.String(20), nullable=True)  # valid | invalid | pending
