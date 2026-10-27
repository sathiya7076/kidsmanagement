import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room

from config import Config
from models import db, User, Child, Message, Notification
import notifications
from routes import (
    auth_bp,
    admin_bp,
    caregiver_bp,
    parent_bp,
    messages_bp,
    learning_bp,
    api_bp
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directories exist
    os.makedirs(app.config['PHOTO_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # SocketIO initialization
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
    )
    notifications.set_socketio(socketio)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(api_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        unread_notifs_count = 0
        if current_user.is_authenticated:
            unread_notifs_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()

        return {
            'now': datetime.utcnow(),
            'today': date.today(),
            'timedelta': timedelta,
            'unread_notifs_count': unread_notifs_count,
            'daycare_name': app.config.get('DAYCARE_NAME', 'Virtual Daycare Platform'),
            'daycare_phone': app.config.get('DAYCARE_PHONE', '+1 (555) 234-5678'),
            'daycare_email': app.config.get('DAYCARE_EMAIL', 'info@littlelearnersdaycare.com')
        }

    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_caretaker:
                if not current_user.is_approved:
                    return redirect(url_for('auth.pending_approval'))
                return redirect(url_for('caregiver.dashboard'))
            elif current_user.is_parent:
                return redirect(url_for('parent.dashboard'))
        return render_template('landing.html')

    # College Presentation Route
    @app.route('/presentation')
    def presentation():
        return render_template('presentation.html')

    @app.route('/Virtual_Daycare_College_Presentation.pptx')
    def download_presentation_pptx():
        return send_from_directory(app.root_path, 'Virtual_Daycare_College_Presentation.pptx', as_attachment=True)


    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # SocketIO Event Handlers
    @socketio.on('join_user_notifications')
    def handle_user_notifications(data):
        if current_user.is_authenticated:
            user_room = f"user_{current_user.id}"
            join_room(user_room)
            emit('connected_status', {'status': 'connected', 'room': user_room})

    @socketio.on('join_child_chat')
    def handle_join_chat(data):
        child_id = data.get('child_id')
        if child_id:
            room = f"child_{child_id}"
            join_room(room)
            emit('chat_joined', {'room': room})

    @socketio.on('send_chat_message')
    def handle_chat_message(data):
        if not current_user.is_authenticated:
            return

        child_id = data.get('child_id')
        content = data.get('content', '').strip()
        is_alert = bool(data.get('is_alert', False))
        severity = data.get('severity', 'info')

        if not child_id or not content:
            return

        child = Child.query.get(child_id)
        if not child:
            return

        # Determine receiver
        if current_user.is_parent:
            receiver_id = child.caregiver_id
        elif current_user.is_caregiver:
            receiver_id = child.parent_id
        else:
            receiver_id = child.parent_id

        if not receiver_id:
            return

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

        # Broadcast to child room
        emit('new_chat_message', msg.to_dict(), room=f"child_{child.id}")

        # Send in-app notification to receiver
        notifications.send_notification(
            user_id=receiver_id,
            title=f"New Message from {current_user.name} ({child.name})",
            message=content[:80],
            link=url_for('messages.thread', child_id=child.id),
            is_urgent=is_alert
        )

    return app, socketio

app, socketio = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("\n🚀 Virtual Daycare Platform starting on http://0.0.0.0:5000\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
