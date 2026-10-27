from datetime import date, datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Child, ActivityLog, Photo, Attendance, Message, User
from routes.utils import role_required, get_authorized_child, save_uploaded_photo
from notifications import notify_child_parents, send_notification

caregiver_bp = Blueprint('caregiver', __name__, url_prefix='/caregiver')

@caregiver_bp.before_request
@login_required
@role_required('caregiver', 'admin')
def caregiver_access_check():
    pass

@caregiver_bp.route('/dashboard')
def dashboard():
    if current_user.is_admin:
        assigned_children = Child.query.order_by(Child.name.asc()).all()
    else:
        assigned_children = Child.query.filter_by(caregiver_id=current_user.id).order_by(Child.name.asc()).all()

    today = date.today()
    return render_template('caregiver/dashboard.html', children=assigned_children, today=today)

@caregiver_bp.route('/child/<int:child_id>')
def child_detail(child_id):
    child = get_authorized_child(child_id)
    today = date.today()
    today_start = datetime.combine(today, time.min)
    
    today_logs = ActivityLog.query.filter(
        ActivityLog.child_id == child.id,
        ActivityLog.timestamp >= today_start
    ).order_by(ActivityLog.timestamp.desc()).all()

    recent_photos = Photo.query.filter_by(child_id=child.id).order_by(Photo.timestamp.desc()).limit(6).all()
    today_att = child.today_attendance

    return render_template(
        'caregiver/child_detail.html',
        child=child,
        today_logs=today_logs,
        recent_photos=recent_photos,
        today_att=today_att,
        today=today
    )

@caregiver_bp.route('/child/<int:child_id>/log', methods=['GET', 'POST'])
def log_activity(child_id):
    child = get_authorized_child(child_id)

    if request.method == 'POST':
        log_type = request.form.get('type', 'note').strip()
        custom_time_str = request.form.get('timestamp')
        
        # Build title & details based on activity type
        title = ""
        details_list = []

        if log_type == 'meal':
            meal_type = request.form.get('meal_type', 'Lunch')
            food_items = request.form.get('food_items', '').strip()
            amount = request.form.get('amount_eaten', 'All')
            title = f"{meal_type}: {food_items if food_items else 'Regular meal'}"
            details_list.append(f"Amount eaten: {amount}")
            if request.form.get('meal_notes'):
                details_list.append(f"Notes: {request.form.get('meal_notes').strip()}")

        elif log_type == 'nap':
            nap_start = request.form.get('nap_start', '')
            nap_end = request.form.get('nap_end', '')
            nap_quality = request.form.get('nap_quality', 'Peaceful')
            title = f"Nap ({nap_start} - {nap_end})" if nap_start and nap_end else "Rest Time / Nap"
            details_list.append(f"Quality: {nap_quality}")
            if request.form.get('nap_notes'):
                details_list.append(f"Notes: {request.form.get('nap_notes').strip()}")

        elif log_type == 'mood':
            mood_val = request.form.get('mood_val', 'Happy')
            title = f"Mood: {mood_val}"
            if request.form.get('mood_notes'):
                details_list.append(request.form.get('mood_notes').strip())

        elif log_type == 'diaper':
            diaper_type = request.form.get('diaper_type', 'Wet')
            title = f"Bathroom / Diaper: {diaper_type}"
            if request.form.get('diaper_notes'):
                details_list.append(request.form.get('diaper_notes').strip())

        elif log_type == 'milestone':
            title = request.form.get('milestone_title', 'Learning Milestone').strip()
            if request.form.get('milestone_details'):
                details_list.append(request.form.get('milestone_details').strip())

        else: # note
            title = request.form.get('note_title', 'Daily Note').strip() or 'Daily Note'
            if request.form.get('note_details'):
                details_list.append(request.form.get('note_details').strip())

        # Determine timestamp
        log_timestamp = datetime.utcnow()
        if custom_time_str:
            try:
                # Custom time format: YYYY-MM-DDTHH:MM
                log_timestamp = datetime.strptime(custom_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass

        activity = ActivityLog(
            child_id=child.id,
            type=log_type,
            title=title,
            details="\n".join(details_list),
            logged_by=current_user.id,
            timestamp=log_timestamp
        )
        db.session.add(activity)
        db.session.commit()

        # Send notification to parent
        notify_child_parents(
            child=child,
            title=f"New Activity for {child.name}",
            message=f"{title}",
            link=url_for('parent.timeline', child_id=child.id)
        )

        flash(f"Activity log '{title}' recorded successfully for {child.name}.", 'success')
        return redirect(url_for('caregiver.child_detail', child_id=child.id))

    return render_template('caregiver/log_activity.html', child=child)

@caregiver_bp.route('/child/<int:child_id>/photo', methods=['GET', 'POST'])
def upload_photo(child_id):
    child = get_authorized_child(child_id)

    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part in the request.', 'danger')
            return render_template('caregiver/upload_photo.html', child=child)

        file = request.files['photo']
        caption = request.form.get('caption', '').strip()
        category = request.form.get('category', 'Activity')

        if file.filename == '':
            flash('Please select an image to upload.', 'danger')
            return render_template('caregiver/upload_photo.html', child=child)

        saved_path = save_uploaded_photo(file)
        if not saved_path:
            flash('Invalid file format. Please upload PNG, JPG, JPEG, GIF, or WEBP under 5MB.', 'danger')
            return render_template('caregiver/upload_photo.html', child=child)

        photo = Photo(
            child_id=child.id,
            filepath=saved_path,
            caption=caption,
            category=category,
            uploaded_by=current_user.id,
            timestamp=datetime.utcnow()
        )
        db.session.add(photo)
        db.session.commit()

        # Notify parent
        notify_child_parents(
            child=child,
            title=f"New Photo of {child.name}! 📸",
            message=f"{caption if caption else f'Caregiver shared a new {category} photo.'}",
            link=url_for('parent.photos', child_id=child.id)
        )

        flash(f"Photo uploaded successfully for {child.name}.", 'success')
        return redirect(url_for('caregiver.child_detail', child_id=child.id))

    return render_template('caregiver/upload_photo.html', child=child)

@caregiver_bp.route('/child/<int:child_id>/attendance', methods=['GET', 'POST'])
def mark_child_attendance(child_id):
    child = get_authorized_child(child_id)
    today = date.today()
    record = Attendance.query.filter_by(child_id=child.id, date=today).first()

    if request.method == 'POST':
        action = request.form.get('action') # 'check_in', 'check_out', 'mark_absent', 'manual_update'
        status = request.form.get('status', 'present')
        notes = request.form.get('notes', '').strip()
        now = datetime.now()

        if not record:
            record = Attendance(
                child_id=child.id,
                date=today,
                marked_by=current_user.id,
                status=status,
                notes=notes
            )
            db.session.add(record)

        if action == 'check_in':
            record.status = 'present'
            record.check_in_time = now
            record.marked_by = current_user.id
            notify_child_parents(
                child=child,
                title=f"{child.name} Checked In",
                message=f"{child.name} arrived safely at daycare at {now.strftime('%I:%M %p')}.",
                link=url_for('parent.attendance', child_id=child.id)
            )
            flash(f"{child.name} checked in at {now.strftime('%I:%M %p')}.", 'success')

        elif action == 'check_out':
            record.check_out_time = now
            record.marked_by = current_user.id
            notify_child_parents(
                child=child,
                title=f"{child.name} Checked Out",
                message=f"{child.name} was picked up from daycare at {now.strftime('%I:%M %p')}.",
                link=url_for('parent.attendance', child_id=child.id)
            )
            flash(f"{child.name} checked out at {now.strftime('%I:%M %p')}.", 'info')

        elif action == 'mark_absent':
            record.status = 'absent'
            record.marked_by = current_user.id
            if notes:
                record.notes = notes
            flash(f"{child.name} marked as absent today.", 'warning')

        elif action == 'manual_update':
            record.status = status
            record.notes = notes
            check_in_str = request.form.get('check_in_time')
            check_out_str = request.form.get('check_out_time')
            if check_in_str:
                try:
                    record.check_in_time = datetime.strptime(f"{today} {check_in_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            if check_out_str:
                try:
                    record.check_out_time = datetime.strptime(f"{today} {check_out_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            record.marked_by = current_user.id
            flash('Attendance record updated.', 'success')

        db.session.commit()
        return redirect(url_for('caregiver.child_detail', child_id=child.id))

    return render_template('caregiver/attendance.html', child=child, record=record, today=today)

@caregiver_bp.route('/attendance')
def roster_attendance():
    """Daily roster attendance page for quick bulk check-in / check-out"""
    if current_user.is_admin:
        children = Child.query.order_by(Child.name.asc()).all()
    else:
        children = Child.query.filter_by(caregiver_id=current_user.id).order_by(Child.name.asc()).all()

    today = date.today()
    return render_template('caregiver/attendance_roster.html', children=children, today=today)

@caregiver_bp.route('/child/<int:child_id>/alert', methods=['GET', 'POST'])
def emergency_alert(child_id):
    child = get_authorized_child(child_id)

    if request.method == 'POST':
        alert_title = request.form.get('title', '').strip()
        alert_content = request.form.get('content', '').strip()
        severity = request.form.get('severity', 'warning') # 'info', 'warning', 'critical'

        if not alert_title or not alert_content:
            flash('Alert title and description are required.', 'danger')
            return render_template('caregiver/emergency_alert.html', child=child)

        full_message = f"🚨 [{alert_title.upper()}] - {alert_content}"
        
        # Create high-priority Message in chat
        message = Message(
            child_id=child.id,
            sender_id=current_user.id,
            receiver_id=child.parent_id,
            content=full_message,
            is_alert=True,
            alert_severity=severity,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()

        # Send URGENT notification to parent (triggers simulated SMS and email)
        notify_child_parents(
            child=child,
            title=f"EMERGENCY ALERT: {child.name} - {alert_title}",
            message=alert_content,
            link=url_for('parent.dashboard'),
            is_urgent=True
        )

        flash(f"High-priority Emergency Alert dispatched immediately to {child.name}'s parent.", 'danger')
        return redirect(url_for('caregiver.child_detail', child_id=child.id))

    return render_template('caregiver/emergency_alert.html', child=child)

@caregiver_bp.route('/qr-scanner')
def qr_scanner():
    """Redirect to daily attendance roster"""
    return redirect(url_for('caregiver.roster_attendance'))
