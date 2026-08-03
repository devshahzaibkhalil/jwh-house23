"""Seed and update approved FAQ content used by the public chatbot."""
from app import create_app, db
from app.models.faq_item import FaqItem

SELLER_QUESTIONS = [
    (
        "Can James Wholesale Homes help me sell my house quickly?",
        "James Wholesale Homes evaluates properties for direct or investor-supported purchase opportunities. The actual timeline depends on the title status, property details, required documentation and the closing date selected by the parties.",
    ),
    (
        "How does the home-selling process work?",
        "You provide the property information, the team reviews the opportunity, and an offer or proposed solution may be presented. You can review the terms and decide whether to proceed. There is no obligation until you sign an agreement.",
    ),
    (
        "How do I request an offer?",
        "Complete the seller enquiry with the property address, condition, occupancy and preferred timeline. You may also contact James Wholesale Homes directly by phone or email.",
    ),
    (
        "How soon can I receive an offer?",
        "Some properties can be reviewed quickly. The exact response time depends on the completeness of the information provided, the property type and whether additional title or condition details are required.",
    ),
    (
        "Do I need to make repairs before selling?",
        "Many investor purchases are evaluated without requiring the seller to complete repairs. The property's present condition will normally be considered when the proposed price and terms are prepared.",
    ),
    (
        "Do I need to repaint my house?",
        "Usually not for an as-is sale. Cosmetic condition may influence the property's value, but sellers may be able to avoid repainting or completing other surface improvements before the sale.",
    ),
    (
        "Will I pay a real estate commission?",
        "A direct buyer transaction may not involve a traditional listing commission. Any commission, fee, closing cost or deduction should be clearly disclosed in writing before you sign an agreement.",
    ),
    (
        "Can I sell even if I still have a mortgage?",
        "Yes. The remaining mortgage is generally paid from the closing proceeds, provided the sale price and available funds are sufficient to satisfy the loan and any other liens or closing obligations.",
    ),
    (
        "Can I sell a rental property?",
        "Yes. Be prepared to provide available lease documents, rent history, deposit records, operating expenses and tenant information that may legally be shared for the transaction review.",
    ),
    (
        "Can I sell a property during an eviction?",
        "Possibly. Disclose the current status of the eviction and provide available notices, filings and court documents. The team may need to review the tenancy and legal timeline before discussing possible terms.",
    ),
    (
        "I have land for sale. Can I request an offer?",
        "Yes. Please provide the parcel location, acreage, expected selling range, parcel number when available, road access, zoning and utility information. The team can review those details and determine whether the land fits its current buying criteria.",
    ),
]

BUYER_QUESTIONS = [
    (
        "Can I get a home loan or mortgage easily?",
        "Speak with banks or qualified mortgage professionals to check your eligibility, available interest rates and lending terms. The property must also meet the lender's appraisal and approval requirements before financing can be confirmed.",
    ),
    (
        "What are the association or maintenance fees?",
        "For a condominium, apartment or gated community, confirm the monthly or annual association and maintenance charges. Review exactly what the fees cover, such as exterior maintenance, insurance, amenities, utilities, security or reserve contributions.",
    ),
    (
        "What is the resale value and market trend?",
        "Review comparable sales and neighbourhood price trends from the previous three to five years. Planned infrastructure, employment centres, schools, supply and local demand may influence future resale potential, but appreciation is never guaranteed.",
    ),
    (
        "How long has the property been on the market?",
        "A property that has remained available for an extended period may be overpriced, have condition concerns or simply face limited demand. Ask why it has not sold, review inspections and comparable sales, and use verified findings when negotiating.",
    ),
]

FAQ_SEED = {
    "About James Wholesale Homes": [
        (
            "What is James Wholesale Homes?",
            "James Wholesale Homes connects property sellers, real estate investors and qualified buyers with off-market and wholesale property opportunities. The company may also provide or arrange selected real estate funding solutions, depending on the transaction.",
        ),
        (
            "Where is James Wholesale Homes located?",
            "James Wholesale Homes is based in Saint Francis, Minnesota. Contact the team to confirm the current service area and whether an in-person visit is available by appointment.",
        ),
        (
            "Who is James Hamberg?",
            "James Hamberg is the founder of James Wholesale Homes. He works with property owners, investors, contractors and qualified buyers seeking real estate opportunities.",
        ),
        (
            "How quickly will someone respond?",
            "Response time depends on business hours, enquiry volume and the information provided. The team reviews submitted enquiries during normal business hours and responds as soon as reasonably possible.",
        ),
        (
            "Are you a licensed real estate brokerage?",
            "The company's exact role may vary by transaction. James Wholesale Homes should clearly disclose whether it is acting as a buyer, wholesaler, investor, funding participant or through a licensed professional.",
        ),
        (
            "What areas do you serve?",
            "The business primarily focuses on Minnesota markets and may review enquiries from other US locations on a case-by-case basis.",
        ),
    ],
    "Selling a House Fast": SELLER_QUESTIONS,
    "Buying a Property": BUYER_QUESTIONS,
    "Rental and Tenant-Occupied Properties": [
        ("Can I sell a property with tenants still living there?", "Yes. Tenant-occupied properties can be evaluated, subject to existing leases, tenant rights and applicable law."),
        ("Do you buy rental portfolios?", "The team may consider individual rental properties and selected portfolios, depending on location, condition, occupancy and transaction details."),
    ],
    "Off-Market Properties": [
        ("What is an off-market property?", "An off-market property is offered privately rather than being widely advertised through a public listing service."),
        ("How do I get access to off-market listings?", "Buyers can join the investor network and provide their location, property type, budget and investment criteria for matching opportunities."),
    ],
    "Wholesale Real Estate": [
        ("What is wholesale real estate?", "Wholesale real estate commonly involves securing contractual rights to purchase a property and transferring or selling those rights to another buyer where permitted."),
        ("Do you charge sellers a fee to wholesale their property?", "The transaction structure and any fees should be disclosed in writing before an agreement is signed."),
    ],
    "Investor Buyers Network": [
        ("How do I join the buyers network?", "Select Investor Buyers Network in the chatbot and provide your contact details, preferred locations, property types, budget and investment strategy."),
        ("Is there a cost to join?", "Joining may be available without an upfront fee. Any paid service or premium feature should be disclosed separately before enrolment."),
    ],
    "Property Analysis and Due Diligence": [
        ("What does your due diligence process include?", "A property review may consider title, condition, comparable sales, repair estimates, occupancy, zoning and other transaction risks."),
        ("Can you help estimate repair costs?", "The team may provide a preliminary repair range based on available information, photographs or a walkthrough. Buyers should independently verify all costs."),
    ],
    "Private Money and Investment Funding": [
        ("Do you offer private funding for deals?", "The website promotes private-money and investment-funding solutions for selected projects. The exact lender or transaction role and all terms should be disclosed before an application proceeds."),
        ("What information do you need for a funding application?", "Common information includes the property address, purchase price, renovation budget, estimated after-repair value, requested amount, borrower contribution and exit strategy."),
    ],
}


def run():
    app = create_app("development")
    with app.app_context():
        order = 0
        seeded_questions = {}
        created = 0
        updated = 0

        for category, items in FAQ_SEED.items():
            seeded_questions[category] = {question for question, _ in items}
            for question, answer in items:
                item = FaqItem.query.filter_by(category=category, question=question).first()
                if item is None:
                    item = FaqItem(category=category, question=question)
                    db.session.add(item)
                    created += 1
                else:
                    updated += 1
                item.answer = answer
                item.display_order = order
                item.is_active = True
                order += 1

        # Keep approved FAQ sections synchronised so outdated or duplicate
        # questions no longer appear after an existing database is upgraded.
        for synchronised_category in ("About James Wholesale Homes", "Selling a House Fast", "Buying a Property"):
            approved_questions = seeded_questions[synchronised_category]
            for item in FaqItem.query.filter_by(category=synchronised_category).all():
                if item.question not in approved_questions:
                    item.is_active = False

        db.session.commit()
        total = sum(len(items) for items in FAQ_SEED.values())
        print(f"FAQ update complete: {created} created, {updated} updated, {total} approved items active.")


if __name__ == "__main__":
    run()
