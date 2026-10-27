import os
import uuid
from functools import wraps
from flask import abort, flash, redirect, url_for, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from models import Child

def role_required(*roles):
    """Decorator to enforce user roles ('admin', 'caregiver'/'caretaker', 'parent')"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            allowed_roles = set(roles)
            if 'caregiver' in allowed_roles:
                allowed_roles.add('caretaker')
            if 'caretaker' in allowed_roles:
                allowed_roles.add('caregiver')
            if current_user.role not in allowed_roles:
                abort(403)
            # If caretaker, check approval
            if current_user.is_caretaker and not current_user.is_approved:
                flash('Your caretaker account is pending administrator approval.', 'warning')
                return redirect(url_for('auth.pending_approval'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_authorized_child(child_id):
    """
    Fetches child and checks if current_user has access.
    Admin: always has access.
    Caretaker: only if assigned to child.
    Parent: only if parent of child.
    Returns Child or aborts with 403 or 404.
    """
    from models import db
    child = db.session.get(Child, child_id)
    if not child:
        abort(404)

    if current_user.is_admin:
        return child
    if current_user.is_caretaker:
        if child.caregiver_id != current_user.id:
            abort(403)
        return child
    if current_user.is_parent:
        if child.parent_id != current_user.id:
            abort(403)
        return child

    abort(403)

def allowed_file(filename):
    """Checks if uploaded file has an allowed image extension"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_photo(file):
    """
    Saves uploaded file securely with a unique filename in static/uploads/photos/
    Returns relative path (e.g., 'uploads/photos/...')
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    if not unique_filename.endswith(f".{ext}"):
        unique_filename = f"{unique_filename}.{ext}"

    upload_dir = current_app.config['PHOTO_UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    return f"uploads/photos/{unique_filename}"
