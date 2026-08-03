from app import db
from app.models.base import TimestampMixin, gen_uuid

PROPERTY_TYPES_PRIMARY = [
    "Single-Family Home", "Apartment", "Multifamily Property",
    "Commercial Property", "Warehouse", "Vacant Land",
]

PROPERTY_TYPES_EXTENDED = [
    "Condominium", "Townhouse", "Duplex", "Triplex", "Fourplex",
    "Apartment Building", "Mobile or Manufactured Home", "Rental Property",
    "Tenant-Occupied Property", "Office Building", "Retail Property",
    "Industrial Property", "Mixed-Use Property", "Medical Building",
    "Agricultural Land", "Farm or Ranch", "Development Land",
    "Storage Facility", "Hospitality Property", "Car Wash", "Other",
]

OWNERSHIP_STATUS = [
    "I am the sole owner", "I am a joint owner", "I represent the owner",
    "The property was inherited", "The property is in probate",
    "The property belongs to an estate", "I am not sure",
]

OCCUPANCY_STATUS = [
    "Owner occupied", "Tenant occupied", "Vacant",
    "Partially occupied", "Under renovation", "Unknown",
]

CONDITION_STATUS = [
    "Excellent", "Good", "Needs cosmetic updates", "Needs minor repairs",
    "Needs major repairs", "Fire damaged", "Water damaged",
    "Structural concerns", "Condemned", "Unknown",
]

TRANSACTION_CLASSIFICATION = [
    "Wanted to Buy", "Wanted to Sell", "Buy and Sell", "Recently Purchased",
    "Recently Sold", "Available", "Under Review", "Under Contract",
    "Renovation in Progress", "Rental", "Wholesale Assignment",
    "Funding Review", "Closed", "Archived",
]


class PropertyDetails(db.Model, TimestampMixin):
    """Represents the subject property for SELL / current-property-in-buy-and-sell flows."""
    __tablename__ = "property_details"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=False)

    property_type = db.Column(db.String(50), nullable=True)
    secondary_property_type = db.Column(db.String(50), nullable=True)

    # --- Location ---
    street_address = db.Column(db.String(255), nullable=True)
    unit_number = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    county = db.Column(db.String(100), nullable=True)
    parcel_number = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address_validation_status = db.Column(db.String(30), nullable=True)

    # --- Ownership / condition ---
    ownership_status = db.Column(db.String(60), nullable=True)
    occupancy_status = db.Column(db.String(30), nullable=True)
    condition_status = db.Column(db.String(40), nullable=True)

    # --- Selling range ---
    selling_min = db.Column(db.Numeric(12, 2), nullable=True)
    selling_max = db.Column(db.Numeric(12, 2), nullable=True)
    needs_value_estimate = db.Column(db.Boolean, default=False)

    # --- Mortgage / liens ---
    has_mortgage = db.Column(db.Boolean, nullable=True)
    mortgage_balance = db.Column(db.Numeric(12, 2), nullable=True)
    has_liens = db.Column(db.Boolean, nullable=True)
    taxes_current = db.Column(db.Boolean, nullable=True)
    in_foreclosure = db.Column(db.Boolean, nullable=True)
    tenants_in_place = db.Column(db.Boolean, nullable=True)
    repairs_needed = db.Column(db.Boolean, nullable=True)
    has_listing_agreement = db.Column(db.Boolean, nullable=True)
    under_contract = db.Column(db.Boolean, nullable=True)

    selling_reason = db.Column(db.Text, nullable=True)
    selling_timeline = db.Column(db.String(40), nullable=True)
    desired_close_date = db.Column(db.Date, nullable=True)

    transaction_classification = db.Column(db.String(40), nullable=True)
