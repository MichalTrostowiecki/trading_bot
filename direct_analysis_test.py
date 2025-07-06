#!/usr/bin/env python3
"""
Direct analysis test - bypasses API and tests the core strategy logic directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategy.fibonacci_strategy import FibonacciStrategy
from src.data.database import get_database_manager
import pandas as pd
from datetime import datetime

def test_direct_analysis():
    """Test swing detection directly using the strategy class"""
    
    print("🧪 Direct Analysis Test - Swing Detection")
    print("=" * 60)
    
    # Get database manager
    db_manager = get_database_manager()
    if not db_manager:
        print("❌ Database manager not available")
        return False
    
    # Load test data
    print("📊 Loading test data...")
    start_date = datetime.fromisoformat("2025-06-20T05:05:00")
    end_date = datetime.fromisoformat("2025-06-20T10:05:00")
    
    df = db_manager.get_historical_data("DJ30", "M1", start_date, end_date, limit=300)
    
    if df.empty:
        print("❌ No data found")
        return False
    
    print(f"✅ Loaded {len(df)} bars")
    print(f"📅 Date range: {df.index[0]} to {df.index[-1]}")
    
    # Initialize strategy
    print("\n🔄 Initializing Fibonacci Strategy...")
    strategy = FibonacciStrategy()
    
    # Process data step by step to find swings
    print("\n🔄 Processing data to detect fractals and swings...")
    
    fractals = []
    swings = []
    
    for i, (timestamp, row) in enumerate(df.iterrows()):
        # Create bar data in the format expected by the strategy
        bar_data = {
            'timestamp': timestamp,
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        }
        
        # Update strategy with new bar
        try:
            result = strategy.update(bar_data)
            
            # Check if we have new fractals
            if hasattr(strategy, 'fractals') and strategy.fractals:
                if len(strategy.fractals) > len(fractals):
                    new_fractals = strategy.fractals[len(fractals):]
                    fractals.extend(new_fractals)
                    for fractal in new_fractals:
                        print(f"   🔸 New fractal: {fractal.get('type', 'N/A')} at {fractal.get('timestamp', 'N/A')} - Price: {fractal.get('price', 'N/A')}")
            
            # Check if we have new swings  
            if hasattr(strategy, 'swings') and strategy.swings:
                if len(strategy.swings) > len(swings):
                    new_swings = strategy.swings[len(swings):]
                    swings.extend(new_swings)
                    for swing in new_swings:
                        print(f"   📈 New swing: {swing.get('direction', 'N/A')} from {swing.get('start_price', 'N/A')} to {swing.get('end_price', 'N/A')}")
                        print(f"      Time: {swing.get('start_time', 'N/A')} to {swing.get('end_time', 'N/A')}")
                        print(f"      Is dominant: {swing.get('is_dominant', False)}")
                        
        except Exception as e:
            print(f"   ❌ Error processing bar {i}: {e}")
    
    print(f"\n📊 Final Analysis Results:")
    print(f"   Total fractals detected: {len(fractals)}")
    print(f"   Total swings detected: {len(swings)}")
    
    # Check for dominant swings
    dominant_swings = [s for s in swings if s.get('is_dominant', False)]
    if dominant_swings:
        print(f"   🎯 Dominant swings found: {len(dominant_swings)}")
        for i, swing in enumerate(dominant_swings):
            direction = swing.get('direction', 'N/A')
            start_price = swing.get('start_price', 'N/A')
            end_price = swing.get('end_price', 'N/A')
            print(f"      {i+1}. {direction} swing: {start_price} -> {end_price}")
            
            # Check if this is the expected upward swing
            if direction.upper() == 'UP':
                price_change = end_price - start_price if isinstance(end_price, (int, float)) and isinstance(start_price, (int, float)) else 0
                if price_change > 50:  # Significant upward movement
                    print(f"         ✅ Large upward swing detected! Price change: {price_change}")
                    print(f"         ✅ This should result in BULLISH market bias")
                    return True
    else:
        print("   ⚠️ No dominant swings found")
    
    # If no swings found, check if the strategy has the required methods
    print(f"\n🔧 Strategy debugging:")
    print(f"   Strategy class: {strategy.__class__.__name__}")
    print(f"   Has fractals attribute: {hasattr(strategy, 'fractals')}")
    print(f"   Has swings attribute: {hasattr(strategy, 'swings')}")
    print(f"   Available methods: {[m for m in dir(strategy) if not m.startswith('_')]}")
    
    return False

if __name__ == "__main__":
    test_direct_analysis()