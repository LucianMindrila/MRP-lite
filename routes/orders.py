from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Order, OrderItem, Customer, Product
from mrp_engine import create_work_orders_for_order
from datetime import datetime
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
    products = Product.query.order_by(Product.code).all()
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
    return render_template('orders/view_order.html', order=order)


@orders_bp.route('/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'confirmed'
    db.session.commit()
    create_work_orders_for_order(order)
    flash(f'Order {order.order_ref} confirmed and work orders generated.', 'success')
    return redirect(url_for('orders.view_order', order_id=order.id))


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
