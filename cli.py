import click
import secrets
import string
from datetime import date
from flask.cli import with_appcontext
from models import db, User, Document, Revision, Transmittal, SourceOfTruth
from utils import log_activity, generate_doc_id, generate_tx_id, save_uploaded_file
import os

def register_cli_commands(app):
    @app.cli.command('seed-admin')
    @with_appcontext
    def seed_admin():
        existing = User.query.filter_by(role='admin').first()
        if existing:
            click.echo('Admin user already exists. Use --force to override.')
            return

        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        admin = User(
            username='admin',
            email='admin@calmic.local',
            role='admin'
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        click.echo('=' * 60)
        click.echo('ADMIN USER CREATED')
        click.echo('=' * 60)
        click.echo(f'Username: admin')
        click.echo(f'Email: admin@calmic.local')
        click.echo(f'Password: {password}')
        click.echo('=' * 60)
        click.echo('IMPORTANT: Save this password securely. It will not be shown again.')
        click.echo('=' * 60)

    @app.cli.command('seed-db')
    @with_appcontext
    def seed_db():
        click.echo('Seeding database with sample data...')

        if User.query.filter_by(username='admin').first() is None:
            click.echo('Creating admin user...')
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            admin = User(
                username='admin',
                email='admin@calmic.local',
                role='admin'
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.flush()

            click.echo(f'Admin password: {password}')
        else:
            admin = User.query.filter_by(username='admin').first()

        if User.query.filter_by(username='architect').first() is None:
            click.echo('Creating consultant_full user (architect firm)...')
            arch = User(
                username='architect',
                email='arch@firm.local',
                role='consultant_full'
            )
            arch.set_password('architect123')
            db.session.add(arch)
            db.session.flush()

        if User.query.filter_by(username='structural_eng').first() is None:
            click.echo('Creating consultant_limited user (structural engineer)...')
            struct = User(
                username='structural_eng',
                email='struct@firm.local',
                role='consultant_limited'
            )
            struct.set_password('structural123')
            db.session.add(struct)
            db.session.flush()

        db.session.commit()

        if Document.query.first() is None:
            click.echo('Creating sample documents...')

            doc1 = Document(
                doc_id='DOC-001',
                name='Site Layout Plan',
                format='.pdf',
                status='Active',
                distribution='External',
                description='Master site layout showing all structures and utilities',
                owner_party='Calmic'
            )
            db.session.add(doc1)

            doc2 = Document(
                doc_id='DOC-002',
                name='Structural Design Report',
                format='.docx',
                status='Active — Pending Signature',
                distribution='External',
                description='Detailed structural analysis and design calculations',
                owner_party='AASB'
            )
            db.session.add(doc2)

            doc3 = Document(
                doc_id='DOC-003',
                name='Environmental Impact Assessment',
                format='.pdf',
                status='Draft — Pending Review',
                distribution='Internal',
                description='EIA for the project site',
                owner_party='EIA Consultants'
            )
            db.session.add(doc3)

            db.session.flush()

            click.echo('Creating sample revisions...')

            rev1 = Revision(
                document_id='DOC-001',
                revision_number='Rev 1',
                revision_date=date(2025, 1, 15),
                file_path=os.path.join('uploads/DOC-001', 'Rev1_SiteLayoutPlan.pdf'),
                original_filename='SiteLayoutPlan.pdf',
                summary_of_changes='Initial version',
                trigger='Project initiation',
                uploaded_by_user_id=admin.id
            )
            db.session.add(rev1)

            rev2 = Revision(
                document_id='DOC-001',
                revision_number='Rev 2',
                revision_date=date(2025, 2, 20),
                file_path=os.path.join('uploads/DOC-001', 'Rev2_SiteLayoutPlan.pdf'),
                original_filename='SiteLayoutPlan.pdf',
                summary_of_changes='Updated with utility routes',
                trigger='Client feedback',
                uploaded_by_user_id=admin.id
            )
            db.session.add(rev2)

            rev3 = Revision(
                document_id='DOC-002',
                revision_number='Rev 1',
                revision_date=date(2025, 2, 1),
                file_path=os.path.join('uploads/DOC-002', 'Rev1_StructuralReport.docx'),
                original_filename='StructuralReport.docx',
                summary_of_changes='Initial structural analysis',
                trigger='Design phase completion',
                uploaded_by_user_id=admin.id
            )
            db.session.add(rev3)

            db.session.commit()

            click.echo('Creating sample Source of Truth entries...')

            sot = SourceOfTruth(
                fact_name='Site frontage dimension: 150m',
                master_document_id='DOC-001',
                sync_rule='Must be consistent across all design documents and EIA',
                status='Resolved'
            )
            doc2.related_documents.append(sot)
            db.session.add(sot)
            db.session.commit()

            click.echo('Creating sample transmittal...')

            tx = Transmittal(
                tx_id='TX-001',
                date_sent=date(2025, 3, 1),
                revision_sent='Rev 1',
                recipient_party='Ministry of Environment',
                method='Email',
                purpose='Regulatory submission',
                acknowledged='Pending',
                notes='Initial EIA submission for review'
            )
            db.session.add(tx)
            db.session.commit()

        click.echo('Database seeded successfully!')

    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        click.echo('Creating database schema...')
        db.create_all()
        click.echo('Schema created successfully!')
        click.echo('Now run: flask seed-admin')
