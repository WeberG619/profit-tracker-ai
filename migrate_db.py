"""
Database migration script to add new columns safely
"""

from app.app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column_if_not_exists(table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist"""
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name = :column_name
            """), {"table_name": table_name, "column_name": column_name})
            
            if not result.fetchone():
                # Column doesn't exist, add it
                db.session.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN {column_name} {column_type}
                """))
                db.session.commit()
                logger.info(f"Added column {column_name} to {table_name}")
            else:
                logger.info(f"Column {column_name} already exists in {table_name}")
                
        except Exception as e:
            # SQLite doesn't support information_schema, try a different approach
            try:
                # Try to select the column
                db.session.execute(text(f"SELECT {column_name} FROM {table_name} LIMIT 1"))
                logger.info(f"Column {column_name} already exists in {table_name}")
            except:
                # Column doesn't exist, add it
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN {column_name} {column_type}
                    """))
                    db.session.commit()
                    logger.info(f"Added column {column_name} to {table_name}")
                except Exception as add_error:
                    logger.error(f"Failed to add column {column_name}: {str(add_error)}")

if __name__ == "__main__":
    # Add receipt_hash column if it doesn't exist
    add_column_if_not_exists('receipt', 'receipt_hash', 'VARCHAR(64)')
    print("Migration completed!")