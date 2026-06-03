"""export_db.py — Dump all business data from the live database to JSON.

Run this on the work PC to capture everything currently in the database.

Usage:
    python scripts/export_db.py

Output:
    scripts/db_export.json  — full export of all records
    (printed summary to console)
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import create_app
from models import db, User, Customer, Supplier, Category, Material, Product, BOMItem, Order, OrderItem

app = create_app()

with app.app_context():
    data = {}

    # Users (logins) — password hashes deliberately NOT exported.
    # setup_real_data.py recreates users with default passwords.
    users = User.query.order_by(User.id).all()
    data['users'] = [
        {'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role}
        for u in users
    ]

    # Customers
    customers = Customer.query.order_by(Customer.name).all()
    data['customers'] = [
        {'id': c.id, 'name': c.name, 'contact': c.contact,
         'email': c.email, 'phone': c.phone, 'address': c.address,
         'payment_terms': c.payment_terms}
        for c in customers
    ]

    # Suppliers
    suppliers = Supplier.query.order_by(Supplier.name).all()
    data['suppliers'] = [
        {'id': s.id, 'name': s.name, 'contact': s.contact,
         'email': s.email, 'phone': s.phone, 'lead_time_days': s.lead_time_days}
        for s in suppliers
    ]

    # Categories
    categories = Category.query.order_by(Category.name).all()
    data['categories'] = [
        {'id': c.id, 'name': c.name, 'description': c.description}
        for c in categories
    ]

    # Materials
    materials = Material.query.order_by(Material.code).all()
    data['materials'] = [
        {'id': m.id, 'code': m.code, 'name': m.name, 'description': m.description,
         'unit': m.unit, 'stock_qty': m.stock_qty, 'cost_price': m.cost_price,
         'reorder_point': m.reorder_point, 'reorder_qty': m.reorder_qty,
         'supplier_id': m.supplier_id, 'category_id': m.category_id,
         'location': m.location, 'notes': m.notes}
        for m in materials
    ]

    # Products
    products = Product.query.order_by(Product.code).all()
    data['products'] = [
        {'id': p.id, 'code': p.code, 'name': p.name, 'description': p.description,
         'unit': p.unit, 'sale_price': p.sale_price, 'lead_time_days': p.lead_time_days,
         'customer_id': p.customer_id}
        for p in products
    ]

    # BOMs
    bom_items = BOMItem.query.all()
    data['bom_items'] = [
        {'product_id': b.product_id, 'material_id': b.material_id,
         'qty_per_unit': b.qty_per_unit}
        for b in bom_items
    ]

    # Orders (active only — not invoiced)
    orders = Order.query.filter(Order.status.notin_(['invoiced'])).order_by(Order.created_at).all()
    data['orders'] = [
        {'id': o.id, 'order_ref': o.order_ref, 'customer_id': o.customer_id,
         'status': o.status, 'required_date': str(o.required_date) if o.required_date else None,
         'notes': o.notes,
         'items': [
             {'product_id': i.product_id, 'qty': i.qty,
              'qty_dispatched': i.qty_dispatched, 'unit_price': i.unit_price}
             for i in o.items
         ]}
        for o in orders
    ]

    # Write JSON
    out_path = Path(__file__).parent / 'db_export.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n=== DATABASE EXPORT SUMMARY ===")
    print(f"  Users      : {len(data['users'])}")
    print(f"  Customers  : {len(data['customers'])}")
    print(f"  Suppliers  : {len(data['suppliers'])}")
    print(f"  Categories : {len(data['categories'])}")
    print(f"  Materials  : {len(data['materials'])}")
    print(f"  Products   : {len(data['products'])}")
    print(f"  BOM items  : {len(data['bom_items'])}")
    print(f"  Orders     : {len(data['orders'])}")
    print(f"\nFull export saved to: {out_path}")

    print("\n--- CUSTOMERS ---")
    for c in data['customers']:
        print(f"  {c['name']}  ({c['email'] or 'no email'})")

    print("\n--- SUPPLIERS ---")
    for s in data['suppliers']:
        print(f"  {s['name']}  (lead time: {s['lead_time_days']} days)")

    print("\n--- CATEGORIES ---")
    for c in data['categories']:
        print(f"  {c['name']}")

    print("\n--- PRODUCTS ---")
    for p in data['products']:
        print(f"  {p['code']}  —  {p['name']}  @ £{p['sale_price']}")
