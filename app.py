import os
import sys
from flask import Flask

# Add logging to see what's happening
print("Starting Profit Tracker AI...")
print(f"Python version: {sys.version}")
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
print(f"RENDER environment variable: {os.environ.get('RENDER', 'Not set')}")

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profit Tracker AI</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 50px; }
            .success { color: green; }
            .info { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Profit Tracker AI</h1>
        <p class="success">✅ Server is running successfully!</p>
        <div class="info">
            <h3>Debug Information:</h3>
            <p>Port: {}</p>
            <p>Environment: {}</p>
            <p>Python Version: {}</p>
        </div>
        <p><a href="/health">Check Health</a></p>
    </body>
    </html>
    '''.format(
        os.environ.get('PORT', 'Not set'), 
        'Render' if os.environ.get('RENDER') else 'Local',
        sys.version
    )

@app.route('/health')
def health():
    return 'OK - Profit Tracker AI is healthy!'

# Add error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"ERROR: {str(e)}")
    return f"Error: {str(e)}", 500

print("Flask app created successfully")

# This is crucial for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)