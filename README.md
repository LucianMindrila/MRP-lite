# MRP-lite

A lightweight Material Requirements Planning (MRP) web app built with Flask. Designed for small manufacturing businesses to manage stock, purchase orders, sales orders, BOMs, delivery notes, and warehouse operations.

## Requirements

- Python 3.10 or higher
- pip

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/LucianMindrila/MRP-lite.git
cd MRP-lite
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a file called `.env` in the project root (it is gitignored — you must create it manually):

```
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-secret
DB_PASSWORD=localtest123
COMPANY_NAME=Your Company Name
COMPANY_ADDRESS=Your Address
COMPANY_VAT_NUMBER=GB 000 0000 00
```

`SECRET_KEY` can be any random string for local testing.  
`DB_PASSWORD` is only used if you switch to PostgreSQL — for SQLite (default) it is ignored.

### 4. Initialise the database — pick ONE

```bash
# A) Real DT Solutions catalog (recommended). Builds the schema AND loads the real
#    suppliers / materials / products / BOMs / customers / logins from db_export.json:
python scripts/setup_real_data.py

# B) Dummy sample data for quick testing:
flask seed
```

Both create the SQLite database at `instance/mrp.db` and the two default logins below.

> **Note:** `flask db upgrade` cannot build a database from scratch — the migration
> chain assumes the base tables already exist, so it only works on a database that
> is already populated. `setup_real_data.py` creates the schema from the models and
> stamps the migration state to head, so on a fresh machine you do **not** need to
> run `flask db upgrade` first; future migrations still apply normally afterwards.
>
> To refresh the real-data snapshot, run `python scripts/export_db.py` on the work
> PC and commit the updated `scripts/db_export.json`. For an *exact* clone of a live
> machine (including orders/stock), copy the `instance/mrp.db` file directly.

The two default logins created either way:
- **Admin user** — username: `admin`, password: `admin123`
- **Operator user** — username: `operator`, password: `operator123`

### 5. Run the app

```bash
flask run
```

Open your browser at `http://localhost:5000`

---

## Login

| Role | Username | Password | Redirects to |
|------|----------|----------|--------------|
| Admin | `admin` | `admin123` | Admin dashboard |
| Operator | `operator` | `operator123` | Operator tablet UI |

---

## Key features

- **Inventory** — materials, products, BOMs, suppliers, customers
- **Purchasing** — purchase orders, goods-in booking, over-delivery detection
- **Sales orders** — order management, delivery note creation, dispatch
- **Warehouse** — stock check with live diff, batch location tracking, move stock
- **Operator UI** — tablet-friendly interface for goods in/out and stock moves
- **Documents** — printable delivery notes, invoices, work orders
- **Reports** — order history, shopping list / what to buy

---

## Project structure

```
app.py              Flask application factory
config.py           Configuration (development / production)
models.py           SQLAlchemy models
routes/             Blueprint modules (dashboard, inventory, orders, warehouse, operator, …)
templates/          Jinja2 templates
migrations/         Flask-Migrate migration files
scripts/            One-off seed / import scripts
seed_data.py        flask seed command
```

---

## Docker (optional)

A `Dockerfile` and `docker-compose.yml` are included if you prefer to run via Docker:

```bash
docker compose up --build
```
