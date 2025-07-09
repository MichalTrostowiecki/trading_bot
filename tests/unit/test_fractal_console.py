#!/usr/bin/env python3
"""
Simple console test to verify fractal detection backend is working
Prints detected fractals to console as they're found
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.strategy.fibonacci_strategy import FibonacciStrategy
from src.data.database import DatabaseManager

def test_fractal_detection():
    """Simple test that prints fractals to console"""
    print("🔍 Testing Fractal Detection Backend")
    print("=" * 50)
    
    # Initialize database
    try:
        db = DatabaseManager()
        db.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Get test data (first 100 bars of DJ30)
    try:
        df = db.get_historical_data(
            symbol="DJ30",
            timeframe="M1",
            limit=100
        )
        
        if df.empty:
            print("❌ No test data found in database")
            return False
            
        print(f"✅ Loaded {len(df)} bars of test data")
        print(f"📋 Data columns: {list(df.columns)}")
        print(f"📋 Sample data:")
        print(df.head(2))
        
    except Exception as e:
        print(f"❌ Data loading error: {e}")
        return False
    
    # Initialize strategy
    try:
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.0050,  # 50 pips
            fibonacci_levels=[0.236, 0.382, 0.500, 0.618, 0.786],
            lookback_candles=100
        )
        print("✅ Strategy initialized")
        
    except Exception as e:
        print(f"❌ Strategy error: {e}")
        return False
    
    # Process data bar by bar and print fractals
    fractal_count = 0
    print("\n📊 Processing bars and detecting fractals...")
    print("Bar | Time                | Price    | Fractal Type")
    print("-" * 55)
    
    for i in range(len(df)):
        # Process bar with DataFrame (not dictionary)
        strategy.process_bar(df, i)
        
        # Get current state
        state = strategy.get_current_state()
        
        # Check for new fractals
        if 'fractals' in state and state['fractals']:
            for fractal in state['fractals']:
                # Only print fractals at current position (newly detected)
                if fractal.get('bar_index', 0) == i:
                    fractal_count += 1
                    fractal_type = "HIGH" if fractal.get('type') == 'high' else "LOW "
                    price = fractal.get('price', 0)
                    timestamp = fractal.get('timestamp', 'Unknown')
                    
                    print(f"{i:3d} | {timestamp} | {price:8.1f} | {fractal_type} FRACTAL")
    
    print("-" * 55)
    print(f"✅ Test completed: {fractal_count} fractals detected")
    
    if fractal_count > 0:
        print("🎉 Backend fractal detection is working perfectly!")
        return True
    else:
        print("⚠️ No fractals detected - may need more data or parameter adjustment")
        return False

if __name__ == "__main__":
    success = test_fractal_detection()
    sys.exit(0 if success else 1)