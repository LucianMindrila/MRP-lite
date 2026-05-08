from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Category
from . import inventory_bp


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
