# Supply & Demand Zone Detection - Test Specifications

## Document Information
- **Version**: 1.0
- **Date**: July 6, 2025
- **Author**: Claude AI Agent
- **Status**: Draft
- **Dependencies**: SUPPLY_DEMAND_SYSTEM.md, SUPPLY_DEMAND_API.md, SUPPLY_DEMAND_INTEGRATION.md

---

## 1. Test Strategy Overview

### 1.1 Testing Philosophy
The Supply & Demand Zone Detection System follows **Test-Driven Development (TDD)** principles with comprehensive coverage across all architectural layers. Tests are designed to validate both functional correctness and performance requirements.

### 1.2 Test Categories
- **Unit Tests**: Individual component validation
- **Integration Tests**: System interaction validation  
- **Performance Tests**: Speed and memory benchmarks
- **API Tests**: Endpoint functionality and contracts
- **Database Tests**: Data persistence and queries
- **End-to-End Tests**: Complete workflow validation
- **Regression Tests**: Existing system compatibility

### 1.3 Test Coverage Targets
- **Unit Test Coverage**: >95%
- **Integration Test Coverage**: >90%
- **Performance Test Coverage**: 100% of critical paths
- **API Test Coverage**: 100% of endpoints

### 1.4 Performance Test Criteria
- **Zone Detection**: <50ms per update (PASS/FAIL)
- **Rectangle Drawing**: <30ms per chart update (PASS/FAIL)
- **Confluence Calculation**: <20ms per bar (PASS/FAIL)
- **Database Queries**: <10ms per operation (PASS/FAIL)
- **Total System Impact**: <100ms additional overhead (PASS/FAIL)

---

## 2. Unit Test Specifications

### 2.1 BaseCandleDetector Tests

#### 2.1.1 Test File: `test_base_candle_detection.py`

```python
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.analysis.supply_demand.base_candle_detector import BaseCandleDetector, BaseCandleRange

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
            'time': pd.date_range('2025-01-01 10:00', periods=6, freq='1min')
        })
    
    def test_atr_calculation_accuracy(self, detector):
        """
        Test ATR calculation matches standard formula.
        
        Success Criteria:
        - ATR values match manual calculation
        - Handles first 14 bars correctly
        - No division by zero errors
        """
        # Create test data with known ATR values
        test_data = self._create_known_atr_data()
        
        atr_series = detector._calculate_atr(test_data)
        
        # Validate ATR calculation
        assert len(atr_series) == len(test_data)
        assert not atr_series.isna().any()
        
        # Check specific known values
        expected_atr_20 = 0.0015  # Known calculation result
        assert abs(atr_series.iloc[20] - expected_atr_20) < 0.0001
        
    def test_consolidation_candle_identification(self, detector, sample_consolidation_data):
        """
        Test individual candle consolidation classification.
        
        Success Criteria:
        - Small candles correctly identified as consolidation
        - Large candles correctly rejected
        - Body size threshold properly applied
        """
        atr_values = detector._calculate_atr(sample_consolidation_data)
        
        # Test consolidation candles (indices 0-4)
        for i in range(5):
            candle = sample_consolidation_data.iloc[i]
            is_consolidation = detector._is_consolidation_candle(candle, atr_values.iloc[i])
            assert is_consolidation, f"Candle {i} should be consolidation"
        
        # Test breakout candle (index 5)
        breakout_candle = sample_consolidation_data.iloc[5]
        is_consolidation = detector._is_consolidation_candle(breakout_candle, atr_values.iloc[5])
        assert not is_consolidation, "Breakout candle should not be consolidation"
    
    def test_base_candle_range_detection(self, detector, sample_consolidation_data):
        """
        Test complete base candle range detection.
        
        Success Criteria:
        - Detects exactly 1 base candle range
        - Range includes candles 0-4 (5 candles)
        - Excludes breakout candle (index 5)
        - Range boundaries are correct
        """
        ranges = detector.detect_base_candles(sample_consolidation_data)
        
        assert len(ranges) == 1, "Should detect exactly one base candle range"
        
        base_range = ranges[0]
        assert base_range.start_index == 0
        assert base_range.end_index == 4
        assert base_range.candle_count == 5
        assert base_range.consolidation_score > 0.5
        
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
            'time': pd.date_range('2025-01-01', periods=5, freq='1min')
        })
        
        ranges = detector.detect_base_candles(insufficient_data)
        assert ranges == [], "Should return empty list for insufficient data"
    
    def test_edge_case_no_consolidation(self, detector):
        """
        Test behavior when no consolidation patterns exist.
        
        Success Criteria:
        - Returns empty list when all candles are large
        - No false positive detections
        """
        trending_data = self._create_trending_data()  # All large candles
        
        ranges = detector.detect_base_candles(trending_data)
        assert ranges == [], "Should return empty list for trending data"
    
    def test_edge_case_single_consolidation_candle(self, detector):
        """
        Test behavior with only 1 consolidation candle.
        
        Success Criteria:
        - Does not create base range (min_base_candles = 2)
        - Returns empty list
        """
        single_consolidation_data = self._create_single_consolidation_data()
        
        ranges = detector.detect_base_candles(single_consolidation_data)
        assert ranges == [], "Should not detect range with single consolidation candle"
    
    def test_performance_benchmark(self, detector):
        """
        Test performance meets <20ms requirement.
        
        Success Criteria:
        - Processes 1000 bars in <20ms
        - Memory usage remains stable
        - No memory leaks detected
        """
        import time
        import tracemalloc
        
        large_dataset = self._create_large_dataset(1000)
        
        # Measure performance
        tracemalloc.start()
        start_time = time.perf_counter()
        
        ranges = detector.detect_base_candles(large_dataset)
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        
        assert duration_ms < 20, f"Performance test failed: {duration_ms:.2f}ms > 20ms"
        assert peak < 10 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.1f}MB"
    
    def test_configuration_validation(self):
        """
        Test detector configuration validation.
        
        Success Criteria:
        - Rejects invalid threshold values
        - Validates min/max base candle counts
        - Proper error messages for invalid config
        """
        with pytest.raises(ValueError):
            BaseCandleDetector(consolidation_threshold=-0.1)  # Negative threshold
            
        with pytest.raises(ValueError):
            BaseCandleDetector(min_base_candles=0)  # Zero minimum
            
        with pytest.raises(ValueError):
            BaseCandleDetector(min_base_candles=15, max_base_candles=10)  # Min > Max
    
    # Helper methods for test data creation
    def _create_known_atr_data(self):
        """Create OHLC data with known ATR calculation results"""
        # Implementation details...
        
    def _create_trending_data(self):
        """Create trending data with no consolidation"""
        # Implementation details...
        
    def _create_single_consolidation_data(self):
        """Create data with only one consolidation candle"""
        # Implementation details...
        
    def _create_large_dataset(self, size):
        """Create large dataset for performance testing"""
        # Implementation details...
```

### 2.2 BigMoveDetector Tests

#### 2.2.1 Test File: `test_big_move_detection.py`

```python
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
    
    def test_move_magnitude_calculation(self, detector, sample_big_move_data):
        """
        Test accurate move magnitude calculation in ATR multiples.
        
        Success Criteria:
        - Magnitude calculated correctly vs ATR
        - Directional moves properly identified
        - ATR baseline properly established
        """
        base_range = BaseCandleRange(
            start_index=0, end_index=4,
            start_time=sample_big_move_data.iloc[0]['time'],
            end_time=sample_big_move_data.iloc[4]['time'],
            high=1.0810, low=1.0795,
            atr_at_creation=0.0010, candle_count=5,
            consolidation_score=0.8
        )
        
        magnitude = detector._calculate_move_magnitude(
            sample_big_move_data, 5, 8, base_range
        )
        
        # Expected: (1.0855 - 1.0801) / 0.0010 = 5.4x ATR
        expected_magnitude = 5.4
        assert abs(magnitude - expected_magnitude) < 0.2
    
    def test_momentum_score_calculation(self, detector, sample_big_move_data):
        """
        Test momentum score reflects move quality.
        
        Success Criteria:
        - Strong directional moves score >0.8
        - Choppy moves score <0.4
        - Consistent momentum properly weighted
        """
        momentum_score = detector._calculate_momentum_score(
            sample_big_move_data, 5, 8
        )
        
        assert momentum_score > 0.8, f"Strong move should have high momentum: {momentum_score}"
    
    def test_big_move_detection_success(self, detector, sample_big_move_data):
        """
        Test successful big move detection.
        
        Success Criteria:
        - Detects exactly 1 big move
        - Move classified as bullish
        - Proper start/end indices
        - Magnitude meets threshold
        """
        base_ranges = [BaseCandleRange(
            start_index=0, end_index=4,
            start_time=sample_big_move_data.iloc[0]['time'],
            end_time=sample_big_move_data.iloc[4]['time'],
            high=1.0810, low=1.0795,
            atr_at_creation=0.0010, candle_count=5,
            consolidation_score=0.8
        )]
        
        big_moves = detector.detect_big_moves(
            sample_big_move_data, base_ranges
        )
        
        assert len(big_moves) == 1, "Should detect exactly one big move"
        
        move = big_moves[0]
        assert move.direction == "bullish"
        assert move.start_index == 5
        assert move.end_index == 8
        assert move.magnitude >= detector.move_threshold
        assert move.momentum_score >= detector.momentum_threshold
    
    def test_volume_confirmation(self, detector, sample_big_move_data):
        """
        Test volume spike confirmation.
        
        Success Criteria:
        - Volume spike properly detected
        - Volume confirmation flag set correctly
        - Threshold properly applied
        """
        base_ranges = [BaseCandleRange(
            start_index=0, end_index=4,
            start_time=sample_big_move_data.iloc[0]['time'],
            end_time=sample_big_move_data.iloc[4]['time'],
            high=1.0810, low=1.0795,
            atr_at_creation=0.0010, candle_count=5,
            consolidation_score=0.8
        )]
        
        big_moves = detector.detect_big_moves(
            sample_big_move_data, base_ranges
        )
        
        move = big_moves[0]
        assert move.volume_confirmation == True, "Volume spike should be confirmed"
    
    def test_edge_case_weak_move(self, detector):
        """
        Test rejection of weak moves.
        
        Success Criteria:
        - Moves below threshold rejected
        - Poor momentum moves rejected
        - Returns empty list for weak patterns
        """
        weak_move_data = self._create_weak_move_data()
        base_ranges = [self._create_sample_base_range()]
        
        big_moves = detector.detect_big_moves(weak_move_data, base_ranges)
        
        assert big_moves == [], "Weak moves should be rejected"
    
    def test_performance_benchmark(self, detector):
        """
        Test performance meets <30ms requirement.
        
        Success Criteria:
        - Processes 1000 bars with 50 base ranges in <30ms
        - Memory usage remains stable
        """
        import time
        
        large_dataset = self._create_large_move_dataset(1000)
        base_ranges = self._create_multiple_base_ranges(50)
        
        start_time = time.perf_counter()
        big_moves = detector.detect_big_moves(large_dataset, base_ranges)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        assert duration_ms < 30, f"Performance test failed: {duration_ms:.2f}ms > 30ms"
```

### 2.3 SupplyDemandZoneDetector Tests

#### 2.3.1 Test File: `test_zone_detection.py`

```python
class TestSupplyDemandZoneDetector:
    """
    Comprehensive unit tests for main zone detection system.
    
    Tests cover:
    - End-to-end zone detection
    - Zone type classification
    - Boundary calculation accuracy
    - Zone strength scoring
    - Integration with base/move detectors
    """
    
    @pytest.fixture
    def zone_detector(self, base_detector, move_detector):
        return SupplyDemandZoneDetector(
            base_detector=base_detector,
            move_detector=move_detector,
            max_zones_per_timeframe=100,
            zone_expiry_hours=168,
            overlap_tolerance=0.1
        )
    
    @pytest.fixture
    def sample_demand_zone_data(self):
        """
        Complete OHLC data with demand zone pattern.
        
        Pattern: Base candles + bullish breakout = Demand zone
        Expected: 1 demand zone with specific boundaries
        """
        return pd.DataFrame({
            # Base candles (consolidation)
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Red, Green, Red, Green, Red
                    1.0801, 1.0820, 1.0835, 1.0845],          # Bullish breakout
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,  # Consolidation highs
                    1.0825, 1.0840, 1.0850, 1.0860],          # Breakout highs
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,  # Consolidation lows
                    1.0800, 1.0815, 1.0830, 1.0840],          # Breakout lows
            'close':[1.0795, 1.0806, 1.0801, 1.0806, 1.0800,  # Mixed colors
                    1.0820, 1.0835, 1.0845, 1.0855],          # Bullish closes
            'volume': [1000] * 5 + [2500, 2000, 1800, 1600],
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
    
    def test_demand_zone_detection_success(self, zone_detector, sample_demand_zone_data):
        """
        Test successful demand zone detection and classification.
        
        Success Criteria:
        - Detects exactly 1 zone
        - Zone classified as 'demand'
        - Proper boundary calculation per eWavesHarmonics rules
        - Zone strength score >0.5
        """
        zones = zone_detector.detect_zones(
            df=sample_demand_zone_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        assert len(zones) == 1, "Should detect exactly one demand zone"
        
        zone = zones[0]
        assert zone.zone_type == 'demand'
        assert zone.symbol == 'EURUSD'
        assert zone.timeframe == 'M1'
        assert zone.strength_score >= 0.5
        
        # Test eWavesHarmonics boundary rules for demand zone
        # Top: Highest high of base candles = 1.0810
        # Bottom: Lowest open of red candles in base = 1.0795
        assert abs(zone.top_price - 1.0810) < 0.0001
        assert abs(zone.bottom_price - 1.0795) < 0.0001
    
    def test_supply_zone_detection_success(self, zone_detector):
        """
        Test successful supply zone detection and classification.
        
        Success Criteria:
        - Detects supply zone from bearish pattern
        - Proper boundary calculation for supply zones
        - Zone classified as 'supply'
        """
        supply_zone_data = self._create_supply_zone_data()
        
        zones = zone_detector.detect_zones(
            df=supply_zone_data,
            symbol='GBPUSD', 
            timeframe='M5'
        )
        
        assert len(zones) == 1
        zone = zones[0]
        assert zone.zone_type == 'supply'
        
        # Test eWavesHarmonics boundary rules for supply zone
        # Top: Highest open of green candles in base
        # Bottom: Lowest low of base candles
        expected_top = 1.2650  # Calculated from test data
        expected_bottom = 1.2620
        assert abs(zone.top_price - expected_top) < 0.0001
        assert abs(zone.bottom_price - expected_bottom) < 0.0001
    
    def test_zone_strength_calculation(self, zone_detector, sample_demand_zone_data):
        """
        Test zone strength scoring algorithm.
        
        Success Criteria:
        - High volume zones score higher
        - Strong momentum moves increase score
        - Good base candle quality increases score
        - Score range 0.0-1.0 maintained
        """
        zones = zone_detector.detect_zones(
            df=sample_demand_zone_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        zone = zones[0]
        
        # Validate strength score components
        assert 0.0 <= zone.strength_score <= 1.0
        
        # Test with high volume data
        high_volume_data = sample_demand_zone_data.copy()
        high_volume_data['volume'] = high_volume_data['volume'] * 3
        
        high_volume_zones = zone_detector.detect_zones(
            df=high_volume_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        assert high_volume_zones[0].strength_score > zone.strength_score
    
    def test_overlapping_zone_resolution(self, zone_detector):
        """
        Test resolution of overlapping zones.
        
        Success Criteria:
        - Overlapping zones properly merged or prioritized
        - No duplicate zones in output
        - Strongest zones preserved
        """
        overlapping_data = self._create_overlapping_zones_data()
        
        zones = zone_detector.detect_zones(
            df=overlapping_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Verify no overlapping zones
        for i, zone1 in enumerate(zones):
            for j, zone2 in enumerate(zones[i+1:], i+1):
                overlap = self._calculate_zone_overlap(zone1, zone2)
                assert overlap <= zone_detector.overlap_tolerance
    
    def test_performance_benchmark(self, zone_detector):
        """
        Test complete zone detection performance.
        
        Success Criteria:
        - Processes 1000 bars in <50ms
        - Memory usage stable
        - Output quality maintained under load
        """
        import time
        
        large_dataset = self._create_large_zone_dataset(1000)
        
        start_time = time.perf_counter()
        zones = zone_detector.detect_zones(
            df=large_dataset,
            symbol='EURUSD',
            timeframe='M1'
        )
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        assert duration_ms < 50, f"Zone detection performance failed: {duration_ms:.2f}ms > 50ms"
        
        # Verify output quality
        assert len(zones) > 0, "Should detect some zones in large dataset"
        assert all(zone.strength_score > 0 for zone in zones)
```

### 2.4 ZoneStateManager Tests

#### 2.4.1 Test File: `test_zone_state_management.py`

```python
class TestZoneStateManager:
    """
    Tests for zone lifecycle and state transitions.
    
    Tests cover:
    - Zone testing detection
    - Zone break confirmation
    - Zone flip detection
    - State transition accuracy
    - Real-time state updates
    """
    
    @pytest.fixture
    def state_manager(self):
        return ZoneStateManager(
            test_proximity_pips=2.0,
            break_confirmation_bars=3,
            flip_confirmation_bars=5,
            rejection_threshold=0.3
        )
    
    @pytest.fixture
    def sample_demand_zone(self):
        return SupplyDemandZone(
            id=1, symbol='EURUSD', timeframe='M1',
            zone_type='demand', top_price=1.0850, bottom_price=1.0840,
            left_time=datetime(2025, 1, 1, 10, 0),
            right_time=datetime(2025, 1, 1, 10, 30),
            strength_score=0.8, test_count=0, success_count=0,
            status='active', base_range=None, big_move=None,
            atr_at_creation=0.0010, volume_at_creation=1500,
            created_at=datetime(2025, 1, 1, 10, 0),
            updated_at=datetime(2025, 1, 1, 10, 0)
        )
    
    def test_zone_test_detection_touch(self, state_manager, sample_demand_zone):
        """
        Test detection of zone boundary touches.
        
        Success Criteria:
        - Price touch within proximity detected
        - Test type classified as 'touch'
        - Rejection strength calculated
        """
        # Create price data touching zone boundary
        test_data = pd.DataFrame({
            'open': [1.0845, 1.0842],
            'high': [1.0847, 1.0844],
            'low': [1.0841, 1.0840],  # Touches zone bottom
            'close': [1.0844, 1.0843],
            'volume': [1200, 1100],
            'time': pd.date_range('2025-01-01 10:05', periods=2, freq='1min')
        })
        
        zone_test = state_manager.detect_zone_tests(
            sample_demand_zone, test_data, 1
        )
        
        assert zone_test is not None
        assert zone_test.test_type == 'touch'
        assert zone_test.test_price == 1.0840
        assert zone_test.rejection_strength >= 0.3
    
    def test_zone_break_detection(self, state_manager, sample_demand_zone):
        """
        Test detection of zone breaks with confirmation.
        
        Success Criteria:
        - Break detection when price closes below zone
        - Confirmation after specified number of bars
        - No false breaks on temporary penetration
        """
        # Create price data breaking zone with confirmation
        break_data = pd.DataFrame({
            'open': [1.0845, 1.0838, 1.0835, 1.0832],
            'high': [1.0847, 1.0840, 1.0837, 1.0834],
            'low': [1.0835, 1.0832, 1.0830, 1.0828],  # Clean break below 1.0840
            'close': [1.0837, 1.0834, 1.0832, 1.0830], # Confirmed closes below
            'volume': [1800, 1600, 1400, 1300],
            'time': pd.date_range('2025-01-01 10:10', periods=4, freq='1min')
        })
        
        # Test break detection (needs 3 confirmation bars)
        for i in range(len(break_data)):
            is_broken = state_manager.detect_zone_break(
                sample_demand_zone, break_data, i
            )
            
            if i < 2:  # First 2 bars - not enough confirmation
                assert not is_broken
            else:  # After 3 bars - confirmed break
                assert is_broken
    
    def test_zone_flip_detection(self, state_manager, sample_demand_zone):
        """
        Test detection of zone flips (demand becomes supply).
        
        Success Criteria:
        - Flip detected after zone break
        - New zone created with opposite type
        - Proper flip confirmation
        """
        # Mark zone as broken first
        sample_demand_zone.status = 'broken'
        
        # Create price data showing flip behavior
        flip_data = pd.DataFrame({
            'open': [1.0830, 1.0835, 1.0838, 1.0841, 1.0844, 1.0842],
            'high': [1.0835, 1.0840, 1.0843, 1.0846, 1.0847, 1.0845],
            'low': [1.0828, 1.0833, 1.0836, 1.0839, 1.0840, 1.0838],  # Return to zone
            'close': [1.0833, 1.0838, 1.0841, 1.0844, 1.0842, 1.0839], # Rejection from zone
            'volume': [1400, 1500, 1600, 1700, 1600, 1500],
            'time': pd.date_range('2025-01-01 10:15', periods=6, freq='1min')
        })
        
        flip_result = state_manager.detect_zone_flip(
            sample_demand_zone, flip_data, 5  # After sufficient bars
        )
        
        assert flip_result is not None
        new_zone, flip_record = flip_result
        
        assert new_zone.zone_type == 'supply'  # Flipped to opposite type
        assert flip_record.original_zone_id == sample_demand_zone.id
        assert flip_record.confirmation_bars >= state_manager.flip_confirmation_bars
    
    def test_state_update_performance(self, state_manager):
        """
        Test state update performance with multiple zones.
        
        Success Criteria:
        - Updates 100 zones in <20ms
        - No performance degradation with zone count
        """
        import time
        
        zones = self._create_multiple_zones(100)
        test_data = self._create_state_update_data()
        
        start_time = time.perf_counter()
        updated_zones, tests, flips = state_manager.update_zone_states(
            zones, test_data, len(test_data) - 1
        )
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        assert duration_ms < 20, f"State update performance failed: {duration_ms:.2f}ms > 20ms"
```

---

## 3. Integration Test Specifications

### 3.1 Confluence Engine Integration Tests

#### 3.1.1 Test File: `test_confluence_integration.py`

```python
class TestConfluenceIntegration:
    """
    Integration tests for S&D zones with existing confluence system.
    
    Tests cover:
    - Confluence factor integration
    - Fibonacci + S&D alignment scoring
    - Performance impact on existing system
    - Backward compatibility verification
    """
    
    @pytest.fixture
    def integrated_confluence_engine(self, confluence_config):
        """Confluence engine with S&D integration enabled"""
        engine = ConfluenceEngine(confluence_config)
        engine.initialize_supply_demand()
        return engine
    
    def test_supply_demand_factor_integration(self, integrated_confluence_engine):
        """
        Test S&D zones appear as confluence factors.
        
        Success Criteria:
        - S&D zones generate ConfluenceFactor objects
        - Factor type correctly set to SUPPLY_DEMAND
        - Metadata includes zone information
        - Scoring integrates with existing factors
        """
        test_data = self._create_confluence_test_data()
        
        confluence_result = integrated_confluence_engine.process_bar(
            df=test_data,
            current_index=len(test_data) - 1,
            fibonacci_levels=[1.0845, 1.0855, 1.0865],
            abc_patterns=[],
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Verify S&D factors present
        sd_factors = [f for f in confluence_result.factors 
                     if f.factor_type == ConfluenceFactorType.SUPPLY_DEMAND]
        
        assert len(sd_factors) > 0, "Should detect S&D confluence factors"
        
        sd_factor = sd_factors[0]
        assert 'zone_id' in sd_factor.metadata
        assert 'zone_type' in sd_factor.metadata
        assert 'zone_status' in sd_factor.metadata
        assert 0.0 <= sd_factor.strength <= 1.0
    
    def test_fibonacci_alignment_bonus(self, integrated_confluence_engine):
        """
        Test bonus scoring when Fibonacci levels align with S&D zones.
        
        Success Criteria:
        - Aligned factors receive bonus multiplier
        - Non-aligned factors unaffected
        - Bonus calculation accurate
        """
        # Create data where Fibonacci 50% level aligns with demand zone
        aligned_data = self._create_fibonacci_aligned_data()
        fibonacci_levels = [1.0832, 1.0845, 1.0858]  # 50% at 1.0845 = zone center
        
        confluence_result = integrated_confluence_engine.process_bar(
            df=aligned_data,
            current_index=len(aligned_data) - 1,
            fibonacci_levels=fibonacci_levels,
            abc_patterns=[],
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Check for bonus in total score
        assert confluence_result.total_score > 0.8, "Aligned factors should receive bonus"
        
        # Verify individual factor scores
        fib_factors = [f for f in confluence_result.factors 
                      if f.factor_type == ConfluenceFactorType.FIBONACCI]
        sd_factors = [f for f in confluence_result.factors 
                     if f.factor_type == ConfluenceFactorType.SUPPLY_DEMAND]
        
        assert len(fib_factors) > 0 and len(sd_factors) > 0
    
    def test_backward_compatibility(self, integrated_confluence_engine):
        """
        Test existing confluence functionality unchanged.
        
        Success Criteria:
        - Existing factor types still work
        - No performance degradation
        - Original API contracts maintained
        """
        test_data = self._create_legacy_confluence_data()
        
        # Test original functionality
        confluence_result = integrated_confluence_engine.process_bar(
            df=test_data,
            current_index=len(test_data) - 1,
            fibonacci_levels=[1.0845],
            abc_patterns=[],
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Verify existing factor types present
        fib_factors = [f for f in confluence_result.factors 
                      if f.factor_type == ConfluenceFactorType.FIBONACCI]
        volume_factors = [f for f in confluence_result.factors 
                         if f.factor_type == ConfluenceFactorType.VOLUME]
        
        assert len(fib_factors) > 0, "Fibonacci factors should still work"
        assert len(volume_factors) > 0, "Volume factors should still work"
    
    def test_confluence_performance_impact(self, integrated_confluence_engine):
        """
        Test S&D integration stays within performance budget.
        
        Success Criteria:
        - Total confluence processing <60ms (40ms original + 20ms S&D)
        - No memory leaks
        - Performance scales linearly
        """
        import time
        
        large_dataset = self._create_large_confluence_dataset(1000)
        
        start_time = time.perf_counter()
        
        for i in range(100, len(large_dataset)):  # Process last 900 bars
            confluence_result = integrated_confluence_engine.process_bar(
                df=large_dataset[:i+1],
                current_index=i,
                fibonacci_levels=[1.0845, 1.0855],
                abc_patterns=[],
                symbol='EURUSD',
                timeframe='M1'
            )
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Average per bar should be <60ms
        avg_per_bar = duration_ms / 900
        assert avg_per_bar < 60, f"Confluence performance failed: {avg_per_bar:.2f}ms > 60ms"
```

### 3.2 Database Integration Tests

#### 3.2.1 Test File: `test_database_integration.py`

```python
class TestDatabaseIntegration:
    """
    Integration tests for S&D database operations.
    
    Tests cover:
    - Zone persistence and retrieval
    - Query performance optimization
    - Data integrity constraints
    - Migration compatibility
    """
    
    @pytest.fixture
    async def db_repository(self, test_database_url):
        """Test database repository"""
        repo = SupplyDemandRepository(test_database_url)
        await repo.initialize()
        return repo
    
    @pytest.fixture
    def sample_zone_for_db(self):
        """Sample zone for database testing"""
        return SupplyDemandZone(
            id=None,  # Will be assigned by database
            symbol='EURUSD',
            timeframe='M1',
            zone_type='demand',
            top_price=1.0850,
            bottom_price=1.0840,
            left_time=datetime(2025, 1, 1, 10, 0),
            right_time=datetime(2025, 1, 1, 10, 30),
            strength_score=0.8,
            test_count=0,
            success_count=0,
            status='active',
            base_range=None,
            big_move=None,
            atr_at_creation=0.0010,
            volume_at_creation=1500,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def test_zone_crud_operations(self, db_repository, sample_zone_for_db):
        """
        Test complete CRUD operations for zones.
        
        Success Criteria:
        - Create: Zone saved with auto-generated ID
        - Read: Zone retrieved with all fields intact
        - Update: Zone modifications persisted
        - Delete: Zone properly removed
        """
        # CREATE
        zone_id = await db_repository.save_zone(sample_zone_for_db)
        assert zone_id > 0, "Zone should be saved with valid ID"
        
        # READ
        retrieved_zones = await db_repository.get_zones(
            symbol='EURUSD',
            timeframe='M1',
            start_time=datetime(2025, 1, 1, 9, 0),
            end_time=datetime(2025, 1, 1, 11, 0)
        )
        
        assert len(retrieved_zones) == 1
        retrieved_zone = retrieved_zones[0]
        assert retrieved_zone.id == zone_id
        assert retrieved_zone.symbol == sample_zone_for_db.symbol
        assert retrieved_zone.zone_type == sample_zone_for_db.zone_type
        
        # UPDATE
        retrieved_zone.status = 'tested'
        retrieved_zone.test_count = 1
        
        success = await db_repository.update_zone(retrieved_zone)
        assert success, "Zone update should succeed"
        
        # Verify update
        updated_zones = await db_repository.get_zones(
            symbol='EURUSD',
            timeframe='M1',
            start_time=datetime(2025, 1, 1, 9, 0),
            end_time=datetime(2025, 1, 1, 11, 0)
        )
        
        assert updated_zones[0].status == 'tested'
        assert updated_zones[0].test_count == 1
    
    async def test_query_performance(self, db_repository):
        """
        Test database query performance meets requirements.
        
        Success Criteria:
        - Single zone query <10ms
        - Bulk operations scale linearly
        - Indexes properly utilized
        """
        import time
        
        # Insert test zones for performance testing
        test_zones = self._create_performance_test_zones(1000)
        
        # Bulk insert (should be fast)
        start_time = time.perf_counter()
        for zone in test_zones:
            await db_repository.save_zone(zone)
        insert_time = (time.perf_counter() - start_time) * 1000
        
        # Query performance test
        start_time = time.perf_counter()
        zones = await db_repository.get_zones(
            symbol='EURUSD',
            timeframe='M1',
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 1, 2)
        )
        query_time = (time.perf_counter() - start_time) * 1000
        
        assert query_time < 10, f"Query performance failed: {query_time:.2f}ms > 10ms"
        assert len(zones) > 0, "Should retrieve zones from test data"
    
    async def test_data_integrity_constraints(self, db_repository):
        """
        Test database constraints prevent invalid data.
        
        Success Criteria:
        - Price constraints enforced (top > bottom)
        - Time constraints enforced (right >= left)
        - Foreign key constraints work
        - Check constraints validate ranges
        """
        # Test invalid price constraint
        invalid_zone = SupplyDemandZone(
            id=None, symbol='EURUSD', timeframe='M1',
            zone_type='demand',
            top_price=1.0840,  # Invalid: top < bottom
            bottom_price=1.0850,
            left_time=datetime(2025, 1, 1, 10, 0),
            right_time=datetime(2025, 1, 1, 10, 30),
            strength_score=0.8, test_count=0, success_count=0,
            status='active', base_range=None, big_move=None,
            atr_at_creation=0.0010, volume_at_creation=1500,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        with pytest.raises(Exception):  # Should raise constraint violation
            await db_repository.save_zone(invalid_zone)
    
    async def test_zone_statistics(self, db_repository):
        """
        Test zone performance statistics calculation.
        
        Success Criteria:
        - Statistics calculated correctly
        - Aggregation functions work
        - Time-based filtering accurate
        """
        # Insert zones with known statistics
        test_zones = self._create_zones_with_known_stats()
        for zone in test_zones:
            await db_repository.save_zone(zone)
        
        # Get statistics
        stats = await db_repository.get_zone_statistics(
            symbol='EURUSD',
            timeframe='M1',
            days_back=30
        )
        
        assert 'zones_created' in stats
        assert 'avg_zone_strength' in stats
        assert 'success_rate' in stats
        assert stats['zones_created'] == len(test_zones)
```

### 3.3 API Integration Tests

#### 3.3.1 Test File: `test_api_integration.py`

```python
class TestAPIIntegration:
    """
    Integration tests for S&D API endpoints.
    
    Tests cover:
    - Endpoint functionality
    - Request/response validation
    - Error handling
    - Performance requirements
    """
    
    @pytest.fixture
    def test_client(self, app_with_sd_integration):
        """Test client with S&D integration enabled"""
        return TestClient(app_with_sd_integration)
    
    def test_get_zones_endpoint(self, test_client, sample_zones_in_db):
        """
        Test zone retrieval endpoint.
        
        Success Criteria:
        - Returns zones in correct format
        - Filtering parameters work
        - Response time <100ms
        """
        import time
        
        start_time = time.perf_counter()
        response = test_client.get(
            "/api/supply-demand-zones/EURUSD/M1",
            params={
                'start_time': '2025-01-01T00:00:00',
                'end_time': '2025-01-02T00:00:00',
                'status': 'active'
            }
        )
        response_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 100, f"API response too slow: {response_time:.2f}ms"
        
        zones = response.json()
        assert isinstance(zones, list)
        assert len(zones) > 0
        
        # Validate zone structure
        zone = zones[0]
        required_fields = ['id', 'symbol', 'timeframe', 'zone_type', 
                          'top_price', 'bottom_price', 'strength_score']
        for field in required_fields:
            assert field in zone
    
    def test_detect_zones_realtime_endpoint(self, test_client):
        """
        Test real-time zone detection endpoint.
        
        Success Criteria:
        - Accepts OHLC data in request
        - Returns detected zones
        - Performance <100ms for 1000 bars
        """
        request_data = {
            'symbol': 'EURUSD',
            'timeframe': 'M1',
            'start_time': '2025-01-01T10:00:00',
            'end_time': '2025-01-01T11:00:00',
            'include_fibonacci': True,
            'include_fractals': True
        }
        
        response = test_client.post(
            "/api/supply-demand-zones/detect",
            json=request_data
        )
        
        assert response.status_code == 200
        
        zones = response.json()
        assert isinstance(zones, list)
        
        # Validate detected zones
        if len(zones) > 0:
            zone = zones[0]
            assert zone['symbol'] == 'EURUSD'
            assert zone['timeframe'] == 'M1'
            assert 0.0 <= zone['strength_score'] <= 1.0
    
    def test_confluence_calculation_endpoint(self, test_client):
        """
        Test confluence calculation with S&D zones.
        
        Success Criteria:
        - Calculates confluence score
        - Includes S&D factors in breakdown
        - Performance <20ms
        """
        import time
        
        request_data = {
            'symbol': 'EURUSD',
            'timeframe': 'M1',
            'price': 1.0845,
            'fibonacci_levels': [1.0832, 1.0845, 1.0858],
            'include_zones': True
        }
        
        start_time = time.perf_counter()
        response = test_client.post(
            "/api/supply-demand/confluence/calculate",
            json=request_data
        )
        response_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 20, f"Confluence calculation too slow: {response_time:.2f}ms"
        
        confluence = response.json()
        assert 'total_score' in confluence
        assert 'fibonacci_score' in confluence
        assert 'zone_score' in confluence
        assert 'factors' in confluence
        
        assert 0.0 <= confluence['total_score'] <= 1.0
    
    def test_websocket_zone_updates(self, test_client):
        """
        Test WebSocket real-time zone updates.
        
        Success Criteria:
        - WebSocket connection established
        - Zone updates broadcast correctly
        - Message format correct
        """
        with test_client.websocket_connect("/ws/supply-demand/EURUSD/M1") as websocket:
            # Trigger zone detection
            websocket.send_json({'action': 'detect_zones'})
            
            # Receive response
            data = websocket.receive_json()
            
            assert data['type'] == 'sd_zones_detected'
            assert 'data' in data
            assert isinstance(data['data'], list)
```

---

## 4. Performance Test Specifications

### 4.1 Speed Benchmark Tests

#### 4.1.1 Test File: `test_performance_benchmarks.py`

```python
class TestPerformanceBenchmarks:
    """
    Comprehensive performance testing for S&D system.
    
    Tests verify system meets critical performance requirements:
    - Zone detection: <50ms
    - Rectangle drawing: <30ms
    - Confluence calculation: <20ms
    - Database queries: <10ms
    - Total system impact: <100ms
    """
    
    def test_zone_detection_speed_benchmark(self):
        """
        Test zone detection speed with various dataset sizes.
        
        Success Criteria:
        - 100 bars: <10ms
        - 500 bars: <25ms
        - 1000 bars: <50ms
        - Linear scaling verified
        """
        import time
        
        detector = self._create_optimized_detector()
        
        test_sizes = [100, 500, 1000]
        results = {}
        
        for size in test_sizes:
            dataset = self._create_performance_dataset(size)
            
            # Warm up
            detector.detect_zones(dataset, 'EURUSD', 'M1')
            
            # Benchmark
            start_time = time.perf_counter()
            zones = detector.detect_zones(dataset, 'EURUSD', 'M1')
            end_time = time.perf_counter()
            
            duration_ms = (end_time - start_time) * 1000
            results[size] = duration_ms
            
            print(f"Zone detection {size} bars: {duration_ms:.2f}ms")
        
        # Verify performance targets
        assert results[100] < 10, f"100 bars too slow: {results[100]:.2f}ms"
        assert results[500] < 25, f"500 bars too slow: {results[500]:.2f}ms"
        assert results[1000] < 50, f"1000 bars too slow: {results[1000]:.2f}ms"
        
        # Verify linear scaling (±50% tolerance)
        scaling_ratio = results[1000] / results[100]
        assert 5 <= scaling_ratio <= 15, f"Non-linear scaling detected: {scaling_ratio:.1f}x"
    
    def test_rectangle_drawing_performance(self):
        """
        Test TradingView rectangle drawing performance.
        
        Success Criteria:
        - 10 zones: <5ms
        - 50 zones: <15ms
        - 100 zones: <30ms
        """
        import time
        
        mock_chart = MockTradingViewChart()
        rect_manager = SupplyDemandRectangleManager(mock_chart)
        
        test_zone_counts = [10, 50, 100]
        
        for count in test_zone_counts:
            zones = self._create_test_zones(count)
            
            start_time = time.perf_counter()
            rect_manager.update_all_zones(zones)
            end_time = time.perf_counter()
            
            duration_ms = (end_time - start_time) * 1000
            
            target_ms = count * 0.3  # 0.3ms per zone target
            assert duration_ms < target_ms, f"{count} zones too slow: {duration_ms:.2f}ms > {target_ms}ms"
    
    def test_confluence_calculation_performance(self):
        """
        Test confluence calculation performance.
        
        Success Criteria:
        - Single calculation: <5ms
        - 100 calculations: <20ms average
        - 1000 calculations: <20ms average (scaling test)
        """
        import time
        
        confluence_calc = SupplyDemandConfluence(
            zone_detector=self._create_optimized_detector(),
            max_distance_pips=5.0
        )
        
        zones = self._create_test_zones(20)
        fibonacci_levels = [1.0832, 1.0845, 1.0858, 1.0871]
        
        # Single calculation benchmark
        start_time = time.perf_counter()
        score = confluence_calc.calculate_confluence_score(
            price=1.0845, zones=zones, 
            fibonacci_levels=fibonacci_levels, symbol='EURUSD'
        )
        single_time = (time.perf_counter() - start_time) * 1000
        
        assert single_time < 5, f"Single confluence calculation too slow: {single_time:.2f}ms"
        
        # Batch calculation benchmark
        prices = [1.0830 + i * 0.0005 for i in range(100)]
        
        start_time = time.perf_counter()
        for price in prices:
            score = confluence_calc.calculate_confluence_score(
                price=price, zones=zones,
                fibonacci_levels=fibonacci_levels, symbol='EURUSD'
            )
        batch_time = (time.perf_counter() - start_time) * 1000
        
        avg_time = batch_time / 100
        assert avg_time < 20, f"Batch confluence calculation too slow: {avg_time:.2f}ms avg"
    
    def test_database_query_performance(self):
        """
        Test database operation performance.
        
        Success Criteria:
        - Single zone query: <2ms
        - Range query (100 zones): <10ms
        - Complex statistics query: <50ms
        """
        import time
        import asyncio
        
        async def run_db_performance_tests():
            repo = SupplyDemandRepository(test_database_url)
            await repo.initialize()
            
            # Populate test data
            test_zones = self._create_db_performance_zones(1000)
            for zone in test_zones:
                await repo.save_zone(zone)
            
            # Single zone query
            start_time = time.perf_counter()
            zones = await repo.get_zones(
                symbol='EURUSD', timeframe='M1',
                start_time=datetime(2025, 1, 1, 10, 0),
                end_time=datetime(2025, 1, 1, 10, 1)
            )
            single_query_time = (time.perf_counter() - start_time) * 1000
            
            # Range query  
            start_time = time.perf_counter()
            zones = await repo.get_zones(
                symbol='EURUSD', timeframe='M1',
                start_time=datetime(2025, 1, 1),
                end_time=datetime(2025, 1, 2)
            )
            range_query_time = (time.perf_counter() - start_time) * 1000
            
            # Statistics query
            start_time = time.perf_counter()
            stats = await repo.get_zone_statistics(
                symbol='EURUSD', timeframe='M1', days_back=30
            )
            stats_query_time = (time.perf_counter() - start_time) * 1000
            
            return single_query_time, range_query_time, stats_query_time
        
        single_time, range_time, stats_time = asyncio.run(run_db_performance_tests())
        
        assert single_time < 2, f"Single query too slow: {single_time:.2f}ms"
        assert range_time < 10, f"Range query too slow: {range_time:.2f}ms"
        assert stats_time < 50, f"Statistics query too slow: {stats_time:.2f}ms"
    
    def test_end_to_end_system_performance(self):
        """
        Test complete system performance budget.
        
        Success Criteria:
        - Complete workflow <100ms additional overhead
        - Memory usage stable
        - No performance degradation over time
        """
        import time
        import tracemalloc
        
        # Initialize complete system
        system = self._create_complete_sd_system()
        test_data = self._create_realistic_trading_data(1000)
        
        tracemalloc.start()
        
        # Simulate real trading cycle
        start_time = time.perf_counter()
        
        for i in range(100, len(test_data)):  # Process last 900 bars
            # Complete S&D workflow
            zones = system.detect_zones(test_data[:i+1], 'EURUSD', 'M1')
            confluence_score = system.calculate_confluence(
                price=test_data.iloc[i]['close'],
                zones=zones,
                fibonacci_levels=[1.0845, 1.0855]
            )
            system.update_zone_states(zones, test_data[:i+1], i)
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_per_bar = total_time_ms / 900
        
        assert avg_per_bar < 100, f"System performance budget exceeded: {avg_per_bar:.2f}ms > 100ms"
        assert peak < 50 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.1f}MB"
```

### 4.2 Memory Usage Tests

#### 4.2.1 Test File: `test_memory_usage.py`

```python
class TestMemoryUsage:
    """
    Memory usage and leak detection tests.
    
    Tests verify:
    - Memory usage stays within limits
    - No memory leaks during operation
    - Efficient garbage collection
    - Cache management works properly
    """
    
    def test_zone_detection_memory_usage(self):
        """
        Test memory usage during zone detection.
        
        Success Criteria:
        - Memory usage <10MB for 1000 bars
        - No memory leaks after processing
        - Memory scales linearly with data size
        """
        import tracemalloc
        import gc
        
        detector = SupplyDemandZoneDetector(
            base_detector=BaseCandleDetector(),
            move_detector=BigMoveDetector()
        )
        
        # Baseline memory
        gc.collect()
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]
        
        # Process large dataset
        large_dataset = self._create_large_dataset(1000)
        zones = detector.detect_zones(large_dataset, 'EURUSD', 'M1')
        
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        memory_used = (peak_memory - baseline) / 1024 / 1024  # MB
        
        assert memory_used < 10, f"Memory usage too high: {memory_used:.1f}MB"
        
        # Test for memory leaks
        del zones, large_dataset
        gc.collect()
        
        # Process another dataset
        tracemalloc.start()
        second_baseline = tracemalloc.get_traced_memory()[0]
        
        zones2 = detector.detect_zones(
            self._create_large_dataset(1000), 'EURUSD', 'M1'
        )
        second_peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        second_memory = (second_peak - second_baseline) / 1024 / 1024
        
        # Memory usage should be similar (within 20%)
        memory_diff = abs(memory_used - second_memory) / memory_used
        assert memory_diff < 0.2, f"Memory leak detected: {memory_diff:.1f} increase"
    
    def test_zone_cache_memory_management(self):
        """
        Test zone cache memory management.
        
        Success Criteria:
        - Cache respects size limits
        - LRU eviction works correctly
        - Memory freed when zones evicted
        """
        import tracemalloc
        
        cache_manager = ZoneCacheManager(max_size=100)
        
        tracemalloc.start()
        
        # Fill cache to limit
        for i in range(100):
            zone = self._create_test_zone(i)
            cache_manager.add_zone(zone)
        
        memory_at_limit = tracemalloc.get_traced_memory()[0]
        
        # Add more zones (should trigger eviction)
        for i in range(100, 150):
            zone = self._create_test_zone(i)
            cache_manager.add_zone(zone)
        
        memory_after_eviction = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        # Memory should not grow significantly
        memory_growth = (memory_after_eviction - memory_at_limit) / 1024 / 1024
        assert memory_growth < 2, f"Cache memory growth too high: {memory_growth:.1f}MB"
        
        # Verify cache size maintained
        assert len(cache_manager.zones) <= 100
    
    def test_long_running_memory_stability(self):
        """
        Test memory stability over extended operation.
        
        Success Criteria:
        - Memory usage stable over 1000 iterations
        - No gradual memory increase
        - Garbage collection effective
        """
        import tracemalloc
        import gc
        
        system = self._create_complete_sd_system()
        
        memory_samples = []
        
        for iteration in range(100):  # Simulate long operation
            tracemalloc.start()
            
            # Process trading data
            test_data = self._create_trading_data_sample(100)
            zones = system.detect_zones(test_data, 'EURUSD', 'M1')
            confluence = system.calculate_confluence(
                price=test_data.iloc[-1]['close'],
                zones=zones,
                fibonacci_levels=[1.0845]
            )
            
            current, peak = tracemalloc.get_traced_memory()
            memory_samples.append(current / 1024 / 1024)  # MB
            tracemalloc.stop()
            
            # Cleanup
            del test_data, zones, confluence
            
            # Periodic garbage collection
            if iteration % 10 == 0:
                gc.collect()
        
        # Analyze memory trend
        early_avg = sum(memory_samples[:20]) / 20
        late_avg = sum(memory_samples[-20:]) / 20
        
        memory_growth = (late_avg - early_avg) / early_avg
        assert memory_growth < 0.1, f"Memory growth detected: {memory_growth:.1%}"
```

---

## 5. API Test Specifications

### 5.1 Endpoint Validation Tests

#### 5.1.1 Test File: `test_api_endpoints.py`

```python
class TestAPIEndpoints:
    """
    Comprehensive API endpoint testing.
    
    Tests cover:
    - Request/response validation
    - Error handling
    - Authentication (if applicable)
    - Rate limiting compliance
    - Documentation compliance
    """
    
    def test_get_zones_endpoint_validation(self, test_client):
        """
        Test zone retrieval endpoint validation.
        
        Success Criteria:
        - Valid requests return 200
        - Invalid parameters return 400
        - Missing parameters handled gracefully
        - Response schema matches documentation
        """
        # Valid request
        response = test_client.get(
            "/api/supply-demand-zones/EURUSD/M1",
            params={
                'start_time': '2025-01-01T00:00:00Z',
                'end_time': '2025-01-02T00:00:00Z'
            }
        )
        assert response.status_code == 200
        self._validate_zones_response_schema(response.json())
        
        # Invalid symbol
        response = test_client.get(
            "/api/supply-demand-zones/INVALID/M1",
            params={
                'start_time': '2025-01-01T00:00:00Z',
                'end_time': '2025-01-02T00:00:00Z'
            }
        )
        assert response.status_code == 400
        
        # Invalid timeframe
        response = test_client.get(
            "/api/supply-demand-zones/EURUSD/INVALID",
            params={
                'start_time': '2025-01-01T00:00:00Z',
                'end_time': '2025-01-02T00:00:00Z'
            }
        )
        assert response.status_code == 400
        
        # Invalid date format
        response = test_client.get(
            "/api/supply-demand-zones/EURUSD/M1",
            params={
                'start_time': 'invalid-date',
                'end_time': '2025-01-02T00:00:00Z'
            }
        )
        assert response.status_code == 400
    
    def test_detect_zones_endpoint_validation(self, test_client):
        """
        Test zone detection endpoint validation.
        
        Success Criteria:
        - Valid POST data returns zones
        - Invalid JSON returns 400
        - Missing required fields return 400
        - Large datasets handled properly
        """
        # Valid request
        valid_request = {
            'symbol': 'EURUSD',
            'timeframe': 'M1',
            'start_time': '2025-01-01T10:00:00Z',
            'end_time': '2025-01-01T11:00:00Z',
            'include_fibonacci': True,
            'include_fractals': True
        }
        
        response = test_client.post(
            "/api/supply-demand-zones/detect",
            json=valid_request
        )
        assert response.status_code == 200
        self._validate_zones_response_schema(response.json())
        
        # Missing required field
        invalid_request = valid_request.copy()
        del invalid_request['symbol']
        
        response = test_client.post(
            "/api/supply-demand-zones/detect",
            json=invalid_request
        )
        assert response.status_code == 422  # Validation error
        
        # Invalid JSON
        response = test_client.post(
            "/api/supply-demand-zones/detect",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    
    def test_confluence_endpoint_validation(self, test_client):
        """
        Test confluence calculation endpoint validation.
        
        Success Criteria:
        - Valid requests return confluence data
        - Invalid price values rejected
        - Empty fibonacci levels handled
        - Response time meets requirements
        """
        import time
        
        valid_request = {
            'symbol': 'EURUSD',
            'timeframe': 'M1',
            'price': 1.0845,
            'fibonacci_levels': [1.0832, 1.0845, 1.0858],
            'include_zones': True
        }
        
        start_time = time.perf_counter()
        response = test_client.post(
            "/api/supply-demand/confluence/calculate",
            json=valid_request
        )
        response_time = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 100, f"Confluence endpoint too slow: {response_time:.2f}ms"
        
        confluence_data = response.json()
        self._validate_confluence_response_schema(confluence_data)
        
        # Invalid price
        invalid_request = valid_request.copy()
        invalid_request['price'] = -1.0  # Negative price
        
        response = test_client.post(
            "/api/supply-demand/confluence/calculate",
            json=invalid_request
        )
        assert response.status_code == 400
    
    def test_error_handling_consistency(self, test_client):
        """
        Test consistent error handling across endpoints.
        
        Success Criteria:
        - Error responses follow standard format
        - HTTP status codes used correctly
        - Error messages are helpful
        - No sensitive information leaked
        """
        # Test 404 for non-existent endpoint
        response = test_client.get("/api/supply-demand-zones/nonexistent")
        assert response.status_code == 404
        
        # Test 405 for wrong HTTP method
        response = test_client.put("/api/supply-demand-zones/EURUSD/M1")
        assert response.status_code == 405
        
        # Test 500 handling (simulate internal error)
        # This would require mocking internal services to fail
        
    def _validate_zones_response_schema(self, zones_data):
        """Validate zones response matches expected schema"""
        assert isinstance(zones_data, list)
        
        if len(zones_data) > 0:
            zone = zones_data[0]
            required_fields = [
                'id', 'symbol', 'timeframe', 'zone_type',
                'top_price', 'bottom_price', 'left_time', 'right_time',
                'strength_score', 'test_count', 'status', 'created_at'
            ]
            
            for field in required_fields:
                assert field in zone, f"Missing required field: {field}"
            
            # Validate data types
            assert isinstance(zone['id'], int)
            assert isinstance(zone['top_price'], (int, float))
            assert isinstance(zone['bottom_price'], (int, float))
            assert isinstance(zone['strength_score'], (int, float))
            assert 0.0 <= zone['strength_score'] <= 1.0
            assert zone['zone_type'] in ['supply', 'demand', 'continuation']
            assert zone['status'] in ['active', 'tested', 'broken', 'flipped']
    
    def _validate_confluence_response_schema(self, confluence_data):
        """Validate confluence response matches expected schema"""
        required_fields = ['total_score', 'fibonacci_score', 'zone_score', 'factors']
        
        for field in required_fields:
            assert field in confluence_data, f"Missing required field: {field}"
        
        # Validate score ranges
        assert 0.0 <= confluence_data['total_score'] <= 1.0
        assert 0.0 <= confluence_data['fibonacci_score'] <= 1.0
        assert 0.0 <= confluence_data['zone_score'] <= 1.0
        
        # Validate factors array
        assert isinstance(confluence_data['factors'], list)
```

---

## 6. End-to-End Test Specifications

### 6.1 Complete Workflow Tests

#### 6.1.1 Test File: `test_end_to_end_workflows.py`

```python
class TestEndToEndWorkflows:
    """
    Complete workflow testing from data input to final output.
    
    Tests cover:
    - Complete zone detection pipeline
    - Integration with research dashboard
    - Real-time updates via WebSocket
    - Data persistence and retrieval
    """
    
    def test_complete_zone_detection_workflow(self):
        """
        Test complete zone detection from OHLC data to database storage.
        
        Success Criteria:
        - OHLC data processed correctly
        - Zones detected and classified
        - Zones persisted to database
        - Zones retrievable via API
        - Performance within budget
        """
        import time
        
        # Setup complete system
        system = self._create_integrated_system()
        
        # Input: Real OHLC data with known S&D patterns
        test_data = self._load_real_market_data('EURUSD_M1_with_zones.csv')
        
        start_time = time.perf_counter()
        
        # Step 1: Detect zones
        zones = system.zone_detector.detect_zones(
            df=test_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Step 2: Calculate zone strength
        for zone in zones:
            zone.strength_score = system.strength_calculator.calculate_strength(zone, test_data)
        
        # Step 3: Persist to database
        zone_ids = []
        for zone in zones:
            zone_id = asyncio.run(system.repository.save_zone(zone))
            zone_ids.append(zone_id)
        
        # Step 4: Retrieve via API
        retrieved_zones = asyncio.run(system.repository.get_zones(
            symbol='EURUSD',
            timeframe='M1',
            start_time=test_data.iloc[0]['time'],
            end_time=test_data.iloc[-1]['time']
        ))
        
        workflow_time = (time.perf_counter() - start_time) * 1000
        
        # Validate results
        assert len(zones) > 0, "Should detect zones in test data"
        assert len(retrieved_zones) == len(zones), "All zones should be persisted"
        assert workflow_time < 500, f"Complete workflow too slow: {workflow_time:.2f}ms"
        
        # Validate zone quality
        for zone in zones:
            assert zone.strength_score > 0.0
            assert zone.zone_type in ['supply', 'demand', 'continuation']
            assert zone.top_price > zone.bottom_price
    
    def test_real_time_confluence_workflow(self):
        """
        Test real-time confluence calculation workflow.
        
        Success Criteria:
        - New price data triggers zone updates
        - Confluence calculated with latest zones
        - Updates broadcast via WebSocket
        - Performance maintained under load
        """
        system = self._create_integrated_system()
        
        # Setup WebSocket connection mock
        websocket_messages = []
        
        def mock_websocket_send(message):
            websocket_messages.append(message)
        
        system.websocket_manager.broadcast_update = mock_websocket_send
        
        # Simulate real-time data feed
        base_data = self._load_base_market_data('EURUSD_M1_base.csv')
        
        for i in range(100, len(base_data)):
            current_data = base_data[:i+1]
            current_price = current_data.iloc[-1]['close']
            
            # Process new bar
            zones = system.zone_detector.detect_zones(
                df=current_data,
                symbol='EURUSD',
                timeframe='M1'
            )
            
            # Calculate confluence
            confluence_score = system.confluence_calculator.calculate_confluence_score(
                price=current_price,
                zones=zones,
                fibonacci_levels=[1.0832, 1.0845, 1.0858],
                symbol='EURUSD'
            )
            
            # Verify WebSocket updates sent
            if len(zones) > 0:
                assert len(websocket_messages) > 0, "Should send WebSocket updates"
        
        # Validate final state
        final_zones = zones
        assert len(final_zones) > 0
        assert all(zone.status in ['active', 'tested'] for zone in final_zones)
    
    def test_zone_lifecycle_workflow(self):
        """
        Test complete zone lifecycle from creation to expiry.
        
        Success Criteria:
        - Zones created from base candles
        - Zones tested when price returns
        - Zone status updated correctly
        - Zone breaks and flips detected
        """
        system = self._create_integrated_system()
        
        # Load data with complete zone lifecycle
        lifecycle_data = self._load_zone_lifecycle_data()
        
        zones = []
        zone_tests = []
        zone_flips = []
        
        # Process data bar by bar
        for i in range(50, len(lifecycle_data)):
            current_data = lifecycle_data[:i+1]
            
            # Detect new zones
            new_zones = system.zone_detector.detect_zones(
                df=current_data,
                symbol='EURUSD',
                timeframe='M1'
            )
            
            # Update existing zones and detect state changes
            updated_zones, tests, flips = system.state_manager.update_zone_states(
                zones=zones,
                df=current_data,
                current_index=i
            )
            
            zones = updated_zones + new_zones
            zone_tests.extend(tests)
            zone_flips.extend(flips)
        
        # Validate lifecycle events
        assert len(zones) > 0, "Should create zones"
        assert len(zone_tests) > 0, "Should detect zone tests"
        
        # Validate state transitions
        zone_statuses = [zone.status for zone in zones]
        assert 'tested' in zone_statuses, "Should have tested zones"
        
        if len(zone_flips) > 0:
            flip = zone_flips[0]
            original_zone = next(z for z in zones if z.id == flip.original_zone_id)
            new_zone = next(z for z in zones if z.id == flip.new_zone_id)
            assert original_zone.zone_type != new_zone.zone_type, "Flipped zones should have opposite types"
    
    def test_dashboard_integration_workflow(self):
        """
        Test complete dashboard integration workflow.
        
        Success Criteria:
        - Zones displayed on chart
        - UI controls work correctly
        - Real-time updates reflected
        - Performance acceptable for UI
        """
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Setup test browser
        driver = webdriver.Chrome()  # Requires ChromeDriver
        
        try:
            # Load dashboard
            driver.get("http://localhost:8001")
            
            # Wait for chart to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "trading-chart"))
            )
            
            # Select symbol and timeframe
            symbol_dropdown = driver.find_element(By.ID, "symbol-select")
            symbol_dropdown.send_keys("EURUSD")
            
            timeframe_dropdown = driver.find_element(By.ID, "timeframe-select")
            timeframe_dropdown.send_keys("M1")
            
            # Enable S&D zones
            sd_toggle = driver.find_element(By.ID, "sd-zones-toggle")
            if not sd_toggle.is_selected():
                sd_toggle.click()
            
            # Wait for zones to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "supply-demand-zone"))
            )
            
            # Verify zones are displayed
            zone_elements = driver.find_elements(By.CLASS_NAME, "supply-demand-zone")
            assert len(zone_elements) > 0, "Should display S&D zones on chart"
            
            # Test zone filtering
            supply_toggle = driver.find_element(By.ID, "sd-supply-toggle")
            supply_toggle.click()
            
            # Verify supply zones hidden
            visible_zones = [elem for elem in zone_elements if elem.is_displayed()]
            # Additional verification logic here...
            
        finally:
            driver.quit()
```

---

## 7. Regression Test Specifications

### 7.1 Backward Compatibility Tests

#### 7.1.1 Test File: `test_regression_compatibility.py`

```python
class TestRegressionCompatibility:
    """
    Regression tests to ensure S&D integration doesn't break existing functionality.
    
    Tests cover:
    - Existing confluence system unchanged
    - Fibonacci calculations unaffected
    - Research dashboard still works
    - Database schema migrations safe
    """
    
    def test_existing_confluence_system_unchanged(self):
        """
        Test existing confluence system works exactly as before.
        
        Success Criteria:
        - Same confluence scores for same inputs
        - All existing factor types still work
        - Performance not degraded
        - API contracts maintained
        """
        # Load baseline confluence results (pre-S&D integration)
        baseline_results = self._load_baseline_confluence_results()
        
        # Setup confluence engine WITHOUT S&D integration
        legacy_engine = ConfluenceEngine(enable_supply_demand=False)
        
        # Setup confluence engine WITH S&D integration but disabled
        new_engine = ConfluenceEngine(enable_supply_demand=True)
        new_engine.disable_supply_demand()
        
        test_data = self._load_regression_test_data()
        
        for test_case in baseline_results:
            # Test legacy engine
            legacy_result = legacy_engine.process_bar(
                df=test_case['data'],
                current_index=test_case['index'],
                fibonacci_levels=test_case['fibonacci_levels'],
                abc_patterns=test_case['abc_patterns'],
                symbol=test_case['symbol'],
                timeframe=test_case['timeframe']
            )
            
            # Test new engine with S&D disabled
            new_result = new_engine.process_bar(
                df=test_case['data'],
                current_index=test_case['index'],
                fibonacci_levels=test_case['fibonacci_levels'],
                abc_patterns=test_case['abc_patterns'],
                symbol=test_case['symbol'],
                timeframe=test_case['timeframe']
            )
            
            # Results should be identical
            assert abs(legacy_result.total_score - new_result.total_score) < 0.001
            assert len(legacy_result.factors) == len(new_result.factors)
            
            # Verify no S&D factors when disabled
            sd_factors = [f for f in new_result.factors 
                         if f.factor_type == ConfluenceFactorType.SUPPLY_DEMAND]
            assert len(sd_factors) == 0, "No S&D factors when disabled"
    
    def test_fibonacci_calculations_unaffected(self):
        """
        Test Fibonacci calculations produce identical results.
        
        Success Criteria:
        - Same Fibonacci levels calculated
        - Same retracement percentages
        - Same extension levels
        - Performance unchanged
        """
        import time
        
        # Load baseline Fibonacci results
        baseline_fib_results = self._load_baseline_fibonacci_results()
        
        # Setup systems
        legacy_calculator = FibonacciCalculator()
        new_system = self._create_integrated_system()
        
        for test_case in baseline_fib_results:
            # Legacy calculation
            start_time = time.perf_counter()
            legacy_levels = legacy_calculator.calculate_retracement_levels(
                swing_high=test_case['swing_high'],
                swing_low=test_case['swing_low']
            )
            legacy_time = (time.perf_counter() - start_time) * 1000
            
            # New system calculation
            start_time = time.perf_counter()
            new_levels = new_system.fibonacci_calculator.calculate_retracement_levels(
                swing_high=test_case['swing_high'],
                swing_low=test_case['swing_low']
            )
            new_time = (time.perf_counter() - start_time) * 1000
            
            # Results should be identical
            assert len(legacy_levels) == len(new_levels)
            for i, (legacy_level, new_level) in enumerate(zip(legacy_levels, new_levels)):
                assert abs(legacy_level - new_level) < 0.00001, f"Fibonacci level {i} differs"
            
            # Performance should not degrade
            assert new_time <= legacy_time * 1.1, f"Performance degraded: {new_time:.2f}ms > {legacy_time:.2f}ms"
    
    def test_research_dashboard_unchanged(self):
        """
        Test research dashboard existing functionality unchanged.
        
        Success Criteria:
        - All existing endpoints work
        - Chart rendering unchanged
        - WebSocket updates work
        - UI controls functional
        """
        # Test existing API endpoints
        test_client = TestClient(create_app_with_sd_integration())
        
        # Test fractal endpoint (existing)
        response = test_client.get("/api/fractals/EURUSD/M1")
        assert response.status_code == 200
        
        # Test swing endpoint (existing)
        response = test_client.get("/api/swings/EURUSD/M1")
        assert response.status_code == 200
        
        # Test fibonacci endpoint (existing)
        response = test_client.get("/api/fibonacci/EURUSD/M1")
        assert response.status_code == 200
        
        # Test confluence endpoint (existing, should work with S&D disabled)
        response = test_client.get("/api/confluence/EURUSD/M1?enable_supply_demand=false")
        assert response.status_code == 200
        
        confluence_data = response.json()
        # Should not contain S&D factors when disabled
        for zone in confluence_data:
            sd_factors = [f for f in zone.get('factors', []) 
                         if f.get('factor_type') == 'supply_demand']
            assert len(sd_factors) == 0
    
    def test_database_schema_migration_safety(self):
        """
        Test database schema migration is safe and reversible.
        
        Success Criteria:
        - Existing tables unchanged
        - New tables added cleanly
        - Data migration successful
        - Rollback works correctly
        """
        # This would be run against a copy of production database
        
        # Verify baseline schema
        baseline_tables = self._get_database_tables()
        baseline_data = self._export_critical_data()
        
        # Apply S&D migration
        self._apply_supply_demand_migration()
        
        # Verify migration results
        migrated_tables = self._get_database_tables()
        
        # Check existing tables unchanged
        for table in baseline_tables:
            assert table in migrated_tables, f"Existing table {table} missing after migration"
            
            # Verify table structure unchanged
            baseline_schema = self._get_table_schema(table)
            migrated_schema = self._get_table_schema(table)
            assert baseline_schema == migrated_schema, f"Table {table} schema changed"
        
        # Check new tables added
        expected_new_tables = [
            'supply_demand_zones',
            'supply_demand_zone_tests',
            'supply_demand_zone_flips',
            'supply_demand_zone_performance'
        ]
        
        for table in expected_new_tables:
            assert table in migrated_tables, f"New table {table} not created"
        
        # Verify data integrity
        migrated_data = self._export_critical_data()
        assert baseline_data == migrated_data, "Existing data corrupted during migration"
        
        # Test rollback
        self._rollback_supply_demand_migration()
        rolled_back_tables = self._get_database_tables()
        
        assert baseline_tables == rolled_back_tables, "Rollback did not restore original schema"
```

---

## 8. Test Data Specifications

### 8.1 Test Data Requirements

#### 8.1.1 Synthetic Test Data

```python
class TestDataFactory:
    """
    Factory for creating synthetic test data with known patterns.
    
    Provides:
    - OHLC data with embedded S&D patterns
    - Known zone locations and properties
    - Predictable test outcomes
    - Performance testing datasets
    """
    
    @staticmethod
    def create_demand_zone_pattern(
        base_candles: int = 5,
        breakout_candles: int = 4,
        base_range_pips: float = 10,
        breakout_magnitude_atr: float = 3.0
    ) -> pd.DataFrame:
        """
        Create synthetic OHLC data with embedded demand zone pattern.
        
        Args:
            base_candles: Number of consolidation candles
            breakout_candles: Number of breakout candles
            base_range_pips: Range of consolidation in pips
            breakout_magnitude_atr: Breakout size in ATR multiples
            
        Returns:
            DataFrame with OHLC data containing known demand zone
        """
        
    @staticmethod
    def create_supply_zone_pattern(
        base_candles: int = 5,
        breakout_candles: int = 4,
        base_range_pips: float = 10,
        breakout_magnitude_atr: float = 3.0
    ) -> pd.DataFrame:
        """Create synthetic supply zone pattern"""
        
    @staticmethod
    def create_zone_test_pattern(
        zone: SupplyDemandZone,
        test_type: str = 'bounce',
        rejection_strength: float = 0.8
    ) -> pd.DataFrame:
        """Create price data testing a zone with known outcome"""
        
    @staticmethod
    def create_zone_flip_pattern(
        original_zone: SupplyDemandZone
    ) -> pd.DataFrame:
        """Create price data showing zone flip behavior"""
        
    @staticmethod
    def create_performance_dataset(
        bars: int = 1000,
        zones_count: int = 20,
        symbol: str = 'EURUSD'
    ) -> pd.DataFrame:
        """Create large dataset for performance testing"""
```

#### 8.1.2 Real Market Data

```python
class RealMarketDataProvider:
    """
    Provider for real market data with known S&D patterns.
    
    Provides:
    - Historical data with manually identified zones
    - Validation data for accuracy testing
    - Performance data for benchmarking
    """
    
    @staticmethod
    def load_validated_zones_data(
        symbol: str,
        timeframe: str,
        date_range: tuple
    ) -> Tuple[pd.DataFrame, List[SupplyDemandZone]]:
        """
        Load real market data with manually validated zones.
        
        Returns:
            Tuple of (OHLC data, validated zones list)
        """
        
    @staticmethod
    def load_confluence_test_data() -> List[dict]:
        """Load real data for confluence testing"""
        
    @staticmethod
    def load_performance_benchmark_data() -> pd.DataFrame:
        """Load large real dataset for performance testing"""
```

---

## 9. Test Execution Specifications

### 9.1 Test Runner Configuration

#### 9.1.1 Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test markers
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    regression: Regression tests
    slow: Slow running tests
    database: Tests requiring database
    api: API endpoint tests
    e2e: End-to-end tests

# Test output
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src/analysis/supply_demand
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=95

# Test discovery
minversion = 6.0
```

#### 9.1.2 Test Categories and Execution

```bash
# Run all tests
pytest

# Run by category
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m performance    # Performance tests only
pytest -m regression     # Regression tests only

# Run specific test files
pytest tests/unit/test_base_candle_detection.py
pytest tests/integration/test_confluence_integration.py

# Run with coverage
pytest --cov=src/analysis/supply_demand --cov-report=html

# Run performance tests with benchmarking
pytest -m performance --benchmark-only

# Run tests in parallel
pytest -n auto  # Requires pytest-xdist
```

### 9.2 Continuous Integration Configuration

#### 9.2.1 GitHub Actions Workflow

```yaml
name: Supply & Demand Tests

on:
  push:
    branches: [ main, develop ]
    paths: 
      - 'src/analysis/supply_demand/**'
      - 'tests/**'
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_trading_bot
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark
    
    - name: Run unit tests
      run: pytest -m unit --cov=src/analysis/supply_demand
    
    - name: Run integration tests
      run: pytest -m integration
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost/test_trading_bot
    
    - name: Run performance tests
      run: pytest -m performance --benchmark-json=benchmark.json
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Performance regression check
      run: |
        python scripts/check_performance_regression.py benchmark.json
```

---

## 10. Test Success Criteria Summary

### 10.1 Pass/Fail Criteria

#### 10.1.1 Unit Tests
- **Coverage**: >95% code coverage
- **Performance**: All components meet individual timing requirements
- **Accuracy**: Algorithm outputs match expected results within tolerance
- **Edge Cases**: All edge cases handled gracefully

#### 10.1.2 Integration Tests
- **Compatibility**: Existing functionality unchanged
- **Data Flow**: End-to-end data flow works correctly
- **Performance**: Total system impact <100ms
- **Database**: All CRUD operations work correctly

#### 10.1.3 Performance Tests
- **Zone Detection**: <50ms for 1000 bars
- **Rectangle Drawing**: <30ms for 100 zones
- **Confluence Calculation**: <20ms per calculation
- **Database Queries**: <10ms per query
- **Memory Usage**: <10MB for standard operations

#### 10.1.4 API Tests
- **Response Time**: <100ms for API endpoints
- **Data Validation**: All inputs/outputs validated
- **Error Handling**: Proper HTTP status codes and error messages
- **Documentation**: API matches documented specifications

### 10.2 Quality Gates

#### 10.2.1 Pre-Commit Checks
- All unit tests pass
- Code coverage >95%
- Performance benchmarks within limits
- Code style compliance (Black, flake8)

#### 10.2.2 Pre-Merge Checks
- All test categories pass
- Integration tests pass
- Performance regression check
- Documentation updated

#### 10.2.3 Pre-Deployment Checks
- End-to-end tests pass
- Database migration tested
- Backward compatibility verified
- Load testing completed

---

**Document Status**: Complete - Ready for Implementation
**Next Phase**: Code Implementation Following TDD Methodology
**Test Coverage Target**: >95% for all components
**Performance Budget**: <100ms total additional overhead to existing system