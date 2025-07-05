#!/usr/bin/env python3
"""
DEBUG: Swing Formation Logic
Deep dive into why swings aren't being formed from fractals
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from src.strategy.fibonacci_strategy import FibonacciStrategy

def debug_fractal_detection():
    """Debug why fractals aren't being detected properly"""
    print("🔍 DEBUGGING FRACTAL DETECTION")
    print("=" * 40)
    
    # Create simple test data with obvious fractals
    prices = [100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 99, 100, 101, 102]
    #             0   1   2   3   4   5   6   7   8  9  10  11  12  13  14
    #                         ^HIGH FRACTAL (should be detected at index 4)
    #                                                   ^LOW FRACTAL (should be detected at index 10)
    
    dates = pd.date_range(start='2024-01-01', periods=len(prices), freq='h')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 0.1 for p in prices],
        'low': [p - 0.1 for p in prices],
        'close': prices,
        'volume': [1000] * len(prices)
    })
    df.set_index('timestamp', inplace=True)
    
    print(f"📊 Created simple test data:")
    for i, price in enumerate(prices):
        print(f"  Bar {i}: {price}")
    
    strategy = FibonacciStrategy(fractal_period=5, lookback_candles=140)
    
    fractals_found = []
    
    for i in range(len(df)):
        print(f"\n📈 Processing bar {i}: Price {df.iloc[i]['close']}")
        
        results = strategy.process_bar(df, i)
        
        if results.get('new_fractal'):
            fractal = results['new_fractal']
            fractals_found.append(fractal)
            print(f"  🔺 FRACTAL FOUND: {fractal['fractal_type']} at bar {fractal['bar_index']} price {fractal['price']}")
        
        # Show current fractals in strategy
        print(f"  📋 Total fractals in strategy: {len(strategy.fractals)}")
    
    print(f"\n📊 FRACTAL SUMMARY:")
    print(f"Total fractals found: {len(fractals_found)}")
    for fractal in fractals_found:
        print(f"  {fractal['fractal_type']} fractal at bar {fractal['bar_index']}, price {fractal['price']}")
    
    return fractals_found, strategy

def debug_swing_formation_logic():
    """Debug the swing formation logic step by step"""
    print("\n🔍 DEBUGGING SWING FORMATION LOGIC")
    print("=" * 40)
    
    fractals, strategy = debug_fractal_detection()
    
    if len(fractals) < 2:
        print("❌ NOT ENOUGH FRACTALS TO FORM SWINGS")
        return
    
    print(f"\n🌊 ANALYZING SWING FORMATION FROM {len(fractals)} FRACTALS:")
    
    # Manual swing formation check
    for i in range(len(fractals) - 1):
        fractal1 = fractals[i]
        fractal2 = fractals[i + 1]
        
        print(f"\n  Checking swing between:")
        print(f"    Fractal 1: {fractal1['fractal_type']} at bar {fractal1['bar_index']}, price {fractal1['price']}")
        print(f"    Fractal 2: {fractal2['fractal_type']} at bar {fractal2['bar_index']}, price {fractal2['price']}")
        
        # Check swing validity conditions
        price_diff = abs(fractal2['price'] - fractal1['price'])
        print(f"    Price difference: {price_diff}")
        print(f"    Min swing points required: {strategy.min_swing_points}")
        
        if price_diff >= strategy.min_swing_points:
            print(f"    ✅ Price difference meets minimum requirement")
        else:
            print(f"    ❌ Price difference too small")
        
        # Check fractal types
        if fractal1['fractal_type'] != fractal2['fractal_type']:
            print(f"    ✅ Different fractal types (good for swing)")
        else:
            print(f"    ❌ Same fractal types (can't form swing)")

def debug_current_strategy_state():
    """Debug the current strategy state"""
    print("\n🔍 DEBUGGING CURRENT STRATEGY STATE")
    print("=" * 40)
    
    fractals, strategy = debug_fractal_detection()
    
    print(f"Strategy configuration:")
    print(f"  Fractal period: {strategy.fractal_period}")
    print(f"  Min swing points: {strategy.min_swing_points}")
    print(f"  Lookback candles: {strategy.lookback_candles}")
    
    print(f"\nStrategy internal state:")
    print(f"  Fractals: {len(strategy.fractals)}")
    print(f"  Swings: {len(strategy.swings)}")
    print(f"  Current bar: {strategy.current_bar}")
    print(f"  Dominant trend: {strategy.dominant_trend}")
    print(f"  Current dominant swing: {strategy.current_dominant_swing}")

if __name__ == "__main__":
    print("🚨 SWING FORMATION DEBUG ANALYSIS")
    print("=" * 60)
    
    debug_fractal_detection()
    debug_swing_formation_logic()
    debug_current_strategy_state()
    
    print("\n🔍 ANALYSIS COMPLETE")