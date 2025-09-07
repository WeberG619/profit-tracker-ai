import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'profit-tracker-secret-2024')

# Store data in memory
users = {'admin': 'admin123'}
documents = []
jobs = []

def create_page(title, content, show_nav=False):
    """Helper to create consistent pages"""
    nav_html = '''
    <nav style="display: flex; gap: 20px;">
        <a href="/dashboard" style="color: white; text-decoration: none;">Dashboard</a>
        <a href="/jobs" style="color: white; text-decoration: none;">Jobs</a>
        <a href="/documents" style="color: white; text-decoration: none;">Documents</a>
        <a href="/upload" style="color: white; text-decoration: none;">Upload</a>
        <a href="/logout" style="color: white; text-decoration: none; background: #dc3545; padding: 5px 15px; border-radius: 5px;">Logout</a>
    </nav>
    ''' if show_nav else ''
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Profit Tracker AI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, Arial, sans-serif; background: #f5f5f5; color: #333; }}
        header {{ background: #1a1a1a; color: white; padding: 1rem 0; }}
        .header-content {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.5rem; font-weight: bold; }}
        main {{ max-width: 1200px; margin: 2rem auto; padding: 0 20px; }}
        .card {{ background: white; border-radius: 10px; padding: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
        .btn {{ display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }}
        .btn:hover {{ background: #0056b3; }}
        .form-group {{ margin-bottom: 1.5rem; }}
        label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        input, select, textarea {{ width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }}
        .hero {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4rem 2rem; text-align: center; border-radius: 10px; margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="logo">📊 Profit Tracker AI</div>
            {nav_html}
        </div>
    </header>
    <main>
        {content}
    </main>
</body>
</html>
    '''

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return create_page('404 Not Found', '<h1>Page not found</h1><p><a href="/">Go home</a></p>')

@app.errorhandler(500)
def server_error(e):
    import traceback
    error_msg = traceback.format_exc()
    app.logger.error(f'Server Error: {error_msg}')
    # In production, show a simple error message
    if os.environ.get('RENDER'):
        return create_page('Error', '<h1>Something went wrong</h1><p><a href="/">Go home</a></p>')
    # In development, show the full error
    return f'<pre>{error_msg}</pre>', 500

@app.route('/')
def index():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    
    content = '''
        <div class="hero">
            <h1>Stop Losing Money on Every Job</h1>
            <p style="font-size: 1.25rem; margin-bottom: 2rem;">AI-powered profit tracking for contractors.</p>
            <a href="/login" class="btn" style="font-size: 1.125rem; padding: 1rem 2rem;">Get Started</a>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">67%</div>
                <div>of contractors don't track costs properly</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$4,800</div>
                <div>average monthly loss from underpricing</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">23%</div>
                <div>profit increase with proper tracking</div>
            </div>
        </div>
    '''
    return render_template_string(create_page('Home', content))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
    
    content = '''
        <div class="card" style="max-width: 400px; margin: 0 auto;">
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
    '''
    return render_template_string(create_page('Login', content))

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
    
    content = f'''
        <h1>Welcome back, {session['username']}!</h1>
        <div class="stats-grid">
            <div class="stat-card">
                <div>Total Jobs</div>
                <div class="stat-value">{len(jobs)}</div>
            </div>
            <div class="stat-card">
                <div>Documents</div>
                <div class="stat-value">{len(documents)}</div>
            </div>
            <div class="stat-card">
                <div>Revenue</div>
                <div class="stat-value" style="color: green;">${total_revenue:,.2f}</div>
            </div>
            <div class="stat-card">
                <div>Expenses</div>
                <div class="stat-value" style="color: red;">${total_expenses:,.2f}</div>
            </div>
        </div>
        <div class="card">
            <h2>Quick Actions</h2>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <a href="/upload" class="btn">Upload Document</a>
                <a href="/jobs/new" class="btn">New Job</a>
                <a href="/documents" class="btn">View Documents</a>
            </div>
        </div>
    '''
    return render_template_string(create_page('Dashboard', content, show_nav=True))

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
        return redirect(url_for('dashboard'))
    
    job_options = ''.join([f'<option value="{job["id"]}">{job["name"]}</option>' for job in jobs])
    
    content = f'''
        <div class="card">
            <h1>Upload Document</h1>
            <form method="POST">
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
                        {job_options}
                    </select>
                </div>
                <div class="form-group">
                    <label>Vendor/Customer</label>
                    <input type="text" name="vendor" required>
                </div>
                <div class="form-group">
                    <label>Amount</label>
                    <input type="number" name="amount" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Date</label>
                    <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="3"></textarea>
                </div>
                <button type="submit" class="btn">Save Document</button>
            </form>
        </div>
    '''
    return render_template_string(create_page('Upload', content, show_nav=True))

@app.route('/jobs')
def jobs_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    rows = ''
    for job in jobs:
        expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        profit = job['quoted_price'] - expenses
        margin = round((profit / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0, 1)
        
        rows += f'''
        <tr>
            <td>{job['number']}</td>
            <td>{job['customer']}</td>
            <td>${job['quoted_price']:,.2f}</td>
            <td>${expenses:,.2f}</td>
            <td style="color: {'green' if profit > 0 else 'red'}">${profit:,.2f}</td>
            <td>{margin}%</td>
        </tr>
        '''
    
    content = f'''
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <h1>Jobs</h1>
                <a href="/jobs/new" class="btn">+ New Job</a>
            </div>
            {'<p>No jobs yet. Create your first job!</p>' if not jobs else f'''
            <table>
                <thead>
                    <tr>
                        <th>Job #</th>
                        <th>Customer</th>
                        <th>Quoted</th>
                        <th>Expenses</th>
                        <th>Profit</th>
                        <th>Margin</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            '''}
        </div>
    '''
    return render_template_string(create_page('Jobs', content, show_nav=True))

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
        return redirect(url_for('jobs_page'))
    
    content = '''
        <div class="card">
            <h1>Create New Job</h1>
            <form method="POST">
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
                <button type="submit" class="btn">Create Job</button>
            </form>
        </div>
    '''
    return render_template_string(create_page('New Job', content, show_nav=True))

@app.route('/documents')
def documents_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    rows = ''
    for doc in documents:
        color = 'green' if doc['type'] == 'income' else 'red'
        sign = '+' if doc['type'] == 'income' else '-'
        rows += f'''
        <tr>
            <td>{doc['date']}</td>
            <td>{doc['type'].title()}</td>
            <td>{doc['vendor']}</td>
            <td>{doc.get('description', '-')}</td>
            <td style="color: {color}">{sign}${doc['amount']:,.2f}</td>
        </tr>
        '''
    
    content = f'''
        <div class="card">
            <h1>Documents</h1>
            {'<p>No documents uploaded yet.</p>' if not documents else f'''
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
                    {rows}
                </tbody>
            </table>
            '''}
        </div>
    '''
    return render_template_string(create_page('Documents', content, show_nav=True))

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': 'profit-tracker-ai',
        'version': '1.0.0'
    })

@app.route('/test')
def test():
    return 'App is working!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Profit Tracker AI on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)