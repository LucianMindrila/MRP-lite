"""
Seed script: creates dummy test data for operator flow testing.
Run once: python scripts/seed_dummy_test.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from models import db, Supplier, Material, Product, BOMItem, Order, OrderItem
from models import PurchaseOrder, PurchaseOrderItem, StockBatch, StockMovement, DeliveryNote, DeliveryNoteItem
from datetime import date

app = create_app('development')

with app.app_context():

    # ── 1. Dummy Supplier ──────────────────────────────────────────────────
    dummy_sup = Supplier(
        name='Dummy Supplier',
        contact='Test Contact',
        email='test@dummysupplier.com',
        phone='01234 000000',
        lead_time_days=14,
    )
    db.session.add(dummy_sup)
    db.session.flush()
    print(f'Created supplier: {dummy_sup.name} (id {dummy_sup.id})')

    # ── 2. Dummy Raw Material ──────────────────────────────────────────────
    dummy_mat = Material(
        code='DUMMY-RAW',
        name='Dummy Raw Material Sheet',
        description='Test material — replaces Red PVC in dummy knife BOM',
        unit='sheets',
        stock_qty=0,
        reorder_point=5,
        reorder_qty=20,
        cost_price=15.00,
        supplier_id=dummy_sup.id,
    )
    db.session.add(dummy_mat)
    db.session.flush()
    print(f'Created material: {dummy_mat.code} (id {dummy_mat.id})')

    # ── 3. Dummy Knife product (customer: Safety Knife Co, id=3) ──────────
    dummy_prod = Product(
        code='DUMMY/KNIFE',
        name='Dummy Test Knife',
        description='Test product for operator flow — based on Big Fish 9mm N/H BOM',
        unit='pcs',
        sale_price=25.00,
        lead_time_days=1,
        customer_id=3,   # The Safety Knife Company
    )
    db.session.add(dummy_prod)
    db.session.flush()
    print(f'Created product: {dummy_prod.code} (id {dummy_prod.id})')

    # ── 4. BOM (same as Big Fish 9mm N/H except DUMMY-RAW replaces PVC) ──
    bom_lines = [
        (11,  1.0),   # BLADE-BIG-FISH
        (12,  5.0),   # BRASS-BOOT
        (13,  5.0),   # BRASS-SCREW-BOOT
        (14,  1.0),   # M10-LOCK-SCREW
        (15,  1.0),   # MACH-ASSEMB-BFISH
        (dummy_mat.id, 0.01),  # DUMMY-RAW (replaces PVC.RED)
    ]
    for mat_id, qty_per in bom_lines:
        db.session.add(BOMItem(product_id=dummy_prod.id, material_id=mat_id, qty_per_unit=qty_per))
    print(f'Created BOM: {len(bom_lines)} lines')

    # ── 5. Customer sales order: Safety Knife Co, PO ref 12345, 1000 units ─
    order = Order(
        order_ref='ORD-SK-12345',
        customer_id=3,
        status='confirmed',
        required_date=date(2026, 6, 30),
        notes='Safety Knife Company PO reference: 12345',
    )
    db.session.add(order)
    db.session.flush()
    oi = OrderItem(
        order_id=order.id,
        product_id=dummy_prod.id,
        qty=1000.0,
        unit_price=25.00,
    )
    db.session.add(oi)
    print(f'Created order: {order.order_ref} — 1000 x DUMMY/KNIFE')

    # ── 6. Purchase order: Dummy Supplier, 10 sheets dummy raw material ────
    po = PurchaseOrder(
        po_ref='PO-DUMMY-001',
        supplier_id=dummy_sup.id,
        status='sent',
        expected_date=date(2026, 5, 20),
        notes='Test PO — 10 sheets of dummy raw material',
    )
    db.session.add(po)
    db.session.flush()
    db.session.add(PurchaseOrderItem(
        po_id=po.id,
        material_id=dummy_mat.id,
        qty=10.0,
        qty_received=0,
        unit_price=15.00,
    ))
    print(f'Created purchase order: {po.po_ref} — 10 x DUMMY-RAW')

    # ── 7. Free-issued parts in stock at Unit 3 — Assembly Room ──────────
    # BOM qty × 1000 units = stock needed for the full order
    free_issued = [
        (11, 1000.0,  'BLADE-BIG-FISH'),
        (12, 5000.0,  'BRASS-BOOT'),
        (13, 5000.0,  'BRASS-SCREW-BOOT'),
        (14, 1000.0,  'M10-LOCK-SCREW'),
        (15, 1000.0,  'MACH-ASSEMB-BFISH'),
    ]
    for mat_id, qty, code in free_issued:
        mat = db.session.get(Material, mat_id)
        mat.stock_qty = (mat.stock_qty or 0) + qty
        db.session.add(StockBatch(
            material_id=mat_id,
            qty=qty,
            qty_original=qty,
            building='Unit 3',
            location_detail='Assembly Room',
            received_by='LM',
            notes='Free-issued from Safety Knife Company',
            status='active',
        ))
        db.session.add(StockMovement(
            material_id=mat_id,
            movement_type='goods_in',
            qty=qty,
            reference='FREE-ISSUE/SK-12345',
            notes='Free-issued from Safety Knife Company | Recv by: LM',
            created_by=1,
        ))
        print(f'  Stocked {qty:.0f} x {code} at Unit 3 — Assembly Room')

    db.session.commit()

    print()
    print('=== DONE ===')
    print(f'Supplier:        {dummy_sup.name}')
    print(f'Material:        {dummy_mat.code}')
    print(f'Product:         {dummy_prod.code}')
    print(f'Sales Order:     {order.order_ref}')
    print(f'Purchase Order:  {po.po_ref}  (visible in operator Goods In)')
    print(f'Free-issued parts stocked at Unit 3 — Assembly Room')
