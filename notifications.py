import logging
from datetime import datetime
from models import db, Notification, User

logger = logging.getLogger('notifications')

# Global socketio reference that will be set in app.py
socketio_instance = None

def set_socketio(socketio):
    global socketio_instance
    socketio_instance = socketio

def send_notification(user_id, title, message, link=None, is_urgent=False, emit_socket=True):
    """
    Creates an in-app notification for user_id.
    Optionally emits a real-time event via SocketIO.
    If urgent, also triggers SMS/email simulation hooks.
    """
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            is_urgent=is_urgent,
            created_at=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        # Emit SocketIO real-time notification to user's room if connected
        if emit_socket and socketio_instance:
            try:
                socketio_instance.emit('new_notification', notif.to_dict(), room=f"user_{user_id}")
            except Exception as e:
                logger.warning(f"Failed to emit SocketIO notification: {e}")

        # If urgent, simulate external dispatch
        user = db.session.get(User, user_id)
        if user and is_urgent:
            if user.phone:
                send_sms(user.phone, f"URGENT ALERT - {title}: {message}")
            if user.email:
                send_email(user.email, f"URGENT: {title}", message)

        return notif
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating notification for user {user_id}: {e}")
        return None

def notify_child_parents(child, title, message, link=None, is_urgent=False):
    """Notify the parent of a specific child"""
    if child and child.parent_id:
        return send_notification(
            user_id=child.parent_id,
            title=title,
            message=message,
            link=link,
            is_urgent=is_urgent
        )
    return None

def notify_caregiver(child, title, message, link=None, is_urgent=False):
    """Notify the caretaker assigned to a child"""
    if child and child.caregiver_id:
        return send_notification(
            user_id=child.caregiver_id,
            title=title,
            message=message,
            link=link,
            is_urgent=is_urgent
        )
    return None

# Caretaker alias
notify_caretaker = notify_caregiver

def notify_all_admins(title, message, link=None, is_urgent=False):
    """Send notification to all admin users"""
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        send_notification(
            user_id=admin.id,
            title=title,
            message=message,
            link=link,
            is_urgent=is_urgent
        )

# External Service Hooks (Ready to be swapped for Twilio / SendGrid)
def send_sms(to_phone, message_text):
    """
    SMS delivery hook.
    In production, swap with Twilio Client:
    twilio_client.messages.create(body=message_text, from_=TWILIO_PHONE, to=to_phone)
    """
    logger.info(f"[SMS SERVICE DISPATCH] To: {to_phone} | Message: {message_text}")
    print(f"\n[📱 SMS SENT via Mock Twilio] -> To: {to_phone} | Content: {message_text}\n")
    return True

def send_email(to_email, subject, body_html):
    """
    Email delivery hook.
    In production, swap with SendGrid or Flask-Mail:
    sendgrid_client.send(Mail(from_email, to_email, subject, html_content=body_html))
    """
    logger.info(f"[EMAIL SERVICE DISPATCH] To: {to_email} | Subject: {subject}")
    print(f"\n[✉️ EMAIL SENT via Mock SendGrid] -> To: {to_email} | Subject: {subject}\n")
    return True
