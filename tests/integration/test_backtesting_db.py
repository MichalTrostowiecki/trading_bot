#!/usr/bin/env python3
"""
Test script for backtesting database schema and importers.
Verifies that the new database tables work correctly.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import initialize_database, BacktestRun, MarketFractal, MarketSwing, BacktestSignal, MarketContext
from src.data.importers import MT4DataImporter, MT5DataImporter
from src.monitoring import get_logger

logger = get_logger("backtesting_test")


def test_database_schema():
    """Test that all new database tables can be created."""
    print("\n=== Testing Database Schema ===")
    
    try:
        # Initialize database (this creates all tables)
        db_manager = initialize_database()
        
        if not db_manager:
            print("❌ Failed to initialize database")
            return False
        
        print("✅ Database connection established")
        
        # Test creating sample records for each table
        with db_manager.get_session() as session:
            # Test BacktestRun
            run_data = {
                'strategy_name': 'Fibonacci_Test',
                'strategy_version': '1.0.0',
                'date_range_start': datetime.now() - timedelta(days=30),
                'date_range_end': datetime.now(),
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'total_trades': 25,
                'winning_trades': 15,
                'win_rate': 60.0,
                'total_profit': 150.5
            }
            
            run_id = db_manager.store_backtest_run(run_data)
            if run_id:
                print("✅ BacktestRun table working")
            else:
                print("❌ BacktestRun table failed")
                return False
            
            # Test MarketFractal
            fractal_data = {
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'timestamp': datetime.now(),
                'fractal_type': 'high',
                'price': 1.0950,
                'strength': 2,
                'validation_bars': 5,
                'is_valid': True
            }
            
            fractal_id = db_manager.store_fractal(fractal_data)
            if fractal_id:
                print("✅ MarketFractal table working")
            else:
                print("❌ MarketFractal table failed")
                return False
            
            # Test MarketSwing
            swing_data = {
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'start_timestamp': datetime.now() - timedelta(hours=10),
                'end_timestamp': datetime.now(),
                'duration_bars': 10,
                'start_price': 1.0900,
                'end_price': 1.0950,
                'direction': 'up',
                'magnitude_pips': 50,
                'magnitude_percent': 0.46,
                'fractal_start_id': fractal_id,
                'fractal_end_id': fractal_id,
                'is_dominant': True
            }
            
            swing_id = db_manager.store_swing(swing_data)
            if swing_id:
                print("✅ MarketSwing table working")
            else:
                print("❌ MarketSwing table failed")
                return False
            
            # Test BacktestSignal
            signal_data = {
                'backtest_run_id': run_id,
                'timestamp': datetime.now(),
                'signal_type': 'entry',
                'direction': 'buy',
                'price': 1.0920,
                'fibonacci_level': 38.2,
                'swing_id': swing_id,
                'confidence': 0.75,
                'executed': True,
                'outcome': 'win',
                'profit_loss_pips': 25.0
            }
            
            signal_id = db_manager.store_signal(signal_data)
            if signal_id:
                print("✅ BacktestSignal table working")
            else:
                print("❌ BacktestSignal table failed")
                return False
            
            # Test MarketContext
            context_data = {
                'symbol': 'EURUSD',
                'timestamp': datetime.now(),
                'timeframe': 'H1',
                'market_regime': 'trending',
                'volatility_level': 0.65,
                'session': 'london',
                'major_news': False
            }
            
            context_id = db_manager.store_market_context(context_data)
            if context_id:
                print("✅ MarketContext table working")
            else:
                print("❌ MarketContext table failed")
                return False
        
        print("✅ All database tables working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False


def test_database_queries():
    """Test database query operations."""
    print("\n=== Testing Database Queries ===")
    
    try:
        db_manager = initialize_database()
        if not db_manager:
            return False
        
        # Test getting backtest runs
        runs = db_manager.get_backtest_runs(symbol='EURUSD', limit=10)
        print(f"✅ Retrieved {len(runs)} backtest runs")
        
        # Test getting fractals
        fractals = db_manager.get_fractals('EURUSD', 'H1')
        print(f"✅ Retrieved {len(fractals)} fractals")
        
        # Test getting swings
        swings = db_manager.get_swings('EURUSD', 'H1', dominant_only=True)
        print(f"✅ Retrieved {len(swings)} dominant swings")
        
        # Test getting signals
        signals = db_manager.get_signals(symbol='EURUSD')
        print(f"✅ Retrieved {len(signals)} signals")
        
        # Test Fibonacci level performance analysis
        if signals:
            perf = db_manager.get_fibonacci_level_performance('EURUSD', 'H1', 38.2)
            if perf:
                print(f"✅ Fibonacci 38.2% level: {perf['total_signals']} signals, {perf['win_rate']:.1f}% win rate")
            else:
                print("✅ No performance data for Fibonacci 38.2% level")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        return False


def test_mt4_importer():
    """Test MT4 data importer (if MT4 history path is available)."""
    print("\n=== Testing MT4 Importer ===")
    
    # Common MT4 history paths
    possible_paths = [
        "C:\\Users\\%USERNAME%\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\history",
        "C:\\Program Files (x86)\\MetaTrader 4\\history",
        "/home/user/.wine/drive_c/Program Files (x86)/MetaTrader 4/history",
        # Add more paths as needed
    ]
    
    mt4_path = None
    for path_pattern in possible_paths:
        expanded_path = os.path.expandvars(path_pattern)
        if '*' in expanded_path:
            # Handle wildcard paths
            parent = Path(expanded_path).parent
            if parent.exists():
                for child in parent.iterdir():
                    if child.is_dir() and (child / 'history').exists():
                        mt4_path = child / 'history'
                        break
        else:
            if Path(expanded_path).exists():
                mt4_path = Path(expanded_path)
                break
    
    if not mt4_path:
        print("⚠️  MT4 history path not found - skipping MT4 importer test")
        print("   To test MT4 importer, ensure MT4 is installed with history data")
        return True
    
    try:
        db_manager = initialize_database()
        if not db_manager:
            return False
        
        importer = MT4DataImporter(str(mt4_path), db_manager)
        
        # Test listing available files
        info = importer.get_available_data_info()
        if info:
            print(f"✅ Found {len(info)} MT4 HST files")
            
            # Show first few files
            for i, item in enumerate(info[:3]):
                print(f"   {item['symbol']} {item['timeframe']}: {item['estimated_records']} records")
        else:
            print("⚠️  No MT4 HST files found")
        
        return True
        
    except Exception as e:
        print(f"❌ MT4 importer test failed: {e}")
        return False


def test_mt5_importer():
    """Test MT5 data importer (if MT5 is available)."""
    print("\n=== Testing MT5 Importer ===")
    
    try:
        db_manager = initialize_database()
        if not db_manager:
            return False
        
        importer = MT5DataImporter(db_manager)
        
        # Test connection
        if not importer.connect():
            print("⚠️  MT5 not available - skipping MT5 importer test")
            print("   To test MT5 importer, ensure MT5 is installed and configured")
            return True
        
        print("✅ Connected to MT5")
        
        # Test getting available symbols
        symbols = importer.get_available_symbols()
        if symbols:
            print(f"✅ Found {len(symbols)} available symbols")
            print(f"   First few: {', '.join(symbols[:5])}")
        
        # Test symbol info
        if 'EURUSD' in symbols:
            info = importer.get_symbol_info('EURUSD')
            if info:
                print(f"✅ EURUSD info: {info['digits']} digits, spread: {info['spread']}")
        
        importer.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ MT5 importer test failed: {e}")
        return False


def test_batch_operations():
    """Test batch database operations for performance."""
    print("\n=== Testing Batch Operations ===")
    
    try:
        db_manager = initialize_database()
        if not db_manager:
            return False
        
        # Test batch fractal storage
        fractals_data = []
        for i in range(100):
            fractal_data = {
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'timestamp': datetime.now() - timedelta(hours=i),
                'fractal_type': 'high' if i % 2 == 0 else 'low',
                'price': 1.0900 + (i * 0.0001),
                'strength': 2,
                'validation_bars': 5,
                'is_valid': True
            }
            fractals_data.append(fractal_data)
        
        start_time = datetime.now()
        success = db_manager.store_fractals_batch(fractals_data)
        duration = (datetime.now() - start_time).total_seconds()
        
        if success:
            print(f"✅ Stored {len(fractals_data)} fractals in {duration:.2f}s")
        else:
            print("❌ Batch fractal storage failed")
            return False
        
        # Test batch signal storage
        signals_data = []
        for i in range(50):
            # Need a valid backtest run ID first
            run_data = {
                'strategy_name': f'Test_Strategy_{i}',
                'strategy_version': '1.0.0',
                'date_range_start': datetime.now() - timedelta(days=1),
                'date_range_end': datetime.now(),
                'symbol': 'EURUSD',
                'timeframe': 'H1'
            }
            run_id = db_manager.store_backtest_run(run_data)
            
            signal_data = {
                'backtest_run_id': run_id,
                'timestamp': datetime.now() - timedelta(hours=i),
                'signal_type': 'entry',
                'direction': 'buy' if i % 2 == 0 else 'sell',
                'price': 1.0900 + (i * 0.0001),
                'fibonacci_level': 38.2,
                'confidence': 0.5 + (i * 0.01),
                'executed': True
            }
            signals_data.append(signal_data)
        
        start_time = datetime.now()
        success = db_manager.store_signals_batch(signals_data)
        duration = (datetime.now() - start_time).total_seconds()
        
        if success:
            print(f"✅ Stored {len(signals_data)} signals in {duration:.2f}s")
        else:
            print("❌ Batch signal storage failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Backtesting Database Tests")
    print("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Database Queries", test_database_queries),
        ("MT4 Importer", test_mt4_importer),
        ("MT5 Importer", test_mt5_importer),
        ("Batch Operations", test_batch_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database schema and importers are ready.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)