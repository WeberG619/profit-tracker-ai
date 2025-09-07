from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests
import re
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from .config import Config

logger = logging.getLogger(__name__)

def init_twilio():
    """Initialize Twilio client"""
    if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
        return Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    return None

def parse_job_number(message_text):
    """Extract job number from SMS message text"""
    if not message_text:
        return None
    
    message_text = message_text.strip()
    
    # Patterns to match:
    # "1234", "Job 1234", "job 1234", "JOB 1234", "1234 materials", "Job 1234 Home Depot"
    patterns = [
        r'^(\d{4})$',  # Just 4 digits
        r'^[Jj][Oo][Bb]\s*(\d{4})',  # "Job 1234" (case insensitive)
        r'^(\d{4})\s+',  # "1234 materials"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_text)
        if match:
            return match.group(1)
    
    # Try to find any 4-digit number in the message
    four_digit_match = re.search(r'\b(\d{4})\b', message_text)
    if four_digit_match:
        return four_digit_match.group(1)
    
    return None

def download_mms_media(media_url, media_type):
    """Download media from Twilio MMS"""
    try:
        # Twilio media URLs require authentication
        response = requests.get(
            media_url,
            auth=(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN),
            stream=True
        )
        response.raise_for_status()
        
        # Generate filename based on media type
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Extract file extension from content type
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        ext_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/bmp': 'bmp',
            'image/webp': 'webp'
        }
        
        extension = ext_map.get(content_type.lower(), 'jpg')
        filename = f"sms_{timestamp}.{extension}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save the file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filename, filepath
        
    except Exception as e:
        logger.error(f"Error downloading MMS media: {str(e)}")
        raise

def send_sms_response(to_number, message_body):
    """Send SMS response using Twilio"""
    try:
        client = init_twilio()
        if client and Config.TWILIO_PHONE_NUMBER:
            message = client.messages.create(
                body=message_body,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}: {message.sid}")
            return True
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
    return False

def calculate_job_total(job_id, db):
    """Calculate total expenses for a job"""
    from models import Receipt
    
    receipts = Receipt.query.filter_by(job_id=job_id).all()
    total = sum(r.total for r in receipts if r.total)
    return total

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"