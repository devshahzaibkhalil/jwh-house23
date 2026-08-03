from app import db
from app.models.base import TimestampMixin, gen_uuid


class UploadedFile(db.Model, TimestampMixin):
    __tablename__ = "files"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)  # randomized on disk
    file_type = db.Column(db.String(10), nullable=False)
    document_category = db.Column(db.String(60), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)  # outside public web root

    scan_status = db.Column(db.String(20), default="pending")  # pending | clean | infected | error
    scanned_at = db.Column(db.DateTime, nullable=True)
