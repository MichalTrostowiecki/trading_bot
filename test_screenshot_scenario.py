#!/usr/bin/env python3
"""
Test script to replicate the exact screenshot scenario and verify the swing detection fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import direct strategy components
from src.strategy.fibonacci_strategy import FibonacciStrategy
from src.data.database import DatabaseManager
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_screenshot_scenario():
    """Test the exact scenario from the user's screenshot"""
    
    print("🔍 Testing Screenshot Scenario - Swing Detection Fix")
    print("=" * 70)
    
    # Initialize database connection directly
    try:
        # Try to connect to the database directly
        db_path = "data/trading_bot.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found at: {db_path}")
            # Try alternative paths
            alternative_paths = [
                "trading_bot.db",
                "../data/trading_bot.db",
                "src/data/trading_bot.db"
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    db_path = alt_path
                    print(f"✅ Found database at: {db_path}")
                    break
            else:
                print(f"❌ Database not found in any of the expected locations")
                return False
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Load specific data for the screenshot scenario
        target_date = "2025-06-20 05:05:00"
        end_date = "2025-06-20 10:05:00"
        
        query = """
        SELECT timestamp, open, high, low, close, volume
        FROM historical_data 
        WHERE symbol = 'DJ30' 
        AND timeframe = 'M1' 
        AND timestamp >= ? 
        AND timestamp <= ?
        ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, conn, params=(target_date, end_date))
        conn.close()
        
        if df.empty:
            print(f"❌ No data found for DJ30 M1 between {target_date} and {end_date}")
            return False
        
        # Convert timestamp to datetime index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        print(f"📊 Data loaded: {len(df)} bars")
        print(f"📅 Time range: {df.index[0]} to {df.index[-1]}")
        
        # Show price range for context
        print(f"📈 Price range: {df['low'].min():.2f} to {df['high'].max():.2f}")
        
        # Find the significant price moves
        price_range = df['high'].max() - df['low'].min()
        print(f"💹 Total price range: {price_range:.2f} points")
        
        # Initialize Fibonacci strategy
        strategy = FibonacciStrategy()
        
        print("\n🔄 Processing bars to detect swings...")
        
        # Process each bar
        for i, (timestamp, row) in enumerate(df.iterrows()):
            # Update strategy using process_bar method
            try:
                result = strategy.process_bar(df, i)
                
                # Check for swing updates every 20 bars
                if i % 20 == 0:
                    current_state = strategy.get_current_state()
                    
                    if current_state.get('swings'):
                        print(f"\n📊 Bar {i} ({timestamp}): {len(current_state['swings'])} swings detected")
                        
                        # Check for dominant swing
                        dominant_swing = current_state.get('dominant_swing')
                        if dominant_swing:
                            direction = dominant_swing['direction']
                            points = dominant_swing['points']
                            start_price = dominant_swing['start_price']
                            end_price = dominant_swing['end_price']
                            
                            print(f"   🎯 Dominant swing: {direction.upper()} ({points:.1f} pts)")
                            print(f"      From {start_price:.2f} to {end_price:.2f}")
                            
                            # Check if this is the expected large upward swing
                            if direction == 'up' and points > 50:
                                print(f"   ✅ GOOD: Large upward swing detected as dominant!")
                            elif direction == 'down' and points > 50:
                                print(f"   ❌ ISSUE: Large downward swing detected as dominant (may be incorrect)")
                            
                        # Show market bias
                        market_bias = strategy.get_market_bias()
                        if market_bias:
                            print(f"   📈 Market bias: {market_bias['bias']}")
                            
            except Exception as e:
                print(f"❌ Error processing bar {i}: {e}")
                continue
        
        # Final analysis
        print("\n📊 Final Analysis:")
        print("-" * 40)
        
        final_state = strategy.get_current_state()
        
        # Check fractals
        fractals = final_state.get('fractals', [])
        print(f"🔸 Total fractals: {len(fractals)}")
        
        if fractals:
            # Fractals might be objects, not dictionaries
            try:
                high_fractals = [f for f in fractals if getattr(f, 'fractal_type', f.get('fractal_type', '')) == 'high']
                low_fractals = [f for f in fractals if getattr(f, 'fractal_type', f.get('fractal_type', '')) == 'low']
                print(f"   High fractals: {len(high_fractals)}")
                print(f"   Low fractals: {len(low_fractals)}")
            except:
                print(f"   Fractal structure issue - skipping detailed analysis")
        
        # Check swings
        swings = final_state.get('swings', [])
        print(f"📈 Total swings: {len(swings)}")
        
        if swings:
            for i, swing in enumerate(swings):
                direction = swing['direction']
                points = swing['points']
                is_dominant = swing['is_dominant']
                start_price = swing['start_price']
                end_price = swing['end_price']
                
                status = "DOMINANT" if is_dominant else "secondary"
                print(f"   {i+1}. {direction.upper()} swing: {start_price:.2f} -> {end_price:.2f} ({points:.1f} pts) [{status}]")
        
        # Check dominant swing specifically
        dominant_swing = final_state.get('dominant_swing')
        if dominant_swing:
            direction = dominant_swing['direction']
            points = dominant_swing['points']
            start_price = dominant_swing['start_price']
            end_price = dominant_swing['end_price']
            
            print(f"\n🎯 DOMINANT SWING ANALYSIS:")
            print(f"   Direction: {direction.upper()}")
            print(f"   Magnitude: {points:.1f} points")
            print(f"   Price range: {start_price:.2f} -> {end_price:.2f}")
            
            # Verify if this matches the expected outcome
            print(f"\n🔍 EXPECTATION CHECK:")
            if direction == 'up' and points > 50:
                print(f"   ✅ SUCCESS: Large upward swing ({points:.1f} pts) correctly identified as dominant")
                print(f"   ✅ Market bias should be BULLISH")
                
                # Check market bias
                market_bias = strategy.get_market_bias()
                if market_bias:
                    bias = market_bias['bias']
                    print(f"   📊 Actual market bias: {bias}")
                    if bias.upper() in ['BULLISH', 'UP']:
                        print(f"   ✅ PERFECT: Market bias correctly shows {bias}")
                        return True
                    else:
                        print(f"   ❌ ISSUE: Market bias shows {bias}, expected BULLISH")
                        return False
                else:
                    print(f"   ⚠️ WARNING: No market bias calculated")
                    return False
            else:
                print(f"   ❌ ISSUE: Expected large upward swing, got {direction} with {points:.1f} points")
                return False
        else:
            print(f"   ❌ ISSUE: No dominant swing detected")
            return False
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        return False

if __name__ == "__main__":
    success = test_screenshot_scenario()
    
    if success:
        print("\n🎉 TEST PASSED: Swing detection fix working correctly!")
    else:
        print("\n❌ TEST FAILED: Swing detection needs investigation")