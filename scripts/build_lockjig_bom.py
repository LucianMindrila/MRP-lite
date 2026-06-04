"""build_lockjig_bom.py — Build sub-assemblies and BOMs for LOCK/JIG/B and LOCK/JIG/B/US.

Both products share the same machined sub-assemblies.
Differences between UK and US versions (labels, laser-etched variant) to be handled separately.

Run:
  python scripts/build_lockjig_bom.py           # dry-run
  python scripts/build_lockjig_bom.py --commit  # apply
"""
import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Product, BOMItem, Material

# Raw material IDs
HPL_12MM    = 6    # 12MM HPL white, £111.30/sheet
HPL_3MM     = 106  # 3mm white compact laminate Abet, £79.20/sheet
ALU_FLAT    = 136  # 3/4 x 1/8 Alu Flat, £4.15/bar (Dore)
ALU_ANGLE   = 131  # 2 x 1 x 1/4 Alu Angle, £36.00/bar (Dore)
GREY_PVC    = 233  # 2440x1220x10mm grey PVC, £85.67/sheet (Oadby)

# Screw IDs
M5X10_CSK   = 52   # M5x10 Pozi CSK BZP, £0.0209 each (Allcap)
M5X8_CSK    = 51   # M5x8 Pozi CSK BZP, £0.024 each (Allcap)
M6X16_PAN   = 60   # M6x16 Pozi Pan BZP, £0.0297 each (Allcap)


def make_sub(dry, code, name, raw_mat_id, qty_per_sheet_or_bar, note=''):
    """Create a sub-assembly product with a single raw material BOM line."""
    existing = Product.query.filter_by(code=code).first()
    if existing:
        print(f'  EXISTS: {code} (id={existing.id})')
        return existing
    raw = Material.query.get(raw_mat_id)
    cost = round(raw.cost_price / qty_per_sheet_or_bar, 4)
    bom_qty = round(1 / qty_per_sheet_or_bar, 6)
    print(f'  CREATE: {code}  £{cost}  ({qty_per_sheet_or_bar}/bar·sheet){f"  [{note}]" if note else ""}')
    if not dry:
        sub = Product(code=code, name=name, unit='pcs',
                      sale_price=cost, lead_time_days=1, is_subassembly=True)
        db.session.add(sub)
        db.session.flush()
        db.session.add(BOMItem(product_id=sub.id, material_id=raw.id, qty_per_unit=bom_qty))
        return sub
    return None


def add_to_bom(dry, parent, component, qty, label=''):
    """Add a material or sub-product line to a parent BOM."""
    if isinstance(component, Material):
        exists = BOMItem.query.filter_by(product_id=parent.id,
                                         material_id=component.id).first()
        tag = f'MAT {component.code}'
    else:
        if component is None:
            return
        exists = BOMItem.query.filter_by(product_id=parent.id,
                                          component_product_id=component.id).first()
        tag = f'SUB {component.code}'

    if exists:
        print(f'  SKIP (exists): {parent.code} ← {tag}')
        return

    print(f'  ADD qty={qty}  {parent.code} ← {tag}{f"  [{label}]" if label else ""}')
    if not dry:
        if isinstance(component, Material):
            db.session.add(BOMItem(product_id=parent.id,
                                   material_id=component.id, qty_per_unit=qty))
        else:
            db.session.add(BOMItem(product_id=parent.id,
                                   component_product_id=component.id, qty_per_unit=qty))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():

        ljb  = Product.query.filter_by(code='LOCK/JIG/B').first()
        ljbus = Product.query.filter_by(code='LOCK/JIG/B/US').first()

        # ── Create sub-assemblies ─────────────────────────────────────────

        print('\n[1] Jig Body — 12mm white HPL, 25/sheet')
        body = make_sub(dry, 'LOCK/JIG/BODY', 'Lock Jig B Body (12mm white HPL)', HPL_12MM, 25)

        print('\n[2] HPL Insert — 3mm white HPL, 200/sheet')
        insert = make_sub(dry, 'LOCK/JIG/HPL-INSERT',
                          'Lock Jig B HPL Insert (3mm white compact laminate)', HPL_3MM, 200)

        print('\n[3] Sliding Pair — 3/4 x 1/8 Alu Flat, 18 jigs/bar → 36 pairs/bar')
        slide = make_sub(dry, 'LOCK/JIG/SLIDE-PAIR',
                         'Lock Jig B Sliding Plate Pair (3/4 x 1/8 alu flat)', ALU_FLAT, 36)

        print('\n[4] Clamping Plate — 2x1x1/4 Alu Angle, 10/bar')
        clamp = make_sub(dry, 'LOCK/JIG/CLAMP',
                         'Lock Jig B Clamping Plate (2x1x1/4 alu angle, wrapped in bubble wrap)',
                         ALU_ANGLE, 10, note='wrap in bubble wrap')

        print('\n[5] Setting Block — 10mm grey PVC, 500 jigs/sheet → 1000 blocks/sheet')
        setblock = make_sub(dry, 'LOCK/JIG/SET-BLOCK',
                            'Lock Jig B Setting Block (10mm dark grey PVC)', GREY_PVC, 1000,
                            note='put in lay flat tubing')

        if not dry:
            db.session.flush()

        # ── Screws (raw materials) ────────────────────────────────────────
        m5x10 = Material.query.get(M5X10_CSK)
        m5x8  = Material.query.get(M5X8_CSK)
        m6x16 = Material.query.get(M6X16_PAN)

        # ── Add to both product BOMs ──────────────────────────────────────
        for parent in [ljb, ljbus]:
            print(f'\n[BOM] {parent.code}')
            add_to_bom(dry, parent, body,     1,  'body')
            add_to_bom(dry, parent, insert,   2,  '2 inserts')
            add_to_bom(dry, parent, slide,    2,  '2 pairs top+bottom')
            add_to_bom(dry, parent, clamp,    1,  'clamping plate')
            add_to_bom(dry, parent, setblock, 2,  '2 setting blocks in lay flat')
            add_to_bom(dry, parent, m5x10,    4,  'for HPL inserts')
            add_to_bom(dry, parent, m5x8,     2,  'for sliding plates')
            add_to_bom(dry, parent, m6x16,    2,  'for setting blocks')

        if not dry:
            db.session.commit()

        print(f'\n{"="*55}')
        tag = 'DRY RUN — ' if dry else ''
        print(f'{tag}Done.')
        if dry:
            print('Re-run with --commit to apply.\n')


if __name__ == '__main__':
    main()
