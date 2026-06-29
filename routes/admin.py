from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Document
from utils import ROLE_CHOICES, log_activity
import secrets
import string

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role', 'consultant_limited')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_user'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.add_user'))

        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log_activity(current_user.id, 'CREATE_USER', 'user', user.id, f'Role: {role}')

        flash(f'User {username} created successfully. Password: {password}', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/add_user.html', roles=ROLE_CHOICES)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form.get('email')
        user.role = request.form.get('role')

        if user.role == 'consultant_limited':
            selected_doc_ids = request.form.getlist('assigned_documents')
            user.assigned_documents = Document.query.filter(Document.doc_id.in_(selected_doc_ids)).all()

        db.session.commit()

        log_activity(current_user.id, 'UPDATE_USER', 'user', user_id)

        flash(f'User {user.username} updated successfully.', 'success')
        return redirect(url_for('admin.users_list'))

    documents = Document.query.all()
    return render_template('admin/edit_user.html', user=user, documents=documents, roles=ROLE_CHOICES)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users_list'))

    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()

    log_activity(current_user.id, 'DELETE_USER', 'user', user_id, f'Username: {username}')

    flash(f'User {username} deleted successfully.', 'success')
    return redirect(url_for('admin.users_list'))
