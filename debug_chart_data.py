#!/usr/bin/env python3
"""
Debug script to find chart data issues around bar 2769
"""

import sys
import os
sys.path.append('/mnt/d/trading_bot')

from src.data.database import get_database_manager
from datetime import datetime
import pandas as pd

def debug_chart_data():
    """Debug chart data around the problematic bar."""
    
    db_manager = get_database_manager()
    if not db_manager:
        print("❌ Database not available")
        return
    
    # Get DJ30 M1 data around the problematic date
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 6, 3)
    
    print(f"🔍 Querying DJ30 M1 data from {start_date} to {end_date}")
    
    df = db_manager.get_historical_data(
        symbol="DJ30",
        timeframe="M1", 
        start_date=start_date,
        end_date=end_date
    )
    
    if df.empty:
        print("❌ No data found")
        return
    
    print(f"📊 Found {len(df)} bars")
    
    # Check around bar 2769 (approximate)
    target_bar = min(2769, len(df) - 1)
    start_check = max(0, target_bar - 10)
    end_check = min(len(df), target_bar + 10)
    
    print(f"🎯 Checking bars {start_check} to {end_check} around target bar {target_bar}")
    
    # Convert to list format like the API does
    data = []
    for i, (timestamp, row) in enumerate(df.iterrows()):
        if start_check <= i <= end_check:
            bar_data = {
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            }
            
            # Test JavaScript timestamp conversion
            try:
                js_timestamp = timestamp.timestamp()
                print(f"Bar {i}: {bar_data['timestamp']} -> {js_timestamp}")
                
                # Check for invalid data
                if pd.isna(row['open']) or pd.isna(row['high']) or pd.isna(row['low']) or pd.isna(row['close']):
                    print(f"  ❌ Invalid OHLC data in bar {i}")
                    
                if row['high'] < row['low']:
                    print(f"  ❌ High < Low in bar {i}: H={row['high']}, L={row['low']}")
                    
                if row['open'] < 0 or row['high'] < 0 or row['low'] < 0 or row['close'] < 0:
                    print(f"  ❌ Negative price in bar {i}")
                    
            except Exception as e:
                print(f"  ❌ Timestamp conversion error in bar {i}: {e}")
                
            data.append(bar_data)
    
    # Look for the specific date 2025-06-02 05:38
    target_time = datetime(2025, 6, 2, 5, 38)
    print(f"\n🎯 Looking for bars around {target_time}")
    
    for i, (timestamp, row) in enumerate(df.iterrows()):
        if abs((timestamp - target_time).total_seconds()) < 300:  # Within 5 minutes
            print(f"Bar {i}: {timestamp.isoformat()} - O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}")
    
    # Check for data quality issues
    print(f"\n🔍 Data Quality Check:")
    print(f"  - Total bars: {len(df)}")
    print(f"  - Date range: {df.index.min()} to {df.index.max()}")
    print(f"  - Any NaN values: {df.isna().any().any()}")
    
    if df.isna().any().any():
        print("  ❌ Found NaN values:")
        print(df[df.isna().any(axis=1)].head(10))
    
    # Check for impossible price relationships
    invalid_bars = df[df['high'] < df['low']]
    if not invalid_bars.empty:
        print(f"  ❌ Found {len(invalid_bars)} bars with High < Low")
        print(invalid_bars.head(10))
    
    # Check for extreme price movements
    df['price_change'] = df['close'].pct_change()
    extreme_moves = df[abs(df['price_change']) > 0.1]  # >10% moves
    if not extreme_moves.empty:
        print(f"  ⚠️  Found {len(extreme_moves)} bars with >10% price moves")
        print(extreme_moves[['open', 'high', 'low', 'close', 'price_change']].head(10))

if __name__ == "__main__":
    debug_chart_data()