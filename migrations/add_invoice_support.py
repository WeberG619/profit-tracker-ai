"""
Add invoice support to the system
This migration adds fields to track both receipts and invoices
"""

from app.app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add invoice support"""
    with app.app_context():
        try:
            # Add new columns to receipt table for invoice support
            migrations = [
                # Document type fields
                "ALTER TABLE receipt ADD COLUMN document_type VARCHAR(50) DEFAULT 'receipt'",
                "ALTER TABLE receipt ADD COLUMN direction VARCHAR(20) DEFAULT 'expense'",
                "ALTER TABLE receipt ADD COLUMN status VARCHAR(20) DEFAULT 'paid'",
                
                # Invoice-specific fields
                "ALTER TABLE receipt ADD COLUMN due_date DATE",
                "ALTER TABLE receipt ADD COLUMN customer_name VARCHAR(255)",
                "ALTER TABLE receipt ADD COLUMN customer_email VARCHAR(255)",
                "ALTER TABLE receipt ADD COLUMN customer_phone VARCHAR(50)",
                "ALTER TABLE receipt ADD COLUMN invoice_number VARCHAR(100)",
                
                # Payment tracking
                "ALTER TABLE receipt ADD COLUMN sent_date DATETIME",
                "ALTER TABLE receipt ADD COLUMN paid_date DATETIME",
                "ALTER TABLE receipt ADD COLUMN payment_method VARCHAR(50)",
                
                # Additional fields
                "ALTER TABLE receipt ADD COLUMN terms TEXT",
                "ALTER TABLE receipt ADD COLUMN notes TEXT",
            ]
            
            # Add indexes for performance
            indexes = [
                "CREATE INDEX idx_document_type ON receipt(document_type)",
                "CREATE INDEX idx_document_status ON receipt(status)",
                "CREATE INDEX idx_due_date ON receipt(due_date)",
            ]
            
            # Run each migration
            for migration in migrations:
                try:
                    db.session.execute(text(migration))
                    logger.info(f"✓ Executed: {migration}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        logger.info(f"Column already exists, skipping: {migration}")
                    else:
                        logger.error(f"Failed to execute: {migration} - Error: {str(e)}")
            
            # Add indexes
            for index in indexes:
                try:
                    db.session.execute(text(index))
                    logger.info(f"✓ Created index: {index}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"Index already exists, skipping: {index}")
                    else:
                        logger.error(f"Failed to create index: {index} - Error: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            logger.info("✅ Migration completed successfully!")
            
            # Update existing receipts to have correct defaults
            db.session.execute(text("""
                UPDATE receipt 
                SET document_type = 'receipt', 
                    direction = 'expense', 
                    status = 'paid'
                WHERE document_type IS NULL
            """))
            db.session.commit()
            logger.info("✓ Updated existing records with defaults")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if run_migration():
        print("✅ Invoice support migration completed!")
    else:
        print("❌ Migration failed - check logs")