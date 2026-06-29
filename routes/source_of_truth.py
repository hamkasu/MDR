from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, SourceOfTruth, Document
from utils import log_activity
from datetime import datetime

sot_bp = Blueprint('source_of_truth', __name__, url_prefix='/source-of-truth')

def admin_or_consultant_full(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ('admin', 'consultant_full'):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@sot_bp.route('/')
@login_required
def sot_list():
    facts = SourceOfTruth.query.all()

    status_filter = request.args.get('status')
    if status_filter:
        facts = [f for f in facts if f.status == status_filter]

    return render_template('source_of_truth/list.html', facts=facts)

@sot_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_or_consultant_full
def new_sot():
    if request.method == 'POST':
        fact_name = request.form.get('fact_name')
        master_doc_id = request.form.get('master_document_id')
        sync_rule = request.form.get('sync_rule')
        status = request.form.get('status', 'Unresolved')
        also_appears_in = request.form.getlist('also_appears_in')

        master_doc = Document.query.get_or_404(master_doc_id)

        fact = SourceOfTruth(
            fact_name=fact_name,
            master_document_id=master_doc_id,
            sync_rule=sync_rule,
            status=status
        )

        related_docs = Document.query.filter(Document.doc_id.in_(also_appears_in)).all()
        fact.related_documents = related_docs

        db.session.add(fact)
        db.session.commit()

        log_activity(current_user.id, 'CREATE_SOT', 'source_of_truth', fact.id)

        flash(f'Source of Truth entry "{fact_name}" created successfully.', 'success')
        return redirect(url_for('source_of_truth.sot_list'))

    documents = Document.query.all()
    return render_template('source_of_truth/new.html', documents=documents)

@sot_bp.route('/<int:fact_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_consultant_full
def edit_sot(fact_id):
    fact = SourceOfTruth.query.get_or_404(fact_id)

    if request.method == 'POST':
        fact.fact_name = request.form.get('fact_name')
        fact.sync_rule = request.form.get('sync_rule')
        fact.status = request.form.get('status')

        also_appears_in = request.form.getlist('also_appears_in')
        related_docs = Document.query.filter(Document.doc_id.in_(also_appears_in)).all()
        fact.related_documents = related_docs

        db.session.commit()

        log_activity(current_user.id, 'UPDATE_SOT', 'source_of_truth', fact_id)

        flash(f'Source of Truth entry updated successfully.', 'success')
        return redirect(url_for('source_of_truth.sot_list'))

    documents = Document.query.all()
    return render_template('source_of_truth/edit.html', fact=fact, documents=documents)

@sot_bp.route('/<int:fact_id>/delete', methods=['POST'])
@login_required
@admin_or_consultant_full
def delete_sot(fact_id):
    fact = SourceOfTruth.query.get_or_404(fact_id)
    fact_name = fact.fact_name

    db.session.delete(fact)
    db.session.commit()

    log_activity(current_user.id, 'DELETE_SOT', 'source_of_truth', fact_id, f'Fact: {fact_name}')

    flash(f'Source of Truth entry deleted successfully.', 'success')
    return redirect(url_for('source_of_truth.sot_list'))
