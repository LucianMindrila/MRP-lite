"""setup_real_data.py — Rebuild the real DT Solutions catalog on a fresh database.

This is the matched partner to export_db.py:

    WORK PC:   python scripts/export_db.py        -> writes scripts/db_export.json
    git:       commit db_export.json               (version-controlled source of truth)
    ANY PC:    python scripts/setup_real_data.py    (builds the schema AND fills the data)

This script creates the database schema itself (via create_all) and stamps the
migration state as current, so there is no need to run `flask db upgrade` first.
(The migration chain cannot build a fresh DB from scratch — its root migration
assumes the base tables already exist — so we create the schema from the models
and then stamp Alembic to head, which keeps future migrations working normally.)

What it restores (the "master / reference" data — the irreplaceable hand-built catalog):
    users, categories, suppliers, customers, materials, products, BOM items

What it does NOT restore (transactional / live state):
    orders, purchase orders, delivery notes, work orders, stock movements, stock batches.
    For an exact clone of a live machine, just copy the instance/mrp.db file instead.

Original primary-key IDs from the export are preserved on insert, so every
foreign-key link (material->supplier, product->customer, BOM->product/material)
lines up exactly as it was on the work PC.

Usage:
    python scripts/setup_real_data.py            # fills an empty catalog
    python scripts/setup_real_data.py --force    # wipes the catalog first, then refills

Safety:
    - Refuses to run if catalog data already exists (unless --force).
    - Refuses even with --force if transactional data (orders etc.) is present,
      so it can never orphan live records. Use a fresh DB for that case.
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy import inspect
from flask_migrate import stamp
from app import create_app
from models import (db, User, Customer, Supplier, Category, Material, Product,
                    BOMItem, Order, PurchaseOrder, DeliveryNote, WorkOrder,
                    StockMovement, StockBatch)

EXPORT_PATH = Path(__file__).parent / 'db_export.json'

# Default passwords for restored logins. Matches the README / `flask seed`
# convention. Anything not listed gets a placeholder that must be changed.
DEFAULT_PASSWORDS = {'admin': 'admin123', 'operator': 'operator123'}
FALLBACK_PASSWORD = 'changeme123'


def load_export():
    if not EXPORT_PATH.exists():
        sys.exit(f"ERROR: {EXPORT_PATH} not found. Run `python scripts/export_db.py` "
                 "on the work PC first, then copy db_export.json across.")
    with open(EXPORT_PATH, encoding='utf-8') as f:
        return json.load(f)


def ensure_schema():
    """Create the schema from the models if the tables don't exist yet, and stamp
    the Alembic migration state to head so future `flask db upgrade` runs work.
    On a DB that already has tables this is a harmless no-op."""
    had_tables = inspect(db.engine).has_table('materials')
    db.create_all()
    if not had_tables:
        stamp(revision='head')
        print("Created database schema from models and stamped migrations to head.")


def catalog_count():
    """How many master-data rows already exist."""
    return (User.query.count() + Category.query.count() + Supplier.query.count() +
            Customer.query.count() + Material.query.count() + Product.query.count() +
            BOMItem.query.count())


def transactional_count():
    """Live/transactional rows — must be zero before we wipe anything."""
    return (Order.query.count() + PurchaseOrder.query.count() + DeliveryNote.query.count() +
            WorkOrder.query.count() + StockMovement.query.count() + StockBatch.query.count())


def wipe_catalog():
    """Delete catalog rows in child-first order. Only safe when there is no
    transactional data referencing them (guarded by the caller)."""
    BOMItem.query.delete()
    Product.query.delete()
    Material.query.delete()
    Customer.query.delete()
    Supplier.query.delete()
    Category.query.delete()
    User.query.delete()
    db.session.commit()


def restore(data):
    """Insert the catalog in dependency order, preserving original IDs."""

    # 1. Users (no dependencies). Passwords are NOT in the export — set defaults.
    warned = []
    for u in data.get('users', []):
        user = User(id=u['id'], username=u['username'], email=u['email'], role=u['role'])
        pw = DEFAULT_PASSWORDS.get(u['username'], FALLBACK_PASSWORD)
        user.set_password(pw)
        if pw == FALLBACK_PASSWORD:
            warned.append(u['username'])
        db.session.add(user)

    # 2. Categories (no dependencies)
    for c in data.get('categories', []):
        db.session.add(Category(id=c['id'], name=c['name'], description=c.get('description')))

    # 3. Suppliers (no dependencies)
    for s in data.get('suppliers', []):
        db.session.add(Supplier(
            id=s['id'], name=s['name'], contact=s.get('contact'), email=s.get('email'),
            phone=s.get('phone'), lead_time_days=s.get('lead_time_days', 7)))

    # 4. Customers (no dependencies)
    for c in data.get('customers', []):
        db.session.add(Customer(
            id=c['id'], name=c['name'], contact=c.get('contact'), email=c.get('email'),
            phone=c.get('phone'), address=c.get('address'),
            payment_terms=c.get('payment_terms', '30 days Nett')))

    # 5. Materials (-> supplier, category)
    for m in data.get('materials', []):
        db.session.add(Material(
            id=m['id'], code=m['code'], name=m['name'], description=m.get('description'),
            unit=m.get('unit', 'pcs'), stock_qty=m.get('stock_qty', 0),
            cost_price=m.get('cost_price', 0), reorder_point=m.get('reorder_point', 0),
            reorder_qty=m.get('reorder_qty', 0), supplier_id=m.get('supplier_id'),
            category_id=m.get('category_id'), location=m.get('location'),
            notes=m.get('notes')))

    # 6. Products (-> customer)
    for p in data.get('products', []):
        db.session.add(Product(
            id=p['id'], code=p['code'], name=p['name'], description=p.get('description'),
            unit=p.get('unit', 'pcs'), sale_price=p.get('sale_price', 0),
            lead_time_days=p.get('lead_time_days', 1), customer_id=p.get('customer_id')))

    # Flush parents so the BOM foreign keys resolve cleanly.
    db.session.flush()

    # 7. BOM items (-> product, material)
    for b in data.get('bom_items', []):
        db.session.add(BOMItem(
            product_id=b['product_id'], material_id=b['material_id'],
            qty_per_unit=b['qty_per_unit']))

    db.session.commit()
    return warned


def main():
    parser = argparse.ArgumentParser(description='Rebuild the real catalog from db_export.json')
    parser.add_argument('--force', action='store_true',
                        help='Wipe existing catalog data before restoring')
    args = parser.parse_args()

    data = load_export()
    app = create_app()

    with app.app_context():
        # Build the schema if needed (the migration chain can't create a fresh DB).
        ensure_schema()
        existing = catalog_count()

        if existing > 0:
            if not args.force:
                sys.exit(f"ERROR: catalog already has {existing} rows. This script is for a "
                         "FRESH database.\n  - For a clean rebuild here, re-run with --force.\n"
                         "  - For an exact clone of a live machine, copy instance/mrp.db instead.")
            if transactional_count() > 0:
                sys.exit("ERROR: --force refused — transactional data (orders, POs, stock, etc.) "
                         "exists.\nWiping the catalog would orphan those records. Use a fresh "
                         "database instead.")
            print(f"--force: wiping {existing} existing catalog rows...")
            wipe_catalog()

        warned = restore(data)

    # Summary
    print("\n=== REAL DATA RESTORED ===")
    print(f"  Users      : {len(data.get('users', []))}")
    print(f"  Categories : {len(data.get('categories', []))}")
    print(f"  Suppliers  : {len(data.get('suppliers', []))}")
    print(f"  Customers  : {len(data.get('customers', []))}")
    print(f"  Materials  : {len(data.get('materials', []))}")
    print(f"  Products   : {len(data.get('products', []))}")
    print(f"  BOM items  : {len(data.get('bom_items', []))}")
    print("\nLogins restored with default passwords:")
    for name, pw in DEFAULT_PASSWORDS.items():
        print(f"  {name} / {pw}")
    if warned:
        print(f"\n  WARNING: these users got the placeholder password '{FALLBACK_PASSWORD}' "
              f"(change them): {', '.join(warned)}")
    print("\nDone. Transactional data (orders/stock) was intentionally not restored.")


if __name__ == '__main__':
    main()
