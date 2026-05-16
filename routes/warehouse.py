from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, StockMovement, StockBatch, Material, PurchaseOrder, Order

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/warehouse')


@warehouse_bp.route('/')
@login_required
def index():
    recent = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(50).all()
    return render_template('warehouse/index.html', movements=recent)


@warehouse_bp.route('/goods-in/po', methods=['GET', 'POST'])
@login_required
def goods_in_po():
    pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['sent', 'partial'])
    ).order_by(PurchaseOrder.po_ref).all()
    selected_po = None
    if request.method == 'POST':
        po_id = request.form.get('po_id')
        if po_id:
            selected_po = PurchaseOrder.query.get(int(po_id))
            if 'submit_recv' in request.form:
                all_received = True
                for item in selected_po.items:
                    recv = float(request.form.get(f'recv_{item.id}', 0))
                    if recv > 0:
                        item.qty_received += recv
                        item.material.stock_qty += recv
                        db.session.add(StockMovement(
                            material_id=item.material_id,
                            movement_type='goods_in',
                            qty=recv,
                            reference=selected_po.po_ref,
                            notes=request.form.get('notes', ''),
                            created_by=current_user.id,
                        ))
                    if item.qty_received < item.qty:
                        all_received = False
                selected_po.status = 'received' if all_received else 'partial'
                db.session.commit()
                flash(f'Goods received against {selected_po.po_ref}.', 'success')
                return redirect(url_for('warehouse.goods_in_po'))
    return render_template('warehouse/goods_in_po.html', pos=pos, selected_po=selected_po)


@warehouse_bp.route('/goods-out/order', methods=['GET', 'POST'])
@login_required
def goods_out_order():
    orders = Order.query.filter(
        Order.status.in_(['confirmed', 'in_production', 'ready'])
    ).order_by(Order.order_ref).all()
    if request.method == 'POST':
        material_id = int(request.form['material_id'])
        qty = float(request.form['qty'])
        reference = request.form.get('reference', '')
        material = Material.query.get_or_404(material_id)
        material.stock_qty -= qty
        db.session.add(StockMovement(
            material_id=material_id,
            movement_type='goods_out',
            qty=-qty,
            reference=reference,
            notes=request.form.get('notes', ''),
            created_by=current_user.id,
        ))
        db.session.commit()
        flash(f'Issued {qty} {material.unit} of {material.code}.', 'success')
        return redirect(url_for('warehouse.goods_out_order'))
    materials = Material.query.order_by(Material.code).all()
    return render_template('warehouse/goods_out_order.html', orders=orders, materials=materials)


@warehouse_bp.route('/stock-check', methods=['GET', 'POST'])
@login_required
def stock_check():
    show_all = request.args.get('show_all', '0') == '1'

    if request.method == 'POST':
        reference = request.form.get('reference', '').strip() or 'STOCK-CHECK'
        all_materials = Material.query.order_by(Material.code).all()
        adjustments = []

        for m in all_materials:
            counted_str = request.form.get(f'count_{m.id}', '').strip()
            if not counted_str:
                continue
            try:
                counted = float(counted_str)
            except ValueError:
                continue

            old_qty = m.stock_qty or 0
            diff = counted - old_qty
            m.stock_qty = counted

            if diff != 0:
                db.session.add(StockMovement(
                    material_id=m.id,
                    movement_type='stock_check',
                    qty=diff,
                    reference=reference,
                    notes=f'Physical count: {counted} (was {old_qty:.2f})',
                    created_by=current_user.id,
                ))
                adjustments.append({
                    'code': m.code,
                    'name': m.name,
                    'unit': m.unit,
                    'old_qty': old_qty,
                    'counted': counted,
                    'diff': diff,
                })

        db.session.commit()

        if not adjustments:
            flash('Stock check complete — no adjustments needed.', 'success')
            return redirect(url_for('warehouse.stock_check'))

        return render_template('warehouse/stock_check_results.html',
                               adjustments=adjustments, reference=reference)

    # GET — filter to active materials by default
    if show_all:
        materials = Material.query.order_by(Material.code).all()
    else:
        materials = Material.query.filter(
            (Material.stock_qty > 0) | (Material.reorder_point > 0)
        ).order_by(Material.code).all()

    # Build batch map: material_id → list of active batches
    batch_map = {}
    for b in StockBatch.query.filter_by(status='active').all():
        batch_map.setdefault(b.material_id, []).append(b)

    return render_template('warehouse/stock_check.html',
                           materials=materials, batch_map=batch_map, show_all=show_all)
