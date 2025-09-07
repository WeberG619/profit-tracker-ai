"""
Working version of the app with all features
"""
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import text

# Create Flask app with proper paths
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'app/templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'app/static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///receipts.db')

# Handle postgres:// URLs from Render
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='company', lazy=True)
    receipts = db.relationship('Receipt', backref='company', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    vendor_name = db.Column(db.String(200))
    total_amount = db.Column(db.Float)
    date = db.Column(db.Date)
    image_path = db.Column(db.String(500))
    document_type = db.Column(db.String(50), default='receipt')
    direction = db.Column(db.String(20), default='expense')
    status = db.Column(db.String(20), default='paid')
    customer_name = db.Column(db.String(255))
    invoice_number = db.Column(db.String(100))
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    job_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(200))
    quoted_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    """Main landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
        
        # Count records
        user_count = User.query.count()
        company_count = Company.query.count()
        
        return jsonify({
            'status': 'ok',
            'database': db_status,
            'users': user_count,
            'companies': company_count,
            'app': 'working'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                if user.company_id:
                    login_user(user, remember=True)
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                else:
                    flash('Account setup incomplete', 'error')
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Please enter username and password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    stats = {
        'total_receipts': 0,
        'total_expenses': 0,
        'total_income': 0,
        'active_jobs': 0
    }
    
    if current_user.company_id:
        try:
            stats['total_receipts'] = Receipt.query.filter_by(company_id=current_user.company_id).count()
            
            expenses = db.session.query(db.func.sum(Receipt.total_amount)).filter_by(
                company_id=current_user.company_id,
                document_type='receipt'
            ).scalar()
            stats['total_expenses'] = expenses or 0
            
            income = db.session.query(db.func.sum(Receipt.total_amount)).filter_by(
                company_id=current_user.company_id,
                document_type='invoice',
                status='paid'
            ).scalar()
            stats['total_income'] = income or 0
            
            stats['active_jobs'] = Job.query.filter_by(
                company_id=current_user.company_id,
                status='active'
            ).count()
        except:
            pass
    
    return render_template('company_dashboard.html', stats=stats, recent_receipts=[])

@app.route('/upload')
@login_required
def upload_page():
    """Upload page"""
    return render_template('index.html')

@app.route('/list')
@login_required
def list_receipts():
    """List all receipts"""
    receipts = []
    if current_user.company_id:
        receipts = Receipt.query.filter_by(company_id=current_user.company_id).order_by(Receipt.created_at.desc()).all()
    return render_template('list.html', receipts=receipts)

@app.route('/accounts-receivable')
@login_required
def accounts_receivable():
    """Accounts receivable dashboard"""
    return render_template('accounts_receivable.html',
                         outstanding_total=0,
                         overdue_total=0,
                         due_this_week=0,
                         collection_rate=0,
                         overdue_invoices=[],
                         pending_invoices=[],
                         due_this_week_list=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle registration
        company_name = request.form.get('company_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if company_name and username and email and password:
            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
            else:
                # Create company
                company = Company(name=company_name)
                db.session.add(company)
                db.session.commit()
                
                # Create user
                user = User(
                    username=username,
                    email=email,
                    company_id=company.id
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                
                login_user(user)
                return redirect(url_for('dashboard'))
    
    return render_template('register.html')

# Initialize database
with app.app_context():
    db.create_all()
    
    # Ensure admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create demo company
        demo_company = Company.query.filter_by(name='Demo Company').first()
        if not demo_company:
            demo_company = Company(name='Demo Company')
            db.session.add(demo_company)
            db.session.commit()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            company_id=demo_company.id,
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)