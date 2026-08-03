from flask import Blueprint, render_template, current_app

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def index():
    """Demo host page embedding the chat widget (in production this snippet
    would be embedded on the company's real website)."""
    return render_template("index.html", brand=current_app.config["BRAND"])


@chat_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")
