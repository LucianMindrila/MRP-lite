"""update_boms_from_trend.py — Apply BOM updates derived from Trend May 2026 price sheet.

Adds missing BOM lines where the material exists and there is no conflict.
Cleans up orphaned BOM items (pointing to deleted materials).
Flags issues that need manual review.

Run:
  python scripts/update_boms_from_trend.py              # dry-run (preview)
  python scripts/update_boms_from_trend.py --commit     # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, Material, BOMItem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():

        def get_product(code):
            return Product.query.filter_by(code=code).first()

        def get_material(code):
            return Material.query.filter_by(code=code).first()

        def has_bom(product, material):
            return BOMItem.query.filter_by(
                product_id=product.id, material_id=material.id).first() is not None

        def add_bom(product, material, qty, reason):
            if has_bom(product, material):
                print(f'  SKIP (already exists): {product.code} ← {material.code}')
                return
            print(f'  ADD  qty={qty:.3f}  {product.code:20s} ← {material.code}  ({reason})')
            if not dry:
                db.session.add(BOMItem(
                    product_id=product.id,
                    material_id=material.id,
                    qty_per_unit=qty,
                ))

        added = 0
        cleaned = 0

        # ── 1. KWJ950/PRO — add Pro 72pp manual ───────────────────────────
        p = get_product('KWJ950/PRO')
        m = get_material('KWJ700950PROJIG-MANUAL-72PP')
        if p and m:
            add_bom(p, m, 1.0, 'PDF: DTS manual £0.86, Spot On Print 72pp £0.82')
            added += 1

        # ── 2. DG/JIG/A — add 12pp Spot On Print manual ───────────────────
        p = get_product('DG/JIG/A')
        m = get_material('12PP-12-PAGES-210-X-148-1-BL')
        if p and m:
            add_bom(p, m, 1.0, 'PDF: DTS manual £0.27 — exact match')
            added += 1

        # ── 3. RS/JIG — add HPL (12 jigs per sheet → qty 1/12) ────────────
        p = get_product('RS/JIG')
        m = get_material('12MM HPL')
        if p and m:
            add_bom(p, m, round(1/12, 4), 'PDF: 12 jigs/sheet, HPL cost £9.28')
            added += 1

        # ── 4. S/KWJ700 — add Zebra label and EU label (present on KWJ700) ─
        p = get_product('S/KWJ700')
        for mat_code, reason in [
            ('ZEBRA.150', 'Present on KWJ700, missing on S/KWJ700'),
            ('LAB.EU.ADD', 'Present on KWJ700, missing on S/KWJ700'),
        ]:
            m = get_material(mat_code)
            if p and m:
                add_bom(p, m, 1.0, reason)
                added += 1

        # ── 5. H/CURVE/JIG — add EU label ─────────────────────────────────
        p = get_product('H/CURVE/JIG')
        m = get_material('LAB.EU.ADD')
        if p and m:
            add_bom(p, m, 1.0, 'Missing EU label')
            added += 1

        # ── 6. Clean orphaned BOM items (material deleted) ─────────────────
        print('\n--- Checking for orphaned BOM items ---')
        all_boms = BOMItem.query.all()
        for b in all_boms:
            mat = Material.query.get(b.material_id)
            if mat is None:
                prod = Product.query.get(b.product_id)
                prod_code = prod.code if prod else f'product_id={b.product_id}'
                print(f'  ORPHAN bom_id={b.id}  product={prod_code}  '
                      f'missing material_id={b.material_id} → delete')
                if not dry:
                    db.session.delete(b)
                cleaned += 1

        if not dry:
            db.session.commit()

        # ── 7. Report issues for manual review ────────────────────────────
        print('\n' + '='*60)
        print('ISSUES FLAGGED FOR MANUAL REVIEW:')
        print("""
  KWJ700/A  — manual is MANU/KWJ79 (KWJ700 manual, £0.57) but PDF
               says KWJ700/A uses a dedicated 52pp manual at £1.98.
               Correct material: MANU-KWJ700A-MANUAL-OFFSET-P (£1.97, Spot On Print).
               Action: remove MANU/KWJ79 from KWJ700/A BOM, add the correct one.

  KWJ700/PRO — manual is MANU/KWJ79 (£0.57) but PDF says Pro uses a
               72pp manual at £0.86. Correct material: KWJ700950PROJIG-MANUAL-72PP (£0.82).
               Action: remove MANU/KWJ79 from KWJ700/PRO BOM, add the 72pp one.

  KWJ650     — missing manual entirely. PDF says DTS manual at £0.71.
               No matching material in DB yet — needs to be created.

  BS/JIG/PRO — missing manual. PDF says DTS manual at £1.13.
               No matching material in DB yet — needs to be created.

  RS/JIG     — missing manual (PDF £1.17) and box (PDF £0.52).
               No matching materials in DB yet — need to be created.

  H/CURVE/JIG — missing box. PDF says £1.45.
               No matching H/CURVE/JIG box material in DB yet.

  PIN COUNTS (current BOM qty vs PDF):
    KWJ650:      6 pins in BOM, PDF says 4
    KWJ700/A:    6 pins in BOM, PDF says 4
    H/CURVE/JIG: 6 pins in BOM, PDF says 4
    DG/JIG/A:    6 pins in BOM, PDF says 2
    BS/JIG/PRO:  6 pins in BOM, PDF says 0

  LAY FLAT TUBBING (present in BOM but PDF says none needed):
    H/KWJ650, H/KWJ950, H/CURVE/JIG
""")

        print('='*60)
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}{added} BOM line(s) added, {cleaned} orphan(s) removed.')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
