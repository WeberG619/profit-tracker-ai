"""
Professional Contractor Profit Tracking System
A comprehensive financial management platform for contractors
"""
import os
import json
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, text
import anthropic

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'profit-tracker-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///profit_tracker.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
    jobs = db.relationship('Job', backref='company', lazy=True)
    documents = db.relationship('Document', backref='company', lazy=True)

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

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    job_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(200))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(20))
    description = db.Column(db.Text)
    quoted_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    documents = db.relationship('Document', backref='job', lazy=True)
    
    @property
    def total_expenses(self):
        return sum(d.total_amount for d in self.documents if d.document_type == 'expense' and d.total_amount) or 0
    
    @property
    def total_income(self):
        return sum(d.total_amount for d in self.documents if d.document_type == 'income' and d.total_amount) or 0
    
    @property
    def profit(self):
        return self.total_income - self.total_expenses
    
    @property
    def profit_margin(self):
        if self.total_income > 0:
            return round((self.profit / self.total_income) * 100, 1)
        return 0

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    document_type = db.Column(db.String(50), default='expense')  # expense, income
    category = db.Column(db.String(100))  # materials, labor, equipment, etc.
    vendor_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    total_amount = db.Column(db.Float)
    tax_amount = db.Column(db.Float)
    date = db.Column(db.Date)
    file_path = db.Column(db.String(500))
    file_type = db.Column(db.String(50))  # pdf, image
    invoice_number = db.Column(db.String(100))
    payment_status = db.Column(db.String(50), default='paid')  # paid, pending, overdue
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    ai_extracted_data = db.Column(db.Text)  # JSON string of AI extracted data

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()
    # Create default admin user if none exists
    if not User.query.filter_by(username='admin').first():
        admin_company = Company(name='Demo Company')
        db.session.add(admin_company)
        db.session.flush()
        
        admin_user = User(username='admin', email='admin@profittrackerai.com', company_id=admin_company.id, is_admin=True)
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing_professional.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login_professional.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # Create company and user
        company = Company(name=company_name)
        db.session.add(company)
        db.session.flush()
        
        user = User(username=username, email=email, company_id=company.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_professional.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get comprehensive stats
    company_id = current_user.company_id
    
    # Current month stats
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    # Get all documents
    all_docs = Document.query.filter_by(company_id=company_id).all()
    month_docs = Document.query.filter(
        Document.company_id == company_id,
        Document.created_at >= month_start
    ).all()
    
    # Calculate totals
    total_revenue = sum(d.total_amount for d in all_docs if d.document_type == 'income' and d.total_amount) or 0
    total_expenses = sum(d.total_amount for d in all_docs if d.document_type == 'expense' and d.total_amount) or 0
    month_revenue = sum(d.total_amount for d in month_docs if d.document_type == 'income' and d.total_amount) or 0
    month_expenses = sum(d.total_amount for d in month_docs if d.document_type == 'expense' and d.total_amount) or 0
    
    # Get jobs
    jobs = Job.query.filter_by(company_id=company_id).all()
    active_jobs = [j for j in jobs if j.status == 'active']
    
    # Calculate job stats
    profitable_jobs = [j for j in jobs if j.profit > 0]
    losing_jobs = [j for j in jobs if j.profit < 0]
    
    stats = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_revenue - total_expenses,
        'month_revenue': month_revenue,
        'month_expenses': month_expenses,
        'month_profit': month_revenue - month_expenses,
        'total_jobs': len(jobs),
        'active_jobs': len(active_jobs),
        'profitable_jobs': len(profitable_jobs),
        'losing_jobs': len(losing_jobs),
        'avg_profit_margin': sum(j.profit_margin for j in jobs) / len(jobs) if jobs else 0,
        'documents_count': len(all_docs),
        'pending_invoices': Document.query.filter_by(
            company_id=company_id, 
            document_type='income', 
            payment_status='pending'
        ).count()
    }
    
    # Get recent activity
    recent_docs = Document.query.filter_by(company_id=company_id)\
        .order_by(Document.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.filter_by(company_id=company_id)\
        .order_by(Job.created_at.desc()).limit(5).all()
    
    return render_template('dashboard_professional.html', 
                         stats=stats, 
                         recent_docs=recent_docs,
                         recent_jobs=recent_jobs,
                         active_jobs=active_jobs)

@app.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.filter_by(company_id=current_user.company_id)\
        .order_by(Job.created_at.desc()).all()
    return render_template('jobs_list.html', jobs=jobs)

@app.route('/jobs/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if request.method == 'POST':
        job = Job(
            company_id=current_user.company_id,
            job_number=request.form.get('job_number'),
            customer_name=request.form.get('customer_name'),
            customer_email=request.form.get('customer_email'),
            customer_phone=request.form.get('customer_phone'),
            description=request.form.get('description'),
            quoted_price=float(request.form.get('quoted_price', 0)),
            status='active'
        )
        db.session.add(job)
        db.session.commit()
        
        flash('Job created successfully!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))
    
    return render_template('job_new.html')

@app.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    job = Job.query.filter_by(id=job_id, company_id=current_user.company_id).first_or_404()
    documents = Document.query.filter_by(job_id=job_id).order_by(Document.date.desc()).all()
    return render_template('job_detail.html', job=job, documents=documents)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('upload'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('upload'))
        
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Create document record
            doc = Document(
                company_id=current_user.company_id,
                job_id=request.form.get('job_id'),
                document_type=request.form.get('document_type', 'expense'),
                category=request.form.get('category'),
                vendor_name=request.form.get('vendor_name'),
                description=request.form.get('description'),
                total_amount=float(request.form.get('total_amount', 0)),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date() if request.form.get('date') else date.today(),
                file_path=filename,
                file_type='pdf' if filename.lower().endswith('.pdf') else 'image'
            )
            db.session.add(doc)
            db.session.commit()
            
            # Process with AI if API key is available
            if os.environ.get('ANTHROPIC_API_KEY'):
                process_with_ai(doc)
            
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('document_detail', doc_id=doc.id))
    
    jobs = Job.query.filter_by(company_id=current_user.company_id, status='active').all()
    return render_template('upload_professional.html', jobs=jobs)

@app.route('/documents')
@login_required
def documents():
    docs = Document.query.filter_by(company_id=current_user.company_id)\
        .order_by(Document.date.desc()).all()
    return render_template('documents_list.html', documents=docs)

@app.route('/documents/<int:doc_id>')
@login_required
def document_detail(doc_id):
    doc = Document.query.filter_by(id=doc_id, company_id=current_user.company_id).first_or_404()
    return render_template('document_detail.html', document=doc)

@app.route('/reports')
@login_required
def reports():
    # Profit/Loss by month
    company_id = current_user.company_id
    
    # Get last 12 months of data
    months_data = []
    for i in range(12):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1)
        if i == 0:
            month_end = datetime.now()
        else:
            next_month = month_start + timedelta(days=32)
            month_end = datetime(next_month.year, next_month.month, 1)
        
        month_docs = Document.query.filter(
            Document.company_id == company_id,
            Document.date >= month_start.date(),
            Document.date < month_end.date()
        ).all()
        
        revenue = sum(d.total_amount for d in month_docs if d.document_type == 'income' and d.total_amount) or 0
        expenses = sum(d.total_amount for d in month_docs if d.document_type == 'expense' and d.total_amount) or 0
        
        months_data.append({
            'month': month_start.strftime('%B %Y'),
            'revenue': revenue,
            'expenses': expenses,
            'profit': revenue - expenses
        })
    
    months_data.reverse()
    
    # Top expense categories
    categories = db.session.query(
        Document.category,
        func.sum(Document.total_amount).label('total')
    ).filter(
        Document.company_id == company_id,
        Document.document_type == 'expense',
        Document.category.isnot(None)
    ).group_by(Document.category).all()
    
    return render_template('reports.html', months_data=months_data, categories=categories)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'professional', 'timestamp': datetime.now().isoformat()})

def process_with_ai(document):
    """Process document with AI to extract data"""
    try:
        # This is where you'd integrate with Anthropic API
        # For now, just mark as processed
        document.processed = True
        db.session.commit()
    except Exception as e:
        app.logger.error(f"AI processing error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)