"""build_strike_jig_bom.py — Create all materials and BOM lines for ASSE/STRIKE/JIG.

Parts:
  - 18 Trend free-issued components (STRIKE/M1-M12, STRIKE/P1-P6), cost £0
  - Lock plate - large (machined in-house from HPL, 30/sheet)
  - Mortise plate - small (machined in-house from HPL, 75/sheet)

Run:
  python scripts/build_strike_jig_bom.py           # dry-run
  python scripts/build_strike_jig_bom.py --commit  # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, Material, BOMItem, Category

HPL_COST      = 111.30
CAT_FREE      = 4    # Fishknife Free Issued
CAT_SHEET     = 1    # Sheet Materials

TREND_PARTS = [
    ('STRIKE/M1',  'Mortise Top/Bottom Plate',   2),
    ('STRIKE/M2',  'Mortise LH Plate',            1),
    ('STRIKE/M3',  'Mortise RH Plate',            1),
    ('STRIKE/M4',  "Strike Top Plate 'B'",        1),
    ('STRIKE/M5',  "Strike Bottom Plate 'A'",     1),
    ('STRIKE/M6',  "Strike Tongue Plate 'B'",     1),
    ('STRIKE/M7',  'Strike Edge Guide',            2),
    ('STRIKE/M8',  'Strike Edge Guide Plate',      2),
    ('STRIKE/M9',  'Strike Edge Guide Spacer',     2),
    ('STRIKE/M10', 'Strike Tongue Plate Nut',      2),
    ('STRIKE/M11', 'Flanged Nut',                  6),
    ('STRIKE/M12', "Strike Tongue Plate 'A'",      1),
    ('STRIKE/P1',  "Top/Bottom Gauge 'A/B'",       2),
    ('STRIKE/P2',  "Tongue Strike Gauge 'A'",      1),
    ('STRIKE/P3',  "Tongue Strike Gauge 'B'",      1),
    ('STRIKE/P4',  'Deadbolt Gauge',               1),
    ('STRIKE/P5',  'Pin',                          4),
    ('STRIKE/P6',  'Rebate Spacer',                2),
]

HPL_PARTS = [
    ('STRIKE/LOCK/LG',  'Lock Plate - Large (machined in-house)',  round(HPL_COST / 30, 2),  1),
    ('STRIKE/MORT/SM',  'Mortise Plate - Small (machined in-house)', round(HPL_COST / 75, 2), 1),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():
        p = Product.query.filter_by(code='ASSE/STRIKE/JIG').first()
        if not p:
            sys.exit('Product ASSE/STRIKE/JIG not found.')

        existing_mat_ids = {b.material_id for b in BOMItem.query.filter_by(product_id=p.id).all()}
        created = added = 0

        def get_or_create(code, name, cost, cat_id):
            nonlocal created
            m = Material.query.filter_by(code=code).first()
            if not m:
                print(f'  CREATE £{cost:5.2f}  {code:20s}  {name}')
                if not dry:
                    m = Material(code=code, name=name, cost_price=cost,
                                 unit='pcs', category_id=cat_id)
                    db.session.add(m)
                    db.session.flush()
                created += 1
            else:
                print(f'  EXIST  £{cost:5.2f}  {code:20s}  {name}')
            return m

        def add_bom(mat, qty):
            nonlocal added
            if mat and mat.id and mat.id in existing_mat_ids:
                print(f'           SKIP (already in BOM): {mat.code}')
                return
            print(f'           ADD  qty={qty}')
            if not dry and mat and mat.id:
                db.session.add(BOMItem(product_id=p.id, material_id=mat.id, qty_per_unit=qty))
                existing_mat_ids.add(mat.id)
            added += 1

        print('--- Trend free-issued parts (£0) ---')
        for code, name, qty in TREND_PARTS:
            m = get_or_create(code, name, 0.0, CAT_FREE)
            add_bom(m, qty)

        print('\n--- HPL machined in-house parts ---')
        for code, name, cost, qty in HPL_PARTS:
            m = get_or_create(code, name, cost, CAT_SHEET)
            add_bom(m, qty)

        if not dry:
            db.session.commit()

        print(f'\n{"="*50}')
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}{created} material(s) created, {added} BOM line(s) added.')
        bom_cost = sum(
            b.qty_per_unit * (Material.query.get(b.material_id).cost_price or 0)
            for b in BOMItem.query.filter_by(product_id=p.id).all()
            if Material.query.get(b.material_id)
        ) if not dry else 0
        if not dry:
            print(f'Total BOM material cost: £{bom_cost:.2f}')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
