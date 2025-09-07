from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Profit Tracker AI</h1><p>Working!</p>'

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    app.run()