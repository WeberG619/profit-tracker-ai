#!/usr/bin/env python
"""
Initialize database - run this manually if tables aren't created
"""
import os
import sys

# Force PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url:
    print(f"Found DATABASE_URL: {database_url[:30]}...")
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        os.environ['DATABASE_URL'] = database_url
        print("Fixed postgres:// to postgresql://")

# Import after setting environment
from app.app import app, db
from app.models import Company, User, Receipt, Job, LineItem

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')[:50]}...")
        
        # Drop all tables first (careful in production!)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating tables...")
        db.create_all()
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\nCreated tables: {tables}")
        
        # Create test data
        if not User.query.first():
            print("\nCreating test company and user...")
            
            # Create test company
            company = Company(
                name="Test Company",
                phone_number="+1234567890"
            )
            db.session.add(company)
            db.session.commit()
            
            # Create test user
            user = User(
                username="admin",
                email="admin@example.com",
                company_id=company.id,
                is_admin=True
            )
            user.set_password("admin123")
            db.session.add(user)
            
            # Create test job
            job = Job(
                job_number="1001",
                customer_name="Test Customer",
                quoted_price=1000.00,
                company_id=company.id
            )
            db.session.add(job)
            
            db.session.commit()
            print("✅ Test data created (username: admin, password: admin123)")
        
        return True

if __name__ == "__main__":
    try:
        init_database()
        print("\n✅ Database initialization complete!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)