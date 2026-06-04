from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Order, OrderItem, Customer, Product, DeliveryNote, DeliveryNoteItem, BOMItem, StockMovement
from mrp_engine import create_work_orders_for_order
from datetime import datetime, date
import random, string

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


def gen_ref():
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"ORD-{datetime.now().strftime('%y%m')}-{suffix}"


@orders_bp.route('/')
@login_required
def orders_list():
    status = request.args.get('status', '')
    q = Order.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(Order.created_at.desc()).all()
    return render_template('orders/orders_list.html', orders=orders, status_filter=status)


@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_order():
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.filter_by(is_archived=False).order_by(Product.code).all()
    if request.method == 'POST':
        order = Order(
            order_ref=gen_ref(),
            customer_id=int(request.form['customer_id']),
            required_date=datetime.strptime(request.form['required_date'], '%Y-%m-%d').date() if request.form.get('required_date') else None,
            notes=request.form.get('notes', ''),
            status='draft',
        )
        db.session.add(order)
        db.session.flush()

        product_ids = request.form.getlist('product_id[]')
        qtys = request.form.getlist('qty[]')
        prices = request.form.getlist('unit_price[]')
        for pid, qty, price in zip(product_ids, qtys, prices):
            if pid and qty:
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=int(pid),
                    qty=float(qty),
                    unit_price=float(price or 0),
                ))
        db.session.commit()
        flash(f'Order {order.order_ref} created.', 'success')
        return redirect(url_for('orders.view_order', order_id=order.id))
    return render_template('orders/create_order.html', customers=customers, products=products)


@orders_bp.route('/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Collect all DNs that include items from this order (including multi-order DNs)
    dn_ids = db.session.query(DeliveryNoteItem.dn_id).join(
        OrderItem, DeliveryNoteItem.order_item_id == OrderItem.id
    ).filter(OrderItem.order_id == order.id).distinct()
    all_dns = DeliveryNote.query.filter(
        DeliveryNote.id.in_(dn_ids)
    ).order_by(DeliveryNote.dispatch_date).all()
    return render_template('orders/view_order.html', order=order,
                           today=date.today().isoformat(), all_dns=all_dns)


@orders_bp.route('/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'confirmed'
    db.session.commit()
    create_work_orders_for_order(order)
    flash(f'Order {order.order_ref} confirmed and work orders generated.', 'success')
    return redirect(url_for('orders.view_order', order_id=order.id))


@orders_bp.route('/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    ref = order.order_ref
    db.session.delete(order)
    db.session.commit()
    flash(f'Order {ref} deleted.', 'success')
    return redirect(url_for('orders.orders_list'))


@orders_bp.route('/<int:order_id>/dispatch', methods=['POST'])
@login_required
def dispatch_order(order_id):
    order = Order.query.get_or_404(order_id)
    dispatch_date_str = request.form.get('dispatch_date') or date.today().isoformat()
    dispatch_date = datetime.strptime(dispatch_date_str, '%Y-%m-%d').date()
    dn_notes = request.form.get('dn_notes', '')

    lines = []
    for item in order.items:
        qty_str = request.form.get(f'qty_{item.id}', '0')
        try:
            qty = float(qty_str)
        except ValueError:
            qty = 0
        if qty > 0:
            lines.append((item, min(qty, item.qty_outstanding)))

    if not lines:
        flash('No quantities entered — nothing dispatched.', 'warning')
        return redirect(url_for('orders.view_order', order_id=order.id))

    dn = DeliveryNote(
        dn_ref=DeliveryNote.next_ref(),
        order_id=order.id,
        customer_id=order.customer_id,
        dispatch_date=dispatch_date,
        status='pending',
        notes=dn_notes,
    )
    db.session.add(dn)
    db.session.flush()

    for item, qty in lines:
        db.session.add(DeliveryNoteItem(
            dn_id=dn.id,
            order_item_id=item.id,
            qty_dispatched=qty,
        ))
        item.qty_dispatched = (item.qty_dispatched or 0) + qty

    # stock deduction happens when operator confirms dispatch via /operator/goods-out
    if all(i.qty_outstanding == 0 for i in order.items):
        order.status = 'ready'
    elif order.status == 'confirmed':
        order.status = 'in_production'

    db.session.commit()
    flash(f'Delivery note {dn.dn_ref} created — awaiting dispatch confirmation.', 'success')
    return redirect(url_for('documents.print_delivery_note_dn', dn_id=dn.id))


@orders_bp.route('/<int:order_id>/update-prices', methods=['POST'])
@login_required
def update_prices(order_id):
    order = Order.query.get_or_404(order_id)
    for item in order.items:
        price_str = request.form.get(f'price_{item.id}')
        if price_str is not None:
            try:
                item.unit_price = float(price_str)
            except ValueError:
                pass
    db.session.commit()
    flash('Order prices updated.', 'success')
    return redirect(url_for('orders.view_order', order_id=order.id))


@orders_bp.route('/multi-dispatch', methods=['GET', 'POST'])
@login_required
def multi_dispatch():
    customers = Customer.query.order_by(Customer.name).all()
    selected_customer = None
    outstanding_items = []

    cust_id = request.args.get('customer_id') or request.form.get('customer_id')

    if request.method == 'POST' and 'select_customer' not in request.form:
        # Create the DN
        customer = Customer.query.get_or_404(int(cust_id))
        dispatch_date_str = request.form.get('dispatch_date') or date.today().isoformat()
        dispatch_date = datetime.strptime(dispatch_date_str, '%Y-%m-%d').date()
        dn_notes = request.form.get('dn_notes', '')

        lines = []
        for key, val in request.form.items():
            if key.startswith('qty_'):
                item_id = int(key[4:])
                try:
                    qty = float(val)
                except ValueError:
                    qty = 0
                if qty > 0:
                    item = OrderItem.query.get(item_id)
                    if item and item.order.customer_id == customer.id:
                        lines.append((item, min(qty, item.qty_outstanding)))

        if not lines:
            flash('No quantities entered — nothing dispatched.', 'warning')
            return redirect(url_for('orders.multi_dispatch', customer_id=cust_id))

        dn = DeliveryNote(
            dn_ref=DeliveryNote.next_ref(),
            order_id=None,
            customer_id=customer.id,
            dispatch_date=dispatch_date,
            status='pending',
            notes=dn_notes,
        )
        db.session.add(dn)
        db.session.flush()

        affected_orders = set()
        for item, qty in lines:
            db.session.add(DeliveryNoteItem(
                dn_id=dn.id,
                order_item_id=item.id,
                qty_dispatched=qty,
            ))
            item.qty_dispatched = (item.qty_dispatched or 0) + qty
            affected_orders.add(item.order)

        # stock deduction happens when operator confirms dispatch via /operator/goods-out
        for order in affected_orders:
            if all(i.qty_outstanding == 0 for i in order.items):
                order.status = 'ready'
            elif order.status == 'confirmed':
                order.status = 'in_production'

        db.session.commit()
        flash(f'Delivery note {dn.dn_ref} created covering {len(affected_orders)} order(s) — awaiting dispatch confirmation.', 'success')
        return redirect(url_for('documents.print_delivery_note_dn', dn_id=dn.id))

    if cust_id:
        selected_customer = Customer.query.get(int(cust_id))
        if selected_customer:
            for order in Order.query.filter_by(customer_id=selected_customer.id).filter(
                Order.status.notin_(['dispatched', 'invoiced', 'draft'])
            ).order_by(Order.required_date).all():
                for item in order.items:
                    if item.qty_outstanding > 0:
                        outstanding_items.append(item)

    return render_template('orders/multi_dispatch.html',
                           customers=customers,
                           selected_customer=selected_customer,
                           outstanding_items=outstanding_items,
                           today=date.today().isoformat())


@orders_bp.route('/history')
@login_required
def order_history():
    today = date.today()
    default_from = date(today.year, 1, 1)

    from_str = request.args.get('from')
    to_str = request.args.get('to')
    customer_id = request.args.get('customer_id', type=int)
    product_id = request.args.get('product_id', type=int)

    try:
        from_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else default_from
    except (ValueError, TypeError):
        from_date = default_from
    try:
        to_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else today
    except (ValueError, TypeError):
        to_date = today

    q = Order.query.filter(
        Order.status.in_(['dispatched', 'invoiced']),
        Order.dispatched_date >= from_date,
        Order.dispatched_date <= to_date,
    )
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)
    if product_id:
        order_ids = db.session.query(OrderItem.order_id).filter(
            OrderItem.product_id == product_id
        ).subquery()
        q = q.filter(Order.id.in_(order_ids))

    orders = q.order_by(Order.dispatched_date.desc()).all()
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.filter_by(is_archived=False).order_by(Product.code).all()

    total_revenue = sum(
        sum((i.qty_dispatched or 0) * i.unit_price for i in o.items)
        for o in orders
    )

    return render_template('orders/order_history.html',
        orders=orders,
        customers=customers,
        products=products,
        customer_id=customer_id,
        product_id=product_id,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        total_revenue=total_revenue,
    )


@orders_bp.route('/<int:order_id>/status', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    valid = ['draft', 'confirmed', 'in_production', 'ready', 'dispatched', 'invoiced']
    if new_status in valid:
        order.status = new_status
        if new_status == 'dispatched':
            order.dispatched_date = datetime.utcnow().date()
        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('orders.view_order', order_id=order.id))
