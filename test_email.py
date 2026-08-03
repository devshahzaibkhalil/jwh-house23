"""Send a test message using the Resend API settings from .env."""
from app import create_app
from app.services.notifications import send_test_email

app = create_app()

with app.app_context():
    success, message = send_test_email()
    print(message)
    raise SystemExit(0 if success else 1)
