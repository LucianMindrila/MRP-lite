import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from app import create_app
from models import Material, Supplier, BOMItem, Product
app = create_app()
with app.app_context():
    s = Supplier.query.filter(Supplier.name.ilike('%springpack%')).first()
    print(f'Springpack id={s.id if s else None}')
    lf = Material.query.filter_by(code='1 1/2 LAY FLAT').first()
    print(f'Lay flat: id={lf.id}, cost={lf.cost_price}, unit={lf.unit}')
    for b in BOMItem.query.filter_by(material_id=lf.id).all():
        p = Product.query.get(b.product_id)
        code = p.code if p else 'unknown'
        print(f'  Used in: {code}  qty={b.qty_per_unit}')
