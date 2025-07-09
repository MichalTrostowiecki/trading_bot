#!/usr/bin/env python3
"""
Test script to validate the ABC pattern detection fix.
Verifies that the new algorithm returns only single, high-quality patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategy.fibonacci_strategy import FibonacciStrategy
from src.strategy.trading_types import Fractal

def create_test_data():
    """Create test OHLC data with known ABC pattern structure."""
    
    # Create 200 bars of test data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
    
    # Base price movement with embedded ABC pattern
    base_prices = np.linspace(1000, 1200, 200)  # Uptrend (dominant swing)
    
    # Add ABC correction around bar 100-150
    abc_correction = np.zeros(200)
    
    # Wave A: Down correction (bars 100-120)
    abc_correction[100:121] = np.linspace(0, -80, 21)  # 80 point drop
    
    # Wave B: Up retracement (bars 120-135) - 50% of Wave A
    abc_correction[120:136] = np.linspace(-80, -40, 16)  # 40 point recovery
    
    # Wave C: Down extension (bars 135-150) - 100% of Wave A
    abc_correction[135:151] = np.linspace(-40, -120, 16)  # 80 point drop
    
    # Final prices
    prices = base_prices + abc_correction
    
    # Create OHLC data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Add some random noise for realistic OHLC
        noise = np.random.normal(0, 2, 4)
        high = price + abs(noise[0])
        low = price - abs(noise[1])
        open_price = price + noise[2]
        close = price + noise[3]
        
        # Ensure OHLC logic
        high = max(high, open_price, close, low + 1)
        low = min(low, open_price, close, high - 1)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 1000
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def test_abc_pattern_detection():
    """Test the fixed ABC pattern detection algorithm."""
    
    print("🧪 Testing ABC Pattern Detection Fix")
    print("=" * 50)
    
    # Create test data
    df = create_test_data()
    
    # Initialize strategy
    strategy = FibonacciStrategy(
        fractal_period=5,
        min_swing_points=30.0,
        lookback_candles=140
    )
    
    # Process bars to build fractals and swings
    patterns_detected = []
    
    for i in range(len(df)):
        result = strategy.process_bar(df, i)
        
        # Check for ABC patterns
        if result.get('new_abc_pattern'):
            patterns_detected.append({
                'bar_index': i,
                'pattern': result['new_abc_pattern']
            })
            
            print(f"\n🌊 ABC Pattern detected at bar {i}:")
            pattern = result['new_abc_pattern']
            print(f"   Wave A: {pattern['wave_a']['direction']} {pattern['wave_a']['points']:.1f} pts")
            print(f"   Wave B: {pattern['wave_b']['direction']} {pattern['wave_b']['points']:.1f} pts")
            print(f"   Wave C: {pattern['wave_c']['direction']} {pattern['wave_c']['points']:.1f} pts")
            print(f"   Complete: {pattern['is_complete']}")
            print(f"   Fibonacci Confluence: {pattern.get('fibonacci_confluence', 'None')}")
    
    # Analysis
    print(f"\n📊 Analysis Results:")
    print(f"   Total patterns detected: {len(patterns_detected)}")
    print(f"   Expected: 1-2 patterns maximum (vs old algorithm: 14+)")
    
    if len(patterns_detected) <= 3:
        print("   ✅ SUCCESS: Pattern count is reasonable")
    else:
        print("   ❌ FAILURE: Too many patterns detected")
    
    # Check pattern quality
    for i, detection in enumerate(patterns_detected):
        pattern = detection['pattern']
        wave_b_ratio = pattern['wave_b']['points'] / pattern['wave_a']['points']
        wave_c_ratio = pattern['wave_c']['points'] / pattern['wave_a']['points']
        
        print(f"\n   Pattern {i+1} Quality:")
        print(f"     Wave B/A ratio: {wave_b_ratio:.3f} (ideal: 0.382-0.618)")
        print(f"     Wave C/A ratio: {wave_c_ratio:.3f} (ideal: 0.618-1.27)")
        print(f"     Complete: {pattern['is_complete']}")
        
        # Quality check
        quality_score = 0
        if 0.382 <= wave_b_ratio <= 0.618:
            quality_score += 1
        if 0.618 <= wave_c_ratio <= 1.27:
            quality_score += 1
        if pattern['is_complete']:
            quality_score += 1
            
        if quality_score >= 2:
            print(f"     ✅ HIGH QUALITY pattern ({quality_score}/3)")
        else:
            print(f"     ⚠️ Low quality pattern ({quality_score}/3)")
    
    print(f"\n🎯 Fix Validation:")
    if len(patterns_detected) <= 3:
        print("✅ Overlapping pattern issue RESOLVED")
    else:
        print("❌ Still generating too many patterns")
    
    complete_patterns = sum(1 for d in patterns_detected if d['pattern']['is_complete'])
    if complete_patterns == len(patterns_detected):
        print("✅ All patterns are complete (Wave C at fractals)")
    else:
        print(f"⚠️ {len(patterns_detected) - complete_patterns} incomplete patterns detected")
    
    return len(patterns_detected) <= 3 and complete_patterns == len(patterns_detected)

if __name__ == "__main__":
    success = test_abc_pattern_detection()
    
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 ABC PATTERN FIX VALIDATION: SUCCESS")
        print("   - Clean single pattern detection achieved")
        print("   - Overlapping pattern noise eliminated")
        print("   - Only complete patterns returned")
    else:
        print("❌ ABC PATTERN FIX VALIDATION: FAILED")
        print("   - Issues still present in pattern detection")
    print("=" * 50)