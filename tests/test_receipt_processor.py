"""Test receipt processor functionality."""
import unittest
from unittest.mock import patch, MagicMock
from app.receipt_processor import process_receipt_image, parse_receipt_text


class TestReceiptProcessor(unittest.TestCase):
    """Test receipt processing functionality."""
    
    @patch('app.receipt_processor.anthropic.Anthropic')
    def test_process_receipt_image(self, mock_anthropic):
        """Test receipt image processing."""
        # Mock the Anthropic API response
        mock_response = MagicMock()
        mock_response.content = [{
            'text': '''
            {
                "vendor_name": "Home Depot",
                "date": "2024-01-15",
                "total_amount": 156.78,
                "items": [
                    {"description": "PVC Pipe 2\"", "quantity": 5, "price": 15.99},
                    {"description": "Pipe Fittings", "quantity": 10, "price": 3.99}
                ],
                "tax": 12.34,
                "subtotal": 144.44
            }
            '''
        }]
        
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Test processing
        result = process_receipt_image('test.jpg')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['vendor_name'], 'Home Depot')
        self.assertEqual(result['total_amount'], 156.78)
        self.assertEqual(len(result['items']), 2)
        
    def test_parse_receipt_text_valid_json(self):
        """Test parsing valid JSON receipt text."""
        text = '''
        {
            "vendor_name": "Test Vendor",
            "total_amount": 100.00,
            "date": "2024-01-15"
        }
        '''
        
        result = parse_receipt_text(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['vendor_name'], 'Test Vendor')
        self.assertEqual(result['total_amount'], 100.00)
        
    def test_parse_receipt_text_invalid_json(self):
        """Test parsing invalid JSON receipt text."""
        text = "Not a valid JSON"
        
        result = parse_receipt_text(text)
        
        self.assertIsNone(result)
        
    def test_parse_receipt_text_with_markdown(self):
        """Test parsing JSON within markdown code blocks."""
        text = '''
        Here's the extracted data:
        
        ```json
        {
            "vendor_name": "Test Vendor",
            "total_amount": 50.00
        }
        ```
        '''
        
        result = parse_receipt_text(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['vendor_name'], 'Test Vendor')
        self.assertEqual(result['total_amount'], 50.00)


if __name__ == '__main__':
    unittest.main()