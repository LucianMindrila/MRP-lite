from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, PurchaseOrder, StockMovement, StockBatch
from datetime import date

operator_bp = Blueprint('operator', __name__, url_prefix='/operator')

BUILDINGS = ['Unit 4', 'Unit 7', 'Unit 16']


@operator_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    open_pos = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['sent', 'partial'])).count()
    due_today = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['sent', 'partial']),
        PurchaseOrder.expected_date == today
    ).count()
    return render_template('operator/dashboard.html', open_pos=open_pos, due_today=due_today)


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
    return render_template('operator/goods_in_receive.html', po=po, buildings=BUILDINGS)


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
        batch_buildings = request.form.getlist(f'batch_building_{item.id}[]')
        batch_locations = request.form.getlist(f'batch_location_{item.id}[]')

        for bqty_s, bbuilding, blocation in zip(batch_qtys, batch_buildings, batch_locations):
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
                building=bbuilding,
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
        old_desc = f'{batch.building} — {batch.location_detail}'
        batch.building = request.form.get('building')
        batch.location_detail = request.form.get('location_detail', '').strip()
        new_desc = f'{batch.building} — {batch.location_detail}'
        db.session.add(StockMovement(
            material_id=batch.material_id,
            movement_type='transfer',
            qty=0,
            reference='MOVE',
            notes=f'Moved by: {initials} | {old_desc} → {new_desc}',
            created_by=current_user.id,
        ))
        db.session.commit()
        flash(f'Batch moved to {batch.building} — {batch.location_detail}.', 'success')
        return redirect(url_for('operator.move_stock_list'))
    return render_template('operator/move_stock.html', batch=batch, buildings=BUILDINGS)
