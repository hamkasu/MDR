from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from models import db, Document, Revision, SourceOfTruth
from utils import generate_doc_id, save_uploaded_file, log_activity
from datetime import datetime, date
import os

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

def check_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        doc_id = kwargs.get('doc_id')
        doc = Document.query.get_or_404(doc_id)

        if current_user.is_authenticated and current_user.role == 'consultant_limited':
            if doc not in current_user.assigned_documents:
                flash('You do not have access to this document.', 'danger')
                return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)
    return decorated_function

@documents_bp.route('/')
@login_required
def documents_list():
    if current_user.is_authenticated and current_user.role == 'consultant_limited':
        documents = current_user.assigned_documents
    else:
        documents = Document.query.all()

    status_filter = request.args.get('status')
    if status_filter:
        documents = [d for d in documents if d.status == status_filter]

    distribution_filter = request.args.get('distribution')
    if distribution_filter:
        documents = [d for d in documents if d.distribution == distribution_filter]

    search_query = request.args.get('search')
    if search_query:
        documents = [
            d for d in documents
            if search_query.lower() in d.name.lower() or search_query.lower() in d.description.lower()
        ]

    return render_template('documents/list.html', documents=documents)

@documents_bp.route('/<doc_id>')
@check_access
def document_detail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    facts_as_master = SourceOfTruth.query.filter_by(master_document_id=doc_id).all()
    facts_in_list = SourceOfTruth.query.all()
    facts_appears_in = [f for f in facts_in_list if doc in f.related_documents]

    return render_template(
        'documents/detail.html',
        document=doc,
        facts_as_master=facts_as_master,
        facts_appears_in=facts_appears_in
    )

@documents_bp.route('/<doc_id>/revisions/new', methods=['GET', 'POST'])
@check_access
def upload_revision(doc_id):
    doc = Document.query.get_or_404(doc_id)

    if not current_user.is_authenticated or not current_user.can_upload_revision(doc):
        flash('You must be logged in to upload revisions.', 'danger')
        return redirect(url_for('documents.document_detail', doc_id=doc_id))

    if request.method == 'POST':
        file = request.files.get('file')
        summary = request.form.get('summary_of_changes')
        trigger = request.form.get('trigger')

        if not file or file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('documents.upload_revision', doc_id=doc_id))

        try:
            next_revision_num = len(doc.revisions) + 1
            revision_number = f'Rev {next_revision_num}'

            file_path = save_uploaded_file(file, doc_id, revision_number)

            revision = Revision(
                document_id=doc_id,
                revision_number=revision_number,
                revision_date=date.today(),
                file_path=file_path,
                original_filename=file.filename,
                summary_of_changes=summary,
                trigger=trigger,
                uploaded_by_user_id=current_user.id
            )
            db.session.add(revision)
            doc.updated_at = datetime.utcnow()
            db.session.commit()

            log_activity(current_user.id, 'UPLOAD_REVISION', 'revision', revision.id, f'Document: {doc_id}')

            flash(f'Revision {revision_number} uploaded successfully.', 'success')
            return redirect(url_for('documents.document_detail', doc_id=doc_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading file: {str(e)}', 'danger')
            return redirect(url_for('documents.upload_revision', doc_id=doc_id))

    return render_template('documents/upload_revision.html', document=doc)

@documents_bp.route('/<doc_id>/revisions/<int:revision_id>/download')
@check_access
def download_revision(doc_id, revision_id):
    doc = Document.query.get_or_404(doc_id)
    revision = Revision.query.filter_by(id=revision_id, document_id=doc_id).first_or_404()

    if current_user.is_authenticated:
        log_activity(current_user.id, 'DOWNLOAD_REVISION', 'revision', revision_id, f'Document: {doc_id}')

    return send_file(
        revision.file_path,
        as_attachment=True,
        download_name=revision.original_filename
    )
