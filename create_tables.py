#!/usr/bin/env python
"""
Create database tables for production
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force PostgreSQL if DATABASE_URL exists
if os.environ.get('DATABASE_URL'):
    import force_postgresql

from app.app import app, db
from app.models import Company, User, Receipt, Job, LineItem

print("Creating database tables...")
print(f"DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")
print(f"Using database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')[:50]}...")

with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✅ Created tables: {', '.join(tables)}")
        
        # Check if tables were actually created
        if not tables:
            print("⚠️  No tables found - database might not be properly connected")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)