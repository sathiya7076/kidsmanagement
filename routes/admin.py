from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from models import db, User, Child, ActivityLog, Attendance, Complaint, LearningResource, Notification
from routes.utils import role_required
from notifications import send_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
@role_required('admin')
def admin_access_check():
    pass

@admin_bp.route('/dashboard')
def dashboard():
    today = date.today()

    # Core stats
    total_children = Child.query.count()
    active_caregivers = User.query.filter(User.role.in_(['caregiver', 'caretaker']), User.is_approved == True).count()
    pending_caregivers = User.query.filter(User.role.in_(['caregiver', 'caretaker']), User.is_approved == False).count()
    total_parents = User.query.filter_by(role='parent').count()
    open_complaints = Complaint.query.filter_by(status='open').count()

    # Today's attendance stats
    today_records = Attendance.query.filter_by(date=today).all()
    present_count = sum(1 for r in today_records if r.status in ('present', 'late'))
    attendance_pct = round((present_count / total_children * 100), 1) if total_children > 0 else 0.0

    # Recent activity logs (last 10)
    recent_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Recent complaints
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_children=total_children,
        active_caregivers=active_caregivers,
        pending_caregivers=pending_caregivers,
        total_parents=total_parents,
        open_complaints=open_complaints,
        attendance_pct=attendance_pct,
        present_count=present_count,
        recent_logs=recent_logs,
        recent_complaints=recent_complaints
    )

@admin_bp.route('/caregivers')
def caregivers():
    caregiver_list = User.query.filter(User.role.in_(['caregiver', 'caretaker'])).order_by(User.is_approved.asc(), User.created_at.desc()).all()
    return render_template('admin/caregivers.html', caregivers=caregiver_list)

@admin_bp.route('/approve/<int:user_id>', methods=['POST', 'GET'])
def approve_caregiver(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_caretaker:
        flash('Target user is not a caretaker.', 'warning')
        return redirect(url_for('admin.caregivers'))

    user.is_approved = True
    db.session.commit()

    # Notify caretaker
    send_notification(
        user_id=user.id,
        title="Account Approved! 🎉",
        message="Your caretaker account has been approved by the Director. You can now access your assigned children.",
        link=url_for('caregiver.dashboard')
    )

    flash(f"Caretaker {user.name} has been approved successfully.", 'success')
    return redirect(url_for('admin.caregivers'))

@admin_bp.route('/reject/<int:user_id>', methods=['POST', 'GET'])
def reject_caregiver(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_caretaker:
        flash('Target user is not a caretaker.', 'warning')
        return redirect(url_for('admin.caregivers'))

    user.is_approved = False
    db.session.commit()
    flash(f"Caretaker {user.name}'s approval status was revoked or denied.", 'info')
    return redirect(url_for('admin.caregivers'))

@admin_bp.route('/children')
def children():
    child_list = Child.query.order_by(Child.name.asc()).all()
    return render_template('admin/children.html', children=child_list)

@admin_bp.route('/child/new', methods=['GET', 'POST'])
def new_child():
    parents = User.query.filter_by(role='parent').order_by(User.name.asc()).all()
    caregivers = User.query.filter(User.role.in_(['caregiver', 'caretaker']), User.is_approved == True).order_by(User.name.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob_str = request.form.get('dob', '').strip()
        gender = request.form.get('gender', 'unspecified')
        parent_id = request.form.get('parent_id')
        caregiver_id = request.form.get('caregiver_id')
        allergies = request.form.get('allergies', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name or not dob_str or not parent_id:
            flash('Name, Date of Birth, and Parent selection are required.', 'danger')
            return render_template('admin/child_form.html', child=None, parents=parents, caregivers=caregivers)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format for Date of Birth.', 'danger')
            return render_template('admin/child_form.html', child=None, parents=parents, caregivers=caregivers)

        child = Child(
            name=name,
            dob=dob,
            gender=gender,
            parent_id=int(parent_id),
            caregiver_id=int(caregiver_id) if caregiver_id else None,
            allergies=allergies,
            notes=notes
        )
        db.session.add(child)
        db.session.commit()

        # Notify parent
        send_notification(
            user_id=child.parent_id,
            title="Child Profile Enrolled",
            message=f"{child.name} has been enrolled in the daycare system.",
            link=url_for('parent.dashboard')
        )

        flash(f"Child profile for {child.name} enrolled successfully.", 'success')
        return redirect(url_for('admin.children'))

    return render_template('admin/child_form.html', child=None, parents=parents, caregivers=caregivers)

@admin_bp.route('/child/<int:child_id>/edit', methods=['GET', 'POST'])
def edit_child(child_id):
    child = Child.query.get_or_404(child_id)
    parents = User.query.filter_by(role='parent').order_by(User.name.asc()).all()
    caregivers = User.query.filter(User.role.in_(['caregiver', 'caretaker']), User.is_approved == True).order_by(User.name.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob_str = request.form.get('dob', '').strip()
        gender = request.form.get('gender', 'unspecified')
        parent_id = request.form.get('parent_id')
        caregiver_id = request.form.get('caregiver_id')
        allergies = request.form.get('allergies', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name or not dob_str or not parent_id:
            flash('Name, Date of Birth, and Parent are required.', 'danger')
            return render_template('admin/child_form.html', child=child, parents=parents, caregivers=caregivers)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('admin/child_form.html', child=child, parents=parents, caregivers=caregivers)

        child.name = name
        child.dob = dob
        child.gender = gender
        child.parent_id = int(parent_id)
        child.caregiver_id = int(caregiver_id) if caregiver_id else None
        child.allergies = allergies
        child.notes = notes

        if not child.qr_code_path:
            child.generate_qr_code(current_app.config['QR_UPLOAD_FOLDER'])

        db.session.commit()
        flash(f"Child profile for {child.name} updated successfully.", 'success')
        return redirect(url_for('admin.children'))

    return render_template('admin/child_form.html', child=child, parents=parents, caregivers=caregivers)

@admin_bp.route('/complaints')
def complaints():
    status_filter = request.args.get('status', 'all')
    query = Complaint.query
    if status_filter in ('open', 'in_progress', 'resolved'):
        query = query.filter_by(status=status_filter)
    complaint_list = query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin/complaints.html', complaints=complaint_list, active_status=status_filter)

@admin_bp.route('/complaint/<int:complaint_id>/respond', methods=['POST'])
def respond_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    response_text = request.form.get('admin_response', '').strip()
    new_status = request.form.get('status', 'resolved')

    if not response_text:
        flash('Response text cannot be empty.', 'danger')
        return redirect(url_for('admin.complaints'))

    complaint.admin_response = response_text
    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()
    db.session.commit()

    # Notify parent
    send_notification(
        user_id=complaint.user_id,
        title="Update on your Inquiry/Feedback",
        message=f"Admin responded to '{complaint.subject}': {response_text[:80]}...",
        link=url_for('parent.complaints')
    )

    flash('Response recorded and status updated.', 'success')
    return redirect(url_for('admin.complaints'))

@admin_bp.route('/learning')
def learning():
    resources = LearningResource.query.order_by(LearningResource.created_at.desc()).all()
    return render_template('admin/learning_manage.html', resources=resources)

@admin_bp.route('/learning/new', methods=['GET', 'POST'])
def new_learning_resource():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        rtype = request.form.get('type', 'rhyme').strip()
        age_group = request.form.get('age_group', 'all').strip()
        category = request.form.get('category', 'General').strip()
        description = request.form.get('description', '').strip()
        content = request.form.get('content', '').strip()
        icon = request.form.get('icon', 'bi-book').strip()

        if not title or not content:
            flash('Title and Content are required.', 'danger')
            return render_template('admin/learning_form.html', resource=None)

        resource = LearningResource(
            title=title,
            type=rtype,
            age_group=age_group,
            category=category,
            description=description,
            content_url_or_text=content,
            icon=icon
        )
        db.session.add(resource)
        db.session.commit()

        flash(f"Learning resource '{title}' added.", 'success')
        return redirect(url_for('admin.learning'))

    return render_template('admin/learning_form.html', resource=None)

@admin_bp.route('/learning/<int:res_id>/edit', methods=['GET', 'POST'])
def edit_learning_resource(res_id):
    resource = LearningResource.query.get_or_404(res_id)

    if request.method == 'POST':
        resource.title = request.form.get('title', '').strip()
        resource.type = request.form.get('type', 'rhyme').strip()
        resource.age_group = request.form.get('age_group', 'all').strip()
        resource.category = request.form.get('category', 'General').strip()
        resource.description = request.form.get('description', '').strip()
        resource.content_url_or_text = request.form.get('content', '').strip()
        resource.icon = request.form.get('icon', 'bi-book').strip()

        if not resource.title or not resource.content_url_or_text:
            flash('Title and Content are required.', 'danger')
            return render_template('admin/learning_form.html', resource=resource)

        db.session.commit()
        flash(f"Resource '{resource.title}' updated successfully.", 'success')
        return redirect(url_for('admin.learning'))

    return render_template('admin/learning_form.html', resource=resource)

@admin_bp.route('/learning/<int:res_id>/delete', methods=['POST'])
def delete_learning_resource(res_id):
    resource = LearningResource.query.get_or_404(res_id)
    title = resource.title
    db.session.delete(resource)
    db.session.commit()
    flash(f"Resource '{title}' deleted.", 'info')
    return redirect(url_for('admin.learning'))
