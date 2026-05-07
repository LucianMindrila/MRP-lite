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
    bom_items = db.relationship('BOMItem', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    work_orders = db.relationship('WorkOrder', backref='product', lazy=True)


class BOMItem(db.Model):
    __tablename__ = 'bom_items'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    qty_per_unit = db.Column(db.Float, nullable=False)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.Text)
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
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    work_orders = db.relationship('WorkOrder', backref='order', lazy=True)

    @property
    def total(self):
        return sum(i.qty * i.unit_price for i in self.items)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(200))


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
    movement_type = db.Column(db.String(20), nullable=False)  # goods_in, goods_out, adjustment, stock_check
    qty = db.Column(db.Float, nullable=False)  # positive = in, negative = out
    reference = db.Column(db.String(80))  # PO ref, order ref, etc.
    notes = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[created_by])
