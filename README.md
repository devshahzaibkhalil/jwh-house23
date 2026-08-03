# James Wholesale Homes — Chatbot & Admin Dashboard

A Flask-based real estate lead-qualification chatbot with an admin dashboard,
built from the project blueprint (branding, flows, validation, and security
requirements in Doc 1 / Doc 2).

## What's included

- **Chat widget** (transparent host, floating navy/orange launcher and branded window) driving buy / sell /
  buy-and-sell / funding / investor-network lead flows, plus professional FAQ navigation
  across 8 categories
- **Validation**: name, email (with typo suggestions), US phone, US state/ZIP,
  buying budget / selling range, funding numbers (with ARV sanity flagging)
- **File uploads** with extension allowlist, magic-byte signature checks,
  randomized safe filenames, and a scan-status pipeline
- **Security**: Argon2id password hashing, email/password login, lockout protection and audit logging
  (QR setup + recovery codes), account lockout after failed logins, and an
  audit log
- **Admin dashboard**: leads list/detail, Security Centre, Users & Roles
- **Database**: SQLite by default (swap via `DATABASE_URL`), full schema for
  leads, property details, buyer criteria, funding details, conversations,
  messages, files, FAQ items, projects, email logs, audit logs

## Setup

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database and a first Owner admin account
python seed.py

# 4. Seed or update FAQ content (includes the complete seller-question flow)
python seed_faq.py

# 5. Run the app
python run.py
```

The app runs at **http://127.0.0.1:5000**

- Chat widget-only page: `/` (no demo landing page; suitable for iframe embedding)
- Admin login: `/admin/login`

The seed script prints the owner login credentials — **change this password
immediately in a real deployment**
on first login (mandatory per the security spec, but not force-enforced in
this dev build so you can log in the first time).

## Configuration

Key environment variables (see `config.py` for the full list):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key — set a real random value in production |
| `DATABASE_URL` | e.g. `postgresql://user:pass@host/db` for production |
| `OWNER_EMAIL` | Address that receives new-lead notifications |
| `RESEND_API_KEY`, `MAIL_DEFAULT_SENDER`, `MAIL_SENDER_NAME` | Resend API configuration for automatic lead and confirmation emails |

## Automatic lead email setup

The app sends a notification to `OWNER_EMAIL` immediately after each lead is safely saved. Email is delivered through the [Resend](https://resend.com) HTTPS API rather than SMTP, because Render (and most PaaS hosts) block outbound SMTP ports 25/465/587.

```bat
copy .env.example .env
notepad .env
python test_email.py
python run.py
```

Create a free Resend account, generate an API key at https://resend.com/api-keys, and verify a sending domain at https://resend.com/domains. See `RESEND_SETUP.txt` for the full walkthrough and troubleshooting.

## Project structure

```
app/
  models/         SQLAlchemy models (Lead, PropertyDetails, BuyerCriteria,
                   FundingDetails, Conversation, Message, UploadedFile,
                   FaqItem, Project, EmailLog, User, AuditLog)
  routes/
    chat.py       Widget host page
    api.py        Chat engine endpoints (/api/chat/*)
    admin.py      Admin email/password auth, dashboard and Security Centre
  services/
    chat_engine.py     Conversation step definitions
    validators.py      Field validation (name/email/phone/location/money)
    security.py        Password hashing and password-policy helpers
    file_security.py   Upload validation (extension/MIME/signature)
    notifications.py   Automatic owner/user email via Resend API with delivery logging
    audit.py           Security event logging
  templates/       Jinja2 templates (widget host page + admin UI)
  static/          Widget CSS/JS
config.py          Environment-based configuration
run.py             Entry point
seed.py            Creates tables + first owner account
seed_faq.py         Creates or updates approved FAQ content
requirements.txt
```

## Known simplifications / next steps

- Resend API email delivery is included. Copy `.env.example` to `.env`, add your Resend API key and sender details, and run `python test_email.py`.
- File malware scanning (`run_malware_scan()`) is a placeholder — integrate a
  real AV engine (e.g. ClamAV) before accepting real uploads
- Step 4 now looks up the ZIP first, suggests the official city/state and revalidates the full city/state/ZIP combination before submission. When the remote service is temporarily unavailable, the lead is retained with manual-review status.
- Buy-and-sell flow shares one property-type/location/budget round rather
  than fully separate current-property and target-property rounds
- Public Statistics module and Recent Projects management UI are not yet built
- Session revocation list and CAPTCHA-on-suspicious-activity are not yet built

## Latest welcome-screen changes

The welcome screen now includes five supplied property images in an automatic carousel. Select any image to open its description and start the related buyer, seller, project, investor-network or question flow. Choice cards turn orange on hover and selection. The bottom action area remains docked while messages scroll. ZIP codes are checked for US format and then validated against the selected city and state when the validation service is available.

## Seller question flow

Selecting **Sell a Property** now opens the complete approved seller-question list.
After an answer, the chatbot asks **Are you interested in moving forward?**

- **Yes, Show Remaining Questions** returns only the unanswered seller questions.
- **No, Start Seller Enquiry** begins the validated seller lead form with the full-name step.
- **Start Seller Enquiry** is also available directly from the seller-question list.

Run `python seed_faq.py` after upgrading, even when an existing `instance/jwh.db` is retained. The script now updates existing FAQ records and disables outdated seller questions instead of skipping an already-seeded database.

## Admin login

Start the server and open `http://127.0.0.1:5000/admin/login`. The development seed account is:

- Email: `owner@jameswholesalehomes.com`
- Password: `correct horse battery staple long passphrase`

The admin dashboard uses email and password authentication. Change the development email and password before production deployment.


## V17 browser hotfix
If an older browser tab cached the previous JavaScript, restart the server and press Ctrl+F5. V17 also appends a version query to static assets automatically.
