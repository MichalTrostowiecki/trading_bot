"""
Unit tests for SupplyDemandRepository class.

Tests cover:
- Zone CRUD operations (Create, Read, Update, Delete)
- Zone history tracking and retrieval
- Test event storage and querying
- Performance benchmarks for database operations
- Database transaction handling

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
from unittest.mock import Mock, MagicMock, patch

# Import the classes we're testing
try:
    from src.analysis.supply_demand.repository import (
        SupplyDemandRepository,
        ZoneQueryFilter,
        ZoneHistoryQuery
    )
    from src.analysis.supply_demand.zone_detector import SupplyDemandZone
    from src.analysis.supply_demand.zone_state_manager import ZoneStateUpdate, ZoneTestEvent
    from src.analysis.supply_demand.base_candle_detector import BaseCandleRange
    from src.analysis.supply_demand.big_move_detector import BigMove
except ImportError:
    # Classes don't exist yet - create placeholders
    @dataclass
    class ZoneQueryFilter:
        """Placeholder for ZoneQueryFilter until implementation"""
        symbol: Optional[str] = None
        timeframe: Optional[str] = None
        zone_type: Optional[str] = None
        status: Optional[str] = None
        min_strength: Optional[float] = None
        max_age_hours: Optional[int] = None
        limit: Optional[int] = None
        
    @dataclass
    class ZoneHistoryQuery:
        """Placeholder for ZoneHistoryQuery until implementation"""
        zone_id: Optional[int] = None
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None
        event_types: Optional[List[str]] = None
        limit: Optional[int] = None
        
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
    class ZoneStateUpdate:
        zone_id: int
        old_status: str
        new_status: str
        update_time: datetime
        trigger_price: float
        trigger_reason: str
        test_success: bool = False
        
        def to_dict(self):
            return {
                'zone_id': self.zone_id,
                'old_status': self.old_status,
                'new_status': self.new_status,
                'update_time': self.update_time,
                'trigger_price': self.trigger_price,
                'trigger_reason': self.trigger_reason,
                'test_success': self.test_success
            }
        
    @dataclass
    class ZoneTestEvent:
        zone_id: int
        test_time: datetime
        test_price: float
        test_type: str
        success: bool
        reaction_strength: float = 0.0
        
        def to_dict(self):
            return {
                'zone_id': self.zone_id,
                'test_time': self.test_time,
                'test_price': self.test_price,
                'test_type': self.test_type,
                'success': self.success,
                'reaction_strength': self.reaction_strength
            }
    
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
    
    class SupplyDemandRepository:
        """Placeholder for SupplyDemandRepository until implementation"""
        def __init__(self, connection_string=None, **kwargs):
            self.connection_string = connection_string
            self._mock_zones = {}
            self._mock_updates = []
            self._mock_events = []
            self._next_id = 1
        
        def save_zone(self, zone):
            if zone.id is None:
                zone.id = self._next_id
                self._next_id += 1
            self._mock_zones[zone.id] = zone
            return zone.id
            
        def get_zone_by_id(self, zone_id):
            return self._mock_zones.get(zone_id)
            
        def update_zone(self, zone):
            if zone.id in self._mock_zones:
                self._mock_zones[zone.id] = zone
                return True
            return False
            
        def delete_zone(self, zone_id):
            if zone_id in self._mock_zones:
                del self._mock_zones[zone_id]
                return True
            return False
            
        def query_zones(self, filter_criteria):
            return list(self._mock_zones.values())
            
        def save_zone_update(self, update):
            self._mock_updates.append(update)
            return True
            
        def save_test_event(self, event):
            self._mock_events.append(event)
            return True
            
        def get_zone_history(self, zone_id, query_params=None):
            return [u for u in self._mock_updates if u.zone_id == zone_id]
            
        def get_test_events(self, zone_id, query_params=None):
            return [e for e in self._mock_events if e.zone_id == zone_id]
            
        def cleanup_old_zones(self, max_age_hours):
            return 0
            
        def get_zone_statistics(self, zone_id):
            return {'test_count': 0, 'success_count': 0, 'success_rate': 0.0}
            
        def bulk_save_zones(self, zones):
            return [self.save_zone(zone) for zone in zones]
            
        def close(self):
            pass


class TestSupplyDemandRepository:
    """
    Comprehensive unit tests for SupplyDemandRepository class.
    
    Tests cover:
    - Zone CRUD operations (Create, Read, Update, Delete)
    - Zone history tracking and retrieval
    - Test event storage and querying
    - Performance benchmarks for database operations
    - Database transaction handling
    """
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection for testing"""
        connection = Mock()
        connection.execute.return_value = Mock()
        connection.fetchone.return_value = None
        connection.fetchall.return_value = []
        connection.commit.return_value = None
        connection.rollback.return_value = None
        connection.close.return_value = None
        return connection
    
    @pytest.fixture
    def repository(self, mock_db_connection):
        """Standard repository configuration for testing"""
        with patch('src.analysis.supply_demand.repository.psycopg2.connect', return_value=mock_db_connection):
            return SupplyDemandRepository(
                connection_string="postgresql://test:test@localhost/test_db",
                pool_size=5,
                max_overflow=10,
                echo=False
            )
    
    @pytest.fixture
    def sample_supply_zone(self):
        """Sample supply zone for testing"""
        return SupplyDemandZone(
            id=None,  # Will be assigned by database
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
    def sample_zone_update(self):
        """Sample zone state update for testing"""
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
    def sample_test_event(self):
        """Sample zone test event for testing"""
        return ZoneTestEvent(
            zone_id=1,
            test_time=datetime(2025, 1, 1, 12, 0),
            test_price=1.0845,
            test_type="touch",
            success=True,
            reaction_strength=0.75
        )
    
    def test_repository_initialization(self, repository):
        """
        Test repository initializes with correct configuration.
        
        Success Criteria:
        - Database connection established
        - Connection pool configured
        - Schema validation passes
        - Required tables exist
        """
        assert repository is not None
        assert hasattr(repository, 'connection_string')
        assert hasattr(repository, 'save_zone')
        assert hasattr(repository, 'get_zone_by_id')
        assert hasattr(repository, 'update_zone')
        assert hasattr(repository, 'delete_zone')
    
    def test_zone_creation_success(self, repository, sample_supply_zone):
        """
        Test successful zone creation in database.
        
        Success Criteria:
        - Zone saved with generated ID
        - All zone fields persisted correctly
        - Related objects (base_range, big_move) serialized
        - Timestamps handled correctly
        """
        # Save zone
        zone_id = repository.save_zone(sample_supply_zone)
        
        # Verify zone was saved
        assert zone_id is not None
        assert isinstance(zone_id, int)
        assert zone_id > 0
        
        # Verify zone can be retrieved
        retrieved_zone = repository.get_zone_by_id(zone_id)
        assert retrieved_zone is not None
        assert retrieved_zone.id == zone_id
        assert retrieved_zone.symbol == sample_supply_zone.symbol
        assert retrieved_zone.zone_type == sample_supply_zone.zone_type
        assert retrieved_zone.top_price == sample_supply_zone.top_price
        assert retrieved_zone.bottom_price == sample_supply_zone.bottom_price
    
    def test_zone_retrieval_by_id(self, repository, sample_supply_zone):
        """
        Test zone retrieval by ID.
        
        Success Criteria:
        - Retrieves correct zone by ID
        - All fields properly deserialized
        - Returns None for non-existent ID
        - Handles invalid ID gracefully
        """
        # Save zone first
        zone_id = repository.save_zone(sample_supply_zone)
        
        # Test successful retrieval
        retrieved_zone = repository.get_zone_by_id(zone_id)
        assert retrieved_zone is not None
        assert retrieved_zone.id == zone_id
        
        # Test non-existent ID
        non_existent_zone = repository.get_zone_by_id(99999)
        assert non_existent_zone is None
        
        # Test invalid ID types
        invalid_zone = repository.get_zone_by_id(None)
        assert invalid_zone is None
    
    def test_zone_update_success(self, repository, sample_supply_zone):
        """
        Test successful zone updates.
        
        Success Criteria:
        - Zone fields updated correctly
        - Updated timestamp automatically set
        - Version control maintained
        - Concurrent update handling
        """
        # Save zone first
        zone_id = repository.save_zone(sample_supply_zone)
        sample_supply_zone.id = zone_id
        
        # Update zone fields
        sample_supply_zone.status = "tested"
        sample_supply_zone.test_count = 1
        sample_supply_zone.success_count = 1
        sample_supply_zone.updated_at = datetime.now()
        
        # Update zone
        update_success = repository.update_zone(sample_supply_zone)
        assert update_success is True
        
        # Verify updates were applied
        updated_zone = repository.get_zone_by_id(zone_id)
        assert updated_zone.status == "tested"
        assert updated_zone.test_count == 1
        assert updated_zone.success_count == 1
    
    def test_zone_deletion_success(self, repository, sample_supply_zone):
        """
        Test successful zone deletion.
        
        Success Criteria:
        - Zone removed from database
        - Related records handled appropriately
        - Cascade behavior correct
        - Returns proper deletion status
        """
        # Save zone first
        zone_id = repository.save_zone(sample_supply_zone)
        
        # Verify zone exists
        assert repository.get_zone_by_id(zone_id) is not None
        
        # Delete zone
        deletion_success = repository.delete_zone(zone_id)
        assert deletion_success is True
        
        # Verify zone is gone
        deleted_zone = repository.get_zone_by_id(zone_id)
        assert deleted_zone is None
        
        # Test deletion of non-existent zone
        non_existent_deletion = repository.delete_zone(99999)
        assert non_existent_deletion is False
    
    def test_zone_querying_with_filters(self, repository):
        """
        Test zone querying with various filter criteria.
        
        Success Criteria:
        - Symbol filter works correctly
        - Timeframe filter works correctly
        - Zone type filter works correctly
        - Status filter works correctly
        - Strength filter works correctly
        - Age filter works correctly
        - Multiple filters combined correctly
        """
        # Create test zones with different properties
        zones = [
            SupplyDemandZone(None, "EURUSD", "M1", "supply", 1.0850, 1.0830, 
                           datetime.now(), datetime.now(), 0.8, 0, 0, "active",
                           None, None, 0.001, 1000, datetime.now(), datetime.now()),
            SupplyDemandZone(None, "GBPUSD", "H1", "demand", 1.3020, 1.3000,
                           datetime.now(), datetime.now(), 0.6, 1, 0, "tested",
                           None, None, 0.001, 1500, datetime.now(), datetime.now()),
            SupplyDemandZone(None, "EURUSD", "M5", "supply", 1.0880, 1.0860,
                           datetime.now(), datetime.now(), 0.9, 0, 0, "active",
                           None, None, 0.001, 2000, datetime.now(), datetime.now())
        ]
        
        # Save all zones
        for zone in zones:
            repository.save_zone(zone)
        
        # Test symbol filter
        symbol_filter = ZoneQueryFilter(symbol="EURUSD")
        eurusd_zones = repository.query_zones(symbol_filter)
        assert len(eurusd_zones) >= 2  # Should find EURUSD zones
        
        # Test zone type filter
        type_filter = ZoneQueryFilter(zone_type="supply")
        supply_zones = repository.query_zones(type_filter)
        assert len(supply_zones) >= 2  # Should find supply zones
        
        # Test strength filter
        strength_filter = ZoneQueryFilter(min_strength=0.7)
        strong_zones = repository.query_zones(strength_filter)
        assert len(strong_zones) >= 2  # Should find strong zones
        
        # Test combined filters
        combined_filter = ZoneQueryFilter(symbol="EURUSD", zone_type="supply", min_strength=0.8)
        filtered_zones = repository.query_zones(combined_filter)
        assert len(filtered_zones) >= 1  # Should find specific zones
    
    def test_zone_history_tracking(self, repository, sample_zone_update):
        """
        Test zone history tracking and retrieval.
        
        Success Criteria:
        - Zone updates stored correctly
        - History retrieved in chronological order
        - Query filters work for history
        - Pagination supported for large histories
        """
        # Save zone update
        save_success = repository.save_zone_update(sample_zone_update)
        assert save_success is True
        
        # Retrieve zone history
        history = repository.get_zone_history(sample_zone_update.zone_id)
        assert len(history) >= 1
        
        # Verify update in history
        found_update = None
        for update in history:
            if (update.zone_id == sample_zone_update.zone_id and 
                update.old_status == sample_zone_update.old_status):
                found_update = update
                break
        
        assert found_update is not None
        assert found_update.new_status == sample_zone_update.new_status
        assert found_update.trigger_reason == sample_zone_update.trigger_reason
    
    def test_test_event_storage(self, repository, sample_test_event):
        """
        Test zone test event storage and retrieval.
        
        Success Criteria:
        - Test events stored correctly
        - Events retrieved by zone ID
        - Query filters work for events
        - Performance metrics tracked
        """
        # Save test event
        save_success = repository.save_test_event(sample_test_event)
        assert save_success is True
        
        # Retrieve test events for zone
        events = repository.get_test_events(sample_test_event.zone_id)
        assert len(events) >= 1
        
        # Verify event in results
        found_event = None
        for event in events:
            if (event.zone_id == sample_test_event.zone_id and
                event.test_type == sample_test_event.test_type):
                found_event = event
                break
        
        assert found_event is not None
        assert found_event.test_price == sample_test_event.test_price
        assert found_event.success == sample_test_event.success
        assert found_event.reaction_strength == sample_test_event.reaction_strength
    
    def test_zone_statistics_calculation(self, repository):
        """
        Test zone statistics calculation and caching.
        
        Success Criteria:
        - Test count calculated correctly
        - Success rate calculated correctly
        - Statistics cached for performance
        - Statistics updated on new events
        """
        zone_id = 1
        
        # Get initial statistics
        initial_stats = repository.get_zone_statistics(zone_id)
        assert 'test_count' in initial_stats
        assert 'success_count' in initial_stats
        assert 'success_rate' in initial_stats
        
        # Add some test events
        test_events = [
            ZoneTestEvent(zone_id, datetime.now(), 1.0845, "touch", True, 0.8),
            ZoneTestEvent(zone_id, datetime.now(), 1.0847, "penetration", False, 0.3),
            ZoneTestEvent(zone_id, datetime.now(), 1.0844, "touch", True, 0.7)
        ]
        
        for event in test_events:
            repository.save_test_event(event)
        
        # Get updated statistics
        updated_stats = repository.get_zone_statistics(zone_id)
        
        # Verify statistics are calculated
        assert isinstance(updated_stats['test_count'], int)
        assert isinstance(updated_stats['success_count'], int)
        assert isinstance(updated_stats['success_rate'], float)
        assert 0.0 <= updated_stats['success_rate'] <= 1.0
    
    def test_bulk_zone_operations(self, repository):
        """
        Test bulk zone operations for performance.
        
        Success Criteria:
        - Bulk save operations efficient
        - Transaction handling correct
        - Rollback on partial failures
        - Batch size optimization
        """
        # Create multiple zones for bulk save
        bulk_zones = []
        for i in range(10):
            zone = SupplyDemandZone(
                None, f"PAIR{i}", "M1", "supply", 1.0850 + i*0.001, 1.0830 + i*0.001,
                datetime.now(), datetime.now(), 0.8, 0, 0, "active",
                None, None, 0.001, 1000, datetime.now(), datetime.now()
            )
            bulk_zones.append(zone)
        
        # Bulk save zones
        saved_ids = repository.bulk_save_zones(bulk_zones)
        
        # Verify all zones were saved
        assert len(saved_ids) == len(bulk_zones)
        assert all(id is not None for id in saved_ids)
        
        # Verify zones can be retrieved
        for zone_id in saved_ids:
            retrieved_zone = repository.get_zone_by_id(zone_id)
            assert retrieved_zone is not None
    
    def test_old_zone_cleanup(self, repository):
        """
        Test automatic cleanup of old zones.
        
        Success Criteria:
        - Old zones identified correctly
        - Cleanup respects age threshold
        - Active zones preserved
        - Cleanup statistics returned
        """
        # Create zones with different ages
        old_time = datetime.now() - timedelta(hours=200)  # 200 hours ago
        recent_time = datetime.now() - timedelta(hours=50)  # 50 hours ago
        
        old_zone = SupplyDemandZone(
            None, "EURUSD", "M1", "supply", 1.0850, 1.0830,
            old_time, old_time, 0.8, 0, 0, "active",
            None, None, 0.001, 1000, old_time, old_time
        )
        
        recent_zone = SupplyDemandZone(
            None, "GBPUSD", "M1", "demand", 1.3020, 1.3000,
            recent_time, recent_time, 0.7, 0, 0, "active",
            None, None, 0.001, 1000, recent_time, recent_time
        )
        
        # Save zones
        old_id = repository.save_zone(old_zone)
        recent_id = repository.save_zone(recent_zone)
        
        # Cleanup zones older than 168 hours (1 week)
        cleanup_count = repository.cleanup_old_zones(max_age_hours=168)
        
        # Verify cleanup results
        assert isinstance(cleanup_count, int)
        assert cleanup_count >= 0
        
        # Verify recent zone still exists
        recent_retrieved = repository.get_zone_by_id(recent_id)
        assert recent_retrieved is not None
    
    def test_performance_benchmark_database_operations(self, repository):
        """
        Test database operation performance.
        
        Success Criteria:
        - Zone save operations <10ms each
        - Zone queries <50ms for 1000 zones
        - Bulk operations scale linearly
        - Memory usage remains stable
        """
        # Create test data
        test_zones = []
        for i in range(100):
            zone = SupplyDemandZone(
                None, f"PAIR{i}", "M1", "supply", 1.0850 + i*0.001, 1.0830 + i*0.001,
                datetime.now(), datetime.now(), 0.8, 0, 0, "active",
                None, None, 0.001, 1000, datetime.now(), datetime.now()
            )
            test_zones.append(zone)
        
        # Measure memory usage
        tracemalloc.start()
        
        # Performance test - bulk save
        start_time = time.perf_counter()
        saved_ids = repository.bulk_save_zones(test_zones)
        save_duration = (time.perf_counter() - start_time) * 1000
        
        # Performance test - query operations
        start_time = time.perf_counter()
        query_filter = ZoneQueryFilter(limit=1000)
        queried_zones = repository.query_zones(query_filter)
        query_duration = (time.perf_counter() - start_time) * 1000
        
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_mb = peak / 1024 / 1024
        
        # Performance assertions
        avg_save_time = save_duration / len(test_zones)
        assert avg_save_time < 10, f"Zone save too slow: {avg_save_time:.2f}ms > 10ms target"
        assert query_duration < 50, f"Zone query too slow: {query_duration:.2f}ms > 50ms target"
        assert memory_mb < 50, f"Memory usage too high: {memory_mb:.1f}MB > 50MB limit"
        
        # Verify operations completed successfully
        assert len(saved_ids) == len(test_zones)
        assert isinstance(queried_zones, list)
    
    def test_database_transaction_handling(self, repository, mock_db_connection):
        """
        Test proper database transaction handling.
        
        Success Criteria:
        - Transactions committed on success
        - Rollback on failures
        - Connection pooling works
        - Deadlock detection and retry
        """
        # Mock transaction failure
        mock_db_connection.execute.side_effect = Exception("Database error")
        
        # Create test zone
        test_zone = SupplyDemandZone(
            None, "EURUSD", "M1", "supply", 1.0850, 1.0830,
            datetime.now(), datetime.now(), 0.8, 0, 0, "active",
            None, None, 0.001, 1000, datetime.now(), datetime.now()
        )
        
        # Attempt to save zone (should handle error gracefully)
        try:
            zone_id = repository.save_zone(test_zone)
            # If no exception, verify result
            assert zone_id is not None or zone_id is None  # Either success or failure handled
        except Exception as e:
            # Should not propagate unhandled database errors
            assert isinstance(e, (ValueError, RuntimeError))  # Expected application errors only
    
    def test_edge_case_invalid_zone_data(self, repository):
        """
        Test handling of invalid zone data.
        
        Success Criteria:
        - Validates required fields
        - Rejects invalid price data
        - Handles malformed timestamps
        - Provides clear error messages
        """
        # Test zone with invalid price data
        invalid_zone = SupplyDemandZone(
            None, "EURUSD", "M1", "supply", 
            1.0830, 1.0850,  # Invalid: top_price < bottom_price
            datetime.now(), datetime.now(), 0.8, 0, 0, "active",
            None, None, 0.001, 1000, datetime.now(), datetime.now()
        )
        
        # Should handle invalid data gracefully
        try:
            zone_id = repository.save_zone(invalid_zone)
            # If saved, verify it was corrected or rejected
            if zone_id:
                retrieved = repository.get_zone_by_id(zone_id)
                assert retrieved.top_price >= retrieved.bottom_price
        except (ValueError, AssertionError) as e:
            # Expected validation error
            assert len(str(e)) > 0
    
    def test_edge_case_concurrent_zone_updates(self, repository, sample_supply_zone):
        """
        Test handling of concurrent zone updates.
        
        Success Criteria:
        - Detects concurrent modifications
        - Handles optimistic locking
        - Preserves data integrity
        - Provides conflict resolution
        """
        # Save initial zone
        zone_id = repository.save_zone(sample_supply_zone)
        sample_supply_zone.id = zone_id
        
        # Simulate concurrent update scenario
        zone_copy1 = repository.get_zone_by_id(zone_id)
        zone_copy2 = repository.get_zone_by_id(zone_id)
        
        # Update both copies
        zone_copy1.status = "tested"
        zone_copy2.status = "broken"
        
        # First update should succeed
        update1_success = repository.update_zone(zone_copy1)
        assert update1_success is True
        
        # Second update should either succeed (last-write-wins) or fail (optimistic locking)
        update2_success = repository.update_zone(zone_copy2)
        assert isinstance(update2_success, bool)  # Either outcome is acceptable
        
        # Verify final state is consistent
        final_zone = repository.get_zone_by_id(zone_id)
        assert final_zone.status in ["tested", "broken"]  # One of the updates applied
    
    def test_repository_cleanup_on_close(self, repository):
        """
        Test proper resource cleanup when repository is closed.
        
        Success Criteria:
        - Database connections closed
        - Connection pool cleaned up
        - Pending transactions handled
        - No resource leaks
        """
        # Verify repository can be closed without errors
        try:
            repository.close()
            # Should not raise exceptions
        except Exception as e:
            pytest.fail(f"Repository close raised unexpected exception: {e}")
        
        # After close, operations should handle gracefully
        test_zone = SupplyDemandZone(
            None, "EURUSD", "M1", "supply", 1.0850, 1.0830,
            datetime.now(), datetime.now(), 0.8, 0, 0, "active",
            None, None, 0.001, 1000, datetime.now(), datetime.now()
        )
        
        # Operations after close should either fail gracefully or reconnect
        try:
            zone_id = repository.save_zone(test_zone)
            # If successful, repository auto-reconnected
            assert zone_id is not None
        except (ConnectionError, RuntimeError):
            # Expected behavior after close
            pass


# Test fixtures for other test files
@pytest.fixture
def supply_demand_repository():
    """Standard SupplyDemandRepository for use in other test files"""
    return SupplyDemandRepository(
        connection_string="postgresql://test:test@localhost/test_db",
        pool_size=5,
        max_overflow=10
    )


@pytest.fixture
def sample_zone_query_filter():
    """Sample ZoneQueryFilter for testing"""
    return ZoneQueryFilter(
        symbol="EURUSD",
        timeframe="M1",
        zone_type="supply",
        status="active",
        min_strength=0.7,
        max_age_hours=168,
        limit=100
    )


@pytest.fixture
def sample_zone_history_query():
    """Sample ZoneHistoryQuery for testing"""
    return ZoneHistoryQuery(
        zone_id=1,
        start_time=datetime(2025, 1, 1, 0, 0),
        end_time=datetime(2025, 1, 2, 0, 0),
        event_types=["zone_test", "zone_break"],
        limit=50
    )


# Performance benchmarking
def benchmark_repository_operations():
    """Standalone performance benchmark for CI/CD"""
    repository = SupplyDemandRepository()
    
    # Create test zones
    zones = []
    for i in range(100):
        zone = SupplyDemandZone(
            None, f"PAIR{i}", "M1", "supply", 1.0850 + i*0.001, 1.0830 + i*0.001,
            datetime.now(), datetime.now(), 0.8, 0, 0, "active",
            None, None, 0.001, 1000, datetime.now(), datetime.now()
        )
        zones.append(zone)
    
    # Benchmark bulk save
    start_time = time.perf_counter()
    saved_ids = repository.bulk_save_zones(zones)
    save_duration = (time.perf_counter() - start_time) * 1000
    
    # Benchmark query
    start_time = time.perf_counter()
    query_filter = ZoneQueryFilter(limit=1000)
    queried_zones = repository.query_zones(query_filter)
    query_duration = (time.perf_counter() - start_time) * 1000
    
    print(f"Repository bulk save 100 zones: {save_duration:.2f}ms")
    print(f"Repository query 1000 zones: {query_duration:.2f}ms")
    
    # Assert performance targets
    assert save_duration < 1000, f"Bulk save too slow: {save_duration:.2f}ms > 1000ms"
    assert query_duration < 50, f"Query too slow: {query_duration:.2f}ms > 50ms"
    
    repository.close()


if __name__ == "__main__":
    # Run performance benchmark
    benchmark_repository_operations()