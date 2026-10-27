from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.caregiver import caregiver_bp
from routes.parent import parent_bp
from routes.messages import messages_bp
from routes.learning import learning_bp
from routes.api import api_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'caregiver_bp',
    'parent_bp',
    'messages_bp',
    'learning_bp',
    'api_bp'
]
