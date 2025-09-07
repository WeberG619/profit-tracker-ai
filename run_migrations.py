#!/usr/bin/env python3
"""
Run database migrations on startup
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import app, db

def run_migrations():
    """Run all database migrations"""
    with app.app_context():
        print("Running database migrations...")
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created/updated")
        
        # Run invoice migration
        try:
            from migrations.add_invoice_support import run_migration
            if run_migration():
                print("✓ Invoice support migration completed")
            else:
                print("⚠ Invoice migration may have already been applied")
        except Exception as e:
            print(f"⚠ Could not run invoice migration: {e}")
        
        print("All migrations completed!")

if __name__ == "__main__":
    run_migrations()