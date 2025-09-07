"""
API routes blueprint
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from twilio.twiml.messaging_response import MessagingResponse
from ..models import db, Receipt, Job, LineItem, Company
from ..receipt_processor import process_receipt_image
from ..sms_handler import parse_job_number, download_mms_media, send_sms_response, calculate_job_total
from ..analytics import get_dashboard_stats, generate_daily_summary
from ..insights import JobInsights, PriceRecommendation, AlertMonitor, get_profit_trends
from ..export_utils import export_receipts_csv, export_job_summary_pdf, export_receipts_zip
from ..auth import company_required
from ..money_losers import check_job_keywords

api_bp = Blueprint('api', __name__)

@api_bp.route('/upload', methods=['POST'])
@login_required
@company_required
def upload():
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Process the receipt
        receipt_data = process_receipt_image(filepath)
        
        if receipt_data:
            # Create receipt record
            receipt = Receipt(
                company_id=current_user.company_id,
                vendor_name=receipt_data.get('vendor_name', 'Unknown'),
                total_amount=float(receipt_data.get('total_amount', 0)),
                tax_amount=float(receipt_data.get('tax', 0)),
                date=datetime.strptime(receipt_data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
                image_path=filename,
                raw_data=str(receipt_data)
            )
            
            # Associate with job if provided
            job_number = request.form.get('job_number')
            if job_number:
                job = Job.query.filter_by(
                    job_number=job_number,
                    company_id=current_user.company_id
                ).first()
                if job:
                    receipt.job_id = job.id
            
            db.session.add(receipt)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'receipt_id': receipt.id,
                'extracted_data': receipt_data
            })
        else:
            return jsonify({'error': 'Could not process receipt'}), 400
    
    return jsonify({'error': 'Invalid file type'}), 400

@api_bp.route('/jobs')
@login_required
@company_required
def get_jobs():
    jobs = Job.query.filter_by(company_id=current_user.company_id).all()
    return jsonify([{
        'id': job.id,
        'job_number': job.job_number,
        'customer_name': job.customer_name,
        'status': job.status
    } for job in jobs])

@api_bp.route('/jobs/create', methods=['POST'])
@login_required
@company_required
def create_job():
    data = request.json
    
    # Check for money-losing keywords
    job_type = data.get('job_type', '')
    warnings = check_job_keywords(job_type)
    
    job = Job(
        company_id=current_user.company_id,
        job_number=data['job_number'],
        customer_name=data['customer_name'],
        job_type=job_type,
        revenue=float(data.get('revenue', 0)),
        status='active'
    )
    
    db.session.add(job)
    db.session.commit()
    
    response = {
        'success': True,
        'job_id': job.id
    }
    
    if warnings:
        response['warnings'] = warnings
    
    return jsonify(response)

@api_bp.route('/receipts/<int:receipt_id>')
@login_required
@company_required
def get_receipt(receipt_id):
    receipt = Receipt.query.filter_by(
        id=receipt_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    return jsonify({
        'id': receipt.id,
        'vendor_name': receipt.vendor_name,
        'total_amount': receipt.total_amount,
        'date': receipt.date.strftime('%Y-%m-%d'),
        'job_id': receipt.job_id
    })

@api_bp.route('/receipts/<int:receipt_id>/update', methods=['POST'])
@login_required
@company_required
def update_receipt(receipt_id):
    receipt = Receipt.query.filter_by(
        id=receipt_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    data = request.json
    receipt.vendor_name = data.get('vendor_name', receipt.vendor_name)
    receipt.total_amount = float(data.get('total_amount', receipt.total_amount))
    
    if 'job_id' in data:
        job_id = data['job_id']
        if job_id:
            job = Job.query.filter_by(
                id=job_id,
                company_id=current_user.company_id
            ).first()
            if job:
                receipt.job_id = job.id
        else:
            receipt.job_id = None
    
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/insights/trends')
@login_required
@company_required
def profit_trends():
    trends = get_profit_trends(current_user.company_id)
    return jsonify(trends)

@api_bp.route('/insights/patterns')
@login_required
@company_required
def job_patterns():
    patterns = JobInsights.find_losing_job_patterns()
    return jsonify(patterns)

@api_bp.route('/insights/pricing-suggestions', methods=['POST'])
@login_required
@company_required
def pricing_suggestions():
    job_type = request.json.get('job_type', '')
    suggestions = PriceRecommendation.generate_suggestions(job_type)
    return jsonify(suggestions)

@api_bp.route('/export/receipts-csv')
@login_required
@company_required
def export_csv():
    output = export_receipts_csv(current_user.company_id)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='receipts.csv')

@api_bp.route('/export/job-pdf/<int:job_id>')
@login_required
@company_required
def export_pdf(job_id):
    job = Job.query.filter_by(
        id=job_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    output = export_job_summary_pdf(job)
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f'job_{job.job_number}.pdf')

@api_bp.route('/sms/receive', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS/MMS from Twilio"""
    # This endpoint needs to be public for Twilio
    # We'll validate the request comes from Twilio
    
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid')
    
    # Find company by phone number
    company = Company.query.filter_by(phone_number=to_number).first()
    if not company:
        resp = MessagingResponse()
        resp.message("This number is not configured for receipt processing.")
        return str(resp)
    
    # Handle the SMS
    num_media = int(request.form.get('NumMedia', 0))
    
    if num_media > 0:
        media_url = request.form.get('MediaUrl0')
        media_content_type = request.form.get('MediaContentType0')
        
        # Download and process the image
        image_path = download_mms_media(message_sid, media_url)
        
        if image_path:
            receipt_data = process_receipt_image(image_path)
            
            if receipt_data:
                # Create receipt
                receipt = Receipt(
                    company_id=company.id,
                    vendor_name=receipt_data.get('vendor_name', 'Unknown'),
                    total_amount=float(receipt_data.get('total_amount', 0)),
                    image_path=image_path,
                    raw_data=str(receipt_data)
                )
                
                # Parse job number from message
                job_number = parse_job_number(body)
                if job_number:
                    job = Job.query.filter_by(
                        job_number=job_number,
                        company_id=company.id
                    ).first()
                    if job:
                        receipt.job_id = job.id
                
                db.session.add(receipt)
                db.session.commit()
                
                # Send confirmation
                response_msg = f"✓ Receipt processed! Amount: ${receipt.total_amount:.2f}"
                if job_number:
                    response_msg += f" for Job #{job_number}"
                
                send_sms_response(from_number, response_msg)
    
    resp = MessagingResponse()
    return str(resp)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']