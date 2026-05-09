import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Order, OrderItem, Customer, Product
    from datetime import date, datetime

    trend = Customer.query.filter(Customer.name.like('%Trend%')).first()
    if not trend:
        print('ERROR: Trend customer not found')
        sys.exit(1)
    print(f'Customer: {trend.name} (id={trend.id})')

    # -- 1. Fix S/KWJ900 price and create missing products ---------------------
    skwj900 = Product.query.filter_by(code='S/KWJ900').first()
    if skwj900 and skwj900.sale_price == 0:
        skwj900.sale_price = 61.03
        print('  Fixed S/KWJ900 price -> PS61.03')

    new_products = [
        ('ASSE/HJ/C',      'Assembly Cost H/JIG/C',                   11.29),
        ('ASSE/STRIKE/JIG','Assembly & JIG Parts Strike/JIG',          37.00),
        ('ECL/02',         'Euro Barrel Template for ECL/JIG',          4.00),
        ('MFT/01',         'MFT Index Pin',                             2.00),
        ('MFT/JIG',        'Multi Functional Table Top JIG',           52.29),
        ('TEMP/SS/A',      'Template Shelf Support 5mm 32mm Centre',   19.20),
    ]
    for code, name, price in new_products:
        if not Product.query.filter_by(code=code).first():
            db.session.add(Product(code=code, name=name, sale_price=price,
                                   unit='pcs', lead_time_days=7, customer_id=trend.id))
            print(f'  Created: {code} -- {name} @ GBP{price}')
    db.session.commit()

    # -- 2. Delete all existing Trend orders -----------------------------------
    existing = Order.query.filter_by(customer_id=trend.id).all()
    for o in existing:
        print(f'  Deleting: {o.order_ref}')
        db.session.delete(o)
    db.session.commit()
    print(f'Deleted {len(existing)} existing Trend orders.')

    # -- 3. Build orders -------------------------------------------------------
    TODAY = date(2026, 5, 9)

    def d(s):
        """Parse dd-Mon-yy, e.g. '02-Feb-26'"""
        return datetime.strptime(s, '%d-%b-%y').date()

    # (po_ref, order_date, required_date, [(product_code, qty, unit_price), ...])
    # required_date = latest delivery date across all lines; qty aggregated for same product
    orders_data = [
        ('066237', '11-Apr-25', '07-Jul-25', [
            ('LOCK/JIG/B/US', 50, 40.12),
        ]),
        ('066282', '07-May-25', '07-Jul-25', [
            ('H/KWJ950',     50, 56.00),
            ('KWJ/PIN/10MM', 4000, 0.33),
            ('KWJ650',       250, 28.22),
            ('KWJ700/PRO',   300, 52.50),
        ]),
        ('066283', '07-May-25', '04-Aug-25', [
            ('ASSE/HJ/C',    400,  11.29),
            ('H/KWJ650',     200,  42.56),
            ('H/KWJ950',      50,  56.00),
            ('KWJ/PIN/10MM', 3000,  0.33),
            ('KWJ650',       250,  28.22),
            ('KWJ700/PRO',   300,  52.50),
            ('MFT/01',        50,   2.00),
            ('MFT/JIG',       50,  52.29),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066284', '07-May-25', '01-Sep-25', [
            ('ASSE/HJ/C',    500,  11.29),
            ('BS/JIG/PRO',   100,  52.00),
            ('H/KWJ650',     200,  42.56),
            ('H/KWJ950',      50,  56.00),
            ('KWJ/PIN/10MM', 4000,  0.33),
            ('KWJ650',       250,  28.22),
            ('KWJ700',       450,  39.15),
            ('KWJ700/PRO',   400,  52.50),
            ('KWJ900',       100,  61.06),
            ('KWJ950/PRO',   100,  73.50),
            ('S/KWJ700',     500,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066496', '09-Jul-25', '06-Oct-25', [
            ('LOCK/JIG/B/US', 50, 40.12),
        ]),
        ('066504', '11-Jul-25', '03-Nov-25', [   # two deliveries aggregated
            ('ASSE/STRIKE/JIG', 1000, 37.00),
        ]),
        ('066509', '14-Jul-25', '06-Oct-25', [
            ('AR/JIG',        50,  40.89),
            ('BS/JIG/PRO',   100,  52.00),
            ('DG/JIG/A',     200,  43.80),
            ('KWJ650',       200,  28.22),
            ('KWJ700/PRO',   500,  52.50),
            ('KWJ950/PRO',   150,  73.50),
            ('KWJ/PIN/10MM', 4000,  0.33),
            ('MFT/JIG',       50,  52.29),
            ('S/KWJ700',     800,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066510', '14-Jul-25', '03-Nov-25', [
            ('BS/JIG/PRO',    50,  52.00),
            ('DG/JIG/A',     100,  43.80),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       300,  39.15),
            ('KWJ700/PRO',   500,  52.50),
            ('KWJ900',        50,  61.06),
            ('KWJ950/PRO',   150,  73.50),
            ('KWJ/PIN/10MM', 4000,  0.33),
            ('S/KWJ700',     800,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066626', '29-Aug-25', '03-Nov-25', [
            ('KWJ/PIN/10MM', 3000, 0.33),
            ('KWJ950/PRO',     50, 73.50),
        ]),
        ('066627', '29-Aug-25', '05-Jan-26', [
            ('AR/JIG',        50,  40.89),
            ('KWJ/PIN/10MM', 3500,  0.33),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       300,  39.15),
            ('KWJ950/PRO',   100,  73.50),
            ('S/KWJ700',     500,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066628', '29-Aug-25', '02-Feb-26', [
            ('BS/JIG/PRO',    50,  52.00),
            ('KWJ/PIN/10MM', 3500,  0.33),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       300,  39.15),
            ('KWJ700/A',      50,  41.00),
            ('KWJ700/PRO',   350,  52.50),
            ('KWJ950/PRO',   100,  73.50),
            ('S/KWJ700',     500,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066629', '29-Aug-25', '02-Mar-26', [
            ('AR/JIG',        50,  40.89),
            ('BS/JIG/PRO',    50,  52.00),
            ('DG/JIG/A',     150,  43.80),
            ('H/KWJ650',     100,  42.56),
            ('MFT/JIG',       50,  52.29),
            ('KWJ/PIN/10MM', 3500,  0.33),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       300,  39.15),
            ('KWJ700/A',      50,  41.00),
            ('KWJ700/PRO',   350,  52.50),
            ('KWJ950/PRO',    50,  73.50),
            ('S/KWJ700',     500,  39.12),
            ('S/KWJ900',      50,  61.03),
        ]),
        ('066681', '18-Sep-25', '02-Mar-26', [   # 3 H/KWJ650 deliveries aggregated
            ('H/CURVE/JIG',  100,  38.25),
            ('H/KWJ650',     400,  42.56),
        ]),
        ('066701', '24-Sep-25', '26-Jan-26', [
            ('ASSE/STRIKE/JIG', 500, 37.00),
        ]),
        ('066737', '08-Oct-25', '02-Mar-26', [
            ('KWJ900', 50, 61.06),
        ]),
        ('066783', '27-Oct-25', '02-Mar-26', [   # Feb+Mar deliveries aggregated
            ('DG/JIG/A', 350, 43.80),
        ]),
        ('066784', '27-Oct-25', '02-Mar-26', [   # Jan+Feb+Mar deliveries aggregated
            ('KWJ700/PRO', 650, 52.50),
        ]),
        ('066785', '27-Oct-25', '05-Jan-26', [
            ('TEMP/SS/A', 50, 19.20),
        ]),
        ('066829', '21-Nov-25', '06-Apr-26', [
            ('ASSE/STRIKE/JIG', 500, 37.00),
        ]),
        ('066865', '03-Dec-25', '02-Mar-26', [
            ('AR/JIG',    50,  40.89),
            ('H/KWJ650', 150,  42.56),
            ('H/KWJ950',  50,  56.00),
            ('KWJ650',   250,  28.22),
        ]),
        ('066922', '11-Dec-25', '01-Jun-26', [
            ('ASSE/STRIKE/JIG', 500, 37.00),
        ]),
        ('066944', '16-Dec-25', '02-Feb-26', [
            ('KWJ700/PRO', 100, 52.50),
            ('LOCK/JIG/B', 100, 40.12),
        ]),
        ('066948', '18-Dec-25', '02-Feb-26', [
            ('DG/JIG/A', 200, 43.80),
        ]),
        ('066953', '19-Dec-25', '02-Mar-26', [
            ('H/CURVE/JIG', 100, 38.25),
        ]),
        ('066969', '08-Jan-26', '02-Mar-26', [
            ('H/KWJ950', 200, 56.00),
        ]),
        ('067016', '30-Jan-26', '09-Mar-26', [
            ('RS/JIG', 50, 52.37),
        ]),
        ('067017', '30-Jan-26', '06-Apr-26', [
            ('DG/JIG/A',        200,  43.80),
            ('ECL/JIG',          50,  32.25),
            ('LOCK/JIG/B/US',    50,  40.12),
            ('KWJ/PIN/10MM',   3000,   0.33),
            ('KWJ650',          250,  28.22),
            ('KWJ700',          300,  39.15),
            ('KWJ900',           50,  61.06),
            ('RS/JIG',           50,  52.37),
        ]),
        ('067018', '30-Jan-26', '04-May-26', [
            ('AR/JIG',         50,  40.89),
            ('BS/JIG/PRO',     50,  52.00),
            ('DG/JIG/A',      200,  43.80),
            ('KWJ/PIN/10MM', 3000,   0.33),
            ('KWJ650',        250,  28.22),
            ('KWJ700',        300,  39.15),
            ('KWJ700/PRO',    350,  52.50),
            ('KWJ900',         50,  61.06),
            ('RS/JIG',         50,  52.37),
        ]),
        ('067019', '30-Jan-26', '01-Jun-26', [
            ('AR/JIG',         50,  40.89),
            ('BS/JIG/PRO',     50,  52.00),
            ('DG/JIG/A',      200,  43.80),
            ('ECL/JIG',        50,  32.25),
            ('KWJ/PIN/10MM', 3000,   0.33),
            ('KWJ650',        250,  28.22),
            ('KWJ700',        300,  39.15),
            ('KWJ700/PRO',    350,  52.50),
            ('KWJ900',         50,  61.06),
            ('LOCK/JIG/B',     50,  40.12),
            ('RS/JIG',         50,  52.37),
            ('S/KWJ700',      400,  39.12),
        ]),
        ('067034', '03-Feb-26', '01-Jun-26', [   # Apr+May+Jun deliveries aggregated
            ('H/KWJ650', 450, 42.56),
            ('H/KWJ950', 250, 56.00),
        ]),
        ('067044', '06-Feb-26', '01-Jun-26', [
            ('LOCK/JIG/B/US', 50, 40.12),
        ]),
        ('067090', '18-Feb-26', '03-Aug-26', [
            ('ASSE/STRIKE/JIG', 500, 37.00),
        ]),
        ('067162', '19-Mar-26', '13-Jul-26', [
            ('ASSE/STRIKE/JIG', 1000, 37.00),
        ]),
        ('067190', '26-Mar-26', '01-Jun-26', [
            ('ECL/02', 30, 4.00),
        ]),
        ('067191', '26-Mar-26', '06-Jul-26', [
            ('H/CURVE/JIG',  400,  38.25),
            ('DG/JIG/A',     200,  43.80),
            ('H/KWJ650',     100,  42.56),
            ('KWJ/PIN/10MM', 3000,  0.33),
            ('KWJ650',       200,  28.22),
            ('LOCK/JIG/B',    50,  40.12),
            ('RS/JIG',        50,  52.37),
            ('S/KWJ700',     400,  39.12),
        ]),
        ('067192', '26-Mar-26', '03-Aug-26', [
            ('AR/JIG',        50,  40.89),
            ('DG/JIG/A',     150,  43.80),
            ('ECL/JIG',       50,  32.25),
            ('H/KWJ650',     150,  42.56),
            ('H/KWJ950',     100,  56.00),
            ('KWJ/PIN/10MM', 3000,  0.33),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       250,  39.15),
            ('KWJ950/PRO',    50,  73.50),
            ('RS/JIG',        50,  52.37),
            ('S/KWJ700',     400,  39.12),
        ]),
        ('067193', '26-Mar-26', '07-Sep-26', [
            ('DG/JIG/A',     150,  43.80),
            ('H/CURVE/JIG',   50,  38.25),
            ('H/KWJ650',     100,  42.56),
            ('KWJ/PIN/10MM', 3000,  0.33),
            ('KWJ650',       200,  28.22),
            ('KWJ700',       250,  39.15),
            ('KWJ700/A',      50,  41.00),
            ('KWJ700/PRO',   350,  52.50),
            ('KWJ950/PRO',    50,  73.50),
            ('LOCK/JIG/B',    50,  40.12),
            ('RS/JIG',        50,  52.37),
            ('S/KWJ700',     400,  39.12),
        ]),
    ]

    created = 0
    for ref, order_date_str, req_date_str, lines in orders_data:
        order_date = datetime.strptime(order_date_str, '%d-%b-%y').date()
        req_date   = datetime.strptime(req_date_str,   '%d-%b-%y').date()
        invoiced   = req_date < TODAY
        status     = 'invoiced' if invoiced else 'confirmed'

        order = Order(
            order_ref=ref,
            customer_id=trend.id,
            status=status,
            required_date=req_date,
            dispatched_date=req_date if invoiced else None,
            notes=f'Imported from Trend PO {ref}',
        )
        order.created_at = datetime(order_date.year, order_date.month, order_date.day)
        db.session.add(order)
        db.session.flush()

        order_total = 0
        skipped = []
        for prod_code, qty, unit_price in lines:
            prod = Product.query.filter_by(code=prod_code).first()
            if not prod:
                skipped.append(prod_code)
                continue
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=prod.id,
                qty=float(qty),
                qty_dispatched=float(qty) if invoiced else 0.0,
                unit_price=unit_price,
            ))
            order_total += qty * unit_price

        tag = 'INVOICED' if invoiced else 'CONFIRMED'
        skip_str = f'  MISSING: {skipped}' if skipped else ''
        print(f'  {tag:10s} {ref} | {len(lines)} lines | GBP{order_total:>10,.2f} | {req_date_str}{skip_str}')
        created += 1

    db.session.commit()
    print(f'\nDone. Created {created} Trend orders.')
