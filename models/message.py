from datetime import datetime
from models import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_alert = db.Column(db.Boolean, default=False)
    alert_severity = db.Column(db.String(20), default='info') # 'info', 'warning', 'critical'
    is_read = db.Column(db.Boolean, default=False)

    # Relationships
    child = db.relationship('Child', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')

    @property
    def formatted_time(self):
        return self.timestamp.strftime('%I:%M %p')

    @property
    def formatted_date(self):
        return self.timestamp.strftime('%b %d, %Y')

    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.name if self.sender else 'Staff',
            'sender_role': self.sender.role if self.sender else 'caregiver',
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.name if self.receiver else '',
            'content': self.content,
            'timestamp': self.formatted_time,
            'date': self.formatted_date,
            'is_alert': self.is_alert,
            'alert_severity': self.alert_severity,
            'is_read': self.is_read
        }

    def __repr__(self):
        return f"<Message {self.id} Child {self.child_id} From {self.sender_id} To {self.receiver_id}>"
