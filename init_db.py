#!/usr/bin/env python
"""
Initialize database for Profit Tracker AI
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import db, Company, User, Job
from app.app import app

def init_database():
    """Initialize database with tables and demo data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if demo company exists
        demo_company = Company.query.filter_by(name='Demo Company').first()
        if not demo_company:
            # Create demo company
            demo_company = Company(
                name='Demo Company',
                phone_number='+1234567890'
            )
            db.session.add(demo_company)
            db.session.commit()
            print("✓ Demo company created")
            
            # Create demo user
            demo_user = User(
                username='demo',
                email='demo@example.com',
                company_id=demo_company.id,
                is_admin=True
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            print("✓ Demo user created (username: demo, password: demo123)")
            
            # Create some demo jobs
            demo_jobs = [
                {'job_number': 'JOB001', 'customer_name': 'Smith Residence', 'job_type': 'plumbing', 'revenue': 500},
                {'job_number': 'JOB002', 'customer_name': 'Johnson Office', 'job_type': 'electrical', 'revenue': 750},
                {'job_number': 'JOB003', 'customer_name': 'Brown Kitchen', 'job_type': 'renovation', 'revenue': 1200}
            ]
            
            for job_data in demo_jobs:
                job = Job(
                    company_id=demo_company.id,
                    **job_data,
                    status='active'
                )
                db.session.add(job)
            
            db.session.commit()
            print("✓ Demo jobs created")
        else:
            print("✓ Demo data already exists")

if __name__ == '__main__':
    init_database()