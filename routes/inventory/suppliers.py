from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Supplier
from . import inventory_bp


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
            address=request.form.get('address', '').strip(),
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
        s.address = request.form.get('address', '').strip()
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
