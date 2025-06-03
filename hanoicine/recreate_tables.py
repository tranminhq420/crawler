#!/usr/bin/env python3

from hanoicine.models import db_connect, Base
from sqlalchemy import text

def recreate_tables():
    """Drop existing tables and recreate them with the correct schema"""
    engine = db_connect()
    
    with engine.connect() as connection:
        # Drop existing tables
        print("Dropping existing tables...")
        connection.execute(text("DROP TABLE IF EXISTS screentimes"))
        connection.execute(text("DROP TABLE IF EXISTS cinemas"))
        connection.execute(text("DROP TABLE IF EXISTS films"))
        connection.commit()
        print("Tables dropped successfully.")
    
    # Recreate tables with the new schema
    print("Creating tables with new schema...")
    Base.metadata.create_all(engine)
    print("Tables created successfully with correct schema!")

if __name__ == "__main__":
    recreate_tables() 