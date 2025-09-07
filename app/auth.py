"""
Authentication and authorization utilities
"""

from flask import redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from .models import User, Company
import os

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def company_required(f):
    """Decorator to ensure user has a company"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.company_id:
            flash('Please complete company setup first.', 'warning')
            return redirect(url_for('setup'))
        
        # Add company filter to session
        session['company_id'] = current_user.company_id
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_company():
    """Get the current user's company"""
    if current_user.is_authenticated:
        return current_user.company
    return None

def filter_by_company(query, model):
    """Filter query by current user's company"""
    if current_user.is_authenticated and hasattr(model, 'company_id'):
        return query.filter_by(company_id=current_user.company_id)
    return query

def is_setup_complete():
    """Check if initial setup is complete"""
    if not current_user.is_authenticated:
        return False
    
    company = current_user.company
    if not company:
        return False
    
    # Check if company has basic configuration
    return bool(company.name and len(company.jobs) > 0)

def create_demo_user():
    """Create a demo user for testing"""
    from models import db
    
    # Check if demo company exists
    demo_company = Company.query.filter_by(name='Demo Company').first()
    if not demo_company:
        demo_company = Company(
            name='Demo Company',
            phone_number='+1234567890',
            twilio_configured=False
        )
        db.session.add(demo_company)
        db.session.commit()
    
    # Check if demo user exists
    demo_user = User.query.filter_by(username='demo').first()
    if not demo_user:
        demo_user = User(
            username='demo',
            email='demo@example.com',
            company_id=demo_company.id,
            is_admin=True
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        db.session.commit()
    
    return demo_user