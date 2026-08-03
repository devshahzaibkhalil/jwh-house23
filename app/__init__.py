import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[env])

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # --- Models must be imported before creating tables ---
    from app.models import (  # noqa: F401
        user, lead, property_details, buyer_criteria,
        conversation, message, file as file_model,
        project, email_log, faq_item, audit_log, funding_details,
        public_statistic, featured_location,
    )

    # --- Blueprints ---
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.path.startswith("/admin"):
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            )
        else:
            frame_ancestors = app.config.get("CHAT_FRAME_ANCESTORS", "'self'")
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; "
                f"frame-ancestors {frame_ancestors}; base-uri 'self'; form-action 'self'",
            )
        if app.config.get("FORCE_HTTPS"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.shell_context_processor
    def make_shell_context():
        return {"db": db}

    return app
