from app import db
from app.models.base import TimestampMixin, gen_uuid, gen_reference

# --- Reference vocab (Doc 1 §13 / Doc 2 §26) -------------------------------

LEAD_TYPES = [
    "buyer", "seller", "buy_and_sell", "investor_network",
    "funding_applicant", "joint_venture", "general_enquiry",
]

CLIENT_CLASSIFICATIONS = [
    "Property Seller", "Property Buyer", "Buyer and Seller", "Cash Investor",
    "Fix-and-Flip Investor", "Buy-and-Hold Investor", "Rental Property Owner",
    "Landowner", "Commercial Investor", "Wholesale Buyer", "Funding Applicant",
    "Joint Venture Applicant", "Agent or Broker", "Contractor", "General Enquiry",
]

QUALIFICATION_LEVELS = [
    "New", "Contact Information Incomplete", "Contact Information Verified",
    "Basic Qualification Complete", "Qualified", "High Priority",
    "Human Review Required", "Appointment Scheduled", "Offer Requested",
    "Under Contract", "Closed", "Long-Term Follow-Up", "Unqualified", "Spam",
]

SERVICE_AREA_STATUS = [
    "In Primary Service Area", "In Extended Service Area",
    "Outside Current Service Area", "Requires Manual Review",
]


class Lead(db.Model, TimestampMixin):
    __tablename__ = "leads"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    reference_number = db.Column(db.String(20), unique=True, default=gen_reference, index=True)

    session_id = db.Column(db.String(36), db.ForeignKey("conversations.session_id"), nullable=True)

    lead_type = db.Column(db.String(30), nullable=False)  # see LEAD_TYPES
    client_classification = db.Column(db.String(50), nullable=True)
    qualification_level = db.Column(db.String(50), default="New")
    service_area_status = db.Column(db.String(50), nullable=True)

    # --- Contact info ---
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20), nullable=False)  # stored E.164, e.g. +17633338501
    phone_verified = db.Column(db.Boolean, default=False)

    # --- Contact preferences ---
    preferred_contact_day = db.Column(db.String(20), nullable=True)
    preferred_contact_time = db.Column(db.String(30), nullable=True)
    preferred_time_zone = db.Column(db.String(40), nullable=True)
    consent_call = db.Column(db.Boolean, default=False)
    consent_text = db.Column(db.Boolean, default=False)
    consent_email = db.Column(db.Boolean, default=False)

    # --- Free-text question ---
    user_question = db.Column(db.Text, nullable=True)
    submitted_links = db.Column(db.JSON, default=list)

    # --- Workflow ---
    status = db.Column(db.String(40), default="New")
    priority = db.Column(db.String(20), default="Normal")  # Normal | High | Urgent
    assigned_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    # --- Relationships ---
    property_details = db.relationship(
        "PropertyDetails", backref="lead", uselist=False, cascade="all, delete-orphan"
    )
    buyer_criteria = db.relationship(
        "BuyerCriteria", backref="lead", uselist=False, cascade="all, delete-orphan"
    )
    files = db.relationship("UploadedFile", backref="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.reference_number} {self.lead_type} {self.full_name}>"
