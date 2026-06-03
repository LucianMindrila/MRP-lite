# MRP-lite Build Plan

## What's Already Built

From code review (June 2026), the following is confirmed implemented:

**Data models (models.py):**
- User (roles: admin, manager, operator)
- Customer, Supplier, Category
- Material (with stock_qty, reorder_point, cost_price, location)
- Product (with sale_price, customer-specific link)
- BOMItem (product → material, qty_per_unit)
- Order + OrderItem (qty_dispatched tracking, outstanding qty)
- DeliveryNote + DeliveryNoteItem (multi-order DN support)
- WorkOrder
- PurchaseOrder + PurchaseOrderItem (partial receipt tracking)
- StockMovement (goods_in, goods_out, adjustment, stock_check, transfer)
- StockBatch (batch/location tracking, building, received_by initials)

**Orders (routes/orders.py):**
- Create, view, confirm, delete orders
- Order status flow: draft → confirmed → in_production → ready → dispatched → invoiced
- Dispatch → auto-creates delivery note
- Multi-dispatch (one DN across multiple orders, same customer)
- Update prices on order
- Order history with date/customer/product filters
- Work orders auto-generated on confirm

**Purchasing (routes/purchasing.py):**
- Shopping list (MRP engine calculates what to order)
- Create, view, print purchase orders
- Mark PO as sent
- Receive goods (partial or full) → updates stock_qty + creates StockMovement

---

## Current Focus / Open Questions

- What is actually working in practice vs what exists in code but hasn't been used/tested?
- What does Lucian find missing or broken when running the app day-to-day?
- PDF extraction from customer email attachments — automate or keep manual entry?

*(To be updated as Lucian answers these questions)*

---

## Phased Build Plan

### Phase 1 — Single order entry point ✓ (largely built)
Admin enters customer orders directly into MRP-lite. Replaces Smartsheet as the live outstanding orders database.

### Phase 2 — BoMs and material planning ✓ (model built, needs data + testing)
Products linked to BoMs. Orders drive automatic material requirements calculation.

### Phase 3 — Purchasing workflow ✓ (largely built)
POs created inside the app. Goods-in updates stock automatically.

### Phase 4 — Production and dispatch ✓ (largely built)
Delivery notes from the app. Dispatch tracked in the app.

### Phase 5 — Invoicing and QuickBooks (to be built)
Month-end invoices auto-generated from delivery notes. QuickBooks API sync.

---

## Order Intake Automation (watch_orders.py) — ALREADY BUILT

Full pipeline is implemented:

1. **Power Automate** watches Outlook inbox → emails labelled as ORDER → saves PDF attachment to OneDrive folder: `C:\Users\conta\OneDrive - DT Solutions LTD\POs\`
2. **watch_orders.py** polls that folder every 10 minutes (run via Windows Task Scheduler using `run_watcher_silent.vbs`)
3. **pdfplumber** extracts raw text from the PDF
4. **Claude Haiku API** (`claude-haiku-4-5-20251001`) parses the text into structured JSON: customer name, PO ref, required date, line items (product code, description, qty, unit price)
5. **Customer matching** — fuzzy name match against customers in DB
6. **Product matching** — by product code, then by description
7. **Draft order created** automatically with matched lines
8. **Unmatched lines** flagged in order notes for admin to add manually
9. **Duplicate guard** — skips PDFs for order refs already in the system
10. **File routing** — processed PDFs move to `processed/`, failures to `needs_review/`
11. **Email body** — Power Automate can also save the email body; script picks it up and associates it with the order

**Current hardcoded paths (from original dev machine `conta`):**
- `run_watcher_silent.vbs` → `C:\Users\conta\Desktop\mrp-lite\`
- `watch_orders.py` → `C:\Users\conta\OneDrive - DT Solutions LTD\POs\`

**These paths need updating for any new machine.**

**Deployment plan:** MRP-lite will run on a dedicated machine at the DT Solutions office, online 24/7 as an internal server. Paths for `watch_orders.py` and `run_watcher_silent.vbs` should be configured once on that machine and left permanent. Staff access the app via browser on the local network.

**Environment variable required:** `ANTHROPIC_API_KEY`

**Dependencies:** `pip install anthropic pdfplumber`

---

## Database Setup — DONE (June 2026)

A clean export/restore pair is now the canonical mechanism for the master data:

- **`scripts/export_db.py`** — dumps the catalog (users, categories, suppliers, customers,
  materials, products, BOMs) + active orders to `scripts/db_export.json`. Run on the work PC.
- **`scripts/db_export.json`** — version-controlled source of truth for the real data.
- **`scripts/setup_real_data.py`** — rebuilds the catalog + logins on any machine from that
  JSON. Builds the schema itself, preserves original IDs (so all FK links survive), is
  idempotent (refuses to run twice without `--force`), and refuses `--force` if transactional
  data is present (so it can never orphan live records).

**Restore scope decision:** the setup script restores the **master/reference catalog + logins
only** — NOT transactional data (orders, POs, delivery notes, stock movements/batches). For an
exact clone of a live machine, copy the `instance/mrp.db` file directly.

**Migration-chain gap discovered:** `flask db upgrade` cannot build a fresh DB — the root
migration assumes the base tables already exist (the original DB was built with `create_all`,
migrations were only recorded later). `setup_real_data.py` works around this by creating the
schema from the models and stamping Alembic to head. *Future cleanup: author a proper initial
migration so `flask db upgrade` works from scratch — deferred to avoid desyncing the live DB's
migration stamp.*

The old per-supplier hand-written scripts (`add_allcap_ironmongery.py`, `seed_safety_knife.py`,
`rebuild_*_orders.py`, etc.) are now **superseded** by this pair. Kept for history; not part of setup.

## Live Data Audit (June 2026) — what's captured vs what's missing

Snapshot: 2 users, 3 customers, 17 suppliers, 7 categories, 90 materials, 65 products, 136 BOM
items, 95 orders (26 active). Functional gaps that block features (these are **data-entry tasks
for Lucian**, not code):

- **37 of 65 products have no BOM** → can't drive material planning (Phase 2). Biggest gap.
- **84 of 90 materials have reorder_point = 0** → MRP shopping list never triggers (Phase 3).
- **12 materials have no supplier; 12 have no cost price** → can't be auto-purchased/costed.
- Contact data thin: 2/3 customers and 12/17 suppliers have no email (POs/invoices can't be emailed).
- Stock barely populated (5/90 materials carry stock) — expected, goods-in was never historically booked.

**Next focus (agreed):** build tools to help Lucian close these gaps fast — e.g. bulk import of
BOMs and reorder points from a spreadsheet — to unlock the already-built MRP & purchasing engines.

## Next Session — Work PC Tasks

1. ~~Pull the repo~~ ✓ done
2. Copy `C:\Users\Lucian\.claude\CLAUDE.md` from home PC to same path on work PC (one-time) — *Lucian's task*
3. ~~Run `scripts/export_db.py`~~ ✓ done
4. ~~Review the export to identify what's missing~~ ✓ done (see audit above)
5. ~~Build `scripts/setup_real_data.py`~~ ✓ done and tested on a fresh DB

## Known Gaps / To Be Investigated

- Invoicing route (`routes/documents.py`) — extent of implementation unknown
- Production scheduling view — Smartsheet Gantt replacement not yet assessed
- UI completeness — templates may exist for routes but quality/completeness unknown
- watch_orders.py path configuration needs updating for dedicated office machine
