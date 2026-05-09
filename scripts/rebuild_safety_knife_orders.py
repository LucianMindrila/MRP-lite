import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Order, OrderItem, Customer, Product
    from datetime import date

    sk = Customer.query.filter(Customer.name.like('%Safety%')).first()
    if not sk:
        print('ERROR: Safety Knife customer not found')
        sys.exit(1)
    print(f'Customer: {sk.name} (id={sk.id})')

    # Delete all existing Safety Knife orders
    existing = Order.query.filter_by(customer_id=sk.id).all()
    for o in existing:
        print(f'  Deleting: {o.order_ref}')
        db.session.delete(o)
    db.session.commit()
    print(f'Deleted {len(existing)} existing orders.')

    # Price map
    prices = {
        'BIG FISH 9MM N/H 1 SGL':   4.95,
        'BIG FISH 9MM TP 1 SINGLE':  4.80,
        'BIG FISH 9MM 1 SINGLES':    4.95,
        'BIG FISH 9MM TC 1 SINGLE':  4.95,
        '13154002':                  4.95,
        'BC-REAKTA-HD 001':          3.00,
    }

    def parse_date(s):
        """Parse dd/mm/yy string to date."""
        d, m, y = s.strip().split('/')
        y = int(y)
        if y < 100:
            y += 2000
        return date(y, int(m), int(d))

    CUTOFF = date(2026, 5, 1)

    # All orders extracted from the 35 PDFs (deduplicated)
    # (type, order_ref, date_issued_str, date_reqd_str, product_code, qty)
    orders_data = [
        # Works Orders
        ('WO', 'WO25527', '03/06/25', '02/07/25', 'BIG FISH 9MM TP 1 SINGLE',  500),
        ('WO', 'WO25528', '03/06/25', '14/07/25', 'BIG FISH 9MM N/H 1 SGL',    500),
        ('WO', 'WO25529', '03/06/25', '21/07/25', 'BIG FISH 9MM TC 1 SINGLE',  100),
        ('WO', 'WO25530', '03/06/25', '11/08/25', 'BIG FISH 9MM TP 1 SINGLE',  500),
        ('WO', 'WO25531', '03/06/25', '11/08/25', 'BIG FISH 9MM N/H 1 SGL',    800),
        ('WO', 'WO25727', '14/08/25', '16/09/25', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO25845', '23/09/25', '21/10/25', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO25892', '21/10/25', '10/11/25', 'BIG FISH 9MM 1 SINGLES',    500),
        ('WO', 'WO25893', '21/10/25', '10/11/25', 'BIG FISH 9MM N/H 1 SGL',    500),
        ('WO', 'WO25997', '18/11/25', '11/12/25', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO26088', '15/12/25', '12/01/26', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO26089', '15/12/25', '12/01/26', 'BIG FISH 9MM TP 1 SINGLE',  500),
        ('WO', 'WO26161', '19/01/26', '16/02/26', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO26162', '19/01/26', '09/03/26', 'BIG FISH 9MM N/H 1 SGL',     96),
        ('WO', 'WO26287', '02/03/26', '13/04/26', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO26288', '02/03/26', '13/04/26', 'BIG FISH 9MM TP 1 SINGLE',  300),
        ('WO', 'WO26289', '02/03/26', '07/04/26', 'BIG FISH 9MM 1 SINGLES',    100),
        ('WO', 'WO26351', '17/03/26', '23/04/26', '13154002',                  1000),
        ('WO', 'WO26436', '23/04/26', '23/04/26', 'BIG FISH 9MM N/H 1 SGL',    500),
        ('WO', 'WO26437', '23/04/26', '11/05/26', 'BIG FISH 9MM TP 1 SINGLE',  200),
        ('WO', 'WO26438', '23/04/26', '08/06/26', 'BIG FISH 9MM N/H 1 SGL',   1000),
        ('WO', 'WO26458', '30/04/26', '18/05/26', '13154002',                  1000),
        ('WO', 'WO26459', '30/04/26', '15/06/26', '13154002',                  1000),
        # Purchase Orders (blades)
        ('PO', '8583',    '03/06/25', '02/07/25', 'BC-REAKTA-HD 001',           500),
        ('PO', '8584',    '03/06/25', '05/08/25', 'BC-REAKTA-HD 001',           500),
        ('PO', '8655',    '18/08/25', '06/10/25', 'BC-REAKTA-HD 001',           500),
        ('PO', '8683',    '23/09/25', '05/11/25', 'BC-REAKTA-HD 001',           500),
        ('PO', '8748',    '06/01/26', '26/01/26', 'BC-REAKTA-HD 001',           500),
        ('PO', '8749',    '06/01/26', '16/02/26', 'BC-REAKTA-HD 001',           500),
        ('PO', '8750',    '06/01/26', '16/03/26', 'BC-REAKTA-HD 001',           500),
        ('PO', '8876',    '30/04/26', '12/05/26', 'BC-REAKTA-HD 001',           500),
        ('PO', '8877',    '30/04/26', '22/06/26', 'BC-REAKTA-HD 001',           500),
    ]

    created = 0
    for doc_type, ref, issued_str, reqd_str, prod_code, qty in orders_data:
        issued = parse_date(issued_str)
        reqd   = parse_date(reqd_str)

        prod = Product.query.filter_by(code=prod_code).first()
        if not prod:
            print(f'  SKIP (product not found): {prod_code}')
            continue

        price = prices.get(prod_code, 0)
        invoiced = reqd < CUTOFF
        status = 'invoiced' if invoiced else 'confirmed'
        dispatched_date = reqd if invoiced else None

        order = Order(
            order_ref=ref,
            customer_id=sk.id,
            status=status,
            required_date=reqd,
            dispatched_date=dispatched_date,
            notes=f'Imported from Safety Knife {doc_type} {ref}',
        )
        # Set created_at to issued date so timeline is correct
        from datetime import datetime
        order.created_at = datetime(issued.year, issued.month, issued.day)
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=prod.id,
            qty=float(qty),
            qty_dispatched=float(qty) if invoiced else 0.0,
            unit_price=price,
        )
        db.session.add(item)
        print(f'  {status.upper():10s} {ref:12s} | {prod_code:30s} x{qty:5d} @ £{price:.2f} | reqd {reqd_str}')
        created += 1

    db.session.commit()
    print(f'\nDone. Created {created} orders.')
