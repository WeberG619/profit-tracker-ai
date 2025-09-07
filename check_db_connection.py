#!/usr/bin/env python
"""
Check database connection and environment
"""
import os
import sys

print("=== DATABASE CONNECTION CHECK ===")
print(f"1. DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")
print(f"2. DATABASE_URL value: {os.environ.get('DATABASE_URL', 'NOT SET')[:50]}...")
print(f"3. RENDER env: {os.environ.get('RENDER', 'NOT SET')}")
print(f"4. Python path: {sys.executable}")
print(f"5. Current directory: {os.getcwd()}")

# Try importing the app
try:
    from app.config import Config
    config = Config()
    print(f"\n6. Config loaded successfully")
    print(f"7. SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI[:50]}...")
    
    # Try connecting to database
    from app.app import app, db
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1'))
        print(f"\n8. Database connection: SUCCESS")
        
        # Check tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"9. Existing tables: {tables}")
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== END CHECK ===")