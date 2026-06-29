import os
from datetime import datetime
from flask import current_app
from models import db, Document, Transmittal, ActivityLog

def generate_doc_id():
    last_doc = Document.query.order_by(Document.created_at.desc()).first()
    if not last_doc:
        return 'DOC-001'

    last_number = int(last_doc.doc_id.split('-')[1])
    new_number = last_number + 1
    return f'DOC-{new_number:03d}'

def generate_tx_id():
    last_tx = Transmittal.query.order_by(Transmittal.created_at.desc()).first()
    if not last_tx:
        return 'TX-001'

    last_number = int(last_tx.tx_id.split('-')[1])
    new_number = last_number + 1
    return f'TX-{new_number:03d}'

def get_upload_path(doc_id, revision_number, original_filename):
    base_path = current_app.config['UPLOAD_FOLDER']
    doc_folder = os.path.join(base_path, doc_id)
    os.makedirs(doc_folder, exist_ok=True)

    filename = f"{revision_number}_{original_filename}"
    return os.path.join(doc_folder, filename)

def save_uploaded_file(file, doc_id, revision_number):
    upload_path = get_upload_path(doc_id, revision_number, file.filename)
    file.save(upload_path)
    return upload_path

def log_activity(user_id, action, target_table, target_id, details=None):
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        details=details
    )
    db.session.add(activity)
    db.session.commit()

STATUS_CHOICES = [
    'Active',
    'Active — Pending Signature',
    'Drafted — Pending Send',
    'Superseded',
    'Historical',
    'Draft — Pending Review'
]

DISTRIBUTION_CHOICES = ['Internal', 'External']

METHOD_CHOICES = ['Email', 'Letter', 'In-Person', 'Platform Upload']

ACKNOWLEDGED_CHOICES = ['Pending', 'Acknowledged', 'Unconfirmed']

ROLE_CHOICES = ['admin', 'consultant_full', 'consultant_limited']
