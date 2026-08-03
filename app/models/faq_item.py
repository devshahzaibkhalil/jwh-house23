from app import db
from app.models.base import TimestampMixin, gen_uuid

FAQ_CATEGORIES = [
    "About James Wholesale Homes",
    "Selling a House Fast",
    "Buying a Property",
    "Rental and Tenant-Occupied Properties",
    "Off-Market Properties",
    "Wholesale Real Estate",
    "Investor Buyers Network",
    "Property Analysis and Due Diligence",
    "Private Money and Investment Funding",
]


class FaqItem(db.Model, TimestampMixin):
    __tablename__ = "faq_items"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    category = db.Column(db.String(60), nullable=False, index=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
