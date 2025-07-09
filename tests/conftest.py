#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for trading bot tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_ohlc_data():
    """Generate sample OHLC data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # Generate realistic price movements
    np.random.seed(42)  # For reproducible tests
    returns = np.random.normal(0, 0.001, 100)  # 0.1% volatility
    prices = 1.0000 * np.exp(np.cumsum(returns))
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Create realistic OHLC from close price
        volatility = 0.0005
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': np.random.randint(100, 1000)
        })
    
    return pd.DataFrame(data).set_index('timestamp')


@pytest.fixture
def trending_up_data():
    """Generate uptrending market data."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    
    # Create clear uptrend
    base_prices = np.linspace(1.0000, 1.0200, 50)
    noise = np.random.normal(0, 0.0005, 50)
    prices = base_prices + noise
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price + 0.0003
        low = price - 0.0003
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': 100
        })
    
    return pd.DataFrame(data).set_index('timestamp')


@pytest.fixture
def trending_down_data():
    """Generate downtrending market data."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    
    # Create clear downtrend
    base_prices = np.linspace(1.0200, 1.0000, 50)
    noise = np.random.normal(0, 0.0005, 50)
    prices = base_prices + noise
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price + 0.0003
        low = price - 0.0003
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': 100
        })
    
    return pd.DataFrame(data).set_index('timestamp')


@pytest.fixture
def sideways_data():
    """Generate sideways/ranging market data."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    
    # Create sideways movement between 1.0000 and 1.0100
    data = []
    for i, date in enumerate(dates):
        # Oscillate between support and resistance
        cycle_position = (i % 20) / 20  # 20-bar cycles
        base_price = 1.0000 + (0.0100 * np.sin(cycle_position * 2 * np.pi))
        noise = np.random.normal(0, 0.0010, 1)[0]
        price = base_price + noise
        
        high = price + 0.0005
        low = price - 0.0005
        open_price = data[-1]['close'] if data else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': 100
        })
    
    return pd.DataFrame(data).set_index('timestamp')


@pytest.fixture
def abc_pattern_data():
    """Generate data with a clear ABC correction pattern."""
    dates = pd.date_range(start='2024-01-01', periods=45, freq='1H')
    
    # Wave A: Up move (bars 0-15)
    wave_a = np.linspace(1.0000, 1.0150, 15)
    
    # Wave B: Retracement down (bars 15-30) - 50% retracement
    wave_b_start = wave_a[-1]
    wave_b_end = wave_a[0] + (wave_a[-1] - wave_a[0]) * 0.5
    wave_b = np.linspace(wave_b_start, wave_b_end, 15)
    
    # Wave C: Continuation down (bars 30-45) - extends beyond Wave A start
    wave_c = np.linspace(wave_b[-1], wave_a[0] - 0.0050, 15)
    
    # Combine waves
    prices = np.concatenate([wave_a, wave_b, wave_c])
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price + 0.0005
        low = price - 0.0005
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': 100
        })
    
    return pd.DataFrame(data).set_index('timestamp')


@pytest.fixture
def fibonacci_strategy():
    """Create a FibonacciStrategy instance with standard parameters."""
    from src.strategy.fibonacci_strategy import FibonacciStrategy
    
    return FibonacciStrategy(
        fractal_period=5,
        min_swing_points=0.001,
        lookback_candles=100
    )


@pytest.fixture
def fractal_detector():
    """Create a FractalDetector instance with standard configuration."""
    from src.core.fractal_detection import FractalDetector, FractalDetectionConfig
    
    config = FractalDetectionConfig(periods=2)
    return FractalDetector(config)


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "fractal: mark test as fractal detection related"
    )
    config.addinivalue_line(
        "markers", "swing: mark test as swing detection related"
    )
    config.addinivalue_line(
        "markers", "abc: mark test as ABC pattern related"
    )
    config.addinivalue_line(
        "markers", "fibonacci: mark test as Fibonacci calculation related"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as frontend logic related"
    )


# Custom assertions for trading-specific validations
class TradingAssertions:
    """Custom assertions for trading logic validation."""
    
    @staticmethod
    def assert_valid_fractal(fractal):
        """Assert that a fractal object is valid."""
        assert hasattr(fractal, 'type')
        assert hasattr(fractal, 'price')
        assert hasattr(fractal, 'timestamp')
        assert hasattr(fractal, 'index')
        assert fractal.price > 0
        assert fractal.index >= 0
    
    @staticmethod
    def assert_valid_swing(swing):
        """Assert that a swing object is valid."""
        assert hasattr(swing, 'direction')
        assert swing.direction in ['up', 'down']
        assert hasattr(swing, 'points')
        assert swing.points > 0
        assert hasattr(swing, 'start_fractal')
        assert hasattr(swing, 'end_fractal')
    
    @staticmethod
    def assert_valid_abc_pattern(pattern):
        """Assert that an ABC pattern is valid."""
        assert hasattr(pattern, 'wave_a')
        assert hasattr(pattern, 'wave_b')
        assert hasattr(pattern, 'wave_c')
        assert pattern.wave_a.direction != pattern.wave_b.direction
        assert pattern.wave_b.direction != pattern.wave_c.direction
    
    @staticmethod
    def assert_fibonacci_levels_ordered(levels):
        """Assert that Fibonacci levels are properly ordered."""
        assert len(levels) > 0
        for i in range(1, len(levels)):
            # Levels should be in ascending order
            assert levels[i].level >= levels[i-1].level


@pytest.fixture
def trading_assertions():
    """Provide trading-specific assertions."""
    return TradingAssertions()
