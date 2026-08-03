from app import db
from app.models.base import TimestampMixin, gen_uuid


class PublicStatistic(db.Model, TimestampMixin):
    __tablename__ = "public_statistics"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    label = db.Column(db.String(120), nullable=False)
    public_value = db.Column(db.String(40), nullable=False)
    actual_verified_value = db.Column(db.Integer, nullable=True)
    verification_source = db.Column(db.String(255), nullable=True)
    verification_note = db.Column(db.Text, nullable=True)
    verified_by = db.Column(db.String(120), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=False)

    def to_public_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "value": self.public_value,
        }
