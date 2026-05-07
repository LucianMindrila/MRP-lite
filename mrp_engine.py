from models import db, Order, OrderItem, BOMItem, Material, PurchaseOrder, PurchaseOrderItem, WorkOrder
from datetime import datetime


def get_open_order_requirements():
    """
    For all confirmed/in_production orders, calculate total material requirements.
    Returns a dict: { material_id: { 'material': obj, 'required': float } }
    """
    open_orders = Order.query.filter(
        Order.status.in_(['confirmed', 'in_production'])
    ).all()

    requirements = {}
    for order in open_orders:
        for item in order.items:
            bom = BOMItem.query.filter_by(product_id=item.product_id).all()
            for bom_item in bom:
                mid = bom_item.material_id
                needed = bom_item.qty_per_unit * item.qty
                if mid not in requirements:
                    requirements[mid] = {
                        'material': bom_item.material,
                        'required': 0,
                        'orders': []
                    }
                requirements[mid]['required'] += needed
                requirements[mid]['orders'].append({
                    'order_ref': order.order_ref,
                    'qty': needed
                })
    return requirements


def get_net_requirements():
    """
    Net requirements = gross requirements - current stock.
    Returns items where stock is insufficient.
    """
    gross = get_open_order_requirements()
    net = {}
    for mid, data in gross.items():
        stock = data['material'].stock_qty
        shortfall = data['required'] - stock
        net[mid] = {
            'material': data['material'],
            'required': data['required'],
            'stock': stock,
            'shortfall': shortfall,
            'orders': data['orders']
        }
    return net


def get_shopping_list():
    """
    Returns materials that need to be purchased (shortfall > 0),
    rounded up to reorder_qty if set.
    """
    net = get_net_requirements()
    shopping = []
    for mid, data in net.items():
        if data['shortfall'] > 0:
            mat = data['material']
            order_qty = data['shortfall']
            if mat.reorder_qty and order_qty < mat.reorder_qty:
                order_qty = mat.reorder_qty
            shopping.append({
                'material': mat,
                'shortfall': data['shortfall'],
                'order_qty': order_qty,
                'supplier': mat.supplier,
                'orders': data['orders']
            })
    return shopping


def get_low_stock_alerts():
    """Materials at or below their reorder point."""
    return Material.query.filter(
        Material.stock_qty <= Material.reorder_point,
        Material.reorder_point > 0
    ).all()


def create_work_orders_for_order(order):
    """Auto-generate work orders for each line of a confirmed order."""
    created = []
    for item in order.items:
        existing = WorkOrder.query.filter_by(
            order_id=order.id, product_id=item.product_id
        ).first()
        if not existing:
            wo_ref = f"WO-{order.order_ref}-{item.product_id}"
            wo = WorkOrder(
                wo_ref=wo_ref,
                order_id=order.id,
                product_id=item.product_id,
                qty=item.qty,
                status='pending'
            )
            db.session.add(wo)
            created.append(wo)
    db.session.commit()
    return created


def get_dashboard_stats():
    """Summary counts for the dashboard."""
    from models import Order, PurchaseOrder, WorkOrder, Material
    return {
        'open_orders': Order.query.filter(
            Order.status.in_(['confirmed', 'in_production', 'ready'])
        ).count(),
        'pending_work_orders': WorkOrder.query.filter_by(status='pending').count(),
        'in_progress_work_orders': WorkOrder.query.filter_by(status='in_progress').count(),
        'open_pos': PurchaseOrder.query.filter(
            PurchaseOrder.status.in_(['draft', 'sent', 'partial'])
        ).count(),
        'low_stock_count': len(get_low_stock_alerts()),
        'draft_orders': Order.query.filter_by(status='draft').count(),
    }
