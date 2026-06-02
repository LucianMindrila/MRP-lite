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

## Known Gaps / To Be Investigated

- Invoicing route (`routes/documents.py`) — extent of implementation unknown
- Production scheduling view — Smartsheet Gantt replacement not yet assessed
- Customer PO attachment (email/PDF) — fields exist on Order model but upload flow unclear
- UI completeness — templates may exist for routes but quality/completeness unknown
