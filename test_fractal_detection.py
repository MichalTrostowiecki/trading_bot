"""
Test Fractal Detection with Real DJ30 Data
Run this on Windows to test fractal detection with your MT5 data.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_fractal_detection():
    """Test fractal detection with real DJ30 data from MT5."""
    print("🚀 Testing Fractal Detection with Real DJ30 Data")
    print("=" * 60)
    
    try:
        # Import required modules
        import MetaTrader5 as mt5
        import pandas as pd
        from core.fractal_detection import FractalDetector, FractalDetectionConfig, FractalType
        
        print("✅ All modules imported successfully")
        
        # Connect to MT5
        print("\n📡 Connecting to MT5...")
        if not mt5.initialize():
            print(f"❌ MT5 initialization failed: {mt5.last_error()}")
            return False
        
        # Login
        login = 12605399
        password = "gY81bI*L"
        server = "BlueberryMarkets-Demo"
        
        if not mt5.login(login=login, password=password, server=server):
            print(f"❌ Login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        print("✅ Connected to MT5 successfully")
        
        # Get DJ30 data (last 5000 bars for good fractal detection)
        print("\n📈 Collecting DJ30 M1 data...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week
        
        rates = mt5.copy_rates_from("DJ30", mt5.TIMEFRAME_M1, start_date, 5000)
        
        if rates is None or len(rates) == 0:
            print("❌ No data received")
            mt5.shutdown()
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low', 
            'close': 'Close',
            'tick_volume': 'Volume'
        }, inplace=True)
        
        print(f"✅ Collected {len(df)} bars from {df.index[0]} to {df.index[-1]}")
        print(f"   Price range: {df['Low'].min():.2f} to {df['High'].max():.2f}")
        
        # Test different fractal configurations
        configs_to_test = [
            ("3-bar", FractalDetectionConfig(periods=3)),
            ("5-bar", FractalDetectionConfig(periods=5)),
            ("7-bar", FractalDetectionConfig(periods=7)),
            ("5-bar with strength", FractalDetectionConfig(periods=5, min_strength_pips=20.0)),
        ]
        
        print("\n🔍 Testing Fractal Detection Configurations:")
        print("-" * 60)
        
        for config_name, config in configs_to_test:
            print(f"\n📊 Testing {config_name} fractals...")
            
            try:
                detector = FractalDetector(config)
                fractals = detector.detect_fractals(df)
                
                up_fractals = [f for f in fractals if f.type == FractalType.UP]
                down_fractals = [f for f in fractals if f.type == FractalType.DOWN]
                
                print(f"✅ {config_name}:")
                print(f"   Total fractals: {len(fractals)}")
                print(f"   Up fractals: {len(up_fractals)}")
                print(f"   Down fractals: {len(down_fractals)}")
                
                if fractals:
                    # Show latest 5 fractals
                    latest_fractals = sorted(fractals, key=lambda f: f.index)[-5:]
                    print(f"   Latest 5 fractals:")
                    for f in latest_fractals:
                        print(f"     {f.timestamp.strftime('%m-%d %H:%M')}: {f.type.value.upper()} at {f.price:.2f} (strength: {f.strength:.2f})")
                
                # Calculate statistics
                stats = detector.calculate_fractal_statistics(fractals)
                if stats:
                    print(f"   Avg time between fractals: {stats.get('avg_time_between_fractals', 'N/A'):.1f} bars")
                    if 'up_avg_strength' in stats:
                        print(f"   Up fractal avg strength: {stats['up_avg_strength']:.2f}")
                    if 'down_avg_strength' in stats:
                        print(f"   Down fractal avg strength: {stats['down_avg_strength']:.2f}")
                
            except Exception as e:
                print(f"❌ Error with {config_name}: {e}")
        
        # Test latest price action for potential new fractals
        print(f"\n🎯 Latest Price Action Analysis:")
        print(f"Current price: {df['Close'].iloc[-1]:.2f}")
        print(f"Last 10 bars high: {df['High'].tail(10).max():.2f}")
        print(f"Last 10 bars low: {df['Low'].tail(10).min():.2f}")
        
        # Disconnect
        mt5.shutdown()
        print("\n🔌 Disconnected from MT5")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install required packages:")
        print("pip install MetaTrader5 pandas numpy")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Fractal Detection Test with Real DJ30 Data")
    print("Make sure:")
    print("1. MT5 terminal is running")
    print("2. Required packages are installed")
    print("3. You're connected to the internet")
    print("")
    
    success = test_fractal_detection()
    
    if success:
        print("\n🎉 Fractal detection test SUCCESSFUL!")
        print("✅ Ready to build swing analysis system")
    else:
        print("\n😞 Fractal detection test FAILED")
    
    input("\nPress Enter to exit...")