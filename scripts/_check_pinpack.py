import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from app import create_app
from models import Product, BOMItem, Material
app = create_app()
with app.app_context():
    print('Products with 1.5" lay flat (mat id=8):')
    for b in BOMItem.query.filter_by(material_id=8).all():
        p = Product.query.get(b.product_id)
        code = p.code if p else 'unknown'
        print(f'  {code}  qty={b.qty_per_unit}')
    print()
    print('Products with pin pack sub-assembly:')
    pack4 = Product.query.filter_by(code='PIN/PACK/4').first()
    pack6 = Product.query.filter_by(code='PIN/PACK/6').first()
    ids = [p.id for p in [pack4, pack6] if p]
    for b in BOMItem.query.filter(BOMItem.component_product_id.in_(ids)).all():
        p = Product.query.get(b.product_id)
        pack = Product.query.get(b.component_product_id)
        pcode = p.code if p else 'unknown'
        packcode = pack.code if pack else 'unknown'
        print(f'  {pcode} -> {packcode}')
