from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime
import json
from .models import db, Receipt, Job, LineItem
from .config import Config
from .receipt_processor import process_receipt_image
from .sms_handler import parse_job_number, download_mms_media, send_sms_response, calculate_job_total, format_currency
from .analytics import get_dashboard_stats, get_jobs_summary, get_job_timeline, generate_daily_summary
from .insights import JobInsights, PriceRecommendation, AlertMonitor, get_profit_trends, get_job_type_profitability
from .export_utils import export_receipts_csv, export_job_summary_pdf, export_receipts_zip
from .scheduler import job_scheduler
from twilio.twiml.messaging_response import MessagingResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize scheduler
job_scheduler.init_app(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/')
def index():
    # Check if job parameter is passed for pre-selection
    job_number = request.args.get('job')
    return render_template('index.html', preselected_job=job_number)

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    jobs = get_jobs_summary()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Create receipt record
            receipt = Receipt(
                image_url=filename,
                uploaded_by=request.form.get('uploaded_by', 'Anonymous')
            )
            db.session.add(receipt)
            db.session.commit()
            
            # Process the image in the background
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
                
            except Exception as e:
                logger.error(f"Error processing receipt: {str(e)}")
                receipt.extracted_data = {'error': str(e)}
                db.session.commit()
            
            return jsonify({
                'success': True,
                'receipt_id': receipt.id,
                'redirect': url_for('review_receipt', receipt_id=receipt.id)
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/review/<int:receipt_id>')
def review_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    jobs = Job.query.filter_by(status='active').all()
    return render_template('review.html', receipt=receipt, jobs=jobs)

@app.route('/update_receipt/<int:receipt_id>', methods=['POST'])
def update_receipt(receipt_id):
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        data = request.json
        
        receipt.vendor = data.get('vendor')
        receipt.total = float(data.get('total')) if data.get('total') else None
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
def list_receipts():
    receipts = Receipt.query.order_by(Receipt.created_at.desc()).all()
    return render_template('list.html', receipts=receipts)

@app.route('/api/jobs')
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
                    image_url=filename,
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
                    
                    if receipt.total:
                        total_amount += receipt.total
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)