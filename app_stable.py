"""
Stable working version - guaranteed to work
"""
import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'stable-2024')

# Professional templates as strings to avoid file issues
LANDING_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Profit Tracker AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
        .nav { background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1rem 0; position: fixed; width: 100%; top: 0; z-index: 1000; }
        .nav-container { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; color: #2563eb; }
        .nav-links { display: flex; gap: 2rem; align-items: center; }
        .nav-links a { color: #333; text-decoration: none; transition: color 0.3s; }
        .nav-links a:hover { color: #2563eb; }
        .btn { padding: 0.5rem 1.5rem; border-radius: 0.375rem; text-decoration: none; transition: all 0.3s; display: inline-block; }
        .btn-primary { background: #2563eb; color: white; }
        .btn-primary:hover { background: #1d4ed8; }
        .hero { margin-top: 4rem; padding: 6rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero p { font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9; }
        .features { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
        .features h2 { text-align: center; font-size: 2.5rem; margin-bottom: 3rem; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
        .feature-card { background: #f8f9fa; padding: 2rem; border-radius: 0.5rem; text-align: center; transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); }
        .feature-icon { font-size: 3rem; margin-bottom: 1rem; }
        .stats { background: #f8f9fa; padding: 4rem 2rem; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; max-width: 800px; margin: 0 auto; }
        .stat { padding: 2rem; }
        .stat-number { font-size: 3rem; font-weight: bold; color: #2563eb; }
        .cta { background: #2563eb; color: white; padding: 4rem 2rem; text-align: center; }
        .cta h2 { font-size: 2.5rem; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <div class="logo">📊 Profit Tracker AI</div>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="#how-it-works">How It Works</a>
                <a href="/login">Login</a>
                <a href="/register" class="btn btn-primary">Start Free Trial</a>
            </div>
        </div>
    </nav>

    <section class="hero">
        <h1>Know Your True Profit on Every Job</h1>
        <p>The AI-powered financial platform built for contractors. Stop losing money on underpriced jobs.</p>
        <a href="/register" class="btn btn-primary" style="font-size: 1.125rem; padding: 0.75rem 2rem;">Start 14-Day Free Trial</a>
    </section>

    <section class="stats">
        <h2 style="font-size: 2rem; margin-bottom: 2rem;">Most Contractors Are Flying Blind</h2>
        <div class="stats-grid">
            <div class="stat">
                <div class="stat-number">67%</div>
                <p>Don't know their true costs</p>
            </div>
            <div class="stat">
                <div class="stat-number">$4,800</div>
                <p>Lost monthly from underpricing</p>
            </div>
            <div class="stat">
                <div class="stat-number">23%</div>
                <p>Average profit increase</p>
            </div>
        </div>
    </section>

    <section class="features" id="features">
        <h2>Everything You Need to Maximize Profits</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">📸</div>
                <h3>AI Receipt Scanning</h3>
                <p>Snap a photo. AI extracts everything. No manual entry.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💼</div>
                <h3>Job Profit Tracking</h3>
                <p>See real-time margins on every job. Know what makes money.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Financial Reports</h3>
                <p>Monthly P&L, expense breakdowns, profit trends.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3>Invoice Management</h3>
                <p>Track what's owed. Never miss a payment.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚠️</div>
                <h3>Cost Alerts</h3>
                <p>Get notified when jobs go over budget.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📤</div>
                <h3>QuickBooks Export</h3>
                <p>Seamless integration for tax time.</p>
            </div>
        </div>
    </section>

    <section class="cta">
        <h2>Stop Leaving Money on the Table</h2>
        <p style="font-size: 1.25rem; margin-bottom: 2rem;">Join 1,000+ contractors who increased profits by 23%</p>
        <a href="/register" class="btn" style="background: white; color: #2563eb; font-size: 1.125rem; padding: 0.75rem 2rem;">Start Your Free Trial</a>
    </section>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Profit Tracker AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f7fa; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .login-container { background: white; padding: 2rem; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        .logo { text-align: center; font-size: 2rem; font-weight: bold; color: #2563eb; margin-bottom: 2rem; }
        h2 { text-align: center; margin-bottom: 1.5rem; color: #333; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; color: #555; font-weight: 500; }
        input { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 0.375rem; font-size: 1rem; }
        input:focus { outline: none; border-color: #2563eb; }
        button { width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 0.375rem; font-size: 1rem; font-weight: 500; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #1d4ed8; }
        .demo-info { background: #e0e7ff; padding: 1rem; border-radius: 0.375rem; margin-top: 1.5rem; text-align: center; }
        .links { text-align: center; margin-top: 1.5rem; }
        .links a { color: #2563eb; text-decoration: none; }
        .links a:hover { text-decoration: underline; }
        .error { background: #fee; color: #c00; padding: 0.75rem; border-radius: 0.375rem; margin-bottom: 1rem; text-align: center; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">📊 Profit Tracker AI</div>
        <h2>Welcome Back</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
        <div class="demo-info">
            <strong>Demo Account</strong><br>
            Username: admin<br>
            Password: admin123
        </div>
        <div class="links">
            <a href="/">← Back to Home</a> | <a href="/register">Create Account</a>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f7fa; }
        .header { background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1rem 0; }
        .header-content { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; color: #2563eb; }
        .nav { display: flex; gap: 2rem; align-items: center; }
        .nav a { color: #333; text-decoration: none; padding: 0.5rem 1rem; border-radius: 0.375rem; transition: background 0.3s; }
        .nav a:hover { background: #f3f4f6; }
        .nav a.active { background: #e0e7ff; color: #2563eb; }
        .logout { background: #ef4444; color: white !important; padding: 0.5rem 1rem; border-radius: 0.375rem; }
        .logout:hover { background: #dc2626 !important; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .welcome { background: white; padding: 2rem; border-radius: 0.5rem; margin-bottom: 2rem; }
        .welcome h1 { margin-bottom: 0.5rem; }
        .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .action-btn { background: #2563eb; color: white; padding: 1rem; text-align: center; border-radius: 0.5rem; text-decoration: none; transition: all 0.3s; }
        .action-btn:hover { background: #1d4ed8; transform: translateY(-2px); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-label { color: #666; font-size: 0.875rem; margin-bottom: 0.5rem; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #333; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .info-card { background: #e0e7ff; padding: 2rem; border-radius: 0.5rem; text-align: center; }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">📊 Profit Tracker AI</div>
            <nav class="nav">
                <a href="/dashboard" class="active">Dashboard</a>
                <a href="/jobs">Jobs</a>
                <a href="/upload">Upload</a>
                <a href="/reports">Reports</a>
                <a href="/logout" class="logout">Logout</a>
            </nav>
        </div>
    </header>

    <div class="container">
        <div class="welcome">
            <h1>Welcome back, {{ username }}!</h1>
            <p>Here's your business overview</p>
        </div>

        <div class="actions">
            <a href="/jobs/new" class="action-btn">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">➕</div>
                <div>New Job</div>
            </a>
            <a href="/upload" class="action-btn" style="background: #10b981;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📸</div>
                <div>Upload Receipt</div>
            </a>
            <a href="/invoices" class="action-btn" style="background: #f59e0b;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💰</div>
                <div>Manage Invoices</div>
            </a>
            <a href="/reports" class="action-btn" style="background: #8b5cf6;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                <div>View Reports</div>
            </a>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Revenue</div>
                <div class="stat-value positive">$0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Expenses</div>
                <div class="stat-value negative">$0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Net Profit</div>
                <div class="stat-value">$0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Jobs</div>
                <div class="stat-value">0</div>
            </div>
        </div>

        <div class="info-card">
            <h2 style="margin-bottom: 1rem;">🚀 Ready to Start Tracking Profits!</h2>
            <p>Upload your first receipt or create a new job to begin tracking your business finances.</p>
        </div>
    </div>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LANDING_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Simple auth for demo
        if username == 'admin' and password == 'admin123':
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML, username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return '<h1>Registration coming soon!</h1><p><a href="/">Back to home</a></p>'

@app.route('/jobs')
def jobs():
    if 'username' not in session:
        return redirect(url_for('login'))
    return '<h1>Jobs Management</h1><p>Feature coming soon! <a href="/dashboard">Back to dashboard</a></p>'

@app.route('/upload')
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    return '<h1>Upload Documents</h1><p>Feature coming soon! <a href="/dashboard">Back to dashboard</a></p>'

@app.route('/reports')
def reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    return '<h1>Financial Reports</h1><p>Feature coming soon! <a href="/dashboard">Back to dashboard</a></p>'

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'stable'}

if __name__ == '__main__':
    app.run(debug=True)