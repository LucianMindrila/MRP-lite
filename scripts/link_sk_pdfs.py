"""Manually link the Safety Knife PDFs to their orders."""
import sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app
from models import db, Order

BASE = Path(r'C:\Users\conta\OneDrive - DT Solutions LTD\POs\The Safety Knife Company')

# PDF Conversion = WO26438, PDF Conversion1 = WO26459, PDF Conversion2 = PO 8877
MAPPINGS = [
    ('PDF Conversion.pdf',  'WO26438'),
    ('PDF Conversion1.pdf', 'WO26459'),
    ('PDF Conversion2.pdf', '8877'),
]

app = create_app()
with app.app_context():
    for filename, order_ref in MAPPINGS:
        path = BASE / filename
        if not path.exists():
            print(f"  File not found: {filename}")
            continue
        order = Order.query.filter_by(order_ref=order_ref).first()
        if not order:
            print(f"  Order not found: {order_ref}")
            continue
        order.po_file_path = str(path)
        print(f"  Linked: {filename} -> {order_ref}")
    db.session.commit()
    print("\nAll Safety Knife orders linked.")
