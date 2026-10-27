from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.child import Child
from models.activity import ActivityLog
from models.photo import Photo
from models.attendance import Attendance
from models.message import Message
from models.learning import LearningResource
from models.complaint import Complaint
from models.notification import Notification

__all__ = [
    'db',
    'User',
    'Child',
    'ActivityLog',
    'Photo',
    'Attendance',
    'Message',
    'LearningResource',
    'Complaint',
    'Notification'
]
