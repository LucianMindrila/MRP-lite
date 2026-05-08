"""Seed Safety Knife Company products, BOMs and orders."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, Customer, Category, Material, Product, BOMItem, Order, OrderItem
from datetime import date

app = create_app()

with app.app_context():
    # ── Look up anchor records ──────────────────────────────────────────────
    customer = Customer.query.filter(Customer.name.ilike('%safety knife%')).first()
    if not customer:
        print("ERROR: 'The Safety Knife Company' customer not found.")
        sys.exit(1)
    print(f"Customer: {customer.name} (id={customer.id})")

    category = Category.query.filter(Category.name.ilike('%fishknife free%')).first()
    if not category:
        print("ERROR: 'Fishknife Free Issued' category not found.")
        sys.exit(1)
    print(f"Category: {category.name} (id={category.id})")

    # ── Helper ──────────────────────────────────────────────────────────────
    def get_or_create_material(code, name):
        m = Material.query.filter_by(code=code).first()
        if not m:
            m = Material(
                code=code,
                name=name,
                unit='pcs',
                stock_qty=0,
                category_id=category.id,
            )
            db.session.add(m)
            db.session.flush()
            print(f"  Created material: {code} — {name}")
        else:
            print(f"  Material exists: {code} — {m.name}")
        return m

    def get_or_create_product(code, name):
        p = Product.query.filter_by(code=code).first()
        if not p:
            p = Product(
                code=code,
                name=name,
                unit='pcs',
                sale_price=0,
                customer_id=customer.id,
            )
            db.session.add(p)
            db.session.flush()
            print(f"  Created product: {code} — {name}")
        else:
            print(f"  Product exists: {code} — {p.name}")
        return p

    def add_bom(product, material, qty_per_unit):
        exists = BOMItem.query.filter_by(
            product_id=product.id, material_id=material.id
        ).first()
        if not exists:
            db.session.add(BOMItem(
                product_id=product.id,
                material_id=material.id,
                qty_per_unit=qty_per_unit,
            ))
            print(f"    BOM: {material.code} × {qty_per_unit}")
        else:
            print(f"    BOM exists: {material.code}")

    # ── Materials ───────────────────────────────────────────────────────────
    print("\n--- Materials ---")
    blade       = get_or_create_material('BLADE-BIG-FISH',    'BLADE FOR BIG FISH')
    brass_boot  = get_or_create_material('BRASS-BOOT',        'BRASS BOOT')
    brass_screw = get_or_create_material('BRASS-SCREW-BOOT',  'BRASS SCREW FOR BOOT')
    m10_lock    = get_or_create_material('M10-LOCK-SCREW',    'M10 LOCKING SCREW')
    machine_svc = get_or_create_material('MACH-ASSEMB-BFISH', 'MACHINE & ASSEMB B/FISH')
    jb3201802   = get_or_create_material('JB3201802',         'JB3201802 STRAIGHT BLADE FOR F200')
    jb96q21822  = get_or_create_material('JB96Q-21822',       'JB96Q-21822 SINGLE END HOOK STAINLESS')

    # ── Product 1: BIG FISH 9MM N/H 1 SGL ──────────────────────────────────
    print("\n--- Product 1 ---")
    p1 = get_or_create_product('BIG FISH 9MM N/H 1 SGL', 'BIG FISH 9MM N/H SINGLE ITEM NO HOOK')

    # Clear existing BOM so we don't duplicate on re-run
    BOMItem.query.filter_by(product_id=p1.id).delete()
    db.session.flush()

    print("  BOM lines:")
    add_bom(p1, blade,       1.0)
    add_bom(p1, brass_boot,  5.0)
    add_bom(p1, brass_screw, 5.0)
    add_bom(p1, m10_lock,    1.0)
    add_bom(p1, machine_svc, 1.0)

    # ── Product 2: BIG FISH 6MM + ST ST HOOK FOR MOD ───────────────────────
    print("\n--- Product 2 ---")
    p2 = get_or_create_product('13154002', 'BIG FISH 6MM + ST ST HOOK FOR MOD')

    BOMItem.query.filter_by(product_id=p2.id).delete()
    db.session.flush()

    print("  BOM lines:")
    add_bom(p2, blade,       1.0)
    add_bom(p2, jb3201802,   1.0)
    add_bom(p2, brass_boot,  5.0)
    add_bom(p2, brass_screw, 5.0)
    add_bom(p2, jb96q21822,  1.0)
    add_bom(p2, m10_lock,    1.0)
    add_bom(p2, machine_svc, 1.0)

    # ── Orders ──────────────────────────────────────────────────────────────
    print("\n--- Orders ---")

    def get_or_create_order(ref, product, qty, required):
        o = Order.query.filter_by(order_ref=ref).first()
        if o:
            print(f"  Order exists: {ref}")
            return o
        o = Order(
            order_ref=ref,
            customer_id=customer.id,
            status='confirmed',
            required_date=required,
            notes=f'Works Order {ref}',
        )
        db.session.add(o)
        db.session.flush()
        db.session.add(OrderItem(
            order_id=o.id,
            product_id=product.id,
            qty=qty,
            unit_price=0,
        ))
        print(f"  Created order: {ref}  qty={qty}  required={required}")
        return o

    # chronological order: WO26438 (08/06/2026), WO26459 (15/06/2026)
    get_or_create_order('WO26438', p1, 1000, date(2026, 6, 8))
    get_or_create_order('WO26459', p2, 1000, date(2026, 6, 15))

    db.session.commit()
    print("\nDone — all records committed.")
