"""Test database models."""
import unittest
from datetime import datetime
from app.models import db, Company, User, Receipt, Job
from app import create_app


class TestModels(unittest.TestCase):
    """Test database models."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        """Tear down test client."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_company_creation(self):
        """Test company model creation."""
        company = Company(
            name='Test Plumbing Co',
            phone_number='+1234567890',
            twilio_configured=True
        )
        db.session.add(company)
        db.session.commit()
        
        self.assertEqual(company.name, 'Test Plumbing Co')
        self.assertEqual(company.phone_number, '+1234567890')
        self.assertTrue(company.twilio_configured)
        
    def test_user_password(self):
        """Test user password hashing."""
        company = Company(name='Test Co')
        db.session.add(company)
        db.session.commit()
        
        user = User(
            username='testuser',
            email='test@example.com',
            company_id=company.id
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.check_password('wrongpass'))
        
    def test_job_profit_calculation(self):
        """Test job profit calculation."""
        company = Company(name='Test Co')
        db.session.add(company)
        db.session.commit()
        
        job = Job(
            job_number='JOB001',
            company_id=company.id,
            customer_name='Test Customer',
            revenue=1000.00,
            expenses=600.00
        )
        db.session.add(job)
        db.session.commit()
        
        self.assertEqual(job.profit, 400.00)
        self.assertEqual(job.profit_margin, 40.0)
        
    def test_receipt_job_association(self):
        """Test receipt-job association."""
        company = Company(name='Test Co')
        db.session.add(company)
        db.session.commit()
        
        job = Job(
            job_number='JOB001',
            company_id=company.id,
            customer_name='Test Customer'
        )
        db.session.add(job)
        db.session.commit()
        
        receipt = Receipt(
            company_id=company.id,
            job_id=job.id,
            vendor_name='Test Vendor',
            total_amount=100.00,
            image_path='test.jpg'
        )
        db.session.add(receipt)
        db.session.commit()
        
        self.assertEqual(receipt.job.job_number, 'JOB001')
        self.assertEqual(len(job.receipts), 1)


if __name__ == '__main__':
    unittest.main()