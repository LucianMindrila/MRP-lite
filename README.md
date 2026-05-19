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

### 4. Initialise the database

```bash
flask db upgrade
```

This creates the SQLite database at `instance/mrp.db` and runs all migrations.

### 5. Seed initial data (optional)

To create two default users and some sample data:

```bash
flask seed
```

This creates:
- **Admin user** — username: `admin`, password: `admin123`
- **Operator user** — username: `operator`, password: `operator123`

### 6. Run the app

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
