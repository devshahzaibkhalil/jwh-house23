from app import db
from app.models.base import TimestampMixin, gen_uuid

INTENDED_USE = [
    "Primary residence", "Fix and flip", "Long-term rental", "Short-term rental",
    "Buy and hold", "Commercial operation", "Development",
    "Wholesale purchase", "Not decided",
]

FUNDING_METHODS = [
    "Cash", "Bank Financing", "Private Money", "Hard-Money Financing",
    "Joint Venture", "Seller Financing", "Not Decided",
]

PURCHASE_TIMELINES = [
    "Immediately", "Within 30 Days", "Within 60 Days",
    "Within 90 Days", "Within Six Months", "Researching Only",
]


class BuyerCriteria(db.Model, TimestampMixin):
    __tablename__ = "buyer_criteria"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=False)

    property_types = db.Column(db.String(255), nullable=True)  # comma-separated, multi-select allowed

    preferred_city = db.Column(db.String(100), nullable=True)
    preferred_state = db.Column(db.String(2), nullable=True)
    preferred_zip = db.Column(db.String(10), nullable=True)
    preferred_county = db.Column(db.String(100), nullable=True)
    additional_cities = db.Column(db.String(255), nullable=True)
    search_radius_miles = db.Column(db.Integer, nullable=True)
    nearby_markets_ok = db.Column(db.Boolean, nullable=True)

    budget_min = db.Column(db.Numeric(12, 2), nullable=True)
    budget_max = db.Column(db.Numeric(12, 2), nullable=True)
    budget_not_finalised = db.Column(db.Boolean, default=False)

    intended_use = db.Column(db.String(40), nullable=True)
    funding_method = db.Column(db.String(30), nullable=True)
    purchase_timeline = db.Column(db.String(30), nullable=True)

    # --- Type-specific specs (kept flexible as JSON-ish text; could normalize later) ---
    min_bedrooms = db.Column(db.Integer, nullable=True)
    min_bathrooms = db.Column(db.Float, nullable=True)
    min_sqft = db.Column(db.Integer, nullable=True)
    max_repair_level = db.Column(db.String(30), nullable=True)
    min_acreage = db.Column(db.Float, nullable=True)
    max_acreage = db.Column(db.Float, nullable=True)
    zoning_preference = db.Column(db.String(60), nullable=True)
    min_building_area = db.Column(db.Integer, nullable=True)
    loading_docks_required = db.Column(db.Boolean, nullable=True)
