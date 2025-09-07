"""Test insights and analytics functionality."""
import unittest
from datetime import datetime, timedelta
from app.models import db, Company, Job
from app.insights import (
    get_profit_trends, get_losing_job_patterns,
    get_price_recommendations, get_customer_insights
)
from app import create_app


class TestInsights(unittest.TestCase):
    """Test insights functionality."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test company
        self.company = Company(name='Test Co')
        db.session.add(self.company)
        db.session.commit()
        
        # Create test jobs
        self._create_test_jobs()
        
    def tearDown(self):
        """Tear down test client."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def _create_test_jobs(self):
        """Create test jobs for analysis."""
        # Profitable jobs
        for i in range(5):
            job = Job(
                job_number=f'PROF{i:03d}',
                company_id=self.company.id,
                customer_name='Good Customer',
                job_type='installation',
                revenue=1000 + (i * 100),
                expenses=600 + (i * 50),
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(job)
            
        # Losing jobs
        for i in range(3):
            job = Job(
                job_number=f'LOSS{i:03d}',
                company_id=self.company.id,
                customer_name='Bad Customer',
                job_type='repair',
                revenue=500,
                expenses=700,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(job)
            
        db.session.commit()
        
    def test_get_profit_trends(self):
        """Test profit trends calculation."""
        trends = get_profit_trends(self.company.id, days=30)
        
        self.assertIsNotNone(trends)
        self.assertGreater(len(trends), 0)
        
        # Check trend structure
        for trend in trends:
            self.assertIn('date', trend)
            self.assertIn('revenue', trend)
            self.assertIn('expenses', trend)
            self.assertIn('profit', trend)
            
    def test_get_losing_job_patterns(self):
        """Test losing job pattern detection."""
        patterns = get_losing_job_patterns(self.company.id)
        
        self.assertIsNotNone(patterns)
        
        # Should identify repair jobs as problematic
        job_type_losses = patterns.get('by_job_type', {})
        self.assertIn('repair', job_type_losses)
        self.assertLess(job_type_losses['repair']['total_profit'], 0)
        
    def test_get_price_recommendations(self):
        """Test price recommendation generation."""
        recommendations = get_price_recommendations(self.company.id)
        
        self.assertIsNotNone(recommendations)
        
        # Should recommend price increase for repair jobs
        for rec in recommendations:
            if rec['job_type'] == 'repair':
                self.assertGreater(rec['recommended_increase'], 0)
                
    def test_get_customer_insights(self):
        """Test customer insights generation."""
        insights = get_customer_insights(self.company.id)
        
        self.assertIsNotNone(insights)
        
        # Should identify both good and bad customers
        self.assertGreater(len(insights['top_customers']), 0)
        self.assertGreater(len(insights['problem_customers']), 0)
        
        # Check customer structure
        for customer in insights['top_customers']:
            self.assertIn('name', customer)
            self.assertIn('total_revenue', customer)
            self.assertIn('total_profit', customer)
            self.assertIn('job_count', customer)


if __name__ == '__main__':
    unittest.main()