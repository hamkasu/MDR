"""Add invoice management tables

Revision ID: 002
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'supplier',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_email', sa.String(120)),
        sa.Column('contact_phone', sa.String(20)),
        sa.Column('default_currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_supplier_name'),
        sa.Index('ix_supplier_name', 'name')
    )

    op.create_table(
        'currency',
        sa.Column('code', sa.String(3), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(5)),
        sa.PrimaryKeyConstraint('code')
    )

    op.create_table(
        'invoice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_invoice_no', sa.String(100)),
        sa.Column('bill_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date()),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('exchange_rate', sa.Float(), server_default='1.0'),
        sa.Column('exchange_rate_currency', sa.String(3), server_default='MYR'),
        sa.Column('linked_po', sa.String(50)),
        sa.Column('reference', sa.String(255)),
        sa.Column('subtotal', sa.Float(), server_default='0.0'),
        sa.Column('tax_amount', sa.Float(), server_default='0.0'),
        sa.Column('total_amount', sa.Float(), server_default='0.0'),
        sa.Column('total_amount_local', sa.Float(), server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='Pending'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number', name='uq_invoice_number'),
        sa.Index('ix_invoice_number', 'invoice_number'),
        sa.Index('ix_invoice_supplier_id', 'supplier_id')
    )

    op.create_table(
        'invoice_line_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('expense_account', sa.String(100)),
        sa.Column('quantity', sa.Float(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('tax_percent', sa.Float(), server_default='0'),
        sa.Column('line_total', sa.Float(), server_default='0.0'),
        sa.Column('tax_amount', sa.Float(), server_default='0.0'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_invoice_line_item_invoice_id', 'invoice_id')
    )

def downgrade():
    op.drop_table('invoice_line_item')
    op.drop_table('invoice')
    op.drop_table('currency')
    op.drop_table('supplier')
