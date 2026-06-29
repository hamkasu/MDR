"""Initial schema with documents, revisions, source of truth, transmittals, users, and activity log

Revision ID: 001
Revises:
Create Date: 2025-06-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    # Create document table
    op.create_table(
        'document',
        sa.Column('doc_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('distribution', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_party', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('doc_id')
    )

    # Create revision table
    op.create_table(
        'revision',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=20), nullable=False),
        sa.Column('revision_number', sa.String(length=50), nullable=False),
        sa.Column('revision_date', sa.Date(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('summary_of_changes', sa.Text(), nullable=True),
        sa.Column('trigger', sa.String(length=255), nullable=True),
        sa.Column('uploaded_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.doc_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revision_document_id'), 'revision', ['document_id'], unique=False)
    op.create_index(op.f('ix_revision_uploaded_by_user_id'), 'revision', ['uploaded_by_user_id'], unique=False)

    # Create source_of_truth table
    op.create_table(
        'source_of_truth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fact_name', sa.String(length=255), nullable=False),
        sa.Column('master_document_id', sa.String(length=20), nullable=False),
        sa.Column('sync_rule', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['master_document_id'], ['document.doc_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_of_truth_master_document_id'), 'source_of_truth', ['master_document_id'], unique=False)

    # Create transmittal table
    op.create_table(
        'transmittal',
        sa.Column('tx_id', sa.String(length=20), nullable=False),
        sa.Column('date_sent', sa.Date(), nullable=False),
        sa.Column('revision_sent', sa.String(length=50), nullable=True),
        sa.Column('recipient_party', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('acknowledged', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('tx_id')
    )

    # Create activity_log table
    op.create_table(
        'activity_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target_table', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_log_timestamp'), 'activity_log', ['timestamp'], unique=False)
    op.create_index(op.f('ix_activity_log_user_id'), 'activity_log', ['user_id'], unique=False)

    # Create association tables
    op.create_table(
        'document_source_of_truth',
        sa.Column('source_of_truth_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.doc_id'], ),
        sa.ForeignKeyConstraint(['source_of_truth_id'], ['source_of_truth.id'], ),
        sa.PrimaryKeyConstraint('source_of_truth_id', 'document_id')
    )

    op.create_table(
        'transmittal_document',
        sa.Column('transmittal_id', sa.String(length=20), nullable=False),
        sa.Column('document_id', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.doc_id'], ),
        sa.ForeignKeyConstraint(['transmittal_id'], ['transmittal.tx_id'], ),
        sa.PrimaryKeyConstraint('transmittal_id', 'document_id')
    )

    op.create_table(
        'document_contributor',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.doc_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'document_id')
    )


def downgrade():
    op.drop_table('document_contributor')
    op.drop_table('transmittal_document')
    op.drop_table('document_source_of_truth')
    op.drop_index(op.f('ix_activity_log_user_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_timestamp'), table_name='activity_log')
    op.drop_table('activity_log')
    op.drop_table('transmittal')
    op.drop_index(op.f('ix_source_of_truth_master_document_id'), table_name='source_of_truth')
    op.drop_table('source_of_truth')
    op.drop_index(op.f('ix_revision_uploaded_by_user_id'), table_name='revision')
    op.drop_index(op.f('ix_revision_document_id'), table_name='revision')
    op.drop_table('revision')
    op.drop_table('document')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_table('user')
