#!/usr/bin/env python3
"""
Simple test to check if fractals are being detected correctly.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only what we need
from src.strategy.fibonacci_strategy import FibonacciStrategy

def create_sample_data():
    """Create sample OHLC data with clear fractal patterns."""
    dates = pd.date_range(start='2025-01-01', periods=50, freq='H')
    
    # Create data with obvious fractal patterns
    data = []
    base_price = 1.0500
    
    for i in range(50):
        if i == 10:  # Create a clear high fractal
            price = base_price + 0.0050
        elif i == 20:  # Create a clear low fractal
            price = base_price - 0.0050
        elif i == 30:  # Another high fractal
            price = base_price + 0.0040
        else:
            # Normal price movement
            price = base_price + np.random.normal(0, 0.0010)
        
        # Create OHLC
        spread = 0.0005
        data.append({
            'open': price - spread/2,
            'high': price + spread,
            'low': price - spread,
            'close': price + spread/2,
            'volume': 1000
        })
    
    return pd.DataFrame(data, index=dates)

def test_fractal_detection():
    """Test fractal detection with sample data."""
    print("🔍 Testing fractal detection with sample data...")
    
    # Create sample data
    df = create_sample_data()
    print(f"📊 Created {len(df)} bars of sample data")
    
    # Initialize strategy
    strategy = FibonacciStrategy(fractal_period=5)
    
    # Process bars and look for fractals
    fractals_found = []
    
    for i in range(len(df)):
        if i < 10:  # Skip first 10 bars
            continue
            
        print(f"📈 Processing bar {i}: close={df.iloc[i]['close']:.5f}")
        
        # Process current bar
        try:
            results = strategy.process_bar(df, i)
            
            # Check for new fractal
            if results.get('new_fractal'):
                fractal = results['new_fractal']
                fractals_found.append(fractal)
                print(f"  🔺 FRACTAL FOUND: {fractal['fractal_type']} at {fractal['price']:.5f} (bar {fractal['bar_index']})")
                print(f"       Timestamp: {fractal['timestamp']}")
            else:
                print(f"  ⚪ No fractal at bar {i}")
                
        except Exception as e:
            print(f"  ❌ Error processing bar {i}: {e}")
            break
    
    print(f"\n✅ Found {len(fractals_found)} fractals in {i+1} bars processed")
    
    # Print fractal details
    for i, fractal in enumerate(fractals_found):
        print(f"  {i+1}. {fractal['fractal_type']} fractal at {fractal['price']:.5f} (bar {fractal['bar_index']})")
    
    return len(fractals_found) > 0

if __name__ == "__main__":
    success = test_fractal_detection()
    if success:
        print("\n✅ Fractal detection is working!")
    else:
        print("\n❌ No fractals detected - there might be an issue")
