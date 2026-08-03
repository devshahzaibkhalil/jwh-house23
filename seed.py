"""
Run once to create tables and a first Owner admin account:
    python seed.py
"""
from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.services import security

app = create_app("development")

with app.app_context():
    db.create_all()

    existing = User.query.filter_by(email="owner@jameswholesalehomes.com").first()
    if not existing:
        password = "correct horse battery staple long passphrase"  # CHANGE before real use
        ok, err = security.validate_password_policy(password)
        assert ok, err

        owner = User(
            name="James Hamberg",
            email="owner@jameswholesalehomes.com",
            role="owner",
            password_hash=security.hash_password(password),
            mfa_enabled=False,  # retained for database compatibility; MFA is not used
        )
        db.session.add(owner)
        db.session.commit()
        print(f"Created owner account: {owner.email} / password: {password}")
    else:
        print("Owner account already exists.")


    # Public recent-project gallery used by the chatbot.
    # This block is idempotent, so running seed.py updates the same six records.
    recent_projects = [
        {
            "slug": "recent-residential-estate-amenities",
            "title": "Residential Estate with Outdoor Amenities",
            "property_type": "Single-Family Home",
            "description": "A spacious residential setting featuring landscaped grounds, a swimming pool and a private recreation court.",
            "image": "/static/img/projects/recent-project-1.webp",
        },
        {
            "slug": "recent-blue-exterior-residence",
            "title": "Blue Exterior Residential Property",
            "property_type": "Single-Family Home",
            "description": "A well-presented residential property with a distinctive exterior, mature landscaping and a welcoming entrance.",
            "image": "/static/img/projects/recent-project-2.webp",
        },
        {
            "slug": "recent-residential-pool-property",
            "title": "Residential Property with Pool",
            "property_type": "Single-Family Home",
            "description": "A residential property centred around a private outdoor pool area and a generous rear living space.",
            "image": "/static/img/projects/recent-project-3.webp",
        },
        {
            "slug": "recent-wooded-residential-property",
            "title": "Wooded Residential Property",
            "property_type": "Single-Family Home",
            "description": "A private residential setting surrounded by mature trees, landscaped grounds and elevated outdoor living areas.",
            "image": "/static/img/projects/recent-project-4.webp",
        },
        {
            "slug": "recent-urban-residential-property",
            "title": "Urban Residential Property",
            "property_type": "Single-Family Home",
            "description": "An urban residential property with traditional character, street access and established neighbourhood surroundings.",
            "image": "/static/img/projects/recent-project-5.webp",
        },
        {
            "slug": "recent-suburban-family-home",
            "title": "Suburban Family Home",
            "property_type": "Single-Family Home",
            "description": "A spacious suburban residence with a broad driveway, attached garage and professionally maintained lawn.",
            "image": "/static/img/projects/recent-project-6.webp",
        },
    ]

    for index, data in enumerate(recent_projects):
        project = Project.query.filter_by(slug=data["slug"]).first()
        if not project:
            project = Project(slug=data["slug"], title=data["title"])
            db.session.add(project)
        project.title = data["title"]
        project.project_category = "residential"
        project.property_type = data["property_type"]
        project.public_location = "Minnesota"
        project.status = "Published"
        project.description = data["description"]
        project.featured = True
        project.image_paths = [data["image"]]

    db.session.commit()
    print("Recent real estate projects are ready.")

    print("Database ready at instance/jwh.db")
