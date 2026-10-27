from datetime import datetime
from models import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_urgent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    @property
    def formatted_time(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'link': self.link or '#',
            'is_read': self.is_read,
            'is_urgent': self.is_urgent,
            'created_at': self.formatted_time
        }

    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id}: {self.title}>"
