# Deploying to Render + Embedding as an iFrame

This package has been cleaned up for deployment (no `venv/`, no `.git/`, no
`__pycache__`, no local database, no `.env` with real credentials). No app
code was changed — only deployment files were added:

- `Procfile`
- `render.yaml`
- `gunicorn` added to `requirements.txt`
- this guide

## 1. Push to GitHub

```bash
cd jwh-chatbot-professional-v18
git init
git add .
git commit -m "Initial deploy-ready commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

(`.gitignore` already excludes `venv/`, `.env`, and the database, so you
won't accidentally commit secrets.)

## 2. Create the service on Render

**Option A — Blueprint (recommended, uses `render.yaml`):**
1. Go to https://dashboard.render.com → **New** → **Blueprint**.
2. Connect the GitHub repo you just pushed.
3. Render reads `render.yaml` and creates the web service + a small persistent
   disk automatically.
4. You'll be prompted to fill in the env vars marked `sync: false`:
   - `OWNER_EMAIL`
   - `RESEND_API_KEY`
   - `MAIL_DEFAULT_SENDER`
   - `ADMIN_BASE_URL` → set this to your final Render URL, e.g.
     `https://jwh-chatbot.onrender.com`

**Option B — Manual web service:**
1. **New** → **Web Service** → connect the repo.
2. Runtime: Python 3.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python seed.py && gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
5. Add the same environment variables listed in `render.yaml` under the
   **Environment** tab.
6. Add a **Disk** (Settings → Disks) mounted at `/opt/render/project/data`
   so the SQLite database isn't wiped on every deploy/restart, and set
   `DATABASE_URL=sqlite:////opt/render/project/data/jwh.db`.

## 3. About email delivery

Email is sent through the **Resend HTTPS API**, not SMTP. Render (and most
PaaS hosts) block outbound SMTP ports 25/465/587 on free instances, and
block port 25 entirely even on paid instances, so an HTTPS API call is used
instead — no extra dependency, and it works on Render's free plan.

1. Create a free account at https://resend.com and generate an API key at
   https://resend.com/api-keys.
2. Verify a sending domain at https://resend.com/domains (add the SPF/DKIM
   DNS records it gives you) so you can send from an address like
   `noreply@yourdomain.com`.
3. In Render's environment settings, set:
   - `RESEND_API_KEY` → the key from step 1
   - `MAIL_DEFAULT_SENDER` → the verified address from step 2
   - `OWNER_EMAIL` → where new-lead notifications should go

See `RESEND_SETUP.txt` for the full walkthrough and troubleshooting.
After deploying, run `python test_email.py` locally (with the same env
vars set) or use the "Send test email" action in Admin → Security Centre
to confirm delivery.

## 4. First login / admin account

`seed.py` runs automatically on each deploy (see `Procfile`) and creates the
tables plus a default owner account **only if one doesn't exist yet**:

- email: `owner@jameswholesalehomes.com`
- password: `correct horse battery staple long passphrase`

**Log in immediately after your first deploy and change this password** —
it's a placeholder from the original codebase, not something new added here.

## 5. Embedding the chatbot in an iframe

The app already ships with the CSP support needed for iframe embedding
(`CHAT_FRAME_ANCESTORS` in `config.py`). Two options:

**A. Allow only your own site (recommended):**
Set the env var on Render:
```
CHAT_FRAME_ANCESTORS='self' https://your-real-website.com
```

**B. Allow embedding anywhere (what `render.yaml` sets by default):**
```
CHAT_FRAME_ANCESTORS=*
```
Only use `*` if you're fine with anyone being able to iframe your chatbot.

Then, on the page where you want the widget, add:

```html
<iframe
  src="https://jwh-chatbot.onrender.com"
  style="border:0; width:400px; height:600px;"
  title="James Wholesale Homes Chat"
  loading="lazy">
</iframe>
```

Adjust width/height to taste — the chat widget itself is a floating
bubble + panel, so a small iframe positioned in a corner of your page (via
CSS `position: fixed`) usually looks best, e.g.:

```html
<iframe
  src="https://jwh-chatbot.onrender.com"
  style="position:fixed; bottom:0; right:0; width:420px; height:640px;
         border:0; z-index:9999; background:transparent;"
  title="Chat widget"
  loading="lazy">
</iframe>
```

## 6. Notes

- Render's **free plan** spins the service down after inactivity, so the
  first message after idle time will be slow (cold start, 30–60s).
- The Admin dashboard is at `/admin` and is deliberately **not**
  iframe-able (`X-Frame-Options: DENY`) even if `CHAT_FRAME_ANCESTORS` is
  wide open — only the public chat widget is embeddable.
