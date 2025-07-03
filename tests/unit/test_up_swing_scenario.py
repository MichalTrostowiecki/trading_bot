"""
Test Up Swing Scenario - Simulates the screenshot scenario
Tests that when price rallies from a low, the UP swing becomes dominant.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from strategy.fibonacci_strategy import FibonacciStrategy

def create_rally_scenario_data():
    """
    Create test data that simulates the screenshot scenario:
    1. Initial high
    2. Decline to a significant low
    3. Strong rally back up (this should create dominant UP swing)
    """
    # Create 150 bars of test data
    dates = pd.date_range(start='2024-01-01', periods=150, freq='1min')
    
    base_price = 35000
    prices = []
    
    for i in range(150):
        if i < 20:
            # Initial high area
            price = base_price + 200 + np.random.normal(0, 10)
        elif i < 60:
            # Decline to low
            decline_progress = (i - 20) / 40
            price = base_price + 200 - (decline_progress * 300) + np.random.normal(0, 15)
        elif i == 60:
            # THE LOWEST LOW
            price = base_price - 100
        elif i < 90:
            # Consolidation around the low
            price = base_price - 80 + np.random.normal(0, 20)
        else:
            # STRONG RALLY UP - this should create dominant UP swing
            rally_progress = (i - 90) / 60
            price = base_price - 80 + (rally_progress * 250) + np.random.normal(0, 10)
        
        prices.append(price)
    
    # Create OHLC data
    df_data = []
    for i, price in enumerate(prices):
        noise = np.random.normal(0, 3)
        open_price = price + noise
        close_price = price - noise
        high_price = max(open_price, close_price) + abs(np.random.normal(0, 2))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 2))
        
        df_data.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': 1000 + np.random.randint(0, 500)
        })
    
    df = pd.DataFrame(df_data, index=dates)
    return df

def test_rally_creates_up_swing():
    """Test that a strong rally from a low creates a dominant UP swing."""
    print("🚀 Testing Rally Creates UP Swing (Screenshot Scenario)")
    print("=" * 65)
    
    # Create test data
    df = create_rally_scenario_data()
    print(f"✅ Created rally scenario data: {len(df)} bars")
    print(f"   Price range: {df['low'].min():.2f} to {df['high'].max():.2f}")
    
    # Initialize strategy
    strategy = FibonacciStrategy(
        fractal_period=5,
        min_swing_points=50.0,
        lookback_candles=100  # Shorter lookback for this test
    )
    
    print(f"\n🔍 Processing bars to detect swings...")
    
    # Track swing changes
    swing_history = []
    
    for i in range(len(df)):
        result = strategy.process_bar(df, i)

        if result['new_fractal']:
            fractal = result['new_fractal']
            print(f"   Bar {i:3d}: {fractal['fractal_type'].upper()} fractal at {fractal['price']:.2f}")

        if result['new_swing']:
            swing = result['new_swing']
            swing_history.append({
                'bar': i,
                'direction': swing['direction'],
                'points': swing['points'],
                'is_dominant': swing['is_dominant']
            })

            dominant_marker = "🔥 DOMINANT" if swing['is_dominant'] else "   regular"
            print(f"   Bar {i:3d}: {dominant_marker} {swing['direction'].upper()} swing: {swing['points']:.1f} pts")
    
    print(f"\n📊 Swing History Analysis:")
    for i, swing in enumerate(swing_history):
        print(f"   {i+1}. Bar {swing['bar']:3d}: {swing['direction'].upper()} swing ({swing['points']:.1f} pts) - {'DOMINANT' if swing['is_dominant'] else 'regular'}")
    
    # Analyze final state
    print(f"\n🎯 Final Analysis:")
    
    if not strategy.current_dominant_swing:
        print("❌ No dominant swing found!")
        return False
    
    final_swing = strategy.current_dominant_swing
    print(f"   Final dominant swing: {final_swing.direction.upper()}")
    print(f"   Start: {final_swing.start_fractal.price:.2f} at bar {final_swing.start_fractal.bar_index}")
    print(f"   End: {final_swing.end_fractal.price:.2f} at bar {final_swing.end_fractal.bar_index}")
    print(f"   Points: {final_swing.points:.1f}")
    
    # Check if we have an UP swing as dominant (which should happen after the rally)
    has_up_swing = final_swing.direction == 'up'
    
    # Check if the UP swing starts from a low area and goes to a high area
    swing_starts_low = final_swing.start_fractal.price < 35000  # Below base price
    swing_ends_high = final_swing.end_fractal.price > 35000    # Above base price
    
    print(f"\n✅ Verification:")
    print(f"   Final dominant swing is UP: {has_up_swing}")
    print(f"   Swing starts from low area: {swing_starts_low}")
    print(f"   Swing ends in high area: {swing_ends_high}")
    
    success = has_up_swing and swing_starts_low and swing_ends_high
    
    if success:
        print(f"\n🎉 SUCCESS: Rally correctly created dominant UP swing!")
        print(f"   ✅ UP swing is now dominant (not DOWN)")
        print(f"   ✅ Swing reflects current market bias")
        print(f"   ✅ System adapts to price action changes")
    else:
        print(f"\n❌ FAILURE: Rally did not create expected UP swing")
        if not has_up_swing:
            print(f"   ❌ Final swing is {final_swing.direction.upper()}, should be UP")
        if not swing_starts_low:
            print(f"   ❌ Swing doesn't start from low area")
        if not swing_ends_high:
            print(f"   ❌ Swing doesn't end in high area")
    
    return success

if __name__ == "__main__":
    print("Rally UP Swing Test - Screenshot Scenario")
    print("Testing that strong rallies create dominant UP swings")
    print("")
    
    success = test_rally_creates_up_swing()
    
    if success:
        print(f"\n🎉 TEST PASSED!")
        print(f"✅ Rally scenario creates correct UP swing")
        print(f"✅ System properly adapts to market bias changes")
    else:
        print(f"\n😞 TEST FAILED")
        print(f"❌ Rally scenario logic needs more work")
    
    input("\nPress Enter to exit...")
