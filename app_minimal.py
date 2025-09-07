"""
Minimal Flask app for testing
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Profit Tracker AI is running',
        'env': {
            'has_anthropic_key': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'has_secret_key': bool(os.environ.get('SECRET_KEY')),
            'database_url': bool(os.environ.get('DATABASE_URL')),
            'port': os.environ.get('PORT', 'not set')
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        'error': str(e),
        'type': type(e).__name__
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)