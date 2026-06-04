"""dedup_materials.py — Find and merge duplicate materials using fuzzy matching.

For each (category, supplier) group, normalises descriptions and computes
pairwise similarity. Pairs above the threshold are flagged as duplicates.
Keeps the best record per group, transfers all FK references, deletes the rest.

Run:
  python scripts/dedup_materials.py              # dry-run (preview, no writes)
  python scripts/dedup_materials.py --commit     # apply changes
  python scripts/dedup_materials.py --cat "Cardboard Boxes"  # one category only
  python scripts/dedup_materials.py --threshold 0.80          # adjust sensitivity
"""
import sys, io, re, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from difflib import SequenceMatcher
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Material, Category, BOMItem, PurchaseOrderItem, StockMovement, StockBatch

DEFAULT_THRESHOLD = 0.90

# Clothing/workwear size tokens — must match exactly between items
_SIZE_RE = re.compile(r'(?<![A-Z0-9])(XXL|XL|XS|2XL|3XL|XXXL|[SML])(?![A-Z0-9])', re.IGNORECASE)
# Numbers including those embedded in unit strings like "900mm", "18mm", "M5", "3.5", "1/4"
# No word boundary so "900" in "900mm" and "5" in "M5" are captured
_NUM_RE  = re.compile(r'\d+(?:[./]\d+)?')


def _specs(s):
    """Return (frozenset of numbers, frozenset of size tokens) from a string.

    Numbers are the key discriminators for manufacturing materials:
    12mm MDF != 18mm MDF, M5 screw != M6 screw, KWJ650 != KWJ900.
    Items with any differing number are treated as different products.
    """
    nums  = frozenset(_NUM_RE.findall(s))
    sizes = frozenset(t.upper() for t in _SIZE_RE.findall(s))
    return nums, sizes


def normalise(s):
    """Lowercase, strip punctuation — keep original word order for similarity check."""
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_dup_groups(materials, threshold):
    """Return list of duplicate groups (each group = list of material IDs).

    A pair is only flagged as a duplicate if:
      1. All numeric specs (dimensions, sizes) are identical — different numbers
         means a different product (M5x6 != M5x8, 12mm MDF != 18mm MDF).
      2. All clothing-size tokens match (Size L != Size XL).
      3. Text similarity of the normalised description exceeds the threshold.
    """
    items = [(m.id, normalise(m.name), _specs(m.name)) for m in materials]
    n = len(items)

    parent = {m.id: m.id for m in materials}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(n):
        for j in range(i + 1, n):
            nums_i, sizes_i = items[i][2]
            nums_j, sizes_j = items[j][2]
            # Guard: specs must be identical — different numbers = different item
            if nums_i != nums_j or sizes_i != sizes_j:
                continue
            if similarity(items[i][1], items[j][1]) >= threshold:
                union(items[i][0], items[j][0])

    groups = {}
    for mid, _, _ in items:
        root = find(mid)
        groups.setdefault(root, []).append(mid)

    return [g for g in groups.values() if len(g) >= 2]


def pick_winner(group_ids, mat_by_id, bom_mat_ids):
    """Keep: 1) has BOM entries, 2) has cost price, 3) lowest id."""
    def score(mid):
        m = mat_by_id[mid]
        return (
            (10 if mid in bom_mat_ids else 0) +
            (2  if (m.cost_price or 0) > 0 else 0) +
            (1  if m.supplier_id else 0)
        )
    ranked = sorted(group_ids, key=lambda mid: (-score(mid), mid))
    return ranked[0], ranked[1:]


def describe_refs(mid):
    parts = []
    n = BOMItem.query.filter_by(material_id=mid).count()
    if n: parts.append(f"{n} BOM")
    n = PurchaseOrderItem.query.filter_by(material_id=mid).count()
    if n: parts.append(f"{n} PO lines")
    n = StockMovement.query.filter_by(material_id=mid).count()
    if n: parts.append(f"{n} stock moves")
    n = StockBatch.query.filter_by(material_id=mid).count()
    if n: parts.append(f"{n} batches")
    return ', '.join(parts) if parts else 'no refs'


def merge(winner_id, loser_ids, dry):
    winner = Material.query.get(winner_id)
    deleted = 0

    for lid in loser_ids:
        loser = Material.query.get(lid)
        if not loser:
            continue

        for b in BOMItem.query.filter_by(material_id=lid).all():
            conflict = BOMItem.query.filter_by(
                material_id=winner_id, product_id=b.product_id).first()
            if not dry:
                if conflict:
                    db.session.delete(b)
                else:
                    b.material_id = winner_id

        for pi in PurchaseOrderItem.query.filter_by(material_id=lid).all():
            if not dry:
                pi.material_id = winner_id

        for sm in StockMovement.query.filter_by(material_id=lid).all():
            if not dry:
                sm.material_id = winner_id

        for sb in StockBatch.query.filter_by(material_id=lid).all():
            if not dry:
                sb.material_id = winner_id

        if not dry:
            if not (winner.cost_price or 0) and (loser.cost_price or 0):
                winner.cost_price = loser.cost_price
            if not winner.supplier_id and loser.supplier_id:
                winner.supplier_id = loser.supplier_id
            db.session.delete(loser)

        deleted += 1

    if not dry:
        db.session.commit()
    return deleted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true',
                    help='Apply changes (default is dry-run / preview only)')
    ap.add_argument('--cat', default=None,
                    help='Process one category only (exact name)')
    ap.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD,
                    help=f'Similarity threshold 0-1 (default {DEFAULT_THRESHOLD})')
    args = ap.parse_args()
    dry = not args.commit

    app = create_app()
    with app.app_context():
        categories = Category.query.order_by(Category.name).all()
        if args.cat:
            categories = [c for c in categories
                          if c.name.lower() == args.cat.lower()]
            if not categories:
                sys.exit(f"Category '{args.cat}' not found.")

        bom_mat_ids = {
            r[0] for r in db.session.query(BOMItem.material_id).distinct().all()
        }

        grand_groups = 0
        grand_deleted = 0

        for cat in categories:
            materials = Material.query.filter_by(
                category_id=cat.id).order_by(Material.id).all()
            if len(materials) < 2:
                continue

            mat_by_id = {m.id: m for m in materials}

            # Group by supplier so we never merge across suppliers
            by_supplier = {}
            for m in materials:
                key = m.supplier_id or 0
                by_supplier.setdefault(key, []).append(m)

            cat_groups = []
            for sup_id, sup_mats in by_supplier.items():
                cat_groups.extend(find_dup_groups(sup_mats, args.threshold))

            if not cat_groups:
                continue

            print(f"\n{'='*60}")
            print(f"Category: {cat.name}  —  {len(cat_groups)} duplicate group(s)\n")

            for group in cat_groups:
                winner_id, loser_ids = pick_winner(group, mat_by_id, bom_mat_ids)
                winner = mat_by_id[winner_id]
                sup = winner.supplier.name if winner.supplier else 'no supplier'

                print(f"  KEEP  [id={winner_id}] {winner.name[:65]}")
                print(f"        {sup}  |  refs: {describe_refs(winner_id)}")
                for lid in loser_ids:
                    loser = mat_by_id[lid]
                    print(f"  DEL   [id={lid}] {loser.name[:65]}")
                    print(f"        refs: {describe_refs(lid)}")
                print()

                grand_groups += 1
                grand_deleted += len(loser_ids)

                if not dry:
                    merge(winner_id, loser_ids, dry=False)

        print('=' * 60)
        if grand_groups == 0:
            print('No duplicates found at this threshold.')
        elif dry:
            print(f'DRY RUN  —  {grand_groups} group(s), '
                  f'{grand_deleted} material(s) would be deleted.')
            print('Re-run with --commit to apply.\n')
        else:
            print(f'Done  —  {grand_deleted} duplicate(s) merged and deleted.\n')


if __name__ == '__main__':
    main()
