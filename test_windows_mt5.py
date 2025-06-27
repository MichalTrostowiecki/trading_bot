"""
Windows MT5 Connection Test
Direct test on Windows system with MT5 installed.
"""

import sys
from datetime import datetime, timedelta

def test_mt5_windows():
    """Test MT5 connection on Windows."""
    print("🚀 Testing MT5 Connection on Windows")
    print("=" * 50)
    
    try:
        # Import MT5
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 package imported successfully")
    except ImportError as e:
        print("❌ MetaTrader5 package not installed")
        print("Install with: pip install MetaTrader5")
        return False
    
    try:
        # Initialize MT5
        print("\n📡 Initializing MT5...")
        if not mt5.initialize():
            print(f"❌ MT5 initialization failed: {mt5.last_error()}")
            return False
        print("✅ MT5 initialized successfully")
        
        # Login with your credentials
        print("\n🔑 Logging in to Blueberry Markets Demo...")
        login = 12605399
        password = "gY81bI*L"
        
        # Try different server name variations
        server_variations = [
            "BlueberryMarkets-Demo",
            "Blueberry Markets-Demo", 
            "BlueberryMarkets Demo",
            "Blueberry-Markets-Demo"
        ]
        
        authorized = False
        working_server = None
        
        for server in server_variations:
            print(f"  Trying server: {server}")
            authorized = mt5.login(login=login, password=password, server=server)
            if authorized:
                working_server = server
                print(f"✅ Login successful with server: {server}")
                break
            else:
                print(f"  ❌ Failed with {server}: {mt5.last_error()}")
        
        if not authorized:
            print("\n❌ All server variations failed")
            print("💡 Suggestions:")
            print("1. Make sure MT5 terminal is running and logged in")
            print("2. Check the exact server name in your MT5 terminal")
            print("3. Verify credentials are correct")
            mt5.shutdown()
            return False
        
        # Get account info
        print("\n📊 Account Information:")
        account_info = mt5.account_info()
        if account_info:
            print(f"  Login: {account_info.login}")
            print(f"  Server: {account_info.server}")
            print(f"  Company: {account_info.company}")
            print(f"  Currency: {account_info.currency}")
            print(f"  Balance: {account_info.balance}")
            print(f"  Leverage: {account_info.leverage}")
        
        # Test DJ30 data
        print("\n📈 Testing DJ30 Data:")
        
        # Check if DJ30 is available
        symbols = mt5.symbols_get()
        dj30_available = any(s.name == "DJ30" for s in symbols if s.name)
        print(f"  DJ30 Available: {dj30_available}")
        
        if dj30_available:
            # Test data collection
            print("\n🔍 Collecting DJ30 M1 data...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last 7 days
            
            rates = mt5.copy_rates_from("DJ30", mt5.TIMEFRAME_M1, start_date, 1000)
            
            if rates is not None and len(rates) > 0:
                print(f"✅ Successfully collected {len(rates)} bars")
                print(f"  Date range: {datetime.fromtimestamp(rates[0][0])} to {datetime.fromtimestamp(rates[-1][0])}")
                print(f"  Latest price: {rates[-1][4]:.2f}")  # Close price
                
                # Show last 5 bars
                print("\n📊 Last 5 bars:")
                for i in range(-5, 0):
                    bar = rates[i]
                    timestamp = datetime.fromtimestamp(bar[0])
                    print(f"  {timestamp}: O={bar[1]:.2f} H={bar[2]:.2f} L={bar[3]:.2f} C={bar[4]:.2f}")
                
            else:
                print("❌ No data received for DJ30")
        else:
            print("❌ DJ30 not available - checking other symbols...")
            # Show available symbols containing '30' or 'DJ'
            available_symbols = [s.name for s in symbols if s.name and ('30' in s.name or 'DJ' in s.name.upper())]
            print(f"  Similar symbols: {available_symbols[:10]}")
        
        # Disconnect
        mt5.shutdown()
        print("\n🔌 Disconnected from MT5")
        
        return True
        
    except Exception as e:
        print(f"💥 Error: {e}")
        try:
            mt5.shutdown()
        except:
            pass
        return False

if __name__ == "__main__":
    print("Windows MT5 Connection Test")
    print("Make sure:")
    print("1. MT5 terminal is running")
    print("2. You're connected to the internet")
    print("3. MetaTrader5 package is installed (pip install MetaTrader5)")
    print("")
    
    success = test_mt5_windows()
    
    if success:
        print("\n🎉 MT5 connection test SUCCESSFUL!")
        print("✅ Ready to proceed with algorithm development")
    else:
        print("\n😞 MT5 connection test FAILED")
        print("❌ Please check the requirements above")
    
    input("\nPress Enter to exit...")