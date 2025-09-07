#!/usr/bin/env python3
"""
Initialize the application and database
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def init_database():
    """Initialize database with proper error handling"""
    try:
        from app.app import app, db
        from app.models import Company, User
        
        with app.app_context():
            print("Initializing database...")
            
            # Create all tables
            db.create_all()
            print("✓ Database tables created")
            
            # Run safe migration
            from safe_migration import run_safe_migration
            run_safe_migration()
            
            return True
            
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)