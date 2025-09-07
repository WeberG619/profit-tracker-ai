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
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .header { background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { margin: 0; color: #333; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; }
        .stat-card .value { font-size: 36px; font-weight: bold; color: #333; }
        .btn { display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .btn:hover { background: #0056b3; }
        .logout { float: right; background: #dc3545; }
        .logout:hover { background: #c82333; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/logout" class="btn logout">Logout</a>
        <h1>Welcome, {{ username }}!</h1>
    </div>
    
    <div class="container">
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h2>Quick Actions</h2>
            <a href="/upload" class="btn">📸 Upload Receipt</a>
            <a href="/receipts" class="btn" style="background: #28a745;">📋 View Receipts</a>
            <a href="/invoices" class="btn" style="background: #ffc107; color: #333;">💰 Invoices</a>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Receipts</h3>
                <div class="value">0</div>
            </div>
            <div class="stat-card">
                <h3>Total Expenses</h3>
                <div class="value" style="color: #dc3545;">$0</div>
            </div>
            <div class="stat-card">
                <h3>Total Income</h3>
                <div class="value" style="color: #28a745;">$0</div>
            </div>
            <div class="stat-card">
                <h3>Net Profit</h3>
                <div class="value">$0</div>
            </div>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <p>🎉 Your Profit Tracker AI is ready! Start by uploading your first receipt.</p>
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

@app.route('/register')
def register():
    return '<h1>Registration coming soon!</h1><p><a href="/">Back to home</a></p>'

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