import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'virtual-daycare-secret-key-super-secure-2026')
    
    # SQLite default, easily swappable with postgresql:// or mysql://
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{BASE_DIR / 'daycare.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads settings
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    PHOTO_UPLOAD_FOLDER = UPLOAD_FOLDER / 'photos'
    QR_UPLOAD_FOLDER = UPLOAD_FOLDER / 'qrcodes'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')
    
    # App Information
    DAYCARE_NAME = os.environ.get('DAYCARE_NAME', 'Little Learners Virtual Daycare')
    DAYCARE_PHONE = os.environ.get('DAYCARE_PHONE', '+1 (555) 234-5678')
    DAYCARE_EMAIL = os.environ.get('DAYCARE_EMAIL', 'info@littlelearnersdaycare.com')
    DAYCARE_ADDRESS = os.environ.get('DAYCARE_ADDRESS', '123 Sunshine Lane, Suite 100, Cityville, CA 90210')
