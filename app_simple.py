"""
Simplified app to get basic functionality working
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Create Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///receipts.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Simple models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(200))
    total_amount = db.Column(db.Float)
    date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    """Landing page"""
    return '''
    <html>
    <head><title>Profit Tracker AI</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>Profit Tracker AI</h1>
        <p>AI-powered receipt tracking for contractors</p>
        <p><a href="/login">Login</a></p>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return '''
    <html>
    <head><title>Login - Profit Tracker AI</title></head>
    <body style="font-family: sans-serif; max-width: 400px; margin: 50px auto;">
        <h1>Login</h1>
        <form method="POST">
            <p>
                <label>Username:</label><br>
                <input type="text" name="username" required>
            </p>
            <p>
                <label>Password:</label><br>
                <input type="password" name="password" required>
            </p>
            <p>
                <button type="submit">Login</button>
            </p>
        </form>
        <p>Default: admin / admin123</p>
    </body>
    </html>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    """Simple dashboard"""
    return f'''
    <html>
    <head><title>Dashboard - Profit Tracker AI</title></head>
    <body style="font-family: sans-serif; padding: 50px;">
        <h1>Welcome, {current_user.username}!</h1>
        <p>This is a simplified dashboard.</p>
        <p><a href="/logout">Logout</a></p>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'app': 'simple'})

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)