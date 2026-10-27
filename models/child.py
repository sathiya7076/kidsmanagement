import os
from datetime import date, datetime
import calendar
import qrcode
from models import db

class Child(db.Model):
    __tablename__ = 'children'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=True, default='unspecified')
    allergies = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    caregiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parent = db.relationship('User', foreign_keys=[parent_id], back_populates='parent_children')
    caregiver = db.relationship('User', foreign_keys=[caregiver_id], back_populates='assigned_children')

    @property
    def caretaker(self):
        return self.caregiver

    @property
    def caretaker_id(self):
        return self.caregiver_id
    
    activity_logs = db.relationship(
        'ActivityLog', back_populates='child', cascade='all, delete-orphan',
        order_by='ActivityLog.timestamp.desc()', lazy='dynamic'
    )
    photos = db.relationship(
        'Photo', back_populates='child', cascade='all, delete-orphan',
        order_by='Photo.timestamp.desc()', lazy='dynamic'
    )
    attendance_records = db.relationship(
        'Attendance', back_populates='child', cascade='all, delete-orphan',
        order_by='Attendance.date.desc()', lazy='dynamic'
    )
    messages = db.relationship(
        'Message', back_populates='child', cascade='all, delete-orphan',
        order_by='Message.timestamp.asc()', lazy='dynamic'
    )

    @property
    def age_string(self):
        if not self.dob:
            return "N/A"
        today = date.today()
        years = today.year - self.dob.year
        months = today.month - self.dob.month
        if today.day < self.dob.day:
            months -= 1
        if months < 0:
            years -= 1
            months += 12

        if years == 0:
            return f"{months} month{'s' if months != 1 else ''}"
        elif months == 0:
            return f"{years} year{'s' if years != 1 else ''}"
        else:
            return f"{years} yr{'s' if years != 1 else ''} {months} mo"

    @property
    def age_group(self):
        """Categorize into infant, toddler, or preschool"""
        if not self.dob:
            return "all"
        today = date.today()
        age_years = (today - self.dob).days / 365.25
        if age_years < 1.0:
            return "infant"
        elif age_years < 3.0:
            return "toddler"
        else:
            return "preschool"

    def generate_qr_code(self, qrcode_dir):
        """Generate and save attendance check-in QR code"""
        os.makedirs(qrcode_dir, exist_ok=True)
        filename = f"child_qr_{self.id}.png"
        filepath = os.path.join(qrcode_dir, filename)
        
        qr_data = f"DAYCARE_CHECKIN:CHILD_ID={self.id}"
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filepath)
        
        self.qr_code_path = f"uploads/qrcodes/{filename}"
        return self.qr_code_path

    @property
    def today_attendance(self):
        from models.attendance import Attendance
        today = date.today()
        return Attendance.query.filter_by(child_id=self.id, date=today).first()

    @property
    def is_checked_in(self):
        att = self.today_attendance
        return att is not None and att.check_in_time is not None and att.check_out_time is None

    @property
    def is_checked_out(self):
        att = self.today_attendance
        return att is not None and att.check_out_time is not None

    @property
    def active_emergency_alert(self):
        """Returns today's latest emergency alert if any"""
        from models.message import Message
        today_start = datetime.combine(date.today(), datetime.min.time())
        return Message.query.filter(
            Message.child_id == self.id,
            Message.is_alert == True,
            Message.timestamp >= today_start
        ).order_by(Message.timestamp.desc()).first()

    def get_monthly_attendance_stats(self, year=None, month=None):
        from models.attendance import Attendance
        today = date.today()
        year = year or today.year
        month = month or today.month

        num_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, min(num_days, today.day if year == today.year and month == today.month else num_days))
        
        records = Attendance.query.filter(
            Attendance.child_id == self.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()

        # Count weekdays (excluding sat/sun) up to target day
        weekdays_count = 0
        cur = start_date
        while cur <= end_date:
            if cur.weekday() < 5:  # Mon-Fri
                weekdays_count += 1
            cur = cur.fromordinal(cur.toordinal() + 1)

        present_count = sum(1 for r in records if r.status in ('present', 'late'))
        
        percentage = round((present_count / weekdays_count * 100), 1) if weekdays_count > 0 else 100.0
        return {
            'total_possible_days': weekdays_count,
            'days_present': present_count,
            'days_absent': sum(1 for r in records if r.status == 'absent'),
            'percentage': percentage,
            'month_name': calendar.month_name[month],
            'year': year
        }

    def __repr__(self):
        return f"<Child {self.name} (ID: {self.id})>"
