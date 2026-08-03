from app import db
from app.models.base import TimestampMixin, gen_uuid


class FeaturedLocation(db.Model, TimestampMixin):
    __tablename__ = "featured_locations"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False, default="MN")
    county = db.Column(db.String(100), nullable=True)
    service_tier = db.Column(db.String(30), default="Extended")  # Primary | Extended | Review
    property_categories = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint("city", "state", name="uq_featured_location_city_state"),
    )

    def to_public_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "state": self.state,
            "county": self.county,
            "service_tier": self.service_tier,
            "property_categories": [
                item.strip() for item in (self.property_categories or "").split(",") if item.strip()
            ],
            "description": self.description,
            "image_path": self.image_path,
        }
