# 🎈 Virtual Daycare Platform (Deployment Ready)

A full-stack, production-style web application connecting parents and early childhood educators in real-time. Built with Python 3.11, Flask, SQLAlchemy ORM, Flask-Login, Flask-SocketIO, and Bootstrap 5.

---

## 🌟 Production Architecture & Features

- **Role-Based Access Control:**
  - **Daycare Director (Admin):** Manages educator approvals, child enrollment, center analytics, parent inquiries, and learning curriculum.
  - **Caretakers & Educators:** Classroom roster attendance, multi-category daily activity logging (meals, naps, moods, diapers, notes), child photo sharing, daily attendance marking, and priority emergency alerts.
  - **Parents & Guardians:** Live daily activity timeline with interactive date-picker, private child photo feed, attendance history with monthly percentage calculation, direct caretaker messaging, and high-priority health advisory banners.
- **Privacy Enforcement:** Built-in `@role_required` decorators and `get_authorized_child` validation guarantee strict tenant-like isolation — parents cannot view or access data for any children other than their own.
- **Streamlined Daily Attendance Roster:** 1-Click morning check-in and evening check-out with automated monthly percentage analytics.
- **Real-Time Communication:** WebSockets powered by Flask-SocketIO with seamless AJAX fallback polling for chat and notification bell updates.
- **Emergency Alert System:** Instant warning banner for fever, accidents, or urgent pickup alerts with simulated SMS (Twilio) and Email (SendGrid) service hooks in `notifications.py`.
- **Interactive Early Learning Hub:** Library of nursery rhymes, interactive stories, and developmental sensory activities categorized for Infants, Toddlers, and Preschoolers.

---

## 📁 Project Structure

```
virtual-daycare/
├── app.py                     # Application factory, SocketIO integration & entry point
├── config.py                  # Environment and database configuration
├── init_db.py                 # Production database initialization (zero sample data)
├── wsgi.py                    # WSGI production server entry point
├── Procfile                   # Process file for cloud deployments (Render, Railway, etc.)
├── requirements.txt           # Python dependencies (Flask, Gunicorn, Pillow, etc.)
├── seed.py                    # Optional staging/demo seeding utility
├── test_daycare.py            # Automated test suite (8 test cases)
├── .env                       # Active environment variables
├── .env.example               # Environment variables template
├── notifications.py           # Notification service with SMS/Email hooks
├── models/
│   ├── __init__.py            # SQLAlchemy db instance & model exports
│   ├── user.py                # User model & password hashing
│   ├── child.py               # Child model & QR code generator
│   ├── activity.py            # Daily activity logs (meal, nap, mood, diaper, note)
│   ├── photo.py               # Photo updates
│   ├── attendance.py          # Check-in / check-out records
│   ├── message.py             # Chat messages & emergency alert records
│   ├── learning.py            # Nursery rhymes, stories, and activities
│   ├── complaint.py           # Parent inquiries & admin responses
│   └── notification.py        # In-app notifications
├── routes/
│   ├── __init__.py            # Blueprint registration
│   ├── auth.py                # Login, registration, password reset
│   ├── admin.py               # Director center, caretaker approvals, enrollment
│   ├── caregiver.py           # Caretaker classroom portal, logging, attendance roster
│   ├── parent.py              # Parent dashboard, timeline, photos, attendance
│   ├── messages.py            # Real-time chat & message threads
│   ├── learning.py            # Learning hub browsing & reading mode
│   ├── api.py                 # In-app notification endpoints
│   └── utils.py               # Role decorators, child auth checks, file upload
├── templates/
│   ├── base.html              # Base layout with notification bell & navbar
│   ├── landing.html           # Public landing page with secure portal links
│   ├── 403.html, 404.html, 500.html # Custom error pages
│   ├── auth/                  # login.html, register.html, pending_approval.html, reset_*.html
│   ├── admin/                 # dashboard.html, caregivers.html, children.html, child_form.html, etc.
│   ├── caregiver/             # dashboard.html, child_detail.html, log_activity.html, attendance*.html
│   ├── parent/                # dashboard.html, timeline.html, photos.html, attendance.html, etc.
│   ├── messages/              # thread.html, list.html
│   └── learning/              # index.html, detail.html
└── static/
    ├── css/style.css          # Daycare portal styling & mobile responsiveness
    ├── js/main.js             # Notification bell, toasts, and datepicker automation
    ├── js/chat.js             # SocketIO & AJAX fallback chat script
    └── uploads/
        ├── photos/            # Uploaded child activity photos (.gitkeep)
        └── qrcodes/           # Generated student attendance QR codes (.gitkeep)
```

---

## 🚀 Production Deployment Steps

### 1. Clone & Set Up Virtual Environment
```bash
cd /home/user/virtual-daycare
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your production secrets:
```bash
cp .env.example .env
```
Key settings in `.env`:
- `SECRET_KEY`: Set to a strong random string.
- `DATABASE_URL`: Set to `sqlite:///daycare.db` or PostgreSQL connection string (`postgresql://user:password@host:5432/dbname`).
- `ADMIN_EMAIL`: Initial administrator email (default: `admin@daycare.com`).
- `ADMIN_PASSWORD`: Initial administrator password (default: `AdminSecure2026!`).
- `DAYCARE_NAME`: Name of your daycare institution.

### 3. Initialize Clean Production Database
Run `init_db.py` to create the database schema, register the initial Director Administrator account, and populate the learning curriculum. **All sample parents, dummy children, mock logs, and demo accounts are excluded**:
```bash
python init_db.py
```

### 4. Run in Production
#### Option A: Gunicorn / WSGI (Recommended for VPS or Linux servers)
```bash
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
```

#### Option B: Direct Python Runner / Container Entry
```bash
python wsgi.py
# or
python app.py
```

The portal is live at: **`http://localhost:5000`**

---

## 🛡️ Initial Administrator Account

| Parameter | Production Value | Description |
|---|---|---|
| **Email** | `admin@daycare.com` | Configurable via `ADMIN_EMAIL` in `.env` |
| **Password** | `AdminSecure2026!` | Configurable via `ADMIN_PASSWORD` in `.env` |
| **Role** | `admin` | Full administrative control |

### Initial Onboarding Workflow:
1. Log in with the Director administrator account.
2. Go to **Children &bull; Enroll New Child** to enroll your first students.
3. Invite or register educators; review their applications under **Caregiver Approvals**.
4. Parents register via the **Register** page to immediately connect with their children.

---

## 🧪 Automated Test Verification

Run the test suite to verify all endpoints, security decorators, and flows:
```bash
source venv/bin/activate
python -m unittest -v test_daycare.py
```

All 8 automated test suites verify:
1. Landing page and role-based login redirects
2. Caregiver pending approval blocker and Director approval flow
3. Caregiver activity logging and parent live timeline synchronization
4. Child data access control isolation (strict 403 enforcement)
5. Emergency alert dispatch and high-priority banner rendering
6. Digital QR attendance check-in and check-out API
7. Interactive learning module browsing and reading mode
8. Password reset token generation and credential updates
