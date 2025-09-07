"""
Application factory for Profit Tracker AI
"""

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging

def create_app(config_name='production'):
    """Create Flask application with configuration"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'production':
        app.config.from_object('app.config.Config')
    else:
        app.config.from_object('app.config.Config')
        app.config['TESTING'] = config_name == 'testing'
        app.config['DEBUG'] = config_name == 'development'
    
    # Initialize extensions
    from .models import db
    from .auth import login_manager
    from .scheduler import job_scheduler
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
    
    # Initialize scheduler
    if not app.config.get('TESTING'):
        job_scheduler.init_app(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s'
        )
    
    # Create upload folder
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Register blueprints/routes
    with app.app_context():
        # Import routes here to avoid circular imports
        from . import routes
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(routes.auth_bp)
        app.register_blueprint(routes.api_bp, url_prefix='/api')
        
        # Create database tables
        if not app.config.get('TESTING'):
            db.create_all()
    
    return app