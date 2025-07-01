#!/usr/bin/env python3
"""
Test script for the Research Dashboard.
Tests API endpoints and basic functionality.
"""

import os
import sys
import requests
import json
import time
import threading
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import initialize_database
from src.monitoring import get_logger

logger = get_logger("dashboard_test")

class ResearchDashboardTester:
    """Test the research dashboard API endpoints."""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def wait_for_server(self, max_wait=30):
        """Wait for the server to be ready."""
        print(f"⏳ Waiting for server at {self.base_url}...")
        
        for i in range(max_wait):
            try:
                response = self.session.get(f"{self.base_url}/")
                if response.status_code == 200:
                    print(f"✅ Server ready after {i+1}s")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            
            time.sleep(1)
        
        print(f"❌ Server not ready after {max_wait}s")
        return False
    
    def test_homepage(self):
        """Test the homepage loads correctly."""
        print("\n🧪 Testing homepage...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                if "Research Dashboard" in response.text:
                    print("✅ Homepage loads with correct content")
                    return True
                else:
                    print("❌ Homepage missing expected content")
                    return False
            else:
                print(f"❌ Homepage returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Homepage test failed: {e}")
            return False
    
    def test_data_api_empty(self):
        """Test data API with no data in database."""
        print("\n🧪 Testing data API (empty database)...")
        
        try:
            data = {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if not result.get("success"):
                    print("✅ Data API correctly reports no data")
                    return True
                else:
                    print("✅ Data API returned data (unexpected but okay)")
                    return True
            else:
                print(f"❌ Data API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Data API test failed: {e}")
            return False
    
    def test_backtest_api(self):
        """Test backtest API."""
        print("\n🧪 Testing backtest API...")
        
        try:
            data = {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02",
                "strategy_name": "Fibonacci"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/backtest",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ Backtest API working")
                    print(f"   Mock results: {result['results']['total_trades']} trades")
                    return True
                else:
                    print(f"❌ Backtest failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ Backtest API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backtest API test failed: {e}")
            return False
    
    def test_fractals_api(self):
        """Test fractals API."""
        print("\n🧪 Testing fractals API...")
        
        try:
            params = {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02"
            }
            
            response = self.session.get(
                f"{self.base_url}/api/fractals",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Fractals API working ({result['count']} fractals)")
                    return True
                else:
                    print(f"❌ Fractals failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ Fractals API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Fractals API test failed: {e}")
            return False
    
    def test_swings_api(self):
        """Test swings API."""
        print("\n🧪 Testing swings API...")
        
        try:
            params = {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "start_date": "2024-01-01", 
                "end_date": "2024-01-02"
            }
            
            response = self.session.get(
                f"{self.base_url}/api/swings",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Swings API working ({result['count']} swings)")
                    return True
                else:
                    print(f"❌ Swings failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ Swings API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Swings API test failed: {e}")
            return False
    
    def test_signals_api(self):
        """Test signals API."""
        print("\n🧪 Testing signals API...")
        
        try:
            params = {
                "symbol": "EURUSD",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02"
            }
            
            response = self.session.get(
                f"{self.base_url}/api/signals",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Signals API working ({result['count']} signals)")
                    return True
                else:
                    print(f"❌ Signals failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ Signals API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Signals API test failed: {e}")
            return False
    
    def test_backtest_runs_api(self):
        """Test backtest runs API."""
        print("\n🧪 Testing backtest runs API...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/backtest-runs")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Backtest runs API working ({result['count']} runs)")
                    return True
                else:
                    print(f"❌ Backtest runs failed: {result.get('message')}")
                    return False
            else:
                print(f"❌ Backtest runs API returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backtest runs API test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests."""
        tests = [
            ("Homepage", self.test_homepage),
            ("Data API", self.test_data_api_empty),
            ("Backtest API", self.test_backtest_api),
            ("Fractals API", self.test_fractals_api),
            ("Swings API", self.test_swings_api),
            ("Signals API", self.test_signals_api),
            ("Backtest Runs API", self.test_backtest_runs_api)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ {test_name} test error: {e}")
                results.append((test_name, False))
        
        return results

def setup_test_data():
    """Set up some test data in the database."""
    print("\n📁 Setting up test data...")
    
    try:
        db_manager = initialize_database()
        if not db_manager:
            print("❌ Cannot initialize database")
            return False
        
        # Create some sample historical data
        dates = pd.date_range(start='2024-01-01', end='2024-01-03', freq='H')
        data = []
        
        base_price = 1.0900
        for i, timestamp in enumerate(dates):
            # Generate realistic OHLC data
            noise = (i % 10 - 5) * 0.0002
            open_price = base_price + noise
            high_price = open_price + abs(noise) + 0.0005
            low_price = open_price - abs(noise) - 0.0003
            close_price = open_price + noise * 0.5
            
            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 100 + (i % 50)
            })
        
        df = pd.DataFrame(data, index=dates)
        
        # Store in database
        success = db_manager.store_historical_data('EURUSD', 'H1', df)
        
        if success:
            print(f"✅ Created {len(df)} test data points")
            
            # Add some test fractals
            fractal_data = {
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'timestamp': dates[10],
                'fractal_type': 'high',
                'price': df.iloc[10]['high'],
                'strength': 2,
                'validation_bars': 5,
                'is_valid': True
            }
            
            fractal_id = db_manager.store_fractal(fractal_data)
            if fractal_id:
                print("✅ Created test fractal")
            
            return True
        else:
            print("❌ Failed to store test data")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Research Dashboard API Tests")
    print("=" * 50)
    
    # Setup test data
    setup_test_data()
    
    # Initialize tester
    tester = ResearchDashboardTester()
    
    # Wait for server to be ready
    if not tester.wait_for_server():
        print("❌ Server not available - make sure to start the dashboard first:")
        print("   python3 launch_research_dashboard.py")
        return False
    
    # Run all tests
    print("\n🚀 Running API tests...")
    results = tester.run_all_tests()
    
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
        print("🎉 All API tests passed! Research dashboard is working correctly.")
        print(f"\n🌐 Open http://localhost:8001 in your browser to use the dashboard")
    else:
        print("⚠️  Some tests failed. Check the server logs for more details.")
    
    return passed == total

if __name__ == "__main__":
    # Import pandas here to avoid import issues
    import pandas as pd
    
    success = main()
    sys.exit(0 if success else 1)