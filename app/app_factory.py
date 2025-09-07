"""
Application factory with authentication and production features
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime

def create_app(config_name='development'):
    """Create Flask application with configuration"""
    app = Flask(__name__)
    
    # Load configuration
    from config_prod import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from models import db
    from auth import login_manager
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    )
    
    # Configure logging
    if app.config.get('LOG_TO_STDOUT'):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        app.logger.addHandler(stream_handler)
    
    # Import all the existing routes and functions
    from models import User, Company, Job, Receipt, LineItem
    from auth import company_required, admin_required, create_demo_user
    from analytics import get_dashboard_stats, get_jobs_summary, get_job_timeline
    from insights import JobInsights, PriceRecommendation, AlertMonitor
    from scheduler import job_scheduler
    
    # Initialize scheduler
    if config_name == 'production':
        job_scheduler.init_app(app)
    
    # Security headers
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False)
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                
                # Check if setup is complete
                if not user.company or not user.company.jobs:
                    return redirect(url_for('setup'))
                
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("3 per hour")
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            # Create company first
            company = Company(
                name=request.form.get('company_name'),
                phone_number=request.form.get('phone_number')
            )
            db.session.add(company)
            db.session.commit()
            
            # Create user
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                company_id=company.id,
                is_admin=True  # First user is admin
            )
            user.set_password(request.form.get('password'))
            
            try:
                db.session.add(user)
                db.session.commit()
                
                login_user(user)
                flash('Account created successfully!', 'success')
                return redirect(url_for('setup'))
                
            except Exception as e:
                db.session.rollback()
                flash('Username or email already exists', 'error')
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/setup')
    @login_required
    def setup():
        return render_template('setup.html', company=current_user.company)
    
    # API endpoints for setup
    @app.route('/api/setup/company', methods=['POST'])
    @login_required
    def setup_company():
        data = request.json
        company = current_user.company
        
        company.name = data.get('name', company.name)
        company.phone_number = data.get('phone_number', company.phone_number)
        
        db.session.commit()
        return jsonify({'success': True})
    
    @app.route('/api/setup/twilio', methods=['POST'])
    @login_required
    def setup_twilio():
        data = request.json
        company = current_user.company
        
        company.phone_number = data.get('twilio_number')
        company.twilio_configured = True
        
        db.session.commit()
        return jsonify({'success': True})
    
    # Apply company filter to all protected routes
    @app.before_request
    def filter_by_company():
        if current_user.is_authenticated:
            # Store company_id in g for easy access
            from flask import g
            g.company_id = current_user.company_id
    
    # Override the main routes to require authentication
    app.route('/')(company_required(lambda: render_template('index.html', preselected_job=request.args.get('job'))))
    app.route('/dashboard')(company_required(lambda: render_template('dashboard.html', stats=get_dashboard_stats(), jobs=get_jobs_summary())))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Create demo user if in development
        if config_name == 'development':
            create_demo_user()
    
    return app