from app import db
from app.models.base import TimestampMixin, gen_uuid

EXIT_STRATEGIES = [
    "Fix and Flip (Resale)", "Buy and Hold Refinance (BRRRR)",
    "Long-Term Rental", "Wholesale Assignment", "New Construction Sale", "Other",
]


class FundingDetails(db.Model, TimestampMixin):
    __tablename__ = "funding_details"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey("leads.id"), nullable=False)

    business_name = db.Column(db.String(150), nullable=True)

    property_type = db.Column(db.String(50), nullable=True)
    street_address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)

    purchase_price = db.Column(db.Numeric(12, 2), nullable=True)
    renovation_budget = db.Column(db.Numeric(12, 2), nullable=True)
    estimated_arv = db.Column(db.Numeric(12, 2), nullable=True)
    requested_funding = db.Column(db.Numeric(12, 2), nullable=True)
    borrower_contribution = db.Column(db.Numeric(12, 2), nullable=True)

    exit_strategy = db.Column(db.String(60), nullable=True)
    experience_summary = db.Column(db.Text, nullable=True)
    expected_closing_date = db.Column(db.Date, nullable=True)

    # Flags raised by validation logic — surfaced to staff, never auto-decided.
    flagged_for_review = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(255), nullable=True)
