"""fix_boms_trend2.py — Fix remaining BOM issues from Trend May 2026 price sheet.

Changes applied:
  1. KWJ700/A  — swap MANU/KWJ79 for dedicated KWJ700/A 52pp manual
  2. KWJ700/PRO — swap MANU/KWJ79 for 72pp Pro manual
  3. Create + add KWJ650 manual (Spot On Print, £0.71)
  4. Create + add BS/JIG/PRO manual (Spot On Print, £1.13)
  5. Create + add RS/JIG manual (Spot On Print, £1.17)
  6. Create + add H/CURVE/JIG box (RH Fibreboard, £1.45)
  7. Create + add RS/JIG box (RH Fibreboard, £0.52)
  8. Fix pin quantities: KWJ650 6→4, KWJ700/A 6→4, H/CURVE/JIG 6→4, DG/JIG/A 6→2
  9. Remove pin BOM item from BS/JIG/PRO (PDF: 0 pins)
 10. Remove lay flat tubbing from H/KWJ650, H/KWJ950, H/CURVE/JIG (PDF: not used)

Run:
  python scripts/fix_boms_trend2.py           # dry-run
  python scripts/fix_boms_trend2.py --commit  # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, Material, BOMItem, Category, Supplier

SUP_SPOT_ON   = 46   # Spot On Print
SUP_RH_FIBRE  = 19   # RH Fibreboard
MAT_PIN       = 7    # 10MM PIN
MAT_LAY_FLAT  = 8    # 1 1/2 LAY FLAT


def get_or_create_material(dry, cat_id, code, name, cost, supplier_id, log):
    m = Material.query.filter_by(code=code).first()
    if m:
        log.append(f'  EXISTING material: {code} (id={m.id})')
        return m
    log.append(f'  CREATE material: {code} — {name}  £{cost:.2f}')
    if not dry:
        m = Material(code=code, name=name, cost_price=cost,
                     unit='pcs', category_id=cat_id, supplier_id=supplier_id)
        db.session.add(m)
        db.session.flush()
    return m


def get_bom(product_id, material_id):
    return BOMItem.query.filter_by(
        product_id=product_id, material_id=material_id).first()


def add_bom(dry, product, material, qty, log):
    if get_bom(product.id, material.id):
        log.append(f'  SKIP (exists): {product.code} ← {material.code}')
        return
    log.append(f'  ADD bom qty={qty:.3f}: {product.code} ← {material.code}')
    if not dry and material.id:
        db.session.add(BOMItem(product_id=product.id,
                               material_id=material.id, qty_per_unit=qty))


def remove_bom(dry, product, material_id, log):
    b = BOMItem.query.filter_by(product_id=product.id, material_id=material_id).first()
    if not b:
        log.append(f'  SKIP (not found): remove material_id={material_id} from {product.code}')
        return
    m = Material.query.get(material_id)
    log.append(f'  REMOVE bom: {product.code} ← {m.code if m else material_id}')
    if not dry:
        db.session.delete(b)


def fix_pin_qty(dry, product, new_qty, log):
    b = BOMItem.query.filter_by(product_id=product.id, material_id=MAT_PIN).first()
    if not b:
        log.append(f'  SKIP: no pin BOM found for {product.code}')
        return
    log.append(f'  FIX pin qty: {product.code}  {b.qty_per_unit} → {new_qty}')
    if not dry:
        b.qty_per_unit = new_qty


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():
        log = []

        cat_manuals = Category.query.filter_by(name='Manuals and Labels').first()
        cat_boxes   = Category.query.filter_by(name='Cardboard Boxes').first()

        # Existing materials we'll reference
        manu_kwj79     = Material.query.filter_by(code='MANU/KWJ79').first()
        manu_kwj700a   = Material.query.filter_by(code='MANU-KWJ700A-MANUAL-OFFSET-P').first()
        manu_72pp      = Material.query.filter_by(code='KWJ700950PROJIG-MANUAL-72PP').first()

        p_kwj700a      = Product.query.filter_by(code='KWJ700/A').first()
        p_kwj700pro    = Product.query.filter_by(code='KWJ700/PRO').first()
        p_kwj650       = Product.query.filter_by(code='KWJ650').first()
        p_bsjig        = Product.query.filter_by(code='BS/JIG/PRO').first()
        p_rsjig        = Product.query.filter_by(code='RS/JIG').first()
        p_hcurve       = Product.query.filter_by(code='H/CURVE/JIG').first()
        p_hkwj650      = Product.query.filter_by(code='H/KWJ650').first()
        p_hkwj950      = Product.query.filter_by(code='H/KWJ950').first()
        p_dgjig        = Product.query.filter_by(code='DG/JIG/A').first()

        # ── 1. KWJ700/A: swap manual ─────────────────────────────────────
        log.append('\n[1] KWJ700/A — swap manual')
        if p_kwj700a and manu_kwj79 and manu_kwj700a:
            remove_bom(dry, p_kwj700a, manu_kwj79.id, log)
            add_bom(dry, p_kwj700a, manu_kwj700a, 1.0, log)

        # ── 2. KWJ700/PRO: swap manual ───────────────────────────────────
        log.append('\n[2] KWJ700/PRO — swap manual')
        if p_kwj700pro and manu_kwj79 and manu_72pp:
            remove_bom(dry, p_kwj700pro, manu_kwj79.id, log)
            add_bom(dry, p_kwj700pro, manu_72pp, 1.0, log)

        # ── 3. KWJ650: create + add manual ───────────────────────────────
        log.append('\n[3] KWJ650 — create + add manual')
        manu_kwj650 = get_or_create_material(
            dry, cat_manuals.id, 'MANU/KWJ650',
            'Kitchen Worktop Jig 650mm Manual', 0.71, SUP_SPOT_ON, log)
        if p_kwj650 and manu_kwj650:
            add_bom(dry, p_kwj650, manu_kwj650, 1.0, log)

        # ── 4. BS/JIG/PRO: create + add manual ───────────────────────────
        log.append('\n[4] BS/JIG/PRO — create + add manual')
        manu_bsjig = get_or_create_material(
            dry, cat_manuals.id, 'MANU/BS/JIG',
            'Belfast Sink Jig Pro Manual', 1.13, SUP_SPOT_ON, log)
        if p_bsjig and manu_bsjig:
            add_bom(dry, p_bsjig, manu_bsjig, 1.0, log)

        # ── 5. RS/JIG: create + add manual ───────────────────────────────
        log.append('\n[5] RS/JIG — create + add manual')
        manu_rsjig = get_or_create_material(
            dry, cat_manuals.id, 'MANU/RS/JIG',
            'Router Surfacing Jig Manual', 1.17, SUP_SPOT_ON, log)
        if p_rsjig and manu_rsjig:
            add_bom(dry, p_rsjig, manu_rsjig, 1.0, log)

        # ── 6. H/CURVE/JIG: create + add box ─────────────────────────────
        log.append('\n[6] H/CURVE/JIG — create + add box')
        box_hcurve = get_or_create_material(
            dry, cat_boxes.id, 'H/CURVE/JIG BOX',
            'Howden Curve Jig Box', 1.45, SUP_RH_FIBRE, log)
        if p_hcurve and box_hcurve:
            add_bom(dry, p_hcurve, box_hcurve, 1.0, log)

        # ── 7. RS/JIG: create + add box ──────────────────────────────────
        log.append('\n[7] RS/JIG — create + add box')
        box_rsjig = get_or_create_material(
            dry, cat_boxes.id, 'RS/JIG BOX',
            'Router Surfacing Jig Box', 0.52, SUP_RH_FIBRE, log)
        if p_rsjig and box_rsjig:
            add_bom(dry, p_rsjig, box_rsjig, 1.0, log)

        # ── 8. Fix pin quantities ─────────────────────────────────────────
        log.append('\n[8] Fix pin quantities (PDF values)')
        fix_pin_qty(dry, p_kwj650,   4, log)  # was 6, PDF says 4
        fix_pin_qty(dry, p_kwj700a,  4, log)  # was 6, PDF says 4
        fix_pin_qty(dry, p_hcurve,   4, log)  # was 6, PDF says 4
        fix_pin_qty(dry, p_dgjig,    2, log)  # was 6, PDF says 2

        # ── 9. BS/JIG/PRO: remove pins (PDF says 0) ──────────────────────
        log.append('\n[9] BS/JIG/PRO — remove pins (PDF: 0 pins)')
        remove_bom(dry, p_bsjig, MAT_PIN, log)

        # ── 10. Remove lay flat from H/KWJ650, H/KWJ950, H/CURVE/JIG ────
        log.append('\n[10] Remove lay flat tubbing (PDF: not used for these)')
        for p in [p_hkwj650, p_hkwj950, p_hcurve]:
            if p:
                remove_bom(dry, p, MAT_LAY_FLAT, log)

        if not dry:
            db.session.commit()

        print('\n'.join(log))
        print()
        print('=' * 60)
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}Done.')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
