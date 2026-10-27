from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='parent') # 'admin', 'caregiver', 'parent'
    phone = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True) # caregivers need admin approval
    
    # Password reset
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationships
    parent_children = db.relationship('Child', back_populates='parent', foreign_keys='Child.parent_id', lazy='dynamic')
    assigned_children = db.relationship('Child', back_populates='caregiver', foreign_keys='Child.caregiver_id', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='author', lazy='dynamic')
    photos_uploaded = db.relationship('Photo', back_populates='uploader', lazy='dynamic')
    sent_messages = db.relationship('Message', back_populates='sender', foreign_keys='Message.sender_id', lazy='dynamic')
    received_messages = db.relationship('Message', back_populates='receiver', foreign_keys='Message.receiver_id', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_caretaker(self):
        return self.role in ('caretaker', 'caregiver')

    @property
    def is_caregiver(self):
        return self.is_caretaker

    @property
    def is_parent(self):
        return self.role == 'parent'

    @property
    def display_role(self):
        if self.is_caretaker:
            return "Caretaker"
        return self.role.title()

    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token):
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f"<User {self.name} ({self.role}) - {self.email}>"
