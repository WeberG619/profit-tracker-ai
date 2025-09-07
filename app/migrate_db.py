"""
Database migration script to add SMS-related fields to existing database.
Run this if you have an existing database that needs the new fields.
"""

import sqlite3
import os

def migrate_database():
    db_path = 'instance/receipts.db'
    
    if not os.path.exists(db_path):
        print("No existing database found. Run the app first to create it.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(receipt)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add phone_number column if it doesn't exist
        if 'phone_number' not in columns:
            cursor.execute("ALTER TABLE receipt ADD COLUMN phone_number VARCHAR(20)")
            print("Added phone_number column")
        
        # Add upload_method column if it doesn't exist
        if 'upload_method' not in columns:
            cursor.execute("ALTER TABLE receipt ADD COLUMN upload_method VARCHAR(20) DEFAULT 'web'")
            print("Added upload_method column")
            
            # Update existing records to have 'web' as upload method
            cursor.execute("UPDATE receipt SET upload_method = 'web' WHERE upload_method IS NULL")
            print("Updated existing records with default upload_method")
        
        # Check job table columns
        cursor.execute("PRAGMA table_info(job)")
        job_columns = [col[1] for col in cursor.fetchall()]
        
        # Add completed_at column to jobs if it doesn't exist
        if 'completed_at' not in job_columns:
            cursor.execute("ALTER TABLE job ADD COLUMN completed_at TIMESTAMP")
            print("Added completed_at column to job table")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()