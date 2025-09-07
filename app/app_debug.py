"""
Debug version of app.py to help diagnose issues
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/receipts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}

# Initialize extensions
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db initialization
from .models import Receipt, Job, LineItem, Company, User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Basic route to test
@app.route('/')
def index():
    if current_user.is_authenticated:
        return f"<h1>Logged in as {current_user.username}</h1><p><a href='/logout'>Logout</a></p>"
    return "<h1>Profit Tracker AI</h1><p><a href='/login'>Login</a> | <a href='/register'>Register</a></p>"

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'database': 'connected' if db.engine else 'not connected',
        'upload_folder': os.path.exists(app.config['UPLOAD_FOLDER'])
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        return "Invalid login"
    return '''
    <form method="post">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Create company
            company = Company(
                name=request.form.get('company_name', 'Test Company'),
                phone_number=request.form.get('phone_number', '')
            )
            db.session.add(company)
            db.session.commit()
            
            # Create user
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email', 'test@example.com'),
                company_id=company.id,
                is_admin=True
            )
            user.set_password(request.form.get('password', 'password'))
            db.session.add(user)
            db.session.commit()
            
            return "Registration successful! <a href='/login'>Login</a>"
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}"
    
    return '''
    <form method="post">
        <input name="company_name" placeholder="Company Name" required>
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Register</button>
    </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

# Create tables
with app.app_context():
    db.create_all()
    print("Database tables created")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))