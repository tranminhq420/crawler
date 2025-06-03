#!/usr/bin/env python3

"""
Update database schema to add film_id column to screentimes table
"""

from models import db_connect, Base, Screentime
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Add film_id column to screentimes table if it doesn't exist"""
    
    engine = db_connect()
    
    try:
        with engine.connect() as connection:
            # Check if film_id column already exists
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'screentimes' 
                AND COLUMN_NAME = 'film_id'
                AND TABLE_SCHEMA = 'hanoicinema'
            """))
            
            if result.fetchone():
                logger.info("✅ film_id column already exists in screentimes table")
            else:
                # Add the column
                logger.info("🔄 Adding film_id column to screentimes table...")
                connection.execute(text("""
                    ALTER TABLE screentimes 
                    ADD COLUMN film_id VARCHAR(50) NULL 
                    COMMENT 'Link to specific film'
                """))
                connection.commit()
                logger.info("✅ Successfully added film_id column to screentimes table")
        
        logger.info("Database update completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error updating database: {e}")
        raise

if __name__ == "__main__":
    update_database() 