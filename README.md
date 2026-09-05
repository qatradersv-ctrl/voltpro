# VoltPro Electrodata Solutions — company site (Django)

A company website for **VoltPro Electrodata Solutions**: solar installation,
electrical work, building wiring, UPS & clean power, battery/power backup,
fingerprint door access, generator install & repair, electric security
fencing, CCTV, network cabling, control panels, electric sliding gates, and
industrial/commercial switchgear.

## Stack
- Django 5 (project `voltpro`, app `core`)
- Server-rendered templates + one custom stylesheet, no frontend build step
- SQLite by default (swap `DATABASES` in `voltpro/settings.py` for Postgres/MySQL in production)

## What's in the app
- `Service` model — the 13 services, each with its own detail page (`/services/<slug>/`)
- `Project` model — optional "our work" gallery, only renders once you add entries
- `Testimonial` model — client quotes
- `QuoteRequest` model — every "Request a quote" form submission lands here, visible in `/admin/`
- `Quote` + `QuoteLineItem` — formal, numbered quotations (`VP-2026-0001`, auto-numbered)
  with line items, VAT, subtotal/total, a client-facing page, and a branded PDF
- Django admin registered for all models

### Quote-to-close workflow
1. A lead comes in through the site's "Request a quote" form → saved as a `QuoteRequest`,
   visible under **Core > Quote requests** in `/admin/`.
2. Select the lead in admin and run the **"Create a draft quote from selected request(s)"**
   action. This creates a `Quote` (status `draft`) pre-filled with the lead's contact details.
3. Open the quote and add line items in the inline table (description, qty, unit, unit price —
   totals and VAT calculate automatically). Add scope notes and adjust terms if needed.
4. Set status to `sent` when ready. The admin change form shows two links under
   **"Share with client"**:
   - the client-facing quote page (`/quotes/<uuid>/`) — client can accept or decline it there
   - the PDF (`/quotes/<uuid>/pdf/`) — same document, downloadable/printable
   Send either link to the client (email, WhatsApp, SMS — whatever's convenient).
5. When the client clicks **Accept** or **Decline** on the quote page, its status updates
   automatically. You can also create a `Quote` from scratch (no linked `QuoteRequest`) via
   **Core > Quotes > Add**.

Quotes use a UUID (`public_id`) in the client-facing URLs rather than the numeric ID, so a
client can only reach the quote they were sent the link to — there's no login for clients.

## Run it locally
```bash
python -m venv .venv && source .venv/bin/activate     # optional but recommended
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_services        # loads the 13 services + sample testimonials
python manage.py createsuperuser      # for /admin/

python manage.py runserver
```
Visit `http://127.0.0.1:8000/`. Admin is at `http://127.0.0.1:8000/admin/`.

## Editing content
- Service copy, order, and category all live in the admin (`Core > Services`),
  or edit the seed data in `core/management/commands/seed_services.py` and
  re-run `python manage.py seed_services` (it upserts by slug, safe to re-run).
- Contact phone/email/hours are in `templates/core/base.html` (footer) and
  `templates/core/home.html` (contact section) — update both.
- Project photos: add entries under `Core > Projects` in admin and upload an
  image; the "Our work" section only appears once at least one project exists.

## Before going live
- Set `DEBUG = False` and a real `SECRET_KEY` (env var, not hardcoded) in `voltpro/settings.py`.
- Set `ALLOWED_HOSTS` to your domain.
- Point `DATABASES` at Postgres/MySQL for production.
- Run `python manage.py collectstatic` and serve `/static/` via your web server or WhiteNoise.
- Wire the quote form to send you an email/SMS notification on submit (currently it
  only saves to `QuoteRequest` — check `/admin/core/quoterequest/` for leads).
- Swap the placeholder phone number / email in the templates for the real ones.

## Structure
```
voltpro/            project settings, root urls
core/                app: models, views, admin, urls, seed command
templates/core/      base.html, home.html, service_detail.html, _icons.html
static/core/css/     style.css (single stylesheet, no build step)
```
