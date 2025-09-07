#!/usr/bin/env python3
"""
Safe migration script that handles all database updates gracefully
"""
import os
import sys
from sqlalchemy import text, inspect

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import app, db
from app.models import User, Company, Receipt

def safe_add_column(table_name, column_name, column_type, default_value=None):
    """Safely add a column if it doesn't exist"""
    try:
        with db.engine.connect() as conn:
            # Check if column exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if column_name not in columns:
                # Add column
                if default_value is not None:
                    query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                else:
                    query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                
                conn.execute(text(query))
                conn.commit()
                print(f"✓ Added column {column_name} to {table_name}")
            else:
                print(f"  Column {column_name} already exists in {table_name}")
                
    except Exception as e:
        print(f"  Warning: Could not add {column_name}: {str(e)}")

def run_safe_migration():
    """Run database migrations safely"""
    with app.app_context():
        print("=== Running Safe Migration ===\n")
        
        # First ensure all tables exist
        print("1. Creating/updating tables...")
        try:
            db.create_all()
            print("✓ Tables created/verified")
        except Exception as e:
            print(f"⚠ Table creation warning: {e}")
        
        # Add invoice support columns to receipt table
        print("\n2. Adding invoice support columns...")
        invoice_columns = [
            ('document_type', 'VARCHAR(50)', 'receipt'),
            ('direction', 'VARCHAR(20)', 'expense'),
            ('status', 'VARCHAR(20)', 'paid'),
            ('due_date', 'DATE', None),
            ('customer_name', 'VARCHAR(255)', None),
            ('customer_email', 'VARCHAR(255)', None),
            ('customer_phone', 'VARCHAR(50)', None),
            ('invoice_number', 'VARCHAR(100)', None),
            ('sent_date', 'TIMESTAMP', None),
            ('paid_date', 'TIMESTAMP', None),
            ('payment_method', 'VARCHAR(50)', None),
            ('terms', 'TEXT', None),
            ('notes', 'TEXT', None),
        ]
        
        for col_name, col_type, default in invoice_columns:
            safe_add_column('receipt', col_name, col_type, default)
        
        # Ensure admin user exists
        print("\n3. Checking admin user...")
        try:
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                # Create demo company first
                company = Company.query.filter_by(name='Demo Company').first()
                if not company:
                    company = Company(name='Demo Company', phone_number='+1234567890')
                    db.session.add(company)
                    db.session.commit()
                    print("✓ Created Demo Company")
                
                # Create admin user
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    company_id=company.id,
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Created admin user")
            else:
                # Ensure admin has company
                if not admin.company_id:
                    company = Company.query.filter_by(name='Demo Company').first()
                    if not company:
                        company = Company(name='Demo Company')
                        db.session.add(company)
                        db.session.commit()
                    admin.company_id = company.id
                    db.session.commit()
                    print("✓ Fixed admin company association")
                
                # Reset password
                admin.set_password('admin123')
                db.session.commit()
                print("✓ Reset admin password")
                
        except Exception as e:
            print(f"⚠ Admin user warning: {e}")
        
        print("\n=== Migration Complete ===")
        print("\nLogin credentials:")
        print("  Username: admin")
        print("  Password: admin123")

if __name__ == "__main__":
    run_safe_migration()