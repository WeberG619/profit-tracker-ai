from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20))
    twilio_configured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    jobs = db.relationship('Job', backref='company', lazy=True)
    receipts = db.relationship('Receipt', backref='company', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Receipt(db.Model):
    # Note: Keeping table name as 'receipt' for backward compatibility
    # But this now handles both receipts and invoices
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    vendor_name = db.Column(db.String(200))
    total_amount = db.Column(db.Float)
    date = db.Column(db.Date)
    receipt_number = db.Column(db.String(100))
    extracted_data = db.Column(db.JSON)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    uploaded_by = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))  # Track SMS sender
    upload_method = db.Column(db.String(20), default='web')  # 'web' or 'sms'
    receipt_hash = db.Column(db.String(64))  # MD5 hash for quick duplicate checking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields for invoice support
    document_type = db.Column(db.String(50), default='receipt')  # receipt/invoice/quote
    direction = db.Column(db.String(20), default='expense')  # expense/income
    status = db.Column(db.String(20), default='paid')  # paid/pending/overdue/draft
    
    # Invoice-specific fields
    due_date = db.Column(db.Date)
    customer_name = db.Column(db.String(255))
    customer_email = db.Column(db.String(255))
    customer_phone = db.Column(db.String(50))
    invoice_number = db.Column(db.String(100))
    
    # Payment tracking
    sent_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    
    # Additional fields
    terms = db.Column(db.Text)  # Payment terms
    notes = db.Column(db.Text)  # Internal notes
    
    # Relationships
    line_items = db.relationship('LineItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    job = db.relationship('Job', backref='receipts')
    
    @property
    def is_overdue(self):
        """Check if an invoice is overdue"""
        if self.document_type == 'invoice' and self.status == 'pending' and self.due_date:
            return self.due_date < datetime.now().date()
        return False
    
    @property
    def days_overdue(self):
        """Calculate how many days overdue an invoice is"""
        if self.is_overdue:
            return (datetime.now().date() - self.due_date).days
        return 0
    
    @property
    def display_name(self):
        """Get appropriate name for display"""
        if self.document_type == 'invoice':
            return self.customer_name or 'Unknown Customer'
        else:
            return self.vendor_name or 'Unknown Vendor'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(200))
    quoted_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Add unique constraint for job_number + company_id
    __table_args__ = (db.UniqueConstraint('job_number', 'company_id'),)
    
    @property
    def current_costs(self):
        """Calculate total costs from all receipts"""
        return sum(r.total or 0 for r in self.receipts)
    
    @property
    def profit_amount(self):
        """Calculate profit amount"""
        if self.quoted_price:
            return self.quoted_price - self.current_costs
        return 0
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.quoted_price and self.quoted_price > 0:
            return ((self.quoted_price - self.current_costs) / self.quoted_price) * 100
        return 0
    
    @property
    def status_color(self):
        """Return color based on profit margin"""
        margin = self.profit_margin
        if margin > 20:
            return 'green'
        elif margin >= 5:
            return 'yellow'
        else:
            return 'red'

class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    description = db.Column(db.String(500))
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))