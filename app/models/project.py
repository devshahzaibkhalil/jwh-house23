from app import db
from app.models.base import TimestampMixin, gen_uuid


class Project(db.Model, TimestampMixin):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)

    project_category = db.Column(db.String(40), nullable=True)  # purchase | sale | renovation | land | commercial
    property_type = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    public_location = db.Column(db.String(150), nullable=True)  # e.g. "Saint Francis, Minnesota" (no full address)

    status = db.Column(
        db.String(30), default="Draft"
    )  # Draft | Published | Recently Purchased | Recently Sold | Available |
       # Under Contract | Renovation in Progress | Completed | Archived

    description = db.Column(db.Text, nullable=True)
    private_notes = db.Column(db.Text, nullable=True)  # never exposed publicly

    completion_date = db.Column(db.Date, nullable=True)
    featured = db.Column(db.Boolean, default=False)
    image_paths = db.Column(db.JSON, default=list)

    related_lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=True)


    def to_public_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "project_category": self.project_category,
            "property_type": self.property_type,
            "city": self.city,
            "state": self.state,
            "public_location": self.public_location,
            "status": self.status,
            "description": self.description,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "featured": self.featured,
            "image_paths": self.image_paths or [],
        }
