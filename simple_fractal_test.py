#!/usr/bin/env python3
"""
Ultra-simple fractal detection test
Direct test of fractal algorithm without complex strategy layer
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.fractal_detection import FractalDetector, FractalDetectionConfig, FractalType
from src.data.database import DatabaseManager

def simple_fractal_test():
    """Simple direct test of fractal detection"""
    print("🔍 SIMPLE FRACTAL DETECTION TEST")
    print("=" * 50)
    
    # Initialize database
    try:
        db = DatabaseManager()
        db.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Get test data
    try:
        df = db.get_historical_data(
            symbol="DJ30",
            timeframe="M1",
            limit=50  # Just 50 bars for simple test
        )
        
        if df.empty:
            print("❌ No test data found")
            return False
            
        print(f"✅ Loaded {len(df)} bars")
        print(f"📊 Price range: {df['low'].min():.1f} - {df['high'].max():.1f}")
        
        # Ensure column names are uppercase (required by fractal detector)
        df.columns = df.columns.str.upper()
        print(f"📋 Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Data error: {e}")
        return False
    
    # Initialize fractal detector
    try:
        config = FractalDetectionConfig(periods=5)  # 5-bar fractal
        detector = FractalDetector(config)
        print("✅ Fractal detector initialized")
        
    except Exception as e:
        print(f"❌ Detector error: {e}")
        return False
    
    # Detect fractals
    print("\n🔍 Detecting fractals...")
    try:
        fractals = detector.detect_fractals(df)
        
        print("Index | Time            | Type | Price")
        print("-" * 45)
        
        fractal_count = len(fractals)
        
        for fractal in fractals:
            timestamp = fractal.timestamp.strftime("%H:%M")
            fractal_type = "HIGH" if fractal.type == FractalType.UP else "LOW "
            print(f"{fractal.index:5d} | {timestamp}         | {fractal_type} | {fractal.price:7.1f}")
            
    except Exception as e:
        print(f"❌ Fractal detection error: {e}")
        return False
    
    print("-" * 45)
    print(f"✅ Scan complete: {fractal_count} fractals found")
    
    if fractal_count > 0:
        print("🎉 BACKEND FRACTAL DETECTION IS WORKING!")
        return True
    else:
        print("⚠️ No fractals detected (may be normal with small dataset)")
        return False

if __name__ == "__main__":
    success = simple_fractal_test()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)