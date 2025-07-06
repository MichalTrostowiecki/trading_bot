#!/usr/bin/env python3
"""
Debug script to test fractal detection and display issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.database import get_database_manager, initialize_database
from src.strategy.fibonacci_strategy import FibonacciStrategy
import pandas as pd

def test_fractal_detection():
    """Test fractal detection on real data."""
    print("🔍 Testing fractal detection...")

    # Initialize database
    initialize_database()

    # Get data
    db_manager = get_database_manager()
    df = db_manager.get_historical_data('EURUSD', '1H', limit=200)

    if df is None or len(df) == 0:
        print("❌ No data in database, creating sample data...")
        # Create sample data for testing
        import numpy as np
        dates = pd.date_range(start='2025-01-01', periods=100, freq='H')

        # Create realistic price data with fractals
        base_price = 1.0500
        prices = []
        for i in range(100):
            # Add some volatility and trends
            noise = np.random.normal(0, 0.0005)
            trend = 0.0001 * np.sin(i / 10)  # Slow trend
            price = base_price + trend + noise
            prices.append(price)

        # Create OHLC data
        df_data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price + abs(np.random.normal(0, 0.0003))
            low = price - abs(np.random.normal(0, 0.0003))
            open_price = prices[i-1] if i > 0 else price
            close_price = price

            df_data.append({
                'open': open_price,
                'high': max(open_price, high, close_price),
                'low': min(open_price, low, close_price),
                'close': close_price,
                'volume': np.random.randint(1000, 5000)
            })

        df = pd.DataFrame(df_data, index=dates)
        print(f"📊 Created sample data with {len(df)} bars")
    
    print(f"📊 Loaded {len(df)} bars of data")
    print(f"📅 Date range: {df.index[0]} to {df.index[-1]}")
    
    # Initialize strategy
    strategy = FibonacciStrategy(fractal_period=5)
    
    # Process bars and look for fractals
    fractals_found = []
    
    for i in range(len(df)):
        if i < 20:  # Skip first 20 bars
            continue
            
        print(f"\n📈 Processing bar {i}: {df.iloc[i]['close']:.5f} at {df.index[i]}")
        
        # Process current bar
        results = strategy.process_bar(df, i)
        
        # Check for new fractal
        if results.get('new_fractal'):
            fractal = results['new_fractal']
            fractals_found.append(fractal)
            print(f"  🔺 FRACTAL FOUND: {fractal['fractal_type']} at {fractal['price']:.5f} (bar {fractal['bar_index']})")
            print(f"       Timestamp: {fractal['timestamp']}")
        
        # Stop after finding a few fractals
        if len(fractals_found) >= 5:
            break
    
    print(f"\n✅ Found {len(fractals_found)} fractals in {i+1} bars processed")
    
    # Print fractal details
    for i, fractal in enumerate(fractals_found):
        print(f"  {i+1}. {fractal['fractal_type']} fractal at {fractal['price']:.5f} (bar {fractal['bar_index']})")

if __name__ == "__main__":
    test_fractal_detection()
