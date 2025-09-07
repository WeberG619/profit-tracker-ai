"""
Ultra minimal app - absolute bare minimum
"""
import os
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-2024')

# Simple HTML pages
@app.route('/')
def index():
    return '''
    <h1>Profit Tracker AI</h1>
    <p>Stop losing money on jobs. AI-powered receipt tracking for contractors.</p>
    <a href="/login">Login</a> | <a href="/register">Register</a>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == 'admin' and password == 'admin123':
            session['username'] = username
            return redirect('/dashboard')
        return '''
        <h1>Login</h1>
        <p style="color: red;">Invalid credentials</p>
        <form method="POST">
            <input name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        <p>Demo: admin / admin123</p>
        '''
    
    return '''
    <h1>Login</h1>
    <form method="POST">
        <input name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
    <p>Demo: admin / admin123</p>
    '''

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    return f'''
    <h1>Dashboard - Welcome {session['username']}!</h1>
    <p><a href="/logout">Logout</a></p>
    <h2>Quick Actions</h2>
    <ul>
        <li><a href="/upload">Upload Receipt</a></li>
        <li><a href="/receipts">View Receipts</a></li>
        <li><a href="/invoices">Manage Invoices</a></li>
    </ul>
    <h2>Stats</h2>
    <ul>
        <li>Total Documents: 0</li>
        <li>Total Expenses: $0.00</li>
        <li>Total Income: $0.00</li>
        <li>Net Profit: $0.00</li>
    </ul>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register')
def register():
    return '<h1>Registration coming soon!</h1><a href="/">Back</a>'

@app.route('/upload')
def upload():
    return '<h1>Upload coming soon!</h1><a href="/dashboard">Back</a>'

@app.route('/receipts')
def receipts():
    return '<h1>Receipts coming soon!</h1><a href="/dashboard">Back</a>'

@app.route('/invoices')
def invoices():
    return '<h1>Invoices coming soon!</h1><a href="/dashboard">Back</a>'

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'ultra_minimal'}

@app.route('/debug')
def debug():
    import sys
    return f'''
    <h1>Debug Info</h1>
    <ul>
        <li>Python Version: {sys.version}</li>
        <li>Flask Version: {Flask.__version__ if hasattr(Flask, '__version__') else 'Unknown'}</li>
        <li>Environment: {os.environ.get('RENDER', 'Not on Render')}</li>
        <li>Port: {os.environ.get('PORT', 'Not set')}</li>
        <li>Routes: {', '.join([rule.endpoint for rule in app.url_map.iter_rules()])}</li>
    </ul>
    '''

if __name__ == '__main__':
    app.run()