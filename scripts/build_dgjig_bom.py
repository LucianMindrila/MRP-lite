"""build_dgjig_bom.py — Build DG/JIG/A multi-level BOM and fix lay flat across all products.

Changes:
  1. Fix "1 1/2 LAY FLAT" cost: £18.50/roll → £0.135/m (£13.50 / 100m)
  2. Update all lay flat BOM quantities from 0.01 to 0.2 (20cm per jig)
  3. Remove lay flat from products that shouldn't have it (per Trend PDF):
       KWJ650, KWJ700/A, KWJ700/PRO, KWJ950/PRO, BS/JIG/PRO
  4. Create "1 INCH LAY FLAT" material (£0.135/m, Springpack)
  5. Create "FOAM/PEANUTS" material (£0.001/pcs, Springpack)
  6. Create DG/JIG/BODY sub-assembly product + BOM (HPL × 0.1, 10/sheet)
  7. Create DG/JIG/RAIL sub-assembly product + BOM (HPL × 0.003571, 280/sheet)
  8. Rebuild DG/JIG/A BOM:
       Remove: raw HPL, ABS pins, 1.5" lay flat, EU label
       Add: Body (×1), Rail (×5), M5×16 black screws (×15),
            hex wrench (×1), 1" lay flat (×0.2m), foam peanuts (×10)

Run:
  python scripts/build_dgjig_bom.py           # dry-run
  python scripts/build_dgjig_bom.py --commit  # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, Material, BOMItem, Category, Supplier

LAY_FLAT_15_ID  = 8      # 1 1/2 LAY FLAT
PIN_MAT_ID      = 7      # 10MM PIN
HPL_CODE        = '12MM HPL'
SUP_SPRINGPACK  = 6
CAT_CONSUMABLES = 9
CAT_SHEET       = 1

LAYFLAT_COST_PER_M = round(13.50 / 100, 4)   # £0.135/m
LAYFLAT_QTY_PER_JIG = 0.2                     # 20cm = 0.2m

NO_LAYFLAT = {'KWJ650', 'KWJ700/A', 'KWJ700/PRO', 'KWJ950/PRO', 'BS/JIG/PRO'}


def log(dry, msg):
    prefix = '[DRY] ' if dry else '      '
    print(f'{prefix}{msg}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():

        hpl = Material.query.filter_by(code=HPL_CODE).first()
        lf15 = Material.query.get(LAY_FLAT_15_ID)

        # ── 1. Fix 1.5" lay flat cost ─────────────────────────────────────
        print('\n[1] Fix 1.5" lay flat cost')
        log(dry, f'Update {lf15.code}: cost £{lf15.cost_price} → £{LAYFLAT_COST_PER_M}/m')
        if not dry:
            lf15.cost_price = LAYFLAT_COST_PER_M

        # ── 2 & 3. Fix all lay flat BOM quantities ────────────────────────
        print('\n[2/3] Fix lay flat BOM quantities / remove where not needed')
        for b in BOMItem.query.filter_by(material_id=LAY_FLAT_15_ID).all():
            p = Product.query.get(b.product_id)
            if not p:
                continue
            if p.code in NO_LAYFLAT:
                log(dry, f'REMOVE lay flat from {p.code}')
                if not dry:
                    db.session.delete(b)
            else:
                log(dry, f'UPDATE qty {b.qty_per_unit} → {LAYFLAT_QTY_PER_JIG}m for {p.code}')
                if not dry:
                    b.qty_per_unit = LAYFLAT_QTY_PER_JIG

        # ── 4. Create 1" lay flat ─────────────────────────────────────────
        print('\n[4] Create 1 inch lay flat material')
        lf1 = Material.query.filter_by(code='1 INCH LAY FLAT').first()
        if not lf1:
            log(dry, f'CREATE: 1 INCH LAY FLAT  £{LAYFLAT_COST_PER_M}/m  (Springpack)')
            if not dry:
                lf1 = Material(code='1 INCH LAY FLAT', name='1 inch lay flat tubing',
                               unit='m', cost_price=LAYFLAT_COST_PER_M,
                               supplier_id=SUP_SPRINGPACK, category_id=CAT_CONSUMABLES)
                db.session.add(lf1)
                db.session.flush()
        else:
            log(dry, f'EXISTS: {lf1.code} id={lf1.id}')

        # ── 5. Create foam peanuts ────────────────────────────────────────
        print('\n[5] Create foam peanuts material')
        foam = Material.query.filter_by(code='FOAM/PEANUTS').first()
        if not foam:
            log(dry, 'CREATE: FOAM/PEANUTS  £0.001/pcs  (Springpack)')
            if not dry:
                foam = Material(code='FOAM/PEANUTS',
                                name='Foam Peanuts / Biodegradable Padding',
                                unit='pcs', cost_price=0.001,
                                supplier_id=SUP_SPRINGPACK, category_id=CAT_CONSUMABLES)
                db.session.add(foam)
                db.session.flush()
        else:
            log(dry, f'EXISTS: {foam.code} id={foam.id}')

        # ── 6. Create DG/JIG/BODY sub-assembly ───────────────────────────
        print('\n[6] Create DG/JIG/BODY sub-assembly')
        body_cost = round(hpl.cost_price / 10, 2)   # 10 per sheet
        body = Product.query.filter_by(code='DG/JIG/BODY').first()
        if not body:
            log(dry, f'CREATE product: DG/JIG/BODY  sale_price=£{body_cost} (cost to make)')
            if not dry:
                body = Product(code='DG/JIG/BODY',
                               name='DG/JIG Body (machined in-house)',
                               unit='pcs', sale_price=body_cost,
                               lead_time_days=1, is_subassembly=True)
                db.session.add(body)
                db.session.flush()
                db.session.add(BOMItem(product_id=body.id,
                                       material_id=hpl.id,
                                       qty_per_unit=round(1/10, 4)))
                log(dry, f'  BOM: HPL × {round(1/10,4)} (10 bodies/sheet)')
        else:
            log(dry, f'EXISTS: {body.code} id={body.id}')

        # ── 7. Create DG/JIG/RAIL sub-assembly ───────────────────────────
        print('\n[7] Create DG/JIG/RAIL sub-assembly')
        rail_cost = round(hpl.cost_price / 280, 4)  # 280 per sheet
        rail = Product.query.filter_by(code='DG/JIG/RAIL').first()
        if not rail:
            log(dry, f'CREATE product: DG/JIG/RAIL  sale_price=£{rail_cost} (cost to make)')
            if not dry:
                rail = Product(code='DG/JIG/RAIL',
                               name='DG/JIG Rail (machined in-house)',
                               unit='pcs', sale_price=rail_cost,
                               lead_time_days=1, is_subassembly=True)
                db.session.add(rail)
                db.session.flush()
                db.session.add(BOMItem(product_id=rail.id,
                                       material_id=hpl.id,
                                       qty_per_unit=round(1/280, 6)))
                log(dry, f'  BOM: HPL × {round(1/280,6)} (280 rails/sheet)')
        else:
            log(dry, f'EXISTS: {rail.code} id={rail.id}')

        # ── 8. Rebuild DG/JIG/A BOM ───────────────────────────────────────
        print('\n[8] Rebuild DG/JIG/A BOM')
        dgjig = Product.query.filter_by(code='DG/JIG/A').first()

        # Materials to remove
        REMOVE_MAT_CODES = {HPL_CODE, '10MM PIN', '1 1/2 LAY FLAT', 'LAB.EU.ADD'}
        for b in BOMItem.query.filter_by(product_id=dgjig.id).all():
            m = Material.query.get(b.material_id)
            if m and m.code in REMOVE_MAT_CODES:
                log(dry, f'REMOVE from BOM: {m.code}')
                if not dry:
                    db.session.delete(b)

        def add_mat(mat, qty):
            if not mat or not mat.id:
                return
            exists = BOMItem.query.filter_by(product_id=dgjig.id, material_id=mat.id).first()
            if exists:
                log(dry, f'EXISTS in BOM: {mat.code} qty={exists.qty_per_unit}')
            else:
                log(dry, f'ADD MAT: {mat.code} × {qty}')
                if not dry:
                    db.session.add(BOMItem(product_id=dgjig.id,
                                           material_id=mat.id, qty_per_unit=qty))

        def add_sub(sub_prod, qty):
            if not sub_prod or not sub_prod.id:
                return
            exists = BOMItem.query.filter_by(product_id=dgjig.id,
                                              component_product_id=sub_prod.id).first()
            if exists:
                log(dry, f'EXISTS in BOM: {sub_prod.code} qty={exists.qty_per_unit}')
            else:
                log(dry, f'ADD SUB: {sub_prod.code} × {qty}')
                if not dry:
                    db.session.add(BOMItem(product_id=dgjig.id,
                                           component_product_id=sub_prod.id,
                                           qty_per_unit=qty))

        # Flush removals before adding so IDs are consistent
        if not dry:
            db.session.flush()

        add_sub(body, 1)
        add_sub(rail, 5)
        add_mat(Material.query.get(110), 15)   # M5 x 16 Black Socket Screw
        add_mat(Material.query.get(107), 1)    # 3mm Hex Wrench
        add_mat(lf1, LAYFLAT_QTY_PER_JIG)     # 1" lay flat 0.2m
        add_mat(foam, 10)                      # Foam peanuts

        if not dry:
            db.session.commit()

        print(f'\n{"="*55}')
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}Done.')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
