#!/usr/bin/env python3
"""
Quick CSV data importer for DJ30 data from MT4
"""

import sys
import os
import csv
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, '/mnt/d/trading_bot/src')

from src.data.database import initialize_database
from src.monitoring.logging_config import setup_logging

def import_csv_data():
    """Import CSV data to PostgreSQL database."""
    
    setup_logging()
    print("📊 Importing DJ30 CSV data to PostgreSQL...")
    print("=" * 50)
    
    # Initialize database
    db_manager = initialize_database()
    if not db_manager:
        print("❌ Failed to initialize database")
        return False
    
    csv_file = "/mnt/d/trading_bot/data/data_from_mt4_dj30/DJ301.csv"
    
    # Read CSV data
    try:
        data = []
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    # Parse MT4 CSV format: Date,Time,Open,High,Low,Close,Volume
                    date_str = row[0]
                    time_str = row[1]
                    datetime_str = f"{date_str} {time_str}"
                    
                    timestamp = datetime.strptime(datetime_str, "%Y.%m.%d %H:%M")
                    
                    data.append({
                        'timestamp': timestamp,
                        'symbol': 'DJ30',
                        'timeframe': 'M1',  # 1-minute data
                        'open': float(row[2]),
                        'high': float(row[3]),
                        'low': float(row[4]),
                        'close': float(row[5]),
                        'volume': int(row[6]) if row[6].isdigit() else 0
                    })
        
        print(f"📈 Parsed {len(data)} bars from CSV")
        
        # Store in database
        if data:
            # Convert to DataFrame with timestamp as index
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')  # Set timestamp as index
            
            # Use historical data store method
            success = db_manager.store_historical_data('DJ30', 'M1', df)
            
            if success:
                print(f"✅ Successfully imported {len(data)} bars to PostgreSQL")
                print(f"   Symbol: DJ30")
                print(f"   Timeframe: M1") 
                print(f"   Date range: {data[0]['timestamp']} to {data[-1]['timestamp']}")
                return True
            else:
                print("❌ Failed to store data in database")
                return False
        else:
            print("❌ No valid data found in CSV")
            return False
            
    except Exception as e:
        print(f"❌ Error importing CSV data: {e}")
        return False

if __name__ == "__main__":
    success = import_csv_data()
    
    if success:
        print("\n🎉 CSV data import completed!")
        print("   Ready to use in research dashboard")
    else:
        print("\n❌ CSV import failed")
    
    sys.exit(0 if success else 1)