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

## Known Gaps / To Be Investigated

- Invoicing route (`routes/documents.py`) — extent of implementation unknown
- Production scheduling view — Smartsheet Gantt replacement not yet assessed
- UI completeness — templates may exist for routes but quality/completeness unknown
- watch_orders.py path configuration needs updating per machine (currently hardcoded to `conta` user)
