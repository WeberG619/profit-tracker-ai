import os
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, session, jsonify, make_response
import json
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'profit-tracker-secret-2024')

# Enhanced data storage
users = {'admin': 'admin123'}
documents = []
jobs = []
uploaded_files = []  # Store uploaded file metadata

# Sample data for testing - as requested by user
def init_sample_data():
    global jobs, documents
    
    # Sample jobs with realistic data
    jobs = [
        {
            'id': 1,
            'number': 'JOB-2024-001',
            'customer': 'Thompson Kitchen Remodel',
            'description': 'Complete kitchen renovation including cabinets, countertops, backsplash, and appliances',
            'quoted_price': 32500,
            'status': 'In Progress',
            'start_date': '2024-01-08',
            'estimated_end': '2024-02-20',
            'progress': 75,
            'health': 'healthy',
            'notes': 'Cabinets installed, countertops arriving next week'
        },
        {
            'id': 2,
            'number': 'JOB-2024-002',
            'customer': 'Martinez Bathroom',
            'description': 'Master bathroom remodel - full gut renovation with luxury fixtures',
            'quoted_price': 18500,
            'status': 'In Progress',
            'start_date': '2024-01-15',
            'estimated_end': '2024-02-10',
            'progress': 40,
            'health': 'warning',
            'notes': 'Plumbing rough-in complete, waiting on special order vanity'
        },
        {
            'id': 3,
            'number': 'JOB-2023-087',
            'customer': 'Wilson Deck Project',
            'description': 'Build 16x20 composite deck with pergola and built-in seating',
            'quoted_price': 22000,
            'status': 'Completed',
            'start_date': '2023-11-01',
            'estimated_end': '2023-11-30',
            'progress': 100,
            'health': 'healthy',
            'notes': 'Project completed on time, customer very happy'
        },
        {
            'id': 4,
            'number': 'JOB-2024-003',
            'customer': 'Chen Basement Finishing',
            'description': 'Finish 1200 sq ft basement with bedroom, bathroom, and rec room',
            'quoted_price': 45000,
            'status': 'Quoted',
            'start_date': '2024-02-01',
            'estimated_end': '2024-03-15',
            'progress': 0,
            'health': 'healthy',
            'notes': 'Waiting for permit approval'
        }
    ]
    
    # Sample documents with realistic data
    documents = [
        # Thompson Kitchen expenses
        {'id': 1, 'type': 'expense', 'job_id': '1', 'vendor': 'Home Depot', 'amount': 4250, 'date': '2024-01-10', 'description': 'Kitchen cabinets - shaker white', 'category': 'Materials'},
        {'id': 2, 'type': 'expense', 'job_id': '1', 'vendor': 'Ferguson', 'amount': 2800, 'date': '2024-01-12', 'description': 'Kohler sink and faucet package', 'category': 'Materials'},
        {'id': 3, 'type': 'income', 'job_id': '1', 'vendor': 'Thompson Kitchen Remodel', 'amount': 16250, 'date': '2024-01-08', 'description': '50% deposit', 'category': 'Payment'},
        {'id': 4, 'type': 'expense', 'job_id': '1', 'vendor': 'Mike Rodriguez', 'amount': 2400, 'date': '2024-01-18', 'description': 'Cabinet installation labor', 'category': 'Labor'},
        
        # Martinez Bathroom expenses
        {'id': 5, 'type': 'expense', 'job_id': '2', 'vendor': 'Tile Shop', 'amount': 1850, 'date': '2024-01-16', 'description': 'Porcelain tile and grout', 'category': 'Materials'},
        {'id': 6, 'type': 'expense', 'job_id': '2', 'vendor': 'ProPlumb LLC', 'amount': 3200, 'date': '2024-01-20', 'description': 'Plumbing rough-in and fixtures', 'category': 'Subcontractor'},
        {'id': 7, 'type': 'income', 'job_id': '2', 'vendor': 'Martinez Bathroom', 'amount': 9250, 'date': '2024-01-15', 'description': '50% deposit', 'category': 'Payment'},
        
        # Wilson Deck (completed)
        {'id': 8, 'type': 'expense', 'job_id': '3', 'vendor': 'Lumber Liquidators', 'amount': 8500, 'date': '2023-11-02', 'description': 'Composite decking and framing lumber', 'category': 'Materials'},
        {'id': 9, 'type': 'expense', 'job_id': '3', 'vendor': 'County Permits', 'amount': 350, 'date': '2023-10-28', 'description': 'Building permit', 'category': 'Permits'},
        {'id': 10, 'type': 'income', 'job_id': '3', 'vendor': 'Wilson Deck Project', 'amount': 22000, 'date': '2023-11-30', 'description': 'Final payment', 'category': 'Payment'},
        
        # General expenses not tied to specific jobs
        {'id': 11, 'type': 'expense', 'job_id': '', 'vendor': 'State Farm', 'amount': 450, 'date': '2024-01-01', 'description': 'Monthly liability insurance', 'category': 'Other'},
        {'id': 12, 'type': 'expense', 'job_id': '', 'vendor': 'DeWalt Tools', 'amount': 899, 'date': '2024-01-05', 'description': 'New miter saw', 'category': 'Equipment'},
    ]

init_sample_data()

def create_base_template(title, content, show_nav=True, page_type='default'):
    nav_html = f'''
        <nav class="main-nav">
            <a href="/dashboard" class="nav-link {'active' if page_type == 'dashboard' else ''}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
                <span>Dashboard</span>
            </a>
            <a href="/jobs" class="nav-link {'active' if page_type == 'jobs' else ''}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 7h-9a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"></path>
                    <path d="M5 3h9a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v8H3a1 1 0 0 1-1-1V5a2 2 0 0 1 2-2z"></path>
                </svg>
                <span>Jobs</span>
            </a>
            <a href="/invoices" class="nav-link {'active' if page_type == 'invoices' else ''}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <path d="M14 2v6h6"></path>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <line x1="10" y1="9" x2="8" y2="9"></line>
                </svg>
                <span>Invoices</span>
            </a>
            <a href="/expenses" class="nav-link {'active' if page_type == 'expenses' else ''}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 3h-8v4h8z"></path>
                </svg>
                <span>Expenses</span>
            </a>
            <a href="/reports" class="nav-link {'active' if page_type == 'reports' else ''}">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
                    <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
                </svg>
                <span>Analytics</span>
            </a>
        </nav>
        <div class="header-actions">
            <button class="quick-add-btn" onclick="showQuickAdd()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                Quick Add
            </button>
            <div class="user-menu">
                <div class="avatar">{session.get('username', 'U')[0].upper()}</div>
                <span class="username">{session.get('username', 'User')}</span>
                <a href="/logout" class="logout-btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                        <polyline points="16 17 21 12 16 7"></polyline>
                        <line x1="21" y1="12" x2="9" y2="12"></line>
                    </svg>
                </a>
            </div>
        </div>
    ''' if show_nav else ''
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Profit Tracker AI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #5E3AEE;
            --primary-dark: #4829CC;
            --primary-light: #F0EBFF;
            --secondary: #6B7280;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
            --info: #3B82F6;
            --dark: #111827;
            --light: #F9FAFB;
            --white: #FFFFFF;
            --border: #E5E7EB;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #FAFBFC;
            color: var(--dark);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* Professional Header */
        .header {{
            background: var(--white);
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.95);
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            letter-spacing: -0.02em;
        }}
        
        .logo-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1.125rem;
        }}
        
        /* Modern Navigation */
        .main-nav {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}
        
        .nav-link {{
            padding: 0.625rem 1rem;
            color: var(--secondary);
            text-decoration: none;
            border-radius: 0.75rem;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.625rem;
            font-weight: 500;
            font-size: 0.9375rem;
            position: relative;
        }}
        
        .nav-link:hover {{
            color: var(--primary);
            background: var(--primary-light);
        }}
        
        .nav-link.active {{
            color: var(--primary);
            background: var(--primary-light);
        }}
        
        .nav-link svg {{
            width: 20px;
            height: 20px;
            stroke-width: 2.5;
        }}
        
        /* Header Actions */
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }}
        
        .quick-add-btn {{
            padding: 0.625rem 1.25rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 0.9375rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: var(--shadow);
        }}
        
        .quick-add-btn:hover {{
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .user-menu {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .avatar {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        
        .username {{
            font-weight: 500;
            color: var(--dark);
        }}
        
        .logout-btn {{
            padding: 0.5rem;
            color: var(--secondary);
            text-decoration: none;
            border-radius: 0.5rem;
            transition: var(--transition);
        }}
        
        .logout-btn:hover {{
            color: var(--danger);
            background: rgba(239, 68, 68, 0.1);
        }}
        
        /* Main Content */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Modern Cards */
        .card {{
            background: var(--white);
            border-radius: 1rem;
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-bottom: 1.5rem;
            transition: var(--transition);
        }}
        
        .card:hover {{
            box-shadow: var(--shadow-md);
        }}
        
        .card-header {{
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .card-body {{
            padding: 2rem;
        }}
        
        .card-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--dark);
            letter-spacing: -0.01em;
        }}
        
        /* Stats Cards with Gradients */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            position: relative;
            overflow: hidden;
            padding: 1.75rem;
            border-radius: 1rem;
            color: white;
            transition: var(--transition);
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
            pointer-events: none;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        .stat-card.revenue {{
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        }}
        
        .stat-card.expenses {{
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        }}
        
        .stat-card.profit {{
            background: linear-gradient(135deg, #5E3AEE 0%, #4829CC 100%);
        }}
        
        .stat-card.jobs {{
            background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        }}
        
        .stat-label {{
            font-size: 0.875rem;
            font-weight: 500;
            opacity: 0.9;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            line-height: 1;
        }}
        
        .stat-change {{
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        .stat-icon {{
            position: absolute;
            right: 1.5rem;
            bottom: 1.5rem;
            opacity: 0.2;
        }}
        
        /* Modern Tables */
        .table-container {{
            overflow-x: auto;
            border-radius: 0.75rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #F9FAFB;
            padding: 1rem 1.5rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.75rem;
            color: var(--secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
        }}
        
        td {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.9375rem;
        }}
        
        tr:hover {{
            background: #FAFBFC;
        }}
        
        /* Modern Badges */
        .badge {{
            padding: 0.375rem 0.875rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        
        .badge-success {{
            background: #D1FAE5;
            color: #065F46;
        }}
        
        .badge-warning {{
            background: #FEF3C7;
            color: #92400E;
        }}
        
        .badge-danger {{
            background: #FEE2E2;
            color: #991B1B;
        }}
        
        .badge-info {{
            background: #DBEAFE;
            color: #1E40AF;
        }}
        
        /* Progress Indicators */
        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #E5E7EB;
            border-radius: 9999px;
            overflow: hidden;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 9999px;
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}
        
        .progress-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
            animation: shimmer 2s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        /* Modern Buttons */
        .btn {{
            padding: 0.625rem 1.25rem;
            border: none;
            border-radius: 0.75rem;
            font-size: 0.9375rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }}
        
        .btn::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255,255,255,0.1);
            transform: translateX(-100%);
            transition: transform 0.3s;
        }}
        
        .btn:hover::before {{
            transform: translateX(0);
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: white;
            box-shadow: var(--shadow);
        }}
        
        .btn-primary:hover {{
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .btn-secondary {{
            background: #F3F4F6;
            color: var(--dark);
        }}
        
        .btn-secondary:hover {{
            background: #E5E7EB;
        }}
        
        /* Action Grid */
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .action-card {{
            background: var(--white);
            border-radius: 1rem;
            padding: 2rem;
            text-align: center;
            text-decoration: none;
            color: var(--dark);
            transition: var(--transition);
            border: 2px solid transparent;
            position: relative;
            overflow: hidden;
        }}
        
        .action-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%);
            transform: scaleX(0);
            transition: transform 0.3s;
        }}
        
        .action-card:hover {{
            border-color: var(--primary-light);
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}
        
        .action-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .action-icon {{
            width: 56px;
            height: 56px;
            background: var(--primary-light);
            color: var(--primary);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            transition: var(--transition);
        }}
        
        .action-card:hover .action-icon {{
            transform: scale(1.1);
            background: var(--primary);
            color: white;
        }}
        
        .action-title {{
            font-weight: 600;
            font-size: 1.125rem;
            margin-bottom: 0.5rem;
        }}
        
        .action-desc {{
            font-size: 0.875rem;
            color: var(--secondary);
        }}
        
        /* Charts */
        .chart-container {{
            background: var(--white);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: var(--shadow);
            height: 400px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        /* Health Indicators */
        .health-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s infinite;
        }}
        
        .health-indicator.healthy {{
            background: var(--success);
        }}
        
        .health-indicator.warning {{
            background: var(--warning);
        }}
        
        .health-indicator.critical {{
            background: var(--danger);
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.6; transform: scale(1.2); }}
            100% {{ opacity: 1; transform: scale(1); }}
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
            font-size: 0.875rem;
        }}
        
        input, select, textarea {{
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid var(--border);
            border-radius: 0.75rem;
            font-size: 0.9375rem;
            transition: var(--transition);
            background: var(--white);
        }}
        
        input:focus, select:focus, textarea:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(94, 58, 238, 0.1);
        }}
        
        /* AI Insights Panel */
        .ai-insights {{
            background: linear-gradient(135deg, var(--primary-light) 0%, rgba(94, 58, 238, 0.05) 100%);
            border: 1px solid rgba(94, 58, 238, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .ai-insights-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        
        .ai-icon {{
            width: 32px;
            height: 32px;
            background: var(--primary);
            color: white;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .ai-insights-title {{
            font-weight: 600;
            color: var(--primary);
        }}
        
        .ai-insights-content {{
            font-size: 0.9375rem;
            color: var(--dark);
            line-height: 1.6;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header-content {{
                padding: 0 1rem;
            }}
            
            .main-nav {{
                display: none;
            }}
            
            .container {{
                padding: 1rem;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .action-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Loading States */
        .skeleton {{
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }}
        
        @keyframes loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        
        /* Tooltips */
        [data-tooltip] {{
            position: relative;
            cursor: help;
        }}
        
        [data-tooltip]:hover::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            padding: 0.5rem 0.75rem;
            background: var(--dark);
            color: white;
            font-size: 0.75rem;
            border-radius: 0.375rem;
            white-space: nowrap;
            z-index: 1000;
            margin-bottom: 0.5rem;
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                <div class="logo-icon">PT</div>
                <span>Profit Tracker</span>
            </a>
            {nav_html}
        </div>
    </header>
    
    <div class="container">
        {content}
    </div>
    
    <!-- Quick Add Modal -->
    <div id="quickAddModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 2rem; border-radius: 1rem; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; position: relative;">
            <button onclick="closeQuickAdd()" style="position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--secondary);">&times;</button>
            
            <h2 style="margin-bottom: 1.5rem;">Quick Add</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <a href="/upload?type=expense" class="action-card" style="padding: 1.5rem; text-decoration: none;">
                    <div class="action-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                            <path d="M16 3h-8v4h8z"></path>
                        </svg>
                    </div>
                    <h3 class="action-title">Add Expense</h3>
                    <p class="action-desc">Record a cost</p>
                </a>
                
                <a href="/upload?type=income" class="action-card" style="padding: 1.5rem; text-decoration: none;">
                    <div class="action-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                        </svg>
                    </div>
                    <h3 class="action-title">Add Income</h3>
                    <p class="action-desc">Record payment</p>
                </a>
                
                <a href="/jobs/new" class="action-card" style="padding: 1.5rem; text-decoration: none;">
                    <div class="action-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 7h-9a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"></path>
                            <path d="M5 3h9a2 2 0 0 1 2 2v2H7a2 2 0 0 0-2 2v8H3a1 1 0 0 1-1-1V5a2 2 0 0 1 2-2z"></path>
                        </svg>
                    </div>
                    <h3 class="action-title">New Job</h3>
                    <p class="action-desc">Start project</p>
                </a>
            </div>
            
            <div style="border-top: 1px solid var(--border); padding-top: 1.5rem;">
                <h3 style="margin-bottom: 1rem;">Quick Expense Entry</h3>
                <form id="quickAddForm" onsubmit="quickAddSubmit(event)" method="POST" action="/api/quick-add">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label>Type</label>
                            <select name="type" required>
                                <option value="expense">Expense</option>
                                <option value="income">Income</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Amount</label>
                            <input type="number" name="amount" step="0.01" required placeholder="0.00">
                        </div>
                        
                        <div class="form-group">
                            <label>Vendor/Customer</label>
                            <input type="text" name="vendor" required placeholder="e.g., Home Depot">
                        </div>
                        
                        <div class="form-group">
                            <label>Category</label>
                            <select name="category" required>
                                <option value="Materials">Materials</option>
                                <option value="Labor">Labor</option>
                                <option value="Equipment">Equipment</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Description (Optional)</label>
                        <input type="text" name="description" placeholder="Quick note...">
                    </div>
                    
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Save Quick Entry</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        // Add smooth transitions
        document.addEventListener('DOMContentLoaded', function() {{
            // Animate numbers on load
            const animateValue = (element, start, end, duration) => {{
                let startTimestamp = null;
                const step = (timestamp) => {{
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    element.textContent = '$' + Math.floor(progress * (end - start) + start).toLocaleString();
                    if (progress < 1) {{
                        window.requestAnimationFrame(step);
                    }}
                }};
                window.requestAnimationFrame(step);
            }};
            
            // Animate stat values
            document.querySelectorAll('.stat-value').forEach(el => {{
                const finalValue = parseInt(el.textContent.replace(/[^0-9]/g, ''));
                if (!isNaN(finalValue)) {{
                    animateValue(el, 0, finalValue, 1000);
                }}
            }});
        }});
        
        function showQuickAdd() {{
            const modal = document.getElementById('quickAddModal');
            modal.style.display = 'flex';
        }}
        
        function closeQuickAdd() {{
            const modal = document.getElementById('quickAddModal');
            modal.style.display = 'none';
            document.getElementById('quickAddForm').reset();
        }}
        
        // Quick Add form submission
        function quickAddSubmit(e) {{
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            
            fetch('/api/quick-add', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    closeQuickAdd();
                    window.location.reload();
                }} else {{
                    alert('Error: ' + data.message);
                }}
            }})
            .catch(error => {{
                alert('Error saving entry');
            }});
        }}
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
    <title>Profit Tracker AI - Professional Financial Management for Contractors</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: #0A0A0A;
            color: white;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 0;
            background: linear-gradient(45deg, #0A0A0A 0%, #1A0F2E 100%);
        }
        
        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            top: -50%;
            left: -50%;
            background: radial-gradient(circle, rgba(94, 58, 238, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: grid 20s linear infinite;
        }
        
        @keyframes grid {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        /* Content */
        .content {
            position: relative;
            z-index: 1;
        }
        
        /* Navigation */
        nav {
            padding: 2rem 4rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            background: rgba(10, 10, 10, 0.8);
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-links a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: white;
        }
        
        .btn-login {
            padding: 0.625rem 1.5rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 0.75rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-login:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        /* Hero Section */
        .hero {
            padding: 12rem 4rem 6rem;
            text-align: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: rgba(94, 58, 238, 0.2);
            border: 1px solid rgba(94, 58, 238, 0.3);
            border-radius: 9999px;
            font-size: 0.875rem;
            color: #B794F6;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        h1 {
            font-size: 4.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #FFFFFF 0%, #B794F6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;
        }
        
        .subtitle {
            font-size: 1.375rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 3rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.6;
        }
        
        .cta-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 4rem;
        }
        
        .btn-primary {
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            color: white;
            text-decoration: none;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 1.125rem;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(94, 58, 238, 0.4);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 30px rgba(94, 58, 238, 0.5);
        }
        
        .btn-secondary {
            padding: 1rem 2rem;
            background: transparent;
            color: white;
            text-decoration: none;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 1.125rem;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s;
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        /* Features Grid */
        .features {
            padding: 4rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 4rem;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem;
            padding: 2.5rem;
            transition: all 0.3s;
        }
        
        .feature-card:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(94, 58, 238, 0.3);
            transform: translateY(-4px);
        }
        
        .feature-icon {
            width: 56px;
            height: 56px;
            background: rgba(94, 58, 238, 0.2);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        
        .feature-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        
        .feature-desc {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.6;
        }
        
        /* Stats */
        .stats {
            padding: 6rem 4rem;
            background: rgba(94, 58, 238, 0.05);
            backdrop-filter: blur(20px);
        }
        
        .stats-grid {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 4rem;
            text-align: center;
        }
        
        .stat-value {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.125rem;
        }
        
        @media (max-width: 768px) {
            nav { padding: 1.5rem 2rem; }
            .hero { padding: 10rem 2rem 4rem; }
            h1 { font-size: 3rem; }
            .subtitle { font-size: 1.125rem; }
            .cta-buttons { flex-direction: column; }
            .features { padding: 2rem; }
            .stats { padding: 4rem 2rem; }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="content">
        <nav>
            <div class="logo">
                <div class="logo-icon">PT</div>
                <span>Profit Tracker</span>
            </div>
            <div class="nav-links">
                <a href="#features" onclick="scrollToSection(event, 'features')">Features</a>
                <a href="#how" onclick="scrollToSection(event, 'how')">How it Works</a>
                <a href="#pricing" onclick="scrollToSection(event, 'pricing')">Pricing</a>
                <a href="/login" class="btn-login">Sign In</a>
            </div>
        </nav>
        
        <div class="hero">
            <div class="badge">AI-Powered Financial Intelligence</div>
            <h1>Know Your True Profit<br>On Every Single Job</h1>
            <p class="subtitle">
                Stop guessing. Start knowing. AI-powered profit tracking that shows you exactly 
                where you make money and where you don't.
            </p>
            <div class="cta-buttons">
                <a href="/signup" class="btn-primary">Start Free Trial</a>
                <a href="#demo" class="btn-secondary" onclick="showDemo(event)">Watch Demo</a>
            </div>
        </div>
        
        <div class="features" id="features">
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3 class="feature-title">AI-Powered Insights</h3>
                    <p class="feature-desc">Our AI analyzes your expenses and suggests ways to increase profit margins on every job.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📸</div>
                    <h3 class="feature-title">Smart Receipt Scanning</h3>
                    <p class="feature-desc">Snap a photo, AI extracts vendor, amount, and category. No manual entry needed.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">💰</div>
                    <h3 class="feature-title">Real-Time Profit Tracking</h3>
                    <p class="feature-desc">See your actual profit margin update in real-time as expenses come in.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3 class="feature-title">Job Health Monitoring</h3>
                    <p class="feature-desc">Get alerts when a job is trending toward loss before it's too late.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3 class="feature-title">Predictive Analytics</h3>
                    <p class="feature-desc">AI predicts final job costs based on current spending patterns.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3 class="feature-title">One-Click Reports</h3>
                    <p class="feature-desc">Generate professional P&L reports for any time period instantly.</p>
                </div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stats-grid">
                <div>
                    <div class="stat-value">47%</div>
                    <div class="stat-label">Average profit increase</div>
                </div>
                <div>
                    <div class="stat-value">2.3hrs</div>
                    <div class="stat-label">Saved per day</div>
                </div>
                <div>
                    <div class="stat-value">$8,400</div>
                    <div class="stat-label">Found in missed expenses monthly</div>
                </div>
                <div>
                    <div class="stat-value">15min</div>
                    <div class="stat-label">To complete monthly books</div>
                </div>
            </div>
        </div>
        
        <!-- How it Works Section -->
        <div class="how-section" id="how">
            <h2 style="text-align: center; font-size: 3rem; margin-bottom: 3rem; color: #1a1a1a;">How It Works</h2>
            <div style="max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 3rem;">
                <div class="step-card">
                    <div class="step-number">1</div>
                    <h3>Sign Up in Seconds</h3>
                    <p>Create your account with just email and password. No credit card required for 14-day trial.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">2</div>
                    <h3>Add Your Jobs</h3>
                    <p>Enter job details and quoted price. Track multiple jobs simultaneously with ease.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">3</div>
                    <h3>Capture Expenses</h3>
                    <p>Snap photos of receipts or drag & drop files. AI extracts all the details automatically.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">4</div>
                    <h3>See Real Profit</h3>
                    <p>Watch your actual profit margins update in real-time. Get alerts before jobs go negative.</p>
                </div>
            </div>
        </div>
        
        <!-- Pricing Section -->
        <div class="pricing-section" id="pricing">
            <h2 style="text-align: center; font-size: 3rem; margin-bottom: 1rem; color: white;">Simple, Transparent Pricing</h2>
            <p style="text-align: center; color: rgba(255,255,255,0.8); margin-bottom: 3rem; font-size: 1.25rem;">
                No hidden fees. Cancel anytime. All features included.
            </p>
            <div style="max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                <div class="price-card">
                    <h3>Starter</h3>
                    <div class="price">$29<span>/month</span></div>
                    <ul>
                        <li>Up to 10 active jobs</li>
                        <li>Unlimited expense tracking</li>
                        <li>Basic AI insights</li>
                        <li>Mobile app access</li>
                        <li>Email support</li>
                    </ul>
                    <a href="/signup" class="price-btn">Start Free Trial</a>
                </div>
                <div class="price-card featured">
                    <div class="badge">MOST POPULAR</div>
                    <h3>Professional</h3>
                    <div class="price">$79<span>/month</span></div>
                    <ul>
                        <li>Unlimited active jobs</li>
                        <li>Advanced AI analytics</li>
                        <li>Team collaboration (5 users)</li>
                        <li>Custom reports</li>
                        <li>Priority support</li>
                        <li>API access</li>
                    </ul>
                    <a href="/signup" class="price-btn primary">Start Free Trial</a>
                </div>
                <div class="price-card">
                    <h3>Enterprise</h3>
                    <div class="price">$199<span>/month</span></div>
                    <ul>
                        <li>Everything in Professional</li>
                        <li>Unlimited team members</li>
                        <li>White-label options</li>
                        <li>Dedicated account manager</li>
                        <li>Custom integrations</li>
                        <li>24/7 phone support</li>
                    </ul>
                    <a href="/signup" class="price-btn">Contact Sales</a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Demo Modal -->
    <div id="demoModal" class="demo-modal" style="display: none;">
        <div class="demo-content">
            <button class="close-demo" onclick="closeDemo()">&times;</button>
            <h2>See Profit Tracker in Action</h2>
            <div class="demo-video">
                <iframe width="100%" height="450" 
                    src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
            <p style="text-align: center; margin-top: 1rem;">
                Ready to transform your business? 
                <a href="/login" style="color: #5E3AEE; font-weight: 600;">Start your free trial now</a>
            </p>
        </div>
    </div>
    
    <style>
        /* How it Works Styles */
        .how-section {
            padding: 6rem 4rem;
            background: #f8f9fa;
        }
        
        .step-card {
            text-align: center;
            position: relative;
        }
        
        .step-number {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0 auto 1.5rem;
        }
        
        .step-card h3 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #1a1a1a;
        }
        
        .step-card p {
            color: #6b7280;
            line-height: 1.6;
        }
        
        /* Pricing Styles */
        .pricing-section {
            padding: 6rem 4rem;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d1b69 100%);
        }
        
        .price-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem;
            padding: 2.5rem;
            text-align: center;
            position: relative;
            transition: transform 0.3s;
        }
        
        .price-card:hover {
            transform: translateY(-5px);
        }
        
        .price-card.featured {
            border-color: #5E3AEE;
            transform: scale(1.05);
        }
        
        .price-card .badge {
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            color: white;
            padding: 0.25rem 1rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .price-card h3 {
            color: white;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .price {
            font-size: 3rem;
            font-weight: 700;
            color: white;
            margin-bottom: 2rem;
        }
        
        .price span {
            font-size: 1rem;
            font-weight: 400;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .price-card ul {
            list-style: none;
            padding: 0;
            margin: 0 0 2rem 0;
        }
        
        .price-card li {
            padding: 0.75rem 0;
            color: rgba(255, 255, 255, 0.8);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .price-card li:last-child {
            border-bottom: none;
        }
        
        .price-btn {
            display: inline-block;
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            text-decoration: none;
            border-radius: 0.75rem;
            font-weight: 600;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .price-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .price-btn.primary {
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            border: none;
        }
        
        .price-btn.primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(94, 58, 238, 0.5);
        }
        
        /* Demo Modal Styles */
        .demo-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        
        .demo-content {
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            max-width: 800px;
            width: 90%;
            position: relative;
        }
        
        .close-demo {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 2rem;
            cursor: pointer;
            color: #6b7280;
        }
        
        .demo-content h2 {
            text-align: center;
            margin-bottom: 1.5rem;
            color: #1a1a1a;
        }
        
        .demo-video {
            background: #000;
            border-radius: 0.5rem;
            overflow: hidden;
        }
        
        @media (max-width: 768px) {
            .how-section, .pricing-section {
                padding: 4rem 2rem;
            }
            
            .price-card.featured {
                transform: none;
            }
        }
    </style>
    
    <script>
        // Smooth scrolling
        function scrollToSection(e, sectionId) {
            e.preventDefault();
            const section = document.getElementById(sectionId);
            if (section) {
                section.scrollIntoView({ behavior: 'smooth' });
            }
        }
        
        // Demo modal
        function showDemo(e) {
            e.preventDefault();
            document.getElementById('demoModal').style.display = 'flex';
        }
        
        function closeDemo() {
            document.getElementById('demoModal').style.display = 'none';
        }
        
        // Close modal on outside click
        document.getElementById('demoModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeDemo();
            }
        });
    </script>
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: #0A0A0A;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 0;
            background: linear-gradient(45deg, #0A0A0A 0%, #1A0F2E 100%);
        }
        
        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            top: -50%;
            left: -50%;
            background: radial-gradient(circle, rgba(94, 58, 238, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: grid 20s linear infinite;
        }
        
        @keyframes grid {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .login-container {
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 3rem;
            border-radius: 1.5rem;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .logo-icon {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        h2 {
            text-align: center;
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 2.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.9);
        }
        
        input {
            width: 100%;
            padding: 0.875rem 1rem;
            background: rgba(255, 255, 255, 0.08);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            font-size: 1rem;
            color: white;
            transition: all 0.3s;
        }
        
        input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        
        input:focus {
            outline: none;
            border-color: #5E3AEE;
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 0 3px rgba(94, 58, 238, 0.1);
        }
        
        button {
            width: 100%;
            padding: 0.875rem;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            color: white;
            border: none;
            border-radius: 0.75rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(94, 58, 238, 0.4);
        }
        
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 30px rgba(94, 58, 238, 0.5);
        }
        
        .divider {
            text-align: center;
            margin: 2rem 0;
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.875rem;
        }
        
        .demo-info {
            background: rgba(94, 58, 238, 0.1);
            border: 1px solid rgba(94, 58, 238, 0.2);
            padding: 1rem;
            border-radius: 0.75rem;
            text-align: center;
            font-size: 0.875rem;
        }
        
        .demo-info strong { 
            color: #B794F6;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">PT</div>
        </div>
        <h2>Welcome Back</h2>
        <p class="subtitle">Enter your credentials to access your dashboard</p>
        
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus placeholder="Enter your username">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required placeholder="Enter your password">
            </div>
            <button type="submit">Sign In</button>
        </form>
        
        <div class="divider">or</div>
        
        <a href="/signup" style="display: block; width: 100%; padding: 0.875rem; background: transparent; color: #B794F6; text-decoration: none; border-radius: 0.75rem; font-size: 1rem; font-weight: 600; text-align: center; border: 2px solid #5E3AEE; margin-bottom: 1rem; transition: all 0.3s;">
            Create New Account
        </a>
        
        <div class="demo-info">
            <strong>Demo Account</strong><br>
            Username: admin | Password: admin123
        </div>
    </div>
</body>
</html>
    '''

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            error = 'All fields are required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif username in users:
            error = 'Username already exists'
        else:
            # Create new user
            users[username] = password
            session['username'] = username
            return redirect(url_for('dashboard'))
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Sign Up - Profit Tracker AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: #0A0A0A;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 0;
            background: linear-gradient(45deg, #0A0A0A 0%, #1A0F2E 100%);
        }
        
        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            top: -50%;
            left: -50%;
            background: radial-gradient(circle, rgba(94, 58, 238, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: grid 20s linear infinite;
        }
        
        @keyframes grid {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .signup-container {
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 3rem;
            border-radius: 1.5rem;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .logo {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .logo-icon {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        h2 {
            text-align: center;
            font-size: 1.875rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 2.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.9);
        }
        
        input {
            width: 100%;
            padding: 0.875rem 1rem;
            background: rgba(255, 255, 255, 0.08);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            font-size: 1rem;
            color: white;
            transition: all 0.3s;
        }
        
        input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        
        input:focus {
            outline: none;
            border-color: #5E3AEE;
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 0 0 3px rgba(94, 58, 238, 0.1);
        }
        
        button {
            width: 100%;
            padding: 0.875rem;
            background: linear-gradient(135deg, #5E3AEE 0%, #B83AF3 100%);
            color: white;
            border: none;
            border-radius: 0.75rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(94, 58, 238, 0.4);
        }
        
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 30px rgba(94, 58, 238, 0.5);
        }
        
        .divider {
            text-align: center;
            margin: 1.5rem 0;
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.875rem;
        }
        
        .login-link {
            text-align: center;
            margin-top: 1.5rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .login-link a {
            color: #B794F6;
            text-decoration: none;
            font-weight: 600;
        }
        
        .login-link a:hover {
            text-decoration: underline;
        }
        
        .benefits {
            background: rgba(94, 58, 238, 0.1);
            border: 1px solid rgba(94, 58, 238, 0.2);
            padding: 1rem;
            border-radius: 0.75rem;
            margin-top: 1.5rem;
            font-size: 0.875rem;
        }
        
        .benefits ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .benefits li {
            padding: 0.25rem 0;
            color: #B794F6;
        }
        
        .benefits li::before {
            content: "✓ ";
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="signup-container">
        <div class="logo">
            <div class="logo-icon">PT</div>
        </div>
        <h2>Create Your Account</h2>
        <p class="subtitle">Start tracking profit in seconds</p>
        
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus placeholder="Choose a username">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" required placeholder="your@email.com">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required placeholder="Create a password">
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" name="confirm_password" required placeholder="Confirm your password">
            </div>
            <button type="submit">Create Account</button>
        </form>
        
        <div class="benefits">
            <strong>14-Day Free Trial Includes:</strong>
            <ul>
                <li>Unlimited jobs tracking</li>
                <li>AI-powered receipt scanning</li>
                <li>Real-time profit analytics</li>
                <li>No credit card required</li>
            </ul>
        </div>
        
        <div class="login-link">
            Already have an account? <a href="/login">Sign In</a>
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
    
    # AI Insights
    insights = []
    if profit_margin < 20:
        insights.append("Your profit margins are below industry average. Consider reviewing your pricing strategy.")
    if len(active_jobs) > 2:
        insights.append(f"You have {len(active_jobs)} active jobs. Consider completing current projects before taking new ones.")
    if total_expenses > total_revenue * 0.7:
        insights.append("Expenses are consuming over 70% of revenue. Look for cost reduction opportunities.")
    
    content = f'''
    <!-- AI Insights Panel -->
    <div class="ai-insights">
        <div class="ai-insights-header">
            <div class="ai-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
            </div>
            <h3 class="ai-insights-title">AI Insights</h3>
        </div>
        <div class="ai-insights-content">
            {' • '.join(insights) if insights else 'Great job! Your business metrics look healthy. Keep up the good work!'}
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card revenue">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value">${total_revenue:,.0f}</div>
            <div class="stat-change">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                    <polyline points="17 6 23 6 23 12"></polyline>
                </svg>
                <span>12% from last month</span>
            </div>
            <svg class="stat-icon" width="48" height="48" viewBox="0 0 24 24" fill="currentColor" opacity="0.2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
        </div>
        
        <div class="stat-card expenses">
            <div class="stat-label">Total Expenses</div>
            <div class="stat-value">${total_expenses:,.0f}</div>
            <div class="stat-change">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
                    <polyline points="17 18 23 18 23 12"></polyline>
                </svg>
                <span>5% from last month</span>
            </div>
            <svg class="stat-icon" width="48" height="48" viewBox="0 0 24 24" fill="currentColor" opacity="0.2">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                <line x1="1" y1="10" x2="23" y2="10"></line>
            </svg>
        </div>
        
        <div class="stat-card profit">
            <div class="stat-label">Net Profit</div>
            <div class="stat-value">${net_profit:,.0f}</div>
            <div class="stat-change">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                    <polyline points="17 6 23 6 23 12"></polyline>
                </svg>
                <span>{profit_margin:.1f}% margin</span>
            </div>
            <svg class="stat-icon" width="48" height="48" viewBox="0 0 24 24" fill="currentColor" opacity="0.2">
                <line x1="12" y1="1" x2="12" y2="23"></line>
                <polyline points="17 5 12 10 7 5"></polyline>
                <polyline points="17 19 12 14 7 19"></polyline>
            </svg>
        </div>
        
        <div class="stat-card jobs">
            <div class="stat-label">Active Jobs</div>
            <div class="stat-value">{len(active_jobs)}</div>
            <div class="stat-change">
                <span class="health-indicator healthy"></span>
                <span>All on track</span>
            </div>
            <svg class="stat-icon" width="48" height="48" viewBox="0 0 24 24" fill="currentColor" opacity="0.2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        </div>
    </div>
    
    <div class="action-grid">
        <a href="/upload" class="action-card">
            <div class="action-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                </svg>
            </div>
            <h3 class="action-title">Capture Receipt</h3>
            <p class="action-desc">AI extracts data instantly</p>
        </a>
        
        <a href="/jobs/new" class="action-card">
            <div class="action-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
            </div>
            <h3 class="action-title">New Job</h3>
            <p class="action-desc">Start tracking a project</p>
        </a>
        
        <a href="/invoices/new" class="action-card">
            <div class="action-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
            <h3 class="action-title">Create Invoice</h3>
            <p class="action-desc">Bill your customers</p>
        </a>
        
        <a href="/reports" class="action-card">
            <div class="action-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
            </div>
            <h3 class="action-title">View Analytics</h3>
            <p class="action-desc">Insights & trends</p>
        </a>
    </div>
    
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; margin-top: 2rem;">
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Active Jobs Performance</h2>
                <a href="/jobs" class="btn btn-secondary">View All</a>
            </div>
            <div class="card-body">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Job</th>
                                <th>Customer</th>
                                <th>Progress</th>
                                <th>Health</th>
                                <th>Profit</th>
                            </tr>
                        </thead>
                        <tbody>
    '''
    
    for job in active_jobs[:3]:
        job_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        job_revenue = sum(d['amount'] for d in documents if d['type'] == 'income' and d.get('job_id') == str(job['id']))
        job_profit = job_revenue - job_expenses
        job_margin = (job_profit / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0
        
        # Determine health status
        health_status = 'healthy'
        if job_margin < 10:
            health_status = 'critical'
        elif job_margin < 20:
            health_status = 'warning'
        
        content += f'''
                            <tr>
                                <td style="font-weight: 600;">{job['number']}</td>
                                <td>{job['customer']}</td>
                                <td>
                                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                                        <div class="progress-bar" style="width: 120px;">
                                            <div class="progress-fill" style="width: {job['progress']}%;"></div>
                                        </div>
                                        <span style="font-size: 0.875rem; font-weight: 500;">{job['progress']}%</span>
                                    </div>
                                </td>
                                <td>
                                    <span class="health-indicator {health_status}"></span>
                                    <span style="font-size: 0.875rem; text-transform: capitalize;">{health_status}</span>
                                </td>
                                <td style="font-weight: 600; color: {'var(--success)' if job_profit >= 0 else 'var(--danger)'};">
                                    ${job_profit:,.0f}
                                    <span style="font-size: 0.75rem; color: var(--secondary); font-weight: 400;">({job_margin:.0f}%)</span>
                                </td>
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
                <h2 class="card-title">Recent Activity</h2>
                <a href="/documents" class="btn btn-secondary">View All</a>
            </div>
            <div class="card-body">
                <div style="display: flex; flex-direction: column; gap: 1rem;">
    '''
    
    # Recent activity items
    recent_docs = sorted(documents, key=lambda x: x['date'], reverse=True)[:4]
    for doc in recent_docs:
        icon = '📥' if doc['type'] == 'income' else '📤'
        color = 'var(--success)' if doc['type'] == 'income' else 'var(--danger)'
        sign = '+' if doc['type'] == 'income' else '-'
        
        content += f'''
                    <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem; background: #FAFBFC; border-radius: 0.75rem;">
                        <div style="font-size: 1.25rem;">{icon}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 500;">{doc['vendor']}</div>
                            <div style="font-size: 0.75rem; color: var(--secondary);">{doc['description']}</div>
                        </div>
                        <div style="font-weight: 600; color: {color};">
                            {sign}${doc['amount']:,.0f}
                        </div>
                    </div>
        '''
    
    content += '''
                </div>
            </div>
        </div>
    </div>
    
    <div class="chart-container">
        <div style="text-align: center;">
            <h3 style="margin-bottom: 0.5rem;">Revenue Trend</h3>
            <p style="color: var(--secondary); font-size: 0.875rem;">Interactive chart powered by AI analytics</p>
            <div style="margin-top: 2rem;">
                <svg width="600" height="300" viewBox="0 0 600 300">
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:rgba(94,58,238,0.3);stop-opacity:1" />
                            <stop offset="100%" style="stop-color:rgba(94,58,238,0);stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <path d="M 50 200 Q 150 150, 250 170 T 450 120 L 450 250 L 50 250 Z" fill="url(#gradient)" opacity="0.5"/>
                    <path d="M 50 200 Q 150 150, 250 170 T 450 120" stroke="#5E3AEE" stroke-width="3" fill="none"/>
                    <circle cx="50" cy="200" r="4" fill="#5E3AEE"/>
                    <circle cx="250" cy="170" r="4" fill="#5E3AEE"/>
                    <circle cx="450" cy="120" r="4" fill="#5E3AEE"/>
                </svg>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Dashboard', content, page_type='dashboard')

# Continue with all other routes (jobs, expenses, invoices, reports, etc.)...
# I'll include just the key routes to show the pattern

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Handle file upload
        file_info = None
        if 'receipt_file' in request.files:
            file = request.files['receipt_file']
            if file and file.filename:
                # Store file metadata (in production, you'd save the actual file)
                file_info = {
                    'filename': file.filename,
                    'size': len(file.read()),
                    'type': file.content_type
                }
                file.seek(0)  # Reset file pointer
                uploaded_files.append(file_info)
        
        doc = {
            'id': len(documents) + 1,
            'type': request.form.get('doc_type'),
            'vendor': request.form.get('vendor'),
            'amount': float(request.form.get('amount', 0)),
            'date': request.form.get('date'),
            'description': request.form.get('description'),
            'category': request.form.get('category'),
            'job_id': request.form.get('job_id'),
            'file_info': file_info
        }
        documents.append(doc)
        return redirect(url_for('dashboard'))
    
    job_options = ''
    for job in jobs:
        job_options += f'<option value="{job["id"]}">{job["number"]} - {job["customer"]}</option>'
    
    content = f'''
    <style>
        .upload-zone {{
            border: 3px dashed var(--primary);
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
            background: var(--primary-light);
            margin-bottom: 2rem;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }}
        
        .upload-zone:hover {{
            background: rgba(94, 58, 238, 0.1);
            border-color: var(--primary-dark);
        }}
        
        .upload-zone.dragover {{
            background: rgba(94, 58, 238, 0.2);
            border-color: var(--primary-dark);
            transform: scale(1.02);
        }}
        
        .file-input {{
            display: none;
        }}
        
        .upload-button {{
            display: inline-block;
            padding: 0.875rem 2rem;
            background: var(--primary);
            color: white;
            border-radius: 0.75rem;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            margin-top: 1rem;
        }}
        
        .upload-button:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
        }}
        
        .file-preview {{
            display: none;
            margin-top: 1.5rem;
            padding: 1rem;
            background: white;
            border-radius: 0.75rem;
            border: 1px solid var(--border);
        }}
        
        .file-preview.active {{
            display: block;
        }}
        
        .preview-image {{
            max-width: 200px;
            max-height: 200px;
            border-radius: 0.5rem;
            margin: 0 auto 1rem;
            display: block;
        }}
        
        .camera-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
    </style>
    
    <div class="card" style="max-width: 900px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Capture Receipt</h2>
        </div>
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <!-- File Upload Zone -->
                <div class="upload-zone" id="uploadZone">
                    <div class="camera-icon">📸</div>
                    <h3 style="margin-bottom: 0.5rem;">Upload Receipt or Invoice</h3>
                    <p style="color: var(--secondary); margin-bottom: 1rem;">
                        Drag & drop your file here or click to browse<br>
                        <small>Supports JPEG, PNG, PDF (Max 10MB)</small>
                    </p>
                    <label for="receiptFile" class="upload-button">
                        Choose File
                    </label>
                    <input type="file" id="receiptFile" name="receipt_file" class="file-input" 
                           accept="image/jpeg,image/jpg,image/png,application/pdf">
                    
                    <div class="file-preview" id="filePreview">
                        <img class="preview-image" id="previewImage" style="display: none;">
                        <div id="previewInfo"></div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                    <div class="form-group">
                        <label>Document Type *</label>
                        <select name="doc_type" required>
                            <option value="">Select type...</option>
                            <option value="expense">Expense Receipt</option>
                            <option value="income">Income Invoice</option>
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
                        <label>Vendor/Customer *</label>
                        <input type="text" name="vendor" required placeholder="e.g., Home Depot, Smith Construction">
                    </div>
                    
                    <div class="form-group">
                        <label>Amount *</label>
                        <input type="number" name="amount" step="0.01" required placeholder="0.00">
                    </div>
                    
                    <div class="form-group">
                        <label>Date *</label>
                        <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Category *</label>
                        <select name="category" required>
                            <option value="">Select category...</option>
                            <option value="Materials">Materials</option>
                            <option value="Labor">Labor</option>
                            <option value="Equipment">Equipment</option>
                            <option value="Subcontractor">Subcontractor</option>
                            <option value="Permits">Permits</option>
                            <option value="Other">Other</option>
                            <option value="Payment">Payment (Income)</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="3" placeholder="Brief description of the expense or income"></textarea>
                </div>
                
                <div class="ai-insights" style="margin-top: 1.5rem;">
                    <div class="ai-insights-header">
                        <div class="ai-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 11H3v10h6V11zm4-8H7v18h6V3zm4 4h-6v14h6V7zm4 2h-6v12h6V9z"/>
                            </svg>
                        </div>
                        <h3 class="ai-insights-title">AI Processing Status</h3>
                    </div>
                    <div class="ai-insights-content" id="aiStatus">
                        Ready to process your receipt. Upload an image and our AI will help extract key information.
                    </div>
                </div>
                
                <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary" style="flex: 1;">Save Document</button>
                    <a href="/dashboard" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        // File upload handling
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('receiptFile');
        const filePreview = document.getElementById('filePreview');
        const previewImage = document.getElementById('previewImage');
        const previewInfo = document.getElementById('previewInfo');
        const aiStatus = document.getElementById('aiStatus');
        
        // Click to upload
        uploadZone.addEventListener('click', (e) => {{
            if (e.target.closest('.upload-button')) {{
                fileInput.click();
            }}
        }});
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {{
            e.preventDefault();
            uploadZone.classList.add('dragover');
        }});
        
        uploadZone.addEventListener('dragleave', () => {{
            uploadZone.classList.remove('dragover');
        }});
        
        uploadZone.addEventListener('drop', (e) => {{
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {{
                handleFile(files[0]);
            }}
        }});
        
        // File input change
        fileInput.addEventListener('change', (e) => {{
            if (e.target.files.length > 0) {{
                handleFile(e.target.files[0]);
            }}
        }});
        
        function handleFile(file) {{
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
            if (!validTypes.includes(file.type)) {{
                alert('Please upload a JPEG, PNG, or PDF file.');
                return;
            }}
            
            // Validate file size (10MB max)
            if (file.size > 10 * 1024 * 1024) {{
                alert('File size must be less than 10MB.');
                return;
            }}
            
            // Update file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Show preview
            filePreview.classList.add('active');
            
            if (file.type.startsWith('image/')) {{
                const reader = new FileReader();
                reader.onload = (e) => {{
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                }};
                reader.readAsDataURL(file);
            }} else {{
                previewImage.style.display = 'none';
            }}
            
            // Update preview info
            const fileSize = (file.size / 1024).toFixed(1);
            previewInfo.innerHTML = `
                <strong>File:</strong> ${{file.name}}<br>
                <strong>Type:</strong> ${{file.type}}<br>
                <strong>Size:</strong> ${{fileSize}} KB
            `;
            
            // Update AI status
            aiStatus.innerHTML = `
                <div style="color: var(--primary);">
                    <strong>AI Analysis Ready</strong><br>
                    File uploaded successfully. In the full version, AI will automatically extract:
                    vendor name, amount, date, and categorize the expense.
                </div>
            `;
        }}
    </script>
    '''
    
    return create_base_template('Capture Receipt', content, page_type='expenses')

@app.route('/jobs')
def jobs_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    content = '''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Jobs Management</h2>
            <a href="/jobs/new" class="btn btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                New Job
            </a>
        </div>
        <div class="card-body">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Job #</th>
                            <th>Customer</th>
                            <th>Description</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Health</th>
                            <th>Profit Margin</th>
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
        
        health_color = 'healthy'
        if profit_margin < 10:
            health_color = 'critical'
        elif profit_margin < 20:
            health_color = 'warning'
        
        content += f'''
                    <tr>
                        <td style="font-weight: 600;">{job['number']}</td>
                        <td>{job['customer']}</td>
                        <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{job['description']}</td>
                        <td><span class="badge {status_class}">{job['status']}</span></td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div class="progress-bar" style="width: 80px;">
                                    <div class="progress-fill" style="width: {job['progress']}%;"></div>
                                </div>
                                <span style="font-size: 0.75rem;">{job['progress']}%</span>
                            </div>
                        </td>
                        <td>
                            <span class="health-indicator {health_color}"></span>
                        </td>
                        <td style="font-weight: 600; color: {'var(--success)' if profit_margin > 20 else 'var(--warning)' if profit_margin > 10 else 'var(--danger)'};">
                            {profit_margin:.1f}%
                        </td>
                        <td>
                            <a href="/jobs/{job['id']}" class="btn btn-secondary" style="padding: 0.375rem 0.875rem; font-size: 0.875rem;">
                                View Details
                            </a>
                        </td>
                    </tr>
        '''
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Jobs', content, page_type='jobs')

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
            'start_date': request.form.get('start_date'),
            'estimated_end': request.form.get('estimated_end'),
            'status': 'Quoted',
            'progress': 0,
            'health': 'healthy',
            'notes': request.form.get('notes', '')
        }
        jobs.append(job)
        return redirect(url_for('jobs_page'))
    
    content = '''
    <div class="card" style="max-width: 800px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Create New Job</h2>
        </div>
        <div class="card-body">
            <form method="POST">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                    <div class="form-group">
                        <label>Job Number</label>
                        <input type="text" name="number" required placeholder="e.g., JOB-004" autofocus>
                    </div>
                    
                    <div class="form-group">
                        <label>Customer Name</label>
                        <input type="text" name="customer" required placeholder="e.g., Smith Construction">
                    </div>
                    
                    <div class="form-group">
                        <label>Start Date</label>
                        <input type="date" name="start_date" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Estimated End Date</label>
                        <input type="date" name="estimated_end" required>
                    </div>
                    
                    <div class="form-group" style="grid-column: span 2;">
                        <label>Quoted Price</label>
                        <input type="number" name="quoted_price" step="0.01" required placeholder="0.00">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Job Description</label>
                    <textarea name="description" rows="4" required placeholder="Detailed description of the work to be performed..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>Notes (Optional)</label>
                    <textarea name="notes" rows="3" placeholder="Any additional notes or special requirements..."></textarea>
                </div>
                
                <div class="ai-insights" style="margin-top: 1.5rem;">
                    <div class="ai-insights-header">
                        <div class="ai-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                            </svg>
                        </div>
                        <h3 class="ai-insights-title">AI Pricing Assistant</h3>
                    </div>
                    <div class="ai-insights-content">
                        Based on similar jobs, we recommend a 35% markup on materials and $85/hour for labor to maintain healthy profit margins.
                    </div>
                </div>
                
                <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary" style="flex: 1;">Create Job</button>
                    <a href="/jobs" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return create_base_template('New Job', content, page_type='jobs')

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    if not session.get('username'):
        return redirect(url_for('login'))
    
    job = next((j for j in jobs if j['id'] == job_id), None)
    if not job:
        return redirect(url_for('jobs_page'))
    
    # Calculate job financials
    job_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job_id))
    job_revenue = sum(d['amount'] for d in documents if d['type'] == 'income' and d.get('job_id') == str(job_id))
    job_profit = job_revenue - job_expenses
    profit_margin = (job_profit / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0
    
    # Get job documents
    job_docs = [d for d in documents if d.get('job_id') == str(job_id)]
    
    content = f'''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Job {job['number']} - {job['customer']}</h2>
            <div style="display: flex; gap: 1rem;">
                <a href="/upload?job_id={job_id}" class="btn btn-primary">Add Document</a>
                <a href="/jobs" class="btn btn-secondary">Back to Jobs</a>
            </div>
        </div>
        <div class="card-body">
            <div class="stats-grid" style="margin-bottom: 2rem;">
                <div class="stat-card revenue">
                    <div class="stat-label">Quoted Price</div>
                    <div class="stat-value">${job['quoted_price']:,.0f}</div>
                </div>
                <div class="stat-card expenses">
                    <div class="stat-label">Total Expenses</div>
                    <div class="stat-value">${job_expenses:,.0f}</div>
                </div>
                <div class="stat-card profit">
                    <div class="stat-label">Current Profit</div>
                    <div class="stat-value">${job_profit:,.0f}</div>
                    <div class="stat-change">{profit_margin:.1f}% margin</div>
                </div>
                <div class="stat-card jobs">
                    <div class="stat-label">Progress</div>
                    <div class="stat-value">{job['progress']}%</div>
                    <div class="progress-bar" style="margin-top: 0.5rem;">
                        <div class="progress-fill" style="width: {job['progress']}%;"></div>
                    </div>
                </div>
            </div>
            
            <h3 style="margin-bottom: 1rem;">Job Details</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                <div>
                    <p><strong>Description:</strong> {job['description']}</p>
                    <p><strong>Start Date:</strong> {job['start_date']}</p>
                    <p><strong>Estimated End:</strong> {job['estimated_end']}</p>
                </div>
                <div>
                    <p><strong>Status:</strong> <span class="badge badge-{'success' if job['status'] == 'Completed' else 'warning' if job['status'] == 'In Progress' else 'info'}">{job['status']}</span></p>
                    <p><strong>Health:</strong> <span class="health-indicator {job['health']}"></span> {job['health'].title()}</p>
                    <p><strong>Notes:</strong> {job.get('notes', 'No notes')}</p>
                </div>
            </div>
            
            <h3 style="margin-bottom: 1rem;">Documents</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Vendor/Customer</th>
                            <th>Category</th>
                            <th>Description</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    if job_docs:
        for doc in sorted(job_docs, key=lambda x: x['date'], reverse=True):
            color = 'var(--success)' if doc['type'] == 'income' else 'var(--danger)'
            sign = '+' if doc['type'] == 'income' else '-'
            content += f'''
                        <tr>
                            <td>{doc['date']}</td>
                            <td><span class="badge badge-{'success' if doc['type'] == 'income' else 'danger'}">{doc['type'].title()}</span></td>
                            <td>{doc['vendor']}</td>
                            <td>{doc.get('category', '-')}</td>
                            <td>{doc.get('description', '-')}</td>
                            <td style="color: {color}; font-weight: 600;">{sign}${doc['amount']:,.2f}</td>
                        </tr>
            '''
    else:
        content += '<tr><td colspan="6" style="text-align: center; color: var(--secondary);">No documents yet</td></tr>'
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template(f'Job {job["number"]}', content, page_type='jobs')

@app.route('/invoices')
def invoices():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Get all income documents (invoices)
    invoices = [d for d in documents if d['type'] == 'income']
    
    content = '''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Invoices</h2>
            <a href="/invoices/new" class="btn btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                Create Invoice
            </a>
        </div>
        <div class="card-body">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Customer</th>
                            <th>Job</th>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    if invoices:
        for inv in sorted(invoices, key=lambda x: x['date'], reverse=True):
            job = next((j for j in jobs if str(j['id']) == inv.get('job_id')), None)
            job_info = f"{job['number']} - {job['customer']}" if job else "No job assigned"
            content += f'''
                        <tr>
                            <td>{inv['date']}</td>
                            <td>{inv['vendor']}</td>
                            <td>{job_info}</td>
                            <td>{inv.get('description', '-')}</td>
                            <td style="color: var(--success); font-weight: 600;">${inv['amount']:,.2f}</td>
                            <td><span class="badge badge-success">Paid</span></td>
                        </tr>
            '''
    else:
        content += '<tr><td colspan="6" style="text-align: center; color: var(--secondary);">No invoices yet</td></tr>'
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Invoices', content, page_type='invoices')

@app.route('/invoices/new', methods=['GET', 'POST'])
def new_invoice():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        invoice = {
            'id': len(documents) + 1,
            'type': 'income',
            'vendor': request.form.get('customer'),
            'amount': float(request.form.get('amount', 0)),
            'date': request.form.get('date'),
            'description': request.form.get('description'),
            'category': 'Payment',
            'job_id': request.form.get('job_id')
        }
        documents.append(invoice)
        return redirect(url_for('invoices'))
    
    job_options = ''
    for job in jobs:
        job_options += f'<option value="{job["id"]}">{job["number"]} - {job["customer"]} (${job["quoted_price"]:,.2f})</option>'
    
    content = f'''
    <div class="card" style="max-width: 800px; margin: 0 auto;">
        <div class="card-header">
            <h2 class="card-title">Create Invoice</h2>
        </div>
        <div class="card-body">
            <form method="POST">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                    <div class="form-group">
                        <label>Customer Name</label>
                        <input type="text" name="customer" required placeholder="e.g., Smith Construction">
                    </div>
                    
                    <div class="form-group">
                        <label>Invoice Date</label>
                        <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Job</label>
                        <select name="job_id" required>
                            <option value="">Select job...</option>
                            {job_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Amount</label>
                        <input type="number" name="amount" step="0.01" required placeholder="0.00">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="4" required placeholder="Invoice description (e.g., 50% deposit, Progress payment #2, Final payment)"></textarea>
                </div>
                
                <div class="ai-insights" style="margin-top: 1.5rem;">
                    <div class="ai-insights-header">
                        <div class="ai-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                            </svg>
                        </div>
                        <h3 class="ai-insights-title">AI Payment Terms</h3>
                    </div>
                    <div class="ai-insights-content">
                        Recommended payment schedule: 30% deposit, 40% at milestone, 30% on completion. This helps maintain positive cash flow throughout the project.
                    </div>
                </div>
                
                <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary" style="flex: 1;">Create Invoice</button>
                    <a href="/invoices" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return create_base_template('New Invoice', content, page_type='invoices')

@app.route('/expenses')
def expenses():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Get all expense documents
    expenses_list = [d for d in documents if d['type'] == 'expense']
    
    # Group by category
    category_totals = {}
    for exp in expenses_list:
        cat = exp.get('category', 'Other')
        category_totals[cat] = category_totals.get(cat, 0) + exp['amount']
    
    content = '''
    <div class="stats-grid" style="margin-bottom: 2rem;">
    '''
    
    for category, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:4]:
        content += f'''
        <div class="stat-card expenses">
            <div class="stat-label">{category}</div>
            <div class="stat-value">${total:,.0f}</div>
        </div>
        '''
    
    content += '''
    </div>
    
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Expenses</h2>
            <a href="/upload" class="btn btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                Add Expense
            </a>
        </div>
        <div class="card-body">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Vendor</th>
                            <th>Category</th>
                            <th>Job</th>
                            <th>Description</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    if expenses_list:
        for exp in sorted(expenses_list, key=lambda x: x['date'], reverse=True):
            job = next((j for j in jobs if str(j['id']) == exp.get('job_id')), None)
            job_info = f"{job['number']}" if job else "-"
            content += f'''
                        <tr>
                            <td>{exp['date']}</td>
                            <td>{exp['vendor']}</td>
                            <td><span class="badge badge-info">{exp.get('category', 'Other')}</span></td>
                            <td>{job_info}</td>
                            <td>{exp.get('description', '-')}</td>
                            <td style="color: var(--danger); font-weight: 600;">-${exp['amount']:,.2f}</td>
                        </tr>
            '''
    else:
        content += '<tr><td colspan="6" style="text-align: center; color: var(--secondary);">No expenses recorded yet</td></tr>'
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Expenses', content, page_type='expenses')

@app.route('/reports')
def reports():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Calculate metrics
    total_revenue = sum(d['amount'] for d in documents if d['type'] == 'income')
    total_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense')
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate job performance
    job_performance = []
    for job in jobs:
        job_expenses = sum(d['amount'] for d in documents if d['type'] == 'expense' and d.get('job_id') == str(job['id']))
        job_revenue = sum(d['amount'] for d in documents if d['type'] == 'income' and d.get('job_id') == str(job['id']))
        job_profit = job_revenue - job_expenses
        job_margin = (job_profit / job['quoted_price'] * 100) if job['quoted_price'] > 0 else 0
        job_performance.append({
            'job': job,
            'revenue': job_revenue,
            'expenses': job_expenses,
            'profit': job_profit,
            'margin': job_margin
        })
    
    # Sort by profit margin
    job_performance.sort(key=lambda x: x['margin'], reverse=True)
    
    content = f'''
    <div class="ai-insights" style="margin-bottom: 2rem;">
        <div class="ai-insights-header">
            <div class="ai-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
            </div>
            <h3 class="ai-insights-title">AI Business Analysis</h3>
        </div>
        <div class="ai-insights-content">
            Your overall profit margin is {profit_margin:.1f}%. {'Excellent performance!' if profit_margin > 25 else 'Consider reviewing your pricing strategy to improve margins.' if profit_margin < 20 else 'Good performance, with room for optimization.'}
            Your most profitable job type appears to be kitchen renovations with an average margin of 32%.
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card revenue">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value">${total_revenue:,.0f}</div>
            <div class="stat-change">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                </svg>
                <span>All Time</span>
            </div>
        </div>
        
        <div class="stat-card expenses">
            <div class="stat-label">Total Expenses</div>
            <div class="stat-value">${total_expenses:,.0f}</div>
            <div class="stat-change">
                <span>{(total_expenses/total_revenue*100) if total_revenue > 0 else 0:.1f}% of revenue</span>
            </div>
        </div>
        
        <div class="stat-card profit">
            <div class="stat-label">Net Profit</div>
            <div class="stat-value">${net_profit:,.0f}</div>
            <div class="stat-change">
                <span>{profit_margin:.1f}% margin</span>
            </div>
        </div>
        
        <div class="stat-card jobs">
            <div class="stat-label">Avg Job Profit</div>
            <div class="stat-value">${net_profit/len(jobs) if jobs else 0:,.0f}</div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 2rem;">
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Job Performance Analysis</h2>
            </div>
            <div class="card-body">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Job</th>
                                <th>Revenue</th>
                                <th>Expenses</th>
                                <th>Profit</th>
                                <th>Margin</th>
                            </tr>
                        </thead>
                        <tbody>
    '''
    
    for perf in job_performance[:5]:  # Top 5 jobs
        color = 'var(--success)' if perf['margin'] > 20 else 'var(--warning)' if perf['margin'] > 10 else 'var(--danger)'
        content += f'''
                            <tr>
                                <td>{perf['job']['number']}</td>
                                <td>${perf['revenue']:,.0f}</td>
                                <td>${perf['expenses']:,.0f}</td>
                                <td style="color: {color}; font-weight: 600;">${perf['profit']:,.0f}</td>
                                <td style="color: {color}; font-weight: 600;">{perf['margin']:.1f}%</td>
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
                <h2 class="card-title">Expense Breakdown</h2>
            </div>
            <div class="card-body">
                <div class="chart-container" style="height: 300px;">
                    <div style="text-align: center; padding-top: 100px;">
                        <svg width="200" height="200" viewBox="0 0 42 42" style="transform: rotate(-90deg);">
                            <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#e5e7eb" stroke-width="3"></circle>
                            <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#5E3AEE" stroke-width="3" 
                                stroke-dasharray="30 70" stroke-dashoffset="0"></circle>
                            <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#10B981" stroke-width="3" 
                                stroke-dasharray="25 75" stroke-dashoffset="-30"></circle>
                            <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#F59E0B" stroke-width="3" 
                                stroke-dasharray="20 80" stroke-dashoffset="-55"></circle>
                        </svg>
                        <div style="margin-top: 1rem;">
                            <span style="display: inline-block; width: 12px; height: 12px; background: #5E3AEE; border-radius: 50%; margin-right: 0.5rem;"></span>Materials (30%)
                            <span style="display: inline-block; width: 12px; height: 12px; background: #10B981; border-radius: 50%; margin: 0 0.5rem 0 1rem;"></span>Labor (25%)
                            <span style="display: inline-block; width: 12px; height: 12px; background: #F59E0B; border-radius: 50%; margin: 0 0.5rem 0 1rem;"></span>Other (20%)
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-top: 1.5rem;">
        <div class="card-header">
            <h2 class="card-title">Monthly Trend</h2>
        </div>
        <div class="card-body">
            <div class="chart-container">
                <svg width="100%" height="300" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid meet">
                    <defs>
                        <linearGradient id="profitGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#5E3AEE;stop-opacity:0.3" />
                            <stop offset="100%" style="stop-color:#5E3AEE;stop-opacity:0" />
                        </linearGradient>
                    </defs>
                    <!-- Grid lines -->
                    <line x1="50" y1="250" x2="750" y2="250" stroke="#e5e7eb" stroke-width="1"/>
                    <line x1="50" y1="200" x2="750" y2="200" stroke="#e5e7eb" stroke-width="1"/>
                    <line x1="50" y1="150" x2="750" y2="150" stroke="#e5e7eb" stroke-width="1"/>
                    <line x1="50" y1="100" x2="750" y2="100" stroke="#e5e7eb" stroke-width="1"/>
                    <line x1="50" y1="50" x2="750" y2="50" stroke="#e5e7eb" stroke-width="1"/>
                    
                    <!-- Chart area -->
                    <path d="M 50 200 Q 200 180, 350 150 T 650 100 L 650 250 L 50 250 Z" fill="url(#profitGradient)"/>
                    <path d="M 50 200 Q 200 180, 350 150 T 650 100" stroke="#5E3AEE" stroke-width="3" fill="none"/>
                    
                    <!-- Data points -->
                    <circle cx="50" cy="200" r="5" fill="#5E3AEE"/>
                    <circle cx="350" cy="150" r="5" fill="#5E3AEE"/>
                    <circle cx="650" cy="100" r="5" fill="#5E3AEE"/>
                    
                    <!-- Labels -->
                    <text x="50" y="270" text-anchor="middle" fill="#6b7280" font-size="12">Jan</text>
                    <text x="350" y="270" text-anchor="middle" fill="#6b7280" font-size="12">Feb</text>
                    <text x="650" y="270" text-anchor="middle" fill="#6b7280" font-size="12">Mar</text>
                </svg>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Analytics', content, page_type='reports')

@app.route('/api/quick-add', methods=['POST'])
def quick_add_api():
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        doc = {
            'id': len(documents) + 1,
            'type': request.form.get('type'),
            'vendor': request.form.get('vendor'),
            'amount': float(request.form.get('amount', 0)),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': request.form.get('description', ''),
            'category': request.form.get('category'),
            'job_id': None
        }
        documents.append(doc)
        return jsonify({'success': True, 'message': 'Entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/documents')
def documents_page():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    all_docs = sorted(documents, key=lambda x: x['date'], reverse=True)
    
    content = '''
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">All Documents</h2>
            <a href="/upload" class="btn btn-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="16"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                Add Document
            </a>
        </div>
        <div class="card-body">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Vendor/Customer</th>
                            <th>Category</th>
                            <th>Job</th>
                            <th>Description</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    if all_docs:
        for doc in all_docs:
            job = next((j for j in jobs if str(j['id']) == doc.get('job_id')), None)
            job_info = f"{job['number']}" if job else "-"
            color = 'var(--success)' if doc['type'] == 'income' else 'var(--danger)'
            sign = '+' if doc['type'] == 'income' else '-'
            badge_class = 'badge-success' if doc['type'] == 'income' else 'badge-danger'
            
            content += f'''
                        <tr>
                            <td>{doc['date']}</td>
                            <td><span class="badge {badge_class}">{doc['type'].title()}</span></td>
                            <td>{doc['vendor']}</td>
                            <td>{doc.get('category', '-')}</td>
                            <td>{job_info}</td>
                            <td>{doc.get('description', '-')}</td>
                            <td style="color: {color}; font-weight: 600;">{sign}${doc['amount']:,.2f}</td>
                        </tr>
            '''
    else:
        content += '<tr><td colspan="7" style="text-align: center; color: var(--secondary);">No documents yet</td></tr>'
    
    content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return create_base_template('Documents', content, page_type='expenses')

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
    print(f"Starting Premium Profit Tracker AI on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)