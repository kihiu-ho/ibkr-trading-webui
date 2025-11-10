#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
database_url = os.getenv('DATABASE_URL')
print(f"Connecting to: {database_url[:50]}...")

# Create engine
engine = create_engine(database_url)

# Check if artifacts table exists and what columns it has
with engine.connect() as conn:
    # Check if table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'artifacts'
        );
    """))
    table_exists = result.scalar()
    print(f"\nArtifacts table exists: {table_exists}")
    
    if table_exists:
        # Get columns
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='artifacts' 
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print("\nColumns in artifacts table:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        # Count rows
        result = conn.execute(text("SELECT COUNT(*) FROM artifacts"))
        count = result.scalar()
        print(f"\nTotal artifacts: {count}")

