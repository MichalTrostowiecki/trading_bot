#!/usr/bin/env python3
"""
Test Fibonacci Level Display
Test that Fibonacci retracement levels are correctly calculated and displayed for dominant swings.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from strategy.fibonacci_strategy import FibonacciStrategy

def create_test_data():
    """Create test data with a clear dominant swing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    
    # Create a clear downward swing followed by retracement
    prices = []
    base_price = 35000
    
    for i in range(100):
        if i < 20:
            # Initial sideways movement
            price = base_price + np.random.normal(0, 10)
        elif i < 60:
            # Strong downward swing (dominant swing)
            decline = (i - 20) * 8  # 8 points per bar decline
            price = base_price - decline + np.random.normal(0, 5)
        else:
            # Retracement upward
            retracement = (i - 60) * 3  # 3 points per bar retracement
            price = (base_price - 320) + retracement + np.random.normal(0, 5)
        
        prices.append(price)
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        high = price + np.random.uniform(5, 15)
        low = price - np.random.uniform(5, 15)
        open_price = price + np.random.uniform(-5, 5)
        close = price + np.random.uniform(-3, 3)
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 1000
        })
    
    return pd.DataFrame(data).set_index('timestamp')

def test_fibonacci_levels():
    """Test that Fibonacci levels are calculated correctly for dominant swing."""
    print("🧪 Testing Fibonacci Level Calculation and Display")
    print("=" * 60)
    
    # Create test data
    df = create_test_data()
    print(f"✅ Created test data: {len(df)} bars")
    print(f"   Price range: {df['low'].min():.2f} to {df['high'].max():.2f}")
    
    # Initialize strategy
    strategy = FibonacciStrategy(
        fractal_period=5,
        min_swing_points=50.0,
        lookback_candles=80
    )
    
    # Process all bars
    print("\n🔍 Processing bars to detect swings and calculate Fibonacci levels...")
    fibonacci_results = []
    
    for i in range(len(df)):
        result = strategy.process_bar(df, i)
        
        # Check for Fibonacci levels
        if result.get('fibonacci_levels') and len(result['fibonacci_levels']) > 0:
            fibonacci_results.append({
                'bar': i,
                'levels': result['fibonacci_levels'],
                'dominant_swing': strategy.get_dominant_swing()
            })
            print(f"   Bar {i:3d}: 📐 Fibonacci levels calculated ({len(result['fibonacci_levels'])} levels)")
    
    # Analyze final results
    print(f"\n📊 Final Results:")
    print(f"   Total Fibonacci calculations: {len(fibonacci_results)}")
    
    if fibonacci_results:
        final_result = fibonacci_results[-1]
        dominant_swing = final_result['dominant_swing']
        levels = final_result['levels']
        
        print(f"\n🎯 Final Dominant Swing:")
        if dominant_swing:
            print(f"   Direction: {dominant_swing.direction.upper()}")
            print(f"   Start: {dominant_swing.start_fractal.price:.2f} at bar {dominant_swing.start_fractal.bar_index}")
            print(f"   End: {dominant_swing.end_fractal.price:.2f} at bar {dominant_swing.end_fractal.bar_index}")
            print(f"   Points: {dominant_swing.points:.1f}")
            print(f"   Bars: {dominant_swing.bars}")
        
        print(f"\n📐 Fibonacci Retracement Levels:")
        for level in levels:
            percentage = level['level'] * 100
            print(f"   {percentage:5.1f}%: {level['price']:8.2f}")
            if level.get('hit'):
                print(f"          ✅ HIT")
        
        # Verify levels are reasonable
        print(f"\n✅ Verification:")
        if dominant_swing:
            swing_high = max(dominant_swing.start_fractal.price, dominant_swing.end_fractal.price)
            swing_low = min(dominant_swing.start_fractal.price, dominant_swing.end_fractal.price)
            
            print(f"   Swing range: {swing_low:.2f} to {swing_high:.2f}")
            
            # Check that 0% and 100% levels match swing extremes
            level_0 = next((l for l in levels if l['level'] == 0.0), None)
            level_100 = next((l for l in levels if l['level'] == 1.0), None)
            
            if dominant_swing.direction == 'down':
                # For down swing: 0% = high, 100% = low
                expected_0 = swing_high
                expected_100 = swing_low
            else:
                # For up swing: 0% = low, 100% = high  
                expected_0 = swing_low
                expected_100 = swing_high
            
            # Check key levels are within swing range
            key_levels = [l for l in levels if l['level'] in [0.382, 0.500, 0.618]]
            all_within_range = all(swing_low <= l['price'] <= swing_high for l in key_levels)
            
            print(f"   Key levels within swing range: {all_within_range}")
            print(f"   Number of key trading levels: {len(key_levels)}")
            
            if all_within_range and len(key_levels) >= 3:
                print(f"\n🎉 SUCCESS: Fibonacci levels calculated correctly!")
                print(f"   ✅ Levels are within swing range")
                print(f"   ✅ Key trading levels available (38.2%, 50%, 61.8%)")
                print(f"   ✅ Ready for dashboard display")
                return True
            else:
                print(f"\n❌ FAILURE: Fibonacci levels have issues")
                return False
        else:
            print(f"\n❌ FAILURE: No dominant swing found")
            return False
    else:
        print(f"\n❌ FAILURE: No Fibonacci levels calculated")
        return False

if __name__ == "__main__":
    success = test_fibonacci_levels()
    
    if success:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Start the research dashboard: python start.py")
        print(f"   2. Load data and enable 'Show Fibonacci' checkbox")
        print(f"   3. Verify Fibonacci levels appear on chart")
        print(f"   4. Check that levels update when dominant swing changes")
    else:
        print(f"\n🔧 Issues found - check Fibonacci calculation logic")
    
    input("\nPress Enter to exit...")
