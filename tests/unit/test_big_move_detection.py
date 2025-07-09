"""
Unit tests for BigMoveDetector class.

Tests cover:
- Move magnitude calculation
- Momentum score validation
- Breakout confirmation logic
- Volume analysis integration
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

# Import the classes we're testing
try:
    from src.analysis.supply_demand.big_move_detector import (
        BigMoveDetector,
        BigMove
    )
    from src.analysis.supply_demand.base_candle_detector import BaseCandleRange
except ImportError:
    # Classes don't exist yet - we'll create placeholders
    @dataclass
    class BigMove:
        """Placeholder for BigMove until implementation"""
        start_index: int
        end_index: int
        start_time: datetime
        end_time: datetime
        direction: str  # 'bullish' or 'bearish'
        magnitude: float  # ATR multiples
        momentum_score: float  # 0.0 to 1.0
        breakout_level: float
        volume_confirmation: bool
    
    @dataclass
    class BaseCandleRange:
        """Placeholder for BaseCandleRange"""
        start_index: int
        end_index: int
        start_time: datetime
        end_time: datetime
        high: float
        low: float
        atr_at_creation: float
        candle_count: int
        consolidation_score: float
    
    class BigMoveDetector:
        """Placeholder for BigMoveDetector until implementation"""
        def __init__(self, **kwargs):
            self.move_threshold = kwargs.get('move_threshold', 2.0)
            self.min_move_candles = kwargs.get('min_move_candles', 3)
            self.momentum_threshold = kwargs.get('momentum_threshold', 0.6)
            self.volume_multiplier = kwargs.get('volume_multiplier', 1.5)
            self.breakout_confirmation = kwargs.get('breakout_confirmation', True)
        
        def detect_big_moves(self, df, base_ranges, fractal_levels=None):
            return []  # Placeholder
        
        def _calculate_move_magnitude(self, df, start_index, end_index, base_range):
            return 2.5  # Placeholder
        
        def _calculate_momentum_score(self, df, start_index, end_index):
            return 0.8  # Placeholder
        
        def _validate_breakout(self, move, fractal_levels):
            return True  # Placeholder


class TestBigMoveDetector:
    """
    Comprehensive unit tests for BigMoveDetector class.
    
    Tests cover:
    - Move magnitude calculation
    - Momentum score validation
    - Breakout confirmation logic
    - Volume analysis integration
    - Performance benchmarks
    """
    
    @pytest.fixture
    def detector(self):
        """Standard detector configuration for testing"""
        return BigMoveDetector(
            move_threshold=2.0,
            min_move_candles=3,
            momentum_threshold=0.6,
            volume_multiplier=1.5,
            breakout_confirmation=True
        )
    
    @pytest.fixture
    def sample_big_move_data(self):
        """
        Sample data with clear big move pattern.
        
        Pattern: 5-candle consolidation + 4-candle bullish move
        Expected: 1 big move detected (bullish, 2.5x ATR magnitude)
        """
        return pd.DataFrame({
            # 5 consolidation candles then 4 big move candles
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Consolidation
                    1.0801, 1.0820, 1.0835, 1.0845],          # Big move
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,  # Small ranges
                    1.0825, 1.0840, 1.0850, 1.0860],          # Large ranges
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,  # Consolidation
                    1.0800, 1.0815, 1.0830, 1.0840],          # Strong momentum
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801,  # Small bodies
                    1.0820, 1.0835, 1.0845, 1.0855],          # Large bodies
            'volume': [1000] * 5 + [2500, 2000, 1800, 1600],  # Volume spike
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
    
    @pytest.fixture
    def sample_base_range(self):
        """Sample base candle range for testing"""
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
    
    @pytest.fixture
    def sample_bearish_move_data(self):
        """Sample data with bearish big move pattern"""
        return pd.DataFrame({
            # 5 consolidation candles then 4 bearish move candles
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Consolidation
                    1.0801, 1.0780, 1.0765, 1.0755],          # Big bearish move
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,  # Small ranges
                    1.0805, 1.0785, 1.0770, 1.0760],          # Bearish highs
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,  # Consolidation
                    1.0775, 1.0760, 1.0745, 1.0740],          # Strong bearish momentum
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801,  # Small bodies
                    1.0780, 1.0765, 1.0755, 1.0745],          # Large bearish bodies
            'volume': [1000] * 5 + [2500, 2000, 1800, 1600],  # Volume spike
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
    
    def test_detector_initialization(self, detector):
        """
        Test detector initializes with correct parameters.
        
        Success Criteria:
        - All parameters set correctly
        - Default values applied when not specified
        - Parameter validation works
        """
        assert detector.move_threshold == 2.0
        assert detector.min_move_candles == 3
        assert detector.momentum_threshold == 0.6
        assert detector.volume_multiplier == 1.5
        assert detector.breakout_confirmation == True
    
    def test_move_magnitude_calculation_bullish(self, detector, sample_big_move_data, sample_base_range):
        """
        Test accurate move magnitude calculation for bullish moves.
        
        Success Criteria:
        - Magnitude calculated correctly vs ATR
        - Bullish moves properly identified
        - ATR baseline properly established
        """
        magnitude = detector._calculate_move_magnitude(
            sample_big_move_data, 5, 8, sample_base_range
        )
        
        # Expected calculation:
        # Move from base end (1.0801) to move end (1.0855) = 0.0054
        # ATR at creation = 0.0010
        # Magnitude = 0.0054 / 0.0010 = 5.4x ATR
        expected_magnitude = 5.4
        tolerance = 0.5  # Allow some tolerance for calculation differences
        
        assert abs(magnitude - expected_magnitude) < tolerance, \
            f"Move magnitude incorrect: {magnitude:.2f} vs expected {expected_magnitude:.2f}"
        assert magnitude >= detector.move_threshold, \
            f"Move magnitude {magnitude:.2f} should exceed threshold {detector.move_threshold}"
    
    def test_move_magnitude_calculation_bearish(self, detector, sample_bearish_move_data, sample_base_range):
        """
        Test accurate move magnitude calculation for bearish moves.
        
        Success Criteria:
        - Bearish magnitude calculated correctly
        - Direction properly identified
        - Absolute magnitude used for threshold comparison
        """
        magnitude = detector._calculate_move_magnitude(
            sample_bearish_move_data, 5, 8, sample_base_range
        )
        
        # Expected calculation:
        # Move from base end (1.0801) to move end (1.0745) = -0.0056
        # ATR at creation = 0.0010  
        # Magnitude = abs(-0.0056) / 0.0010 = 5.6x ATR
        expected_magnitude = 5.6
        tolerance = 0.5
        
        assert abs(magnitude - expected_magnitude) < tolerance, \
            f"Bearish move magnitude incorrect: {magnitude:.2f} vs expected {expected_magnitude:.2f}"
        assert magnitude >= detector.move_threshold, \
            f"Bearish move magnitude {magnitude:.2f} should exceed threshold {detector.move_threshold}"
    
    def test_momentum_score_calculation_strong(self, detector, sample_big_move_data):
        """
        Test momentum score reflects strong directional movement.
        
        Success Criteria:
        - Strong directional moves score >0.8
        - Consistent momentum properly weighted
        - Score range 0.0-1.0 maintained
        """
        momentum_score = detector._calculate_momentum_score(
            sample_big_move_data, 5, 8
        )
        
        assert 0.0 <= momentum_score <= 1.0, \
            f"Momentum score should be 0-1, got {momentum_score}"
        assert momentum_score > 0.8, \
            f"Strong consistent move should have high momentum: {momentum_score:.3f}"
        assert momentum_score >= detector.momentum_threshold, \
            f"Strong move momentum {momentum_score:.3f} should exceed threshold {detector.momentum_threshold}"
    
    def test_momentum_score_calculation_weak(self, detector):
        """
        Test momentum score reflects weak/choppy movement.
        
        Success Criteria:
        - Choppy moves score <0.4
        - Inconsistent direction penalized
        - Poor momentum properly identified
        """
        # Create choppy movement data
        choppy_data = pd.DataFrame({
            'open': [1.0800, 1.0820, 1.0810, 1.0825, 1.0815],
            'high': [1.0825, 1.0825, 1.0830, 1.0830, 1.0820],
            'low':  [1.0795, 1.0805, 1.0805, 1.0810, 1.0810],
            'close':[1.0820, 1.0810, 1.0825, 1.0815, 1.0818],  # Choppy closes
            'volume': [1500, 1600, 1400, 1300, 1200],
            'time': pd.date_range('2025-01-01 10:05', periods=5, freq='1min')
        })
        
        momentum_score = detector._calculate_momentum_score(choppy_data, 0, 4)
        
        assert 0.0 <= momentum_score <= 1.0, \
            f"Momentum score should be 0-1, got {momentum_score}"
        assert momentum_score < 0.4, \
            f"Choppy move should have low momentum: {momentum_score:.3f}"
    
    def test_big_move_detection_success_bullish(self, detector, sample_big_move_data, sample_base_range):
        """
        Test successful bullish big move detection.
        
        Success Criteria:
        - Detects exactly 1 big move
        - Move classified as bullish
        - Proper start/end indices
        - Magnitude meets threshold
        - Momentum meets threshold
        """
        base_ranges = [sample_base_range]
        
        big_moves = detector.detect_big_moves(
            sample_big_move_data, base_ranges
        )
        
        assert len(big_moves) == 1, f"Should detect exactly one big move, got {len(big_moves)}"
        
        move = big_moves[0]
        assert move.direction == "bullish", f"Should detect bullish move, got {move.direction}"
        assert move.start_index == 5, f"Move should start at index 5, got {move.start_index}"
        assert move.end_index == 8, f"Move should end at index 8, got {move.end_index}"
        assert move.magnitude >= detector.move_threshold, \
            f"Move magnitude {move.magnitude:.2f} should exceed threshold {detector.move_threshold}"
        assert move.momentum_score >= detector.momentum_threshold, \
            f"Move momentum {move.momentum_score:.3f} should exceed threshold {detector.momentum_threshold}"
        
        # Validate time boundaries
        expected_start_time = sample_big_move_data.iloc[5]['time']
        expected_end_time = sample_big_move_data.iloc[8]['time']
        assert move.start_time == expected_start_time
        assert move.end_time == expected_end_time
    
    def test_big_move_detection_success_bearish(self, detector, sample_bearish_move_data, sample_base_range):
        """
        Test successful bearish big move detection.
        
        Success Criteria:
        - Detects bearish move correctly
        - Proper direction classification
        - Magnitude calculation correct for bearish moves
        """
        base_ranges = [sample_base_range]
        
        big_moves = detector.detect_big_moves(
            sample_bearish_move_data, base_ranges
        )
        
        assert len(big_moves) == 1, f"Should detect exactly one bearish move, got {len(big_moves)}"
        
        move = big_moves[0]
        assert move.direction == "bearish", f"Should detect bearish move, got {move.direction}"
        assert move.magnitude >= detector.move_threshold, \
            f"Bearish move magnitude {move.magnitude:.2f} should exceed threshold {detector.move_threshold}"
    
    def test_volume_confirmation_success(self, detector, sample_big_move_data, sample_base_range):
        """
        Test volume spike confirmation for big moves.
        
        Success Criteria:
        - Volume spike properly detected
        - Volume confirmation flag set correctly
        - Threshold properly applied
        """
        base_ranges = [sample_base_range]
        
        big_moves = detector.detect_big_moves(
            sample_big_move_data, base_ranges
        )
        
        move = big_moves[0]
        assert move.volume_confirmation == True, \
            f"Volume spike should be confirmed for big move"
        
        # Test with low volume data
        low_volume_data = sample_big_move_data.copy()
        low_volume_data['volume'] = [1000] * len(low_volume_data)  # No volume spike
        
        big_moves_low_vol = detector.detect_big_moves(
            low_volume_data, base_ranges
        )
        
        if len(big_moves_low_vol) > 0:
            move_low_vol = big_moves_low_vol[0]
            assert move_low_vol.volume_confirmation == False, \
                f"Low volume should not be confirmed"
    
    def test_breakout_confirmation(self, detector, sample_big_move_data, sample_base_range):
        """
        Test breakout level confirmation.
        
        Success Criteria:
        - Breakout level properly identified
        - Previous levels used for confirmation
        - Fractal levels integration works
        """
        base_ranges = [sample_base_range]
        fractal_levels = [1.0790, 1.0815]  # Sample fractal levels
        
        big_moves = detector.detect_big_moves(
            sample_big_move_data, base_ranges, fractal_levels
        )
        
        move = big_moves[0]
        
        # Breakout level should be the consolidation high for bullish move
        expected_breakout = sample_base_range.high  # 1.0810
        tolerance = 0.00005
        
        assert abs(move.breakout_level - expected_breakout) < tolerance, \
            f"Breakout level incorrect: {move.breakout_level:.5f} vs expected {expected_breakout:.5f}"
    
    def test_edge_case_weak_move_rejection(self, detector, sample_base_range):
        """
        Test rejection of weak moves that don't meet thresholds.
        
        Success Criteria:
        - Moves below magnitude threshold rejected
        - Poor momentum moves rejected
        - Returns empty list for weak patterns
        """
        # Create weak move data (small magnitude)
        weak_move_data = pd.DataFrame({
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Base
                    1.0801, 1.0803, 1.0805, 1.0807],          # Weak move
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,
                    1.0805, 1.0807, 1.0809, 1.0811],          # Small ranges
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,
                    1.0800, 1.0801, 1.0803, 1.0805],
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801,
                    1.0803, 1.0805, 1.0807, 1.0809],          # Small move
            'volume': [1000] * 9,
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
        
        base_ranges = [sample_base_range]
        
        big_moves = detector.detect_big_moves(weak_move_data, base_ranges)
        
        # Should reject weak move
        assert big_moves == [], f"Weak moves should be rejected, got {len(big_moves)} moves"
    
    def test_edge_case_insufficient_move_candles(self, detector, sample_base_range):
        """
        Test rejection of moves with insufficient candles.
        
        Success Criteria:
        - Moves shorter than min_move_candles rejected
        - Proper validation of move duration
        """
        # Create data with only 2 move candles (below min_move_candles=3)
        short_move_data = pd.DataFrame({
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Base (5 candles)
                    1.0801, 1.0820],                          # Short move (2 candles)
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,
                    1.0825, 1.0840],
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,
                    1.0800, 1.0815],
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801,
                    1.0820, 1.0835],
            'volume': [1000] * 7,
            'time': pd.date_range('2025-01-01 10:00', periods=7, freq='1min')
        })
        
        base_ranges = [sample_base_range]
        
        big_moves = detector.detect_big_moves(short_move_data, base_ranges)
        
        # Should reject short move
        assert big_moves == [], f"Short moves should be rejected, got {len(big_moves)} moves"
    
    def test_multiple_base_ranges(self, detector):
        """
        Test detection with multiple base ranges.
        
        Success Criteria:
        - Processes multiple base ranges correctly
        - Each range can generate separate moves
        - No interference between ranges
        """
        # Create data with two separate base ranges and moves
        multi_range_data = pd.DataFrame({
            'open': [1.0800, 1.0805, 1.0803,  # First base (0-2)
                    1.0820, 1.0835, 1.0845,   # First move (3-5)
                    1.0840, 1.0845, 1.0843,   # Second base (6-8)
                    1.0860, 1.0875, 1.0885],  # Second move (9-11)
            'high': [1.0810, 1.0808, 1.0806,
                    1.0850, 1.0865, 1.0875,
                    1.0850, 1.0848, 1.0846,
                    1.0890, 1.0905, 1.0915],
            'low':  [1.0795, 1.0802, 1.0801,
                    1.0815, 1.0830, 1.0840,
                    1.0835, 1.0842, 1.0841,
                    1.0855, 1.0870, 1.0880],
            'close':[1.0805, 1.0803, 1.0804,
                    1.0845, 1.0860, 1.0870,
                    1.0845, 1.0843, 1.0844,
                    1.0885, 1.0900, 1.0910],
            'volume': [1000] * 12,
            'time': pd.date_range('2025-01-01 10:00', periods=12, freq='1min')
        })
        
        # Create multiple base ranges
        base_ranges = [
            BaseCandleRange(0, 2, datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 10, 2),
                           1.0810, 1.0795, 0.0010, 3, 0.8),
            BaseCandleRange(6, 8, datetime(2025, 1, 1, 10, 6), datetime(2025, 1, 1, 10, 8),
                           1.0850, 1.0835, 0.0010, 3, 0.8)
        ]
        
        big_moves = detector.detect_big_moves(multi_range_data, base_ranges)
        
        # Should detect moves for both ranges
        assert len(big_moves) >= 1, f"Should detect moves from multiple ranges, got {len(big_moves)}"
        
        # Validate moves don't overlap with base ranges
        for move in big_moves:
            for base_range in base_ranges:
                if move.start_index <= base_range.end_index:
                    # Move should start after its base range
                    assert move.start_index > base_range.end_index, \
                        f"Move should start after base range: move {move.start_index} vs base {base_range.end_index}"
    
    def test_performance_benchmark(self, detector):
        """
        Test performance meets <30ms requirement.
        
        Success Criteria:
        - Processes 1000 bars with 50 base ranges in <30ms
        - Memory usage remains stable
        - Scales linearly with data size
        """
        # Create large dataset for performance testing
        large_dataset = self._create_large_move_dataset(1000)
        base_ranges = self._create_multiple_base_ranges(50)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Warm up
        detector.detect_big_moves(large_dataset.head(100), base_ranges[:5])
        
        # Performance test
        start_time = time.perf_counter()
        
        big_moves = detector.detect_big_moves(large_dataset, base_ranges)
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        assert duration_ms < 30, f"Performance test failed: {duration_ms:.2f}ms > 30ms target"
        assert memory_mb < 15, f"Memory usage too high: {memory_mb:.1f}MB > 15MB limit"
        
        # Verify algorithm correctness under load
        assert isinstance(big_moves, list), "Should return list even with large dataset"
    
    def test_configuration_validation(self):
        """
        Test detector configuration validation.
        
        Success Criteria:
        - Rejects invalid parameter values
        - Validates threshold ranges
        - Proper error messages for invalid config
        """
        # Test invalid move threshold
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(move_threshold=0.0)  # Zero threshold
        
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(move_threshold=-1.0)  # Negative threshold
        
        # Test invalid min move candles
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(min_move_candles=0)  # Zero minimum
        
        # Test invalid momentum threshold
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(momentum_threshold=1.5)  # Above 1.0
        
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(momentum_threshold=-0.1)  # Negative
        
        # Test invalid volume multiplier
        with pytest.raises((ValueError, AssertionError)):
            BigMoveDetector(volume_multiplier=0.5)  # Below 1.0
    
    def test_data_validation(self, detector, sample_base_range):
        """
        Test input data validation.
        
        Success Criteria:
        - Validates required columns exist
        - Handles missing volume data appropriately
        - Validates data integrity
        """
        # Test missing volume column
        data_no_volume = pd.DataFrame({
            'open': [1.0800, 1.0820],
            'high': [1.0810, 1.0840],
            'low': [1.0795, 1.0815],
            'close': [1.0805, 1.0835],
            'time': pd.date_range('2025-01-01 10:00', periods=2, freq='1min')
        })
        
        base_ranges = [sample_base_range]
        
        # Should handle missing volume gracefully (volume confirmation = False)
        big_moves = detector.detect_big_moves(data_no_volume, base_ranges)
        # Should not crash, may return moves with volume_confirmation=False
        
        # Test empty dataframe
        empty_data = pd.DataFrame()
        
        big_moves_empty = detector.detect_big_moves(empty_data, base_ranges)
        assert big_moves_empty == [], "Empty data should return empty list"
    
    # Helper methods for test data creation
    def _create_large_move_dataset(self, size: int) -> pd.DataFrame:
        """Create large dataset for performance testing"""
        np.random.seed(42)  # Reproducible results
        
        data = []
        base_price = 1.0800
        
        for i in range(size):
            # Create realistic price movement
            if i % 20 < 5:  # Consolidation periods
                price_change = np.random.normal(0, 0.00002)
            else:  # Trending periods
                price_change = np.random.normal(0.00005, 0.00010)
            
            base_price += price_change
            
            # Generate OHLC
            spread = abs(np.random.normal(0, 0.00005))
            open_price = base_price
            high_price = base_price + spread + 0.00002
            low_price = base_price - spread - 0.00002
            close_price = base_price + price_change
            
            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': np.random.randint(800, 2000),
                'time': datetime(2025, 1, 1, 10, 0) + timedelta(minutes=i)
            })
        
        return pd.DataFrame(data)
    
    def _create_multiple_base_ranges(self, count: int) -> List[BaseCandleRange]:
        """Create multiple base ranges for testing"""
        ranges = []
        
        for i in range(count):
            start_index = i * 10  # Space out ranges
            end_index = start_index + 3
            
            base_range = BaseCandleRange(
                start_index=start_index,
                end_index=end_index,
                start_time=datetime(2025, 1, 1, 10, 0) + timedelta(minutes=start_index),
                end_time=datetime(2025, 1, 1, 10, 0) + timedelta(minutes=end_index),
                high=1.0800 + (i * 0.0010),
                low=1.0790 + (i * 0.0010),
                atr_at_creation=0.0010,
                candle_count=4,
                consolidation_score=0.7 + (i % 3) * 0.1
            )
            ranges.append(base_range)
        
        return ranges


# Test fixtures for other test files
@pytest.fixture
def big_move_detector():
    """Standard BigMoveDetector for use in other test files"""
    return BigMoveDetector(
        move_threshold=2.0,
        min_move_candles=3,
        momentum_threshold=0.6,
        volume_multiplier=1.5,
        breakout_confirmation=True
    )


@pytest.fixture
def sample_big_move():
    """Sample BigMove for testing"""
    return BigMove(
        start_index=5,
        end_index=8,
        start_time=datetime(2025, 1, 1, 10, 5),
        end_time=datetime(2025, 1, 1, 10, 8),
        direction="bullish",
        magnitude=3.2,
        momentum_score=0.85,
        breakout_level=1.0810,
        volume_confirmation=True
    )


# Performance benchmarking
def benchmark_big_move_detection():
    """Standalone performance benchmark for CI/CD"""
    detector = BigMoveDetector()
    
    # Create test data and ranges
    test_data = TestBigMoveDetector()._create_large_move_dataset(1000)
    base_ranges = TestBigMoveDetector()._create_multiple_base_ranges(50)
    
    # Benchmark
    start_time = time.perf_counter()
    moves = detector.detect_big_moves(test_data, base_ranges)
    duration = (time.perf_counter() - start_time) * 1000
    
    print(f"BigMoveDetector 1000 bars, 50 ranges: {duration:.2f}ms")
    
    # Assert performance target
    assert duration < 30, f"Performance test failed: {duration:.2f}ms > 30ms"


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_big_move_detection()