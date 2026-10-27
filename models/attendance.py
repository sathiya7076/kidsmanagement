from datetime import date, datetime
from models import db

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='present') # 'present', 'absent', 'late', 'excused'
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    child = db.relationship('Child', back_populates='attendance_records')
    marker = db.relationship('User', foreign_keys=[marked_by])

    @property
    def formatted_check_in(self):
        return self.check_in_time.strftime('%I:%M %p') if self.check_in_time else '-'

    @property
    def formatted_check_out(self):
        return self.check_out_time.strftime('%I:%M %p') if self.check_out_time else '-'

    @property
    def duration_str(self):
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            total_minutes = int(delta.total_seconds() // 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
        elif self.check_in_time:
            return "Checked in (In Daycare)"
        return "-"

    @property
    def badge_class(self):
        classes = {
            'present': 'bg-success',
            'absent': 'bg-danger',
            'late': 'bg-warning text-dark',
            'excused': 'bg-info text-dark'
        }
        return classes.get(self.status, 'bg-secondary')

    def __repr__(self):
        return f"<Attendance Child {self.child_id} on {self.date}: {self.status}>"
