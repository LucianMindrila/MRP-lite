# MRP-lite

Lightweight MRP web app for DT Solutions Ltd. Goal: single system running the entire business — order intake through to invoicing — replacing paper, Excel, Smartsheet and QuickBooks with one centralised tool.

**Repo:** https://github.com/LucianMindrila/MRP-lite
**Status:** Active development

## Tech Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy, Flask-Migrate
- **Database:** SQLite (default) — `instance/mrp.db`; PostgreSQL optional
- **Frontend:** Jinja2 templates, HTML, CSS, vanilla JavaScript
- **Deployment:** Docker / Docker Compose available

## Running Locally

```bash
venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade      # first time only
flask seed            # optional: creates admin/operator users + sample data
flask run             # http://localhost:5000
```

**.env file required (gitignored — create manually):**
```
FLASK_ENV=development
SECRET_KEY=any-random-string
DB_PASSWORD=localtest123
COMPANY_NAME=DT Solutions Ltd
COMPANY_ADDRESS=Units 3-4 Pearce Way, Gloucester, GL2 5YD
COMPANY_VAT_NUMBER=GB 000 0000 00
```

## Login Credentials (development)

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Operator | `operator` | `operator123` |

## Project Structure

```
app.py              Application factory
config.py           Dev/production config
models.py           All SQLAlchemy models
mrp_engine.py       MRP calculation logic
routes/             Blueprint modules
  auth.py           Login/logout
  dashboard.py      Admin dashboard
  inventory/        Materials, products, BOMs, suppliers, customers, categories
  orders.py         Sales orders
  purchasing.py     Purchase orders, goods-in
  warehouse.py      Stock checks, batch/location tracking, stock moves
  operator.py       Tablet-friendly operator UI
  documents.py      Delivery notes, invoices, work orders
  reports.py        Order history, shopping list
templates/          Jinja2 HTML templates (mirrors routes)
migrations/         Flask-Migrate migration files
scripts/            One-off seed/import utility scripts
static/             CSS, JS, images
```

## Current Build Status

See `docs/build-plan.md` for what's built, what's in progress, and what's next.

## Business Context

See `docs/business-context.md` for the full DT Solutions business flow, pain points, and what this app is replacing.

## Working with Lucian

- Non-developer, business/product owner. Discuss approach before significant work; explain decisions in plain language.
- Once aligned, execute autonomously.
- Actively learning — brief "why" explanations are welcome.
