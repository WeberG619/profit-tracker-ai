"""
WSGI entry point for production deployment
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Debug: Print environment info
print(f"[WSGI] Starting up...")
print(f"[WSGI] DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")
print(f"[WSGI] RENDER env: {bool(os.environ.get('RENDER'))}")

# Force PostgreSQL if DATABASE_URL exists
if os.environ.get('DATABASE_URL'):
    print("[WSGI] DATABASE_URL found, importing force_postgresql")
    import force_postgresql
else:
    print("[WSGI] WARNING: No DATABASE_URL found!")

from app.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))