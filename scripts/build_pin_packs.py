"""build_pin_packs.py — Create 4-pin and 6-pin pack sub-assemblies and
update all product BOMs to use them instead of raw pins + lay flat.

Changes:
  1. Create PIN/PACK/4 sub-assembly  (4 pins + 0.2m lay flat, heat-sealed)
  2. Create PIN/PACK/6 sub-assembly  (6 pins + 0.2m lay flat, heat-sealed)
  3. For every product BOM that currently has 10MM PIN:
       - Remove the direct 10MM PIN line
       - Add PIN/PACK/4 or PIN/PACK/6 (qty=1) based on pin count
  4. Fix H/KWJ650 and H/KWJ950 pin qty (still 6 in DB, PDF says 4)
     — handled automatically by step 3 (they'll get the 4-pack)

Run:
  python scripts/build_pin_packs.py           # dry-run
  python scripts/build_pin_packs.py --commit  # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, Material, BOMItem

PIN_MAT_ID      = 7    # 10MM PIN  (£0.07/pcs)
LAY_FLAT_ID     = 8    # 1 1/2 LAY FLAT  (£0.135/m)
PIN_QTY_PER_M   = 0.2  # 0.2m lay flat per pack


def make_pack(dry, pins, pin_mat, lf_mat):
    code = f'PIN/PACK/{pins}'
    name = f'{pins}-Pin Pack (heat-sealed lay flat)'
    pack = Product.query.filter_by(code=code).first()
    if pack:
        print(f'  EXISTS: {code} id={pack.id}')
        return pack

    cost = round(pins * pin_mat.cost_price + PIN_QTY_PER_M * lf_mat.cost_price, 4)
    print(f'  CREATE: {code}  sale_price=£{cost:.4f}  (is_subassembly)')
    if not dry:
        pack = Product(code=code, name=name, unit='pcs',
                       sale_price=cost, lead_time_days=1, is_subassembly=True)
        db.session.add(pack)
        db.session.flush()
        db.session.add(BOMItem(product_id=pack.id, material_id=pin_mat.id,
                               qty_per_unit=float(pins)))
        db.session.add(BOMItem(product_id=pack.id, material_id=lf_mat.id,
                               qty_per_unit=PIN_QTY_PER_M))
        print(f'    BOM: {pins} × {pin_mat.code}  +  {PIN_QTY_PER_M}m × {lf_mat.code}')
    return pack


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():
        pin_mat = Material.query.get(PIN_MAT_ID)
        lf_mat  = Material.query.get(LAY_FLAT_ID)

        # ── 1 & 2. Create pin pack sub-assemblies ────────────────────────
        print('\n[1] Create PIN/PACK/4')
        pack4 = make_pack(dry, 4, pin_mat, lf_mat)

        print('\n[2] Create PIN/PACK/6')
        pack6 = make_pack(dry, 6, pin_mat, lf_mat)

        if not dry:
            db.session.flush()

        # ── 2b. Fix any remaining wrong pin quantities ────────────────────
        print('\n[2b] Fix remaining wrong pin quantities')
        FORCE_PIN_QTY = {'H/KWJ650': 4, 'H/KWJ950': 4}
        for code, correct_qty in FORCE_PIN_QTY.items():
            p = Product.query.filter_by(code=code).first()
            if not p:
                continue
            b = BOMItem.query.filter_by(product_id=p.id, material_id=PIN_MAT_ID).first()
            if b and int(b.qty_per_unit) != correct_qty:
                print(f'  FIX {code}: pins {int(b.qty_per_unit)} → {correct_qty}')
                if not dry:
                    b.qty_per_unit = float(correct_qty)

        # ── 3. Update all product BOMs ────────────────────────────────────
        print('\n[3] Swap raw pins → pin pack sub-assembly in all product BOMs')

        pin_boms = BOMItem.query.filter_by(material_id=PIN_MAT_ID).all()
        swapped = skipped = 0

        for b in pin_boms:
            # Skip if this is a pin pack's own BOM line
            owner = Product.query.get(b.product_id)
            if not owner or owner.is_subassembly:
                continue

            pin_qty = int(b.qty_per_unit)
            if pin_qty == 4:
                target_pack = pack4
            elif pin_qty == 6:
                target_pack = pack6
            else:
                print(f'  SKIP {owner.code}: unexpected pin qty={b.qty_per_unit} — handle manually')
                skipped += 1
                continue

            print(f'  {owner.code}: remove {pin_qty} pins → add {target_pack.code if not dry else f"PIN/PACK/{pin_qty}"}')
            if not dry:
                db.session.delete(b)
                already = BOMItem.query.filter_by(product_id=owner.id,
                                                   component_product_id=target_pack.id).first()
                if not already:
                    db.session.add(BOMItem(product_id=owner.id,
                                           component_product_id=target_pack.id,
                                           qty_per_unit=1.0))
            swapped += 1

        if not dry:
            db.session.commit()

        print(f'\n{"="*55}')
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}{swapped} product(s) updated, {skipped} skipped.')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
