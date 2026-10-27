import re
from datetime import date, datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Notification, Child, Attendance
from notifications import notify_child_parents

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/notifications/unread')
@login_required
def get_unread_notifications():
    unread_notifs = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()

    total_unread = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({
        'count': total_unread,
        'notifications': [n.to_dict() for n in unread_notifs]
    })

@api_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Notification not found'}), 404

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/qr-scan', methods=['POST'])
@login_required
def scan_qr_code():
    """
    Caregiver / Admin QR scan processor.
    Accepts payload: "DAYCARE_CHECKIN:CHILD_ID=<id>" or numeric child ID.
    Automatically checks in or checks out the child based on today's state!
    """
    if not (current_user.is_caregiver or current_user.is_admin):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    qr_data = data.get('qr_data', '').strip()

    if not qr_data:
        return jsonify({'success': False, 'error': 'No QR code data provided'}), 400

    # Extract child id from string like DAYCARE_CHECKIN:CHILD_ID=3 or just "3"
    child_id = None
    match = re.search(r'CHILD_ID=(\d+)', qr_data)
    if match:
        child_id = int(match.group(1))
    elif qr_data.isdigit():
        child_id = int(qr_data)

    if not child_id:
        return jsonify({'success': False, 'error': 'Invalid QR code format for daycare child'}), 400

    child = db.session.get(Child, child_id)
    if not child:
        return jsonify({'success': False, 'error': f'Child with ID {child_id} not found'}), 404

    # Caregiver access check
    if current_user.is_caregiver and child.caregiver_id != current_user.id:
        return jsonify({
            'success': False,
            'error': f'Child {child.name} is assigned to a different caregiver.'
        }), 403

    today = date.today()
    now = datetime.now()
    record = Attendance.query.filter_by(child_id=child.id, date=today).first()

    if not record:
        # Check-in
        record = Attendance(
            child_id=child.id,
            date=today,
            check_in_time=now,
            status='present',
            marked_by=current_user.id,
            notes='Scanned via QR Code'
        )
        db.session.add(record)
        db.session.commit()

        notify_child_parents(
            child=child,
            title=f"{child.name} Checked In (QR Scan)",
            message=f"{child.name} was checked in via QR scanner at {now.strftime('%I:%M %p')}."
        )

        return jsonify({
            'success': True,
            'action': 'check_in',
            'child_id': child.id,
            'child_name': child.name,
            'time': now.strftime('%I:%M %p'),
            'message': f"✅ {child.name} checked in successfully at {now.strftime('%I:%M %p')}!"
        })

    elif record.check_in_time and not record.check_out_time:
        # Check-out
        record.check_out_time = now
        record.marked_by = current_user.id
        db.session.commit()

        notify_child_parents(
            child=child,
            title=f"{child.name} Checked Out (QR Scan)",
            message=f"{child.name} was checked out via QR scanner at {now.strftime('%I:%M %p')}."
        )

        return jsonify({
            'success': True,
            'action': 'check_out',
            'child_id': child.id,
            'child_name': child.name,
            'time': now.strftime('%I:%M %p'),
            'message': f"👋 {child.name} checked out successfully at {now.strftime('%I:%M %p')}!"
        })

    else:
        # Already checked in and checked out
        return jsonify({
            'success': True,
            'action': 'already_completed',
            'child_id': child.id,
            'child_name': child.name,
            'message': f"ℹ️ {child.name} has already completed attendance today (In: {record.formatted_check_in}, Out: {record.formatted_check_out})."
        })
