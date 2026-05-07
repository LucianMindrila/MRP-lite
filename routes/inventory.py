from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Material, Product, BOMItem, Supplier, Customer, Category

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ── SUPPLIERS ────────────────────────────────────────────────────

@inventory_bp.route('/suppliers')
@login_required
def suppliers_list():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('inventory/suppliers_list.html', suppliers=suppliers)


@inventory_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def supplier_add():
    if request.method == 'POST':
        s = Supplier(
            name=request.form['name'].strip(),
            contact=request.form.get('contact', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            lead_time_days=int(request.form.get('lead_time_days', 7)),
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Supplier "{s.name}" added.', 'success')
        return redirect(url_for('inventory.suppliers_list'))
    return render_template('inventory/supplier_form.html', supplier=None)


@inventory_bp.route('/suppliers/<int:sid>/edit', methods=['GET', 'POST'])
@login_required
def supplier_edit(sid):
    s = Supplier.query.get_or_404(sid)
    if request.method == 'POST':
        s.name = request.form['name'].strip()
        s.contact = request.form.get('contact', '').strip()
        s.email = request.form.get('email', '').strip()
        s.phone = request.form.get('phone', '').strip()
        s.lead_time_days = int(request.form.get('lead_time_days', 7))
        db.session.commit()
        flash(f'Supplier "{s.name}" updated.', 'success')
        return redirect(url_for('inventory.suppliers_list'))
    return render_template('inventory/supplier_form.html', supplier=s)


@inventory_bp.route('/suppliers/<int:sid>/delete', methods=['POST'])
@login_required
def supplier_delete(sid):
    s = Supplier.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    flash(f'Supplier "{s.name}" deleted.', 'success')
    return redirect(url_for('inventory.suppliers_list'))


# ── CUSTOMERS ────────────────────────────────────────────────────

@inventory_bp.route('/customers')
@login_required
def customers_list():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('inventory/customers_list.html', customers=customers)


@inventory_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def customer_add():
    if request.method == 'POST':
        c = Customer(
            name=request.form['name'].strip(),
            contact=request.form.get('contact', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            address=request.form.get('address', '').strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Customer "{c.name}" added.', 'success')
        return redirect(url_for('inventory.customers_list'))
    return render_template('inventory/customer_form.html', customer=None)


@inventory_bp.route('/customers/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
def customer_edit(cid):
    c = Customer.query.get_or_404(cid)
    if request.method == 'POST':
        c.name = request.form['name'].strip()
        c.contact = request.form.get('contact', '').strip()
        c.email = request.form.get('email', '').strip()
        c.phone = request.form.get('phone', '').strip()
        c.address = request.form.get('address', '').strip()
        db.session.commit()
        flash(f'Customer "{c.name}" updated.', 'success')
        return redirect(url_for('inventory.customers_list'))
    return render_template('inventory/customer_form.html', customer=c)


@inventory_bp.route('/customers/<int:cid>/delete', methods=['POST'])
@login_required
def customer_delete(cid):
    c = Customer.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash(f'Customer "{c.name}" deleted.', 'success')
    return redirect(url_for('inventory.customers_list'))


# ── MATERIALS ────────────────────────────────────────────────────

@inventory_bp.route('/materials')
@login_required
def materials_list():
    materials = Material.query.order_by(Material.code).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('inventory/materials_list.html', materials=materials, suppliers=suppliers)


@inventory_bp.route('/materials/add', methods=['GET', 'POST'])
@login_required
def material_add():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    if request.method == 'POST':
        m = Material(
            code=request.form['code'].strip().upper(),
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip(),
            unit=request.form.get('unit', 'pcs'),
            stock_qty=float(request.form.get('stock_qty', 0)),
            reorder_point=float(request.form.get('reorder_point', 0)),
            reorder_qty=float(request.form.get('reorder_qty', 0)),
            cost_price=float(request.form.get('cost_price', 0)),
            supplier_id=request.form.get('supplier_id') or None,
            location=request.form.get('location', '').strip(),
        )
        db.session.add(m)
        db.session.commit()
        flash(f'Material {m.code} added.', 'success')
        return redirect(url_for('inventory.materials_list'))
    return render_template('inventory/material_form.html', material=None, suppliers=suppliers)


@inventory_bp.route('/materials/<int:mid>/edit', methods=['GET', 'POST'])
@login_required
def material_edit(mid):
    m = Material.query.get_or_404(mid)
    suppliers = Supplier.query.order_by(Supplier.name).all()
    if request.method == 'POST':
        m.name = request.form['name'].strip()
        m.description = request.form.get('description', '').strip()
        m.unit = request.form.get('unit', 'pcs')
        m.reorder_point = float(request.form.get('reorder_point', 0))
        m.reorder_qty = float(request.form.get('reorder_qty', 0))
        m.cost_price = float(request.form.get('cost_price', 0))
        m.supplier_id = request.form.get('supplier_id') or None
        m.location = request.form.get('location', '').strip()
        db.session.commit()
        flash(f'Material {m.code} updated.', 'success')
        return redirect(url_for('inventory.materials_list'))
    return render_template('inventory/material_form.html', material=m, suppliers=suppliers)


@inventory_bp.route('/materials/<int:mid>/delete', methods=['POST'])
@login_required
def material_delete(mid):
    m = Material.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    flash(f'Material {m.code} deleted.', 'success')
    return redirect(url_for('inventory.materials_list'))


# ── PRODUCTS ─────────────────────────────────────────────────────

@inventory_bp.route('/products')
@login_required
def products_list():
    products = Product.query.order_by(Product.code).all()
    return render_template('inventory/products_list.html', products=products)


@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    if request.method == 'POST':
        p = Product(
            code=request.form['code'].strip().upper(),
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip(),
            unit=request.form.get('unit', 'pcs'),
            sale_price=float(request.form.get('sale_price', 0)),
            lead_time_days=int(request.form.get('lead_time_days', 1)),
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Product {p.code} added.', 'success')
        return redirect(url_for('inventory.product_edit', pid=p.id))
    return render_template('inventory/product_form.html', product=None, bom_items=[], materials=[])


@inventory_bp.route('/products/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(pid):
    p = Product.query.get_or_404(pid)
    materials = Material.query.order_by(Material.code).all()

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        if action == 'save':
            p.name = request.form['name'].strip()
            p.description = request.form.get('description', '').strip()
            p.unit = request.form.get('unit', 'pcs')
            p.sale_price = float(request.form.get('sale_price', 0))
            p.lead_time_days = int(request.form.get('lead_time_days', 1))
            db.session.commit()
            flash(f'Product {p.code} updated.', 'success')

        elif action == 'add_bom':
            material_id = request.form.get('bom_material_id')
            qty = request.form.get('bom_qty', 0)
            if material_id and float(qty) > 0:
                existing = BOMItem.query.filter_by(product_id=p.id, material_id=int(material_id)).first()
                if existing:
                    existing.qty_per_unit = float(qty)
                    flash('BOM line updated.', 'success')
                else:
                    db.session.add(BOMItem(product_id=p.id, material_id=int(material_id), qty_per_unit=float(qty)))
                    flash('BOM line added.', 'success')
                db.session.commit()

        elif action == 'delete_bom':
            bom_id = request.form.get('bom_id')
            if bom_id:
                bom = BOMItem.query.get(int(bom_id))
                if bom and bom.product_id == p.id:
                    db.session.delete(bom)
                    db.session.commit()
                    flash('BOM line removed.', 'success')

        return redirect(url_for('inventory.product_edit', pid=p.id))

    bom_items = BOMItem.query.filter_by(product_id=p.id).all()
    total_bom_cost = sum(b.qty_per_unit * b.material.cost_price for b in bom_items)
    return render_template('inventory/product_form.html', product=p, bom_items=bom_items, materials=materials, total_bom_cost=total_bom_cost)


@inventory_bp.route('/products/<int:pid>/delete', methods=['POST'])
@login_required
def product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash(f'Product {p.code} deleted.', 'success')
    return redirect(url_for('inventory.products_list'))


# ── CATEGORIES ───────────────────────────────────────────────────

@inventory_bp.route('/categories')
@login_required
def categories_list():
    categories = Category.query.order_by(Category.name).all()
    return render_template('inventory/categories_list.html', categories=categories)


@inventory_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def category_add():
    if request.method == 'POST':
        c = Category(
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Category "{c.name}" added.', 'success')
        return redirect(url_for('inventory.categories_list'))
    return render_template('inventory/category_form.html', category=None)


@inventory_bp.route('/categories/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(cid):
    c = Category.query.get_or_404(cid)
    if request.method == 'POST':
        c.name = request.form['name'].strip()
        c.description = request.form.get('description', '').strip()
        db.session.commit()
        flash(f'Category "{c.name}" updated.', 'success')
        return redirect(url_for('inventory.categories_list'))
    return render_template('inventory/category_form.html', category=c)


@inventory_bp.route('/categories/<int:cid>/delete', methods=['POST'])
@login_required
def category_delete(cid):
    c = Category.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash(f'Category "{c.name}" deleted.', 'success')
    return redirect(url_for('inventory.categories_list'))
