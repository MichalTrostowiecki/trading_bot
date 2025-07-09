#!/usr/bin/env python3
"""
Unit Tests for Strategy Edge Cases
Tests edge cases, error conditions, and boundary scenarios.
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

from src.strategy.fibonacci_strategy import FibonacciStrategy


class TestStrategyEdgeCases:
    """Test edge cases in strategy processing."""
    
    def test_empty_data_handling(self):
        """Test strategy behavior with empty or minimal data."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = strategy.process_bar(empty_df, 0)
        
        # Should not crash and return empty result
        assert isinstance(result, dict)
        assert result.get('new_fractal') is None
        assert result.get('new_swing') is None
    
    def test_insufficient_data_for_fractals(self):
        """Test behavior when there's insufficient data for fractal detection."""
        strategy = FibonacciStrategy(
            fractal_period=5,  # Requires 5 bars minimum
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create data with only 3 bars (insufficient for 5-period fractals)
        dates = pd.date_range(start='2024-01-01', periods=3, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [1.0000, 1.0010, 1.0020],
            'high': [1.0005, 1.0015, 1.0025],
            'low': [0.9995, 1.0005, 1.0015],
            'close': [1.0002, 1.0012, 1.0022],
            'volume': [100, 100, 100]
        }).set_index('timestamp')
        
        # Process each bar
        for i in range(len(data)):
            result = strategy.process_bar(data, i)
            # Should not detect fractals with insufficient data
            assert result.get('new_fractal') is None
    
    def test_flat_market_conditions(self):
        """Test strategy behavior in flat/sideways market conditions."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create flat market data (no significant moves)
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
        base_price = 1.0000
        
        data = []
        for i, date in enumerate(dates):
            # Very small random movements around base price
            noise = np.random.normal(0, 0.0001)
            price = base_price + noise
            
            data.append({
                'timestamp': date,
                'open': price,
                'high': price + 0.0001,
                'low': price - 0.0001,
                'close': price,
                'volume': 100
            })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Process all bars
        fractal_count = 0
        swing_count = 0
        
        for i in range(len(df)):
            result = strategy.process_bar(df, i)
            if result.get('new_fractal'):
                fractal_count += 1
            if result.get('new_swing'):
                swing_count += 1
        
        # In flat conditions, should detect few or no significant swings
        assert swing_count <= fractal_count  # Can't have more swings than fractals
    
    def test_extreme_volatility(self):
        """Test strategy behavior with extreme price volatility."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create extremely volatile data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='1H')
        
        data = []
        for i, date in enumerate(dates):
            # Extreme price swings
            if i % 2 == 0:
                price = 1.0000 + (i * 0.01)  # Big up moves
            else:
                price = 1.0000 - (i * 0.005)  # Big down moves
            
            data.append({
                'timestamp': date,
                'open': price,
                'high': price + 0.005,
                'low': price - 0.005,
                'close': price,
                'volume': 100
            })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Process all bars - should handle extreme volatility gracefully
        for i in range(len(df)):
            result = strategy.process_bar(df, i)
            # Should not crash or produce invalid results
            assert isinstance(result, dict)
    
    def test_duplicate_fractal_handling(self):
        """Test handling of duplicate or very close fractals."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create data with potential duplicate fractals
        dates = pd.date_range(start='2024-01-01', periods=20, freq='1H')
        
        data = []
        for i, date in enumerate(dates):
            # Create pattern that might generate duplicate fractals
            if i in [5, 6]:  # Two consecutive potential highs
                price = 1.0100
            elif i in [10, 11]:  # Two consecutive potential lows
                price = 0.9900
            else:
                price = 1.0000
            
            data.append({
                'timestamp': date,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005,
                'close': price,
                'volume': 100
            })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Track fractal timestamps to check for duplicates
        fractal_timestamps = []
        
        for i in range(len(df)):
            result = strategy.process_bar(df, i)
            if result.get('new_fractal'):
                timestamp = result['new_fractal']['timestamp']
                assert timestamp not in fractal_timestamps, "Duplicate fractal detected"
                fractal_timestamps.append(timestamp)
    
    def test_swing_size_filtering(self):
        """Test that swings below minimum size are filtered out."""
        min_swing_points = 0.0050  # 50 pips minimum
        
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=min_swing_points,
            lookback_candles=50
        )
        
        # Create data with both large and small swings
        dates = pd.date_range(start='2024-01-01', periods=30, freq='1H')
        
        data = []
        for i, date in enumerate(dates):
            if i < 10:
                price = 1.0000 + (i * 0.001)  # Small moves (10 pips total)
            elif i < 20:
                price = 1.0100 + (i * 0.002)  # Larger moves (200 pips total)
            else:
                price = 1.0200 - ((i-20) * 0.001)  # Small moves down
            
            data.append({
                'timestamp': date,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005,
                'close': price,
                'volume': 100
            })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Process all bars and check swing sizes
        for i in range(len(df)):
            result = strategy.process_bar(df, i)
            if result.get('new_swing'):
                swing_points = result['new_swing']['points']
                # All detected swings should meet minimum size requirement
                assert swing_points >= min_swing_points, f"Swing too small: {swing_points}"
    
    def test_lookback_window_limits(self):
        """Test that lookback window limits are respected."""
        lookback_candles = 20
        
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=lookback_candles
        )
        
        # Create data longer than lookback window
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
        
        data = []
        for i, date in enumerate(dates):
            price = 1.0000 + (i * 0.0001)
            data.append({
                'timestamp': date,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005,
                'close': price,
                'volume': 100
            })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Process all bars
        for i in range(len(df)):
            strategy.process_bar(df, i)
        
        # Check that strategy doesn't keep unlimited history
        # (This depends on implementation - adjust based on actual behavior)
        assert len(strategy.fractals) <= lookback_candles * 2  # Reasonable limit
    
    def test_invalid_data_handling(self):
        """Test handling of invalid or corrupted data."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create data with some invalid values
        dates = pd.date_range(start='2024-01-01', periods=10, freq='1H')
        
        data = []
        for i, date in enumerate(dates):
            if i == 5:
                # Invalid data point
                data.append({
                    'timestamp': date,
                    'open': np.nan,
                    'high': np.inf,
                    'low': -np.inf,
                    'close': None,
                    'volume': -100
                })
            else:
                # Valid data
                price = 1.0000 + (i * 0.0001)
                data.append({
                    'timestamp': date,
                    'open': price,
                    'high': price + 0.0005,
                    'low': price - 0.0005,
                    'close': price,
                    'volume': 100
                })
        
        df = pd.DataFrame(data).set_index('timestamp')
        
        # Process all bars - should handle invalid data gracefully
        for i in range(len(df)):
            try:
                result = strategy.process_bar(df, i)
                assert isinstance(result, dict)
            except Exception as e:
                # If it raises an exception, it should be a reasonable one
                assert "invalid" in str(e).lower() or "nan" in str(e).lower()


class TestABCPatternEdgeCases:
    """Test edge cases in ABC pattern detection."""
    
    def test_abc_with_insufficient_fractals(self):
        """Test ABC detection when there are insufficient fractals."""
        strategy = FibonacciStrategy(
            fractal_period=5,
            min_swing_points=0.001,
            lookback_candles=50
        )
        
        # Create minimal data
        dates = pd.date_range(start='2024-01-01', periods=10, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [1.0000] * 10,
            'high': [1.0005] * 10,
            'low': [0.9995] * 10,
            'close': [1.0000] * 10,
            'volume': [100] * 10
        }).set_index('timestamp')
        
        # Process all bars
        for i in range(len(data)):
            result = strategy.process_bar(data, i)
        
        # Should not detect ABC patterns with insufficient fractals
        assert len(strategy.abc_patterns) == 0
    
    def test_abc_fibonacci_validation(self):
        """Test ABC pattern Fibonacci ratio validation."""
        # This would test the specific Fibonacci ratios used in ABC validation
        # Implementation depends on your specific ABC validation logic
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
