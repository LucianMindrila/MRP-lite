from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Material, Supplier, Category, Product, BOMItem
from . import inventory_bp


def _all_categories():
    return Category.query.order_by(Category.name).all()


def _unique_code(base):
    candidate = f"{base}-COPY"
    n = 1
    while Material.query.filter_by(code=candidate).first():
        n += 1
        candidate = f"{base}-COPY-{n}"
    return candidate


BOM_AUTO_BLUE = {'Consumables', 'Tooling'}
BOM_STATUS_OPTIONS = [
    ('', 'Auto (system decides)'),
    ('consumable', 'Consumable — no product assignment needed'),
    ('misc_customer', 'Misc Customers — used for unregistered customers'),
]


@inventory_bp.route('/materials')
@login_required
def materials_list():
    categories = _all_categories()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    cat_filter = request.args.get('cat')
    if cat_filter == 'none':
        materials = Material.query.filter_by(category_id=None).order_by(Material.code).all()
        active_cat = 'none'
    elif cat_filter:
        materials = Material.query.filter_by(category_id=int(cat_filter)).order_by(Material.code).all()
        active_cat = int(cat_filter)
    else:
        materials = Material.query.order_by(Material.code).all()
        active_cat = None
    bom_mat_ids = {r[0] for r in db.session.query(BOMItem.material_id).distinct().all()}
    return render_template('inventory/materials_list.html', materials=materials,
                           suppliers=suppliers, categories=categories, active_cat=active_cat,
                           bom_mat_ids=bom_mat_ids, bom_auto_blue=BOM_AUTO_BLUE,
                           bom_status_options=BOM_STATUS_OPTIONS)


@inventory_bp.route('/materials/add', methods=['GET', 'POST'])
@login_required
def material_add():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    categories = _all_categories()
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
            category_id=request.form.get('category_id') or None,
            location=request.form.get('location', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(m)
        db.session.commit()
        flash(f'Material {m.code} added.', 'success')
        return redirect(url_for('inventory.materials_list'))
    return render_template('inventory/material_form.html', material=None,
                           suppliers=suppliers, categories=categories)


@inventory_bp.route('/materials/<int:mid>/edit', methods=['GET', 'POST'])
@login_required
def material_edit(mid):
    m = Material.query.get_or_404(mid)
    suppliers = Supplier.query.order_by(Supplier.name).all()
    categories = _all_categories()
    products = Product.query.order_by(Product.code).all()

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        if action == 'save':
            m.name = request.form['name'].strip()
            m.description = request.form.get('description', '').strip()
            m.unit = request.form.get('unit', 'pcs')
            m.reorder_point = float(request.form.get('reorder_point', 0))
            m.reorder_qty = float(request.form.get('reorder_qty', 0))
            m.cost_price = float(request.form.get('cost_price', 0))
            m.supplier_id = request.form.get('supplier_id') or None
            m.category_id = request.form.get('category_id') or None
            m.location = request.form.get('location', '').strip()
            m.notes = request.form.get('notes', '').strip()
            m.bom_status = request.form.get('bom_status') or None
            db.session.commit()
            flash(f'Material {m.code} updated.', 'success')
            return redirect(url_for('inventory.materials_list'))

        elif action == 'add_bom':
            product_id = request.form.get('bom_product_id')
            qty = request.form.get('bom_qty', 1)
            if product_id and float(qty) > 0:
                existing = BOMItem.query.filter_by(product_id=int(product_id), material_id=m.id).first()
                if existing:
                    existing.qty_per_unit = float(qty)
                    flash('BOM line updated.', 'success')
                else:
                    db.session.add(BOMItem(product_id=int(product_id), material_id=m.id, qty_per_unit=float(qty)))
                    flash('BOM line added.', 'success')
                db.session.commit()
            return redirect(url_for('inventory.material_edit', mid=mid))

        elif action == 'update_bom':
            bom_id = request.form.get('bom_id')
            qty = request.form.get('bom_qty')
            if bom_id and qty:
                bom = BOMItem.query.get(int(bom_id))
                if bom and bom.material_id == m.id and float(qty) > 0:
                    bom.qty_per_unit = float(qty)
                    db.session.commit()
                    flash('Quantity updated.', 'success')
            return redirect(url_for('inventory.material_edit', mid=mid))

        elif action == 'delete_bom':
            bom_id = request.form.get('bom_id')
            if bom_id:
                bom = BOMItem.query.get(int(bom_id))
                if bom and bom.material_id == m.id:
                    db.session.delete(bom)
                    db.session.commit()
                    flash('BOM line removed.', 'success')
            return redirect(url_for('inventory.material_edit', mid=mid))

    bom_items = BOMItem.query.filter_by(material_id=m.id).all()
    return render_template('inventory/material_form.html', material=m,
                           suppliers=suppliers, categories=categories,
                           products=products, bom_items=bom_items,
                           bom_status_options=BOM_STATUS_OPTIONS)


@inventory_bp.route('/materials/<int:mid>/delete', methods=['POST'])
@login_required
def material_delete(mid):
    m = Material.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    flash(f'Material {m.code} deleted.', 'success')
    return redirect(url_for('inventory.materials_list'))


@inventory_bp.route('/materials/<int:mid>/copy', methods=['POST'])
@login_required
def material_copy(mid):
    m = Material.query.get_or_404(mid)
    copy = Material(
        code=_unique_code(m.code),
        name=f"{m.name} (Copy)",
        description=m.description,
        unit=m.unit,
        stock_qty=0,
        reorder_point=m.reorder_point,
        reorder_qty=m.reorder_qty,
        cost_price=m.cost_price,
        supplier_id=m.supplier_id,
        category_id=m.category_id,
        location=m.location,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f'Copy created as {copy.code}. Update the code and name as needed.', 'success')
    return redirect(url_for('inventory.material_edit', mid=copy.id))
