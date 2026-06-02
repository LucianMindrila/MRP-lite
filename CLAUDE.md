# MRP-lite

Lightweight MRP (Material Requirements Planning) web app built for DT Solutions Ltd. Automates inventory control, purchasing, internal documents, and invoicing for a small manufacturing business.

**Repo:** https://github.com/LucianMindrila/MRP-lite
**Status:** Active development

## Tech Stack

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite (default) — `instance/mrp.db`; PostgreSQL optional
- **ORM:** SQLAlchemy + Flask-Migrate
- **Frontend:** Jinja2 templates, HTML, CSS, vanilla JavaScript
- **Deployment:** Docker / Docker Compose available

## Running Locally

```bash
# Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

# First time setup
flask db upgrade             # Create/migrate database
flask seed                   # Create default users + sample data (optional)

flask run                    # http://localhost:5000
```

**Requires a `.env` file in the project root (gitignored — create manually):**
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
models.py           All SQLAlchemy models (single file)
mrp_engine.py       MRP calculation logic
routes/
  auth.py           Login/logout
  dashboard.py      Admin dashboard
  inventory/        Materials, products, BOMs, suppliers, customers, categories
  orders.py         Sales orders
  purchasing.py     Purchase orders, goods-in
  warehouse.py      Stock checks, batch/location tracking, stock moves
  operator.py       Tablet-friendly operator UI
  documents.py      Delivery notes, invoices, work orders
  reports.py        Order history, shopping list
templates/          Jinja2 HTML templates (mirrors routes structure)
migrations/         Flask-Migrate migration files
scripts/            One-off seed/import utility scripts
static/
  css/app.css       Main stylesheet
  css/print.css     Print styles for documents
  js/app.js         Frontend JS
```

## Key Features

- **Inventory** — materials, products, BOMs, suppliers, customers, categories
- **Purchasing** — purchase orders, goods-in booking, over-delivery detection
- **Sales orders** — order management, delivery note creation, dispatch
- **Warehouse** — live stock diff, batch/location tracking, stock moves
- **Operator UI** — tablet-friendly interface for shop floor use
- **Documents** — printable delivery notes, invoices, work orders
- **Reports** — order history, purchasing shopping list

## Planned Integrations

- **QuickBooks API** — sync invoices and purchase orders
- **Smartsheet API** — sync with production scheduling and order capturing

## About the Owner

Lucian Mindrila — owner of DT Solutions Ltd (manufacturing, Gloucester UK). Non-developer, business/product owner directing technical work. Discuss approach before starting significant changes. Explain technical decisions in plain language tied to business impact.
