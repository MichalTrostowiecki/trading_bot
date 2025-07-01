#!/usr/bin/env python3
"""
Test MT5 Connection and Data Collection
Test connection to Blueberry Markets demo account and collect available data.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data.mt5_interface import MT5Interface
from utils.config import get_config
from monitoring import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("mt5_test")

def test_mt5_connection():
    """Test MT5 connection and data availability."""
    logger.info("🚀 Testing MT5 Connection to Blueberry Markets Demo")
    
    try:
        # Create MT5 interface
        mt5_interface = MT5Interface()
        
        # Test connection
        logger.info("📡 Attempting to connect...")
        if not mt5_interface.connect():
            logger.error("❌ Failed to connect to MT5")
            return False
        
        logger.info("✅ Successfully connected to MT5!")
        
        # Get account info
        account_info = mt5_interface.get_account_info()
        if account_info:
            logger.info(f"📊 Account Info:")
            logger.info(f"  - Login: {account_info['login']}")
            logger.info(f"  - Server: {account_info['server']}")
            logger.info(f"  - Company: {account_info['company']}")
            logger.info(f"  - Currency: {account_info['currency']}")
            logger.info(f"  - Balance: {account_info['balance']}")
            logger.info(f"  - Leverage: {account_info['leverage']}")
        
        # Test data collection for DJ30
        logger.info("📈 Testing DJ30 M1 data collection...")
        
        # Get available symbols
        symbols = mt5_interface.get_symbols()
        dj30_available = any(s.name == "DJ30" for s in symbols)
        logger.info(f"📋 DJ30 Available: {dj30_available}")
        
        if dj30_available:
            # Test different date ranges to find available data
            end_date = datetime.now()
            
            for days_back in [7, 30, 90]:
                start_date = end_date - timedelta(days=days_back)
                logger.info(f"🔍 Testing {days_back} days back ({start_date.date()} to {end_date.date()})")
                
                data = mt5_interface.get_rates(
                    symbol="DJ30",
                    timeframe=mt5_interface.TimeFrame.M1,
                    count=min(days_back * 1440, 10000),  # Max 10k bars for test
                    from_date=start_date
                )
                
                if data is not None and not data.empty:
                    logger.info(f"✅ Got {len(data)} bars of data")
                    logger.info(f"  - Date range: {data.index[0]} to {data.index[-1]}")
                    logger.info(f"  - Latest price: {data['Close'].iloc[-1]}")
                    
                    # Show sample data
                    logger.info("📊 Sample data (last 5 bars):")
                    for i in range(-5, 0):
                        bar = data.iloc[i]
                        logger.info(f"  {data.index[i]}: O={bar['Open']:.5f} H={bar['High']:.5f} L={bar['Low']:.5f} C={bar['Close']:.5f}")
                else:
                    logger.warning(f"❌ No data available for {days_back} days back")
        
        # Disconnect
        mt5_interface.disconnect()
        logger.info("🔌 Disconnected from MT5")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Error during MT5 test: {e}")
        return False

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("MT5 CONNECTION TEST - Blueberry Markets Demo")
    logger.info("=" * 60)
    
    success = test_mt5_connection()
    
    if success:
        logger.info("🎉 MT5 connection test completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Implement enhanced fractal detection")
        logger.info("2. Create visual charts")
        logger.info("3. Test swing analysis")
    else:
        logger.error("😞 MT5 connection test failed")
        logger.error("Please check:")
        logger.error("1. MT5 terminal is running")
        logger.error("2. Login credentials are correct")
        logger.error("3. Internet connection is stable")

if __name__ == "__main__":
    main()