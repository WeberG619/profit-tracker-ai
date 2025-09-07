from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import io
import sys
from datetime import datetime
import json
from .models import db, Receipt, Job, LineItem, Company, User
from .config import Config
from .receipt_processor import process_receipt_image
from .sms_handler import parse_job_number, download_mms_media, send_sms_response, calculate_job_total, format_currency
from .analytics import get_dashboard_stats, get_jobs_summary, get_job_timeline, generate_daily_summary
from .insights import JobInsights, PriceRecommendation, AlertMonitor, get_profit_trends, get_job_type_profitability
from .export_utils import export_receipts_csv, export_job_summary_pdf, export_receipts_zip
from .scheduler import job_scheduler
from .auth import login_manager, company_required
from .money_losers import check_job_keywords
from twilio.twiml.messaging_response import MessagingResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Check required environment variables on startup
required_vars = {
    'ANTHROPIC_API_KEY': 'Required for OCR processing of receipts',
    'DATABASE_URL': 'Required for data persistence (PostgreSQL)'
}

missing_vars = []
for var, description in required_vars.items():
    if not os.getenv(var):
        missing_vars.append(f"- {var}: {description}")
        logger.warning(f"Missing environment variable: {var}")

if missing_vars:
    logger.warning("Missing required environment variables:\n" + "\n".join(missing_vars))
    logger.warning("The app will run but some features may not work properly.")

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager.init_app(app)

# Initialize scheduler
try:
    if not app.config.get('TESTING'):
        job_scheduler.init_app(app)
except Exception as e:
    logger.warning(f"Scheduler initialization failed: {str(e)}")
    # Continue without scheduler

# Create upload folder if it doesn't exist
try:
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder):
        # In production (Render), use /tmp for uploads
        if os.environ.get('RENDER'):
            upload_folder = '/tmp/uploads'
        else:
            upload_folder = os.path.join(os.path.dirname(__file__), '..', upload_folder)
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    logger.info(f"Upload folder set to: {upload_folder}")
except Exception as e:
    logger.warning(f"Could not create upload folder: {str(e)}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create test jobs if they don't exist
        test_jobs = [
            {'job_number': '1001', 'customer_name': 'Johnson Construction', 'quoted_price': 15000.00},
            {'job_number': '1002', 'customer_name': 'Smith Renovations', 'quoted_price': 8500.00},
            {'job_number': '1003', 'customer_name': 'Davis Plumbing', 'quoted_price': 3200.00}
        ]
        
        for job_data in test_jobs:
            if not Job.query.filter_by(job_number=job_data['job_number']).first():
                job = Job(**job_data)
                db.session.add(job)
        
        db.session.commit()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')
        if 'memory' in db_uri:
            db_type = 'sqlite-memory'
        elif 'sqlite' in db_uri:
            db_type = 'sqlite-file'
        elif 'postgresql' in db_uri:
            db_type = 'postgresql'
        else:
            db_type = 'unknown'
    except Exception as e:
        db_status = f'error: {str(e)}'
        db_type = 'error'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'database_type': db_type,
        'render': bool(os.environ.get('RENDER')),
        'has_database_url': bool(os.environ.get('DATABASE_URL'))
    })

@app.route('/init-db-emergency')
def init_db_emergency():
    """Emergency database initialization endpoint"""
    try:
        # Check if already initialized
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            return jsonify({
                'status': 'already_initialized',
                'message': 'Database already has tables',
                'tables': existing_tables
            })
        
        # Create all tables
        db.create_all()
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Create default admin user
        if not User.query.first():
            company = Company(
                name="Default Company",
                phone_number="+1234567890"
            )
            db.session.add(company)
            db.session.commit()
            
            user = User(
                username="admin",
                email="admin@example.com",
                company_id=company.id,
                is_admin=True
            )
            user.set_password("admin123")
            db.session.add(user)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Database initialized successfully',
            'tables': tables,
            'default_user': 'admin/admin123'
        })
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'database_uri': app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')[:50] + '...'
        }), 500

@app.route('/debug-env')
def debug_env():
    """Debug endpoint to check environment"""
    # Only show in development or with a secret parameter
    if not (app.debug or request.args.get('secret') == 'check-env-2024'):
        return jsonify({'error': 'Not available'}), 403
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    return jsonify({
        'upload_folder': app.config.get('UPLOAD_FOLDER'),
        'upload_folder_exists': os.path.exists(app.config.get('UPLOAD_FOLDER', '')),
        'anthropic_key_set': bool(api_key),
        'anthropic_key_format': f"sk-ant-...{api_key[-4:]}" if api_key and len(api_key) > 10 else "Not set",
        'anthropic_key_length': len(api_key) if api_key else 0,
        'database_connected': bool(os.environ.get('DATABASE_URL')),
        'render_env': bool(os.environ.get('RENDER')),
        'allowed_extensions': list(app.config.get('ALLOWED_EXTENSIONS', [])),
        'max_content_length': app.config.get('MAX_CONTENT_LENGTH'),
        'pymupdf_available': 'fitz' in sys.modules or 'PyMuPDF' in sys.modules
    })

@app.route('/test-pdf-processing')
def test_pdf_processing():
    """Test PDF processing capability"""
    if not (app.debug or request.args.get('secret') == 'test-pdf-2024'):
        return jsonify({'error': 'Not available'}), 403
    
    try:
        # Test PyMuPDF import
        import fitz
        fitz_version = fitz.VersionBind
        
        # Test creating a simple PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test PDF")
        
        # Test saving to memory
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Test Anthropic client
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        return jsonify({
            'status': 'success',
            'fitz_version': fitz_version,
            'pdf_test': 'PDF creation successful',
            'pdf_size': len(pdf_bytes),
            'anthropic_client': 'initialized successfully'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/upload-debug', methods=['POST'])
@login_required
@company_required
def upload_debug():
    """Debug version of upload with detailed error tracking"""
    import traceback
    
    try:
        # Step 1: Check request
        if 'file' not in request.files:
            return jsonify({'error': 'No file in request', 'step': 1}), 400
            
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected', 'step': 2}), 400
            
        # Step 2: Check file type
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type: {file.filename}', 'step': 3}), 400
            
        # Step 3: Prepare filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Step 4: Save file
        upload_folder = app.config.get('UPLOAD_FOLDER')
        filepath = os.path.join(upload_folder, filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({'error': f'File save failed: {str(e)}', 'step': 4, 'trace': traceback.format_exc()}), 500
            
        # Step 5: Create receipt record
        try:
            receipt = Receipt(
                company_id=current_user.company_id,
                image_path=filename,
                uploaded_by=current_user.username
            )
            db.session.add(receipt)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}', 'step': 5, 'trace': traceback.format_exc()}), 500
            
        # Step 6: Process image (if API key exists)
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                extracted_data = process_receipt_image(filepath)
                receipt.vendor_name = extracted_data.get('vendor')
                receipt.total_amount = extracted_data.get('total')
                receipt.date = datetime.strptime(extracted_data.get('date'), '%Y-%m-%d').date() if extracted_data.get('date') else None
                receipt.extracted_data = extracted_data
                db.session.commit()
            except Exception as e:
                return jsonify({
                    'error': f'OCR processing error: {str(e)}', 
                    'step': 6, 
                    'trace': traceback.format_exc(),
                    'receipt_id': receipt.id
                }), 500
        
        return jsonify({
            'success': True,
            'receipt_id': receipt.id,
            'redirect': url_for('review_receipt', receipt_id=receipt.id)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'step': 0,
            'trace': traceback.format_exc()
        }), 500

@app.route('/')
@login_required
@company_required
def index():
    # Check if job parameter is passed for pre-selection
    job_number = request.args.get('job')
    return render_template('index.html', preselected_job=job_number)

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    jobs = get_jobs_summary()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@app.route('/debug-upload-form')
@login_required
@company_required
def debug_upload_form():
    """Debug upload form that uses the debug endpoint"""
    return '''
    <html><body>
    <h2>Debug Upload Form</h2>
    <p>This will show detailed error information</p>
    <form id="debugForm">
        <input type="file" id="file" accept=".pdf,.jpg,.png" required>
        <button type="submit">Debug Upload</button>
    </form>
    <pre id="result"></pre>
    <script>
    document.getElementById('debugForm').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('file').files[0]);
        
        try {
            const response = await fetch('/upload-debug', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            if (data.success) {
                setTimeout(() => window.location.href = data.redirect, 2000);
            }
        } catch (error) {
            document.getElementById('result').textContent = 'Network error: ' + error.message;
        }
    };
    </script>
    </body></html>
    '''

@app.route('/upload-test', methods=['GET', 'POST'])
@login_required
@company_required
def upload_test():
    """Simple upload test without OCR"""
    if request.method == 'GET':
        return '''
        <html><body>
        <h2>Simple Upload Test</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf,.jpg,.png" required>
            <button type="submit">Test Upload</button>
        </form>
        </body></html>
        '''
    
    try:
        file = request.files.get('file')
        if not file:
            return "No file provided", 400
            
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Test saving file
        upload_folder = app.config.get('UPLOAD_FOLDER', '/tmp/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        # Create basic receipt record
        receipt = Receipt(
            company_id=current_user.company_id,
            image_path=filename,
            uploaded_by=current_user.username,
            vendor_name="Test Upload",
            total_amount=0.0,
            extracted_data={"test": True, "file_size": file_size}
        )
        db.session.add(receipt)
        db.session.commit()
        
        # Clean up test file
        os.remove(filepath)
        
        return f'''
        <html><body>
        <h2>Upload Test Successful!</h2>
        <p>File: {filename}</p>
        <p>Size: {file_size} bytes</p>
        <p>Receipt ID: {receipt.id}</p>
        <p>Upload folder: {upload_folder}</p>
        <a href="/">Back to main app</a>
        </body></html>
        '''
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return f'''
        <html><body>
        <h2>Upload Test Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{error_trace}</pre>
        </body></html>
        ''', 500

@app.route('/upload', methods=['POST'])
@login_required
@company_required
def upload_file():
    try:
        logger.info(f"Upload request from user {current_user.username}")
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Uploading file: {file.filename}")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Use the configured upload folder
            upload_folder = app.config.get('UPLOAD_FOLDER')
            
            filepath = os.path.join(upload_folder, filename)
            logger.info(f"Saving to: {filepath}")
            file.save(filepath)
            
            # Create receipt record
            receipt = Receipt(
                company_id=current_user.company_id,
                image_path=filename,
                uploaded_by=request.form.get('uploaded_by', current_user.username)
            )
            db.session.add(receipt)
            db.session.commit()
            logger.info(f"Receipt record created with ID: {receipt.id}")
            
            # Check if we have Anthropic API key
            if not os.getenv('ANTHROPIC_API_KEY'):
                logger.warning("ANTHROPIC_API_KEY not set, skipping OCR processing")
                receipt.extracted_data = {
                    'error': 'OCR processing not configured',
                    'note': 'ANTHROPIC_API_KEY environment variable not set'
                }
                receipt.vendor_name = "Manual Entry Required"
                receipt.total_amount = 0.0
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'receipt_id': receipt.id,
                    'redirect': url_for('review_receipt', receipt_id=receipt.id),
                    'warning': 'OCR processing not available - manual entry required'
                })
            
            # Process the image
            try:
                logger.info("Starting OCR processing...")
                extracted_data = process_receipt_image(filepath)
                logger.info(f"OCR completed: {extracted_data}")
                
                # Update receipt with extracted data
                receipt.vendor_name = extracted_data.get('vendor')
                receipt.total_amount = extracted_data.get('total')
                receipt.date = datetime.strptime(extracted_data.get('date'), '%Y-%m-%d').date() if extracted_data.get('date') else None
                receipt.receipt_number = extracted_data.get('receipt_number')
                receipt.extracted_data = extracted_data
                
                # Add line items
                for item in extracted_data.get('line_items', []):
                    line_item = LineItem(
                        receipt_id=receipt.id,
                        description=item.get('description'),
                        amount=item.get('amount'),
                        category=item.get('category')
                    )
                    db.session.add(line_item)
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
                receipt.extracted_data = {'error': str(e)}
                receipt.vendor_name = "Processing Failed"
                receipt.total_amount = 0.0
                db.session.commit()
            
            return jsonify({
                'success': True,
                'receipt_id': receipt.id,
                'redirect': url_for('review_receipt', receipt_id=receipt.id),
                'message': f'Receipt uploaded successfully. ID: {receipt.id}'
            })
        
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type. Allowed: ' + ', '.join(app.config['ALLOWED_EXTENSIONS'])}), 400
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/review/<int:receipt_id>')
@login_required
@company_required
def review_receipt(receipt_id):
    receipt = Receipt.query.filter_by(id=receipt_id, company_id=current_user.company_id).first_or_404()
    jobs = Job.query.filter_by(status='active', company_id=current_user.company_id).all()
    return render_template('review.html', receipt=receipt, jobs=jobs)

@app.route('/update_receipt/<int:receipt_id>', methods=['POST'])
@login_required
@company_required
def update_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        data = request.json
        
        receipt.vendor_name = data.get('vendor')
        receipt.total_amount = float(data.get('total')) if data.get('total') else None
        receipt.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else None
        receipt.receipt_number = data.get('receipt_number')
        receipt.job_id = int(data.get('job_id')) if data.get('job_id') else None
        
        # Update line items
        LineItem.query.filter_by(receipt_id=receipt_id).delete()
        
        for item in data.get('line_items', []):
            if item.get('description') and item.get('amount'):
                line_item = LineItem(
                    receipt_id=receipt_id,
                    description=item['description'],
                    amount=float(item['amount']),
                    category=item.get('category', '')
                )
                db.session.add(line_item)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/receipts')
@login_required
@company_required
def list_receipts():
    receipts = Receipt.query.filter_by(company_id=current_user.company_id).order_by(Receipt.created_at.desc()).all()
    return render_template('list.html', receipts=receipts)

@app.route('/api/jobs')
@login_required
@company_required
def get_jobs():
    jobs = Job.query.filter_by(status='active').all()
    return jsonify([{
        'id': job.id,
        'job_number': job.job_number,
        'customer_name': job.customer_name
    } for job in jobs])

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    timeline = get_job_timeline(job_id)
    return render_template('job_detail.html', job=job, timeline=timeline)

@app.route('/api/jobs/create', methods=['POST'])
def create_job():
    try:
        data = request.json
        
        # Check if job number already exists
        existing_job = Job.query.filter_by(job_number=data.get('job_number')).first()
        if existing_job:
            return jsonify({'error': 'Job number already exists'}), 400
        
        # Create new job
        job = Job(
            job_number=data.get('job_number'),
            customer_name=data.get('customer_name'),
            quoted_price=float(data.get('quoted_price', 0))
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({'success': True, 'job_id': job.id})
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-summary')
def daily_summary():
    summary = generate_daily_summary()
    return jsonify({'summary': summary})

# New API endpoints for insights and reports
@app.route('/api/jobs/losing-money')
def api_losing_jobs():
    """Get jobs that are losing money"""
    jobs = Job.query.filter_by(status='active').all()
    losing_jobs = [
        {
            'id': job.id,
            'job_number': job.job_number,
            'customer': job.customer_name,
            'quoted_price': job.quoted_price,
            'current_costs': job.current_costs,
            'loss_amount': abs(job.profit_amount),
            'profit_margin': job.profit_margin
        }
        for job in jobs if job.profit_margin < 0
    ]
    
    losing_jobs.sort(key=lambda x: x['loss_amount'], reverse=True)
    return jsonify(losing_jobs)

@app.route('/api/insights/pricing-suggestions', methods=['POST'])
def api_pricing_suggestions():
    """Get pricing suggestions based on job description"""
    data = request.json
    description = data.get('description', '')
    target_margin = data.get('target_margin', 25)
    
    suggestion = PriceRecommendation.get_pricing_suggestions(description, target_margin)
    if suggestion:
        return jsonify(suggestion)
    else:
        return jsonify({'error': 'No similar jobs found'}), 404

@app.route('/api/insights/patterns')
def api_job_patterns():
    """Get job pattern insights"""
    patterns = JobInsights.find_losing_job_patterns()
    return jsonify(patterns)

@app.route('/api/insights/profit-trends')
def api_profit_trends():
    """Get profit trends over time"""
    days = request.args.get('days', 30, type=int)
    trends = get_profit_trends(days)
    return jsonify(trends)

@app.route('/api/insights/job-type-profitability')
def api_job_type_profitability():
    """Get profitability by job type"""
    profitability = get_job_type_profitability()
    return jsonify(profitability)

@app.route('/api/alerts/cost-overruns')
def api_cost_alerts():
    """Get jobs approaching budget limits"""
    threshold = request.args.get('threshold', 80, type=int)
    alerts = AlertMonitor.check_cost_alerts(threshold)
    return jsonify(alerts)

@app.route('/api/export/receipts-csv')
def export_receipts_to_csv():
    """Export receipts as CSV"""
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    job_id = request.args.get('job_id')
    
    # Build query
    query = Receipt.query
    
    if start_date:
        query = query.filter(Receipt.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Receipt.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
    if job_id:
        query = query.filter_by(job_id=job_id)
    
    receipts = query.all()
    
    # Generate CSV
    csv_data = export_receipts_csv(receipts)
    
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'receipts_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/api/export/job-pdf/<int:job_id>')
def export_job_pdf(job_id):
    """Export job summary as PDF"""
    job = Job.query.get_or_404(job_id)
    pdf_data = export_job_summary_pdf(job)
    
    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'job_{job.job_number}_summary.pdf'
    )

@app.route('/api/export/receipts-zip')
def export_receipts_to_zip():
    """Export receipts with images as ZIP"""
    # Get parameters
    job_id = request.args.get('job_id')
    include_images = request.args.get('include_images', 'true').lower() == 'true'
    
    # Get receipts
    query = Receipt.query
    if job_id:
        query = query.filter_by(job_id=job_id)
    
    receipts = query.all()
    
    # Generate ZIP
    zip_data = export_receipts_zip(receipts, include_images)
    
    return send_file(
        io.BytesIO(zip_data),
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'receipts_export_{datetime.now().strftime("%Y%m%d")}.zip'
    )

@app.route('/insights')
def insights_page():
    """Insights and reports page"""
    return render_template('insights.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            company_name = request.form.get('company_name', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            phone_number = request.form.get('phone_number', '').strip()
            
            # Validate required fields
            if not company_name or not username or not password:
                flash('Company name, username, and password are required', 'error')
                return render_template('register.html')
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return render_template('register.html')
            
            # Create company first
            company = Company(
                name=company_name,
                phone_number=phone_number
            )
            db.session.add(company)
            db.session.commit()
            
            # Create user
            user = User(
                username=username,
                email=email or f"{username}@example.com",  # Default email if not provided
                company_id=company.id,
                is_admin=True  # First user is admin
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))  # Go to index instead of setup
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/setup')
@login_required
def setup():
    return render_template('setup.html', company=current_user.company)

@app.route('/sms/receive', methods=['POST'])
def receive_sms():
    """Webhook endpoint for Twilio SMS/MMS"""
    try:
        # Get SMS data from Twilio
        from_number = request.values.get('From', '')
        message_body = request.values.get('Body', '')
        num_media = int(request.values.get('NumMedia', 0))
        
        logger.info(f"Received SMS from {from_number}: {message_body}")
        logger.info(f"Number of media attachments: {num_media}")
        
        # Create response
        resp = MessagingResponse()
        
        # Check if there are any media attachments
        if num_media == 0:
            resp.message("No image attached. Please send a photo of the receipt.")
            return str(resp)
        
        # Parse job number from message
        job_number = parse_job_number(message_body)
        if not job_number:
            resp.message("Please include the job number (e.g., 'Job 1234' or just '1234').")
            return str(resp)
        
        # Check if job exists
        job = Job.query.filter_by(job_number=job_number).first()
        if not job:
            resp.message(f"Job number {job_number} not found. Please check and resend.")
            return str(resp)
        
        # Process each media attachment
        total_amount = 0
        receipts_processed = 0
        errors = []
        
        for i in range(num_media):
            media_url = request.values.get(f'MediaUrl{i}')
            media_type = request.values.get(f'MediaContentType{i}')
            
            try:
                # Download the image
                filename, filepath = download_mms_media(media_url, media_type)
                
                # Create receipt record
                receipt = Receipt(
                    image_path=filename,
                    uploaded_by=from_number,
                    phone_number=from_number,
                    upload_method='sms',
                    job_id=job.id
                )
                db.session.add(receipt)
                db.session.commit()
                
                # Process the image
                try:
                    extracted_data = process_receipt_image(filepath)
                    
                    # Update receipt with extracted data
                    receipt.vendor = extracted_data.get('vendor')
                    receipt.total = extracted_data.get('total')
                    receipt.date = datetime.strptime(extracted_data.get('date'), '%Y-%m-%d').date() if extracted_data.get('date') else None
                    receipt.receipt_number = extracted_data.get('receipt_number')
                    receipt.extracted_data = extracted_data
                    
                    # Add line items
                    for item in extracted_data.get('line_items', []):
                        line_item = LineItem(
                            receipt_id=receipt.id,
                            description=item.get('description'),
                            amount=item.get('amount'),
                            category=item.get('category')
                        )
                        db.session.add(line_item)
                    
                    db.session.commit()
                    
                    if receipt.total_amount:
                        total_amount += receipt.total_amount or 0
                    receipts_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing receipt: {str(e)}")
                    receipt.extracted_data = {'error': str(e)}
                    db.session.commit()
                    errors.append("Couldn't read one receipt clearly.")
                    
            except Exception as e:
                logger.error(f"Error downloading media: {str(e)}")
                errors.append("Failed to download image.")
        
        # Generate response message
        if receipts_processed > 0:
            job_total = calculate_job_total(job.id, db)
            
            if errors:
                # Partial success
                message = f"✓ Processed {receipts_processed} receipt(s). Added {format_currency(total_amount)} to Job {job_number}. "
                message += f"Total costs: {format_currency(job_total)}. "
                message += f"Note: {' '.join(errors)}"
            else:
                # Full success
                message = f"✓ Received! Added {format_currency(total_amount)} to Job {job_number}. Total costs: {format_currency(job_total)}"
            
            # Send async response with details
            send_sms_response(from_number, message)
            
            # Send immediate acknowledgment
            resp.message("Receipt received and processing. You'll get a confirmation shortly.")
        else:
            # Complete failure
            resp.message("Couldn't read receipt. Please retake photo with better lighting.")
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"SMS webhook error: {str(e)}")
        resp = MessagingResponse()
        resp.message("System error. Please try again later or use the web interface.")
        return str(resp)

@app.cli.command()
def init_db_command():
    """Initialize the database."""
    init_db()
    print('Initialized the database.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)