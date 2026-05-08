"""Scan OneDrive POs folder for PDFs and link them to matching orders in the database.
Also copies Trend PDFs from Downloads if not already in OneDrive."""
import sys, os, shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app
from models import db, Order

ONEDRIVE_POS = Path(r'C:\Users\conta\OneDrive - DT Solutions LTD\POs')
SKIP_DIRS = {'processed', 'needs_review'}

# Files to copy from Downloads if not already in OneDrive
COPY_FROM_DOWNLOADS = [
    (r'C:\Users\conta\Downloads\PO067191 (DESI).pdf', 'Trend'),
    (r'C:\Users\conta\Downloads\PO067192 (DESI).pdf', 'Trend'),
    (r'C:\Users\conta\Downloads\PO067193 (DESI).pdf', 'Trend'),
]

app = create_app()

with app.app_context():
    # Step 1: copy Downloads PDFs that aren't in OneDrive yet
    for src_str, subfolder in COPY_FROM_DOWNLOADS:
        src = Path(src_str)
        if not src.exists():
            continue
        dest_dir = ONEDRIVE_POS / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        if not dest.exists():
            shutil.copy2(str(src), str(dest))
            print(f"  Copied: {src.name} -> {subfolder}/")

    # Step 2: scan all PDFs in OneDrive POs (excluding processed/needs_review and email bodies)
    all_pdfs = [
        p for p in ONEDRIVE_POS.rglob('*.[pP][dD][fF]')
        if p.parent.name not in SKIP_DIRS
        and 'email-body' not in p.name.lower()
        and 'email_body' not in p.name.lower()
    ]
    print(f"Found {len(all_pdfs)} PO PDF(s) in OneDrive folder.")
    for p in all_pdfs:
        print(f"  {p.relative_to(ONEDRIVE_POS)}")

    # Step 3: match each PDF to an order — check if order ref appears in the filename
    orders = Order.query.all()
    linked = 0
    for pdf in all_pdfs:
        name_clean = pdf.name.lower().replace('-', '').replace(' ', '').replace('_', '')
        for order in orders:
            ref_clean = order.order_ref.lower().replace('-', '').replace(' ', '').replace('_', '')
            if ref_clean in name_clean:
                if order.po_file_path != str(pdf):
                    order.po_file_path = str(pdf)
                    print(f"  Linked: {pdf.name} -> order {order.order_ref}")
                    linked += 1
                break

    db.session.commit()
    print(f"\n{linked} new link(s) saved.")
    print("\nOrders still missing PDF links:")
    missing = Order.query.filter(Order.po_file_path == None).all()
    for o in missing:
        print(f"  {o.order_ref} -- {o.customer.name}")
    if not missing:
        print("  None -- all orders linked!")
