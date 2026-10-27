from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Child
from notifications import notify_all_admins

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if user.is_caretaker and not user.is_approved:
            login_user(user, remember=remember)
            flash('Your caretaker account is pending administrator approval. Please wait for an admin to verify your profile.', 'warning')
            return redirect(url_for('auth.pending_approval'))

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}!', 'success')
        
        # Check next redirect
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
            
        return redirect_user_by_role(user)

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'parent').strip().lower()
        phone = request.form.get('phone', '').strip()

        # Validation
        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if role not in ('parent', 'caregiver', 'caretaker'):
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Create user
        is_approved = True if role == 'parent' else False
        user = User(
            name=name,
            email=email,
            role=role,
            phone=phone,
            is_approved=is_approved
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role in ('caregiver', 'caretaker'):
            # Notify admins of new caretaker registration
            notify_all_admins(
                title="New Caretaker Registration",
                message=f"{user.name} ({user.email}) registered as a caretaker and is waiting for approval.",
                link=url_for('admin.caregivers')
            )
            flash('Registration successful! Your caretaker account is pending administrator approval before you can access children records.', 'info')
            login_user(user)
            return redirect(url_for('auth.pending_approval'))

        # If parent, check if they provided initial child info
        child_name = request.form.get('child_name', '').strip()
        child_dob_str = request.form.get('child_dob', '').strip()
        allergies = request.form.get('allergies', '').strip()
        notes = request.form.get('notes', '').strip()

        if child_name and child_dob_str:
            try:
                child_dob = datetime.strptime(child_dob_str, '%Y-%m-%d').date()
                child = Child(
                    name=child_name,
                    dob=child_dob,
                    allergies=allergies,
                    notes=notes,
                    parent_id=user.id
                )
                db.session.add(child)
                db.session.commit()

                # Generate QR code for child
                child.generate_qr_code(current_app.config['QR_UPLOAD_FOLDER'])
                db.session.commit()
            except ValueError:
                flash('Child date of birth was invalid, but parent account was created.', 'warning')

        login_user(user)
        flash(f'Account created successfully! Welcome to {current_app.config["DAYCARE_NAME"]}.', 'success')
        return redirect(url_for('parent.dashboard'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/pending-approval')
@login_required
def pending_approval():
    if current_user.role != 'caregiver' or current_user.is_approved:
        return redirect_user_by_role(current_user)
    return render_template('auth/pending_approval.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    reset_link = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            flash('Password reset link generated below (simulated email delivery).', 'success')
        else:
            flash('If that email exists in our system, a reset link has been generated.', 'info')

    return render_template('auth/reset_request.html', reset_link=reset_link)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('The password reset token is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.reset_request'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()

        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)

def redirect_user_by_role(user):
    """Helper to route user to proper dashboard based on role"""
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif user.is_caretaker:
        if not user.is_approved:
            return redirect(url_for('auth.pending_approval'))
        return redirect(url_for('caregiver.dashboard'))
    elif user.is_parent:
        return redirect(url_for('parent.dashboard'))
    return redirect(url_for('auth.login'))
