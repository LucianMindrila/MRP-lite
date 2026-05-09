import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import Customer, Order, Product

    trend = Customer.query.filter(Customer.name.like('%Trend%')).first()
    print('Trend customer:', trend.name if trend else 'NOT FOUND', f'id={trend.id}' if trend else '')
    if trend:
        for o in Order.query.filter_by(customer_id=trend.id).order_by(Order.order_ref).all():
            print(f'  {o.order_ref} | {o.status} | {len(o.items)} items')

    codes = [
        'AR/JIG','ASSE/HJ/C','ASSE/STRIKE/JIG','BS/JIG/PRO','DG/JIG/A',
        'ECL/02','ECL/JIG','H/CURVE/JIG','H/KWJ650','H/KWJ950',
        'KWJ/PIN/10MM','KWJ650','KWJ700','KWJ700/A','KWJ700/PRO',
        'KWJ900','KWJ950/PRO','LOCK/JIG/B','LOCK/JIG/B/US',
        'MFT/01','MFT/JIG','RS/JIG','S/KWJ700','S/KWJ900','TEMP/SS/A',
    ]
    print()
    for code in codes:
        p = Product.query.filter_by(code=code).first()
        print(f'  {code}: {"EXISTS @ £" + str(p.sale_price) if p else "MISSING"}')
