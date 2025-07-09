"""
Unit tests for SupplyDemandConfluence class.

Tests cover:
- Integration with existing confluence system
- S&D zone confluence scoring
- Zone proximity calculations
- Zone strength weighting
- Multi-timeframe S&D analysis
- Performance benchmarks

Following TDD methodology - these tests define the expected behavior
before implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time
import tracemalloc

# Import the classes we're testing
try:
    from src.analysis.supply_demand.confluence_integration import (
        SupplyDemandConfluence,
        SDZoneConfluenceScore,
        SDZoneProximity
    )
    from src.analysis.supply_demand.zone_detector import SupplyDemandZone
    from src.analysis.supply_demand.zone_state_manager import ZoneStateManager
    from src.analysis.supply_demand.repository import SupplyDemandRepository
    from src.analysis.supply_demand.base_candle_detector import BaseCandleRange
    from src.analysis.supply_demand.big_move_detector import BigMove
except ImportError:
    # Classes don't exist yet - create placeholders
    @dataclass
    class SDZoneConfluenceScore:
        """Placeholder for SDZoneConfluenceScore until implementation"""
        zone_id: int
        zone_type: str  # 'supply', 'demand'
        proximity_score: float  # 0.0 to 1.0
        strength_score: float   # 0.0 to 1.0
        freshness_score: float  # 0.0 to 1.0
        test_history_score: float  # 0.0 to 1.0
        total_confluence_score: float  # 0.0 to 1.0
        distance_pips: float
        zone_center: float
        zone_boundaries: tuple  # (top, bottom)
        
    @dataclass
    class SDZoneProximity:
        """Placeholder for SDZoneProximity until implementation"""
        zone_id: int
        distance_pips: float
        proximity_score: float  # 1.0 at zone center, decreases with distance
        is_inside_zone: bool
        penetration_percentage: float  # If inside zone
        
    @dataclass
    class SupplyDemandZone:
        """Placeholder for SupplyDemandZone"""
        id: Optional[int]
        symbol: str
        timeframe: str
        zone_type: str
        top_price: float
        bottom_price: float
        left_time: datetime
        right_time: datetime
        strength_score: float
        test_count: int
        success_count: int
        status: str
        base_range: 'BaseCandleRange'
        big_move: 'BigMove'
        atr_at_creation: float
        volume_at_creation: float
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
            
        @property
        def age_hours(self) -> float:
            return (datetime.now() - self.created_at).total_seconds() / 3600
    
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
    
    class SupplyDemandConfluence:
        """Placeholder for SupplyDemandConfluence until implementation"""
        def __init__(self, **kwargs):
            self.proximity_threshold_pips = kwargs.get('proximity_threshold_pips', 50)
            self.min_zone_strength = kwargs.get('min_zone_strength', 0.5)
            self.freshness_weight = kwargs.get('freshness_weight', 0.3)
            self.strength_weight = kwargs.get('strength_weight', 0.4)
            self.test_history_weight = kwargs.get('test_history_weight', 0.3)
            self.multi_timeframe_enabled = kwargs.get('multi_timeframe_enabled', True)
            self.max_zone_age_hours = kwargs.get('max_zone_age_hours', 168)
            
        def calculate_confluence_score(self, price, symbol, timeframes=None):
            return SDZoneConfluenceScore(
                zone_id=1, zone_type="supply", proximity_score=0.8,
                strength_score=0.7, freshness_score=0.6, test_history_score=0.5,
                total_confluence_score=0.65, distance_pips=15.5, zone_center=1.0845,
                zone_boundaries=(1.0850, 1.0840)
            )
            
        def get_nearby_zones(self, price, symbol, timeframe=None, max_distance_pips=None):
            return []
            
        def calculate_zone_proximity(self, zone, price):
            return SDZoneProximity(
                zone_id=zone.id, distance_pips=10.0, proximity_score=0.9,
                is_inside_zone=False, penetration_percentage=0.0
            )
            
        def get_confluence_factors(self, price, symbol, timeframes=None):
            return {
                'supply_zones': [],
                'demand_zones': [],
                'total_confluence_score': 0.0,
                'dominant_zone_type': None
            }
            
        def update_zone_cache(self, zones):
            pass
            
        def get_multi_timeframe_confluence(self, price, symbol, timeframes):
            return {'M1': 0.5, 'M5': 0.6, 'H1': 0.7}


class TestSupplyDemandConfluence:
    """
    Comprehensive unit tests for SupplyDemandConfluence class.
    
    Tests cover:
    - Integration with existing confluence system
    - S&D zone confluence scoring  
    - Zone proximity calculations
    - Zone strength weighting
    - Multi-timeframe S&D analysis
    - Performance benchmarks
    """
    
    @pytest.fixture
    def confluence_system(self):
        """Standard confluence system configuration for testing"""
        return SupplyDemandConfluence(
            proximity_threshold_pips=50,      # 50 pip proximity threshold
            min_zone_strength=0.5,            # Minimum 50% zone strength
            freshness_weight=0.3,             # 30% weight for zone freshness
            strength_weight=0.4,              # 40% weight for zone strength
            test_history_weight=0.3,          # 30% weight for test history
            multi_timeframe_enabled=True,     # Enable multi-TF analysis
            max_zone_age_hours=168            # 1 week maximum age
        )
    
    @pytest.fixture
    def sample_supply_zones(self):
        """Sample supply zones for testing"""
        return [
            SupplyDemandZone(
                id=1, symbol="EURUSD", timeframe="M1", zone_type="supply",
                top_price=1.0850, bottom_price=1.0830, 
                left_time=datetime(2025, 1, 1, 10, 0), right_time=datetime(2025, 1, 1, 10, 5),
                strength_score=0.8, test_count=2, success_count=2, status="active",
                base_range=None, big_move=None, atr_at_creation=0.0010, volume_at_creation=2000,
                created_at=datetime.now() - timedelta(hours=12), updated_at=datetime.now()
            ),
            SupplyDemandZone(
                id=2, symbol="EURUSD", timeframe="M5", zone_type="supply",
                top_price=1.0860, bottom_price=1.0840,
                left_time=datetime(2025, 1, 1, 9, 0), right_time=datetime(2025, 1, 1, 9, 15),
                strength_score=0.6, test_count=1, success_count=0, status="tested",
                base_range=None, big_move=None, atr_at_creation=0.0012, volume_at_creation=1800,
                created_at=datetime.now() - timedelta(hours=24), updated_at=datetime.now()
            )
        ]
    
    @pytest.fixture  
    def sample_demand_zones(self):
        """Sample demand zones for testing"""
        return [
            SupplyDemandZone(
                id=3, symbol="EURUSD", timeframe="M1", zone_type="demand",
                top_price=1.0820, bottom_price=1.0800,
                left_time=datetime(2025, 1, 1, 11, 0), right_time=datetime(2025, 1, 1, 11, 5),
                strength_score=0.75, test_count=1, success_count=1, status="active",
                base_range=None, big_move=None, atr_at_creation=0.0010, volume_at_creation=2200,
                created_at=datetime.now() - timedelta(hours=6), updated_at=datetime.now()
            ),
            SupplyDemandZone(
                id=4, symbol="EURUSD", timeframe="H1", zone_type="demand",
                top_price=1.0825, bottom_price=1.0795,
                left_time=datetime(2025, 1, 1, 8, 0), right_time=datetime(2025, 1, 1, 10, 0),
                strength_score=0.9, test_count=3, success_count=3, status="active",
                base_range=None, big_move=None, atr_at_creation=0.0015, volume_at_creation=3000,
                created_at=datetime.now() - timedelta(hours=48), updated_at=datetime.now()
            )
        ]
    
    def test_confluence_system_initialization(self, confluence_system):
        """
        Test confluence system initializes with correct parameters.
        
        Success Criteria:
        - All parameters set correctly
        - Weights sum to reasonable totals
        - Validation of parameter ranges
        """
        assert confluence_system.proximity_threshold_pips == 50
        assert confluence_system.min_zone_strength == 0.5
        assert confluence_system.freshness_weight == 0.3
        assert confluence_system.strength_weight == 0.4
        assert confluence_system.test_history_weight == 0.3
        assert confluence_system.multi_timeframe_enabled == True
        assert confluence_system.max_zone_age_hours == 168
        
        # Check weight totals (should sum to 1.0)
        weight_sum = (confluence_system.freshness_weight + 
                     confluence_system.strength_weight + 
                     confluence_system.test_history_weight)
        assert abs(weight_sum - 1.0) < 0.01, f"Weights should sum to 1.0, got {weight_sum}"
    
    def test_zone_proximity_calculation_inside_zone(self, confluence_system, sample_supply_zones):
        """
        Test proximity calculation when price is inside zone.
        
        Success Criteria:
        - Detects price inside zone correctly
        - Calculates penetration percentage accurately
        - Proximity score is maximum (1.0) at center
        - Distance in pips calculated correctly
        """
        supply_zone = sample_supply_zones[0]  # 1.0830 - 1.0850
        
        # Test price at zone center
        center_price = 1.0840
        proximity = confluence_system.calculate_zone_proximity(supply_zone, center_price)
        
        assert proximity.is_inside_zone == True
        assert proximity.distance_pips == 0.0  # At center
        assert proximity.proximity_score >= 0.9  # Maximum proximity
        assert 0.4 <= proximity.penetration_percentage <= 0.6  # Around center
        
        # Test price at zone boundary
        boundary_price = 1.0845  # Near top boundary
        boundary_proximity = confluence_system.calculate_zone_proximity(supply_zone, boundary_price)
        
        assert boundary_proximity.is_inside_zone == True
        assert boundary_proximity.distance_pips == 0.0  # Inside zone
        assert boundary_proximity.proximity_score >= 0.7  # High proximity
    
    def test_zone_proximity_calculation_outside_zone(self, confluence_system, sample_supply_zones):
        """
        Test proximity calculation when price is outside zone.
        
        Success Criteria:
        - Detects price outside zone correctly
        - Distance calculation accurate in pips
        - Proximity score decreases with distance
        - Penetration percentage is 0.0
        """
        supply_zone = sample_supply_zones[0]  # 1.0830 - 1.0850
        
        # Test price above zone
        above_price = 1.0870  # 20 pips above zone top
        above_proximity = confluence_system.calculate_zone_proximity(supply_zone, above_price)
        
        assert above_proximity.is_inside_zone == False
        assert above_proximity.distance_pips == 200  # 20 pips = 200 points for EURUSD
        assert above_proximity.proximity_score < 0.5  # Lower proximity due to distance
        assert above_proximity.penetration_percentage == 0.0
        
        # Test price below zone
        below_price = 1.0810  # 20 pips below zone bottom
        below_proximity = confluence_system.calculate_zone_proximity(supply_zone, below_price)
        
        assert below_proximity.is_inside_zone == False
        assert below_proximity.distance_pips == 200  # 20 pips = 200 points
        assert below_proximity.proximity_score < 0.5  # Lower proximity
        assert below_proximity.penetration_percentage == 0.0
    
    def test_confluence_score_calculation_supply_zone(self, confluence_system, sample_supply_zones):
        """
        Test confluence score calculation for supply zones.
        
        Success Criteria:
        - All score components calculated correctly
        - Component weights applied properly
        - Total score within valid range (0.0-1.0)
        - Score reflects zone quality appropriately
        """
        # Update system with zones
        confluence_system.update_zone_cache(sample_supply_zones)
        
        # Test price near strong supply zone
        test_price = 1.0845  # Near first supply zone
        confluence_score = confluence_system.calculate_confluence_score(
            test_price, "EURUSD", ["M1"]
        )
        
        # Verify score components
        assert isinstance(confluence_score, SDZoneConfluenceScore)
        assert confluence_score.zone_type == "supply"
        assert 0.0 <= confluence_score.proximity_score <= 1.0
        assert 0.0 <= confluence_score.strength_score <= 1.0
        assert 0.0 <= confluence_score.freshness_score <= 1.0
        assert 0.0 <= confluence_score.test_history_score <= 1.0
        assert 0.0 <= confluence_score.total_confluence_score <= 1.0
        
        # Verify zone metadata
        assert confluence_score.zone_id == sample_supply_zones[0].id
        assert abs(confluence_score.zone_center - 1.0840) < 0.0001
        assert confluence_score.zone_boundaries == (1.0850, 1.0830)
        
        # Strong zone should have high score components
        assert confluence_score.strength_score >= 0.7  # Strong zone (0.8 strength)
        assert confluence_score.test_history_score >= 0.7  # Perfect test history (2/2)
    
    def test_confluence_score_calculation_demand_zone(self, confluence_system, sample_demand_zones):
        """
        Test confluence score calculation for demand zones.
        
        Success Criteria:
        - Demand zones properly identified
        - Score calculation consistent with supply zones
        - Zone type correctly set to 'demand'
        """
        # Update system with zones
        confluence_system.update_zone_cache(sample_demand_zones)
        
        # Test price near demand zone
        test_price = 1.0810  # Inside first demand zone
        confluence_score = confluence_system.calculate_confluence_score(
            test_price, "EURUSD", ["M1"]
        )
        
        assert confluence_score.zone_type == "demand"
        assert confluence_score.zone_id == sample_demand_zones[0].id
        assert abs(confluence_score.zone_center - 1.0810) < 0.0001
        assert confluence_score.zone_boundaries == (1.0820, 1.0800)
        
        # Fresh, strong demand zone should score well
        assert confluence_score.freshness_score >= 0.8  # Created 6 hours ago
        assert confluence_score.strength_score >= 0.7  # 0.75 strength score
    
    def test_nearby_zones_retrieval(self, confluence_system, sample_supply_zones, sample_demand_zones):
        """
        Test retrieval of zones near a given price.
        
        Success Criteria:
        - Returns zones within proximity threshold
        - Filters out zones beyond threshold  
        - Sorts by proximity/relevance
        - Handles multiple zone types correctly
        """
        all_zones = sample_supply_zones + sample_demand_zones
        confluence_system.update_zone_cache(all_zones)
        
        # Test price between supply and demand zones
        test_price = 1.0830  # Between zones
        nearby_zones = confluence_system.get_nearby_zones(
            test_price, "EURUSD", "M1", max_distance_pips=30
        )
        
        # Should find zones within 30 pips
        assert len(nearby_zones) >= 2  # Should find nearby supply and demand zones
        
        # Verify all returned zones are within threshold
        for zone_proximity in nearby_zones:
            assert zone_proximity.distance_pips <= 300  # 30 pips = 300 points
            assert isinstance(zone_proximity, SDZoneProximity)
    
    def test_multi_timeframe_confluence_analysis(self, confluence_system, sample_supply_zones, sample_demand_zones):
        """
        Test multi-timeframe confluence analysis.
        
        Success Criteria:
        - Combines zones from multiple timeframes
        - Weights different timeframes appropriately
        - Higher timeframe zones get more weight
        - Returns comprehensive confluence picture
        """
        all_zones = sample_supply_zones + sample_demand_zones
        confluence_system.update_zone_cache(all_zones)
        
        # Test multi-timeframe analysis
        test_price = 1.0845
        timeframes = ["M1", "M5", "H1"]
        
        mtf_confluence = confluence_system.get_multi_timeframe_confluence(
            test_price, "EURUSD", timeframes
        )
        
        # Should return confluence scores for each timeframe
        assert isinstance(mtf_confluence, dict)
        for tf in timeframes:
            if tf in mtf_confluence:
                assert 0.0 <= mtf_confluence[tf] <= 1.0
        
        # Higher timeframes should generally have more weight
        # (This is implementation dependent)
        assert len(mtf_confluence) >= 1
    
    def test_confluence_factors_comprehensive(self, confluence_system, sample_supply_zones, sample_demand_zones):
        """
        Test comprehensive confluence factors calculation.
        
        Success Criteria:
        - Returns supply and demand zone analysis
        - Identifies dominant zone type
        - Calculates total confluence score
        - Provides actionable trading signals
        """
        all_zones = sample_supply_zones + sample_demand_zones
        confluence_system.update_zone_cache(all_zones)
        
        # Test confluence factors near supply zones
        test_price = 1.0845  # Near supply zones
        confluence_factors = confluence_system.get_confluence_factors(
            test_price, "EURUSD", ["M1", "M5"]
        )
        
        # Verify structure
        assert 'supply_zones' in confluence_factors
        assert 'demand_zones' in confluence_factors
        assert 'total_confluence_score' in confluence_factors
        assert 'dominant_zone_type' in confluence_factors
        
        # Verify data types
        assert isinstance(confluence_factors['supply_zones'], list)
        assert isinstance(confluence_factors['demand_zones'], list)
        assert isinstance(confluence_factors['total_confluence_score'], (int, float))
        assert 0.0 <= confluence_factors['total_confluence_score'] <= 1.0
        
        # Near supply zones, should identify supply dominance
        if confluence_factors['dominant_zone_type']:
            assert confluence_factors['dominant_zone_type'] in ['supply', 'demand', 'neutral']
    
    def test_zone_strength_weighting(self, confluence_system):
        """
        Test proper weighting of zone strength in confluence scores.
        
        Success Criteria:
        - Stronger zones get higher scores
        - Weak zones filtered out by min_zone_strength
        - Strength component weighted correctly
        """
        # Create zones with different strengths
        weak_zone = SupplyDemandZone(
            id=1, symbol="EURUSD", timeframe="M1", zone_type="supply",
            top_price=1.0850, bottom_price=1.0830,
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.3, test_count=0, success_count=0, status="active",  # Weak
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=1000,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        strong_zone = SupplyDemandZone(
            id=2, symbol="EURUSD", timeframe="M1", zone_type="supply",
            top_price=1.0870, bottom_price=1.0850,
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.9, test_count=2, success_count=2, status="active",  # Strong
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=2000,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        confluence_system.update_zone_cache([weak_zone, strong_zone])
        
        # Test price near weak zone (should be filtered out)
        weak_score = confluence_system.calculate_confluence_score(1.0840, "EURUSD", ["M1"])
        
        # Test price near strong zone (should score well)
        strong_score = confluence_system.calculate_confluence_score(1.0860, "EURUSD", ["M1"])
        
        # Strong zone should score higher than weak zone
        if weak_score and strong_score:
            assert strong_score.strength_score > weak_score.strength_score
            assert strong_score.total_confluence_score > weak_score.total_confluence_score
    
    def test_zone_freshness_scoring(self, confluence_system):
        """
        Test freshness scoring based on zone age.
        
        Success Criteria:
        - Fresh zones score higher than old zones
        - Age threshold properly applied
        - Freshness component weighted correctly
        """
        # Create zones with different ages
        fresh_zone = SupplyDemandZone(
            id=1, symbol="EURUSD", timeframe="M1", zone_type="supply",
            top_price=1.0850, bottom_price=1.0830,
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.8, test_count=0, success_count=0, status="active",
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=2000,
            created_at=datetime.now() - timedelta(hours=2),  # 2 hours old
            updated_at=datetime.now()
        )
        
        old_zone = SupplyDemandZone(
            id=2, symbol="EURUSD", timeframe="M1", zone_type="supply",
            top_price=1.0870, bottom_price=1.0850,
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.8, test_count=0, success_count=0, status="active",
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=2000,
            created_at=datetime.now() - timedelta(hours=120),  # 5 days old
            updated_at=datetime.now()
        )
        
        confluence_system.update_zone_cache([fresh_zone, old_zone])
        
        fresh_score = confluence_system.calculate_confluence_score(1.0840, "EURUSD", ["M1"])
        old_score = confluence_system.calculate_confluence_score(1.0860, "EURUSD", ["M1"])
        
        # Fresh zone should have higher freshness score
        if fresh_score and old_score:
            assert fresh_score.freshness_score > old_score.freshness_score
    
    def test_performance_benchmark_confluence_calculation(self, confluence_system):
        """
        Test confluence calculation performance.
        
        Success Criteria:
        - Processes 100 zones in <100ms
        - Multi-timeframe analysis <200ms
        - Memory usage remains stable
        - Scales linearly with zone count
        """
        # Create large zone dataset
        large_zones = self._create_large_zone_dataset(100)
        confluence_system.update_zone_cache(large_zones)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Performance test - single timeframe
        start_time = time.perf_counter()
        
        for i in range(10):  # Test multiple price points
            test_price = 1.0800 + (i * 0.0010)
            confluence_score = confluence_system.calculate_confluence_score(
                test_price, "EURUSD", ["M1"]
            )
        
        single_tf_duration = (time.perf_counter() - start_time) * 1000
        
        # Performance test - multi-timeframe
        start_time = time.perf_counter()
        
        mtf_confluence = confluence_system.get_multi_timeframe_confluence(
            1.0850, "EURUSD", ["M1", "M5", "H1", "H4"]
        )
        
        mtf_duration = (time.perf_counter() - start_time) * 1000
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        assert single_tf_duration < 100, f"Single TF confluence too slow: {single_tf_duration:.2f}ms > 100ms"
        assert mtf_duration < 200, f"Multi TF confluence too slow: {mtf_duration:.2f}ms > 200ms"
        assert memory_mb < 30, f"Memory usage too high: {memory_mb:.1f}MB > 30MB limit"
    
    def test_edge_case_no_nearby_zones(self, confluence_system):
        """
        Test handling when no zones are near the price.
        
        Success Criteria:
        - Returns appropriate empty/null results
        - No errors or exceptions
        - Provides clear indication of no confluence
        """
        # Test with empty zone cache
        test_price = 1.0850
        confluence_score = confluence_system.calculate_confluence_score(
            test_price, "EURUSD", ["M1"]
        )
        
        nearby_zones = confluence_system.get_nearby_zones(
            test_price, "EURUSD", "M1", max_distance_pips=20
        )
        
        confluence_factors = confluence_system.get_confluence_factors(
            test_price, "EURUSD", ["M1"]
        )
        
        # Should handle gracefully
        assert nearby_zones == []
        assert confluence_factors['total_confluence_score'] == 0.0
        assert confluence_factors['dominant_zone_type'] is None
    
    def test_edge_case_overlapping_zones(self, confluence_system):
        """
        Test handling of overlapping zones.
        
        Success Criteria:
        - Properly handles zone overlaps
        - Combines confluence appropriately
        - Avoids double-counting
        - Returns strongest zone influence
        """
        # Create overlapping zones
        zone1 = SupplyDemandZone(
            id=1, symbol="EURUSD", timeframe="M1", zone_type="supply",
            top_price=1.0850, bottom_price=1.0830,
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.7, test_count=1, success_count=1, status="active",
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=1500,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        zone2 = SupplyDemandZone(
            id=2, symbol="EURUSD", timeframe="M5", zone_type="supply",
            top_price=1.0845, bottom_price=1.0835,  # Overlaps with zone1
            left_time=datetime.now(), right_time=datetime.now(),
            strength_score=0.8, test_count=2, success_count=2, status="active",
            base_range=None, big_move=None, atr_at_creation=0.001, volume_at_creation=2000,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        confluence_system.update_zone_cache([zone1, zone2])
        
        # Test price in overlap area
        overlap_price = 1.0840
        confluence_factors = confluence_system.get_confluence_factors(
            overlap_price, "EURUSD", ["M1", "M5"]
        )
        
        # Should handle overlapping zones appropriately
        assert isinstance(confluence_factors, dict)
        assert confluence_factors['total_confluence_score'] >= 0.0
    
    def test_configuration_validation(self):
        """
        Test confluence system configuration validation.
        
        Success Criteria:
        - Rejects invalid parameter values
        - Validates weight ranges and sums
        - Proper error messages for invalid config
        """
        # Test invalid proximity threshold
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandConfluence(proximity_threshold_pips=0)  # Zero threshold
        
        # Test invalid weights (negative)
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandConfluence(strength_weight=-0.1)  # Negative weight
        
        # Test invalid weights (sum > 1.0)
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandConfluence(
                freshness_weight=0.5,
                strength_weight=0.5,
                test_history_weight=0.5  # Sum = 1.5 > 1.0
            )
        
        # Test invalid min zone strength
        with pytest.raises((ValueError, AssertionError)):
            SupplyDemandConfluence(min_zone_strength=1.5)  # Above 1.0
    
    # Helper methods for test data creation
    def _create_large_zone_dataset(self, count: int) -> List[SupplyDemandZone]:
        """Create large dataset of zones for performance testing"""
        zones = []
        
        for i in range(count):
            zone_type = "supply" if i % 2 == 0 else "demand"
            base_price = 1.0800 + (i * 0.0010)
            
            zone = SupplyDemandZone(
                id=i,
                symbol="EURUSD",
                timeframe=["M1", "M5", "H1"][i % 3],
                zone_type=zone_type,
                top_price=base_price + 0.0010,
                bottom_price=base_price - 0.0010,
                left_time=datetime.now() - timedelta(minutes=i),
                right_time=datetime.now() - timedelta(minutes=i-5),
                strength_score=0.5 + (i % 5) * 0.1,
                test_count=i % 4,
                success_count=(i % 4) // 2,
                status="active",
                base_range=None,
                big_move=None,
                atr_at_creation=0.0010,
                volume_at_creation=1000 + i * 100,
                created_at=datetime.now() - timedelta(hours=i % 48),
                updated_at=datetime.now()
            )
            zones.append(zone)
        
        return zones


# Test fixtures for other test files
@pytest.fixture
def supply_demand_confluence():
    """Standard SupplyDemandConfluence for use in other test files"""
    return SupplyDemandConfluence(
        proximity_threshold_pips=50,
        min_zone_strength=0.5,
        freshness_weight=0.3,
        strength_weight=0.4,
        test_history_weight=0.3,
        multi_timeframe_enabled=True,
        max_zone_age_hours=168
    )


@pytest.fixture
def sample_confluence_score():
    """Sample SDZoneConfluenceScore for testing"""
    return SDZoneConfluenceScore(
        zone_id=1,
        zone_type="supply",
        proximity_score=0.8,
        strength_score=0.7,
        freshness_score=0.6,
        test_history_score=0.5,
        total_confluence_score=0.65,
        distance_pips=15.5,
        zone_center=1.0845,
        zone_boundaries=(1.0850, 1.0840)
    )


# Performance benchmarking
def benchmark_confluence_calculation():
    """Standalone performance benchmark for CI/CD"""
    confluence_system = SupplyDemandConfluence()
    
    # Create test zones
    test_data = TestSupplyDemandConfluence()
    zones = test_data._create_large_zone_dataset(100)
    confluence_system.update_zone_cache(zones)
    
    # Benchmark confluence calculation
    start_time = time.perf_counter()
    
    for i in range(10):
        test_price = 1.0800 + (i * 0.0010)
        confluence_score = confluence_system.calculate_confluence_score(
            test_price, "EURUSD", ["M1"]
        )
    
    duration = (time.perf_counter() - start_time) * 1000
    
    print(f"SupplyDemandConfluence 100 zones, 10 calculations: {duration:.2f}ms")
    
    # Assert performance target
    assert duration < 100, f"Performance test failed: {duration:.2f}ms > 100ms"


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_confluence_calculation()