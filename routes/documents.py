from flask import Blueprint, render_template, abort
from flask_login import login_required
from models import Order, WorkOrder

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')


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
