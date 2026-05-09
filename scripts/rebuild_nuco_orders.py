import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Order, OrderItem, Customer, Product
    from datetime import date, datetime

    nuco = Customer.query.filter(Customer.name.like('%Nuco%')).first()
    if not nuco:
        print('ERROR: NuCo customer not found')
        sys.exit(1)
    print(f'Customer: {nuco.name} (id={nuco.id})')

    # ── 1. Create missing products ────────────────────────────────────────────
    new_products = [
        # code, name, price
        ('101504',    'UJK Hinge Jig with Clamp Plate',              37.25),
        ('101505',    'UJK Stair Jig',                               53.00),
        ('102540',    'UJK MultiFunction Workbench (Frame Only)',     60.00),
        ('102542',    'UJK Twist Dogs (Pair) - 40mm',                 8.50),
        ('102543',    'UJK Laminated Router Top 600x800mm',          90.00),
        ('105278',    'UJK Isometric HDF Valchromat Top',            65.00),
        ('105279',    'UJK Aperture Radius Jig',                     42.00),
        ('105280',    'UJK Assembly Square',                         11.85),
        ('108497',    'UJK Work Top for T-Loc Systainer Cases',      48.03),
        ('108509',    'UJK Purchased Rider Shooting Board (RSB)',    30.75),
        ('109294',    'UJK Full Length Adjustable Hinge Jig',        74.95),
        ('109405',    'UJK Compact Multifunction Workbench',         60.00),
        ('109827',    'UJK MRMDF Top for Bench Dogs',                45.00),
        ('110223',    'UJK Blank Universal Sub-Base',                 8.85),
        ('508615',    'UJK 700MM Standard Worktop Jig',              50.00),
        ('508619',    'UJK Compact Lock Jig',                        37.25),
        ('508621',    'UJK Worktop Pins for Worktop Jigs (pack)',     1.75),
        ('APT006105', 'F25.4 Face Template 25.4mm (for 508619)',      6.00),
        ('APT008645', 'Fixings Pack for 102543 Laminated Top',       10.00),
        ('APT009748', 'H122 Front Top Rail for 109531',               5.50),
        ('APT010718', 'Long Countersink Screw M5x40 x2 (Datum Stop)', 0.00),
        ('UJK0000111','L16 Lock Template 16mm for 508619',            7.50),
        ('UJK000012', 'Pair of Sliding Stop Plates for Lock Jig 508619', 4.85),
    ]

    for code, name, price in new_products:
        if not Product.query.filter_by(code=code).first():
            p = Product(code=code, name=name, sale_price=price,
                        unit='pcs', lead_time_days=7, customer_id=nuco.id)
            db.session.add(p)
            print(f'  Created product: {code} — {name} @ £{price}')
        else:
            print(f'  Exists: {code}')

    db.session.commit()

    # ── 2. Delete existing Nuco orders ────────────────────────────────────────
    existing = Order.query.filter_by(customer_id=nuco.id).all()
    for o in existing:
        print(f'  Deleting: {o.order_ref}')
        db.session.delete(o)
    db.session.commit()
    print(f'Deleted {len(existing)} existing Nuco orders.')

    # ── 3. Build all orders from PDF data ─────────────────────────────────────
    CUTOFF = date(2026, 5, 1)

    def d(s):
        """Parse dd/mm/yyyy."""
        parts = s.split('/')
        return date(int(parts[2]), int(parts[1]), int(parts[0]))

    def price_for(code, pdf_price):
        p = Product.query.filter_by(code=code).first()
        return p.sale_price if p else pdf_price

    # (order_ref, order_date, delivery_date, [(product_code, qty, unit_price), ...])
    orders_data = [
        ('PO-00001071', '24/10/2025', '31/10/2025', [
            ('101504', 50,  37.25),
            ('102540', 50,  60.00),
            ('109796', 15, 135.00),
            ('508615', 50,  50.00),
            ('102540', 100, 60.00),
            ('102542', 43,   8.50),
            ('105279', 20,  42.00),
            ('109294', 50,  74.95),
            ('109405', 50,  60.00),
            ('508615', 50,  50.00),
        ]),
        ('PO-00001089', '06/11/2025', '19/12/2025', [
            ('101505', 30,  53.00),
            ('102543', 12,  90.00),
            ('105278', 12,  65.00),
            ('108497', 25,  48.03),
            ('109827', 20,  45.00),
            ('508619', 40,  37.25),
            ('508621', 10,   1.75),
        ]),
        ('PO-00001102', '07/11/2025', '19/12/2025', [
            ('101504', 50,  37.25),
            ('102543', 12,  90.00),
            ('105280', 96,  11.85),
            ('109796', 15, 135.00),
            ('110223', 20,   8.85),
            ('508621', 20,   1.75),
        ]),
        ('PO-00001160', '04/12/2025', '04/03/2026', [
            ('102537', 60,  65.00),
            ('102543', 12,  90.00),
        ]),
        ('PO-00001184', '12/12/2025', '08/01/2026', [
            ('APT006105', 1, 6.00),
        ]),
        ('PO-00001189', '12/12/2025', '12/03/2026', [
            ('101505', 30, 53.00),
        ]),
        ('PO-00001195', '15/12/2025', '16/12/2025', [
            ('APT009748', 1, 5.50),
        ]),
        ('PO-00001206', '19/12/2025', '19/01/2026', [
            ('105280', 96, 11.85),
        ]),
        ('PO-00001250', '10/02/2026', '18/03/2026', [
            ('109796', 15, 135.00),
            ('102537', 60,  65.00),
            ('109827', 15,  45.00),
        ]),
        ('PO-00001257', '10/02/2026', '10/03/2026', [
            ('10050', 100, 60.00),
        ]),
        ('PO-00001276', '17/02/2026', '26/02/2026', [
            ('UJK0000111', 1, 7.50),
            ('UJK000012',  1, 4.85),
        ]),
        ('PO-00001290', '24/02/2026', '24/03/2026', [
            ('105278', 12, 65.00),
        ]),
        ('PO-00001294', '26/02/2026', '13/03/2026', [
            ('10050', 50, 60.00),
        ]),
        ('PO-00001302', '27/02/2026', '27/04/2026', [
            ('101504', 50,  37.25),
            ('102543', 12,  90.00),
            ('105279', 20,  42.00),
            ('508620', 10,   8.50),
        ]),
        ('PO-00001332', '03/03/2026', '01/05/2026', [
            ('105278', 12, 65.00),
        ]),
        ('PO-00001345', '06/03/2026', '07/05/2026', [
            ('508619', 40, 37.25),
        ]),
        ('PO-00001348', '10/03/2026', '31/03/2026', [
            ('APT010718', 1, 0.00),
        ]),
        ('PO-00001361', '13/03/2026', '13/05/2026', [
            ('105280', 96, 11.85),
        ]),
        ('PO-00001379', '20/03/2026', '15/04/2026', [
            ('APT008645', 2, 10.00),
        ]),
        ('PO-00001384', '25/03/2026', '22/05/2026', [
            ('10050', 50, 60.00),
        ]),
        ('PO-00001393', '26/03/2026', '29/05/2026', [
            ('10386', 50,  76.00),
            ('10389', 50,  75.00),
            ('10390', 50,  70.00),
            ('10392', 50, 115.00),
            ('10393', 50, 195.00),
        ]),
        ('PO-00001407', '01/04/2026', '30/06/2026', [
            ('102537', 60, 65.00),
        ]),
        ('PO-00001413', '14/04/2026', '12/06/2026', [
            ('508620', 20,  8.50),
            ('10050',  50, 60.00),
        ]),
        ('PO-00001445', '27/04/2026', '29/06/2026', [
            ('109796', 25, 135.00),
        ]),
        ('303823', '30/04/2026', '29/06/2026', [
            ('108509', 100, 30.75),
        ]),
    ]

    created = 0
    for ref, order_date_str, del_date_str, lines in orders_data:
        order_date = d(order_date_str)
        del_date   = d(del_date_str)
        invoiced   = del_date < CUTOFF
        status     = 'invoiced' if invoiced else 'confirmed'

        order = Order(
            order_ref=ref,
            customer_id=nuco.id,
            status=status,
            required_date=del_date,
            dispatched_date=del_date if invoiced else None,
            notes=f'Imported from NuCo PO {ref}',
        )
        order.created_at = datetime(order_date.year, order_date.month, order_date.day)
        db.session.add(order)
        db.session.flush()

        order_total = 0
        for prod_code, qty, unit_price in lines:
            prod = Product.query.filter_by(code=prod_code).first()
            if not prod:
                print(f'  WARNING: product {prod_code} not found — skipping line')
                continue
            item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                qty=float(qty),
                qty_dispatched=float(qty) if invoiced else 0.0,
                unit_price=unit_price,
            )
            db.session.add(item)
            order_total += qty * unit_price

        status_tag = 'INVOICED' if invoiced else 'CONFIRMED'
        print(f'  {status_tag:10s} {ref:20s} | {len(lines)} lines | £{order_total:,.2f} | del {del_date_str}')
        created += 1

    db.session.commit()
    print(f'\nDone. Created {created} NuCo orders.')
