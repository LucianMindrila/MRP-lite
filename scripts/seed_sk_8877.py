"""Seed Safety Knife PO 8877 — BC-REAKTA-HD 001."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, Customer, Product, Order, OrderItem
from datetime import date

app = create_app()

with app.app_context():
    customer = Customer.query.filter(Customer.name.ilike('%safety knife%')).first()
    if not customer:
        print("ERROR: The Safety Knife Company not found.")
        sys.exit(1)
    print(f"Customer: {customer.name} (id={customer.id})")

    # Product
    code = 'BC-REAKTA-HD 001'
    product = Product.query.filter_by(code=code).first()
    if not product:
        product = Product(
            code=code,
            name='HD REAKTA CARRIER 92A BLADE',
            unit='pcs',
            sale_price=3.00,
            customer_id=customer.id,
        )
        db.session.add(product)
        db.session.flush()
        print(f"Created product: {code}")
    else:
        print(f"Product exists: {code}")

    # Order
    ref = '8877'
    order = Order.query.filter_by(order_ref=ref).first()
    if order:
        print(f"Order {ref} already exists — skipping.")
    else:
        order = Order(
            order_ref=ref,
            customer_id=customer.id,
            status='confirmed',
            required_date=date(2026, 6, 22),
            notes='Safety Knife PO 8877 — ref LAURA',
        )
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            qty=500,
            unit_price=3.00,
        ))
        print(f"Created order: {ref}  500 × BC-REAKTA-HD 001 @ £3.00  required 22/06/2026")

    db.session.commit()
    print("Done.")
