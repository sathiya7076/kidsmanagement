from datetime import date, datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Child, ActivityLog, Photo, Attendance, Complaint, User
from routes.utils import role_required, get_authorized_child
from notifications import notify_all_admins

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

@parent_bp.before_request
@login_required
@role_required('parent', 'admin')
def parent_access_check():
    pass

@parent_bp.route('/dashboard')
def dashboard():
    if current_user.is_admin:
        children = Child.query.order_by(Child.name.asc()).all()
    else:
        children = Child.query.filter_by(parent_id=current_user.id).order_by(Child.name.asc()).all()

    today = date.today()
    today_start = datetime.combine(today, time.min)

    # Gather summaries for each child
    child_data = []
    for child in children:
        logs_today = ActivityLog.query.filter(
            ActivityLog.child_id == child.id,
            ActivityLog.timestamp >= today_start
        ).order_by(ActivityLog.timestamp.desc()).all()

        latest_photo = Photo.query.filter_by(child_id=child.id).order_by(Photo.timestamp.desc()).first()
        active_alert = child.active_emergency_alert
        today_att = child.today_attendance

        child_data.append({
            'child': child,
            'today_logs': logs_today,
            'latest_photo': latest_photo,
            'active_alert': active_alert,
            'attendance': today_att,
            'logs_count': len(logs_today)
        })

    return render_template('parent/dashboard.html', child_data=child_data, today=today)

@parent_bp.route('/child/<int:child_id>/timeline')
def timeline(child_id):
    child = get_authorized_child(child_id)
    
    # Check date parameter
    date_str = request.args.get('date')
    selected_date = date.today()
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()

    start_datetime = datetime.combine(selected_date, time.min)
    end_datetime = datetime.combine(selected_date, time.max)

    # Fetch logs for selected date
    logs = ActivityLog.query.filter(
        ActivityLog.child_id == child.id,
        ActivityLog.timestamp >= start_datetime,
        ActivityLog.timestamp <= end_datetime
    ).order_by(ActivityLog.timestamp.asc()).all()

    # Photos for selected date
    photos = Photo.query.filter(
        Photo.child_id == child.id,
        Photo.timestamp >= start_datetime,
        Photo.timestamp <= end_datetime
    ).order_by(Photo.timestamp.asc()).all()

    # Attendance for selected date
    attendance = Attendance.query.filter_by(child_id=child.id, date=selected_date).first()

    return render_template(
        'parent/timeline.html',
        child=child,
        logs=logs,
        photos=photos,
        attendance=attendance,
        selected_date=selected_date,
        today=date.today()
    )

@parent_bp.route('/child/<int:child_id>/photos')
def photos(child_id):
    child = get_authorized_child(child_id)
    category_filter = request.args.get('category', 'all')
    
    query = Photo.query.filter_by(child_id=child.id)
    if category_filter and category_filter != 'all':
        query = query.filter_by(category=category_filter)

    photo_list = query.order_by(Photo.timestamp.desc()).all()
    categories = ['All', 'Activity', 'Outdoor', 'Art', 'Meal', 'Milestone', 'Nap']

    return render_template(
        'parent/photos.html',
        child=child,
        photos=photo_list,
        categories=categories,
        current_category=category_filter
    )

@parent_bp.route('/child/<int:child_id>/attendance')
def attendance(child_id):
    child = get_authorized_child(child_id)
    today = date.today()

    # Optional year/month filters
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    monthly_stats = child.get_monthly_attendance_stats(year=year, month=month)
    
    # Fetch recent attendance records (last 30 entries)
    records = Attendance.query.filter_by(child_id=child.id).order_by(Attendance.date.desc()).limit(30).all()

    return render_template(
        'parent/attendance.html',
        child=child,
        stats=monthly_stats,
        records=records,
        today=today
    )

@parent_bp.route('/child/<int:child_id>/profile')
def child_profile(child_id):
    child = get_authorized_child(child_id)
    return render_template('parent/child_profile.html', child=child)

@parent_bp.route('/complaints', methods=['GET', 'POST'])
def complaints():
    user_children = Child.query.filter_by(parent_id=current_user.id).all() if current_user.is_parent else []

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        child_id = request.form.get('child_id')

        if not subject or not message:
            flash('Subject and message are required.', 'danger')
            return redirect(url_for('parent.complaints'))

        complaint = Complaint(
            user_id=current_user.id,
            child_id=int(child_id) if child_id else None,
            subject=subject,
            message=message,
            status='open'
        )
        db.session.add(complaint)
        db.session.commit()

        # Notify admins
        notify_all_admins(
            title=f"New Parent Concern: {subject}",
            message=f"{current_user.name} submitted a feedback/concern: '{subject}'",
            link=url_for('admin.complaints')
        )

        flash('Your inquiry or feedback has been submitted directly to the Daycare Director.', 'success')
        return redirect(url_for('parent.complaints'))

    user_complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template('parent/complaints.html', complaints=user_complaints, children=user_children)
