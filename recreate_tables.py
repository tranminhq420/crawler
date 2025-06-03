#!/usr/bin/env python3

from hanoicine.hanoicine.models import db_connect, create_table, Base

def recreate_tables():
    """Recreate all database tables"""
    print("Connecting to database...")
    engine = db_connect()
    
    print("Creating tables...")
    Base.metadata.drop_all(engine)  # Drop all existing tables
    create_table(engine)  # Create new tables
    
    print("✅ Tables recreated successfully!")
    
    # Verify tables were created
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        print(f"Created tables: {tables}")
        
        # Check screentimes table structure
        result = conn.execute(text("DESCRIBE screentimes"))
        print("\\nScreentimes table structure:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    recreate_tables() 