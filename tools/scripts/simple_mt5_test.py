"""
Simple MT5 Connection Test
Tests MT5 connection without complex imports.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test basic package imports."""
    try:
        import pandas as pd
        print(f"✅ Pandas {pd.__version__}")
        
        import numpy as np
        print(f"✅ Numpy {np.__version__}")
        
        import MetaTrader5 as mt5
        print(f"✅ MetaTrader5 {mt5.__version__}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_mt5_connection():
    """Test MT5 connection."""
    try:
        import MetaTrader5 as mt5
        
        print("\n🔌 Testing MT5 connection...")
        
        # Initialize MT5
        if not mt5.initialize():
            print("❌ Failed to initialize MT5")
            print("Error:", mt5.last_error())
            return False
        
        print("✅ MT5 initialized successfully")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"📊 Terminal: {terminal_info.name}")
            print(f"📍 Path: {terminal_info.path}")
            print(f"🔗 Connected: {terminal_info.connected}")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"👤 Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            print(f"🏢 Server: {account_info.server}")
            print(f"📈 Leverage: 1:{account_info.leverage}")
        else:
            print("⚠️  No account connected (this is normal for testing)")
        
        # Get some symbols
        symbols = mt5.symbols_get()
        if symbols:
            print(f"📊 Available symbols: {len(symbols)}")
            print("🔤 First 5 symbols:", [s.name for s in symbols[:5]])
        
        # Cleanup
        mt5.shutdown()
        print("✅ MT5 connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ MT5 connection error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Simple MT5 Connection Test")
    print("=" * 40)
    
    # Test imports first
    if not test_basic_imports():
        print("\n❌ Basic imports failed. Please install missing packages.")
        return
    
    # Test MT5 connection
    if not test_mt5_connection():
        print("\n❌ MT5 connection failed.")
        print("\n💡 Troubleshooting:")
        print("1. Ensure MetaTrader 5 is installed and running")
        print("2. Check that you're logged into an MT5 account")
        print("3. Verify MT5 allows DLL imports (Tools > Options > Expert Advisors)")
        return
    
    print("\n🎉 All tests passed! MT5 is ready to use.")
    print("\n🚀 Next step: Start the trading bot")
    print("   python main.py")

if __name__ == "__main__":
    main()