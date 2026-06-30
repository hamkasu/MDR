from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Invoice, InvoiceLineItem, Supplier, Currency
from utils import log_activity
from datetime import datetime, date
import json

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')

CURRENCY_RATES = {
    'USD': {'MYR': 4.50, 'SGD': 1.35, 'GBP': 0.79, 'EUR': 0.92},
    'MYR': {'USD': 0.22, 'SGD': 0.30, 'GBP': 0.18, 'EUR': 0.20},
}

@invoices_bp.route('/')
@login_required
def invoices_list():
    invoices = Invoice.query.order_by(Invoice.bill_date.desc()).all()
    status_filter = request.args.get('status')

    if status_filter:
        invoices = [inv for inv in invoices if inv.status == status_filter]

    return render_template('invoices/list.html', invoices=invoices)

@invoices_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    suppliers = Supplier.query.all()
    currencies = ['USD', 'MYR', 'SGD', 'GBP', 'EUR']

    if request.method == 'POST':
        try:
            supplier_id = request.form.get('supplier_id')
            invoice_number = request.form.get('invoice_number')
            supplier_invoice_no = request.form.get('supplier_invoice_no')
            bill_date = datetime.strptime(request.form.get('bill_date'), '%m/%d/%Y').date()
            due_date_str = request.form.get('due_date')
            due_date = datetime.strptime(due_date_str, '%m/%d/%Y').date() if due_date_str else None
            currency = request.form.get('currency', 'USD')
            exchange_rate = float(request.form.get('exchange_rate', 1.0))
            exchange_rate_currency = request.form.get('exchange_rate_currency', 'MYR')
            linked_po = request.form.get('linked_po')
            reference = request.form.get('reference')
            notes = request.form.get('notes')

            invoice = Invoice(
                invoice_number=invoice_number,
                supplier_id=supplier_id,
                supplier_invoice_no=supplier_invoice_no,
                bill_date=bill_date,
                due_date=due_date,
                currency=currency,
                exchange_rate=exchange_rate,
                exchange_rate_currency=exchange_rate_currency,
                linked_po=linked_po,
                reference=reference,
                notes=notes
            )

            db.session.add(invoice)
            db.session.flush()

            line_items_json = request.form.get('line_items', '[]')
            line_items_data = json.loads(line_items_json)

            for item_data in line_items_data:
                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=item_data.get('description'),
                    expense_account=item_data.get('expense_account'),
                    quantity=float(item_data.get('quantity', 1)),
                    unit_price=float(item_data.get('unit_price', 0)),
                    tax_percent=float(item_data.get('tax_percent', 0))
                )
                line_item.calculate_totals()
                db.session.add(line_item)

            invoice.calculate_totals()
            db.session.commit()

            log_activity(current_user.id, 'CREATE_INVOICE', 'invoice', invoice.id, f'Invoice: {invoice_number}')

            flash(f'Invoice {invoice_number} created successfully.', 'success')
            return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'danger')
            return redirect(url_for('invoices.new_invoice'))

    return render_template('invoices/new.html', suppliers=suppliers, currencies=currencies)

@invoices_bp.route('/<int:invoice_id>')
@login_required
def invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoices/detail.html', invoice=invoice)

@invoices_bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    suppliers = Supplier.query.all()
    currencies = ['USD', 'MYR', 'SGD', 'GBP', 'EUR']

    if request.method == 'POST':
        try:
            invoice.supplier_id = request.form.get('supplier_id')
            invoice.supplier_invoice_no = request.form.get('supplier_invoice_no')
            invoice.bill_date = datetime.strptime(request.form.get('bill_date'), '%m/%d/%Y').date()
            due_date_str = request.form.get('due_date')
            invoice.due_date = datetime.strptime(due_date_str, '%m/%d/%Y').date() if due_date_str else None
            invoice.currency = request.form.get('currency', 'USD')
            invoice.exchange_rate = float(request.form.get('exchange_rate', 1.0))
            invoice.exchange_rate_currency = request.form.get('exchange_rate_currency', 'MYR')
            invoice.linked_po = request.form.get('linked_po')
            invoice.reference = request.form.get('reference')
            invoice.notes = request.form.get('notes')
            invoice.status = request.form.get('status', 'Pending')

            InvoiceLineItem.query.filter_by(invoice_id=invoice.id).delete()

            line_items_json = request.form.get('line_items', '[]')
            line_items_data = json.loads(line_items_json)

            for item_data in line_items_data:
                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=item_data.get('description'),
                    expense_account=item_data.get('expense_account'),
                    quantity=float(item_data.get('quantity', 1)),
                    unit_price=float(item_data.get('unit_price', 0)),
                    tax_percent=float(item_data.get('tax_percent', 0))
                )
                line_item.calculate_totals()
                db.session.add(line_item)

            invoice.calculate_totals()
            invoice.updated_at = datetime.utcnow()
            db.session.commit()

            log_activity(current_user.id, 'UPDATE_INVOICE', 'invoice', invoice_id)

            flash(f'Invoice updated successfully.', 'success')
            return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating invoice: {str(e)}', 'danger')
            return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))

    return render_template('invoices/edit.html', invoice=invoice, suppliers=suppliers, currencies=currencies)

@invoices_bp.route('/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()

    log_activity(current_user.id, 'DELETE_INVOICE', 'invoice', invoice_id, f'Invoice: {invoice_number}')

    flash(f'Invoice {invoice_number} deleted.', 'success')
    return redirect(url_for('invoices.invoices_list'))

@invoices_bp.route('/suppliers/list')
@login_required
def suppliers_list():
    suppliers = Supplier.query.all()
    return render_template('invoices/suppliers.html', suppliers=suppliers)

@invoices_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        name = request.form.get('name')
        contact_email = request.form.get('contact_email')
        contact_phone = request.form.get('contact_phone')
        default_currency = request.form.get('default_currency', 'USD')
        notes = request.form.get('notes')

        supplier = Supplier(
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            default_currency=default_currency,
            notes=notes
        )
        db.session.add(supplier)
        db.session.commit()

        log_activity(current_user.id, 'CREATE_SUPPLIER', 'supplier', supplier.id, f'Supplier: {name}')

        flash(f'Supplier {name} added successfully.', 'success')
        return redirect(url_for('invoices.suppliers_list'))

    return render_template('invoices/add_supplier.html', currencies=['USD', 'MYR', 'SGD', 'GBP', 'EUR'])

@invoices_bp.route('/api/exchange-rate')
def get_exchange_rate():
    from_currency = request.args.get('from', 'USD')
    to_currency = request.args.get('to', 'MYR')

    if from_currency in CURRENCY_RATES and to_currency in CURRENCY_RATES[from_currency]:
        rate = CURRENCY_RATES[from_currency][to_currency]
        return jsonify({'rate': rate})

    return jsonify({'rate': 1.0})
