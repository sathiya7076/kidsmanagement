from datetime import datetime
from models import db

class LearningResource(db.Model):
    __tablename__ = 'learning_resources'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(30), nullable=False) # 'rhyme', 'story', 'activity', 'game'
    age_group = db.Column(db.String(30), nullable=False) # 'infant', 'toddler', 'preschool', 'all'
    category = db.Column(db.String(50), nullable=True, default='General')
    description = db.Column(db.Text, nullable=True)
    content_url_or_text = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='bi-book')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def type_badge_class(self):
        badges = {
            'rhyme': 'bg-pink text-white',
            'story': 'bg-primary text-white',
            'activity': 'bg-success text-white',
            'game': 'bg-warning text-dark'
        }
        return badges.get(self.type, 'bg-info text-white')

    @property
    def age_group_display(self):
        labels = {
            'infant': 'Infant (0-1 yr)',
            'toddler': 'Toddler (1-3 yrs)',
            'preschool': 'Preschool (3-5 yrs)',
            'all': 'All Ages'
        }
        return labels.get(self.age_group, self.age_group.title())

    def __repr__(self):
        return f"<LearningResource {self.title} ({self.type})>"
