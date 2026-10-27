from datetime import datetime
from models import db

class Photo(db.Model):
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default='Activity') # 'Art', 'Outdoor', 'Meal', 'Milestone', 'Nap', 'Group'
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    child = db.relationship('Child', back_populates='photos')
    uploader = db.relationship('User', back_populates='photos_uploaded')

    @property
    def formatted_time(self):
        return self.timestamp.strftime('%I:%M %p')

    @property
    def formatted_date(self):
        return self.timestamp.strftime('%B %d, %Y')

    def __repr__(self):
        return f"<Photo {self.id} for Child {self.child_id}>"
