import os
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, session, jsonify, make_response
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'profit-tracker-secret-2024')

# Enhanced data storage
users = {'admin': 'admin123'}
documents = []
jobs = []
invoices = []
expenses = []

# Sample data for demo
def init_sample_data():
    global jobs, documents
    
    # Sample jobs
    jobs = [
        {
            'id': 1,
            'number': 'JOB-001',
            'customer': 'Smith Construction',
            'description': 'Kitchen Renovation - Complete remodel including cabinets, countertops, and appliances',
            'quoted_price': 25000,
            'status': 'In Progress',
            'start_date': '2024-01-15',
            'estimated_end': '2024-02-15',
            'progress': 65,
            'notes': 'Cabinets installed, waiting for countertops'
        },
        {
            'id': 2,
            'number': 'JOB-002',
            'customer': 'Johnson Residence',
            'description': 'Bathroom Remodel - Master bath complete renovation',
            'quoted_price': 15000,
            'status': 'Completed',
            'start_date': '2023-12-01',
            'estimated_end': '2023-12-20',
            'progress': 100,
            'notes': 'Completed on time, customer very satisfied'
        },
        {
            'id': 3,
            'number': 'JOB-003',
            'customer': 'Davis Commercial',
            'description': 'Office Build-out - 2500 sq ft office space',
            'quoted_price': 45000,
            'status': 'Quoted',
            'start_date': '2024-03-01',
            'estimated_end': '2024-04-15',
            'progress': 0,
            'notes': 'Awaiting customer approval'
        }
    ]
    
    # Sample documents
    documents = [
        {'id': 1, 'type': 'expense', 'job_id': '1', 'vendor': 'Home Depot', 'amount': 3500, 'date': '2024-01-20', 'description': 'Kitchen cabinets', 'category': 'Materials'},
        {'id': 2, 'type': 'expense', 'job_id': '1', 'vendor': 'Lowes', 'amount': 1200, 'date': '2024-01-22', 'description': 'Plumbing fixtures', 'category': 'Materials'},
        {'id': 3, 'type': 'income', 'job_id': '1', 'vendor': 'Smith Construction', 'amount': 12500, 'date': '2024-01-15', 'description': '50% deposit', 'category': 'Payment'},
        {'id': 4, 'type': 'expense', 'job_id': '2', 'vendor': 'Tile Shop', 'amount': 2800, 'date': '2023-12-05', 'description': 'Bathroom tiles and grout', 'category': 'Materials'},
        {'id': 5, 'type': 'expense', 'job_id': '2', 'vendor': 'Subcontractor - Mike', 'amount': 3000, 'date': '2023-12-10', 'description': 'Plumbing work', 'category': 'Labor'},
        {'id': 6, 'type': 'income', 'job_id': '2', 'vendor': 'Johnson Residence', 'amount': 15000, 'date': '2023-12-20', 'description': 'Final payment', 'category': 'Payment'},
    ]

init_sample_data()

def create_base_template(title, content, show_nav=True):
    nav_html = '''
        <nav class="main-nav">
            <a href="/dashboard" class="nav-link"><i class="icon">📊</i> Dashboard</a>
            <a href="/jobs" class="nav-link"><i class="icon">💼</i> Jobs</a>
            <a href="/invoices" class="nav-link"><i class="icon">💰</i> Invoices</a>
            <a href="/expenses" class="nav-link"><i class="icon">📁</i> Expenses</a>
            <a href="/reports" class="nav-link"><i class="icon">📈</i> Reports</a>
            <a href="/upload" class="nav-link upload-btn"><i class="icon">📸</i> Quick Upload</a>
        </nav>
        <div class="user-menu">
            <span class="username">👤 {}</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    '''.format(session.get('username', 'User')) if show_nav else ''
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Profit Tracker AI</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #1e293b;
            --light: #f8fafc;
            --border: #e2e8f0;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--light);
            color: var(--dark);
            line-height: 1.6;
        }}
        
        /* Header */
        .header {{
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .main-nav {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}
        
        .nav-link {{
            padding: 0.5rem 1rem;
            color: var(--secondary);
            text-decoration: none;
            border-radius: 0.5rem;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .nav-link:hover {{
            background: var(--light);
            color: var(--primary);
        }}
        
        .upload-btn {{
            background: var(--primary);
            color: white;
        }}
        
        .upload-btn:hover {{
            background: var(--primary-dark);
            color: white;
        }}
        
        .user-menu {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .logout-btn {{
            padding: 0.5rem 1rem;
            background: var(--danger);
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            transition: background 0.2s;
        }}
        
        .logout-btn:hover {{
            background: #dc2626;
        }}
        
        /* Main Content */
        .container {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        /* Cards */
        .card {{
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        
        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--dark);
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary);
        }}
        
        .stat-card.success {{ border-left-color: var(--success); }}
        .stat-card.danger {{ border-left-color: var(--danger); }}
        .stat-card.warning {{ border-left-color: var(--warning); }}
        
        .stat-label {{
            font-size: 0.875rem;
            color: var(--secondary);
            margin-bottom: 0.5rem;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--dark);
        }}
        
        .stat-change {{
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}
        
        .stat-change.positive {{ color: var(--success); }}
        .stat-change.negative {{ color: var(--danger); }}
        
        /* Tables */
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background: var(--light);
            font-weight: 600;
            color: var(--secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
        }}
        
        tr:hover {{
            background: var(--light);
        }}
        
        /* Status Badges */
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-block;
        }}
        
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-warning {{ background: #fed7aa; color: #92400e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-info {{ background: #dbeafe; color: #1e40af; }}
        
        /* Progress Bar */
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        
        .progress-fill {{
            height: 100%;
            background: var(--primary);
            transition: width 0.3s ease;
        }}
        
        /* Buttons */
        .btn {{
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.5rem;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: white;
        }}
        
        .btn-primary:hover {{
            background: var(--primary-dark);
        }}
        
        .btn-secondary {{
            background: var(--secondary);
            color: white;
        }}
        
        .btn-success {{
            background: var(--success);
            color: white;
        }}
        
        .btn-danger {{
            background: var(--danger);
            color: white;
        }}
        
        /* Forms */
        .form-group {{
            margin-bottom: 1.5rem;
        }}
        
        label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
        }}
        
        input, select, textarea {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 1rem;
            transition: border-color 0.2s;
        }}
        
        input:focus, select:focus, textarea:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        
        /* Action Menu */
        .action-menu {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .action-card {{
            flex: 1;
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
            text-decoration: none;
            color: var(--dark);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .action-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .action-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .action-title {{
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        
        .action-desc {{
            font-size: 0.875rem;
            color: var(--secondary);
        }}
        
        /* Charts Placeholder */
        .chart-container {{
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--secondary);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                gap: 1rem;
            }}
            
            .main-nav {{
                flex-wrap: wrap;
                justify-content: center;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .action-menu {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                <span>📊</span>
                <span>Profit Tracker AI</span>
            </a>
            {nav_html}
        </div>
    </header>
    
    <div class="container">
        {content}
    </div>
    
    <script>
        // Add active state to current page
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {{
            if (link.getAttribute('href') === currentPath) {{
                link.style.background = '#eff6ff';
                link.style.color = '#2563eb';
            }}
        }});
    </script>
</body>
</html>
    '''

@app.route('/')
def index():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Profit Tracker AI - Smart Financial Management for Contractors</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, Arial, sans-serif; background: #f8fafc; }
        
        .hero {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .hero p {
            font-size: 1.5rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }
        
        .cta-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 3rem;
        }
        
        .btn {
            padding: 1rem 2rem;
            font-size: 1.125rem;
            border-radius: 0.5rem;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .btn:hover { transform: translateY(-2px); }
        
        .btn-primary {
            background: white;
            color: #2563eb;
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
        }
        
        .features {
            max-width: 1200px;
            margin: -60px auto 60px;
            padding: 0 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }
        
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #1e293b;
        }
        
        .feature-desc {
            color: #64748b;
            line-height: 1.6;
        }
        
        .stats-section {
            background: white;
            padding: 60px 20px;
            text-align: center;
        }
        
        .stats-grid {
            max-width: 900px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 3rem;
        }
        
        .stat {
            font-size: 3rem;
            font-weight: 700;
            color: #2563eb;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 1.125rem;
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .hero p { font-size: 1.125rem; }
            .cta-buttons { flex-direction: column; align-items: center; }
        }
    </style>
</head>
<body>
    <div class="hero">
        <h1>Stop Losing Money on Every Job</h1>
        <p>AI-powered financial tracking built specifically for contractors</p>
        <div class="cta-buttons">
            <a href="/login" class="btn btn-primary">Start Free Trial</a>
            <a href="#features" class="btn btn-secondary">See How It Works</a>
        </div>
    </div>
    
    <div class="features" id="features">
        <div class="feature-card">
            <div class="feature-icon">📸</div>
            <div class="feature-title">Instant Receipt Capture</div>
            <div class="feature-desc">Snap a photo, AI extracts all data automatically. No more manual entry or lost receipts.</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">💼</div>
            <div class="feature-title">Job Profit Tracking</div>
            <div class="feature-desc">See real-time profit margins on every job. Know exactly where you make and lose money.</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Smart Reports</div>
            <div class="feature-desc">Monthly P&L, expense breakdowns, and trend analysis. Make data-driven decisions.</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <div class="feature-title">Invoice Management</div>
            <div class="feature-desc">Track what's owed, send reminders, and never miss a payment again.</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📱</div>
            <div class="feature-title">Mobile Ready</div>
            <div class="feature-desc">Access everything from your phone. Perfect for contractors on the go.</div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">Secure & Private</div>
            <div class="feature-desc">Bank-level encryption keeps your financial data safe and confidential.</div>
        </div>
    </div>
    
    <div class="stats-section">
        <div class="stats-grid">
            <div>
                <div class="stat">23%</div>
                <div class="stat-label">Average profit increase</div>
            </div>
            <div>
                <div class="stat">4.8hrs</div>
                <div class="stat-label">Saved per week</div>
            </div>
            <div>
                <div class="stat">$4,800</div>
                <div class="stat-label">Found in missed expenses</div>
            </div>
        </div>
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, Arial, sans-serif; 
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        
        .login-container {
            background: white;
            padding: 3rem;
            border-radius: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo-icon { font-size: 3rem; }
        
        h2 {
            text-align: center;
            margin-bottom: 2rem;
            color: #1e293b;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #475569;
        }
        
        input {
            width: 100%;
            padding: 0.875rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        
        input:focus {
            outline: none;
            border-color: #2563eb;
        }
        
        button {
            width: 100%;
            padding: 0.875rem;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #1e40af;
        }
        
        .demo-info {
            background: #eff6ff;
            border: 1px solid #dbeafe;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 2rem;
            text-align: center;
            font-size: 0.875rem;
        }
        
        .demo-info strong { color: #1e40af; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">📊</div>
        </div>
        <h2>Welcome Back</h2>
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
        <div class="demo-info">
            <strong>Demo Account</strong><br>
            Username: admin<br>
            Password: admin123
        </div>
    </div>
</body>
</html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Calculate metrics
    total_revenue = sum(d['amount'] for d in documents if d['type'] == 'income')
    total_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense')
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Active jobs
    active_jobs = [j for j in jobs if j['status'] == 'In Progress']
    completed_jobs = [j for j in jobs if j['status'] == 'Completed']
    
    # Recent activity
    recent_docs = sorted(documents, key=lambda x: x['date'], reverse=True)[:5]
    
    content = f'''
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value" style="color: var(--success);">${total_revenue:,.2f}</div>
            <div class="stat-change positive">↑ 12% from last month</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Total Expenses</div>
            <div class="stat-value" style="color: var(--danger);">${total_expenses:,.2f}</div>
            <div class="stat-change negative">↑ 5% from last month</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Net Profit</div>
            <div class="stat-value">${net_profit:,.2f}</div>
            <div class="stat-change positive">↑ 18% from last month</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Profit Margin</div>
            <div class="stat-value">{profit_margin:.1f}%</div>
            <div class="stat-change positive">↑ 2.3% from last month</div>
        </div>
    </div>
    
    <div class="action-menu">
        <a href="/upload" class="action-card">
            <div class="action-icon">📸</div>
            <div class="action-title">Quick Capture</div>
            <div class="action-desc">Upload receipt or invoice</div>
        </a>
        
        <a href="/jobs/new" class="action-card">
            <div class="action-icon">➕</div>
            <div class="action-title">New Job</div>
            <div class="action-desc">Start tracking a new project</div>
        </a>
        
        <a href="/invoices/new" class="action-card">
            <div class="action-icon">💵</div>
            <div class="action-title">Create Invoice</div>
            <div class="action-desc">Bill your customers</div>
        </a>
        
        <a href="/reports" class="action-card">
            <div class="action-icon">📊</div>
            <div class="action-title">View Reports</div>
            <div class="action-desc">Analyze your business</div>
        </a>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Active Jobs</h2>
                <a href="/jobs" class="btn btn-primary">View All</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Job #</th>
                            <th>Customer</th>
                            <th>Progress</th>
                            <th>Profit</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    for job in active_jobs[:3]:
        job_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        job_revenue = sum(d['amount'] for d in documents if d['type'] == 'income' and d.get('job_id') == str(job['id']))
        job_profit = job_revenue - job_expenses
        
        content += f'''
                        <tr>
                            <td>{job['number']}</td>
                            <td>{job['customer']}</td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <span style="font-size: 0.875rem;">{job['progress']}%</span>
                                    <div class="progress-bar" style="flex: 1;">
                                        <div class="progress-fill" style="width: {job['progress']}%;"></div>
                                    </div>
                                </div>
                            </td>
                            <td style="color: {'var(--success)' if job_profit >= 0 else 'var(--danger)'};">${job_profit:,.2f}</td>
                        </tr>
        '''
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Recent Activity</h2>
                <a href="/documents" class="btn btn-secondary">View All</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    for doc in recent_docs:
        color = 'var(--success)' if doc['type'] == 'income' else 'var(--danger)'
        sign = '+' if doc['type'] == 'income' else '-'
        content += f'''
                        <tr>
                            <td>{doc['date']}</td>
                            <td>{doc['description']}</td>
                            <td style="color: {color};">{sign}${doc['amount']:,.2f}</td>
                        </tr>
        '''
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Revenue vs Expenses (Last 12 Months)</h2>
        </div>
        <div class="chart-container">
            <p>📈 Interactive chart coming soon - Revenue trending up 23% YoY</p>
        </div>
    </div>
    '''
    
    return create_base_template('Dashboard', content)

@app.route('/jobs')
def jobs_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    content = '''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Jobs Management</h2>
            <a href="/jobs/new" class="btn btn-primary">+ New Job</a>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Job #</th>
                        <th>Customer</th>
                        <th>Description</th>
                        <th>Quote</th>
                        <th>Expenses</th>
                        <th>Profit</th>
                        <th>Status</th>
                        <th>Progress</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    for job in jobs:
        job_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        job_revenue = sum(d['amount'] for d in documents if d['type'] == 'income' and d.get('job_id') == str(job['id']))
        job_profit = job_revenue - job_expenses
        profit_margin = (job_profit / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0
        
        status_class = {
            'Quoted': 'badge-info',
            'In Progress': 'badge-warning',
            'Completed': 'badge-success'
        }.get(job['status'], 'badge-secondary')
        
        content += f'''
                    <tr>
                        <td><strong>{job['number']}</strong></td>
                        <td>{job['customer']}</td>
                        <td>{job['description'][:50]}...</td>
                        <td>${job['quoted_price']:,.2f}</td>
                        <td>${job_expenses:,.2f}</td>
                        <td style="color: {'var(--success)' if job_profit >= 0 else 'var(--danger)'};">
                            ${job_profit:,.2f} ({profit_margin:.1f}%)
                        </td>
                        <td><span class="badge {status_class}">{job['status']}</span></td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {job['progress']}%;"></div>
                            </div>
                            <small>{job['progress']}%</small>
                        </td>
                        <td>
                            <a href="/jobs/{job['id']}" class="btn btn-secondary" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">View</a>
                        </td>
                    </tr>
        '''
    
    content += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return create_base_template('Jobs', content)

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
            'quoted_price': float(request.form.get('quoted_price', 0)),
            'status': request.form.get('status', 'Quoted'),
            'start_date': request.form.get('start_date'),
            'estimated_end': request.form.get('estimated_end'),
            'progress': 0,
            'notes': request.form.get('notes', '')
        }
        jobs.append(job)
        return redirect(url_for('jobs_page'))
    
    content = '''
    <div class="card" style="max-width: 800px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Create New Job</h2>
        </div>
        
        <form method="POST">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div class="form-group">
                    <label>Job Number*</label>
                    <input type="text" name="number" required placeholder="JOB-004">
                </div>
                
                <div class="form-group">
                    <label>Customer Name*</label>
                    <input type="text" name="customer" required placeholder="John Smith">
                </div>
                
                <div class="form-group" style="grid-column: 1 / -1;">
                    <label>Job Description*</label>
                    <textarea name="description" rows="3" required placeholder="Describe the scope of work..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>Quoted Price*</label>
                    <input type="number" name="quoted_price" step="0.01" required placeholder="25000.00">
                </div>
                
                <div class="form-group">
                    <label>Status</label>
                    <select name="status">
                        <option value="Quoted">Quoted</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" name="start_date">
                </div>
                
                <div class="form-group">
                    <label>Estimated End Date</label>
                    <input type="date" name="estimated_end">
                </div>
                
                <div class="form-group" style="grid-column: 1 / -1;">
                    <label>Notes</label>
                    <textarea name="notes" rows="3" placeholder="Additional notes or special requirements..."></textarea>
                </div>
            </div>
            
            <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                <button type="submit" class="btn btn-primary">Create Job</button>
                <a href="/jobs" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
    '''
    
    return create_base_template('New Job', content)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doc = {
            'id': len(documents) + 1,
            'type': request.form.get('doc_type'),
            'job_id': request.form.get('job_id'),
            'vendor': request.form.get('vendor'),
            'amount': float(request.form.get('amount', 0)),
            'date': request.form.get('date'),
            'description': request.form.get('description'),
            'category': request.form.get('category')
        }
        documents.append(doc)
        return redirect(url_for('dashboard'))
    
    job_options = ''.join([f'<option value="{job["id"]}">{job["number"]} - {job["customer"]}</option>' for job in jobs])
    
    content = f'''
    <div class="card" style="max-width: 600px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Quick Document Upload</h2>
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label>Document Type*</label>
                <select name="doc_type" required onchange="updateCategories(this.value)">
                    <option value="">Select type...</option>
                    <option value="expense">Expense Receipt</option>
                    <option value="income">Income/Invoice</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Job (Optional)</label>
                <select name="job_id">
                    <option value="">No specific job</option>
                    {job_options}
                </select>
            </div>
            
            <div class="form-group">
                <label>Vendor/Customer*</label>
                <input type="text" name="vendor" required placeholder="Home Depot, John Smith, etc.">
            </div>
            
            <div class="form-group">
                <label>Amount*</label>
                <input type="number" name="amount" step="0.01" required placeholder="0.00">
            </div>
            
            <div class="form-group">
                <label>Category</label>
                <select name="category" id="category-select">
                    <option value="">Select category...</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Date*</label>
                <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
            </div>
            
            <div class="form-group">
                <label>Description</label>
                <textarea name="description" rows="3" placeholder="What was this for?"></textarea>
            </div>
            
            <div class="form-group" style="background: var(--light); padding: 1rem; border-radius: 0.5rem;">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="file" accept="image/*" style="display: none;">
                    <span class="btn btn-secondary">📸 Upload Photo</span>
                    <span style="color: var(--secondary);">Coming soon - AI receipt scanning</span>
                </label>
            </div>
            
            <button type="submit" class="btn btn-primary" style="width: 100%;">Save Document</button>
        </form>
    </div>
    
    <script>
    function updateCategories(type) {{
        const categorySelect = document.getElementById('category-select');
        categorySelect.innerHTML = '<option value="">Select category...</option>';
        
        const categories = {{
            expense: ['Materials', 'Labor', 'Equipment', 'Fuel', 'Office', 'Insurance', 'Other'],
            income: ['Payment', 'Deposit', 'Final Payment', 'Change Order', 'Other']
        }};
        
        if (type && categories[type]) {{
            categories[type].forEach(cat => {{
                categorySelect.innerHTML += `<option value="${{cat}}">${{cat}}</option>`;
            }});
        }}
    }}
    </script>
    '''
    
    return create_base_template('Upload Document', content)

@app.route('/expenses')
def expenses_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    expense_docs = [d for d in documents if d['type'] == 'expense']
    
    # Group by category
    categories = {}
    for doc in expense_docs:
        cat = doc.get('category', 'Other')
        if cat not in categories:
            categories[cat] = {'total': 0, 'count': 0}
        categories[cat]['total'] += doc['amount']
        categories[cat]['count'] += 1
    
    content = '''
    <div class="stats-grid">
    '''
    
    for cat, data in categories.items():
        content += f'''
        <div class="stat-card">
            <div class="stat-label">{cat}</div>
            <div class="stat-value">${data['total']:,.2f}</div>
            <div class="stat-change">{data['count']} transactions</div>
        </div>
        '''
    
    content += '''
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Expense History</h2>
            <a href="/upload" class="btn btn-primary">+ Add Expense</a>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Vendor</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Job</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    for doc in sorted(expense_docs, key=lambda x: x['date'], reverse=True):
        job = next((j for j in jobs if str(j['id']) == doc.get('job_id')), None)
        job_name = f"{job['number']} - {job['customer']}" if job else '-'
        
        content += f'''
                    <tr>
                        <td>{doc['date']}</td>
                        <td>{doc['vendor']}</td>
                        <td>{doc['description']}</td>
                        <td><span class="badge badge-info">{doc.get('category', 'Other')}</span></td>
                        <td>{job_name}</td>
                        <td style="color: var(--danger);">-${doc['amount']:,.2f}</td>
                    </tr>
        '''
    
    content += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return create_base_template('Expenses', content)

@app.route('/invoices')
def invoices_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    income_docs = [d for d in documents if d['type'] == 'income']
    
    content = '''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Invoices & Payments</h2>
            <a href="/invoices/new" class="btn btn-primary">+ Create Invoice</a>
        </div>
        
        <div class="stats-grid" style="margin-bottom: 2rem;">
            <div class="stat-card success">
                <div class="stat-label">Total Invoiced</div>
                <div class="stat-value">${:,.2f}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Outstanding</div>
                <div class="stat-value">$12,500</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Overdue</div>
                <div class="stat-value" style="color: var(--danger);">$3,200</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Invoice #</th>
                        <th>Date</th>
                        <th>Customer</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    '''.format(sum(d['amount'] for d in income_docs))
    
    # Add sample invoices
    invoices_list = [
        {'number': 'INV-001', 'date': '2024-01-15', 'customer': 'Smith Construction', 'desc': 'Kitchen renovation - 50% deposit', 'amount': 12500, 'status': 'Paid'},
        {'number': 'INV-002', 'date': '2024-01-20', 'customer': 'Johnson Residence', 'desc': 'Bathroom remodel - Final payment', 'amount': 15000, 'status': 'Paid'},
        {'number': 'INV-003', 'date': '2024-02-01', 'customer': 'Smith Construction', 'desc': 'Kitchen renovation - Final payment', 'amount': 12500, 'status': 'Outstanding'},
    ]
    
    for inv in invoices_list:
        status_class = 'badge-success' if inv['status'] == 'Paid' else 'badge-warning'
        
        content += f'''
                    <tr>
                        <td><strong>{inv['number']}</strong></td>
                        <td>{inv['date']}</td>
                        <td>{inv['customer']}</td>
                        <td>{inv['desc']}</td>
                        <td style="color: var(--success);">${inv['amount']:,.2f}</td>
                        <td><span class="badge {status_class}">{inv['status']}</span></td>
                        <td>
                            <button class="btn btn-secondary" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">View</button>
                        </td>
                    </tr>
        '''
    
    content += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return create_base_template('Invoices', content)

@app.route('/reports')
def reports_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    content = '''
    <div class="action-menu">
        <div class="action-card">
            <div class="action-icon">📊</div>
            <div class="action-title">Profit & Loss</div>
            <div class="action-desc">Monthly P&L statements</div>
        </div>
        
        <div class="action-card">
            <div class="action-icon">💼</div>
            <div class="action-title">Job Analysis</div>
            <div class="action-desc">Profitability by job</div>
        </div>
        
        <div class="action-card">
            <div class="action-icon">📈</div>
            <div class="action-title">Expense Trends</div>
            <div class="action-desc">Category breakdowns</div>
        </div>
        
        <div class="action-card">
            <div class="action-icon">🗓️</div>
            <div class="action-title">Tax Summary</div>
            <div class="action-desc">Year-end reports</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Quick Summary - This Month</h2>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h3 style="margin-bottom: 1rem;">Income Statement</h3>
                <table>
                    <tr>
                        <td style="padding: 0.5rem 0;"><strong>Revenue</strong></td>
                        <td style="text-align: right; padding: 0.5rem 0;">$27,500</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;">Materials</td>
                        <td style="text-align: right; padding: 0.5rem 0;">($6,300)</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;">Labor</td>
                        <td style="text-align: right; padding: 0.5rem 0;">($3,000)</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;">Other Expenses</td>
                        <td style="text-align: right; padding: 0.5rem 0;">($1,200)</td>
                    </tr>
                    <tr style="border-top: 2px solid var(--border);">
                        <td style="padding: 0.5rem 0;"><strong>Net Profit</strong></td>
                        <td style="text-align: right; padding: 0.5rem 0; color: var(--success);"><strong>$17,000</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;"><strong>Profit Margin</strong></td>
                        <td style="text-align: right; padding: 0.5rem 0;"><strong>61.8%</strong></td>
                    </tr>
                </table>
            </div>
            
            <div>
                <h3 style="margin-bottom: 1rem;">Top Performing Jobs</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Job</th>
                            <th>Profit</th>
                            <th>Margin</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>JOB-002</td>
                            <td style="color: var(--success);">$9,200</td>
                            <td>61.3%</td>
                        </tr>
                        <tr>
                            <td>JOB-001</td>
                            <td style="color: var(--success);">$7,800</td>
                            <td>62.4%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Download Reports</h2>
        </div>
        <div style="display: flex; gap: 1rem;">
            <button class="btn btn-primary">📄 Export to PDF</button>
            <button class="btn btn-secondary">📊 Export to Excel</button>
            <button class="btn btn-secondary">📧 Email Report</button>
        </div>
    </div>
    '''
    
    return create_base_template('Reports', content)

@app.route('/invoices/new')
def new_invoice():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    job_options = ''.join([f'<option value="{job["id"]}">{job["number"]} - {job["customer"]}</option>' for job in jobs])
    
    content = f'''
    <div class="card" style="max-width: 800px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Create New Invoice</h2>
        </div>
        
        <div class="invoice-preview" style="background: var(--light); padding: 2rem; border-radius: 0.5rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2rem;">
                <div>
                    <h3>Your Business Name</h3>
                    <p>123 Main Street<br>City, State 12345<br>Phone: (555) 123-4567</p>
                </div>
                <div style="text-align: right;">
                    <h2>INVOICE</h2>
                    <p>Invoice #: INV-004<br>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
                </div>
            </div>
        </div>
        
        <form>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div class="form-group">
                    <label>Job</label>
                    <select name="job_id">
                        <option value="">Custom invoice...</option>
                        {job_options}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Invoice Date</label>
                    <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}">
                </div>
                
                <div class="form-group" style="grid-column: 1 / -1;">
                    <label>Bill To</label>
                    <textarea name="bill_to" rows="3" placeholder="Customer Name&#10;Address&#10;City, State ZIP"></textarea>
                </div>
            </div>
            
            <h3 style="margin: 2rem 0 1rem;">Line Items</h3>
            <table style="width: 100%; margin-bottom: 2rem;">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="width: 100px;">Quantity</th>
                        <th style="width: 150px;">Rate</th>
                        <th style="width: 150px;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><input type="text" placeholder="Service or material description"></td>
                        <td><input type="number" value="1" style="text-align: center;"></td>
                        <td><input type="number" step="0.01" placeholder="0.00"></td>
                        <td style="text-align: right; font-weight: 600;">$0.00</td>
                    </tr>
                </tbody>
            </table>
            
            <button type="button" class="btn btn-secondary" style="margin-bottom: 2rem;">+ Add Line Item</button>
            
            <div style="display: flex; gap: 1rem;">
                <button type="submit" class="btn btn-primary">Create & Send Invoice</button>
                <button type="button" class="btn btn-secondary">Save as Draft</button>
                <a href="/invoices" class="btn" style="background: var(--border); color: var(--secondary);">Cancel</a>
            </div>
        </form>
    </div>
    '''
    
    return create_base_template('New Invoice', content)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test():
    return 'App is working!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Profit Tracker AI Professional on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)