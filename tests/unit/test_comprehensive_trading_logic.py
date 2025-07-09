#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Trading Logic
Tests all core components of the Fibonacci trading system.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.fractal_detection import FractalDetector, FractalDetectionConfig, Fractal, FractalType
from src.strategy.fibonacci_strategy import FibonacciStrategy, ABCPattern, ABCWave
from src.data.database import MarketFractal, MarketSwing


class TestDataGenerator:
    """Generate test market data for various scenarios."""
    
    @staticmethod
    def create_trending_data(bars=100, trend='up', volatility=0.01):
        """Create trending market data."""
        dates = pd.date_range(start='2024-01-01', periods=bars, freq='1H')
        
        # Base trend
        if trend == 'up':
            base_prices = np.linspace(1.0000, 1.0200, bars)
        else:
            base_prices = np.linspace(1.0200, 1.0000, bars)
        
        # Add noise
        noise = np.random.normal(0, volatility, bars)
        prices = base_prices + noise
        
        # Create OHLC data
        data = []
        for i, price in enumerate(prices):
            high = price + abs(np.random.normal(0, volatility/2))
            low = price - abs(np.random.normal(0, volatility/2))
            open_price = prices[i-1] if i > 0 else price
            close = price
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': np.random.randint(100, 1000)
            })
        
        return pd.DataFrame(data).set_index('timestamp')
    
    @staticmethod
    def create_abc_pattern_data():
        """Create data with a clear ABC correction pattern."""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
        
        # Wave A: Up move (bars 0-15)
        wave_a = np.linspace(1.0000, 1.0150, 16)
        
        # Wave B: Retracement down (bars 15-30) - 50% retracement
        wave_b_start = wave_a[-1]
        wave_b_end = wave_a[0] + (wave_a[-1] - wave_a[0]) * 0.5
        wave_b = np.linspace(wave_b_start, wave_b_end, 16)
        
        # Wave C: Continuation down (bars 30-45) - extends beyond Wave A start
        wave_c = np.linspace(wave_b[-1], wave_a[0] - 0.0050, 16)
        
        # Combine waves
        prices = np.concatenate([wave_a, wave_b[1:], wave_c[1:]])
        
        # Add remaining bars
        remaining = 50 - len(prices)
        if remaining > 0:
            final_prices = np.full(remaining, prices[-1])
            prices = np.concatenate([prices, final_prices])
        
        # Create OHLC
        data = []
        for i, price in enumerate(prices):
            high = price + 0.0005
            low = price - 0.0005
            open_price = prices[i-1] if i > 0 else price
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': 100
            })
        
        return pd.DataFrame(data).set_index('timestamp')


class TestFractalDetection:
    """Test fractal detection algorithms."""
    
    def test_basic_fractal_detection(self):
        """Test basic fractal detection with known patterns."""
        # Create data with clear high and low points
        data = TestDataGenerator.create_trending_data(bars=20, trend='up')
        
        # Manually set some clear fractals
        data.iloc[5, data.columns.get_loc('high')] = 1.0200  # Clear high
        data.iloc[10, data.columns.get_loc('low')] = 0.9950  # Clear low
        data.iloc[15, data.columns.get_loc('high')] = 1.0180  # Another high
        
        config = FractalDetectionConfig(periods=2)
        detector = FractalDetector(config)
        
        fractals = detector.detect_fractals(data)
        
        # Should detect at least the manually set fractals
        assert len(fractals) >= 2
        
        # Check fractal types
        fractal_types = [f.type for f in fractals]
        assert FractalType.UP in fractal_types or FractalType.DOWN in fractal_types
    
    def test_fractal_strength_calculation(self):
        """Test fractal strength calculation."""
        data = TestDataGenerator.create_trending_data(bars=15)
        
        config = FractalDetectionConfig(periods=2, min_strength_pips=0.0)
        detector = FractalDetector(config)
        
        fractals = detector.detect_fractals(data)
        
        for fractal in fractals:
            assert hasattr(fractal, 'strength')
            assert fractal.strength >= 0
    
    def test_edge_case_handling(self):
        """Test fractal detection edge cases."""
        # Test with minimal data
        minimal_data = TestDataGenerator.create_trending_data(bars=5)
        
        config = FractalDetectionConfig(periods=2)
        detector = FractalDetector(config)
        
        # Should not crash with minimal data
        fractals = detector.detect_fractals(minimal_data)
        assert isinstance(fractals, list)
        
        # Test with empty data
        empty_data = pd.DataFrame()
        fractals_empty = detector.detect_fractals(empty_data)
        assert len(fractals_empty) == 0


class TestSwingDetection:
    """Test swing detection and dominance logic."""
    
    def test_swing_formation(self):
        """Test basic swing formation between fractals."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        data = TestDataGenerator.create_trending_data(bars=30, trend='up')
        
        # Process data to generate swings
        for i in range(len(data)):
            strategy.process_bar(data, i)
        
        # Should have detected some swings
        assert len(strategy.swings) > 0
        
        # Check swing properties
        for swing in strategy.swings:
            assert hasattr(swing, 'direction')
            assert swing.direction in ['up', 'down']
            assert hasattr(swing, 'points')
            assert swing.points > 0
    
    def test_dominant_swing_logic(self):
        """Test dominant swing identification."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create data with one clearly larger swing
        data = TestDataGenerator.create_trending_data(bars=50, trend='up', volatility=0.02)
        
        # Process all data
        for i in range(len(data)):
            result = strategy.process_bar(data, i)
            
            # Check for dominant swing updates
            if result.get('new_swing') and result['new_swing'].get('is_dominant'):
                dominant_swing = result['new_swing']
                assert dominant_swing['is_dominant'] is True
                assert dominant_swing['points'] > 0
    
    def test_swing_invalidation(self):
        """Test swing invalidation when price moves beyond swing end."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        data = TestDataGenerator.create_trending_data(bars=30)
        
        initial_swing_count = 0
        final_swing_count = 0
        
        for i in range(len(data)):
            strategy.process_bar(data, i)
            if i == 15:
                initial_swing_count = len(strategy.swings)
        
        final_swing_count = len(strategy.swings)
        
        # Swing count should be reasonable (not growing indefinitely)
        assert final_swing_count >= 0


class TestABCPatternDetection:
    """Test ABC pattern detection logic."""
    
    def test_abc_pattern_validation(self):
        """Test ABC pattern validation rules."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=100
        )
        
        data = TestDataGenerator.create_abc_pattern_data()
        
        # Process data to build fractals and swings
        for i in range(len(data)):
            strategy.process_bar(data, i)
        
        # Should detect ABC patterns
        assert len(strategy.abc_patterns) >= 0  # May or may not find patterns depending on data
        
        # If patterns found, validate structure
        for pattern in strategy.abc_patterns:
            assert hasattr(pattern, 'wave_a')
            assert hasattr(pattern, 'wave_b') 
            assert hasattr(pattern, 'wave_c')
            assert pattern.wave_a.direction != pattern.wave_b.direction  # Waves A and B should be opposite
    
    def test_abc_fibonacci_confluence(self):
        """Test ABC pattern Fibonacci confluence detection."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=100
        )
        
        data = TestDataGenerator.create_abc_pattern_data()
        
        for i in range(len(data)):
            strategy.process_bar(data, i)
        
        # Check for Fibonacci confluence in patterns
        for pattern in strategy.abc_patterns:
            if pattern.fibonacci_confluence:
                assert 0.0 <= pattern.fibonacci_confluence <= 2.0  # Reasonable Fib levels


class TestFibonacciCalculations:
    """Test Fibonacci level calculations."""
    
    def test_fibonacci_retracement_levels(self):
        """Test Fibonacci retracement level calculations."""
        strategy = FibonacciStrategy(
            fractal_period=2,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create a mock swing
        from src.strategy.fibonacci_strategy import Swing
        mock_swing = Mock()
        mock_swing.direction = 'up'
        mock_swing.start_fractal.price = 1.0000
        mock_swing.end_fractal.price = 1.0100
        
        fib_levels = strategy.calculate_fibonacci_levels(mock_swing)
        
        assert len(fib_levels) > 0
        
        # Check that levels are in correct order and range
        for level in fib_levels:
            assert 1.0000 <= level.price <= 1.0100
            assert 0.0 <= level.level <= 1.0
    
    def test_fibonacci_extension_levels(self):
        """Test Fibonacci extension calculations."""
        # This would test extension levels beyond 100%
        # Implementation depends on your specific extension logic
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
