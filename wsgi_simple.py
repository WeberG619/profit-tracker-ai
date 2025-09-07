"""
Simplified WSGI entry point for debugging
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a minimal Flask app directly
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-2024')

# Simple HTML template
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Profit Tracker AI</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
        h1 { color: #333; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        a { color: #1976d2; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Profit Tracker AI</h1>
        <p>AI-powered receipt tracking for contractors</p>
        
        <div class="info">
            <h3>System Status: ✅ Running</h3>
            <p>The application is running in minimal mode for debugging.</p>
        </div>
        
        <h3>Available Endpoints:</h3>
        <ul>
            <li><a href="/health">/health</a> - Check system status</li>
            <li><a href="/test-db">/test-db</a> - Test database connection</li>
        </ul>
        
        <p><strong>Note:</strong> Full functionality is being restored. Check back shortly.</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Simple landing page"""
    return LOGIN_HTML

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'mode': 'minimal',
        'environment': {
            'RENDER': os.environ.get('RENDER', 'false'),
            'DATABASE_URL': 'set' if os.environ.get('DATABASE_URL') else 'not set',
            'PORT': os.environ.get('PORT', 'not set')
        }
    })

@app.route('/test-db')
def test_db():
    """Test database connection"""
    try:
        from sqlalchemy import create_engine, text
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({'status': 'error', 'message': 'No DATABASE_URL set'})
        
        # Handle Render's postgres:// URLs
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1'))
            
        return jsonify({
            'status': 'connected',
            'database': 'postgresql',
            'message': 'Database connection successful'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)