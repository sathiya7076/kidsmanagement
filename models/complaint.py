from datetime import datetime
from models import db

class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open') # 'open', 'in_progress', 'resolved'
    admin_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='complaints')
    child = db.relationship('Child')

    @property
    def badge_class(self):
        badges = {
            'open': 'bg-danger',
            'in_progress': 'bg-warning text-dark',
            'resolved': 'bg-success'
        }
        return badges.get(self.status, 'bg-secondary')

    @property
    def formatted_date(self):
        return self.created_at.strftime('%b %d, %Y %I:%M %p')

    def __repr__(self):
        return f"<Complaint {self.id} by User {self.user_id}: {self.subject}>"
