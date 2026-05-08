from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from models import db, Order, WorkOrder, DeliveryNote, DeliveryNoteItem, BOMItem, StockMovement
from datetime import datetime
from pathlib import Path
import os

ONEDRIVE_POS = Path(r'C:\Users\conta\OneDrive - DT Solutions LTD\POs')

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')


@documents_bp.route('/order-file')
@login_required
def serve_order_file():
    """Serve a PO or email body file stored in OneDrive."""
    path = request.args.get('path', '').strip()
    if not path:
        abort(400)
    try:
        real = Path(os.path.realpath(path))
        base = Path(os.path.realpath(ONEDRIVE_POS))
        if base not in real.parents and real != base:
            abort(403)
    except Exception:
        abort(400)
    if not real.exists():
        abort(404)
    return send_file(real, as_attachment=False)


@documents_bp.route('/work-orders')
@login_required
def work_orders_list():
    work_orders = WorkOrder.query.order_by(WorkOrder.created_at.desc()).all()
    return render_template('documents/work_orders_list.html', work_orders=work_orders)


@documents_bp.route('/work-order/<int:wo_id>/print')
@login_required
def print_work_order(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    return render_template('documents/print_work_order.html', wo=wo)


@documents_bp.route('/order/<int:order_id>/invoice')
@login_required
def print_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('documents/print_invoice.html', order=order)


@documents_bp.route('/order/<int:order_id>/delivery-note')
@login_required
def print_delivery_note(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('documents/print_delivery_note.html', order=order)


@documents_bp.route('/delivery-note/<int:dn_id>')
@login_required
def print_delivery_note_dn(dn_id):
    dn = DeliveryNote.query.get_or_404(dn_id)
    return render_template('documents/print_delivery_note_dn.html', dn=dn)


@documents_bp.route('/delivery-note/<int:dn_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_delivery_note(dn_id):
    dn = DeliveryNote.query.get_or_404(dn_id)
    if request.method == 'POST':
        # Update dispatch date and notes
        date_str = request.form.get('dispatch_date')
        if date_str:
            dn.dispatch_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        dn.notes = request.form.get('dn_notes', '')

        for dni in dn.items:
            old_qty = dni.qty_dispatched
            try:
                new_qty = float(request.form.get(f'qty_{dni.id}', old_qty))
            except ValueError:
                new_qty = old_qty

            # cap at ordered qty to prevent over-dispatch
            max_qty = dni.order_item.qty
            new_qty = max(0, min(new_qty, max_qty))
            delta = new_qty - old_qty

            if delta != 0:
                # adjust order item dispatched total
                dni.order_item.qty_dispatched = (dni.order_item.qty_dispatched or 0) + delta
                # adjust stock for each BOM component
                for bom in BOMItem.query.filter_by(product_id=dni.order_item.product_id).all():
                    bom.material.stock_qty = (bom.material.stock_qty or 0) - (bom.qty_per_unit * delta)
                    db.session.add(StockMovement(
                        material_id=bom.material_id,
                        movement_type='goods_out',
                        qty=-(bom.qty_per_unit * delta),
                        reference=f'{dn.dn_ref} (amended)',
                        created_by=current_user.id,
                    ))
                dni.qty_dispatched = new_qty

        # recalculate order status
        order = dn.order
        if all(i.qty_outstanding == 0 for i in order.items):
            order.status = 'dispatched'
        elif any((i.qty_dispatched or 0) > 0 for i in order.items):
            order.status = 'in_production'
        else:
            order.status = 'confirmed'

        db.session.commit()
        flash(f'{dn.dn_ref} updated.', 'success')
        return redirect(url_for('documents.print_delivery_note_dn', dn_id=dn.id))

    return render_template('documents/edit_delivery_note.html', dn=dn)
