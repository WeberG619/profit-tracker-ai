import os
from dotenv import load_dotenv

# Only load .env file in development, not on Render
if not os.environ.get('RENDER'):
    load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # Use PostgreSQL in production, SQLite for local development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Force in-memory SQLite if no DATABASE_URL (for production without PostgreSQL)
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        # Fix for Render's postgres:// URLs (need postgresql://)
        if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    elif os.environ.get('RENDER'):
        # On Render but no DATABASE_URL - use in-memory SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        print("WARNING: Using in-memory SQLite database. Data will not persist!")
    else:
        # Local development - use absolute path to avoid path issues
        import os
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'receipts.db'))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')