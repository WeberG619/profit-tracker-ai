# Phase 1: Invoice Support Implementation Plan

## Overview
Extend the current receipt tracking system to handle both receipts (money out) and invoices (money in), creating a complete financial picture for contractors.

## Database Changes

### 1. Create Migration Script
```python
# migrations/add_invoice_support.py
"""
ALTER TABLE receipt RENAME TO document;

ALTER TABLE document 
ADD COLUMN document_type VARCHAR(50) DEFAULT 'receipt',
ADD COLUMN direction VARCHAR(20) DEFAULT 'expense',
ADD COLUMN status VARCHAR(20) DEFAULT 'paid',
ADD COLUMN due_date DATE,
ADD COLUMN customer_id INTEGER,
ADD COLUMN customer_name VARCHAR(255),
ADD COLUMN customer_email VARCHAR(255),
ADD COLUMN customer_phone VARCHAR(50),
ADD COLUMN sent_date DATETIME,
ADD COLUMN paid_date DATETIME,
ADD COLUMN payment_method VARCHAR(50),
ADD COLUMN invoice_number VARCHAR(100),
ADD COLUMN terms TEXT,
ADD COLUMN notes TEXT;

-- Create index for faster queries
CREATE INDEX idx_document_type ON document(document_type);
CREATE INDEX idx_document_status ON document(status);
CREATE INDEX idx_due_date ON document(due_date);
"""
```

### 2. Update Models
```python
# models.py
class Document(db.Model):  # Renamed from Receipt
    # Existing fields...
    
    # Document type fields
    document_type = db.Column(db.String(50), default='receipt')  # receipt/invoice/quote/purchase_order
    direction = db.Column(db.String(20), default='expense')  # expense/income
    status = db.Column(db.String(20), default='paid')  # paid/pending/overdue/draft
    
    # Invoice-specific fields
    due_date = db.Column(db.Date)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer_name = db.Column(db.String(255))  # Denormalized for quick access
    customer_email = db.Column(db.String(255))
    customer_phone = db.Column(db.String(50))
    
    # Tracking fields
    sent_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    invoice_number = db.Column(db.String(100))
    
    # Content fields
    terms = db.Column(db.Text)  # Payment terms
    notes = db.Column(db.Text)  # Internal notes
    
    @property
    def is_overdue(self):
        if self.document_type == 'invoice' and self.status == 'pending':
            return self.due_date < datetime.now().date() if self.due_date else False
        return False
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (datetime.now().date() - self.due_date).days
        return 0

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = db.relationship('Document', backref='customer', lazy=True)
```

## UI Changes

### 1. Update Upload Page
```html
<!-- templates/upload_document.html -->
<div class="document-type-selector">
    <h3>What are you uploading?</h3>
    <div class="grid grid-cols-2 gap-4">
        <button onclick="selectDocumentType('receipt')" class="type-card">
            <i class="fas fa-receipt text-4xl text-red-500"></i>
            <h4>Receipt</h4>
            <p>Money you spent</p>
        </button>
        <button onclick="selectDocumentType('invoice')" class="type-card">
            <i class="fas fa-file-invoice-dollar text-4xl text-green-500"></i>
            <h4>Invoice</h4>
            <p>Money owed to you</p>
        </button>
    </div>
</div>
```

### 2. New Accounts Receivable Dashboard
```html
<!-- templates/accounts_receivable.html -->
<div class="ar-dashboard">
    <!-- Summary Cards -->
    <div class="grid grid-cols-4 gap-4">
        <div class="stat-card bg-green-100">
            <h3>Total Outstanding</h3>
            <p class="text-3xl font-bold">${{ outstanding_total }}</p>
        </div>
        <div class="stat-card bg-yellow-100">
            <h3>Overdue</h3>
            <p class="text-3xl font-bold text-red-600">${{ overdue_total }}</p>
        </div>
        <div class="stat-card bg-blue-100">
            <h3>Due This Week</h3>
            <p class="text-3xl font-bold">${{ due_this_week }}</p>
        </div>
        <div class="stat-card">
            <h3>Collection Rate</h3>
            <p class="text-3xl font-bold">{{ collection_rate }}%</p>
        </div>
    </div>
    
    <!-- Overdue Invoices Alert -->
    {% if overdue_invoices %}
    <div class="alert alert-warning">
        <h4>Action Required: {{ overdue_invoices|length }} Overdue Invoices</h4>
        {% for invoice in overdue_invoices[:3] %}
        <div class="overdue-item">
            <span>{{ invoice.customer_name }}</span>
            <span>${{ invoice.total_amount }}</span>
            <span>{{ invoice.days_overdue }} days overdue</span>
            <button onclick="sendReminder({{ invoice.id }})">Send Reminder</button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</div>
```

### 3. Enhanced Document Review
```python
# routes/documents.py
@app.route('/document/<int:document_id>')
@login_required
def review_document(document_id):
    doc = Document.query.filter_by(
        id=document_id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    if doc.document_type == 'invoice':
        return render_template('review_invoice.html', invoice=doc)
    else:
        return render_template('review_receipt.html', receipt=doc)
```

## AI Updates

### 1. Document Type Detection
```python
# document_processor.py
def detect_document_type(extracted_data):
    """Use AI to determine if this is a receipt or invoice"""
    
    # Keywords that indicate an invoice
    invoice_keywords = ['invoice', 'bill to', 'due date', 'terms', 'net 30', 'payment due']
    receipt_keywords = ['receipt', 'paid', 'transaction', 'change', 'cash', 'card']
    
    text = extracted_data.get('full_text', '').lower()
    
    invoice_score = sum(1 for keyword in invoice_keywords if keyword in text)
    receipt_score = sum(1 for keyword in receipt_keywords if keyword in text)
    
    # Additional logic
    if 'due' in text and 'date' in text:
        invoice_score += 2
    if 'total due' in text:
        invoice_score += 3
        
    return 'invoice' if invoice_score > receipt_score else 'receipt'
```

### 2. Enhanced Data Extraction
```python
def extract_invoice_data(image_path):
    """Extract invoice-specific data"""
    extracted = process_document_image(image_path)
    
    # Add invoice-specific extraction
    extracted['customer_info'] = extract_customer_info(extracted['full_text'])
    extracted['due_date'] = extract_due_date(extracted['full_text'])
    extracted['invoice_number'] = extract_invoice_number(extracted['full_text'])
    extracted['payment_terms'] = extract_payment_terms(extracted['full_text'])
    
    return extracted
```

## New Features

### 1. Quick Actions Menu
```javascript
// Quick action buttons for invoices
function showInvoiceActions(invoiceId) {
    return `
        <div class="quick-actions">
            <button onclick="markAsPaid(${invoiceId})">
                <i class="fas fa-check"></i> Mark as Paid
            </button>
            <button onclick="sendReminder(${invoiceId})">
                <i class="fas fa-bell"></i> Send Reminder
            </button>
            <button onclick="duplicateInvoice(${invoiceId})">
                <i class="fas fa-copy"></i> Duplicate
            </button>
            <button onclick="exportPDF(${invoiceId})">
                <i class="fas fa-file-pdf"></i> Export PDF
            </button>
        </div>
    `;
}
```

### 2. Collection Reminders
```python
# reminder_service.py
def send_payment_reminder(invoice_id):
    """Send automated payment reminder"""
    invoice = Document.query.get(invoice_id)
    
    if invoice.customer_email:
        # Email reminder
        subject = f"Payment Reminder: Invoice #{invoice.invoice_number}"
        body = render_template('email/payment_reminder.html', 
                             invoice=invoice,
                             days_overdue=invoice.days_overdue)
        send_email(invoice.customer_email, subject, body)
        
    if invoice.customer_phone:
        # SMS reminder
        message = f"Reminder: Invoice #{invoice.invoice_number} for ${invoice.total_amount} is {invoice.days_overdue} days overdue."
        send_sms(invoice.customer_phone, message)
    
    # Log reminder
    invoice.notes = f"{invoice.notes}\nReminder sent on {datetime.now()}"
    db.session.commit()
```

## Dashboard Updates

### 1. Unified Financial Dashboard
```python
@app.route('/financial-dashboard')
@login_required
def financial_dashboard():
    # Income (invoices)
    total_income = Document.query.filter_by(
        company_id=current_user.company_id,
        document_type='invoice',
        status='paid'
    ).with_entities(func.sum(Document.total_amount)).scalar() or 0
    
    # Expenses (receipts)
    total_expenses = Document.query.filter_by(
        company_id=current_user.company_id,
        document_type='receipt'
    ).with_entities(func.sum(Document.total_amount)).scalar() or 0
    
    # Outstanding
    outstanding = Document.query.filter_by(
        company_id=current_user.company_id,
        document_type='invoice',
        status='pending'
    ).with_entities(func.sum(Document.total_amount)).scalar() or 0
    
    # Overdue
    overdue_invoices = Document.query.filter(
        Document.company_id == current_user.company_id,
        Document.document_type == 'invoice',
        Document.status == 'pending',
        Document.due_date < datetime.now().date()
    ).all()
    
    return render_template('financial_dashboard.html',
                         income=total_income,
                         expenses=total_expenses,
                         profit=total_income - total_expenses,
                         outstanding=outstanding,
                         overdue_invoices=overdue_invoices)
```

## Migration Path

### Step 1: Database Update (Day 1)
1. Backup existing database
2. Run migration script
3. Update all "receipt" references to "document"
4. Set document_type='receipt' for all existing records

### Step 2: Code Updates (Day 2-3)
1. Update models.py
2. Update all imports and references
3. Add new routes for invoices
4. Update existing views

### Step 3: UI Updates (Day 4-5)
1. Add document type selector
2. Create invoice-specific views
3. Update navigation
4. Add accounts receivable dashboard

### Step 4: Testing (Day 6-7)
1. Test receipt upload (ensure nothing breaks)
2. Test invoice upload
3. Test document type detection
4. Test reminder system
5. Test with real contractors

## Benefits for Contractors
1. **Complete Picture**: See money in AND out
2. **Get Paid Faster**: Automated reminders
3. **Never Forget**: All unpaid invoices in one place
4. **Cash Flow Clarity**: Know what's coming
5. **Tax Ready**: Income and expenses organized

This gives you a solid foundation to build on!