import unittest
from datetime import date, datetime, timedelta
from config import Config
from app import create_app, db
from models import User, Child, ActivityLog, Photo, Attendance, Message, LearningResource, Complaint, Notification

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # in-memory SQLite per engine

class DaycarePlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self._seed_test_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _seed_test_data(self):
        # Admin
        admin = User(name="Admin", email="admin@daycare.com", role="admin", is_approved=True)
        admin.set_password("Admin123!")

        # Caregivers
        cg1 = User(name="Caregiver Emma", email="caregiver1@daycare.com", role="caregiver", is_approved=True)
        cg1.set_password("Caregiver123!")

        cg_pending = User(name="Caregiver Pending", email="pending@daycare.com", role="caregiver", is_approved=False)
        cg_pending.set_password("Caregiver123!")

        # Parents
        p1 = User(name="Parent David", email="parent1@example.com", role="parent", is_approved=True)
        p1.set_password("Parent123!")

        p2 = User(name="Parent Elena", email="parent2@example.com", role="parent", is_approved=True)
        p2.set_password("Parent123!")

        db.session.add_all([admin, cg1, cg_pending, p1, p2])
        db.session.commit()

        # Children
        c1 = Child(name="Leo Miller", dob=date(2023, 5, 10), parent_id=p1.id, caregiver_id=cg1.id, allergies="Peanuts")
        c2 = Child(name="Sophia Rostova", dob=date(2022, 8, 15), parent_id=p2.id, caregiver_id=cg1.id, allergies="None")
        db.session.add_all([c1, c2])
        db.session.commit()

        # Learning resource
        res = LearningResource(
            title="Itsy Bitsy Spider",
            type="rhyme",
            age_group="infant",
            content_url_or_text="The itsy bitsy spider climbed up the waterspout..."
        )
        db.session.add(res)
        db.session.commit()

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_landing_and_login_flow(self):
        """Test landing page, bad login, and successful login with role redirect"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Connecting Parents & Caretakers in Real-Time', res.data)

        # Invalid login
        res = self.login('admin@daycare.com', 'WrongPassword')
        self.assertIn(b'Invalid email or password', res.data)

        # Admin login
        res = self.login('admin@daycare.com', 'Admin123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Director Control Center', res.data)
        self.logout()

        # Parent login
        res = self.login('parent1@example.com', 'Parent123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Leo Miller', res.data)
        self.logout()

    def test_02_caregiver_pending_approval_flow(self):
        """Test pending caregiver is blocked from classroom and admin can approve them"""
        # Login as pending caregiver
        res = self.login('pending@daycare.com', 'Caregiver123!')
        self.assertIn(b'Caretaker Account Pending Review', res.data)
        self.logout()

        # Login as admin and approve caregiver
        self.login('admin@daycare.com', 'Admin123!')
        with self.app.app_context():
            pending_user = User.query.filter_by(email='pending@daycare.com').first()
            user_id = pending_user.id

        res = self.client.post(f'/admin/approve/{user_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'approved successfully', res.data)
        self.logout()

        # Now pending caregiver can log in and view dashboard
        res = self.login('pending@daycare.com', 'Caregiver123!')
        self.assertIn(b'Caretaker Classroom Portal', res.data)
        self.logout()

    def test_03_activity_log_flow(self):
        """Test caregiver can log a meal and nap, and parent sees it on timeline"""
        self.login('caregiver1@daycare.com', 'Caregiver123!')
        with self.app.app_context():
            leo = Child.query.filter_by(name='Leo Miller').first()
            leo_id = leo.id

        # Post meal log
        res = self.client.post(f'/caregiver/child/{leo_id}/log', data={
            'type': 'meal',
            'meal_type': 'Lunch',
            'food_items': 'Chicken rice and peas',
            'amount_eaten': 'All (100%)',
            'meal_notes': 'Ate well with big smile'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Chicken rice and peas', res.data)
        self.logout()

        # Login as Parent 1 and check timeline
        self.login('parent1@example.com', 'Parent123!')
        res = self.client.get(f'/parent/child/{leo_id}/timeline')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Chicken rice and peas', res.data)
        self.assertIn(b'Ate well with big smile', res.data)
        self.logout()

    def test_04_access_control_isolation(self):
        """Test Parent 1 cannot view Parent 2's child data (strict 403)"""
        self.login('parent1@example.com', 'Parent123!')
        with self.app.app_context():
            sophia = Child.query.filter_by(name='Sophia Rostova').first()
            sophia_id = sophia.id

        # Parent 1 attempts to access Sophia's timeline
        res = self.client.get(f'/parent/child/{sophia_id}/timeline')
        self.assertEqual(res.status_code, 403)

        # Parent 1 attempts to access Sophia's photos
        res = self.client.get(f'/parent/child/{sophia_id}/photos')
        self.assertEqual(res.status_code, 403)

        # Parent 1 attempts to access Sophia's chat
        res = self.client.get(f'/messages/{sophia_id}')
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_05_emergency_alert_and_messaging(self):
        """Test emergency alert creates high priority banner on parent dashboard"""
        self.login('caregiver1@daycare.com', 'Caregiver123!')
        with self.app.app_context():
            leo = Child.query.filter_by(name='Leo Miller').first()
            leo_id = leo.id

        # Dispatch alert
        res = self.client.post(f'/caregiver/child/{leo_id}/alert', data={
            'title': 'High Fever Detected',
            'severity': 'critical',
            'content': 'Leo has a temperature of 101.5F. Resting in quiet room.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.logout()

        # Login as Parent 1 and check banner
        self.login('parent1@example.com', 'Parent123!')
        res = self.client.get('/parent/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'URGENT HEALTH / SAFETY ADVISORY', res.data)
        self.assertIn(b'HIGH FEVER DETECTED', res.data)
        self.logout()

    def test_06_daily_attendance_flow(self):
        """Test Caretaker daily attendance roster check-in and check-out flow"""
        self.login('caregiver1@daycare.com', 'Caregiver123!')
        with self.app.app_context():
            leo = Child.query.filter_by(name='Leo Miller').first()
            leo_id = leo.id

        # Check roster view
        res = self.client.get('/caregiver/attendance')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Daily Attendance Roster', res.data)
        self.assertIn(b'Leo Miller', res.data)

        # Check in child
        res = self.client.post(f'/caregiver/child/{leo_id}/attendance', data={
            'action': 'check_in'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'checked in at', res.data)

        with self.app.app_context():
            leo = Child.query.get(leo_id)
            self.assertTrue(leo.is_checked_in)
            self.assertIsNotNone(leo.today_attendance.check_in_time)

        # Check out child
        res = self.client.post(f'/caregiver/child/{leo_id}/attendance', data={
            'action': 'check_out'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'checked out at', res.data)

        with self.app.app_context():
            leo = Child.query.get(leo_id)
            self.assertTrue(leo.is_checked_out)
            self.assertIsNotNone(leo.today_attendance.check_out_time)

        self.logout()

    def test_07_learning_resources_flow(self):
        """Test browsing and viewing learning resources"""
        self.login('parent1@example.com', 'Parent123!')
        res = self.client.get('/learning/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Itsy Bitsy Spider', res.data)

        with self.app.app_context():
            res_item = LearningResource.query.first()
            res_id = res_item.id

        res = self.client.get(f'/learning/{res_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'The itsy bitsy spider climbed up the waterspout', res.data)
        self.logout()

    def test_08_password_reset_flow(self):
        """Test requesting reset link and setting new password"""
        # Request reset
        res = self.client.post('/reset-password', data={'email': 'parent1@example.com'})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Reset Token Generated', res.data)

        with self.app.app_context():
            p1 = User.query.filter_by(email='parent1@example.com').first()
            token = p1.reset_token
            self.assertIsNotNone(token)

        # Set new password
        res = self.client.post(f'/reset-password/{token}', data={
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'password has been reset successfully', res.data)

        # Confirm can login with new password
        res = self.login('parent1@example.com', 'NewPassword123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Leo Miller', res.data)
        self.logout()

if __name__ == '__main__':
    unittest.main()
