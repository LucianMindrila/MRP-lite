from app import create_app
app = create_app()
with app.app_context():
    from models import db, Product, Customer

    trend_customer = Customer.query.filter(Customer.name.ilike('%Trend%')).first()
    cid = trend_customer.id if trend_customer else None
    print('Linking to customer:', trend_customer.name if trend_customer else 'None')

    new_products = [
        Product(code='BS/JIG/PRO', name='Belfast Sink Jig Pro',      sale_price=52.00, unit='pcs', lead_time_days=1, customer_id=cid),
        Product(code='KWJ900',     name='Kitchen Worktop Jig 900mm', sale_price=61.06, unit='pcs', lead_time_days=1, customer_id=cid),
    ]

    for p in new_products:
        db.session.add(p)
        print('Added:', p.code, '-', p.name, '@ £' + str(p.sale_price))

    db.session.commit()
    print('Done.')
