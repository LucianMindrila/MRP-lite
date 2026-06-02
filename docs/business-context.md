# Business Context — DT Solutions Ltd

## The Business

Manufacturing company in Gloucester, UK. Produces panel-based products (kitchen units, office furniture, laminated doors, bespoke items) using sheet goods: Compact Grade laminate, plywood, MFC, MDF, plastic sheets.

**Services:** Panel sizing, edgebanding, flat bonding of laminates/veneers, CNC routing, laser engraving.
**Customers:** Trade customers UK-wide (furniture manufacturers, kitchen designers, fit-out companies).
**Team:** Small — admin, operators on shop floor, owner (Lucian Mindrila).
**Location:** Units 3-4 Pearce Way, Gloucester, GL2 5YD

## Current Manual Flow (what this app replaces)

1. **Order intake** — Customer sends PO via email (Outlook) as PDF attachment
2. **Paper copy** — Admin prints PDF, places in physical folder
3. **Smartsheet entry** — Admin manually types all order lines into Smartsheet (current "database" of outstanding orders)
4. **Material planning** — No formal BoM system. Materials ordered on mental calculation: products needed → sheets/yield estimate
5. **Purchase orders** — Manually created in Excel, emailed to supplier
6. **Goods received** — Not booked into any system. Lucian verbally tells operators what delivery is expected and which job it's for
7. **Production scheduling** — Smartsheet Gantt chart across machines (CNC, saw, edgebander)
8. **Delivery notes** — Manually created in Excel when goods are ready
9. **Dispatch** — Marked manually on Smartsheet outstanding orders sheet
10. **Invoicing** — Month-end: admin reconciles customer orders against delivery notes in Excel, creates invoices manually
11. **QuickBooks** — Job costing (raw material cost vs job cost) and invoice tracking

## Core Problems Being Solved

1. **Triple data entry** — same order handled 3+ times: printed, typed into Smartsheet, reconciled at month-end
2. **No BoM system** — material ordering runs on one person's mental calculation
3. **No stock control** — goods arrive but never booked in; nobody knows what's on the shelf
4. **Single point of failure** — entire operation depends on one person's memory
5. **Disconnected documents** — POs in Excel, DNs in Excel, invoices in Excel, orders in Smartsheet, financials in QuickBooks. Nothing connects.

## External Systems

- **QuickBooks** — accounting; future integration for invoice/PO sync
- **Smartsheet** — current production scheduling and order capturing; to be replaced or synced by this app
