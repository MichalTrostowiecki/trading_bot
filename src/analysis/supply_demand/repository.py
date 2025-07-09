"""
SupplyDemandRepository - Professional Database Layer

Handles all database operations for supply/demand zones including CRUD operations,
history tracking, statistics calculation, and performance optimization.

Performance Target: <10ms per zone save, <50ms per 1000 zone query
"""

import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import pandas as pd

from .zone_detector import SupplyDemandZone
from .zone_state_manager import ZoneStateUpdate, ZoneTestEvent
from .base_candle_detector import BaseCandleRange
from .big_move_detector import BigMove

logger = logging.getLogger(__name__)


@dataclass
class ZoneQueryFilter:
    """
    Filter criteria for zone queries.
    
    Provides flexible filtering options for zone retrieval.
    """
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    zone_type: Optional[str] = None  # 'supply', 'demand', 'continuation'
    status: Optional[str] = None     # 'active', 'tested', 'broken', 'expired'
    min_strength: Optional[float] = None
    max_strength: Optional[float] = None
    min_age_hours: Optional[int] = None
    max_age_hours: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class ZoneHistoryQuery:
    """
    Query parameters for zone history retrieval.
    
    Enables filtered historical analysis of zone events.
    """
    zone_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[str]] = None  # ['zone_test', 'zone_break', 'zone_flip']
    trigger_reasons: Optional[List[str]] = None
    success_only: Optional[bool] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class SupplyDemandRepository:
    """
    Professional database layer for supply/demand zone management.
    
    Provides optimized CRUD operations, history tracking, and statistics calculation
    with connection pooling and transaction management.
    
    Performance Target: <10ms per zone save, <50ms per 1000 zone query
    """
    
    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False
    ):
        """
        Initialize repository with database connection.
        
        Args:
            connection_string: PostgreSQL connection string
            pool_size: Base connection pool size
            max_overflow: Maximum additional connections
            echo: Enable SQL query logging
            
        Raises:
            ConnectionError: If database connection fails
            ValueError: If connection string is invalid
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
        
        # Initialize connection pool
        try:
            self._connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=pool_size + max_overflow,
                dsn=connection_string
            )
            
            # Test connection and create tables if needed
            self._initialize_schema()
            
            logger.info(f"SupplyDemandRepository initialized with pool_size={pool_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    def _initialize_schema(self) -> None:
        """Initialize database schema if tables don't exist"""
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Create zones table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_demand_zones (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    zone_type VARCHAR(20) NOT NULL,
                    top_price DECIMAL(12, 6) NOT NULL,
                    bottom_price DECIMAL(12, 6) NOT NULL,
                    left_time TIMESTAMP NOT NULL,
                    right_time TIMESTAMP NOT NULL,
                    strength_score DECIMAL(4, 3) NOT NULL,
                    test_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'active',
                    base_range_data JSONB,
                    big_move_data JSONB,
                    atr_at_creation DECIMAL(10, 8),
                    volume_at_creation DECIMAL(15, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create zone updates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zone_state_updates (
                    id SERIAL PRIMARY KEY,
                    zone_id INTEGER REFERENCES supply_demand_zones(id) ON DELETE CASCADE,
                    old_status VARCHAR(20) NOT NULL,
                    new_status VARCHAR(20) NOT NULL,
                    update_time TIMESTAMP NOT NULL,
                    trigger_price DECIMAL(12, 6) NOT NULL,
                    trigger_reason VARCHAR(50) NOT NULL,
                    test_success BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create test events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zone_test_events (
                    id SERIAL PRIMARY KEY,
                    zone_id INTEGER REFERENCES supply_demand_zones(id) ON DELETE CASCADE,
                    test_time TIMESTAMP NOT NULL,
                    test_price DECIMAL(12, 6) NOT NULL,
                    test_type VARCHAR(20) NOT NULL,
                    success BOOLEAN NOT NULL,
                    reaction_strength DECIMAL(4, 3) DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_zones_symbol_timeframe 
                ON supply_demand_zones(symbol, timeframe);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_zones_status_created 
                ON supply_demand_zones(status, created_at);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_updates_zone_time 
                ON zone_state_updates(zone_id, update_time);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_zone_time 
                ON zone_test_events(zone_id, test_time);
            """)
            
            connection.commit()
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            connection.rollback()
            raise
        finally:
            self._return_connection(connection)
    
    def _get_connection(self):
        """Get connection from pool"""
        return self._connection_pool.getconn()
    
    def _return_connection(self, connection) -> None:
        """Return connection to pool"""
        self._connection_pool.putconn(connection)
    
    def save_zone(self, zone: SupplyDemandZone) -> int:
        """
        Save supply/demand zone to database.
        
        Args:
            zone: SupplyDemandZone object to save
            
        Returns:
            Generated zone ID
            
        Raises:
            ValueError: If zone data is invalid
            RuntimeError: If database operation fails
            
        Performance: <10ms per zone
        """
        if not self._validate_zone_data(zone):
            raise ValueError("Invalid zone data provided")
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Serialize complex objects
            base_range_json = self._serialize_base_range(zone.base_range) if zone.base_range else None
            big_move_json = self._serialize_big_move(zone.big_move) if zone.big_move else None
            
            # Insert zone
            cursor.execute("""
                INSERT INTO supply_demand_zones (
                    symbol, timeframe, zone_type, top_price, bottom_price,
                    left_time, right_time, strength_score, test_count, success_count,
                    status, base_range_data, big_move_data, atr_at_creation,
                    volume_at_creation, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
            """, (
                zone.symbol, zone.timeframe, zone.zone_type, zone.top_price, zone.bottom_price,
                zone.left_time, zone.right_time, zone.strength_score, zone.test_count,
                zone.success_count, zone.status, base_range_json, big_move_json,
                zone.atr_at_creation, zone.volume_at_creation, zone.created_at, zone.updated_at
            ))
            
            zone_id = cursor.fetchone()[0]
            connection.commit()
            
            logger.debug(f"Saved zone {zone_id} for {zone.symbol} {zone.timeframe}")
            return zone_id
            
        except Exception as e:
            logger.error(f"Failed to save zone: {e}")
            connection.rollback()
            raise RuntimeError(f"Zone save failed: {e}")
        finally:
            self._return_connection(connection)
    
    def get_zone_by_id(self, zone_id: int) -> Optional[SupplyDemandZone]:
        """
        Retrieve zone by ID.
        
        Args:
            zone_id: Zone ID to retrieve
            
        Returns:
            SupplyDemandZone object or None if not found
        """
        if zone_id is None or zone_id <= 0:
            return None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM supply_demand_zones WHERE id = %s;
            """, (zone_id,))
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_zone(dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve zone {zone_id}: {e}")
            return None
        finally:
            self._return_connection(connection)
    
    def update_zone(self, zone: SupplyDemandZone) -> bool:
        """
        Update existing zone in database.
        
        Args:
            zone: SupplyDemandZone object with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        if zone.id is None or zone.id <= 0:
            return False
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Update zone with current timestamp
            zone.updated_at = datetime.now()
            
            # Serialize complex objects
            base_range_json = self._serialize_base_range(zone.base_range) if zone.base_range else None
            big_move_json = self._serialize_big_move(zone.big_move) if zone.big_move else None
            
            cursor.execute("""
                UPDATE supply_demand_zones SET
                    symbol = %s, timeframe = %s, zone_type = %s,
                    top_price = %s, bottom_price = %s, left_time = %s, right_time = %s,
                    strength_score = %s, test_count = %s, success_count = %s,
                    status = %s, base_range_data = %s, big_move_data = %s,
                    atr_at_creation = %s, volume_at_creation = %s, updated_at = %s
                WHERE id = %s;
            """, (
                zone.symbol, zone.timeframe, zone.zone_type, zone.top_price,
                zone.bottom_price, zone.left_time, zone.right_time, zone.strength_score,
                zone.test_count, zone.success_count, zone.status, base_range_json,
                big_move_json, zone.atr_at_creation, zone.volume_at_creation,
                zone.updated_at, zone.id
            ))
            
            rows_affected = cursor.rowcount
            connection.commit()
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update zone {zone.id}: {e}")
            connection.rollback()
            return False
        finally:
            self._return_connection(connection)
    
    def delete_zone(self, zone_id: int) -> bool:
        """
        Delete zone from database.
        
        Args:
            zone_id: Zone ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if zone_id is None or zone_id <= 0:
            return False
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                DELETE FROM supply_demand_zones WHERE id = %s;
            """, (zone_id,))
            
            rows_affected = cursor.rowcount
            connection.commit()
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete zone {zone_id}: {e}")
            connection.rollback()
            return False
        finally:
            self._return_connection(connection)
    
    def query_zones(self, filter_criteria: ZoneQueryFilter) -> List[SupplyDemandZone]:
        """
        Query zones with filtering criteria.
        
        Args:
            filter_criteria: ZoneQueryFilter with filter options
            
        Returns:
            List of matching SupplyDemandZone objects
            
        Performance: <50ms for 1000 zones
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Build dynamic query
            query_parts = ["SELECT * FROM supply_demand_zones WHERE 1=1"]
            params = []
            
            if filter_criteria.symbol:
                query_parts.append("AND symbol = %s")
                params.append(filter_criteria.symbol)
            
            if filter_criteria.timeframe:
                query_parts.append("AND timeframe = %s")
                params.append(filter_criteria.timeframe)
            
            if filter_criteria.zone_type:
                query_parts.append("AND zone_type = %s")
                params.append(filter_criteria.zone_type)
            
            if filter_criteria.status:
                query_parts.append("AND status = %s")
                params.append(filter_criteria.status)
            
            if filter_criteria.min_strength is not None:
                query_parts.append("AND strength_score >= %s")
                params.append(filter_criteria.min_strength)
            
            if filter_criteria.max_strength is not None:
                query_parts.append("AND strength_score <= %s")
                params.append(filter_criteria.max_strength)
            
            if filter_criteria.created_after:
                query_parts.append("AND created_at >= %s")
                params.append(filter_criteria.created_after)
            
            if filter_criteria.created_before:
                query_parts.append("AND created_at <= %s")
                params.append(filter_criteria.created_before)
            
            if filter_criteria.max_age_hours:
                cutoff_time = datetime.now() - timedelta(hours=filter_criteria.max_age_hours)
                query_parts.append("AND created_at >= %s")
                params.append(cutoff_time)
            
            # Add ordering
            query_parts.append("ORDER BY created_at DESC")
            
            # Add pagination
            if filter_criteria.limit:
                query_parts.append("LIMIT %s")
                params.append(filter_criteria.limit)
                
                if filter_criteria.offset:
                    query_parts.append("OFFSET %s")
                    params.append(filter_criteria.offset)
            
            query = " ".join(query_parts)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to zones
            zones = [self._row_to_zone(dict(row)) for row in rows]
            
            logger.debug(f"Queried {len(zones)} zones with filter criteria")
            return zones
            
        except Exception as e:
            logger.error(f"Failed to query zones: {e}")
            return []
        finally:
            self._return_connection(connection)
    
    def save_zone_update(self, update: ZoneStateUpdate) -> bool:
        """
        Save zone state update to database.
        
        Args:
            update: ZoneStateUpdate object to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO zone_state_updates (
                    zone_id, old_status, new_status, update_time,
                    trigger_price, trigger_reason, test_success
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                update.zone_id, update.old_status, update.new_status,
                update.update_time, update.trigger_price, update.trigger_reason,
                update.test_success
            ))
            
            connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save zone update: {e}")
            connection.rollback()
            return False
        finally:
            self._return_connection(connection)
    
    def save_test_event(self, event: ZoneTestEvent) -> bool:
        """
        Save zone test event to database.
        
        Args:
            event: ZoneTestEvent object to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO zone_test_events (
                    zone_id, test_time, test_price, test_type,
                    success, reaction_strength
                ) VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                event.zone_id, event.test_time, event.test_price,
                event.test_type, event.success, event.reaction_strength
            ))
            
            connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save test event: {e}")
            connection.rollback()
            return False
        finally:
            self._return_connection(connection)
    
    def get_zone_history(
        self,
        zone_id: int,
        query_params: Optional[ZoneHistoryQuery] = None
    ) -> List[ZoneStateUpdate]:
        """
        Get zone state update history.
        
        Args:
            zone_id: Zone ID to get history for
            query_params: Optional query parameters for filtering
            
        Returns:
            List of ZoneStateUpdate objects in chronological order
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            query_parts = ["""
                SELECT zone_id, old_status, new_status, update_time,
                       trigger_price, trigger_reason, test_success
                FROM zone_state_updates WHERE zone_id = %s
            """]
            params = [zone_id]
            
            if query_params:
                if query_params.start_time:
                    query_parts.append("AND update_time >= %s")
                    params.append(query_params.start_time)
                
                if query_params.end_time:
                    query_parts.append("AND update_time <= %s")
                    params.append(query_params.end_time)
                
                if query_params.trigger_reasons:
                    placeholders = ",".join(["%s"] * len(query_params.trigger_reasons))
                    query_parts.append(f"AND trigger_reason IN ({placeholders})")
                    params.extend(query_params.trigger_reasons)
                
                if query_params.success_only:
                    query_parts.append("AND test_success = TRUE")
            
            query_parts.append("ORDER BY update_time ASC")
            
            if query_params and query_params.limit:
                query_parts.append("LIMIT %s")
                params.append(query_params.limit)
            
            query = " ".join(query_parts)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to ZoneStateUpdate objects
            updates = []
            for row in rows:
                update = ZoneStateUpdate(
                    zone_id=row['zone_id'],
                    old_status=row['old_status'],
                    new_status=row['new_status'],
                    update_time=row['update_time'],
                    trigger_price=float(row['trigger_price']),
                    trigger_reason=row['trigger_reason'],
                    test_success=row['test_success']
                )
                updates.append(update)
            
            return updates
            
        except Exception as e:
            logger.error(f"Failed to get zone history for {zone_id}: {e}")
            return []
        finally:
            self._return_connection(connection)
    
    def get_test_events(
        self,
        zone_id: int,
        query_params: Optional[ZoneHistoryQuery] = None
    ) -> List[ZoneTestEvent]:
        """
        Get zone test events.
        
        Args:
            zone_id: Zone ID to get events for
            query_params: Optional query parameters for filtering
            
        Returns:
            List of ZoneTestEvent objects in chronological order
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            query_parts = ["""
                SELECT zone_id, test_time, test_price, test_type,
                       success, reaction_strength
                FROM zone_test_events WHERE zone_id = %s
            """]
            params = [zone_id]
            
            if query_params:
                if query_params.start_time:
                    query_parts.append("AND test_time >= %s")
                    params.append(query_params.start_time)
                
                if query_params.end_time:
                    query_parts.append("AND test_time <= %s")
                    params.append(query_params.end_time)
                
                if query_params.event_types:
                    placeholders = ",".join(["%s"] * len(query_params.event_types))
                    query_parts.append(f"AND test_type IN ({placeholders})")
                    params.extend(query_params.event_types)
                
                if query_params.success_only:
                    query_parts.append("AND success = TRUE")
            
            query_parts.append("ORDER BY test_time ASC")
            
            if query_params and query_params.limit:
                query_parts.append("LIMIT %s")
                params.append(query_params.limit)
            
            query = " ".join(query_parts)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to ZoneTestEvent objects
            events = []
            for row in rows:
                event = ZoneTestEvent(
                    zone_id=row['zone_id'],
                    test_time=row['test_time'],
                    test_price=float(row['test_price']),
                    test_type=row['test_type'],
                    success=row['success'],
                    reaction_strength=float(row['reaction_strength'])
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get test events for {zone_id}: {e}")
            return []
        finally:
            self._return_connection(connection)
    
    def get_zone_statistics(self, zone_id: int) -> Dict[str, Any]:
        """
        Get calculated statistics for a zone.
        
        Args:
            zone_id: Zone ID to get statistics for
            
        Returns:
            Dictionary with zone statistics
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Get test statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as test_count,
                    COUNT(*) FILTER (WHERE success = TRUE) as success_count,
                    AVG(reaction_strength) as avg_reaction_strength,
                    MAX(test_time) as last_test_time
                FROM zone_test_events 
                WHERE zone_id = %s;
            """, (zone_id,))
            
            stats_row = cursor.fetchone()
            
            if stats_row:
                test_count = stats_row['test_count'] or 0
                success_count = stats_row['success_count'] or 0
                success_rate = (success_count / test_count) if test_count > 0 else 0.0
                
                return {
                    'test_count': test_count,
                    'success_count': success_count,
                    'success_rate': success_rate,
                    'average_reaction_strength': float(stats_row['avg_reaction_strength'] or 0.0),
                    'last_test_time': stats_row['last_test_time'],
                    'total_penetrations': test_count  # All tests are penetrations
                }
            
            # Return default statistics
            return {
                'test_count': 0,
                'success_count': 0,
                'success_rate': 0.0,
                'average_reaction_strength': 0.0,
                'last_test_time': None,
                'total_penetrations': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get zone statistics for {zone_id}: {e}")
            return {
                'test_count': 0,
                'success_count': 0,
                'success_rate': 0.0,
                'average_reaction_strength': 0.0,
                'last_test_time': None,
                'total_penetrations': 0
            }
        finally:
            self._return_connection(connection)
    
    def bulk_save_zones(self, zones: List[SupplyDemandZone]) -> List[int]:
        """
        Bulk save multiple zones for performance.
        
        Args:
            zones: List of SupplyDemandZone objects to save
            
        Returns:
            List of generated zone IDs
        """
        if not zones:
            return []
        
        zone_ids = []
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Use batch insert for performance
            for zone in zones:
                if not self._validate_zone_data(zone):
                    logger.warning(f"Skipping invalid zone data for {zone.symbol}")
                    zone_ids.append(None)
                    continue
                
                # Serialize complex objects
                base_range_json = self._serialize_base_range(zone.base_range) if zone.base_range else None
                big_move_json = self._serialize_big_move(zone.big_move) if zone.big_move else None
                
                cursor.execute("""
                    INSERT INTO supply_demand_zones (
                        symbol, timeframe, zone_type, top_price, bottom_price,
                        left_time, right_time, strength_score, test_count, success_count,
                        status, base_range_data, big_move_data, atr_at_creation,
                        volume_at_creation, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id;
                """, (
                    zone.symbol, zone.timeframe, zone.zone_type, zone.top_price, zone.bottom_price,
                    zone.left_time, zone.right_time, zone.strength_score, zone.test_count,
                    zone.success_count, zone.status, base_range_json, big_move_json,
                    zone.atr_at_creation, zone.volume_at_creation, zone.created_at, zone.updated_at
                ))
                
                zone_id = cursor.fetchone()[0]
                zone_ids.append(zone_id)
            
            connection.commit()
            logger.info(f"Bulk saved {len(zone_ids)} zones")
            return zone_ids
            
        except Exception as e:
            logger.error(f"Failed to bulk save zones: {e}")
            connection.rollback()
            raise RuntimeError(f"Bulk zone save failed: {e}")
        finally:
            self._return_connection(connection)
    
    def cleanup_old_zones(self, max_age_hours: int) -> int:
        """
        Clean up zones older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of zones cleaned up
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Delete old zones (cascade will handle related records)
            cursor.execute("""
                DELETE FROM supply_demand_zones 
                WHERE created_at < %s AND status IN ('expired', 'broken');
            """, (cutoff_time,))
            
            cleanup_count = cursor.rowcount
            connection.commit()
            
            logger.info(f"Cleaned up {cleanup_count} old zones")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old zones: {e}")
            connection.rollback()
            return 0
        finally:
            self._return_connection(connection)
    
    def close(self) -> None:
        """Close connection pool and cleanup resources"""
        try:
            if hasattr(self, '_connection_pool'):
                self._connection_pool.closeall()
            logger.info("Repository connection pool closed")
        except Exception as e:
            logger.error(f"Error closing repository: {e}")
    
    def _validate_zone_data(self, zone: SupplyDemandZone) -> bool:
        """Validate zone data before saving"""
        if not zone.symbol or not zone.timeframe:
            return False
        
        if zone.top_price <= zone.bottom_price:
            return False
        
        if zone.strength_score < 0 or zone.strength_score > 1:
            return False
        
        if zone.zone_type not in ['supply', 'demand', 'continuation']:
            return False
        
        return True
    
    def _serialize_base_range(self, base_range: BaseCandleRange) -> str:
        """Serialize BaseCandleRange to JSON"""
        if not base_range:
            return None
        
        return json.dumps({
            'start_index': base_range.start_index,
            'end_index': base_range.end_index,
            'start_time': base_range.start_time.isoformat(),
            'end_time': base_range.end_time.isoformat(),
            'high': float(base_range.high),
            'low': float(base_range.low),
            'atr_at_creation': float(base_range.atr_at_creation),
            'candle_count': base_range.candle_count,
            'consolidation_score': float(base_range.consolidation_score)
        })
    
    def _serialize_big_move(self, big_move: BigMove) -> str:
        """Serialize BigMove to JSON"""
        if not big_move:
            return None
        
        return json.dumps({
            'start_index': big_move.start_index,
            'end_index': big_move.end_index,
            'start_time': big_move.start_time.isoformat(),
            'end_time': big_move.end_time.isoformat(),
            'direction': big_move.direction,
            'magnitude': float(big_move.magnitude),
            'momentum_score': float(big_move.momentum_score),
            'breakout_level': float(big_move.breakout_level),
            'volume_confirmation': big_move.volume_confirmation
        })
    
    def _deserialize_base_range(self, json_data: str) -> Optional[BaseCandleRange]:
        """Deserialize BaseCandleRange from JSON"""
        if not json_data:
            return None
        
        try:
            data = json.loads(json_data)
            return BaseCandleRange(
                start_index=data['start_index'],
                end_index=data['end_index'],
                start_time=datetime.fromisoformat(data['start_time']),
                end_time=datetime.fromisoformat(data['end_time']),
                high=data['high'],
                low=data['low'],
                atr_at_creation=data['atr_at_creation'],
                candle_count=data['candle_count'],
                consolidation_score=data['consolidation_score']
            )
        except Exception as e:
            logger.warning(f"Failed to deserialize base range: {e}")
            return None
    
    def _deserialize_big_move(self, json_data: str) -> Optional[BigMove]:
        """Deserialize BigMove from JSON"""
        if not json_data:
            return None
        
        try:
            data = json.loads(json_data)
            return BigMove(
                start_index=data['start_index'],
                end_index=data['end_index'],
                start_time=datetime.fromisoformat(data['start_time']),
                end_time=datetime.fromisoformat(data['end_time']),
                direction=data['direction'],
                magnitude=data['magnitude'],
                momentum_score=data['momentum_score'],
                breakout_level=data['breakout_level'],
                volume_confirmation=data['volume_confirmation']
            )
        except Exception as e:
            logger.warning(f"Failed to deserialize big move: {e}")
            return None
    
    def _row_to_zone(self, row: Dict[str, Any]) -> SupplyDemandZone:
        """Convert database row to SupplyDemandZone object"""
        # Deserialize complex objects
        base_range = self._deserialize_base_range(row.get('base_range_data'))
        big_move = self._deserialize_big_move(row.get('big_move_data'))
        
        return SupplyDemandZone(
            id=row['id'],
            symbol=row['symbol'],
            timeframe=row['timeframe'],
            zone_type=row['zone_type'],
            top_price=float(row['top_price']),
            bottom_price=float(row['bottom_price']),
            left_time=row['left_time'],
            right_time=row['right_time'],
            strength_score=float(row['strength_score']),
            test_count=row['test_count'],
            success_count=row['success_count'],
            status=row['status'],
            base_range=base_range,
            big_move=big_move,
            atr_at_creation=float(row['atr_at_creation']) if row['atr_at_creation'] else 0.0,
            volume_at_creation=float(row['volume_at_creation']) if row['volume_at_creation'] else 0.0,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


def create_test_repository() -> SupplyDemandRepository:
    """Create repository with test-friendly configuration"""
    return SupplyDemandRepository(
        connection_string="postgresql://test:test@localhost/test_supply_demand",
        pool_size=2,
        max_overflow=3,
        echo=False
    )