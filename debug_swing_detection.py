#!/usr/bin/env python3
"""
DEBUG: Swing Detection Logic Analysis
Systematically test what got broken during ABC pattern implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from src.strategy.fibonacci_strategy import FibonacciStrategy

def create_test_data():
    """Create test data that should generate dominant swing changes"""
    # Create test data with clear swing patterns
    dates = pd.date_range(start='2024-01-01', periods=200, freq='H')
    
    # Simulate price data with clear uptrend and downtrend swings
    prices = []
    base_price = 1000.0
    
    # Create clear swing pattern:
    # 1. Uptrend (dominant up swing)
    # 2. Small pullback (non-dominant down swing) 
    # 3. Continuation up (should create new dominant up swing)
    # 4. Larger pullback (should create dominant down swing)
    
    for i in range(200):
        if i < 50:  # Initial uptrend - should create dominant UP swing
            trend = 2.0
        elif i < 70:  # Small pullback - should be non-dominant DOWN swing
            trend = -1.0
        elif i < 120:  # Continuation up - should create new dominant UP swing
            trend = 2.5
        elif i < 200:  # Larger pullback - should create dominant DOWN swing
            trend = -2.0
        
        noise = (i % 5 - 2) * 0.5  # Small noise
        base_price += trend + noise
        prices.append(base_price)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(p*0.001) for p in prices],
        'low': [p - abs(p*0.001) for p in prices],
        'close': prices,
        'volume': [1000] * 200
    })
    df.set_index('timestamp', inplace=True)
    
    return df

def test_swing_detection_flow():
    """Test the swing detection flow step by step"""
    print("🔍 DEBUGGING SWING DETECTION FLOW")
    print("=" * 50)
    
    # Create test data
    df = create_test_data()
    print(f"📊 Created test data with {len(df)} bars")
    
    # Initialize strategy
    strategy = FibonacciStrategy(fractal_period=5, lookback_candles=140)
    
    # Process data step by step and track swing changes
    dominant_swings = []
    all_swings = []
    
    for i in range(len(df)):
        if i < 20:  # Skip first 20 bars for fractal formation
            continue
            
        print(f"\n📈 Processing bar {i}: Price {df.iloc[i]['close']:.2f}")
        
        # Process current bar
        results = strategy.process_bar(df, i)
        
        # Track swing changes
        if results.get('new_swing'):
            swing = results['new_swing']
            all_swings.append(swing)
            
            print(f"  🌊 NEW SWING: {swing['direction']} from {swing['start_fractal']['price']:.2f} to {swing['end_fractal']['price']:.2f}")
            print(f"       Dominant: {swing['is_dominant']}")
            
            if swing['is_dominant']:
                dominant_swings.append(swing)
                print(f"  ⭐ DOMINANT SWING #{len(dominant_swings)}: {swing['direction']}")
        
        # Check fractal detection
        if results.get('new_fractal'):
            fractal = results['new_fractal']
            print(f"  🔺 NEW FRACTAL: {fractal['fractal_type']} at {fractal['price']:.2f}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total swings detected: {len(all_swings)}")
    print(f"Dominant swings detected: {len(dominant_swings)}")
    
    print(f"\n🎯 DOMINANT SWING PROGRESSION:")
    for i, swing in enumerate(dominant_swings):
        print(f"  {i+1}. {swing['direction'].upper()} swing: {swing['start_fractal']['price']:.2f} → {swing['end_fractal']['price']:.2f}")
    
    return all_swings, dominant_swings

def compare_with_current_logic():
    """Compare current logic with what should happen"""
    print("\n🔍 ANALYZING CURRENT FRONTEND LOGIC")
    print("=" * 50)
    
    # Simulate the frontend logic I modified
    accumulatedDominantSwing = None
    accumulatedSwings = []
    
    # Simulate swing sequence
    test_swings = [
        {'direction': 'up', 'is_dominant': True, 'id': 'swing1'},
        {'direction': 'down', 'is_dominant': False, 'id': 'swing2'},  # Non-dominant (dotted)
        {'direction': 'up', 'is_dominant': True, 'id': 'swing3'},     # Should become new dominant
    ]
    
    print("Testing swing processing logic:")
    
    for swing in test_swings:
        print(f"\n📈 Processing swing: {swing['id']} ({swing['direction']}, dominant: {swing['is_dominant']})")
        
        # My current logic:
        previousDominantSwing = accumulatedDominantSwing
        newDominantSwing = swing if swing['is_dominant'] else None
        
        print(f"  Previous dominant: {previousDominantSwing['id'] if previousDominantSwing else 'None'}")
        print(f"  New dominant: {newDominantSwing['id'] if newDominantSwing else 'None'}")
        
        # Check dominant swing change logic
        if (previousDominantSwing and newDominantSwing and 
            previousDominantSwing['id'] != newDominantSwing['id']):
            print("  🔄 DOMINANT SWING CHANGE DETECTED - Would clear ABC patterns")
        
        # Update swings
        accumulatedSwings = []
        accumulatedSwings.append(swing)
        
        # My current update logic:
        if swing['is_dominant']:
            accumulatedDominantSwing = swing
            print(f"  ✅ Updated dominant swing to: {swing['id']}")
        else:
            print(f"  📍 Kept existing dominant swing: {accumulatedDominantSwing['id'] if accumulatedDominantSwing else 'None'}")
    
    print(f"\n🎯 Final dominant swing: {accumulatedDominantSwing['id'] if accumulatedDominantSwing else 'None'}")

if __name__ == "__main__":
    print("🚨 SWING DETECTION DEBUG ANALYSIS")
    print("=" * 60)
    
    # Test 1: Backend swing detection
    all_swings, dominant_swings = test_swing_detection_flow()
    
    # Test 2: Frontend logic simulation
    compare_with_current_logic()
    
    print("\n🔍 ANALYSIS COMPLETE - Check output above for issues")