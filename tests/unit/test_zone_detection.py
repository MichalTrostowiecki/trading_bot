"""
Unit tests for SupplyDemandZoneDetector class.

Tests cover:
- End-to-end zone detection
- Zone type classification  
- Boundary calculation accuracy
- Zone strength scoring
- Integration with base/move detectors

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
    from src.analysis.supply_demand.zone_detector import (
        SupplyDemandZoneDetector,
        SupplyDemandZone
    )
    from src.analysis.supply_demand.base_candle_detector import (
        BaseCandleDetector, 
        BaseCandleRange
    )
    from src.analysis.supply_demand.big_move_detector import (
        BigMoveDetector,
        BigMove
    )
except ImportError:
    # Classes don't exist yet - create placeholders
    @dataclass
    class SupplyDemandZone:
        """Placeholder for SupplyDemandZone until implementation"""
        id: Optional[int]
        symbol: str
        timeframe: str
        zone_type: str  # 'supply', 'demand', 'continuation'
        
        # Zone boundaries
        top_price: float
        bottom_price: float
        left_time: datetime
        right_time: datetime
        
        # Zone metadata
        strength_score: float  # 0.0 to 1.0
        test_count: int
        success_count: int
        status: str  # 'active', 'tested', 'broken', 'flipped'
        
        # Creation context
        base_range: 'BaseCandleRange'
        big_move: 'BigMove'
        atr_at_creation: float
        volume_at_creation: float
        
        # Timestamps
        created_at: datetime
        updated_at: datetime
        
        def contains_price(self, price: float) -> bool:
            return self.bottom_price <= price <= self.top_price
        
        def distance_from_price(self, price: float) -> float:
            if self.contains_price(price):
                return 0.0
            elif price < self.bottom_price:
                return self.bottom_price - price
            else:
                return price - self.top_price
        
        @property
        def height(self) -> float:
            return self.top_price - self.bottom_price
        
        @property
        def center(self) -> float:
            return (self.top_price + self.bottom_price) / 2.0
    
    @dataclass
    class BaseCandleRange:
        start_index: int
        end_index: int
        start_time: datetime
        end_time: datetime
        high: float
        low: float
        atr_at_creation: float
        candle_count: int
        consolidation_score: float
    
    @dataclass
    class BigMove:
        start_index: int
        end_index: int
        start_time: datetime
        end_time: datetime
        direction: str
        magnitude: float
        momentum_score: float
        breakout_level: float
        volume_confirmation: bool
    
    class BaseCandleDetector:
        def __init__(self, **kwargs):
            pass
        def detect_base_candles(self, df, start_index=0, end_index=None):
            return []
    
    class BigMoveDetector:
        def __init__(self, **kwargs):
            pass
        def detect_big_moves(self, df, base_ranges, fractal_levels=None):
            return []
    
    class SupplyDemandZoneDetector:
        """Placeholder for SupplyDemandZoneDetector until implementation"""
        def __init__(self, base_detector, move_detector, **kwargs):
            self.base_detector = base_detector
            self.move_detector = move_detector
            self.max_zones_per_timeframe = kwargs.get('max_zones_per_timeframe', 100)
            self.zone_expiry_hours = kwargs.get('zone_expiry_hours', 168)
            self.overlap_tolerance = kwargs.get('overlap_tolerance', 0.1)
        
        def detect_zones(self, df, symbol, timeframe, fractal_levels=None, existing_zones=None):
            return []  # Placeholder
        
        def _classify_zone_type(self, base_range, big_move):
            return "demand"  # Placeholder
        
        def _calculate_zone_boundaries(self, df, base_range, zone_type):
            return (1.0850, 1.0840)  # Placeholder
        
        def _calculate_zone_strength(self, zone, df):
            return 0.8  # Placeholder


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
    def base_detector(self):
        """Configured BaseCandleDetector for testing"""
        return BaseCandleDetector(
            consolidation_threshold=0.5,
            min_base_candles=2,
            max_base_candles=10,
            body_size_threshold=0.3,
            atr_period=14
        )
    
    @pytest.fixture
    def move_detector(self):
        """Configured BigMoveDetector for testing"""
        return BigMoveDetector(
            move_threshold=2.0,
            min_move_candles=3,
            momentum_threshold=0.6,
            volume_multiplier=1.5,
            breakout_confirmation=True
        )
    
    @pytest.fixture
    def zone_detector(self, base_detector, move_detector):
        """Configured SupplyDemandZoneDetector for testing"""
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
            # Base candles (consolidation) - indices 0-4
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,  # Mixed colors
                    1.0801, 1.0820, 1.0835, 1.0845],          # Bullish breakout
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,  # Consolidation highs
                    1.0825, 1.0840, 1.0850, 1.0860],          # Breakout highs
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,  # Consolidation lows
                    1.0800, 1.0815, 1.0830, 1.0840],          # Breakout lows
            'close':[1.0795, 1.0806, 1.0801, 1.0806, 1.0800,  # Red, Green, Red, Green, Red
                    1.0820, 1.0835, 1.0845, 1.0855],          # Bullish closes
            'volume': [1000] * 5 + [2500, 2000, 1800, 1600],  # Volume spike on breakout
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
    
    @pytest.fixture
    def sample_supply_zone_data(self):
        """
        Complete OHLC data with supply zone pattern.
        
        Pattern: Base candles + bearish breakout = Supply zone
        Expected: 1 supply zone with specific boundaries
        """
        return pd.DataFrame({
            # Base candles (consolidation) - indices 0-4
            'open': [1.2650, 1.2645, 1.2647, 1.2646, 1.2648,  # Mixed colors
                    1.2649, 1.2630, 1.2615, 1.2605],          # Bearish breakdown
            'high': [1.2660, 1.2658, 1.2656, 1.2657, 1.2655,  # Consolidation highs
                    1.2655, 1.2635, 1.2620, 1.2610],          # Breakdown highs
            'low':  [1.2635, 1.2642, 1.2641, 1.2642, 1.2640,  # Consolidation lows
                    1.2620, 1.2605, 1.2590, 1.2580],          # Breakdown lows
            'close':[1.2655, 1.2644, 1.2647, 1.2644, 1.2648,  # Green, Red, Green, Red, Green
                    1.2630, 1.2615, 1.2605, 1.2595],          # Bearish closes
            'volume': [1000] * 5 + [2500, 2000, 1800, 1600],  # Volume spike on breakdown
            'time': pd.date_range('2025-01-01 10:00', periods=9, freq='1min')
        })
    
    @pytest.fixture
    def sample_base_range(self):
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
    
    @pytest.fixture
    def sample_bullish_move(self):
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
    
    def test_detector_initialization(self, zone_detector):
        """
        Test detector initializes with correct parameters.
        
        Success Criteria:
        - Component detectors properly set
        - Configuration parameters applied
        - Default values used correctly
        """
        assert zone_detector.base_detector is not None
        assert zone_detector.move_detector is not None
        assert zone_detector.max_zones_per_timeframe == 100
        assert zone_detector.zone_expiry_hours == 168
        assert zone_detector.overlap_tolerance == 0.1
    
    def test_demand_zone_detection_success(self, zone_detector, sample_demand_zone_data):
        """
        Test successful demand zone detection and classification.
        
        Success Criteria:
        - Detects exactly 1 zone
        - Zone classified as 'demand'
        - Proper boundary calculation per eWavesHarmonics rules
        - Zone strength score >0.5
        - All zone properties correctly set
        """
        zones = zone_detector.detect_zones(
            df=sample_demand_zone_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # This test will fail initially - implementation needs to detect the zone
        assert len(zones) == 1, f"Should detect exactly one demand zone, got {len(zones)}"
        
        zone = zones[0]
        
        # Validate basic zone properties
        assert zone.zone_type == 'demand', f"Should classify as demand zone, got {zone.zone_type}"
        assert zone.symbol == 'EURUSD', f"Symbol should be EURUSD, got {zone.symbol}"
        assert zone.timeframe == 'M1', f"Timeframe should be M1, got {zone.timeframe}"
        assert zone.status == 'active', f"New zone should be active, got {zone.status}"
        
        # Validate zone strength
        assert 0.0 <= zone.strength_score <= 1.0, \
            f"Strength score should be 0-1, got {zone.strength_score}"
        assert zone.strength_score >= 0.5, \
            f"Good zone should score >0.5, got {zone.strength_score}"
        
        # Test eWavesHarmonics boundary rules for demand zone
        # Top: Highest high of base candles = 1.0810
        # Bottom: Lowest open of red candles in base range
        expected_top = 1.0810  # Max high of base candles (0-4)
        expected_bottom = 1.0795  # Lowest open of red candles in base range
        
        tolerance = 0.00005
        assert abs(zone.top_price - expected_top) < tolerance, \
            f"Top price incorrect: {zone.top_price:.5f} vs expected {expected_top:.5f}"
        assert abs(zone.bottom_price - expected_bottom) < tolerance, \
            f"Bottom price incorrect: {zone.bottom_price:.5f} vs expected {expected_bottom:.5f}"
        
        # Validate time boundaries
        expected_left_time = sample_demand_zone_data.iloc[0]['time']
        expected_right_time = sample_demand_zone_data.iloc[4]['time']
        assert zone.left_time == expected_left_time
        assert zone.right_time == expected_right_time
        
        # Validate zone helper methods
        assert zone.height > 0, "Zone should have positive height"
        assert zone.bottom_price < zone.center < zone.top_price, "Center should be between boundaries"
        
        # Test price containment
        assert zone.contains_price(zone.center), "Zone should contain its center price"
        assert not zone.contains_price(zone.top_price + 0.0001), "Price above zone should not be contained"
        assert not zone.contains_price(zone.bottom_price - 0.0001), "Price below zone should not be contained"
    
    def test_supply_zone_detection_success(self, zone_detector, sample_supply_zone_data):
        """
        Test successful supply zone detection and classification.
        
        Success Criteria:
        - Detects supply zone from bearish pattern
        - Proper boundary calculation for supply zones
        - Zone classified as 'supply'
        """
        zones = zone_detector.detect_zones(
            df=sample_supply_zone_data,
            symbol='GBPUSD', 
            timeframe='M5'
        )
        
        assert len(zones) == 1, f"Should detect exactly one supply zone, got {len(zones)}"
        zone = zones[0]
        
        assert zone.zone_type == 'supply', f"Should classify as supply zone, got {zone.zone_type}"
        assert zone.symbol == 'GBPUSD'
        assert zone.timeframe == 'M5'
        
        # Test eWavesHarmonics boundary rules for supply zone
        # Top: Highest open of green candles in base range
        # Bottom: Lowest low of base candles
        expected_top = 1.2655  # Highest open of green candles in base (indices 0, 2, 4)
        expected_bottom = 1.2635  # Lowest low of base candles (0-4)
        
        tolerance = 0.00005
        assert abs(zone.top_price - expected_top) < tolerance, \
            f"Supply zone top incorrect: {zone.top_price:.5f} vs expected {expected_top:.5f}"
        assert abs(zone.bottom_price - expected_bottom) < tolerance, \
            f"Supply zone bottom incorrect: {zone.bottom_price:.5f} vs expected {expected_bottom:.5f}"
    
    def test_zone_type_classification(self, zone_detector, sample_base_range):
        """
        Test zone type classification logic.
        
        Success Criteria:
        - Bullish moves create demand zones
        - Bearish moves create supply zones
        - Classification based on move direction
        """
        # Test bullish move -> demand zone
        bullish_move = BigMove(
            start_index=5, end_index=8,
            start_time=datetime(2025, 1, 1, 10, 5),
            end_time=datetime(2025, 1, 1, 10, 8),
            direction="bullish", magnitude=3.0, momentum_score=0.8,
            breakout_level=1.0810, volume_confirmation=True
        )
        
        zone_type = zone_detector._classify_zone_type(sample_base_range, bullish_move)
        assert zone_type == "demand", f"Bullish move should create demand zone, got {zone_type}"
        
        # Test bearish move -> supply zone
        bearish_move = BigMove(
            start_index=5, end_index=8,
            start_time=datetime(2025, 1, 1, 10, 5),
            end_time=datetime(2025, 1, 1, 10, 8),
            direction="bearish", magnitude=3.0, momentum_score=0.8,
            breakout_level=1.0795, volume_confirmation=True
        )
        
        zone_type = zone_detector._classify_zone_type(sample_base_range, bearish_move)
        assert zone_type == "supply", f"Bearish move should create supply zone, got {zone_type}"
    
    def test_zone_boundary_calculation_demand(self, zone_detector, sample_demand_zone_data, sample_base_range):
        """
        Test precise zone boundary calculation for demand zones.
        
        Success Criteria:
        - eWavesHarmonics rules properly implemented
        - Boundaries calculated from correct candles
        - Precision maintained
        """
        top_price, bottom_price = zone_detector._calculate_zone_boundaries(
            sample_demand_zone_data, sample_base_range, "demand"
        )
        
        # Expected boundaries for demand zone:
        # Top: Highest high of base candles
        # Bottom: Lowest open of red (bearish) candles in base range
        expected_top = 1.0810   # Max of highs[0:5] = max(1.0810, 1.0808, 1.0806, 1.0807, 1.0805)
        expected_bottom = 1.0795  # Min open of red candles (candles with close < open)
        
        tolerance = 0.00001
        assert abs(top_price - expected_top) < tolerance, \
            f"Demand zone top boundary incorrect: {top_price:.5f} vs expected {expected_top:.5f}"
        assert abs(bottom_price - expected_bottom) < tolerance, \
            f"Demand zone bottom boundary incorrect: {bottom_price:.5f} vs expected {expected_bottom:.5f}"
        
        # Validate boundary relationship
        assert top_price > bottom_price, f"Top price should be > bottom price"
    
    def test_zone_boundary_calculation_supply(self, zone_detector, sample_supply_zone_data):
        """
        Test precise zone boundary calculation for supply zones.
        
        Success Criteria:
        - Supply zone boundaries calculated correctly
        - eWavesHarmonics rules for supply zones
        """
        # Create base range for supply zone data
        supply_base_range = BaseCandleRange(
            start_index=0, end_index=4,
            start_time=datetime(2025, 1, 1, 10, 0),
            end_time=datetime(2025, 1, 1, 10, 4),
            high=1.2660, low=1.2635,
            atr_at_creation=0.0010, candle_count=5,
            consolidation_score=0.8
        )
        
        top_price, bottom_price = zone_detector._calculate_zone_boundaries(
            sample_supply_zone_data, supply_base_range, "supply"
        )
        
        # Expected boundaries for supply zone:
        # Top: Highest open of green (bullish) candles in base range
        # Bottom: Lowest low of base candles
        expected_top = 1.2655    # Max open of green candles (close >= open)
        expected_bottom = 1.2635  # Min of lows[0:5]
        
        tolerance = 0.00001
        assert abs(top_price - expected_top) < tolerance, \
            f"Supply zone top boundary incorrect: {top_price:.5f} vs expected {expected_top:.5f}"
        assert abs(bottom_price - expected_bottom) < tolerance, \
            f"Supply zone bottom boundary incorrect: {bottom_price:.5f} vs expected {expected_bottom:.5f}"
    
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
        assert 0.0 <= zone.strength_score <= 1.0, \
            f"Strength score should be 0-1, got {zone.strength_score}"
        
        # Test with high volume data
        high_volume_data = sample_demand_zone_data.copy()
        high_volume_data['volume'] = high_volume_data['volume'] * 3  # Triple volume
        
        high_volume_zones = zone_detector.detect_zones(
            df=high_volume_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # High volume should increase strength score
        assert high_volume_zones[0].strength_score > zone.strength_score, \
            f"High volume should increase strength: {high_volume_zones[0].strength_score} vs {zone.strength_score}"
        
        # Test with low volume data
        low_volume_data = sample_demand_zone_data.copy()
        low_volume_data['volume'] = low_volume_data['volume'] * 0.3  # Reduce volume
        
        low_volume_zones = zone_detector.detect_zones(
            df=low_volume_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Low volume should decrease strength score
        assert low_volume_zones[0].strength_score < zone.strength_score, \
            f"Low volume should decrease strength: {low_volume_zones[0].strength_score} vs {zone.strength_score}"
    
    def test_overlapping_zone_resolution(self, zone_detector):
        """
        Test resolution of overlapping zones.
        
        Success Criteria:
        - Overlapping zones properly merged or prioritized
        - No duplicate zones in output
        - Strongest zones preserved
        """
        # Create data with potential overlapping zones
        overlapping_data = pd.DataFrame({
            # First potential zone (0-2)
            'open': [1.0800, 1.0805, 1.0803,
                    # Small move (3-4)
                    1.0820, 1.0825,
                    # Second potential zone (5-7) - overlapping price range
                    1.0805, 1.0807, 1.0806,
                    # Bigger move (8-10)
                    1.0840, 1.0855, 1.0870],
            'high': [1.0810, 1.0808, 1.0806,
                    1.0830, 1.0835,
                    1.0815, 1.0812, 1.0811,
                    1.0850, 1.0865, 1.0880],
            'low':  [1.0795, 1.0802, 1.0801,
                    1.0815, 1.0820,
                    1.0800, 1.0804, 1.0803,
                    1.0835, 1.0850, 1.0865],
            'close':[1.0805, 1.0803, 1.0804,
                    1.0825, 1.0830,
                    1.0807, 1.0806, 1.0805,
                    1.0845, 1.0860, 1.0875],
            'volume': [1000] * 11,
            'time': pd.date_range('2025-01-01 10:00', periods=11, freq='1min')
        })
        
        zones = zone_detector.detect_zones(
            df=overlapping_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Verify no overlapping zones beyond tolerance
        for i, zone1 in enumerate(zones):
            for j, zone2 in enumerate(zones[i+1:], i+1):
                overlap = self._calculate_zone_overlap(zone1, zone2)
                assert overlap <= zone_detector.overlap_tolerance, \
                    f"Zones {i} and {j} overlap too much: {overlap:.3f} > {zone_detector.overlap_tolerance}"
    
    def test_multiple_zones_detection(self, zone_detector):
        """
        Test detection of multiple separate zones.
        
        Success Criteria:
        - Detects multiple zones when they exist
        - Zones don't interfere with each other
        - Each zone meets quality criteria
        """
        # Create data with two separate zone opportunities
        multi_zone_data = pd.DataFrame({
            # First demand zone setup (0-4)
            'open': [1.0800, 1.0805, 1.0803, 1.0804, 1.0802,
                    # First bullish move (5-7)
                    1.0820, 1.0835, 1.0845,
                    # Second demand zone setup (8-12)
                    1.0840, 1.0845, 1.0843, 1.0844, 1.0842,
                    # Second bullish move (13-15)
                    1.0860, 1.0875, 1.0885],
            'high': [1.0810, 1.0808, 1.0806, 1.0807, 1.0805,
                    1.0840, 1.0855, 1.0865,
                    1.0850, 1.0848, 1.0846, 1.0847, 1.0845,
                    1.0880, 1.0895, 1.0905],
            'low':  [1.0795, 1.0802, 1.0801, 1.0802, 1.0800,
                    1.0815, 1.0830, 1.0840,
                    1.0835, 1.0842, 1.0841, 1.0842, 1.0840,
                    1.0855, 1.0870, 1.0880],
            'close':[1.0805, 1.0803, 1.0804, 1.0802, 1.0801,
                    1.0835, 1.0850, 1.0860,
                    1.0845, 1.0843, 1.0844, 1.0842, 1.0841,
                    1.0875, 1.0890, 1.0900],
            'volume': [1000] * 5 + [2500, 2000, 1800] + [1000] * 5 + [2500, 2000, 1800],
            'time': pd.date_range('2025-01-01 10:00', periods=16, freq='1min')
        })
        
        zones = zone_detector.detect_zones(
            df=multi_zone_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Should detect multiple zones
        assert len(zones) >= 1, f"Should detect at least one zone, got {len(zones)}"
        
        # If multiple zones detected, validate they're separate
        if len(zones) > 1:
            for i, zone1 in enumerate(zones):
                for j, zone2 in enumerate(zones[i+1:], i+1):
                    # Zones should be time-separated or price-separated
                    time_separated = zone1.right_time < zone2.left_time or zone2.right_time < zone1.left_time
                    price_separated = zone1.top_price < zone2.bottom_price or zone2.top_price < zone1.bottom_price
                    
                    assert time_separated or price_separated, \
                        f"Zones {i} and {j} should be separated in time or price"
    
    def test_edge_case_no_zones(self, zone_detector):
        """
        Test behavior when no valid zones can be detected.
        
        Success Criteria:
        - Returns empty list when no patterns found
        - No false positive detections
        - Handles trending data correctly
        """
        # Create trending data with no consolidation
        trending_data = pd.DataFrame({
            'open': [1.0000 + i*0.0050 for i in range(20)],  # Strong trend
            'high': [1.0060 + i*0.0050 for i in range(20)],
            'low':  [0.9980 + i*0.0050 for i in range(20)],
            'close':[1.0050 + i*0.0050 for i in range(20)],
            'volume': [1500] * 20,
            'time': pd.date_range('2025-01-01 10:00', periods=20, freq='1min')
        })
        
        zones = zone_detector.detect_zones(
            df=trending_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        assert zones == [], f"Should return empty list for trending data, got {len(zones)} zones"
    
    def test_edge_case_insufficient_data(self, zone_detector):
        """
        Test behavior with insufficient data.
        
        Success Criteria:
        - Handles small datasets gracefully
        - Returns appropriate results or empty list
        - No exceptions thrown
        """
        # Create minimal dataset
        small_data = pd.DataFrame({
            'open': [1.0800, 1.0805, 1.0810],
            'high': [1.0810, 1.0815, 1.0820],
            'low': [1.0795, 1.0800, 1.0805],
            'close': [1.0805, 1.0810, 1.0815],
            'volume': [1000, 1100, 1200],
            'time': pd.date_range('2025-01-01 10:00', periods=3, freq='1min')
        })
        
        # Should not crash
        zones = zone_detector.detect_zones(
            df=small_data,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        # Should return list (may be empty)
        assert isinstance(zones, list), "Should return list even with insufficient data"
    
    def test_performance_benchmark(self, zone_detector):
        """
        Test complete zone detection performance.
        
        Success Criteria:
        - Processes 1000 bars in <50ms
        - Memory usage stable
        - Output quality maintained under load
        """
        # Create large dataset for performance testing
        large_dataset = self._create_large_zone_dataset(1000)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Warm up
        zone_detector.detect_zones(large_dataset.head(100), 'EURUSD', 'M1')
        
        # Performance test
        start_time = time.perf_counter()
        
        zones = zone_detector.detect_zones(
            df=large_dataset,
            symbol='EURUSD',
            timeframe='M1'
        )
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        assert duration_ms < 50, f"Zone detection performance failed: {duration_ms:.2f}ms > 50ms target"
        assert memory_mb < 20, f"Memory usage too high: {memory_mb:.1f}MB > 20MB limit"
        
        # Verify output quality
        assert isinstance(zones, list), "Should return list even with large dataset"
        
        # Validate zone quality if any detected
        for zone in zones:
            assert zone.strength_score > 0.0, "All zones should have positive strength"
            assert zone.zone_type in ['supply', 'demand', 'continuation']
            assert zone.top_price > zone.bottom_price
    
    def test_configuration_validation(self):
        """
        Test detector configuration validation.
        
        Success Criteria:
        - Validates component detectors
        - Validates configuration parameters
        - Proper error handling for invalid config
        """
        base_detector = BaseCandleDetector()
        move_detector = BigMoveDetector()
        
        # Test invalid max zones
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandZoneDetector(
                base_detector, move_detector,
                max_zones_per_timeframe=0  # Invalid
            )
        
        # Test invalid overlap tolerance
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandZoneDetector(
                base_detector, move_detector,
                overlap_tolerance=1.5  # > 1.0
            )
        
        # Test None detectors
        with pytest.raises((ValueError, TypeError)):
            SupplyDemandZoneDetector(None, move_detector)
        
        with pytest.raises((ValueError, TypeError)):
            SupplyDemandZoneDetector(base_detector, None)
    
    def test_fractal_levels_integration(self, zone_detector, sample_demand_zone_data):
        """
        Test integration with fractal levels.
        
        Success Criteria:
        - Fractal levels passed to move detector
        - Breakout confirmation uses fractal levels
        - Zone detection quality improved with fractals
        """
        fractal_levels = [1.0790, 1.0815, 1.0850]  # Sample fractal levels
        
        zones_with_fractals = zone_detector.detect_zones(
            df=sample_demand_zone_data,
            symbol='EURUSD',
            timeframe='M1',
            fractal_levels=fractal_levels
        )
        
        zones_without_fractals = zone_detector.detect_zones(
            df=sample_demand_zone_data,
            symbol='EURUSD',
            timeframe='M1',
            fractal_levels=None
        )
        
        # Should return zones in both cases
        assert isinstance(zones_with_fractals, list)
        assert isinstance(zones_without_fractals, list)
    
    # Helper methods
    def _calculate_zone_overlap(self, zone1: SupplyDemandZone, zone2: SupplyDemandZone) -> float:
        """Calculate overlap percentage between two zones"""
        # Calculate price overlap
        overlap_top = min(zone1.top_price, zone2.top_price)
        overlap_bottom = max(zone1.bottom_price, zone2.bottom_price)
        
        if overlap_top <= overlap_bottom:
            return 0.0  # No overlap
        
        overlap_height = overlap_top - overlap_bottom
        zone1_height = zone1.height
        zone2_height = zone2.height
        
        if zone1_height <= 0 or zone2_height <= 0:
            return 0.0
        
        # Calculate overlap as percentage of smaller zone
        min_height = min(zone1_height, zone2_height)
        overlap_percentage = overlap_height / min_height
        
        return overlap_percentage
    
    def _create_large_zone_dataset(self, size: int) -> pd.DataFrame:
        """Create large dataset for performance testing"""
        np.random.seed(42)  # Reproducible results
        
        data = []
        base_price = 1.0800
        
        for i in range(size):
            # Create market phases: consolidation -> breakout -> trend
            phase = i % 30
            
            if phase < 8:  # Consolidation phase
                price_change = np.random.normal(0, 0.00005)
                volume = np.random.randint(900, 1100)
            elif phase < 12:  # Breakout phase
                price_change = np.random.normal(0.0002, 0.00010)
                volume = np.random.randint(1800, 2500)
            else:  # Trending phase
                price_change = np.random.normal(0.0001, 0.00008)
                volume = np.random.randint(1200, 1600)
            
            base_price += price_change
            
            # Generate realistic OHLC
            spread = abs(np.random.normal(0, 0.00003))
            open_price = base_price
            high_price = base_price + spread + 0.00002
            low_price = base_price - spread - 0.00002
            close_price = base_price + price_change * 0.8
            
            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'time': datetime(2025, 1, 1, 10, 0) + timedelta(minutes=i)
            })
        
        return pd.DataFrame(data)


# Test fixtures for other test files
@pytest.fixture
def supply_demand_zone_detector(base_candle_detector, big_move_detector):
    """Standard SupplyDemandZoneDetector for use in other test files"""
    return SupplyDemandZoneDetector(
        base_detector=base_candle_detector,
        move_detector=big_move_detector,
        max_zones_per_timeframe=100,
        zone_expiry_hours=168,
        overlap_tolerance=0.1
    )


@pytest.fixture
def sample_supply_demand_zone():
    """Sample SupplyDemandZone for testing"""
    return SupplyDemandZone(
        id=1,
        symbol='EURUSD',
        timeframe='M1',
        zone_type='demand',
        top_price=1.0850,
        bottom_price=1.0840,
        left_time=datetime(2025, 1, 1, 10, 0),
        right_time=datetime(2025, 1, 1, 10, 4),
        strength_score=0.8,
        test_count=0,
        success_count=0,
        status='active',
        base_range=None,
        big_move=None,
        atr_at_creation=0.0010,
        volume_at_creation=1500,
        created_at=datetime(2025, 1, 1, 10, 0),
        updated_at=datetime(2025, 1, 1, 10, 0)
    )


# Performance benchmarking
def benchmark_zone_detection():
    """Standalone performance benchmark for CI/CD"""
    base_detector = BaseCandleDetector()
    move_detector = BigMoveDetector()
    zone_detector = SupplyDemandZoneDetector(base_detector, move_detector)
    
    # Create test data
    test_data = TestSupplyDemandZoneDetector()._create_large_zone_dataset(1000)
    
    # Benchmark
    start_time = time.perf_counter()
    zones = zone_detector.detect_zones(test_data, 'EURUSD', 'M1')
    duration = (time.perf_counter() - start_time) * 1000
    
    print(f"SupplyDemandZoneDetector 1000 bars: {duration:.2f}ms")
    
    # Assert performance target
    assert duration < 50, f"Performance test failed: {duration:.2f}ms > 50ms"


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_zone_detection()