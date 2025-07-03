#!/usr/bin/env python3
"""
Debug script to check dominant swing detection and data structure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.fibonacci_strategy import FibonacciStrategy
import pandas as pd
import numpy as np
import requests
import json

def create_simple_test_data():
    """Create simple test data with one clear dominant swing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    
    # Create a clear down swing
    prices = []
    base_price = 1.1000
    
    # Up trend first (bars 0-30)
    for i in range(30):
        price = base_price + (i * 0.0003) + np.random.normal(0, 0.00005)
        prices.append(price)
    
    # Large down swing (bars 30-70) - This should be dominant
    peak_price = prices[-1]
    for i in range(40):
        price = peak_price - (i * 0.0008) + np.random.normal(0, 0.00005)
        prices.append(price)
    
    # Small sideways (bars 70-100)
    last_price = prices[-1]
    for i in range(30):
        price = last_price + np.random.normal(0, 0.00005)
        prices.append(price)
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        high = price + np.random.uniform(0, 0.0001)
        low = price - np.random.uniform(0, 0.0001)
        open_price = price + np.random.uniform(-0.00005, 0.00005)
        close_price = price + np.random.uniform(-0.00005, 0.00005)
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': 1000
        })
    
    return pd.DataFrame(data).set_index('timestamp')

def test_backend_swing_detection():
    """Test backend swing detection and dominant marking."""
    print("🔍 Testing backend swing detection...")
    
    # Create test data
    df = create_simple_test_data()
    print(f"Created test data with {len(df)} bars")
    
    # Initialize strategy
    strategy = FibonacciStrategy(
        fractal_period=5,
        min_swing_points=0.001,
        lookback_candles=100
    )
    
    # Process all bars
    final_result = None
    for i in range(len(df)):
        result = strategy.process_bar(df, i)
        final_result = result
        
        if result.get('new_swing'):
            swing = result['new_swing']
            print(f"  Bar {i:2d}: {swing['direction'].upper()} swing: "
                  f"{swing['points']:.5f} pts ({swing['points']*10000:.1f} pips) "
                  f"- {'DOMINANT' if swing['is_dominant'] else 'normal'}")
    
    # Check final state
    print(f"\n📊 Final Strategy State:")
    print(f"  Total swings: {len(strategy.swings)}")
    
    for i, swing in enumerate(strategy.swings):
        print(f"    {i+1}. {swing.direction.upper()} swing: "
              f"{swing.points:.5f} pts ({swing.points*10000:.1f} pips) "
              f"- {'DOMINANT' if swing.is_dominant else 'normal'}")
        print(f"       From bar {swing.start_fractal.bar_index} to {swing.end_fractal.bar_index}")
    
    # Get dominant swing
    dominant_swing = strategy.get_dominant_swing()
    if dominant_swing:
        print(f"\n🎯 Dominant Swing Found:")
        print(f"  Direction: {dominant_swing.direction.upper()}")
        print(f"  Points: {dominant_swing.points:.5f} ({dominant_swing.points*10000:.1f} pips)")
        print(f"  From: {dominant_swing.start_fractal.price:.5f} to {dominant_swing.end_fractal.price:.5f}")
        print(f"  Bars: {dominant_swing.start_fractal.bar_index} to {dominant_swing.end_fractal.bar_index}")
        print(f"  is_dominant flag: {dominant_swing.is_dominant}")
        
        return True
    else:
        print(f"\n❌ No dominant swing found!")
        return False

def test_api_swing_data():
    """Test the API endpoint to see what swing data is being returned."""
    print(f"\n🌐 Testing API swing data...")
    
    try:
        # Test the analyze-all endpoint
        response = requests.get('http://localhost:8001/api/backtest/analyze-all', 
                              params={'symbol': 'EURUSD', 'timeframe': 'H1'})
        
        if response.status_code == 200:
            data = response.json()
            
            if 'swings' in data:
                swings = data['swings']
                print(f"  API returned {len(swings)} swings")
                
                for i, swing in enumerate(swings):
                    is_dominant = swing.get('is_dominant', False)
                    points = swing.get('points', 0)
                    direction = swing.get('direction', 'unknown')
                    
                    print(f"    {i+1}. {direction.upper()} swing: "
                          f"{points:.5f} pts ({points*10000:.1f} pips) "
                          f"- {'DOMINANT' if is_dominant else 'normal'}")
                    
                    if is_dominant:
                        print(f"       🎯 This swing is marked as DOMINANT in API response")
                        print(f"       Swing data structure: {json.dumps(swing, indent=2, default=str)}")
                
                # Check if any swing is marked as dominant
                dominant_swings = [s for s in swings if s.get('is_dominant', False)]
                print(f"\n  Dominant swings in API response: {len(dominant_swings)}")
                
                return len(dominant_swings) > 0
            else:
                print(f"  No 'swings' key in API response")
                print(f"  Response keys: {list(data.keys())}")
                return False
        else:
            print(f"  API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Debugging Dominant Swing Detection\n")
    
    # Test backend logic
    backend_success = test_backend_swing_detection()
    
    # Test API data
    api_success = test_api_swing_data()
    
    print(f"\n📋 Debug Results:")
    print(f"  Backend swing detection: {'✅ WORKING' if backend_success else '❌ FAILED'}")
    print(f"  API swing data: {'✅ WORKING' if api_success else '❌ FAILED'}")
    
    if backend_success and not api_success:
        print(f"\n🔍 Issue likely in API serialization or frontend processing")
    elif not backend_success:
        print(f"\n🔍 Issue in backend swing detection logic")
    elif backend_success and api_success:
        print(f"\n🔍 Issue likely in frontend swing line drawing or styling")
    
    sys.exit(0 if (backend_success and api_success) else 1)
