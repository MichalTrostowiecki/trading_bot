#!/usr/bin/env python3
"""
Check the database schema to understand the table structure
"""

import sqlite3
import os
import pandas as pd

def check_database_schema():
    """Check the database schema and available data"""
    
    # Try to find the database file
    possible_paths = [
        "data/trading_bot.db",
        "trading_bot.db",
        "../data/trading_bot.db",
        "src/data/trading_bot.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found")
        return False
    
    print(f"📊 Database found at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Available tables: {[table[0] for table in tables]}")
        
        # Check each table
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"   Columns: {[col[1] for col in columns]}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Row count: {count}")
            
            # If this looks like market data, show sample
            if any(keyword in table_name.lower() for keyword in ['market', 'data', 'candle', 'bar']):
                print(f"   Sample data:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample = cursor.fetchall()
                for row in sample:
                    print(f"      {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database_schema()