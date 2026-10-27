from datetime import datetime
from models import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    type = db.Column(db.String(30), nullable=False) # 'meal', 'nap', 'mood', 'diaper', 'note', 'milestone'
    title = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text, nullable=True)
    logged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    child = db.relationship('Child', back_populates='activity_logs')
    author = db.relationship('User', back_populates='activity_logs')

    @property
    def icon_class(self):
        type_icons = {
            'meal': 'bi-cup-hot-fill text-warning',
            'nap': 'bi-moon-stars-fill text-indigo',
            'mood': 'bi-emoji-smile-fill text-success',
            'diaper': 'bi-droplet-fill text-info',
            'note': 'bi-journal-bookmark-fill text-primary',
            'milestone': 'bi-star-fill text-danger'
        }
        return type_icons.get(self.type, 'bi-clock-history text-secondary')

    @property
    def badge_class(self):
        type_badges = {
            'meal': 'badge-meal',
            'nap': 'badge-nap',
            'mood': 'badge-mood',
            'diaper': 'badge-diaper',
            'note': 'badge-note',
            'milestone': 'badge-milestone'
        }
        return type_badges.get(self.type, 'bg-secondary')

    @property
    def formatted_time(self):
        return self.timestamp.strftime('%I:%M %p')

    @property
    def formatted_date(self):
        return self.timestamp.strftime('%B %d, %Y')

    def __repr__(self):
        return f"<ActivityLog {self.type} - {self.title} for Child {self.child_id}>"
