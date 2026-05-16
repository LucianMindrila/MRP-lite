from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, PurchaseOrder, DeliveryNote, BOMItem, StockMovement, StockBatch
from datetime import date

operator_bp = Blueprint('operator', __name__, url_prefix='/operator')

LOCATIONS = [
    'Unit 3 — Assembly Room',
    'Unit 3 — Racking',
    'Unit 3 — Stockroom',
    'Unit 4 — Laser Room',
    'Unit 4 — Racking',
    'Unit 7',
]

def _building_from_location(loc):
    for b in ['Unit 16', 'Unit 7', 'Unit 4', 'Unit 3']:
        if loc.startswith(b):
            return b
    return 'Unit 4'


@operator_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    open_pos = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['sent', 'partial'])).count()
    po_due_today = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['sent', 'partial']),
        PurchaseOrder.expected_date == today
    ).count()
    pending_dns = DeliveryNote.query.filter_by(status='pending').count()
    dns_due = DeliveryNote.query.filter(
        DeliveryNote.status == 'pending',
        DeliveryNote.dispatch_date <= today
    ).count()
    return render_template('operator/dashboard.html',
                           open_pos=open_pos, po_due_today=po_due_today,
                           pending_dns=pending_dns, dns_due=dns_due)


@operator_bp.route('/goods-in')
@login_required
def goods_in_list():
    today = date.today()
    pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['sent', 'partial'])
    ).order_by(PurchaseOrder.expected_date).all()
    return render_template('operator/goods_in_list.html', pos=pos, today=today)


@operator_bp.route('/goods-in/<int:po_id>')
@login_required
def goods_in_receive(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    return render_template('operator/goods_in_receive.html', po=po, locations=LOCATIONS)


@operator_bp.route('/goods-in/<int:po_id>/confirm', methods=['POST'])
@login_required
def goods_in_confirm(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    initials = request.form.get('initials', '').strip().upper()[:5]
    if not initials:
        flash('Please enter your initials before confirming.', 'danger')
        return redirect(url_for('operator.goods_in_receive', po_id=po_id))

    notes = request.form.get('notes', '').strip()
    movement_notes = f'Recv by: {initials}'
    if notes:
        movement_notes += f' | {notes}'

    any_received = False
    over_deliveries = []

    for item in po.items:
        recv_str = request.form.get(f'recv_{item.id}', '').strip()
        if not recv_str:
            continue
        try:
            recv = float(recv_str)
        except ValueError:
            continue
        if recv <= 0:
            continue

        any_received = True

        outstanding = item.qty - item.qty_received
        if recv > outstanding:
            over_deliveries.append(
                f'{item.material.code}: {recv:.0f} received vs {item.qty:.0f} ordered'
            )

        item.qty_received += recv
        item.material.stock_qty += recv
        db.session.add(StockMovement(
            material_id=item.material_id,
            movement_type='goods_in',
            qty=recv,
            reference=po.po_ref,
            notes=movement_notes,
            created_by=current_user.id,
        ))

        batch_qtys = request.form.getlist(f'batch_qty_{item.id}[]')
        batch_locations = request.form.getlist(f'batch_location_{item.id}[]')

        for bqty_s, blocation in zip(batch_qtys, batch_locations):
            try:
                bqty = float(bqty_s)
            except (ValueError, TypeError):
                continue
            if bqty <= 0:
                continue
            db.session.add(StockBatch(
                material_id=item.material_id,
                qty=bqty,
                qty_original=bqty,
                building=_building_from_location(blocation),
                location_detail=blocation.strip(),
                po_id=po.id,
                received_by=initials,
                notes=notes or None,
                status='active',
            ))

    if not any_received:
        flash('No quantities entered — nothing was saved.', 'warning')
        return redirect(url_for('operator.goods_in_receive', po_id=po_id))

    all_received = all(item.qty_received >= item.qty for item in po.items)
    po.status = 'received' if all_received else 'partial'
    db.session.commit()

    if over_deliveries:
        flash(f'Over-delivery — admin review needed: {"; ".join(over_deliveries)}', 'warning')
    flash(f'Goods booked in against {po.po_ref}. Logged as: {initials}.', 'success')
    return redirect(url_for('operator.goods_in_list'))


def _deduct_from_batches(material_id, qty_needed):
    """Deduct from Unit 7 batches first, fall back to Unit 4. Returns shortfall."""
    remaining = qty_needed
    for building in ['Unit 7', 'Unit 4']:
        if remaining <= 0:
            break
        batches = (StockBatch.query
                   .filter_by(material_id=material_id, building=building, status='active')
                   .order_by(StockBatch.received_at)
                   .all())
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.qty, remaining)
            batch.qty -= take
            if batch.qty <= 0:
                batch.status = 'empty'
            remaining -= take
    return remaining


@operator_bp.route('/goods-out')
@login_required
def goods_out_list():
    today = date.today()
    dns = (DeliveryNote.query
           .filter_by(status='pending')
           .order_by(DeliveryNote.dispatch_date)
           .all())
    due_today = sum(1 for d in dns if d.dispatch_date <= today)
    return render_template('operator/goods_out_list.html', dns=dns, today=today, due_today=due_today)


@operator_bp.route('/goods-out/<int:dn_id>')
@login_required
def goods_out_detail(dn_id):
    dn = DeliveryNote.query.get_or_404(dn_id)
    return render_template('operator/goods_out_detail.html', dn=dn)


@operator_bp.route('/goods-out/<int:dn_id>/dispatch', methods=['POST'])
@login_required
def goods_out_dispatch(dn_id):
    dn = DeliveryNote.query.get_or_404(dn_id)
    if dn.status == 'dispatched':
        flash('This delivery note has already been dispatched.', 'warning')
        return redirect(url_for('operator.goods_out_list'))

    initials = request.form.get('initials', '').strip().upper()[:5]
    if not initials:
        flash('Please enter your initials before confirming.', 'danger')
        return redirect(url_for('operator.goods_out_detail', dn_id=dn_id))

    shortfalls = []
    affected_orders = set()

    for dni in dn.items:
        order_item = dni.order_item
        qty = dni.qty_dispatched
        affected_orders.add(order_item.order)

        for bom in BOMItem.query.filter_by(product_id=order_item.product_id).all():
            needed = bom.qty_per_unit * qty
            shortfall = _deduct_from_batches(bom.material_id, needed)
            bom.material.stock_qty = (bom.material.stock_qty or 0) - needed
            db.session.add(StockMovement(
                material_id=bom.material_id,
                movement_type='goods_out',
                qty=-needed,
                reference=dn.dn_ref,
                notes=f'Dispatched by: {initials}',
                created_by=current_user.id,
            ))
            if shortfall > 0:
                shortfalls.append(f'{bom.material.code}: {shortfall:.0f} short at Unit 7/4')

    dn.status = 'dispatched'

    today = date.today()
    for order in affected_orders:
        if all(i.qty_outstanding == 0 for i in order.items):
            order.status = 'dispatched'
            order.dispatched_date = today
        elif any((i.qty_dispatched or 0) > 0 for i in order.items):
            order.status = 'in_production'

    db.session.commit()

    if shortfalls:
        flash(f'Stock shortfalls — admin review needed: {"; ".join(shortfalls)}', 'warning')
    flash(f'{dn.dn_ref} marked as dispatched. Logged as: {initials}.', 'success')
    return redirect(url_for('operator.goods_out_list'))


@operator_bp.route('/move-stock')
@login_required
def move_stock_list():
    batches = (StockBatch.query
               .filter_by(status='active')
               .join(StockBatch.material)
               .order_by(StockBatch.building, StockBatch.received_at)
               .all())
    return render_template('operator/move_stock_list.html', batches=batches)


@operator_bp.route('/move-stock/<int:batch_id>', methods=['GET', 'POST'])
@login_required
def move_stock(batch_id):
    batch = StockBatch.query.get_or_404(batch_id)
    if request.method == 'POST':
        initials = request.form.get('initials', '').strip().upper()[:5]
        if not initials:
            flash('Please enter your initials.', 'danger')
            return redirect(url_for('operator.move_stock', batch_id=batch_id))
        old_desc = batch.location_detail or batch.building
        new_location = request.form.get('location', '').strip()
        batch.building = _building_from_location(new_location)
        batch.location_detail = new_location
        new_desc = new_location
        db.session.add(StockMovement(
            material_id=batch.material_id,
            movement_type='transfer',
            qty=0,
            reference='MOVE',
            notes=f'Moved by: {initials} | {old_desc} → {new_desc}',
            created_by=current_user.id,
        ))
        db.session.commit()
        flash(f'Batch moved to {batch.location_detail}.', 'success')
        return redirect(url_for('operator.move_stock_list'))
    return render_template('operator/move_stock.html', batch=batch, locations=LOCATIONS)
