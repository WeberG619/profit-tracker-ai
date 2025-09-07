#!/usr/bin/env python
"""
Create database tables for production
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import app, db

print("Creating database tables...")

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
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        sys.exit(1)