import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Material, Supplier, Category, BOMItem, Product

    # Update existing PSL Cardboard supplier with correct details
    psl = Supplier.query.filter_by(name='PSL Cardboard').first()
    if psl:
        psl.name = 'Protective Solutions (UK) Ltd'
        psl.contact = ''
        psl.phone = ''
        psl.address = 'Units 11 & 12, Stonedale Road, Oldends Lane, Stonehouse, Gloucestershire GL10 3RQ'
        print(f'Updated supplier: PSL Cardboard -> Protective Solutions (UK) Ltd (id={psl.id})')
    else:
        psl = Supplier(name='Protective Solutions (UK) Ltd',
                       address='Units 11 & 12, Stonedale Road, Oldends Lane, Stonehouse, Gloucestershire GL10 3RQ')
        db.session.add(psl)
        db.session.flush()
        print(f'Added supplier: Protective Solutions (UK) Ltd (id={psl.id})')

    cat = Category.query.filter_by(name='Cardboard Boxes').first()

    boxes = [
        # code, name, description, price, po_ref, po_date
        ('PSL/DG-JIG-BOX',      'Drainer Groove Jig Protective Box',      '776 x 586 x 30mm (with 25mm overlap). PO 5832_4, dated 05/02/2026.', 1.78),
        ('PSL/LG-ROUTER-BOX',   'Axminster Large Router Top Box',          '800 x 600 x 34mm brown. PO 5880_4, dated 22/04/2026.', 3.30),
        ('PSL/SM-ROUTER-BOX',   'Axminster Small Router Top Box',          '610 x 410 x 34mm (with 25mm overlap). PO 5816_4, dated 26/01/2026.', 2.09),
        ('PSL/FRAME-BOX',       'Axminster Frame Box',                     '155 x 155 x 1145mm. PO 5852_4, dated 02/03/2026.', 2.64),
        ('PSL/VALCHROMAT-BOX',  'Axminster Valchromat MFT Top Box',        '1116 x 726 x 26mm. PO 5801_4, dated 09/01/2026.', 2.34),
        ('PSL/HINGE-JIG-BOX',   'Axminster Hinge Jig Box',                 '482 x 90 x 42mm brown. PO 5723_4, dated 03/09/2025.', 0.80),
        ('PSL/LOCK-JIG-BOX',    'Axminster Lock Jig Box',                  '320 x 120 x 28mm brown. PO 5723_4, dated 03/09/2025.', 0.80),
        ('PSL/LOOSE-PARTS-BOX', 'Axminster Loose Parts Box',               '18" x 18" x 18". PO 5662_4, dated 16/05/2025.', 1.75),
        ('PSL/MFT-JIG-BOX',     'Trend MFT Jig Box',                      '587 x 313 x 14mm. PO 5691_4, dated 01/07/2025.', 1.80),
    ]

    mat_map = {}
    added = 0
    for code, name, desc, price in boxes:
        existing = Material.query.filter_by(code=code).first()
        if not existing:
            m = Material(code=code, name=name, description=desc, cost_price=price,
                         unit='pcs', supplier_id=psl.id, category_id=cat.id,
                         stock_qty=0, reorder_point=0, reorder_qty=0)
            db.session.add(m)
            db.session.flush()
            mat_map[code] = m.id
            print(f'  Added: {code} @ £{price}')
            added += 1
        else:
            mat_map[code] = existing.id
            print(f'  Exists: {code}')

    db.session.commit()

    # BOM links — only where confident
    confident_links = [
        ('PSL/DG-JIG-BOX',     'DG/JIG/A'),
        ('PSL/LOCK-JIG-BOX',   'LOCK/JIG/B'),
        ('PSL/VALCHROMAT-BOX', '102537'),
    ]

    print()
    for mat_code, prod_code in confident_links:
        prod = Product.query.filter_by(code=prod_code).first()
        mid = mat_map.get(mat_code)
        if prod and mid:
            exists = BOMItem.query.filter_by(product_id=prod.id, material_id=mid).first()
            if not exists:
                db.session.add(BOMItem(product_id=prod.id, material_id=mid, qty_per_unit=1.0))
                print(f'  BOM linked: {prod_code} <- {mat_code}')
            else:
                print(f'  BOM exists: {prod_code} <- {mat_code}')
        else:
            print(f'  SKIP: prod={prod_code}, mat={mat_code}')

    db.session.commit()
    print(f'\nDone. Added {added} materials.')
    print()
    print('Unconfirmed BOM links — please advise which products these map to:')
    unconfirmed = [
        ('PSL/LG-ROUTER-BOX',   'Axminster Large Router Top Box — UJK Floor Standing or Bench Top Router Table Top?'),
        ('PSL/SM-ROUTER-BOX',   'Axminster Small Router Top Box — UJK Trim Router Table or Bench Top?'),
        ('PSL/FRAME-BOX',       'Axminster Frame Box — UJK Multifunction Workbench or Router Table Frame?'),
        ('PSL/HINGE-JIG-BOX',   'Axminster Hinge Jig Box — no matching product found'),
        ('PSL/LOOSE-PARTS-BOX', 'Axminster Loose Parts Box — which product?'),
        ('PSL/MFT-JIG-BOX',     'Trend MFT Jig Box — UJK Rail Clamp MFT Top (109796)?'),
    ]
    for code, question in unconfirmed:
        print(f'  {code}: {question}')
