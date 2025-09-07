"""Test SMS handler functionality."""
import unittest
from unittest.mock import patch, MagicMock
from app.sms_handler import parse_job_number, download_mms_media, process_sms_receipt


class TestSMSHandler(unittest.TestCase):
    """Test SMS handling functionality."""
    
    def test_parse_job_number_with_hash(self):
        """Test parsing job number with # symbol."""
        body = "Receipt for job #JOB123"
        result = parse_job_number(body)
        self.assertEqual(result, "JOB123")
        
    def test_parse_job_number_with_colon(self):
        """Test parsing job number with Job: prefix."""
        body = "Job: JOB456 receipt attached"
        result = parse_job_number(body)
        self.assertEqual(result, "JOB456")
        
    def test_parse_job_number_standalone(self):
        """Test parsing standalone job number."""
        body = "JOB789"
        result = parse_job_number(body)
        self.assertEqual(result, "JOB789")
        
    def test_parse_job_number_case_insensitive(self):
        """Test case insensitive job number parsing."""
        body = "job number: job999"
        result = parse_job_number(body)
        self.assertEqual(result, "JOB999")
        
    def test_parse_job_number_not_found(self):
        """Test when no job number is found."""
        body = "Here's a receipt"
        result = parse_job_number(body)
        self.assertIsNone(result)
        
    @patch('app.sms_handler.requests.get')
    @patch('app.sms_handler.twilio_client')
    def test_download_mms_media_success(self, mock_twilio, mock_requests):
        """Test successful MMS media download."""
        # Mock Twilio media fetch
        mock_media = MagicMock()
        mock_media.uri = '/2010-04-01/Accounts/AC123/Messages/MM123/Media/ME123'
        mock_twilio.messages.return_value.media.return_value.fetch.return_value = mock_media
        
        # Mock requests response
        mock_response = MagicMock()
        mock_response.content = b'fake image data'
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Test download
        result = download_mms_media('MM123', 'ME123')
        
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.jpg'))
        
    @patch('app.sms_handler.requests.get')
    def test_download_mms_media_failure(self, mock_requests):
        """Test failed MMS media download."""
        mock_requests.side_effect = Exception("Download failed")
        
        result = download_mms_media('MM123', 'ME123')
        
        self.assertIsNone(result)
        
    @patch('app.sms_handler.download_mms_media')
    @patch('app.sms_handler.process_receipt_image')
    def test_process_sms_receipt_with_media(self, mock_process, mock_download):
        """Test processing SMS receipt with media."""
        mock_download.return_value = 'test.jpg'
        mock_process.return_value = {
            'vendor_name': 'Test Vendor',
            'total_amount': 100.00
        }
        
        result = process_sms_receipt(
            message_sid='MM123',
            body='Job #JOB123',
            from_number='+1234567890',
            media_url='http://example.com/image.jpg',
            media_content_type='image/jpeg',
            company_id=1
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['job_number'], 'JOB123')
        self.assertIsNotNone(result['receipt_id'])
        
    def test_process_sms_receipt_no_media(self):
        """Test processing SMS receipt without media."""
        result = process_sms_receipt(
            message_sid='SM123',
            body='Job #JOB123',
            from_number='+1234567890',
            media_url=None,
            media_content_type=None,
            company_id=1
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No image', result['message'])


if __name__ == '__main__':
    unittest.main()