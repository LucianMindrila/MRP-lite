from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Customer
from . import inventory_bp


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
            payment_terms=request.form.get('payment_terms', '30 days Nett').strip(),
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
        c.payment_terms = request.form.get('payment_terms', '30 days Nett').strip()
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
