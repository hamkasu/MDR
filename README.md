# Document Management System (DMS)

A comprehensive web-based document management system for construction/engineering projects, built with Flask and PostgreSQL.

## Features

- **Master Document Register**: Central registry of all project documents with version control
- **Revision History**: Complete audit trail of document versions with download capability
- **Source of Truth Tracking**: Track facts that appear across multiple documents and keep them synchronized
- **Transmittal Log**: Record and track document transmissions to external parties
- **Role-Based Access Control**: Three user roles (admin, consultant_full, consultant_limited) with appropriate permissions
- **Activity Logging**: Audit trail of all user actions
- **Bootstrap 5 UI**: Clean, responsive web interface

## Tech Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Flask-Migrate (Alembic)
- **Frontend**: Jinja2 templates with Bootstrap 5
- **File Storage**: Local disk (configurable for S3 migration)
- **Deployment**: Railway
- **Authentication**: Flask-Login with password hashing

## Local Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip

### Installation Steps

1. **Clone the repository** (if applicable) or navigate to the project directory:
```bash
cd /path/to/mdr
```

2. **Create and activate a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create a PostgreSQL database** (if using local PostgreSQL):
```bash
createdb dms_dev
```

5. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and set:
```
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost:5432/dms_dev
SECRET_KEY=your-secret-key-change-this
```

6. **Initialize the database**:
```bash
flask db upgrade
```

7. **Seed the database with sample data and create admin user**:
```bash
flask seed-db
```

The command will output the admin user credentials. **Save the password securely!**

8. **Run the development server**:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Admin Login

**Username**: `admin`  
**Password**: (printed during `flask seed-db`)

## User Roles

### Admin
- Full access to all documents
- User management capabilities
- Source of Truth and Transmittal Log management

### Consultant Full
- View all documents
- Upload revisions to any document
- Cannot delete documents or manage users
- Can manage Source of Truth and Transmittal logs

### Consultant Limited
- View and upload to only assigned documents
- Cannot see full Master Register
- Cannot manage Source of Truth or Transmittal logs

## Database Schema

### Core Tables

1. **Document**: Master register of all project documents
   - doc_id, name, format, status, distribution, description, owner_party
   - Relationships: revisions, source_of_truth_entries, transmittals

2. **Revision**: Version history for each document
   - document_id (FK), revision_number, revision_date, file_path
   - original_filename, summary_of_changes, trigger, uploaded_by_user_id

3. **SourceOfTruth**: Tracked facts with cross-document references
   - fact_name, master_document_id (FK), sync_rule, status
   - Many-to-many: also_appears_in (documents)

4. **Transmittal**: Document distribution log
   - tx_id, date_sent, recipient_party, method, purpose
   - acknowledged, notes
   - Many-to-many: documents

5. **User**: User accounts with roles
   - username, email, password_hash, role (admin/consultant_full/consultant_limited)
   - Many-to-many: assigned_documents (for consultant_limited)

6. **ActivityLog**: Audit trail
   - user_id (FK), action, target_table, target_id, details, timestamp

## File Storage

Files are stored in `./uploads/<doc_id>/` with naming pattern: `<revision_number>_<original_filename>`

To migrate to S3-compatible storage later, modify the storage logic in `utils.py` (specifically `save_uploaded_file()` and `get_upload_path()` functions).

## Deployment to Railway

### Prerequisites

- Railway account (railway.app)
- Git repository (forked or created)

### Deployment Steps

1. **Push code to a Git repository** (GitHub, GitLab, etc.):
```bash
git add .
git commit -m "Initial DMS commit"
git push origin main
```

2. **Create a Railway project**:
   - Go to https://railway.app
   - Click "New Project"
   - Choose "Deploy from GitHub" and select your repository

3. **Add a PostgreSQL plugin**:
   - In the Railway dashboard, click "Add" on your project
   - Select "PostgreSQL"
   - Railway will automatically inject `DATABASE_URL` environment variable

4. **Set required environment variables**:
   - `SECRET_KEY`: Generate a random secret key
   - `FLASK_ENV`: Set to `production`
   - `UPLOAD_FOLDER`: Set to `/uploads` or configure for cloud storage

5. **Deploy**:
   - Railway will automatically detect the `Procfile` and `requirements.txt`
   - The `release` command will run `flask db upgrade` automatically

6. **Access the deployed application**:
   - Your URL will be available in the Railway dashboard
   - Log in with the admin credentials created during seeding

## Important Notes

### Permanent File Storage on Railway

Railway's filesystem is ephemeral (resets on redeploy). For permanent file storage:

**Option 1**: Use Railway's Volume feature
- Attach a volume to store uploads persistently
- Configure `UPLOAD_FOLDER` to point to the volume mount

**Option 2**: Use Cloudflare R2 or AWS S3
- Set `STORAGE_TYPE=s3` in environment variables
- Modify `save_uploaded_file()` in `utils.py` to use S3 SDK
- Provides better scalability and performance

### Database Migrations

Migrations are run automatically during deployment via the `release` command in the Procfile. New migrations are created with:

```bash
flask db migrate -m "Description of change"
flask db upgrade  # Test locally before deploying
```

### Security

- Change the `SECRET_KEY` in production
- Use strong passwords for all users
- Configure HTTPS (Railway provides this by default)
- Consider adding rate limiting for login attempts

## CLI Commands

### Create/reset admin user
```bash
flask seed-admin
```

### Seed sample data
```bash
flask seed-db
```

### Initialize database schema
```bash
flask init-db
```

### Create a new migration after model changes
```bash
flask db migrate -m "Description"
flask db upgrade
```

## Troubleshooting

### Database connection error
- Verify PostgreSQL is running
- Check `DATABASE_URL` format in `.env`
- Ensure database exists: `createdb dms_dev`

### Missing `flask` command
- Verify virtual environment is activated
- Reinstall with `pip install -r requirements.txt`

### File upload fails
- Check `UPLOAD_FOLDER` directory permissions
- Verify directory exists: `mkdir -p uploads`
- Ensure sufficient disk space

### Railway deployment fails
- Check Railway logs: `railway logs`
- Verify `Procfile` and `requirements.txt` are in root directory
- Ensure `SECRET_KEY` environment variable is set

## Follow-up Features

The prompt included guidance for future enhancements:

- **Email Notifications**: Add Flask-Mail for revision upload alerts
- **Excel Import/Export**: Add openpyxl for Excel file handling
- **Cloud Storage**: Migrate file uploads to S3/R2
- **Advanced Reporting**: Build custom reports and dashboards

## Support

For issues or questions, check:
1. Application logs: `flask run` with debug output
2. Railway logs: Dashboard → Project → Logs
3. Database migrations: `flask db current` to check applied migrations

---

**Last Updated**: 2025-06-29  
**Version**: 1.0  
**Status**: Production Ready
