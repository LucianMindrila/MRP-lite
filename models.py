from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='operator')  # admin, manager, operator
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    materials = db.relationship('Material', backref='category', lazy=True)


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.Text)
    lead_time_days = db.Column(db.Integer, default=7)
    materials = db.relationship('Material', backref='supplier', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)


class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), default='pcs')  # pcs, m2, kg, m, ltr
    stock_qty = db.Column(db.Float, default=0)
    reorder_point = db.Column(db.Float, default=0)
    reorder_qty = db.Column(db.Float, default=0)
    cost_price = db.Column(db.Float, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    location = db.Column(db.String(40))  # warehouse location/bay
    notes = db.Column(db.Text)
    bom_status = db.Column(db.String(20))  # None=auto, 'consumable', 'misc_customer'
    bom_items = db.relationship('BOMItem', backref='material', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='material', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), default='pcs')
    sale_price = db.Column(db.Float, default=0)
    lead_time_days = db.Column(db.Integer, default=1)
    is_subassembly = db.Column(db.Boolean, default=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    bom_items = db.relationship('BOMItem', foreign_keys='BOMItem.product_id',
                                backref='product', lazy=True, cascade='all, delete-orphan')
    used_in_boms = db.relationship('BOMItem', foreign_keys='BOMItem.component_product_id',
                                   backref='component_product', lazy=True)
    routing = db.relationship('ProductOperation', backref='product', lazy=True,
                              order_by='ProductOperation.sequence', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    work_orders = db.relationship('WorkOrder', backref='product', lazy=True)


class BOMItem(db.Model):
    __tablename__ = 'bom_items'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    component_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    qty_per_unit = db.Column(db.Float, nullable=False)

    @property
    def component_name(self):
        if self.material:
            return self.material.name
        if self.component_product:
            return self.component_product.name
        return '—'

    @property
    def unit_cost(self):
        if self.material:
            return self.material.cost_price
        return 0


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.Text)
    payment_terms = db.Column(db.String(40), default='30 days Nett')
    orders = db.relationship('Order', backref='customer', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_ref = db.Column(db.String(40), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, confirmed, in_production, ready, dispatched, invoiced
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    required_date = db.Column(db.Date)
    dispatched_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    po_file_path = db.Column(db.String(500))
    email_file_path = db.Column(db.String(500))
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    work_orders = db.relationship('WorkOrder', backref='order', lazy=True, cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(i.qty * i.unit_price for i in self.items)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    qty_dispatched = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(200))

    @property
    def qty_outstanding(self):
        return max(self.qty - (self.qty_dispatched or 0), 0)


class DeliveryNote(db.Model):
    __tablename__ = 'delivery_notes'
    id = db.Column(db.Integer, primary_key=True)
    dn_ref = db.Column(db.String(20), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    dispatch_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, dispatched
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', backref=db.backref('delivery_notes', lazy=True), foreign_keys=[order_id])
    customer = db.relationship('Customer', backref='delivery_notes', lazy=True)
    items = db.relationship('DeliveryNoteItem', backref='delivery_note', lazy=True, cascade='all, delete-orphan')

    @staticmethod
    def next_ref():
        last = DeliveryNote.query.order_by(DeliveryNote.id.desc()).first()
        n = (last.id + 1) if last else 1
        return f'DN-{n:05d}'


class DeliveryNoteItem(db.Model):
    __tablename__ = 'delivery_note_items'
    id = db.Column(db.Integer, primary_key=True)
    dn_id = db.Column(db.Integer, db.ForeignKey('delivery_notes.id'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    qty_dispatched = db.Column(db.Float, nullable=False)
    order_item = db.relationship('OrderItem')


class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    id = db.Column(db.Integer, primary_key=True)
    wo_ref = db.Column(db.String(40), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, complete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    parent_wo_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=True)
    parent_wo = db.relationship('WorkOrder', remote_side='WorkOrder.id', backref='sub_work_orders')


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    po_ref = db.Column(db.String(40), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, sent, partial, received, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(i.qty * i.unit_price for i in self.items)


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    qty_received = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    material = db.relationship('Material')


class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # goods_in, goods_out, adjustment, stock_check, transfer
    qty = db.Column(db.Float, nullable=False)  # positive = in, negative = out, 0 = location transfer
    reference = db.Column(db.String(80))  # PO ref, order ref, etc.
    notes = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[created_by])


class StockBatch(db.Model):
    __tablename__ = 'stock_batches'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    qty = db.Column(db.Float, nullable=False)           # current qty on this batch
    qty_original = db.Column(db.Float, nullable=False)  # qty when first received
    building = db.Column(db.String(20), nullable=False) # Unit 4, Unit 7, Unit 16
    location_detail = db.Column(db.String(200))         # freeform: 'middle racking left bay'
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    received_by = db.Column(db.String(10))              # operator initials
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active') # active, empty
    notes = db.Column(db.String(200))
    material = db.relationship('Material', backref='stock_batches')
    purchase_order = db.relationship('PurchaseOrder', backref='stock_batches')


# --- Production Routing & Scheduling ---

class Machine(db.Model):
    __tablename__ = 'machines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    machine_type = db.Column(db.String(40))   # CNC Router, CNC Milling, Beamsaw, etc.
    unit = db.Column(db.String(10))            # U3, U4, U7, U16
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)


operation_machines = db.Table(
    'operation_machines',
    db.Column('operation_id', db.Integer, db.ForeignKey('operations.id'), primary_key=True),
    db.Column('machine_id', db.Integer, db.ForeignKey('machines.id'), primary_key=True)
)


class Operation(db.Model):
    __tablename__ = 'operations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)  # Beamsaw, CNC Roughing, etc.
    requires_machine = db.Column(db.Boolean, default=True)        # False for Assembly, Packing, QC
    notes = db.Column(db.Text)
    eligible_machines = db.relationship('Machine', secondary='operation_machines',
                                        backref='operations', lazy=True)


class ProductOperation(db.Model):
    __tablename__ = 'product_operations'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    operation_id = db.Column(db.Integer, db.ForeignKey('operations.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)       # 1, 2, 3... defines the order
    daily_output = db.Column(db.Float, nullable=True)      # units per working day; null = TBD
    notes = db.Column(db.Text)
    operation = db.relationship('Operation', backref='product_operations')


class ProductionTask(db.Model):
    __tablename__ = 'production_tasks'
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    product_operation_id = db.Column(db.Integer, db.ForeignKey('product_operations.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=True)  # null for manual ops
    planned_start = db.Column(db.Date, nullable=False)
    planned_end = db.Column(db.Date, nullable=False)
    qty = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, complete
    actual_start = db.Column(db.Date)
    actual_end = db.Column(db.Date)
    notes = db.Column(db.Text)
    work_order = db.relationship('WorkOrder', backref='production_tasks')
    product_operation = db.relationship('ProductOperation', backref='production_tasks')
    machine = db.relationship('Machine', backref='production_tasks')
