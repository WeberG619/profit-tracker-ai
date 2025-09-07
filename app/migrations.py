"""
Database migrations for production updates
"""

import os
import sys
from alembic import command
from alembic.config import Config
from flask_migrate import Migrate, init, migrate, upgrade
from app_factory import create_app
from models import db

def run_migrations():
    """Run database migrations"""
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    
    with app.app_context():
        # Initialize Flask-Migrate
        Migrate(app, db)
        
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            print("Initializing migrations...")
            init()
        
        # Create migration
        try:
            print("Creating migration...")
            migrate(message='Auto migration')
        except:
            print("No changes detected")
        
        # Apply migrations
        print("Applying migrations...")
        upgrade()
        
        print("Migrations complete!")

def create_tables():
    """Create all tables (fallback method)"""
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    
    with app.app_context():
        db.create_all()
        print("Tables created successfully!")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--create-tables':
        create_tables()
    else:
        run_migrations()