#!/usr/bin/env python3
"""
Script to diagnose and fix login issues
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import app, db
from app.models import User, Company
from werkzeug.security import generate_password_hash

def diagnose_and_fix():
    """Diagnose and fix login issues"""
    with app.app_context():
        print("=== Login Issue Diagnosis ===\n")
        
        # Check if any users exist
        user_count = User.query.count()
        print(f"Total users in database: {user_count}")
        
        # Check if any companies exist
        company_count = Company.query.count()
        print(f"Total companies in database: {company_count}")
        
        # List all users
        print("\nExisting users:")
        users = User.query.all()
        for user in users:
            print(f"  - Username: {user.username}, Email: {user.email}, Company ID: {user.company_id}")
        
        # Check for admin user
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"\nAdmin user found: Company ID = {admin_user.company_id}")
            
            # Check if company exists
            if admin_user.company:
                print(f"Company: {admin_user.company.name}")
            else:
                print("WARNING: Admin user has no associated company!")
                
                # Fix by creating a default company
                print("\nCreating default company...")
                default_company = Company(name="Demo Company")
                db.session.add(default_company)
                db.session.commit()
                
                admin_user.company_id = default_company.id
                db.session.commit()
                print(f"✓ Created company and linked to admin user")
        else:
            print("\nNo admin user found. Creating one...")
            
            # Create default company first
            default_company = Company.query.filter_by(name="Demo Company").first()
            if not default_company:
                default_company = Company(name="Demo Company")
                db.session.add(default_company)
                db.session.commit()
                print(f"✓ Created Demo Company (ID: {default_company.id})")
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                company_id=default_company.id,
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ Created admin user with password 'admin123'")
        
        # Reset admin password to ensure it works
        print("\nResetting admin password to 'admin123'...")
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.set_password('admin123')
            db.session.commit()
            print("✓ Admin password reset successfully")
        
        print("\n=== Fix Complete ===")
        print("\nYou should now be able to login with:")
        print("  Username: admin")
        print("  Password: admin123")

if __name__ == "__main__":
    diagnose_and_fix()