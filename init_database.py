#!/usr/bin/env python3
"""
Initialize the database for profit-tracker-ai
This script creates the database tables and sets up basic data.
"""

import sys
import os

# Ensure the instance directory exists
os.makedirs('instance', exist_ok=True)

# Set environment to avoid production checks
os.environ['TESTING'] = '1'

# Import Flask and SQLAlchemy manually to avoid app startup issues
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create minimal Flask app
app = Flask(__name__)
db_path = os.path.abspath('instance/receipts.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key-for-init'

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Define models (copied from models.py)
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20))
    twilio_configured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    jobs = db.relationship('Job', backref='company', lazy=True)
    receipts = db.relationship('Receipt', backref='company', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    vendor_name = db.Column(db.String(200))
    total_amount = db.Column(db.Float)
    date = db.Column(db.Date)
    receipt_number = db.Column(db.String(100))
    extracted_data = db.Column(db.JSON)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    uploaded_by = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    upload_method = db.Column(db.String(20), default='web')
    receipt_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    line_items = db.relationship('LineItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    job = db.relationship('Job', backref='receipts')

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(200))
    quoted_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Add unique constraint for job_number + company_id
    __table_args__ = (db.UniqueConstraint('job_number', 'company_id'),)

class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    description = db.Column(db.String(500))
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))

def main():
    print("=== Initializing Profit Tracker AI Database ===")
    
    with app.app_context():
        try:
            # Drop all tables if they exist (for clean start)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ Created tables: {tables}")
            
            # Create default admin user for testing
            print("Creating default admin user...")
            
            company = Company(
                name="Test Company",
                phone_number="+1234567890"
            )
            db.session.add(company)
            db.session.flush()  # Get the ID
            
            from werkzeug.security import generate_password_hash
            user = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123"),
                company_id=company.id,
                is_admin=True
            )
            db.session.add(user)
            
            # Create a test job
            job = Job(
                job_number="TEST001",
                customer_name="Test Customer",
                quoted_price=1000.0,
                company_id=company.id,
                status="active"
            )
            db.session.add(job)
            
            db.session.commit()
            
            print("✓ Default data created:")
            print("  - Company: Test Company")
            print("  - User: admin / admin123")
            print("  - Job: TEST001")
            
            # Test the database
            print("\nTesting database connection...")
            from sqlalchemy import text
            result = db.session.execute(text('SELECT COUNT(*) FROM company'))
            company_count = result.scalar()
            print(f"✓ Database test successful - {company_count} companies found")
            
            print("\n=== Database initialization complete! ===")
            print("You can now run the application with: python -m flask --app app.app:app run")
            
        except Exception as e:
            print(f"✗ Error during initialization: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())