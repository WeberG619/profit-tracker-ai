import anthropic
import base64
import os
import json
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_receipt_image(image_path):
    """Process receipt image using Anthropic Claude Vision API."""
    try:
        # Get API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Encode the image
        base64_image = encode_image(image_path)
        
        # Create the prompt for Claude
        prompt = """Analyze this receipt/invoice image and extract the following information in JSON format:
        {
            "vendor": "store or company name",
            "total": numeric total amount,
            "date": "YYYY-MM-DD format",
            "receipt_number": "invoice or receipt number if visible",
            "line_items": [
                {
                    "description": "item description",
                    "amount": numeric amount,
                    "category": "suggested category (e.g., materials, tools, supplies)"
                }
            ]
        }
        
        Be as accurate as possible. If any field is not visible or unclear, use null.
        For dates, convert to YYYY-MM-DD format. For amounts, extract numeric values only."""
        
        # Send request to Claude
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            extracted_data = json.loads(json_match.group())
        else:
            # If no JSON found, create a basic structure
            extracted_data = {
                "vendor": None,
                "total": None,
                "date": None,
                "receipt_number": None,
                "line_items": [],
                "raw_response": response_text
            }
        
        # Clean and validate the data
        if extracted_data.get('date'):
            try:
                # Validate date format
                datetime.strptime(extracted_data['date'], '%Y-%m-%d')
            except:
                extracted_data['date'] = None
        
        if extracted_data.get('total'):
            try:
                extracted_data['total'] = float(str(extracted_data['total']).replace('$', '').replace(',', ''))
            except:
                extracted_data['total'] = None
        
        # Clean line items
        cleaned_items = []
        for item in extracted_data.get('line_items', []):
            if item.get('amount'):
                try:
                    amount = float(str(item['amount']).replace('$', '').replace(',', ''))
                    cleaned_items.append({
                        'description': item.get('description', ''),
                        'amount': amount,
                        'category': item.get('category', 'Uncategorized')
                    })
                except:
                    pass
        
        extracted_data['line_items'] = cleaned_items
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise