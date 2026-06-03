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

## Factory Layout & Machines

### Units
- **Unit 3 & 4** — same building, separated by a wall. Goods move between U3/4 and U16 by forklift.
- **Unit 16** — across the street from U3-4. Forklift access.
- **Unit 7** — further away. Goods move to/from U7 via 3.5t truck.

### Dispatch locations
- **Unit 7** — mainly Trend products
- **Unit 4** — all Safety Knife, all NuCo, some Trend

### Machines

| Machine | Type | Unit |
|---|---|---|
| Selco SK4 | Beamsaw (sheet cutting) | U4 |
| Raptor U4 | CNC Router | U4 |
| Felder | CNC Router | U4 |
| Raptor U3 | CNC Router | U3 |
| Thermwood 1 | CNC Router | U7 |
| Thermwood 2 | CNC Router | U7 |
| Thermwood 3 | CNC Router | U7 |
| Thermwood 4 | CNC Router | U7 |
| Multicam | CNC Router | U7 |
| Thermwood 5 | CNC Router | U16 |
| Thermwood 6 | CNC Router | U16 |
| Hurco VMC U4 | CNC Milling | U4 |
| Hurco VMC U7 | CNC Milling | U7 |
| Hurco VMC U16 | CNC Milling | U16 |
| Hurco Lathe | CNC Lathe | U16 |
| Lotus 1 | Laser Engraving | U7 |
| Lotus 2 | Laser Engraving | U7 |
| Lotus 3 | Laser Engraving | U7 |
| Edgebander | Edgebanding | U3 |

### Manual Operations (no machine — present for all products)
- Assembly
- Packing
- Quality checking

Daily throughput for manual operations is product-specific — to be defined per product routing.

---

## Working with Lucian

- Non-developer, business/product owner. Discuss approach before significant work; explain decisions in plain language.
- Once aligned, execute autonomously.
- Actively learning — brief "why" explanations are welcome.
