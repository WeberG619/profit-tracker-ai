"""
Duplicate Receipt Detection System

This module provides intelligent duplicate detection for receipts to prevent
users from accidentally uploading the same receipt multiple times.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Smart duplicate detection for receipts"""
    
    @staticmethod
    def check_for_duplicates(new_receipt_data: dict, existing_receipts: List, company_id: int) -> Tuple[bool, Optional[dict]]:
        """
        Check if a receipt is a duplicate based on multiple factors
        
        Args:
            new_receipt_data: Extracted data from the new receipt
            existing_receipts: List of existing Receipt objects for the company
            company_id: ID of the company
            
        Returns:
            Tuple of (is_duplicate, duplicate_info)
        """
        
        # Extract key fields from new receipt
        new_vendor = new_receipt_data.get('vendor', '').lower().strip()
        new_total = new_receipt_data.get('total', 0)
        new_date = new_receipt_data.get('date')
        new_receipt_number = new_receipt_data.get('receipt_number', '').strip()
        
        # Check each existing receipt
        for receipt in existing_receipts:
            duplicate_score = 0
            max_score = 0
            
            # Check receipt number (highest weight)
            if new_receipt_number and receipt.receipt_number:
                max_score += 40
                if new_receipt_number.lower() == receipt.receipt_number.lower():
                    duplicate_score += 40
            
            # Check vendor name
            if new_vendor and receipt.vendor_name:
                max_score += 20
                existing_vendor = receipt.vendor_name.lower().strip()
                if new_vendor == existing_vendor:
                    duplicate_score += 20
                elif DuplicateDetector._similar_vendor_names(new_vendor, existing_vendor):
                    duplicate_score += 10
            
            # Check total amount
            if new_total and receipt.total_amount:
                max_score += 20
                if abs(new_total - receipt.total_amount) < 0.01:  # Exact match
                    duplicate_score += 20
                elif abs(new_total - receipt.total_amount) < 1.00:  # Close match
                    duplicate_score += 10
            
            # Check date (within same day)
            if new_date and receipt.date:
                max_score += 20
                try:
                    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                    if new_date_obj == receipt.date:
                        duplicate_score += 20
                    elif abs((new_date_obj - receipt.date).days) <= 1:
                        duplicate_score += 10
                except:
                    pass
            
            # Calculate percentage match
            if max_score > 0:
                match_percentage = (duplicate_score / max_score) * 100
                
                # If match is above threshold, it's likely a duplicate
                if match_percentage >= 75:
                    duplicate_info = {
                        'receipt_id': receipt.id,
                        'match_percentage': match_percentage,
                        'vendor': receipt.vendor_name,
                        'total': receipt.total_amount,
                        'date': receipt.date.strftime('%Y-%m-%d') if receipt.date else None,
                        'receipt_number': receipt.receipt_number,
                        'uploaded_at': receipt.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    logger.warning(f"Duplicate detected: {match_percentage}% match with receipt #{receipt.id}")
                    return True, duplicate_info
        
        return False, None
    
    @staticmethod
    def _similar_vendor_names(name1: str, name2: str) -> bool:
        """Check if two vendor names are similar (fuzzy matching)"""
        # Simple similarity check - can be enhanced with fuzzy matching library
        # Remove common words
        common_words = ['inc', 'llc', 'corp', 'corporation', 'company', 'co', 'ltd', 'store', 'market']
        
        words1 = [w for w in name1.lower().split() if w not in common_words]
        words2 = [w for w in name2.lower().split() if w not in common_words]
        
        # Check if any significant words match
        if words1 and words2:
            common = set(words1).intersection(set(words2))
            return len(common) >= len(words1) * 0.5 or len(common) >= len(words2) * 0.5
        
        return False
    
    @staticmethod
    def generate_receipt_hash(receipt_data: dict) -> str:
        """Generate a hash for quick duplicate checking"""
        # Create a string from key fields
        key_string = f"{receipt_data.get('vendor', '')}-{receipt_data.get('total', 0):.2f}-{receipt_data.get('date', '')}-{receipt_data.get('receipt_number', '')}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def find_similar_receipts(receipt_data: dict, existing_receipts: List, limit: int = 5) -> List[dict]:
        """Find similar receipts that might be related but not exact duplicates"""
        similar_receipts = []
        
        new_vendor = receipt_data.get('vendor', '').lower().strip()
        new_total = receipt_data.get('total', 0)
        new_date = receipt_data.get('date')
        
        for receipt in existing_receipts:
            similarity_reasons = []
            
            # Same vendor
            if receipt.vendor_name and new_vendor:
                if receipt.vendor_name.lower().strip() == new_vendor:
                    similarity_reasons.append("same vendor")
            
            # Similar amount (within 10%)
            if receipt.total_amount and new_total:
                diff_percentage = abs(receipt.total_amount - new_total) / max(receipt.total_amount, new_total) * 100
                if diff_percentage <= 10:
                    similarity_reasons.append(f"similar amount (within {diff_percentage:.0f}%)")
            
            # Same day
            if receipt.date and new_date:
                try:
                    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                    if receipt.date == new_date_obj:
                        similarity_reasons.append("same date")
                except:
                    pass
            
            if similarity_reasons:
                similar_receipts.append({
                    'receipt_id': receipt.id,
                    'vendor': receipt.vendor_name,
                    'total': receipt.total_amount,
                    'date': receipt.date.strftime('%Y-%m-%d') if receipt.date else None,
                    'reasons': similarity_reasons
                })
        
        # Sort by number of matching criteria and return top matches
        similar_receipts.sort(key=lambda x: len(x['reasons']), reverse=True)
        return similar_receipts[:limit]