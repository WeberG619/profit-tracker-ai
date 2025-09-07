"""
WSGI entry point for production deployment
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force PostgreSQL if DATABASE_URL exists
if os.environ.get('DATABASE_URL'):
    import force_postgresql

from app.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))