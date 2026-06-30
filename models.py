from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import string

db = SQLAlchemy()

# Association tables
document_source_of_truth = db.Table(
    'document_source_of_truth',
    db.Column('source_of_truth_id', db.Integer, db.ForeignKey('source_of_truth.id'), primary_key=True),
    db.Column('document_id', db.String(20), db.ForeignKey('document.doc_id'), primary_key=True)
)

transmittal_document = db.Table(
    'transmittal_document',
    db.Column('transmittal_id', db.String(20), db.ForeignKey('transmittal.tx_id'), primary_key=True),
    db.Column('document_id', db.String(20), db.ForeignKey('document.doc_id'), primary_key=True)
)

document_contributor = db.Table(
    'document_contributor',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('document_id', db.String(20), db.ForeignKey('document.doc_id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='consultant_limited')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    revisions = db.relationship('Revision', backref='uploader', lazy=True)
    assigned_documents = db.relationship('Document', secondary=document_contributor, backref='contributors')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_view_document(self, document):
        if self.role in ('admin', 'consultant_full'):
            return True
        return document in self.assigned_documents

    def can_upload_revision(self, document):
        if self.role in ('admin', 'consultant_full'):
            return True
        return document in self.assigned_documents

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    doc_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    format = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Draft — Pending Review')
    distribution = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    owner_party = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    revisions = db.relationship('Revision', backref='document', lazy=True, cascade='all, delete-orphan')
    source_of_truth_entries = db.relationship(
        'SourceOfTruth',
        secondary=document_source_of_truth,
        backref='related_documents'
    )
    transmittals = db.relationship(
        'Transmittal',
        secondary=transmittal_document,
        backref='documents'
    )

    @property
    def current_revision(self):
        latest = self.revisions[-1] if self.revisions else None
        return latest.revision_number if latest else None

    @property
    def last_revised_date(self):
        latest = self.revisions[-1] if self.revisions else None
        return latest.revision_date if latest else None

    def __repr__(self):
        return f'<Document {self.doc_id}>'

class Revision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(20), db.ForeignKey('document.doc_id'), nullable=False, index=True)
    revision_number = db.Column(db.String(50), nullable=False)
    revision_date = db.Column(db.Date, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    summary_of_changes = db.Column(db.Text)
    trigger = db.Column(db.String(255))
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Revision {self.document_id} - {self.revision_number}>'

class SourceOfTruth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fact_name = db.Column(db.String(255), nullable=False)
    master_document_id = db.Column(db.String(20), db.ForeignKey('document.doc_id'), nullable=False, index=True)
    sync_rule = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='Unresolved')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    master_document = db.relationship('Document', foreign_keys=[master_document_id], backref='master_facts')

    def __repr__(self):
        return f'<SourceOfTruth {self.fact_name}>'

class Transmittal(db.Model):
    tx_id = db.Column(db.String(20), primary_key=True)
    date_sent = db.Column(db.Date, nullable=False)
    revision_sent = db.Column(db.String(50))
    recipient_party = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text)
    acknowledged = db.Column(db.String(20), nullable=False, default='Pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Transmittal {self.tx_id}>'

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    action = db.Column(db.String(50), nullable=False)
    target_table = db.Column(db.String(50))
    target_id = db.Column(db.String(50))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='activities')

    def __repr__(self):
        return f'<ActivityLog {self.action} on {self.target_table}>'

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    default_currency = db.Column(db.String(3), nullable=False, default='USD')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.name}>'

class Currency(db.Model):
    code = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(5))

    def __repr__(self):
        return f'<Currency {self.code} {self.name}>'

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False, index=True)
    supplier_invoice_no = db.Column(db.String(100))
    bill_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)
    exchange_rate_currency = db.Column(db.String(3), default='MYR')
    linked_po = db.Column(db.String(50))
    reference = db.Column(db.String(255))
    subtotal = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    total_amount_local = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy=True, cascade='all, delete-orphan')

    def calculate_totals(self):
        self.subtotal = sum(item.line_total for item in self.line_items)
        self.tax_amount = sum(item.tax_amount for item in self.line_items)
        self.total_amount = self.subtotal + self.tax_amount
        self.total_amount_local = self.total_amount * self.exchange_rate

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    expense_account = db.Column(db.String(100))
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    tax_percent = db.Column(db.Float, default=0)
    line_total = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)

    def calculate_totals(self):
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.tax_percent / 100)

    def __repr__(self):
        return f'<InvoiceLineItem {self.description}>'
