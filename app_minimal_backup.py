import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'profit-tracker-secret-2024')

# Store data in memory
users = {'admin': 'admin123'}
documents = []
jobs = []

@app.route('/')
def index():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 40px; text-align: center; border-radius: 10px; margin-bottom: 40px; }
        .hero h1 { font-size: 48px; margin-bottom: 20px; }
        .hero p { font-size: 20px; margin-bottom: 30px; }
        .btn { display: inline-block; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-size: 18px; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="hero">
        <h1>Stop Losing Money on Every Job</h1>
        <p>AI-powered profit tracking for contractors.</p>
        <a href="/login" class="btn">Get Started</a>
    </div>
</body>
</html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Welcome Back</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
        <div class="info">
            <strong>Demo Account</strong><br>
            Username: admin<br>
            Password: admin123
        </div>
    </div>
</body>
</html>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    total_revenue = sum(d.get('amount', 0) for d in documents if d.get('type') == 'income')
    total_expenses = sum(d.get('amount', 0) for d in documents if d.get('type') == 'expense')
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Profit Tracker AI</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; }}
        header {{ background: #1a1a1a; color: white; padding: 15px 0; }}
        .header-content {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
        nav a {{ color: white; text-decoration: none; margin-left: 20px; }}
        nav a:hover {{ text-decoration: underline; }}
        .logout {{ background: #dc3545; padding: 8px 16px; border-radius: 5px; }}
        main {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ background: white; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .actions {{ display: flex; gap: 15px; margin-top: 30px; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        .btn:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>Profit Tracker AI</h1>
            <nav>
                <a href="/jobs">Jobs</a>
                <a href="/documents">Documents</a>
                <a href="/upload">Upload</a>
                <a href="/logout" class="logout">Logout</a>
            </nav>
        </div>
    </header>
    <main>
        <h2>Welcome back, {session.get('username')}!</h2>
        <div class="stats">
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
        <div class="actions">
            <a href="/upload" class="btn">Upload Document</a>
            <a href="/jobs/new" class="btn">New Job</a>
        </div>
    </main>
</body>
</html>
    '''

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doc = {
            'id': len(documents) + 1,
            'type': request.form.get('doc_type'),
            'vendor': request.form.get('vendor'),
            'amount': float(request.form.get('amount', 0)),
            'date': request.form.get('date'),
            'description': request.form.get('description')
        }
        documents.append(doc)
        return redirect(url_for('dashboard'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { margin-bottom: 30px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { padding: 12px 30px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload Document</h1>
        <form method="POST">
            <label>Type</label>
            <select name="doc_type" required>
                <option value="expense">Expense Receipt</option>
                <option value="income">Income Invoice</option>
            </select>
            
            <label>Vendor/Customer</label>
            <input type="text" name="vendor" required>
            
            <label>Amount</label>
            <input type="number" name="amount" step="0.01" required>
            
            <label>Date</label>
            <input type="date" name="date" required>
            
            <label>Description</label>
            <textarea name="description" rows="3"></textarea>
            
            <button type="submit">Save</button>
            <a href="/dashboard" style="margin-left: 10px;">Cancel</a>
        </form>
    </div>
</body>
</html>
    '''

@app.route('/jobs')
def jobs_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Jobs - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .btn { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .btn:hover { background: #0056b3; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Jobs</h1>
            <a href="/jobs/new" class="btn">+ New Job</a>
        </div>
        <p>No jobs yet. Create your first job!</p>
        <a href="/dashboard">← Back to Dashboard</a>
    </div>
</body>
</html>
    '''

@app.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        job = {
            'id': len(jobs) + 1,
            'number': request.form.get('number'),
            'customer': request.form.get('customer'),
            'quoted_price': float(request.form.get('quoted_price', 0))
        }
        jobs.append(job)
        return redirect(url_for('jobs_page'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>New Job - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { padding: 12px 30px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Create New Job</h1>
        <form method="POST">
            <label>Job Number</label>
            <input type="text" name="number" required>
            
            <label>Customer</label>
            <input type="text" name="customer" required>
            
            <label>Quoted Price</label>
            <input type="number" name="quoted_price" step="0.01" required>
            
            <button type="submit">Create</button>
            <a href="/jobs" style="margin-left: 10px;">Cancel</a>
        </form>
    </div>
</body>
</html>
    '''

@app.route('/documents')
def documents_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Documents - Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Documents</h1>
        <p>No documents uploaded yet.</p>
        <a href="/dashboard">← Back to Dashboard</a>
    </div>
</body>
</html>
    '''

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test():
    return 'App is working!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Profit Tracker AI on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)