#!/usr/bin/env python3
"""
Test script to verify the dominant swing detection fix
Tests the specific scenario from the user's screenshot
"""

import requests
import json
from datetime import datetime
import time

def test_swing_detection():
    """Test the specific scenario from the user's screenshot"""
    
    base_url = "http://localhost:8001"
    
    print("🧪 Testing Dominant Swing Detection Fix")
    print("=" * 50)
    
    # Test parameters from the user's screenshot
    test_params = {
        "symbol": "DJ30",
        "timeframe": "M1",
        "start_date": "2025-06-20T05:05:00",
        "bars_to_load": 300,
        "target_bar": 246  # Bar position from screenshot
    }
    
    print(f"📊 Test Parameters:")
    print(f"   Symbol: {test_params['symbol']}")
    print(f"   Timeframe: {test_params['timeframe']}")
    print(f"   Start Date: {test_params['start_date']}")
    print(f"   Target Bar: {test_params['target_bar']}")
    print()
    
    # Step 1: Load market data
    print("🔄 Step 1: Loading market data...")
    try:
        response = requests.post(f"{base_url}/api/data", json={
            "symbol": test_params["symbol"],
            "timeframe": test_params["timeframe"],
            "start_date": test_params["start_date"],
            "limit": test_params["bars_to_load"]
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Loaded {len(data['data'])} bars")
            print(f"   📅 Date range: {data['data'][0]['timestamp']} to {data['data'][-1]['timestamp']}")
            
            # Check price levels around the target bar
            if len(data['data']) >= test_params['target_bar']:
                target_bar_data = data['data'][test_params['target_bar']]
                print(f"   📈 Target bar data (bar {test_params['target_bar']}):")
                print(f"      Time: {target_bar_data['timestamp']}")
                print(f"      High: {target_bar_data['high']}")
                print(f"      Low: {target_bar_data['low']}")
                print(f"      Close: {target_bar_data['close']}")
        else:
            print(f"   ❌ Failed to load data: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        return False
    
    print()
    
    # Step 2: Run backtesting to trigger swing analysis
    print("🔄 Step 2: Running backtesting to trigger swing analysis...")
    try:
        # Run backtesting for a broader range to capture the swing
        backtest_response = requests.post(f"{base_url}/api/backtest", json={
            "symbol": test_params["symbol"],
            "timeframe": test_params["timeframe"],
            "start_date": "2025-06-20T04:00:00",
            "end_date": "2025-06-20T07:00:00",
            "strategy_name": "Fibonacci"
        })
        
        if backtest_response.status_code == 200:
            backtest_data = backtest_response.json()
            print(f"   ✅ Backtesting completed successfully")
            if 'run_id' in backtest_data:
                print(f"   🆔 Run ID: {backtest_data['run_id']}")
        else:
            print(f"   ❌ Backtesting failed: {backtest_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error running backtesting: {e}")
    
    print()
    
    # Step 3: Check for fractals
    print("🔄 Step 3: Checking fractal detection...")
    try:
        fractals_response = requests.get(f"{base_url}/api/fractals", params={
            "symbol": test_params["symbol"],
            "timeframe": test_params["timeframe"],
            "start_date": "2025-06-20T04:00:00",
            "end_date": "2025-06-20T07:00:00"
        })
        
        if fractals_response.status_code == 200:
            fractals_data = fractals_response.json()
            print(f"   📊 Found {len(fractals_data.get('fractals', []))} fractals")
            
            if fractals_data.get('fractals'):
                print("   📈 Recent fractals:")
                for i, fractal in enumerate(fractals_data['fractals'][-5:]):
                    print(f"      {i+1}. {fractal.get('fractal_type', 'N/A')} at {fractal.get('timestamp', 'N/A')} - Price: {fractal.get('price', 'N/A')}")
            else:
                print("   ⚠️ No fractals detected")
        else:
            print(f"   ❌ Failed to get fractals: {fractals_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking fractals: {e}")
    
    print()
    
    # Step 4: Check for swings
    print("🔄 Step 4: Checking swing detection...")
    try:
        swings_response = requests.get(f"{base_url}/api/swings", params={
            "symbol": test_params["symbol"],
            "timeframe": test_params["timeframe"],
            "start_date": "2025-06-20T04:00:00",
            "end_date": "2025-06-20T07:00:00"
        })
        
        if swings_response.status_code == 200:
            swings_data = swings_response.json()
            print(f"   📊 Found {len(swings_data.get('swings', []))} swings")
            
            if swings_data.get('swings'):
                print("   📈 Swing analysis:")
                for i, swing in enumerate(swings_data['swings']):
                    direction = swing.get('direction', 'N/A')
                    start_price = swing.get('start_price', 'N/A')
                    end_price = swing.get('end_price', 'N/A')
                    is_dominant = swing.get('is_dominant', False)
                    start_time = swing.get('start_timestamp', 'N/A')
                    
                    print(f"      {i+1}. {direction} swing: {start_price} -> {end_price}")
                    print(f"         Start time: {start_time}")
                    print(f"         Is dominant: {'YES' if is_dominant else 'NO'}")
                    print()
                    
                # Check for dominant swing analysis
                dominant_swings = [s for s in swings_data['swings'] if s.get('is_dominant', False)]
                if dominant_swings:
                    dominant_swing = dominant_swings[0]
                    print(f"   🎯 DOMINANT SWING DETECTED:")
                    print(f"      Direction: {dominant_swing.get('direction', 'N/A')}")
                    print(f"      Price range: {dominant_swing.get('start_price', 'N/A')} -> {dominant_swing.get('end_price', 'N/A')}")
                    print(f"      Time range: {dominant_swing.get('start_timestamp', 'N/A')} -> {dominant_swing.get('end_timestamp', 'N/A')}")
                    
                    # Determine expected market bias
                    direction = dominant_swing.get('direction', '').upper()
                    if direction == 'UP':
                        expected_bias = "BULLISH"
                    elif direction == 'DOWN':
                        expected_bias = "BEARISH"
                    else:
                        expected_bias = "NEUTRAL"
                    
                    print(f"      Expected market bias: {expected_bias}")
                    
                    # Check if this matches the user's expectation
                    if direction == 'UP':
                        print("   ✅ SUCCESS: Large upward swing correctly identified as dominant!")
                        print("   ✅ Market bias should be BULLISH")
                    else:
                        print("   ❌ ISSUE: Expected upward swing to be dominant, but found:", direction)
                        print("   ❌ This indicates the swing detection fix may not be working correctly")
                        
                else:
                    print("   ⚠️ No dominant swing found")
            else:
                print("   ⚠️ No swings detected")
        else:
            print(f"   ❌ Failed to get swings: {swings_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking swings: {e}")
    
    print()
    print("🏁 Test completed!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_swing_detection()