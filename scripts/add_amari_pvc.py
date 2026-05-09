import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Material, Supplier, Category, BOMItem, Product

    # --- Amari Plastics supplier ---
    amari = Supplier.query.filter(Supplier.name.like('%Amari%')).first()
    if amari:
        amari.name = 'Amari Plastics'
        amari.contact = 'Richard Hill'
        amari.phone = '01179 723 900'
        amari.email = 'richard.hill@amariplastics.com'
        print(f'Updated supplier: Amari Plastics (id={amari.id})')
    else:
        amari = Supplier(
            name='Amari Plastics',
            contact='Richard Hill',
            phone='01179 723 900',
            email='richard.hill@amariplastics.com',
        )
        db.session.add(amari)
        db.session.flush()
        print(f'Added supplier: Amari Plastics (id={amari.id})')

    # --- Red PVC sheet material ---
    sheet_cat = Category.query.filter_by(name='Sheet Materials').first()
    if not sheet_cat:
        sheet_cat = Category.query.get(1)
    print(f'Using category: {sheet_cat.name} (id={sheet_cat.id})')

    mat_code = 'PVC.RED.2001X1000X6'
    pvc = Material.query.filter_by(code=mat_code).first()
    if pvc:
        pvc.cost_price = 86.52
        pvc.supplier_id = amari.id
        pvc.category_id = sheet_cat.id
        print(f'Updated material: {mat_code} @ £86.52')
    else:
        pvc = Material(
            code=mat_code,
            name='PVC Red Sheet 2001x1000x6mm',
            description='2001 x 1000 x 6mm PVC Red. PO 5866_4 / ref PO 5782, Amari Plastics.',
            unit='sheet',
            cost_price=86.52,
            supplier_id=amari.id,
            category_id=sheet_cat.id,
            stock_qty=0,
            reorder_point=0,
            reorder_qty=0,
        )
        db.session.add(pvc)
        db.session.flush()
        print(f'Added material: {mat_code} @ £86.52 (id={pvc.id})')

    db.session.commit()

    # --- BOM links: 0.01 sheet to all Safety Knife products except the blade ---
    # Blade to exclude: BC-REAKTA-HD 001
    safety_knife_codes = [
        'BIG FISH 9MM N/H 1 SGL',
        'BIG FISH 9MM TP 1 SINGLE',
        'BIG FISH 9MM 1 SINGLES',
        'BIG FISH 9MM TC 1 SINGLE',
        '13154002',
    ]

    print()
    for prod_code in safety_knife_codes:
        prod = Product.query.filter_by(code=prod_code).first()
        if not prod:
            print(f'  NOT FOUND: {prod_code}')
            continue
        existing = BOMItem.query.filter_by(product_id=prod.id, material_id=pvc.id).first()
        if existing:
            print(f'  BOM exists: {prod_code} <- {mat_code} ({existing.qty_per_unit})')
        else:
            db.session.add(BOMItem(product_id=prod.id, material_id=pvc.id, qty_per_unit=0.01))
            print(f'  BOM linked: {prod_code} <- {mat_code} x 0.01 sheet')

    db.session.commit()
    print('\nDone.')
