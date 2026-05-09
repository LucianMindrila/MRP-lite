import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import Customer, Order, Product

    nuco = Customer.query.filter(Customer.name.like('%Nuco%')).first()
    print('Nuco customer:', nuco.name if nuco else 'NOT FOUND')
    if nuco:
        for o in Order.query.filter_by(customer_id=nuco.id).all():
            print(f'  Existing order: {o.order_ref} | {o.status} | {len(o.items)} items')

    codes = [
        '101504','101505','102537','102540','102542','102543','105278','105279',
        '105280','108497','108509','109294','109405','109796','109827','110223',
        '508615','508619','508620','508621','10050','10386','10389','10390',
        '10392','10393','APT006105','APT009748','APT010718','UJK0000111','UJK000012','APT008645',
    ]
    print()
    for code in codes:
        p = Product.query.filter_by(code=code).first()
        status = f'EXISTS — {p.name} @ £{p.sale_price}' if p else 'MISSING'
        print(f'  {code}: {status}')
