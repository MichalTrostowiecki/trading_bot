"""
Unit tests for BaseCandleDetector class.

Tests cover:
- ATR calculation accuracy
- Consolidation candle identification  
- Base candle range detection
- Edge cases and error handling
- Performance benchmarks

Following TDD methodology - these tests define the expected behavior
before implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import time
import tracemalloc

# Import the classes we're testing (these will be implemented after tests)
try:
    from src.analysis.supply_demand.base_candle_detector import (
        BaseCandleDetector, 
        BaseCandleRange
    )
except ImportError:
    # Classes don't exist yet - we'll create them
    @dataclass
    class BaseCandleRange:
        """Placeholder for BaseCandleRange until implementation"""
        start_index: int
        end_index: int
        start_time: datetime
        end_time: datetime
        high: float
        low: float
        atr_at_creation: float
        candle_count: int
        consolidation_score: float
    
    class BaseCandleDetector:
        """Placeholder for BaseCandleDetector until implementation"""
        def __init__(self, **kwargs):
            self.consolidation_threshold = kwargs.get('consolidation_threshold', 0.5)
            self.min_base_candles = kwargs.get('min_base_candles', 2)
            self.max_base_candles = kwargs.get('max_base_candles', 10)
            self.body_size_threshold = kwargs.get('body_size_threshold', 0.3)
            self.atr_period = kwargs.get('atr_period', 14)
        
        def detect_base_candles(self, df, start_index=0, end_index=None):
            return []  # Placeholder
        
        def _calculate_atr(self, df):
            return pd.Series([0.001] * len(df))  # Placeholder
        
        def _is_consolidation_candle(self, candle, atr_value):
            return False  # Placeholder
        
        def _validate_base_range(self, candles):
            return 0.5  # Placeholder


class TestBaseCandleDetector:
    """
    Comprehensive unit tests for BaseCandleDetector class.
    
    Tests cover:
    - ATR calculation accuracy
    - Consolidation candle identification
    - Base candle range detection
    - Edge cases and error handling
    - Performance benchmarks
    """
    
    @pytest.fixture
    def detector(self):
        """Standard detector configuration for testing"""
        return BaseCandleDetector(
            consolidation_threshold=0.5,
            min_base_candles=2,
            max_base_candles=10,
            body_size_threshold=0.3,
            atr_period=14
        )
    
    @pytest.fixture
    def sample_consolidation_data(self):
        """
        Sample OHLC data with known consolidation pattern.
        
        Pattern: 5 small consolidation candles followed by breakout
        Expected: 1 base candle range detected
        """
        return pd.DataFrame({
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802, 1.0820],  # Small then big
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805, 1.0850],  # Tight then wide
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800, 1.0815],  # Consolidation then break
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801, 1.0845],  # Small bodies then big
            'volume': [1000, 1100, 1050, 1000, 950, 2500],             # Normal then spike
            'time': pd.date_range('2025-01-01 10:00', periods=6, freq='1min')
        })
    
    @pytest.fixture
    def known_atr_data(self):
        """
        OHLC data with known ATR calculation results.
        
        Designed to test ATR calculation accuracy against manual calculations.
        """
        # Create data where we can manually calculate expected ATR
        data = {
            'open': [1.0000, 1.0010, 1.0020, 1.0015, 1.0025] * 4,  # 20 bars
            'high': [1.0010, 1.0020, 1.0030, 1.0025, 1.0035] * 4,
            'low':  [0.9990, 1.0000, 1.0010, 1.0005, 1.0015] * 4,
            'close':[1.0005, 1.0015, 1.0025, 1.0020, 1.0030] * 4,
            'time': pd.date_range('2025-01-01 10:00', periods=20, freq='1min')
        }
        return pd.DataFrame(data)
    
    def test_detector_initialization(self, detector):
        """
        Test detector initializes with correct parameters.
        
        Success Criteria:
        - All parameters set correctly
        - Default values applied when not specified
        - Parameter validation works
        """
        assert detector.consolidation_threshold == 0.5
        assert detector.min_base_candles == 2
        assert detector.max_base_candles == 10
        assert detector.body_size_threshold == 0.3
        assert detector.atr_period == 14
    
    def test_atr_calculation_accuracy(self, detector, known_atr_data):
        """
        Test ATR calculation matches standard formula.
        
        Success Criteria:
        - ATR values match manual calculation
        - Handles first 14 bars correctly
        - No division by zero errors
        - Series length matches input data
        """
        atr_series = detector._calculate_atr(known_atr_data)
        
        # Basic validation
        assert len(atr_series) == len(known_atr_data), "ATR series length should match input data"
        assert not atr_series.isna().any(), "ATR series should not contain NaN values"
        assert (atr_series > 0).all(), "All ATR values should be positive"
        
        # Test ATR calculation formula
        # For our known data, True Range should be consistent
        # Manual calculation for first few bars after warmup period
        
        # Bar 0: TR = max(H-L, H-Cp, Cp-L) = max(0.002, 0.001, 0.001) = 0.002
        # Bar 1: TR = max(0.002, 0.001, 0.001) = 0.002
        # etc...
        
        # After 14-period warmup, ATR should be around 0.002 for our uniform data
        if len(atr_series) >= 14:
            atr_after_warmup = atr_series.iloc[14]
            expected_atr = 0.002  # Based on our uniform true range
            tolerance = 0.0005
            assert abs(atr_after_warmup - expected_atr) < tolerance, \
                f"ATR calculation incorrect: {atr_after_warmup} vs expected {expected_atr}"
    
    def test_atr_calculation_edge_cases(self, detector):
        """
        Test ATR calculation edge cases.
        
        Success Criteria:
        - Handles insufficient data gracefully
        - Zero volatility data doesn't break
        - Missing values handled correctly
        """
        # Test with insufficient data (< ATR period)
        small_data = pd.DataFrame({
            'open': [1.0000, 1.0010, 1.0020],
            'high': [1.0010, 1.0020, 1.0030],
            'low':  [0.9990, 1.0000, 1.0010],
            'close':[1.0005, 1.0015, 1.0025],
            'time': pd.date_range('2025-01-01 10:00', periods=3, freq='1min')
        })
        
        atr_series = detector._calculate_atr(small_data)
        assert len(atr_series) == len(small_data), "Should return ATR for all bars even with insufficient data"
        
        # Test with zero volatility
        flat_data = pd.DataFrame({
            'open': [1.0000] * 20,
            'high': [1.0000] * 20,
            'low':  [1.0000] * 20,
            'close':[1.0000] * 20,
            'time': pd.date_range('2025-01-01 10:00', periods=20, freq='1min')
        })
        
        atr_series = detector._calculate_atr(flat_data)
        assert (atr_series >= 0).all(), "Zero volatility should produce zero ATR, not negative"
    
    def test_consolidation_candle_identification(self, detector, sample_consolidation_data):
        """
        Test individual candle consolidation classification.
        
        Success Criteria:
        - Small candles correctly identified as consolidation
        - Large candles correctly rejected
        - Body size threshold properly applied
        - ATR threshold properly applied
        """
        atr_values = detector._calculate_atr(sample_consolidation_data)
        
        # Test consolidation candles (indices 0-4)
        # These should be small relative to ATR
        for i in range(5):
            candle = sample_consolidation_data.iloc[i]
            atr_value = atr_values.iloc[i] if i < len(atr_values) else 0.001
            
            # For our test data, set a minimum ATR to ensure meaningful comparison
            atr_value = max(atr_value, 0.001)
            
            is_consolidation = detector._is_consolidation_candle(candle, atr_value)
            
            # Calculate actual candle metrics for debugging
            candle_range = candle['high'] - candle['low']
            candle_body = abs(candle['close'] - candle['open'])
            
            # With our test data design, first 5 candles should be consolidation
            # This test will fail initially - implementation needs to make it pass
            expected_is_consolidation = True  # Based on test data design
            
            if expected_is_consolidation:
                assert is_consolidation, \
                    f"Candle {i} should be consolidation. Range: {candle_range:.5f}, " \
                    f"Body: {candle_body:.5f}, ATR: {atr_value:.5f}"
        
        # Test breakout candle (index 5)
        # This should be large relative to ATR
        if len(sample_consolidation_data) > 5:
            breakout_candle = sample_consolidation_data.iloc[5]
            atr_value = max(atr_values.iloc[5] if 5 < len(atr_values) else 0.001, 0.001)
            
            is_consolidation = detector._is_consolidation_candle(breakout_candle, atr_value)
            
            # Breakout candle should NOT be consolidation
            assert not is_consolidation, \
                f"Breakout candle should not be consolidation. " \
                f"Range: {breakout_candle['high'] - breakout_candle['low']:.5f}, " \
                f"ATR: {atr_value:.5f}"
    
    def test_base_candle_range_detection(self, detector, sample_consolidation_data):
        """
        Test complete base candle range detection.
        
        Success Criteria:
        - Detects exactly 1 base candle range
        - Range includes candles 0-4 (5 candles)
        - Excludes breakout candle (index 5)
        - Range boundaries are correct
        - Consolidation score calculated
        """
        ranges = detector.detect_base_candles(sample_consolidation_data)
        
        # This test will fail initially - implementation needs to detect the range
        assert len(ranges) == 1, f"Should detect exactly one base candle range, got {len(ranges)}"
        
        base_range = ranges[0]
        
        # Validate range properties
        assert base_range.start_index == 0, f"Range should start at index 0, got {base_range.start_index}"
        assert base_range.end_index == 4, f"Range should end at index 4, got {base_range.end_index}"
        assert base_range.candle_count == 5, f"Range should have 5 candles, got {base_range.candle_count}"
        
        # Validate time boundaries
        expected_start_time = sample_consolidation_data.iloc[0]['time']
        expected_end_time = sample_consolidation_data.iloc[4]['time']
        assert base_range.start_time == expected_start_time
        assert base_range.end_time == expected_end_time
        
        # Validate price boundaries
        expected_high = sample_consolidation_data.iloc[0:5]['high'].max()  # 1.0810
        expected_low = sample_consolidation_data.iloc[0:5]['low'].min()    # 1.0795
        assert abs(base_range.high - expected_high) < 0.00001
        assert abs(base_range.low - expected_low) < 0.00001
        
        # Validate consolidation score
        assert 0.0 <= base_range.consolidation_score <= 1.0, \
            f"Consolidation score should be 0-1, got {base_range.consolidation_score}"
        assert base_range.consolidation_score > 0.5, \
            f"Good consolidation should score >0.5, got {base_range.consolidation_score}"
    
    def test_edge_case_insufficient_data(self, detector):
        """
        Test behavior with insufficient data.
        
        Success Criteria:
        - Handles data with <14 bars (ATR requirement)
        - Returns empty list for insufficient data
        - No exceptions thrown
        """
        insufficient_data = pd.DataFrame({
            'open': [1.0800] * 5,
            'high': [1.0810] * 5,
            'low': [1.0790] * 5,
            'close': [1.0805] * 5,
            'time': pd.date_range('2025-01-01 10:00', periods=5, freq='1min')
        })
        
        # Should not raise exception
        ranges = detector.detect_base_candles(insufficient_data)
        
        # Should return empty list or handle gracefully
        assert isinstance(ranges, list), "Should return list even with insufficient data"
        # Note: specific behavior (empty vs partial results) depends on implementation choice
    
    def test_edge_case_no_consolidation(self, detector):
        """
        Test behavior when no consolidation patterns exist.
        
        Success Criteria:
        - Returns empty list when all candles are large
        - No false positive detections
        """
        # Create trending data with large candles only
        trending_data = pd.DataFrame({
            'open': [1.0000, 1.0050, 1.0100, 1.0150, 1.0200, 1.0250, 1.0300, 1.0350] * 3,
            'high': [1.0060, 1.0110, 1.0160, 1.0210, 1.0260, 1.0310, 1.0360, 1.0410] * 3,
            'low':  [0.9980, 1.0030, 1.0080, 1.0130, 1.0180, 1.0230, 1.0280, 1.0330] * 3,
            'close':[1.0050, 1.0100, 1.0150, 1.0200, 1.0250, 1.0300, 1.0350, 1.0400] * 3,
            'time': pd.date_range('2025-01-01 10:00', periods=24, freq='1min')
        })
        
        ranges = detector.detect_base_candles(trending_data)
        
        # Should not detect any consolidation in strong trending data
        assert ranges == [], f"Should return empty list for trending data, got {len(ranges)} ranges"
    
    def test_edge_case_single_consolidation_candle(self, detector):
        """
        Test behavior with only 1 consolidation candle.
        
        Success Criteria:
        - Does not create base range (min_base_candles = 2)
        - Returns empty list
        """
        # Create data with only one small candle among large ones
        single_consolidation_data = pd.DataFrame({
            'open': [1.0000, 1.0100, 1.0102, 1.0200, 1.0300] * 3,  # One small move at index 2
            'high': [1.0060, 1.0160, 1.0103, 1.0260, 1.0360] * 3,
            'low':  [0.9980, 1.0080, 1.0101, 1.0180, 1.0280] * 3,
            'close':[1.0050, 1.0150, 1.0102, 1.0250, 1.0350] * 3,
            'time': pd.date_range('2025-01-01 10:00', periods=15, freq='1min')
        })
        
        ranges = detector.detect_base_candles(single_consolidation_data)
        
        # Should not detect range with single consolidation candle
        assert ranges == [], \
            f"Should not detect range with single consolidation candle, got {len(ranges)} ranges"
    
    def test_multiple_consolidation_ranges(self, detector):
        """
        Test detection of multiple separate consolidation ranges.
        
        Success Criteria:
        - Detects multiple ranges when they exist
        - Ranges don't overlap
        - Each range meets minimum criteria
        """
        # Create data with two separate consolidation periods
        multiple_ranges_data = pd.DataFrame({
            # First consolidation (indices 0-2)
            'open': [1.0800, 1.0805, 1.0803,
                    # Breakout (index 3)
                    1.0820,
                    # Second consolidation (indices 4-6)  
                    1.0840, 1.0845, 1.0843,
                    # Final breakout (index 7)
                    1.0860],
            'high': [1.0810, 1.0808, 1.0806,
                    1.0850,
                    1.0850, 1.0848, 1.0846,
                    1.0890],
            'low':  [1.0795, 1.0802, 1.0801,
                    1.0815,
                    1.0835, 1.0842, 1.0841,
                    1.0855],
            'close':[1.0805, 1.0803, 1.0804,
                    1.0845,
                    1.0845, 1.0843, 1.0844,
                    1.0885],
            'time': pd.date_range('2025-01-01 10:00', periods=8, freq='1min')
        })
        
        ranges = detector.detect_base_candles(multiple_ranges_data)
        
        # Should detect both consolidation ranges
        assert len(ranges) >= 1, f"Should detect at least one consolidation range, got {len(ranges)}"
        
        # Validate ranges don't overlap
        for i, range1 in enumerate(ranges):
            for j, range2 in enumerate(ranges[i+1:], i+1):
                assert range1.end_index < range2.start_index or range2.end_index < range1.start_index, \
                    f"Ranges {i} and {j} should not overlap"
    
    def test_performance_benchmark(self, detector):
        """
        Test performance meets <20ms requirement.
        
        Success Criteria:
        - Processes 1000 bars in <20ms
        - Memory usage remains stable
        - No memory leaks detected
        """
        # Create large dataset for performance testing
        large_dataset = self._create_large_dataset(1000)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Warm up (exclude from timing)
        detector.detect_base_candles(large_dataset.head(100))
        
        # Actual performance test
        start_time = time.perf_counter()
        
        ranges = detector.detect_base_candles(large_dataset)
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        assert duration_ms < 20, f"Performance test failed: {duration_ms:.2f}ms > 20ms target"
        assert memory_mb < 10, f"Memory usage too high: {memory_mb:.1f}MB > 10MB limit"
        
        # Verify algorithm still works correctly under load
        assert isinstance(ranges, list), "Should return list even with large dataset"
        # Note: Exact count depends on test data characteristics
    
    def test_configuration_validation(self):
        """
        Test detector configuration validation.
        
        Success Criteria:
        - Rejects invalid threshold values
        - Validates min/max base candle counts
        - Proper error messages for invalid config
        """
        # Test invalid consolidation threshold
        with pytest.raises((ValueError, AssertionError)):
            BaseCandleDetector(consolidation_threshold=-0.1)  # Negative threshold
        
        with pytest.raises((ValueError, AssertionError)):
            BaseCandleDetector(consolidation_threshold=2.0)   # Too high threshold
        
        # Test invalid base candle counts
        with pytest.raises((ValueError, AssertionError)):
            BaseCandleDetector(min_base_candles=0)  # Zero minimum
        
        with pytest.raises((ValueError, AssertionError)):
            BaseCandleDetector(min_base_candles=15, max_base_candles=10)  # Min > Max
        
        # Test invalid ATR period
        with pytest.raises((ValueError, AssertionError)):
            BaseCandleDetector(atr_period=0)  # Zero ATR period
    
    def test_base_range_validation(self, detector):
        """
        Test base candle range validation logic.
        
        Success Criteria:
        - Validates range quality correctly
        - Scores based on consolidation tightness
        - Rejects poor quality ranges
        """
        # Create test data for range validation
        tight_consolidation = pd.DataFrame({
            'open': [1.0800, 1.0801, 1.0802],
            'high': [1.0802, 1.0803, 1.0804],  # Very tight range
            'low':  [1.0799, 1.0800, 1.0801],
            'close':[1.0801, 1.0802, 1.0801],
            'time': pd.date_range('2025-01-01 10:00', periods=3, freq='1min')
        })
        
        loose_consolidation = pd.DataFrame({
            'open': [1.0800, 1.0820, 1.0790],
            'high': [1.0850, 1.0860, 1.0840],  # Wide range
            'low':  [1.0750, 1.0770, 1.0740],
            'close':[1.0820, 1.0790, 1.0820],
            'time': pd.date_range('2025-01-01 10:00', periods=3, freq='1min')
        })
        
        tight_score = detector._validate_base_range(tight_consolidation)
        loose_score = detector._validate_base_range(loose_consolidation)
        
        # Tight consolidation should score higher
        assert 0.0 <= tight_score <= 1.0, f"Tight score should be 0-1, got {tight_score}"
        assert 0.0 <= loose_score <= 1.0, f"Loose score should be 0-1, got {loose_score}"
        assert tight_score > loose_score, \
            f"Tight consolidation should score higher: {tight_score} vs {loose_score}"
    
    def test_data_validation(self, detector):
        """
        Test input data validation.
        
        Success Criteria:
        - Validates required columns exist
        - Handles missing data appropriately
        - Validates data types
        """
        # Test missing required columns
        invalid_data = pd.DataFrame({
            'open': [1.0800, 1.0805],
            'high': [1.0810, 1.0808],
            # Missing 'low' and 'close'
            'time': pd.date_range('2025-01-01 10:00', periods=2, freq='1min')
        })
        
        with pytest.raises((KeyError, ValueError)):
            detector.detect_base_candles(invalid_data)
        
        # Test empty dataframe
        empty_data = pd.DataFrame()
        
        with pytest.raises((ValueError, IndexError)):
            detector.detect_base_candles(empty_data)
    
    # Helper methods for test data creation
    def _create_large_dataset(self, size: int) -> pd.DataFrame:
        """Create large dataset for performance testing"""
        np.random.seed(42)  # Reproducible results
        
        # Generate realistic OHLC data
        base_price = 1.0800
        returns = np.random.normal(0, 0.0001, size)  # Small random returns
        
        prices = [base_price]
        for ret in returns[:-1]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLC from prices with some noise
        data = []
        for i, price in enumerate(prices):
            noise = np.random.normal(0, 0.00005)
            open_price = price
            high_price = price + abs(noise) + 0.00002
            low_price = price - abs(noise) - 0.00002
            close_price = price + noise
            
            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': np.random.randint(800, 1200),
                'time': datetime(2025, 1, 1, 10, 0) + timedelta(minutes=i)
            })
        
        return pd.DataFrame(data)


# Test fixtures and utilities for other test files
@pytest.fixture
def base_candle_detector():
    """Standard BaseCandleDetector for use in other test files"""
    return BaseCandleDetector(
        consolidation_threshold=0.5,
        min_base_candles=2,
        max_base_candles=10,
        body_size_threshold=0.3,
        atr_period=14
    )


@pytest.fixture
def sample_base_candle_range():
    """Sample BaseCandleRange for testing"""
    return BaseCandleRange(
        start_index=0,
        end_index=4,
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 10, 4),
        high=1.0810,
        low=1.0795,
        atr_at_creation=0.0010,
        candle_count=5,
        consolidation_score=0.8
    )


# Performance benchmarking utilities
def benchmark_base_candle_detection():
    """Standalone performance benchmark for CI/CD"""
    detector = BaseCandleDetector()
    
    # Create test datasets of various sizes
    sizes = [100, 500, 1000]
    
    for size in sizes:
        # Create test data
        data = TestBaseCandleDetector()._create_large_dataset(size)
        
        # Benchmark
        start_time = time.perf_counter()
        ranges = detector.detect_base_candles(data)
        duration = (time.perf_counter() - start_time) * 1000
        
        print(f"BaseCandleDetector {size} bars: {duration:.2f}ms")
        
        # Assert performance targets
        if size == 100:
            assert duration < 5, f"100 bars: {duration:.2f}ms > 5ms"
        elif size == 500:
            assert duration < 15, f"500 bars: {duration:.2f}ms > 15ms"
        elif size == 1000:
            assert duration < 20, f"1000 bars: {duration:.2f}ms > 20ms"


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_base_candle_detection()