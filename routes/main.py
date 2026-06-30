from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Document, SourceOfTruth
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    if current_user.is_authenticated and current_user.role == 'consultant_limited':
        docs = current_user.assigned_documents
    else:
        docs = Document.query.all()

    total_documents = len(docs)

    status_counts = {}
    for doc in docs:
        status = doc.status
        status_counts[status] = status_counts.get(status, 0) + 1

    pending_send = [d for d in docs if d.status == 'Drafted — Pending Send']
    pending_signature = [d for d in docs if d.status == 'Active — Pending Signature']

    unresolved_facts = SourceOfTruth.query.filter_by(status='Unresolved').all()

    if current_user.is_authenticated and current_user.role == 'consultant_limited':
        unresolved_facts = [
            fact for fact in unresolved_facts
            if fact.master_document in docs or any(d in docs for d in fact.related_documents)
        ]

    return render_template(
        'dashboard.html',
        total_documents=total_documents,
        status_counts=status_counts,
        pending_send=pending_send,
        pending_signature=pending_signature,
        unresolved_facts=unresolved_facts
    )
