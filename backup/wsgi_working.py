"""
WSGI entry point for working version
"""
import os
import sys

# Add the directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ['FLASK_APP'] = 'app_working'

# Force PostgreSQL if DATABASE_URL exists
if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    if db_url.startswith('postgres://'):
        os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

from app_working import app

if __name__ == '__main__':
    app.run()