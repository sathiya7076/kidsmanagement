from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Child, Message, User
from routes.utils import get_authorized_child
from notifications import send_notification

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages')
@login_required
def message_threads():
    """Show list of accessible chat threads for current user"""
    if current_user.is_admin:
        children = Child.query.order_by(Child.name.asc()).all()
    elif current_user.is_caregiver:
        children = Child.query.filter_by(caregiver_id=current_user.id).order_by(Child.name.asc()).all()
    elif current_user.is_parent:
        children = Child.query.filter_by(parent_id=current_user.id).order_by(Child.name.asc()).all()
    else:
        children = []

    # Gather thread info for each child
    threads = []
    for child in children:
        latest_msg = Message.query.filter_by(child_id=child.id).order_by(Message.timestamp.desc()).first()
        unread_count = Message.query.filter_by(
            child_id=child.id,
            receiver_id=current_user.id,
            is_read=False
        ).count()
        threads.append({
            'child': child,
            'latest_message': latest_msg,
            'unread_count': unread_count
        })

    return render_template('messages/list.html', threads=threads)

@messages_bp.route('/messages/<int:child_id>', methods=['GET', 'POST'])
@login_required
def thread(child_id):
    child = get_authorized_child(child_id)

    # Determine recipient
    if current_user.is_parent:
        receiver_id = child.caregiver_id
        other_party_name = child.caregiver.name if child.caregiver else "Daycare Staff"
    elif current_user.is_caregiver:
        receiver_id = child.parent_id
        other_party_name = child.parent.name if child.parent else "Parent"
    else: # admin
        receiver_id = child.parent_id
        other_party_name = f"Parent ({child.parent.name})" if child.parent else "Parent"

    # Mark unread incoming messages as read
    Message.query.filter_by(
        child_id=child.id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        is_alert = bool(request.form.get('is_alert'))
        severity = request.form.get('severity', 'info')

        if not content:
            flash('Message content cannot be empty.', 'danger')
            return redirect(url_for('messages.thread', child_id=child.id))

        if not receiver_id:
            flash('No assigned caregiver or parent found for this child to receive messages.', 'warning')
            return redirect(url_for('messages.thread', child_id=child.id))

        message = Message(
            child_id=child.id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            is_alert=is_alert,
            alert_severity=severity if is_alert else 'info',
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()

        # Send notification to receiver
        send_notification(
            user_id=receiver_id,
            title=f"New message regarding {child.name}",
            message=f"{current_user.name}: {content[:80]}",
            link=url_for('messages.thread', child_id=child.id),
            is_urgent=is_alert
        )

        flash('Message sent.', 'success')
        return redirect(url_for('messages.thread', child_id=child.id))

    messages = Message.query.filter_by(child_id=child.id).order_by(Message.timestamp.asc()).all()

    return render_template(
        'messages/thread.html',
        child=child,
        messages=messages,
        other_party_name=other_party_name,
        receiver_id=receiver_id
    )

@messages_bp.route('/api/messages/<int:child_id>', methods=['GET'])
@login_required
def api_get_messages(child_id):
    """JSON endpoint for chat polling / refresh"""
    child = get_authorized_child(child_id)
    messages = Message.query.filter_by(child_id=child.id).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read
    Message.query.filter_by(
        child_id=child.id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return jsonify({
        'success': True,
        'messages': [m.to_dict() for m in messages],
        'current_user_id': current_user.id
    })

@messages_bp.route('/api/messages/<int:child_id>/send', methods=['POST'])
@login_required
def api_send_message(child_id):
    """JSON endpoint for AJAX instant sending"""
    child = get_authorized_child(child_id)
    data = request.get_json() or request.form

    content = data.get('content', '').strip()
    is_alert = bool(data.get('is_alert', False))
    severity = data.get('alert_severity', 'info')

    if not content:
        return jsonify({'success': False, 'error': 'Message content cannot be empty'}), 400

    if current_user.is_parent:
        receiver_id = child.caregiver_id
    elif current_user.is_caregiver:
        receiver_id = child.parent_id
    else:
        receiver_id = child.parent_id

    if not receiver_id:
        return jsonify({'success': False, 'error': 'Recipient not assigned'}), 400

    msg = Message(
        child_id=child.id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        is_alert=is_alert,
        alert_severity=severity if is_alert else 'info',
        timestamp=datetime.utcnow()
    )
    db.session.add(msg)
    db.session.commit()

    # In-app notification
    send_notification(
        user_id=receiver_id,
        title=f"New message from {current_user.name} ({child.name})",
        message=content[:80],
        link=url_for('messages.thread', child_id=child.id),
        is_urgent=is_alert
    )

    return jsonify({
        'success': True,
        'message': msg.to_dict()
    })
