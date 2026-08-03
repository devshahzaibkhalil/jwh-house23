import os
from datetime import timedelta

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load local email and application settings before Config is evaluated.
# Existing system environment variables take precedence over values in .env.
load_dotenv(os.path.join(basedir, ".env"), override=False)


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'jwh.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Sessions / cookies (admin dashboard) ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)  # admin idle timeout
    SESSION_REFRESH_EACH_REQUEST = True

    # --- Chat embedding / security headers ---
    CHAT_FRAME_ANCESTORS = os.environ.get("CHAT_FRAME_ANCESTORS", "'self'")
    FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "0") == "1"

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(basedir, "instance", "uploads")
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB per request (per-file enforced in code)
    ALLOWED_EXTENSIONS = {
        "pdf", "jpg", "jpeg", "png", "webp",
        "doc", "docx", "xls", "xlsx", "txt",
    }
    MAX_FILES_PER_SUBMISSION = 5

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per hour"

    # --- Branding (Document 1 palette) ---
    BRAND = {
        "background": "#16243E",
        "accent": "#E3562B",
        "text": "#FFFFFF",
        "light_bg": "#FAF7F3",
        "muted_text": "#6B7280",
        "border": "#3A4963",
        "success": "#24705A",
        "error": "#B42318",
    }

    # --- Owner notification email (configurable, never hard-coded in logic) ---
    # OWNER_EMAIL may contain one address or a comma-separated list.
    OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "")
    # Email is sent via the Resend HTTPS API (not SMTP) because Render blocks
    # outbound SMTP ports 25/465/587 on free instances, and blocks port 25
    # entirely even on paid instances. Get a key at https://resend.com/api-keys.
    # MAIL_PROVIDER selects the transport: "mailjet" (default), "smtp2go",
    # "brevo", "sendgrid" or "resend". Leave it unset and the provider is
    # inferred from whichever key is present. Every option except Resend can
    # verify a single sender address by emailing it a confirmation link, so no
    # DNS access or domain ownership is needed. Resend verifies domains only.
    MAIL_PROVIDER = os.environ.get("MAIL_PROVIDER", "")
    SMTP2GO_API_KEY = os.environ.get("SMTP2GO_API_KEY", "")
    MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY", "")
    MAILJET_SECRET_KEY = os.environ.get("MAILJET_SECRET_KEY", "")
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    MAIL_API_KEY = os.environ.get("MAIL_API_KEY", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
    MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "James Wholesale Homes")
    MAIL_TIMEOUT = int(os.environ.get("MAIL_TIMEOUT", 20))
    ADMIN_BASE_URL = os.environ.get("ADMIN_BASE_URL", "http://127.0.0.1:5000")

    # --- Contact verification ---
    CONTACT_OTP_TTL_SECONDS = int(os.environ.get("CONTACT_OTP_TTL_SECONDS", 600))
    CONTACT_OTP_MAX_ATTEMPTS = int(os.environ.get("CONTACT_OTP_MAX_ATTEMPTS", 5))
    SHOW_DEV_OTP = os.environ.get("SHOW_DEV_OTP", "1") == "1"
    SMS_WEBHOOK_URL = os.environ.get("SMS_WEBHOOK_URL", "")
    SMS_WEBHOOK_TOKEN = os.environ.get("SMS_WEBHOOK_TOKEN", "")

    # --- Optional remote US ZIP validation ---
    REMOTE_ZIP_VALIDATION = os.environ.get("REMOTE_ZIP_VALIDATION", "1") == "1"
    ZIP_VALIDATION_TIMEOUT = float(os.environ.get("ZIP_VALIDATION_TIMEOUT", 4.0))


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
