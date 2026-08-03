from functools import wraps
from datetime import datetime, timezone, timedelta
import secrets
import re
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app, abort,
)
from app import db, limiter
from app.models.user import User
from app.models.lead import Lead
from app.models.project import Project
from app.models.public_statistic import PublicStatistic
from app.models.featured_location import FeaturedLocation
from app.models.faq_item import FaqItem, FAQ_CATEGORIES
from app.models.email_log import EmailLog
from app.services import security
from app.services.audit import log_event

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def csrf_token():
    token = session.get("admin_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["admin_csrf_token"] = token
    return token


@admin_bp.app_context_processor
def inject_admin_helpers():
    return {"csrf_token": csrf_token}


@admin_bp.before_request
def protect_admin_posts():
    if request.method == "POST":
        submitted = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("admin_csrf_token")
        if not expected or not submitted or not secrets.compare_digest(expected, submitted):
            abort(400, description="Invalid or expired security token.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("admin.login"))
        user = User.query.get(session.get("user_id"))
        if not user or user.account_status == "disabled":
            session.clear()
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


def permission_required(action):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = User.query.get(session.get("user_id"))
            if not user or not user.has_permission(action):
                flash("You do not have permission to access that.", "error")
                return redirect(url_for("admin.dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "GET":
        return render_template("admin/login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    # Constant-time-ish: always run verify_password even on missing user
    # by comparing against a dummy hash, to reduce user-enumeration timing signal.
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    password_ok = security.verify_password(password, user.password_hash if user else dummy_hash)

    # --- Active lockout check (time-based, auto-expires) ---
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        flash(f"This account is temporarily locked. Please try again in about {minutes_left} minute(s).", "error")
        log_event("login_failed", "Login attempt while account locked", user=user, resolved=False)
        return redirect(url_for("admin.login"))

    if not user or not password_ok:
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
                user.account_status = "locked"
                log_event("account_locked",
                           f"Locked after {user.failed_login_count} failed attempts", user=user, resolved=False)
            db.session.commit()
            log_event("login_failed", "Incorrect password", user=user, resolved=False)
        flash("Invalid email or password.", "error")
        return redirect(url_for("admin.login"))

    if user.account_status == "disabled":
        flash("This account has been disabled. Contact the owner for access.", "error")
        return redirect(url_for("admin.login"))

    # --- Success: reset lockout state, rotate session ---
    session.clear()
    session.permanent = True
    session["user_id"] = user.id

    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.remote_addr
    user.failed_login_count = 0
    user.locked_until = None
    if user.account_status == "locked":
        user.account_status = "active"
    db.session.commit()

    log_event("login_success", None, user=user)
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/logout")
def logout():
    user = current_user()
    if user:
        log_event("logout", None, user=user)
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    total_leads = Lead.query.count()
    new_leads = Lead.query.filter_by(status="New").count()
    buyer_leads = Lead.query.filter_by(lead_type="buy").count()
    seller_leads = Lead.query.filter_by(lead_type="sell").count()

    cards = {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "buyer_leads": buyer_leads,
        "seller_leads": seller_leads,
    }
    return render_template("admin/dashboard.html", cards=cards)


@admin_bp.route("/leads")
@login_required
def leads_list():
    status = request.args.get("status")
    lead_type = request.args.get("lead_type")

    query = Lead.query
    if status:
        query = query.filter_by(status=status)
    if lead_type:
        query = query.filter_by(lead_type=lead_type)

    leads = query.order_by(Lead.created_at.desc()).limit(200).all()
    return render_template("admin/leads_list.html", leads=leads)


@admin_bp.route("/leads/<lead_id>")
@login_required
def lead_detail(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return render_template("admin/lead_detail.html", lead=lead)


# ---------------------------------------------------------------------------
# Administrator security centre and account controls
# ---------------------------------------------------------------------------

@admin_bp.route("/security")
@login_required
@permission_required("*")
def security_centre():
    from app.models.audit_log import AuditLog

    recent_events = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    failed_logins_24h = AuditLog.query.filter(
        AuditLog.event_type == "login_failed"
    ).order_by(AuditLog.created_at.desc()).limit(20).all()
    locked_accounts = User.query.filter(User.account_status == "locked").all()
    all_users = User.query.all()
    unresolved = AuditLog.query.filter_by(resolved=False).order_by(AuditLog.created_at.desc()).limit(20).all()

    return render_template(
        "admin/security_centre.html",
        recent_events=recent_events,
        failed_logins=failed_logins_24h,
        locked_accounts=locked_accounts,
        total_users=len(all_users),
        unresolved=unresolved,
    )


@admin_bp.route("/security/unlock/<user_id>", methods=["POST"])
@login_required
@permission_required("*")
def unlock_account(user_id):
    target = User.query.get_or_404(user_id)
    target.account_status = "active"
    target.locked_until = None
    target.failed_login_count = 0
    db.session.commit()
    log_event("account_unlocked", f"Unlocked by {current_user().email}", user=target)
    flash(f"{target.email} has been unlocked.", "success")
    return redirect(url_for("admin.security_centre"))


@admin_bp.route("/security/resolve/<event_id>", methods=["POST"])
@login_required
@permission_required("*")
def resolve_event(event_id):
    from app.models.audit_log import AuditLog
    event = AuditLog.query.get_or_404(event_id)
    event.resolved = True
    db.session.commit()
    return redirect(url_for("admin.security_centre"))



@admin_bp.route("/account-settings", methods=["GET", "POST"])
@login_required
def account_settings():
    user = current_user()

    if request.method == "GET":
        return render_template("admin/account_settings.html", user=user)

    action = request.form.get("action", "").strip()
    current_password = request.form.get("current_password", "")

    if not security.verify_password(current_password, user.password_hash):
        flash("Your current password is incorrect.", "error")
        return redirect(url_for("admin.account_settings"))

    if action == "change_email":
        new_email = request.form.get("new_email", "").strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", new_email):
            flash("Enter a valid email address.", "error")
            return redirect(url_for("admin.account_settings"))
        duplicate = User.query.filter(User.email == new_email, User.id != user.id).first()
        if duplicate:
            flash("That email address is already assigned to another administrator.", "error")
            return redirect(url_for("admin.account_settings"))
        old_email = user.email
        user.email = new_email
        db.session.commit()
        log_event("admin_email_changed", f"Changed from {old_email} to {new_email}", user=user)
        flash("Administrator email updated successfully.", "success")
        return redirect(url_for("admin.account_settings"))

    if action == "change_password":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if new_password != confirm_password:
            flash("The new passwords do not match.", "error")
            return redirect(url_for("admin.account_settings"))
        valid, message = security.validate_password_policy(new_password)
        if not valid:
            flash(message, "error")
            return redirect(url_for("admin.account_settings"))
        if security.verify_password(new_password, user.password_hash):
            flash("Choose a new password that is different from the current password.", "error")
            return redirect(url_for("admin.account_settings"))
        user.password_hash = security.hash_password(new_password)
        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()
        log_event("admin_password_changed", "Password changed from Account Settings", user=user)
        session.clear()
        flash("Password updated successfully. Sign in again with your new password.", "success")
        return redirect(url_for("admin.login"))

    flash("Select an account setting to update.", "error")
    return redirect(url_for("admin.account_settings"))


@admin_bp.route("/users")
@login_required
@permission_required("*")
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users_list.html", users=users)


