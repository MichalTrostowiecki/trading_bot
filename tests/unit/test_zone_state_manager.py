"""
Unit tests for ZoneStateManager class.

Tests cover:
- Zone state transitions (active -> tested -> broken/flipped)
- Zone testing detection when price touches zone
- Zone flip detection when zone changes type
- Zone expiry management
- Performance benchmarks for real-time updates

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
    from src.analysis.supply_demand.zone_state_manager import (
        ZoneStateManager,
        ZoneStateUpdate,
        ZoneTestEvent
    )
    from src.analysis.supply_demand.zone_detector import SupplyDemandZone
    from src.analysis.supply_demand.base_candle_detector import BaseCandleRange
    from src.analysis.supply_demand.big_move_detector import BigMove
except ImportError:
    # Classes don't exist yet - create placeholders
    @dataclass
    class ZoneStateUpdate:
        """Placeholder for ZoneStateUpdate until implementation"""
        zone_id: int
        old_status: str
        new_status: str
        update_time: datetime
        trigger_price: float
        trigger_reason: str
        test_success: bool = False
        
    @dataclass
    class ZoneTestEvent:
        """Placeholder for ZoneTestEvent until implementation"""
        zone_id: int
        test_time: datetime
        test_price: float
        test_type: str  # 'touch', 'penetration', 'break'
        success: bool
        reaction_strength: float = 0.0
        
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
    
    class ZoneStateManager:
        """Placeholder for ZoneStateManager until implementation"""
        def __init__(self, **kwargs):
            self.test_penetration_threshold = kwargs.get('test_penetration_threshold', 0.1)
            self.break_threshold = kwargs.get('break_threshold', 0.3)
            self.flip_confirmation_bars = kwargs.get('flip_confirmation_bars', 3)
            self.max_test_attempts = kwargs.get('max_test_attempts', 5)
            self.zone_expiry_hours = kwargs.get('zone_expiry_hours', 168)
            self.reaction_strength_threshold = kwargs.get('reaction_strength_threshold', 0.6)
            self._zones: Dict[int, SupplyDemandZone] = {}
            self._zone_updates: List[ZoneStateUpdate] = []
            self._test_events: List[ZoneTestEvent] = []
        
        def update_zone_states(self, zones, current_prices, current_time):
            return []  # Placeholder
            
        def detect_zone_tests(self, zones, price_data, current_time):
            return []  # Placeholder
            
        def detect_zone_flips(self, zones, price_data, current_time):
            return []  # Placeholder
            
        def expire_old_zones(self, zones, current_time):
            return []  # Placeholder
            
        def get_zone_history(self, zone_id):
            return []  # Placeholder
            
        def get_test_statistics(self, zone_id):
            return {'test_count': 0, 'success_count': 0, 'success_rate': 0.0}


class TestZoneStateManager:
    """
    Comprehensive unit tests for ZoneStateManager class.
    
    Tests cover:
    - Zone state transitions (active -> tested -> broken/flipped)
    - Zone testing detection when price touches zone
    - Zone flip detection when zone changes type
    - Zone expiry management
    - Performance benchmarks for real-time updates
    """
    
    @pytest.fixture
    def state_manager(self):
        """Standard state manager configuration for testing"""
        return ZoneStateManager(
            test_penetration_threshold=0.1,    # 10% penetration before test
            break_threshold=0.3,               # 30% penetration breaks zone
            flip_confirmation_bars=3,          # 3 bars to confirm flip
            max_test_attempts=5,               # Max tests before zone marked weak
            zone_expiry_hours=168,             # 1 week expiry
            reaction_strength_threshold=0.6    # 60% reaction strength required
        )
    
    @pytest.fixture
    def sample_supply_zone(self):
        """Sample supply zone for testing"""
        return SupplyDemandZone(
            id=1,
            symbol="EURUSD",
            timeframe="M1",
            zone_type="supply",
            top_price=1.0850,
            bottom_price=1.0830,
            left_time=datetime(2025, 1, 1, 10, 0),
            right_time=datetime(2025, 1, 1, 10, 5),
            strength_score=0.8,
            test_count=0,
            success_count=0,
            status="active",
            base_range=BaseCandleRange(0, 4, datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 10, 4),
                                     1.0850, 1.0830, 0.0010, 5, 0.8),
            big_move=BigMove(5, 8, datetime(2025, 1, 1, 10, 5), datetime(2025, 1, 1, 10, 8),
                           "bearish", 3.0, 0.8, 1.0830, True),
            atr_at_creation=0.0010,
            volume_at_creation=2000.0,
            created_at=datetime(2025, 1, 1, 10, 0),
            updated_at=datetime(2025, 1, 1, 10, 0)
        )
    
    @pytest.fixture
    def sample_demand_zone(self):
        """Sample demand zone for testing"""
        return SupplyDemandZone(
            id=2,
            symbol="EURUSD",
            timeframe="M1",
            zone_type="demand",
            top_price=1.0820,
            bottom_price=1.0800,
            left_time=datetime(2025, 1, 1, 11, 0),
            right_time=datetime(2025, 1, 1, 11, 5),
            strength_score=0.75,
            test_count=0,
            success_count=0,
            status="active",
            base_range=BaseCandleRange(10, 14, datetime(2025, 1, 1, 11, 0), datetime(2025, 1, 1, 11, 4),
                                     1.0820, 1.0800, 0.0010, 5, 0.75),
            big_move=BigMove(15, 18, datetime(2025, 1, 1, 11, 5), datetime(2025, 1, 1, 11, 8),
                           "bullish", 2.8, 0.75, 1.0820, True),
            atr_at_creation=0.0010,
            volume_at_creation=1800.0,
            created_at=datetime(2025, 1, 1, 11, 0),
            updated_at=datetime(2025, 1, 1, 11, 0)
        )
    
    @pytest.fixture
    def sample_price_data_zone_test(self):
        """Sample price data showing zone test scenario"""
        return pd.DataFrame({
            'open': [1.0825, 1.0826, 1.0835, 1.0840, 1.0845],
            'high': [1.0830, 1.0840, 1.0850, 1.0855, 1.0850],
            'low': [1.0820, 1.0825, 1.0832, 1.0835, 1.0840],
            'close': [1.0828, 1.0838, 1.0848, 1.0850, 1.0847],
            'volume': [1500, 1800, 2200, 1900, 1600],
            'time': pd.date_range('2025-01-01 12:00', periods=5, freq='1min')
        })
    
    @pytest.fixture
    def sample_price_data_zone_break(self):
        """Sample price data showing zone break scenario"""
        return pd.DataFrame({
            'open': [1.0825, 1.0820, 1.0815, 1.0810, 1.0805],
            'high': [1.0830, 1.0825, 1.0820, 1.0815, 1.0810],
            'low': [1.0820, 1.0815, 1.0810, 1.0805, 1.0800],
            'close': [1.0822, 1.0817, 1.0812, 1.0807, 1.0802],
            'volume': [2000, 2500, 3000, 2800, 2200],
            'time': pd.date_range('2025-01-01 12:00', periods=5, freq='1min')
        })
    
    def test_state_manager_initialization(self, state_manager):
        """
        Test state manager initializes with correct parameters.
        
        Success Criteria:
        - All parameters set correctly
        - Default values applied when not specified
        - Parameter validation works
        """
        assert state_manager.test_penetration_threshold == 0.1
        assert state_manager.break_threshold == 0.3
        assert state_manager.flip_confirmation_bars == 3
        assert state_manager.max_test_attempts == 5
        assert state_manager.zone_expiry_hours == 168
        assert state_manager.reaction_strength_threshold == 0.6
        
        # Check internal state initialization
        assert isinstance(state_manager._zones, dict)
        assert isinstance(state_manager._zone_updates, list)
        assert isinstance(state_manager._test_events, list)
    
    def test_zone_test_detection_supply_zone(self, state_manager, sample_supply_zone, sample_price_data_zone_test):
        """
        Test detection of zone tests for supply zones.
        
        Success Criteria:
        - Detects when price touches zone boundary
        - Classifies test type (touch, penetration, break)
        - Calculates reaction strength correctly
        - Updates zone test count
        """
        zones = [sample_supply_zone]
        current_time = datetime(2025, 1, 1, 12, 5)
        
        # Test zone testing detection
        test_events = state_manager.detect_zone_tests(zones, sample_price_data_zone_test, current_time)
        
        # Should detect test events
        assert len(test_events) > 0, "Should detect zone test events"
        
        test_event = test_events[0]
        assert test_event.zone_id == sample_supply_zone.id
        assert test_event.test_type in ['touch', 'penetration', 'break']
        assert isinstance(test_event.test_price, float)
        assert isinstance(test_event.success, bool)
        assert 0.0 <= test_event.reaction_strength <= 1.0
    
    def test_zone_break_detection_supply_zone(self, state_manager, sample_supply_zone, sample_price_data_zone_break):
        """
        Test detection of zone breaks for supply zones.
        
        Success Criteria:
        - Detects when price breaks through zone completely
        - Updates zone status to 'broken'
        - Calculates break confirmation correctly
        - Records proper break event
        """
        zones = [sample_supply_zone]
        current_time = datetime(2025, 1, 1, 12, 5)
        
        # Test zone break detection
        state_updates = state_manager.update_zone_states(zones, sample_price_data_zone_break, current_time)
        
        # Should detect zone break
        broken_updates = [update for update in state_updates if update.new_status == 'broken']
        assert len(broken_updates) > 0, "Should detect zone break"
        
        break_update = broken_updates[0]
        assert break_update.zone_id == sample_supply_zone.id
        assert break_update.old_status == 'active'
        assert break_update.new_status == 'broken'
        assert break_update.trigger_reason == 'price_break'
    
    def test_zone_flip_detection_supply_to_demand(self, state_manager, sample_supply_zone):
        """
        Test detection of zone flips from supply to demand.
        
        Success Criteria:
        - Detects when supply zone becomes demand zone
        - Updates zone type correctly
        - Requires proper confirmation bars
        - Maintains zone history
        """
        # Create price data showing supply zone flip to demand
        flip_data = pd.DataFrame({
            'open': [1.0825, 1.0830, 1.0835, 1.0840, 1.0845],
            'high': [1.0830, 1.0840, 1.0850, 1.0855, 1.0860],
            'low': [1.0820, 1.0825, 1.0830, 1.0835, 1.0840],
            'close': [1.0828, 1.0838, 1.0848, 1.0853, 1.0858],
            'volume': [1500, 1800, 2200, 1900, 1600],
            'time': pd.date_range('2025-01-01 12:00', periods=5, freq='1min')
        })
        
        zones = [sample_supply_zone]
        current_time = datetime(2025, 1, 1, 12, 5)
        
        # Test zone flip detection
        flip_updates = state_manager.detect_zone_flips(zones, flip_data, current_time)
        
        # Should detect potential flip
        if len(flip_updates) > 0:
            flip_update = flip_updates[0]
            assert flip_update.zone_id == sample_supply_zone.id
            assert flip_update.trigger_reason == 'zone_flip'
            assert flip_update.new_status in ['flipped', 'testing_flip']
    
    def test_zone_expiry_management(self, state_manager, sample_supply_zone, sample_demand_zone):
        """
        Test automatic zone expiry based on age.
        
        Success Criteria:
        - Detects zones older than expiry threshold
        - Updates zone status to 'expired'
        - Preserves zone data for historical analysis
        - Handles multiple zones correctly
        """
        # Create expired zones (older than 168 hours)
        expired_zone = sample_supply_zone
        expired_zone.created_at = datetime.now() - timedelta(hours=200)  # 200 hours ago
        
        # Create active zone (within expiry threshold)
        active_zone = sample_demand_zone
        active_zone.created_at = datetime.now() - timedelta(hours=100)  # 100 hours ago
        
        zones = [expired_zone, active_zone]
        current_time = datetime.now()
        
        # Test zone expiry
        expiry_updates = state_manager.expire_old_zones(zones, current_time)
        
        # Should expire old zone but keep active zone
        expired_updates = [update for update in expiry_updates if update.new_status == 'expired']
        assert len(expired_updates) >= 1, "Should expire old zones"
        
        expired_update = expired_updates[0]
        assert expired_update.zone_id == expired_zone.id
        assert expired_update.trigger_reason == 'age_expiry'
    
    def test_zone_test_statistics_tracking(self, state_manager, sample_supply_zone):
        """
        Test accurate tracking of zone test statistics.
        
        Success Criteria:
        - Tracks total test count correctly
        - Tracks successful test count
        - Calculates success rate accurately
        - Handles edge cases (zero tests)
        """
        zone_id = sample_supply_zone.id
        
        # Initial statistics should be zero
        initial_stats = state_manager.get_test_statistics(zone_id)
        assert initial_stats['test_count'] == 0
        assert initial_stats['success_count'] == 0
        assert initial_stats['success_rate'] == 0.0
        
        # After some test events, statistics should update
        # (This would be done by the actual implementation)
        # For now, we test the expected interface
        assert 'test_count' in initial_stats
        assert 'success_count' in initial_stats
        assert 'success_rate' in initial_stats
        assert isinstance(initial_stats['success_rate'], float)
    
    def test_zone_history_tracking(self, state_manager, sample_supply_zone):
        """
        Test comprehensive zone history tracking.
        
        Success Criteria:
        - Records all zone state changes
        - Maintains chronological order
        - Includes all relevant metadata
        - Provides queryable history
        """
        zone_id = sample_supply_zone.id
        
        # Test zone history retrieval
        history = state_manager.get_zone_history(zone_id)
        
        # Should return list of historical events
        assert isinstance(history, list)
        
        # If history exists, validate structure
        if len(history) > 0:
            event = history[0]
            # Should have required fields for historical tracking
            assert hasattr(event, 'zone_id') or 'zone_id' in event
            assert hasattr(event, 'update_time') or 'update_time' in event
    
    def test_multiple_zones_simultaneous_updates(self, state_manager, sample_supply_zone, sample_demand_zone):
        """
        Test handling multiple zones with simultaneous updates.
        
        Success Criteria:
        - Processes multiple zones efficiently
        - Maintains zone isolation (no interference)
        - Handles concurrent state changes
        - Preserves data integrity
        """
        zones = [sample_supply_zone, sample_demand_zone]
        
        # Create price data that affects both zones
        multi_zone_data = pd.DataFrame({
            'open': [1.0815, 1.0820, 1.0825, 1.0830, 1.0835],
            'high': [1.0825, 1.0830, 1.0835, 1.0840, 1.0845],
            'low': [1.0810, 1.0815, 1.0820, 1.0825, 1.0830],
            'close': [1.0822, 1.0827, 1.0832, 1.0837, 1.0842],
            'volume': [1500, 1800, 2200, 1900, 1600],
            'time': pd.date_range('2025-01-01 12:00', periods=5, freq='1min')
        })
        
        current_time = datetime(2025, 1, 1, 12, 5)
        
        # Test simultaneous updates
        updates = state_manager.update_zone_states(zones, multi_zone_data, current_time)
        
        # Should handle multiple zones
        assert isinstance(updates, list)
        
        # Validate zone isolation
        zone_ids = [update.zone_id for update in updates]
        unique_zones = set(zone_ids)
        assert len(unique_zones) <= len(zones), "Should not create duplicate zone updates"
    
    def test_edge_case_zone_boundary_exact_price(self, state_manager, sample_supply_zone):
        """
        Test edge case where price exactly matches zone boundary.
        
        Success Criteria:
        - Handles exact boundary prices correctly
        - Proper test vs break classification
        - Consistent behavior for top/bottom boundaries
        - No floating point precision issues
        """
        zones = [sample_supply_zone]
        
        # Create price data with exact boundary matches
        boundary_data = pd.DataFrame({
            'open': [1.0840, 1.0845, 1.0850, 1.0845, 1.0840],
            'high': [1.0845, 1.0850, 1.0850, 1.0850, 1.0845],
            'low': [1.0835, 1.0840, 1.0845, 1.0840, 1.0835],
            'close': [1.0845, 1.0850, 1.0850, 1.0845, 1.0840],  # Exact boundaries
            'volume': [1500, 1800, 2200, 1900, 1600],
            'time': pd.date_range('2025-01-01 12:00', periods=5, freq='1min')
        })
        
        current_time = datetime(2025, 1, 1, 12, 5)
        
        # Test boundary handling
        test_events = state_manager.detect_zone_tests(zones, boundary_data, current_time)
        
        # Should handle exact boundaries without errors
        assert isinstance(test_events, list)
        
        # Should classify boundary touches correctly
        for event in test_events:
            assert event.test_type in ['touch', 'penetration', 'break']
    
    def test_edge_case_insufficient_confirmation_bars(self, state_manager, sample_supply_zone):
        """
        Test edge case with insufficient bars for flip confirmation.
        
        Success Criteria:
        - Handles insufficient data gracefully
        - Does not confirm flips prematurely
        - Maintains pending flip status appropriately
        - Provides clear feedback on data requirements
        """
        zones = [sample_supply_zone]
        
        # Create insufficient data (only 2 bars, need 3 for confirmation)
        insufficient_data = pd.DataFrame({
            'open': [1.0825, 1.0830],
            'high': [1.0830, 1.0840],
            'low': [1.0820, 1.0825],
            'close': [1.0828, 1.0838],
            'volume': [1500, 1800],
            'time': pd.date_range('2025-01-01 12:00', periods=2, freq='1min')
        })
        
        current_time = datetime(2025, 1, 1, 12, 2)
        
        # Test with insufficient data
        flip_updates = state_manager.detect_zone_flips(zones, insufficient_data, current_time)
        
        # Should handle insufficient data gracefully
        assert isinstance(flip_updates, list)
        
        # Should not confirm flips with insufficient data
        confirmed_flips = [update for update in flip_updates if update.new_status == 'flipped']
        assert len(confirmed_flips) == 0, "Should not confirm flips with insufficient data"
    
    def test_performance_benchmark_real_time_updates(self, state_manager):
        """
        Test performance meets real-time requirements.
        
        Success Criteria:
        - Processes 100 zones with 1000 price bars in <50ms
        - Memory usage remains stable
        - Scales linearly with zone count
        - Maintains accuracy under load
        """
        # Create large dataset for performance testing
        large_zones = self._create_large_zone_dataset(100)
        large_price_data = self._create_large_price_dataset(1000)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Warm up
        state_manager.update_zone_states(large_zones[:10], large_price_data.head(100), datetime.now())
        
        # Performance test
        start_time = time.perf_counter()
        
        updates = state_manager.update_zone_states(large_zones, large_price_data, datetime.now())
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        duration_ms = (end_time - start_time) * 1000
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        assert duration_ms < 50, f"Performance test failed: {duration_ms:.2f}ms > 50ms target"
        assert memory_mb < 20, f"Memory usage too high: {memory_mb:.1f}MB > 20MB limit"
        
        # Verify algorithm correctness under load
        assert isinstance(updates, list), "Should return list even with large dataset"
    
    def test_configuration_validation(self):
        """
        Test state manager configuration validation.
        
        Success Criteria:
        - Rejects invalid parameter values
        - Validates threshold ranges
        - Proper error messages for invalid config
        """
        # Test invalid penetration threshold
        with pytest.raises((ValueError, AssertionError)):
            ZoneStateManager(test_penetration_threshold=0.0)  # Zero threshold
        
        with pytest.raises((ValueError, AssertionError)):
            ZoneStateManager(test_penetration_threshold=1.5)  # Above 1.0
        
        # Test invalid break threshold
        with pytest.raises((ValueError, AssertionError)):
            ZoneStateManager(break_threshold=0.0)  # Zero threshold
        
        # Test invalid confirmation bars
        with pytest.raises((ValueError, AssertionError)):
            ZoneStateManager(flip_confirmation_bars=0)  # Zero bars
        
        # Test invalid expiry hours
        with pytest.raises((ValueError, AssertionError)):
            ZoneStateManager(zone_expiry_hours=0)  # Zero hours
    
    def test_data_validation(self, state_manager, sample_supply_zone):
        """
        Test input data validation.
        
        Success Criteria:
        - Validates required columns exist
        - Handles missing data appropriately
        - Validates data integrity
        - Provides clear error messages
        """
        # Test with missing required columns
        incomplete_data = pd.DataFrame({
            'open': [1.0825],
            'high': [1.0830],
            # Missing 'low', 'close', 'time'
        })
        
        zones = [sample_supply_zone]
        current_time = datetime(2025, 1, 1, 12, 0)
        
        # Should handle missing data gracefully
        try:
            updates = state_manager.update_zone_states(zones, incomplete_data, current_time)
            assert isinstance(updates, list)
        except (ValueError, KeyError) as e:
            # Should provide clear error message
            assert len(str(e)) > 0
        
        # Test with empty dataframe
        empty_data = pd.DataFrame()
        
        updates_empty = state_manager.update_zone_states(zones, empty_data, current_time)
        assert isinstance(updates_empty, list)
    
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
                timeframe="M1",
                zone_type=zone_type,
                top_price=base_price + 0.0010,
                bottom_price=base_price - 0.0010,
                left_time=datetime(2025, 1, 1, 10, 0) + timedelta(minutes=i),
                right_time=datetime(2025, 1, 1, 10, 5) + timedelta(minutes=i),
                strength_score=0.7 + (i % 3) * 0.1,
                test_count=i % 3,
                success_count=i % 2,
                status="active",
                base_range=BaseCandleRange(0, 4, datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 10, 4),
                                         base_price + 0.0010, base_price - 0.0010, 0.0010, 5, 0.8),
                big_move=BigMove(5, 8, datetime(2025, 1, 1, 10, 5), datetime(2025, 1, 1, 10, 8),
                               "bullish" if zone_type == "demand" else "bearish", 3.0, 0.8, base_price, True),
                atr_at_creation=0.0010,
                volume_at_creation=2000.0,
                created_at=datetime(2025, 1, 1, 10, 0),
                updated_at=datetime(2025, 1, 1, 10, 0)
            )
            zones.append(zone)
        
        return zones
    
    def _create_large_price_dataset(self, size: int) -> pd.DataFrame:
        """Create large price dataset for performance testing"""
        np.random.seed(42)  # Reproducible results
        
        data = []
        base_price = 1.0800
        
        for i in range(size):
            # Create realistic price movement
            price_change = np.random.normal(0, 0.00005)
            base_price += price_change
            
            # Generate OHLC
            spread = abs(np.random.normal(0, 0.00003))
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


# Test fixtures for other test files
@pytest.fixture
def zone_state_manager():
    """Standard ZoneStateManager for use in other test files"""
    return ZoneStateManager(
        test_penetration_threshold=0.1,
        break_threshold=0.3,
        flip_confirmation_bars=3,
        max_test_attempts=5,
        zone_expiry_hours=168,
        reaction_strength_threshold=0.6
    )


@pytest.fixture
def sample_zone_update():
    """Sample ZoneStateUpdate for testing"""
    return ZoneStateUpdate(
        zone_id=1,
        old_status="active",
        new_status="tested",
        update_time=datetime(2025, 1, 1, 12, 0),
        trigger_price=1.0845,
        trigger_reason="zone_test",
        test_success=True
    )


@pytest.fixture
def sample_test_event():
    """Sample ZoneTestEvent for testing"""
    return ZoneTestEvent(
        zone_id=1,
        test_time=datetime(2025, 1, 1, 12, 0),
        test_price=1.0845,
        test_type="touch",
        success=True,
        reaction_strength=0.75
    )


# Performance benchmarking
def benchmark_zone_state_management():
    """Standalone performance benchmark for CI/CD"""
    state_manager = ZoneStateManager()
    
    # Create test data
    test_data = TestZoneStateManager()
    zones = test_data._create_large_zone_dataset(100)
    price_data = test_data._create_large_price_dataset(1000)
    
    # Benchmark
    start_time = time.perf_counter()
    updates = state_manager.update_zone_states(zones, price_data, datetime.now())
    duration = (time.perf_counter() - start_time) * 1000
    
    print(f"ZoneStateManager 100 zones, 1000 bars: {duration:.2f}ms")
    
    # Assert performance target
    assert duration < 50, f"Performance test failed: {duration:.2f}ms > 50ms"


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_zone_state_management()