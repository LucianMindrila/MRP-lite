from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, PurchaseOrder, PurchaseOrderItem, Material, Supplier
from mrp_engine import get_shopping_list
from datetime import datetime
import random, string

purchasing_bp = Blueprint('purchasing', __name__, url_prefix='/purchasing')


def gen_po_ref():
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"PO-{datetime.now().strftime('%y%m')}-{suffix}"


@purchasing_bp.route('/shopping-list')
@login_required
def shopping_list():
    raw = get_shopping_list()
    items = [
        {
            'material_name': entry['material'].name,
            'sku':           entry['material'].code,
            'in_stock':      entry['material'].stock_qty,
            'uom':           entry['material'].unit,
            'total_required': round(entry['material'].stock_qty + entry['shortfall'], 4),
            'order_quantity': entry['order_qty'],
            'supplier_name': entry['supplier'].name if entry['supplier'] else '—',
            'lead_time_days': entry['supplier'].lead_time_days if entry['supplier'] else '—',
            'estimated_cost': entry['order_qty'] * entry['material'].cost_price,
        }
        for entry in raw
    ]
    return render_template('purchasing/shopping_list.html', items=items)


@purchasing_bp.route('/po')
@login_required
def po_list():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return render_template('purchasing/po_list.html', pos=pos)


@purchasing_bp.route('/po/new', methods=['GET', 'POST'])
@login_required
def po_new():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    materials = Material.query.order_by(Material.code).all()
    if request.method == 'POST':
        po = PurchaseOrder(
            po_ref=gen_po_ref(),
            supplier_id=int(request.form['supplier_id']),
            expected_date=datetime.strptime(request.form['expected_date'], '%Y-%m-%d').date() if request.form.get('expected_date') else None,
            notes=request.form.get('notes', ''),
            status='draft',
        )
        db.session.add(po)
        db.session.flush()

        material_ids = request.form.getlist('material_id[]')
        qtys = request.form.getlist('qty[]')
        prices = request.form.getlist('unit_price[]')
        for mid, qty, price in zip(material_ids, qtys, prices):
            if mid and qty:
                db.session.add(PurchaseOrderItem(
                    po_id=po.id,
                    material_id=int(mid),
                    qty=float(qty),
                    unit_price=float(price or 0),
                ))
        db.session.commit()
        flash(f'Purchase Order {po.po_ref} created.', 'success')
        return redirect(url_for('purchasing.po_detail', po_id=po.id))
    return render_template('purchasing/po_form.html', suppliers=suppliers, materials=materials)


@purchasing_bp.route('/po/<int:po_id>')
@login_required
def po_detail(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    return render_template('purchasing/po_detail.html', po=po)


@purchasing_bp.route('/po/<int:po_id>/send', methods=['POST'])
@login_required
def po_send(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    po.status = 'sent'
    db.session.commit()
    flash(f'{po.po_ref} marked as sent.', 'success')
    return redirect(url_for('purchasing.po_detail', po_id=po.id))


@purchasing_bp.route('/po/<int:po_id>/receive', methods=['POST'])
@login_required
def po_receive(po_id):
    from models import StockMovement
    from flask_login import current_user
    po = PurchaseOrder.query.get_or_404(po_id)
    all_received = True
    for item in po.items:
        recv = float(request.form.get(f'recv_{item.id}', 0))
        if recv > 0:
            item.qty_received += recv
            item.material.stock_qty += recv
            db.session.add(StockMovement(
                material_id=item.material_id,
                movement_type='goods_in',
                qty=recv,
                reference=po.po_ref,
                created_by=current_user.id,
            ))
        if item.qty_received < item.qty:
            all_received = False
    po.status = 'received' if all_received else 'partial'
    db.session.commit()
    flash(f'Goods received for {po.po_ref}.', 'success')
    return redirect(url_for('purchasing.po_detail', po_id=po.id))
