from flask import Blueprint, render_template, request
from flask_login import login_required
from models import Order, StockMovement, Material, PurchaseOrder
from sqlalchemy import func
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    # Sales summary last 30 days
    since = datetime.utcnow() - timedelta(days=30)
    recent_orders = Order.query.filter(
        Order.created_at >= since,
        Order.status.in_(['confirmed', 'in_production', 'ready', 'dispatched', 'invoiced'])
    ).all()

    sales_total = sum(o.total for o in recent_orders)
    order_count = len(recent_orders)

    # Stock value
    materials = Material.query.all()
    stock_value = sum(m.stock_qty * m.cost_price for m in materials)

    # Recent stock movements
    movements = StockMovement.query.order_by(
        StockMovement.created_at.desc()
    ).limit(20).all()

    # Open POs value
    open_pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['draft', 'sent', 'partial'])
    ).all()
    po_value = sum(po.total for po in open_pos)

    return render_template('reports/index.html',
        sales_total=sales_total,
        order_count=order_count,
        stock_value=stock_value,
        movements=movements,
        po_value=po_value,
        period_days=30,
    )
