import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'profit-tracker-secret-2024')

# Add error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template_string('<h1>404 - Page not found</h1><p><a href="/">Go home</a></p>'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f'Server Error: {e}')
    return render_template_string('<h1>500 - Internal Server Error</h1><p>Something went wrong. <a href="/">Go home</a></p>'), 500

# Store data in memory for now (will be reset on restart)
users = {'admin': 'admin123'}
documents = []
jobs = []

# Templates
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Profit Tracker AI{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }
        
        /* Header */
        header { background: #1a1a1a; color: white; padding: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header-content { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; display: flex; align-items: center; gap: 10px; }
        nav a { color: white; text-decoration: none; padding: 0.5rem 1rem; margin: 0 5px; border-radius: 5px; transition: background 0.3s; }
        nav a:hover { background: rgba(255,255,255,0.1); }
        .btn-logout { background: #dc3545; }
        .btn-logout:hover { background: #c82333; }
        
        /* Main Content */
        main { max-width: 1200px; margin: 2rem auto; padding: 0 20px; }
        
        /* Cards */
        .card { background: white; border-radius: 10px; padding: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        
        /* Buttons */
        .btn { display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; font-size: 1rem; transition: background 0.3s; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .btn-warning { background: #ffc107; color: #333; }
        .btn-warning:hover { background: #e0a800; }
        
        /* Forms */
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        input, select, textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #007bff; }
        
        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-value { font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }
        .stat-label { color: #666; font-size: 0.875rem; }
        
        /* Tables */
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        
        /* Hero */
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4rem 2rem; text-align: center; border-radius: 10px; margin-bottom: 2rem; }
        .hero h1 { font-size: 2.5rem; margin-bottom: 1rem; }
        
        /* Flash Messages */
        .flash { padding: 1rem; border-radius: 5px; margin-bottom: 1rem; }
        .flash-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .flash-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        
        /* Actions */
        .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .action-card { background: white; padding: 2rem; border-radius: 10px; text-align: center; text-decoration: none; color: #333; transition: transform 0.3s, box-shadow 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .action-card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .action-icon { font-size: 3rem; margin-bottom: 1rem; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header-content { flex-direction: column; gap: 1rem; }
            .stats-grid { grid-template-columns: 1fr; }
            .hero h1 { font-size: 2rem; }
        }
    </style>
    {% block extra_style %}{% endblock %}
</head>
<body>
    {% if session.get('username') %}
    <header>
        <div class="header-content">
            <div class="logo">
                📊 Profit Tracker AI
            </div>
            <nav>
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                <a href="{{ url_for('jobs_page') }}">Jobs</a>
                <a href="{{ url_for('documents_page') }}">Documents</a>
                <a href="{{ url_for('upload') }}">Upload</a>
                <a href="{{ url_for('logout') }}" class="btn-logout">Logout</a>
            </nav>
        </div>
    </header>
    {% endif %}
    
    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>
    
    {% block script %}{% endblock %}
</body>
</html>
'''

INDEX_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Profit Tracker AI - Home{% endblock %}
{% block content %}
<div class="hero">
    <h1>Stop Losing Money on Every Job</h1>
    <p style="font-size: 1.25rem; margin-bottom: 2rem;">AI-powered profit tracking for contractors. Know your true margins instantly.</p>
    <a href="{{ url_for('login') }}" class="btn" style="font-size: 1.125rem; padding: 1rem 2rem;">Get Started</a>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">67%</div>
        <div class="stat-label">of contractors don't track costs properly</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">$4,800</div>
        <div class="stat-label">average monthly loss from underpricing</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">23%</div>
        <div class="stat-label">profit increase with proper tracking</div>
    </div>
</div>

<div class="card">
    <h2 style="text-align: center; margin-bottom: 2rem;">Everything You Need to Maximize Profits</h2>
    <div class="actions">
        <div class="action-card">
            <div class="action-icon">📸</div>
            <h3>Instant Receipt Scanning</h3>
            <p>Upload photos, AI extracts all data automatically</p>
        </div>
        <div class="action-card">
            <div class="action-icon">💼</div>
            <h3>Job Profit Tracking</h3>
            <p>See real-time profit margins on every job</p>
        </div>
        <div class="action-card">
            <div class="action-icon">📊</div>
            <h3>Smart Reports</h3>
            <p>Monthly P&L, expense breakdowns, trends</p>
        </div>
        <div class="action-card">
            <div class="action-icon">💰</div>
            <h3>Invoice Management</h3>
            <p>Track what's owed, never miss payments</p>
        </div>
    </div>
</div>
{% endblock %}
'''

LOGIN_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Login - Profit Tracker AI{% endblock %}
{% block content %}
<div class="card" style="max-width: 400px; margin: 4rem auto;">
    <h2 style="text-align: center; margin-bottom: 2rem;">Welcome Back</h2>
    <form method="POST">
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required autofocus>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn" style="width: 100%;">Sign In</button>
    </form>
    
    <div style="background: #e3f2fd; padding: 1rem; border-radius: 5px; margin-top: 2rem; text-align: center;">
        <strong>Demo Account</strong><br>
        Username: admin<br>
        Password: admin123
    </div>
</div>
{% endblock %}
'''

DASHBOARD_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Dashboard - Profit Tracker AI{% endblock %}
{% block content %}
<h1 style="margin-bottom: 2rem;">Welcome back, {{ session.username }}!</h1>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-label">Total Jobs</div>
        <div class="stat-value">{{ jobs|length }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Documents Uploaded</div>
        <div class="stat-value">{{ documents|length }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Total Revenue</div>
        <div class="stat-value" style="color: #28a745;">${{ total_revenue }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Total Expenses</div>
        <div class="stat-value" style="color: #dc3545;">${{ total_expenses }}</div>
    </div>
</div>

<div class="actions">
    <a href="{{ url_for('new_job') }}" class="action-card">
        <div class="action-icon">➕</div>
        <h3>New Job</h3>
        <p>Create a new job entry</p>
    </a>
    <a href="{{ url_for('upload') }}" class="action-card">
        <div class="action-icon">📸</div>
        <h3>Upload Document</h3>
        <p>Add receipt or invoice</p>
    </a>
    <a href="{{ url_for('documents_page') }}" class="action-card">
        <div class="action-icon">📄</div>
        <h3>View Documents</h3>
        <p>See all uploaded files</p>
    </a>
    <a href="{{ url_for('jobs_page') }}" class="action-card">
        <div class="action-icon">💼</div>
        <h3>Manage Jobs</h3>
        <p>Track job profitability</p>
    </a>
</div>

<div class="card">
    <h2>Recent Activity</h2>
    {% if documents %}
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Vendor/Customer</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
            {% for doc in documents[:5] %}
            <tr>
                <td>{{ doc.date }}</td>
                <td>{{ doc.type }}</td>
                <td>{{ doc.vendor }}</td>
                <td style="color: {{ 'green' if doc.type == 'income' else 'red' }}">
                    {{ '+' if doc.type == 'income' else '-' }}${{ doc.amount }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="text-align: center; color: #666; padding: 2rem;">No documents uploaded yet. Start by uploading your first receipt!</p>
    {% endif %}
</div>
{% endblock %}
'''

UPLOAD_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Upload Document - Profit Tracker AI{% endblock %}
{% block content %}
<div class="card">
    <h1>Upload Document</h1>
    <form method="POST" style="max-width: 600px;">
        <div class="form-group">
            <label>Document Type</label>
            <select name="doc_type" required>
                <option value="expense">Expense Receipt</option>
                <option value="income">Income Invoice</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>Job</label>
            <select name="job_id">
                <option value="">No specific job</option>
                {% for job in jobs %}
                <option value="{{ job.id }}">{{ job.name }} - {{ job.customer }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Vendor/Customer Name</label>
            <input type="text" name="vendor" required>
        </div>
        
        <div class="form-group">
            <label>Amount</label>
            <input type="number" name="amount" step="0.01" required>
        </div>
        
        <div class="form-group">
            <label>Date</label>
            <input type="date" name="date" value="{{ today }}" required>
        </div>
        
        <div class="form-group">
            <label>Description</label>
            <textarea name="description" rows="3"></textarea>
        </div>
        
        <button type="submit" class="btn btn-success">Save Document</button>
        <a href="{{ url_for('dashboard') }}" class="btn" style="background: #6c757d;">Cancel</a>
    </form>
</div>
{% endblock %}
'''

JOBS_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Jobs - Profit Tracker AI{% endblock %}
{% block content %}
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h1>Jobs</h1>
        <a href="{{ url_for('new_job') }}" class="btn btn-success">+ New Job</a>
    </div>
    
    {% if jobs %}
    <table>
        <thead>
            <tr>
                <th>Job #</th>
                <th>Customer</th>
                <th>Quoted</th>
                <th>Expenses</th>
                <th>Profit</th>
                <th>Margin</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for job in jobs %}
            <tr>
                <td>{{ job.number }}</td>
                <td>{{ job.customer }}</td>
                <td>${{ job.quoted_price }}</td>
                <td>${{ job.expenses }}</td>
                <td style="color: {{ 'green' if job.profit > 0 else 'red' }}">${{ job.profit }}</td>
                <td>{{ job.margin }}%</td>
                <td>{{ job.status }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="text-align: center; color: #666; padding: 2rem;">No jobs created yet. Create your first job to start tracking profitability!</p>
    {% endif %}
</div>
{% endblock %}
'''

NEW_JOB_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}New Job - Profit Tracker AI{% endblock %}
{% block content %}
<div class="card">
    <h1>Create New Job</h1>
    <form method="POST" style="max-width: 600px;">
        <div class="form-group">
            <label>Job Number</label>
            <input type="text" name="number" required placeholder="e.g., JOB-001">
        </div>
        
        <div class="form-group">
            <label>Customer Name</label>
            <input type="text" name="customer" required>
        </div>
        
        <div class="form-group">
            <label>Job Description</label>
            <textarea name="description" rows="3" required></textarea>
        </div>
        
        <div class="form-group">
            <label>Quoted Price</label>
            <input type="number" name="quoted_price" step="0.01" required>
        </div>
        
        <button type="submit" class="btn btn-success">Create Job</button>
        <a href="{{ url_for('jobs_page') }}" class="btn" style="background: #6c757d;">Cancel</a>
    </form>
</div>
{% endblock %}
'''

# Routes
@app.route('/')
def index():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return render_template_string(BASE_TEMPLATE + INDEX_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template_string(BASE_TEMPLATE + LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    total_revenue = sum(d['amount'] for d in documents if d['type'] == 'income')
    total_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense')
    
    return render_template_string(BASE_TEMPLATE + DASHBOARD_TEMPLATE,
                                jobs=jobs,
                                documents=documents,
                                total_revenue=f"{total_revenue:,.2f}",
                                total_expenses=f"{total_expenses:,.2f}")

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doc = {
            'id': len(documents) + 1,
            'type': request.form.get('doc_type'),
            'vendor': request.form.get('vendor'),
            'amount': float(request.form.get('amount')),
            'date': request.form.get('date'),
            'description': request.form.get('description'),
            'job_id': request.form.get('job_id')
        }
        documents.append(doc)
        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template_string(BASE_TEMPLATE + UPLOAD_TEMPLATE,
                                jobs=jobs,
                                today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/jobs')
def jobs_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Calculate job metrics
    for job in jobs:
        job['expenses'] = sum(d['amount'] for d in documents 
                            if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        job['profit'] = job['quoted_price'] - job['expenses']
        job['margin'] = round((job['profit'] / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0, 1)
    
    return render_template_string(BASE_TEMPLATE + JOBS_TEMPLATE, jobs=jobs)

@app.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        job = {
            'id': len(jobs) + 1,
            'number': request.form.get('number'),
            'customer': request.form.get('customer'),
            'description': request.form.get('description'),
            'quoted_price': float(request.form.get('quoted_price')),
            'status': 'Active',
            'name': f"{request.form.get('number')} - {request.form.get('customer')}"
        }
        jobs.append(job)
        flash('Job created successfully!', 'success')
        return redirect(url_for('jobs_page'))
    
    return render_template_string(BASE_TEMPLATE + NEW_JOB_TEMPLATE)

@app.route('/documents')
def documents_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Simple documents list
    return render_template_string(BASE_TEMPLATE + '''
    {% extends "base.html" %}
    {% block content %}
    <div class="card">
        <h1>Documents</h1>
        {% if documents %}
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Vendor/Customer</th>
                    <th>Description</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                {% for doc in documents %}
                <tr>
                    <td>{{ doc.date }}</td>
                    <td>{{ doc.type|title }}</td>
                    <td>{{ doc.vendor }}</td>
                    <td>{{ doc.description or '-' }}</td>
                    <td style="color: {{ 'green' if doc.type == 'income' else 'red' }}">
                        {{ '+' if doc.type == 'income' else '-' }}${{ "{:,.2f}".format(doc.amount) }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="text-align: center; color: #666; padding: 2rem;">No documents uploaded yet.</p>
        {% endif %}
    </div>
    {% endblock %}
    ''', documents=documents)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': 'profit-tracker-ai',
        'version': '1.0.0',
        'environment': os.environ.get('RENDER', 'local')
    })

@app.route('/test')
def test():
    return 'App is working!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Profit Tracker AI on port {port}")
    print("Server starting...")
    app.run(host='0.0.0.0', port=port, debug=False)