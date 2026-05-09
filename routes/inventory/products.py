from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Product, BOMItem, Material, Customer
from . import inventory_bp


def _unique_code(base):
    candidate = f"{base}-COPY"
    n = 1
    while Product.query.filter_by(code=candidate).first():
        n += 1
        candidate = f"{base}-COPY-{n}"
    return candidate


@inventory_bp.route('/products')
@login_required
def products_list():
    customers = Customer.query.order_by(Customer.name).all()
    cust_filter = request.args.get('cust')
    if cust_filter == 'none':
        products = Product.query.filter_by(customer_id=None).order_by(Product.code).all()
        active_customer = 'none'
    elif cust_filter:
        products = Product.query.filter_by(customer_id=int(cust_filter)).order_by(Product.code).all()
        active_customer = int(cust_filter)
    else:
        products = Product.query.order_by(Product.code).all()
        active_customer = None
    return render_template('inventory/products_list.html', products=products,
                           customers=customers, active_customer=active_customer)


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
            customer_id=request.form.get('customer_id') or None,
        )
        db.session.add(p)
        db.session.commit()
        flash(f'Product {p.code} added.', 'success')
        return redirect(url_for('inventory.product_edit', pid=p.id))
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('inventory/product_form.html', product=None,
                           bom_items=[], materials=[], customers=customers)


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
            p.customer_id = request.form.get('customer_id') or None
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

        elif action == 'update_bom':
            bom_id = request.form.get('bom_id')
            qty = request.form.get('bom_qty')
            if bom_id and qty:
                bom = BOMItem.query.get(int(bom_id))
                if bom and bom.product_id == p.id and float(qty) > 0:
                    bom.qty_per_unit = float(qty)
                    db.session.commit()
                    flash('BOM quantity updated.', 'success')

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
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('inventory/product_form.html', product=p, bom_items=bom_items,
                           materials=materials, total_bom_cost=total_bom_cost, customers=customers)


@inventory_bp.route('/products/<int:pid>/delete', methods=['POST'])
@login_required
def product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash(f'Product {p.code} deleted.', 'success')
    return redirect(url_for('inventory.products_list'))


@inventory_bp.route('/products/<int:pid>/copy', methods=['POST'])
@login_required
def product_copy(pid):
    p = Product.query.get_or_404(pid)
    copy = Product(
        code=_unique_code(p.code),
        name=f"{p.name} (Copy)",
        description=p.description,
        unit=p.unit,
        sale_price=p.sale_price,
        lead_time_days=p.lead_time_days,
        customer_id=p.customer_id,
    )
    db.session.add(copy)
    db.session.flush()
    for b in p.bom_items:
        db.session.add(BOMItem(
            product_id=copy.id,
            material_id=b.material_id,
            qty_per_unit=b.qty_per_unit,
        ))
    db.session.commit()
    flash(f'Copy created as {copy.code} with {len(p.bom_items)} BOM line(s). Update the code and name as needed.', 'success')
    return redirect(url_for('inventory.product_edit', pid=copy.id))
