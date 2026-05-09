from flask import Blueprint, render_template, request
from flask_login import login_required
from models import db, Order, OrderItem, StockMovement, Material, PurchaseOrder, Customer, Product
from sqlalchemy import func
from datetime import datetime, timedelta, date

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


def _date_range():
    today = date.today()
    default_from = date(today.year, 1, 1)
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    try:
        from_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else default_from
    except (ValueError, TypeError):
        from_date = default_from
    try:
        to_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else today
    except (ValueError, TypeError):
        to_date = today
    return from_date, to_date


@reports_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'overview')
    from_date, to_date = _date_range()

    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.code).all()
    customer_id = request.args.get('customer_id', type=int)
    product_id = request.args.get('product_id', type=int)

    # Overview KPIs (always computed)
    since = datetime.utcnow() - timedelta(days=30)
    recent_orders = Order.query.filter(
        Order.created_at >= since,
        Order.status.in_(['confirmed', 'in_production', 'ready', 'dispatched', 'invoiced'])
    ).all()
    sales_total = sum(o.total for o in recent_orders)
    order_count = len(recent_orders)

    materials_all = Material.query.all()
    stock_value = sum(m.stock_qty * m.cost_price for m in materials_all)

    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(20).all()

    open_pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['draft', 'sent', 'partial'])
    ).all()
    po_value = sum(po.total for po in open_pos)

    # Sales by Customer
    by_customer = []
    by_customer_total = 0
    if tab == 'by_customer':
        q = db.session.query(
            Customer.id,
            Customer.name,
            func.count(Order.id.distinct()).label('order_count'),
            func.coalesce(func.sum(OrderItem.qty_dispatched * OrderItem.unit_price), 0).label('revenue'),
            func.coalesce(func.sum(OrderItem.qty_dispatched), 0).label('qty_total'),
        ).join(Order, Order.customer_id == Customer.id
        ).join(OrderItem, OrderItem.order_id == Order.id
        ).filter(
            Order.status.in_(['dispatched', 'invoiced']),
            Order.dispatched_date >= from_date,
            Order.dispatched_date <= to_date,
        )
        if product_id:
            q = q.filter(OrderItem.product_id == product_id)
        by_customer = q.group_by(Customer.id, Customer.name).order_by(
            func.sum(OrderItem.qty_dispatched * OrderItem.unit_price).desc()
        ).all()
        by_customer_total = sum(r.revenue for r in by_customer)

    # Sales by Product
    by_product = []
    by_product_total = 0
    if tab == 'by_product':
        q = db.session.query(
            Product.id,
            Product.code,
            Product.name,
            func.coalesce(func.sum(OrderItem.qty_dispatched), 0).label('qty_total'),
            func.coalesce(func.sum(OrderItem.qty_dispatched * OrderItem.unit_price), 0).label('revenue'),
        ).join(OrderItem, OrderItem.product_id == Product.id
        ).join(Order, Order.id == OrderItem.order_id
        ).filter(
            Order.status.in_(['dispatched', 'invoiced']),
            Order.dispatched_date >= from_date,
            Order.dispatched_date <= to_date,
        )
        if customer_id:
            q = q.filter(Order.customer_id == customer_id)
        by_product = q.group_by(Product.id, Product.code, Product.name).order_by(
            func.sum(OrderItem.qty_dispatched * OrderItem.unit_price).desc()
        ).all()
        by_product_total = sum(r.revenue for r in by_product)

    return render_template('reports/index.html',
        tab=tab,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        customers=customers,
        products=products,
        customer_id=customer_id,
        product_id=product_id,
        sales_total=sales_total,
        order_count=order_count,
        stock_value=stock_value,
        movements=movements,
        po_value=po_value,
        period_days=30,
        by_customer=by_customer,
        by_customer_total=by_customer_total,
        by_product=by_product,
        by_product_total=by_product_total,
    )
