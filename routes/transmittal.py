from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Transmittal, Document
from utils import generate_tx_id, log_activity, METHOD_CHOICES, ACKNOWLEDGED_CHOICES
from datetime import datetime, date

transmittal_bp = Blueprint('transmittal', __name__, url_prefix='/transmittals')

@transmittal_bp.route('/')
@login_required
def transmittal_list():
    acknowledged_filter = request.args.get('acknowledged')

    if current_user.role == 'consultant_limited':
        transmittals = Transmittal.query.all()
        assigned_doc_ids = {d.doc_id for d in current_user.assigned_documents}
        transmittals = [
            tx for tx in transmittals
            if any(doc.doc_id in assigned_doc_ids for doc in tx.documents)
        ]
    else:
        transmittals = Transmittal.query.all()

    if acknowledged_filter:
        transmittals = [tx for tx in transmittals if tx.acknowledged == acknowledged_filter]

    return render_template('transmittal/list.html', transmittals=transmittals)

@transmittal_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_transmittal():
    if request.method == 'POST':
        date_sent_str = request.form.get('date_sent')
        revision_sent = request.form.get('revision_sent')
        recipient = request.form.get('recipient_party')
        method = request.form.get('method')
        purpose = request.form.get('purpose')
        notes = request.form.get('notes')
        doc_ids = request.form.getlist('documents')

        try:
            date_sent = datetime.strptime(date_sent_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('transmittal.new_transmittal'))

        if not doc_ids:
            flash('Please select at least one document.', 'danger')
            return redirect(url_for('transmittal.new_transmittal'))

        tx_id = generate_tx_id()
        transmittal = Transmittal(
            tx_id=tx_id,
            date_sent=date_sent,
            revision_sent=revision_sent,
            recipient_party=recipient,
            method=method,
            purpose=purpose,
            acknowledged='Pending',
            notes=notes
        )

        documents = Document.query.filter(Document.doc_id.in_(doc_ids)).all()
        transmittal.documents = documents

        db.session.add(transmittal)
        db.session.commit()

        log_activity(current_user.id, 'CREATE_TRANSMITTAL', 'transmittal', tx_id)

        flash(f'Transmittal {tx_id} created successfully.', 'success')
        return redirect(url_for('transmittal.transmittal_detail', tx_id=tx_id))

    documents = Document.query.all()
    if current_user.role == 'consultant_limited':
        documents = current_user.assigned_documents

    return render_template('transmittal/new.html', documents=documents, methods=METHOD_CHOICES)

@transmittal_bp.route('/<tx_id>')
@login_required
def transmittal_detail(tx_id):
    transmittal = Transmittal.query.get_or_404(tx_id)

    if current_user.role == 'consultant_limited':
        assigned_doc_ids = {d.doc_id for d in current_user.assigned_documents}
        if not any(doc.doc_id in assigned_doc_ids for doc in transmittal.documents):
            flash('You do not have access to this transmittal.', 'danger')
            return redirect(url_for('transmittal.transmittal_list'))

    return render_template('transmittal/detail.html', transmittal=transmittal)

@transmittal_bp.route('/<tx_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transmittal(tx_id):
    transmittal = Transmittal.query.get_or_404(tx_id)

    if current_user.role not in ('admin', 'consultant_full'):
        flash('You do not have permission to edit transmittals.', 'danger')
        return redirect(url_for('transmittal.transmittal_detail', tx_id=tx_id))

    if request.method == 'POST':
        transmittal.revision_sent = request.form.get('revision_sent')
        transmittal.acknowledged = request.form.get('acknowledged')
        transmittal.notes = request.form.get('notes')
        transmittal.updated_at = datetime.utcnow()

        db.session.commit()

        log_activity(current_user.id, 'UPDATE_TRANSMITTAL', 'transmittal', tx_id)

        flash(f'Transmittal {tx_id} updated successfully.', 'success')
        return redirect(url_for('transmittal.transmittal_detail', tx_id=tx_id))

    return render_template('transmittal/edit.html', transmittal=transmittal, acknowledged_choices=ACKNOWLEDGED_CHOICES)
