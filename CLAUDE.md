# MRP-lite

Lightweight MRP (Material Requirements Planning) web app built for DT Solutions Ltd. The goal is for this to become the single piece of software running the entire business — from the moment a customer places an order through to invoicing. It replaces a fragmented mix of paper, Excel, Smartsheet, and QuickBooks with one centralised system.

**Repo:** https://github.com/LucianMindrila/MRP-lite
**Status:** Active development

---

## The Business — DT Solutions Ltd

Manufacturing company in Gloucester, UK. Produces panel-based products (kitchen units, office furniture, laminated doors, bespoke items) using sheet goods materials: Compact Grade laminate, plywood, MFC, MDF, plastic sheets.

**Services:** Panel sizing, edgebanding, flat bonding of laminates/veneers, CNC routing, laser engraving.
**Customers:** Trade customers UK-wide (furniture manufacturers, kitchen designers, etc.)
**Team:** Small — admin, operators on shop floor, owner (Lucian).

---

## Current Business Flow (as-is — what the app must replace)

Understanding the current manual process is critical to building the right thing:

1. **Order intake** — Customer sends a PO via email (Outlook) as a PDF attachment
2. **Paper copy** — Admin prints the PDF, places it in a physical folder
3. **Smartsheet entry** — Admin manually types all order lines and details into Smartsheet. This is the current "database" of outstanding orders
4. **Material planning** — No formal BoM system. Materials ordered based on mental calculation: product needed → sheets/yield estimate → order placed
5. **Purchase orders** — Manually created in Excel, emailed to supplier
6. **Goods received** — Not booked into any system. Lucian verbally communicates to operators what delivery is expected and which job it's for. No centralised stock knowledge
7. **Production scheduling** — Smartsheet Gantt chart scheduling jobs across machines (CNC, saw, edgebander)
8. **Delivery notes** — Manually created in Excel when goods are ready
9. **Dispatch** — Marked manually on the Smartsheet outstanding orders sheet
10. **Invoicing** — Done at month-end. Admin manually reconciles customer orders against delivery notes produced that month and creates invoices in Excel
11. **QuickBooks** — Used mainly for job costing (raw material cost vs job cost) and tracking invoices

---

## Core Problems Being Solved

1. **Triple data entry** — the same order is handled 3+ times: printed, typed into Smartsheet, reconciled at month-end. Each step is a source of error and lost time
2. **No BoM system** — material ordering runs entirely on one person's mental calculation
3. **No stock control** — goods arrive but are never booked in. Nobody knows what's actually on the shelf
4. **Single point of failure** — the entire operation depends on one person's memory
5. **Disconnected documents** — POs in Excel, delivery notes in Excel, invoices in Excel, orders in Smartsheet, financials in QuickBooks. Nothing talks to anything else

---

## Build Plan — Phased Approach

Each phase delivers real business value before the next begins. Do not skip phases or build ahead.

### Phase 1 — Replace paper folder + Smartsheet order sheet ← CURRENT FOCUS
- Customer orders entered directly into MRP-lite by admin (single entry point)
- MRP-lite becomes the live outstanding orders database
- Eliminates duplicate data entry; one source of truth for all orders
- **Open question:** Does Lucian want to eventually automate PDF extraction from email attachments, or is manual entry acceptable long-term?

### Phase 2 — BoMs and materials
- Capture all products and their bill of materials
- Link sales orders to BoMs so the app calculates material requirements automatically
- Removes mental calculation dependency

### Phase 3 — Purchasing workflow
- Generate purchase orders from inside the app (replaces Excel POs)
- Book goods in on arrival → stock updates automatically
- Removes memory dependency; stock always known

### Phase 4 — Production and dispatch
- Jobs linked to production schedule
- Delivery notes generated from the app (replaces Excel)
- Dispatch recorded in the app (replaces Smartsheet)
- Full job lifecycle tracked in one place

### Phase 5 — Invoicing and QuickBooks
- Month-end invoices auto-generated from delivery notes
- QuickBooks sync
- Month-end reconciliation becomes a button press

---

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

---

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

## What the App Already Has

- Sales orders ✓
- Purchase orders ✓
- Goods-in booking ✓
- Stock/inventory tracking ✓
- Delivery notes (printable) ✓
- Invoicing ✓
- BoMs ✓
- Supplier and customer management ✓
- Role-based access (Admin / Operator) ✓
- Tablet-friendly operator UI ✓

---

## Planned Integrations

- **QuickBooks API** — sync invoices and purchase orders (Phase 5)
- **Smartsheet API** — transition period sync; eventually replaced by the app entirely

---

## Working with Lucian

- Non-developer, business/product owner. Handles direction; Claude handles technical execution.
- Always discuss approach and align before starting significant work.
- Explain technical decisions in plain language tied to business impact.
- Once aligned, execute autonomously — no need to check in mid-task.
- Lucian is actively learning — brief explanations of the "why" behind decisions are welcome.
