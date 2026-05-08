"""watch_orders.py — Poll OneDrive POs folder and create draft orders in MRP Lite.

Run manually or via Windows Task Scheduler (every 5-10 minutes).

Setup:
  1. pip install anthropic pdfplumber
  2. Set environment variable: ANTHROPIC_API_KEY=sk-ant-...
  3. Run: python watch_orders.py

Folder layout (auto-created):
  C:\\Users\\conta\\OneDrive - DT Solutions LTD\\POs\\              <- drop PDFs here (Power Automate does this)
  C:\\Users\\conta\\OneDrive - DT Solutions LTD\\POs\\processed\\  <- successfully imported
  C:\\Users\\conta\\OneDrive - DT Solutions LTD\\POs\\needs_review\\ <- unmatched customer or parse failure
"""
import os, sys, json, shutil, re
from pathlib import Path
from datetime import datetime

import anthropic
import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from app import create_app
from models import db, Customer, Product, Order, OrderItem

# ── Config ───────────────────────────────────────────────────────────────────
INCOMING_DIR  = Path(r'C:\Users\conta\OneDrive - DT Solutions LTD\POs')
PROCESSED_DIR = INCOMING_DIR / 'processed'
REVIEW_DIR    = INCOMING_DIR / 'needs_review'
API_KEY       = os.environ.get('ANTHROPIC_API_KEY', '')

EXTRACT_PROMPT = """\
Extract purchase order data from the text below and return ONLY valid JSON — no explanation, no markdown.

Return exactly this structure:
{
  "customer_name": "the company that issued this PO (they are buying from us)",
  "po_ref": "their PO or order or works-order number",
  "order_date": "YYYY-MM-DD or null",
  "required_date": "YYYY-MM-DD or null",
  "lines": [
    {"product_code": "stock code", "description": "product description", "qty": 0, "unit_price": 0.0}
  ]
}

Rules:
- customer_name is the BUYER. DT Solutions Ltd / DT Solutions LTD is always US (the supplier) — never set them as customer_name.
- po_ref is the PO number, order number, or works-order number from the buyer.
- Convert dates like 30/4/26 or 22/6/2026 to YYYY-MM-DD. Use null if absent.
- qty and unit_price must be numbers. Use 0 if not shown.
- Include every line item.

Purchase order text:
"""


# ── PDF helpers ───────────────────────────────────────────────────────────────
def extract_pdf_text(path: Path) -> str:
    text = ''
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or '') + '\n'
    except Exception as e:
        print(f"  PDF read error: {e}")
    return text.strip()


def parse_with_claude(text: str) -> dict | None:
    try:
        client = anthropic.Anthropic(api_key=API_KEY)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': EXTRACT_PROMPT + text}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  Claude parse error: {e}")
        return None


# ── Database helpers ──────────────────────────────────────────────────────────
def match_customer(name: str):
    name_l = name.lower().strip()
    for c in Customer.query.all():
        c_l = c.name.lower()
        if name_l in c_l or c_l in name_l:
            return c
    return None


def match_product(code: str, description: str):
    if code:
        p = Product.query.filter_by(code=code).first()
        if p:
            return p
        p = Product.query.filter(Product.code.ilike(f'%{code}%')).first()
        if p:
            return p
    if description:
        p = Product.query.filter(Product.name.ilike(f'%{description[:25]}%')).first()
        if p:
            return p
    return None


def unique_order_ref(po_ref: str) -> str:
    base = po_ref.strip()[:30]
    if not Order.query.filter_by(order_ref=base).first():
        return base
    for i in range(2, 50):
        candidate = f'{base}-{i}'
        if not Order.query.filter_by(order_ref=candidate).first():
            return candidate
    return f'{base}-{datetime.now().strftime("%H%M%S")}'


# ── Core processor ────────────────────────────────────────────────────────────
def process_pdf(pdf_path: Path) -> str:
    """Process one PDF. Returns 'ok', 'review', or 'skip'."""
    print(f"\n  Processing: {pdf_path.name}")

    text = extract_pdf_text(pdf_path)
    if not text:
        print("    No text extracted.")
        return 'review'

    parsed = parse_with_claude(text)
    if not parsed:
        print("    Claude parse failed.")
        return 'review'

    customer_raw = parsed.get('customer_name', '')
    po_ref       = str(parsed.get('po_ref', '')).strip()
    required_raw = parsed.get('required_date')
    lines_raw    = parsed.get('lines', [])

    print(f"    Customer : {customer_raw}")
    print(f"    PO Ref   : {po_ref}")
    print(f"    Required : {required_raw}")
    print(f"    Lines    : {len(lines_raw)}")

    customer = match_customer(customer_raw)
    if not customer:
        print(f"    No customer match for '{customer_raw}'.")
        return 'review'

    if not po_ref:
        print("    No PO ref found.")
        return 'review'

    # Duplicate guard
    if Order.query.filter_by(order_ref=po_ref).first():
        print(f"    Order {po_ref} already exists — skipping.")
        return 'skip'

    # Parse required date
    required_date = None
    if required_raw:
        try:
            required_date = datetime.strptime(required_raw, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Match products
    matched, unmatched = [], []
    for line in lines_raw:
        product = match_product(line.get('product_code', ''), line.get('description', ''))
        qty   = float(line.get('qty', 0) or 0)
        price = float(line.get('unit_price', 0) or 0)
        if product and qty > 0:
            matched.append((product, qty, price))
        else:
            unmatched.append(
                f"{line.get('product_code', '?')} — {line.get('description', '?')} (qty {qty})"
            )

    notes = f"Auto-imported from {pdf_path.name}"
    if unmatched:
        notes += '\nUNMATCHED LINES — add manually:\n' + '\n'.join(f'  • {u}' for u in unmatched)

    # Find matching email body file in the same folder (saved by Power Automate)
    email_body_path = _find_email_body(pdf_path.parent)

    # Destination paths (files will be moved here after processing)
    dest_result = REVIEW_DIR if unmatched else PROCESSED_DIR
    po_dest      = str(dest_result / pdf_path.name)
    email_dest   = str(dest_result / email_body_path.name) if email_body_path else None

    order = Order(
        order_ref=unique_order_ref(po_ref),
        customer_id=customer.id,
        status='draft',
        required_date=required_date,
        notes=notes,
        po_file_path=po_dest,
        email_file_path=email_dest,
    )
    db.session.add(order)
    db.session.flush()

    for product, qty, price in matched:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            qty=qty,
            unit_price=price,
        ))

    db.session.commit()

    # Move email body alongside the PO so they stay together
    if email_body_path and email_body_path.exists():
        shutil.move(str(email_body_path), email_dest)

    flag = ' ⚠ unmatched lines' if unmatched else ''
    print(f"    Created draft order {order.order_ref} for {customer.name}{flag}")
    if unmatched:
        print(f"    Unmatched: {'; '.join(unmatched)}")

    return 'review' if unmatched else 'ok'


def _find_email_body(folder: Path) -> Path | None:
    """Look for an email body file saved by Power Automate in the same folder."""
    for pattern in ['*email-body*', '*email_body*', '*_body.*']:
        candidates = [
            p for p in folder.glob(pattern)
            if p.suffix.lower() in ('.pdf', '.html', '.htm')
        ]
        if candidates:
            # Pick the most recently modified one
            return max(candidates, key=lambda p: p.stat().st_mtime)
    return None


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("  Run:  set ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    PROCESSED_DIR.mkdir(exist_ok=True)
    REVIEW_DIR.mkdir(exist_ok=True)

    # Scan root and any customer subfolders; exclude processed/needs_review and email body files
    pdfs = sorted(
        p for p in INCOMING_DIR.rglob('*.[pP][dD][fF]')
        if PROCESSED_DIR not in p.parents
        and REVIEW_DIR not in p.parents
        and 'email-body' not in p.name.lower()
        and 'email_body' not in p.name.lower()
    )
    if not pdfs:
        print("No new PDFs in incoming folder.")
        return

    print(f"Found {len(pdfs)} PDF(s) to process.")

    app = create_app()
    results = {'ok': 0, 'review': 0, 'skip': 0, 'error': 0}

    with app.app_context():
        for pdf_path in pdfs:
            try:
                result = process_pdf(pdf_path)
            except Exception as e:
                print(f"    Unexpected error: {e}")
                result = 'review'

            results[result] = results.get(result, 0) + 1

            dest = {
                'ok':     PROCESSED_DIR,
                'review': REVIEW_DIR,
                'skip':   PROCESSED_DIR,
                'error':  REVIEW_DIR,
            }.get(result, REVIEW_DIR)

            shutil.move(str(pdf_path), str(dest / pdf_path.name))

    print(f"\nSummary: {results['ok']} imported, {results['skip']} skipped (duplicate), "
          f"{results['review']} need review, {results['error']} errors.")
    if results['review']:
        print(f"  Check: {REVIEW_DIR}")


if __name__ == '__main__':
    main()
