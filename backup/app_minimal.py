"""
Minimal working app - just the essentials
"""
import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-2024')

# Database config
db_url = os.environ.get('DATABASE_URL', 'sqlite:///receipts.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# HTML Templates as strings
LANDING_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .btn { display: inline-block; padding: 12px 30px; margin: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .btn:hover { background: #0056b3; }
        .features { margin: 40px 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; text-align: left; }
        .feature { padding: 20px; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Profit Tracker AI</h1>
        <p style="font-size: 1.2em; color: #666;">Stop losing money on jobs. AI-powered receipt tracking for contractors.</p>
        
        <div>
            <a href="/login" class="btn">Login</a>
            <a href="/register" class="btn" style="background: #28a745;">Register</a>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>📸 Snap & Track</h3>
                <p>Take a photo of any receipt</p>
            </div>
            <div class="feature">
                <h3>🤖 AI Processing</h3>
                <p>Automatic data extraction</p>
            </div>
            <div class="feature">
                <h3>💰 Track Profits</h3>
                <p>Know your margins instantly</p>
            </div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .error { color: #dc3545; text-align: center; margin: 10px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔐 Login</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="info">
            <strong>Demo Account:</strong><br>
            Username: admin<br>
            Password: admin123
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <a href="/">← Back</a> | <a href="/register">Create Account</a>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Profit Tracker AI</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f0f2f5; }
        .navbar { background: #1a1a1a; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .navbar h1 { margin: 0; font-size: 1.5rem; font-weight: 600; }
        .navbar .user-info { display: flex; align-items: center; gap: 1rem; }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .welcome-section { background: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .welcome-section h2 { margin: 0 0 1rem 0; font-size: 1.875rem; color: #111; }
        .action-buttons { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1.5rem; }
        .btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 500; text-decoration: none; border-radius: 8px; transition: all 0.2s; }
        .btn-primary { background: #2563eb; color: white; }
        .btn-primary:hover { background: #1d4ed8; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.2); }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(16,185,129,0.2); }
        .btn-warning { background: #f59e0b; color: white; }
        .btn-warning:hover { background: #d97706; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(245,158,11,0.2); }
        .btn-danger { background: #ef4444; color: white; }
        .btn-danger:hover { background: #dc2626; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.3s; }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .stat-card .icon { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 1rem; }
        .stat-card h3 { margin: 0 0 0.5rem 0; font-size: 0.875rem; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.025em; }
        .stat-card .value { font-size: 2.25rem; font-weight: 700; color: #111; margin: 0; }
        .stat-card .change { font-size: 0.875rem; margin-top: 0.5rem; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .recent-activity { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .recent-activity h3 { margin: 0 0 1.5rem 0; font-size: 1.25rem; font-weight: 600; }
        .activity-list { list-style: none; padding: 0; margin: 0; }
        .activity-item { padding: 1rem 0; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; gap: 1rem; }
        .activity-item:last-child { border-bottom: none; }
        .activity-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; }
        .activity-details { flex: 1; }
        .activity-time { color: #6b7280; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>📊 Profit Tracker AI</h1>
        <div class="user-info">
            <span>{{ username }}</span>
            <a href="/logout" class="btn btn-danger">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="welcome-section">
            <h2>Welcome back, {{ username }}!</h2>
            <p style="color: #6b7280; margin: 0;">Track your expenses and income to maximize profits.</p>
            
            <div class="action-buttons">
                <a href="/upload" class="btn btn-primary">
                    <span>📸</span> Upload Receipt
                </a>
                <a href="/receipts" class="btn btn-success">
                    <span>📋</span> View Receipts
                </a>
                <a href="/invoices" class="btn btn-warning">
                    <span>💰</span> Manage Invoices
                </a>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon" style="background: #dbeafe; color: #2563eb;">📄</div>
                <h3>Total Documents</h3>
                <p class="value">0</p>
                <p class="change positive">+0% from last month</p>
            </div>
            
            <div class="stat-card">
                <div class="icon" style="background: #fee2e2; color: #ef4444;">💸</div>
                <h3>Total Expenses</h3>
                <p class="value">$0.00</p>
                <p class="change negative">+0% from last month</p>
            </div>
            
            <div class="stat-card">
                <div class="icon" style="background: #d1fae5; color: #10b981;">💵</div>
                <h3>Total Income</h3>
                <p class="value">$0.00</p>
                <p class="change positive">+0% from last month</p>
            </div>
            
            <div class="stat-card">
                <div class="icon" style="background: #e0e7ff; color: #6366f1;">📈</div>
                <h3>Net Profit</h3>
                <p class="value">$0.00</p>
                <p class="change positive">+0% margin</p>
            </div>
        </div>
        
        <div class="recent-activity">
            <h3>Recent Activity</h3>
            <ul class="activity-list">
                <li class="activity-item">
                    <div class="activity-icon" style="background: #f3f4f6; color: #6b7280;">🎉</div>
                    <div class="activity-details">
                        <div>Welcome to Profit Tracker AI!</div>
                        <div class="activity-time">Get started by uploading your first receipt</div>
                    </div>
                </li>
            </ul>
        </div>
    </div>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    return LANDING_HTML

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML, username=session.get('username', 'User'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

REGISTER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .register-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #28a745; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #218838; }
        .error { color: #dc3545; text-align: center; margin: 10px 0; }
        .success { color: #28a745; text-align: center; margin: 10px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="register-box">
        <h2>🚀 Create Account</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="password" name="confirm_password" placeholder="Confirm Password" required>
            <button type="submit">Create Account</button>
        </form>
        <div style="text-align: center; margin-top: 20px;">
            <a href="/">← Back</a> | <a href="/login">Already have an account?</a>
        </div>
    </div>
</body>
</html>
'''

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            error = 'Passwords do not match'
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = 'Username already exists'
            else:
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                success = 'Account created! You can now login.'
    
    return render_template_string(REGISTER_HTML, error=error, success=success)

@app.route('/upload')
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return '<h1>Upload feature coming soon!</h1><p><a href="/dashboard">Back to dashboard</a></p>'

@app.route('/receipts')
def receipts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return '<h1>Receipts list coming soon!</h1><p><a href="/dashboard">Back to dashboard</a></p>'

@app.route('/invoices')
def invoices():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return '<h1>Invoices feature coming soon!</h1><p><a href="/dashboard">Back to dashboard</a></p>'

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'minimal'}

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)