"""
ZoneStateManager - Professional Zone Lifecycle Management

Manages supply/demand zone states including testing detection, flip detection,
expiry management, and state transitions using institutional order flow analysis.

Performance Target: <50ms for 100 zones with 1000 price bars
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .zone_detector import SupplyDemandZone

logger = logging.getLogger(__name__)


@dataclass
class ZoneStateUpdate:
    """
    Represents a zone state change event.
    
    Tracks all zone lifecycle transitions for analysis and backtesting.
    """
    zone_id: int
    old_status: str
    new_status: str
    update_time: datetime
    trigger_price: float
    trigger_reason: str  # 'zone_test', 'zone_break', 'zone_flip', 'age_expiry'
    test_success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
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
    """
    Represents a zone test event with reaction analysis.
    
    Captures institutional reaction strength for zone quality assessment.
    """
    zone_id: int
    test_time: datetime
    test_price: float
    test_type: str  # 'touch', 'penetration', 'break'
    success: bool
    reaction_strength: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'zone_id': self.zone_id,
            'test_time': self.test_time,
            'test_price': self.test_price,
            'test_type': self.test_type,
            'success': self.success,
            'reaction_strength': self.reaction_strength
        }


class ZoneStateManager:
    """
    Manages supply/demand zone states including testing detection, flip detection,
    expiry management, and state transitions.
    
    Provides real-time zone lifecycle management for institutional order flow analysis.
    Performance Target: <50ms for 100 zones with 1000 price bars
    """
    
    def __init__(
        self,
        test_penetration_threshold: float = 0.1,      # 10% penetration for test
        break_threshold: float = 0.3,                 # 30% penetration breaks zone
        flip_confirmation_bars: int = 3,              # Bars needed to confirm flip
        max_test_attempts: int = 5,                   # Max tests before weak zone
        zone_expiry_hours: int = 168,                 # 1 week zone expiry
        reaction_strength_threshold: float = 0.6      # 60% reaction for success
    ):
        """
        Initialize zone state manager.
        
        Args:
            test_penetration_threshold: % of zone penetration to trigger test
            break_threshold: % of zone penetration to break zone
            flip_confirmation_bars: Bars required to confirm zone flip
            max_test_attempts: Maximum test attempts before marking weak
            zone_expiry_hours: Hours before zone expires
            reaction_strength_threshold: Minimum reaction strength for success
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_parameters(
            test_penetration_threshold, break_threshold, flip_confirmation_bars,
            max_test_attempts, zone_expiry_hours, reaction_strength_threshold
        )
        
        self.test_penetration_threshold = test_penetration_threshold
        self.break_threshold = break_threshold
        self.flip_confirmation_bars = flip_confirmation_bars
        self.max_test_attempts = max_test_attempts
        self.zone_expiry_hours = zone_expiry_hours
        self.reaction_strength_threshold = reaction_strength_threshold
        
        # Internal state tracking
        self._zones: Dict[int, SupplyDemandZone] = {}
        self._zone_updates: List[ZoneStateUpdate] = []
        self._test_events: List[ZoneTestEvent] = []
        self._zone_statistics: Dict[int, Dict[str, Any]] = {}
        
        logger.debug(f"ZoneStateManager initialized with test_threshold={test_penetration_threshold}")
    
    def _validate_parameters(
        self,
        test_penetration_threshold: float,
        break_threshold: float,
        flip_confirmation_bars: int,
        max_test_attempts: int,
        zone_expiry_hours: int,
        reaction_strength_threshold: float
    ) -> None:
        """Validate initialization parameters"""
        if not 0.0 < test_penetration_threshold <= 1.0:
            raise ValueError(f"test_penetration_threshold must be 0.0-1.0, got {test_penetration_threshold}")
        
        if not 0.0 < break_threshold <= 1.0:
            raise ValueError(f"break_threshold must be 0.0-1.0, got {break_threshold}")
        
        if test_penetration_threshold >= break_threshold:
            raise ValueError(f"test_penetration_threshold ({test_penetration_threshold}) must be < break_threshold ({break_threshold})")
        
        if flip_confirmation_bars < 1:
            raise ValueError(f"flip_confirmation_bars must be >= 1, got {flip_confirmation_bars}")
        
        if max_test_attempts < 1:
            raise ValueError(f"max_test_attempts must be >= 1, got {max_test_attempts}")
        
        if zone_expiry_hours < 1:
            raise ValueError(f"zone_expiry_hours must be >= 1, got {zone_expiry_hours}")
        
        if not 0.0 <= reaction_strength_threshold <= 1.0:
            raise ValueError(f"reaction_strength_threshold must be 0.0-1.0, got {reaction_strength_threshold}")
    
    def update_zone_states(
        self,
        zones: List[SupplyDemandZone],
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> List[ZoneStateUpdate]:
        """
        Update all zone states based on current price action.
        
        Args:
            zones: List of zones to update
            price_data: Recent OHLC price data
            current_time: Current timestamp
            
        Returns:
            List of zone state updates
            
        Performance: <50ms for 100 zones with 1000 price bars
        """
        if not zones or price_data.empty:
            return []
        
        try:
            # Update internal zone tracking
            self._update_zone_cache(zones)
            
            # Collect all state updates
            all_updates = []
            
            # 1. Detect zone tests and breaks
            test_updates = self._detect_zone_interactions(zones, price_data, current_time)
            all_updates.extend(test_updates)
            
            # 2. Detect zone flips
            flip_updates = self.detect_zone_flips(zones, price_data, current_time)
            all_updates.extend(flip_updates)
            
            # 3. Handle zone expiry
            expiry_updates = self.expire_old_zones(zones, current_time)
            all_updates.extend(expiry_updates)
            
            # 4. Update zone statistics
            self._update_zone_statistics(zones, all_updates)
            
            # Store updates for history
            self._zone_updates.extend(all_updates)
            
            logger.debug(f"Updated {len(zones)} zones, generated {len(all_updates)} state changes")
            return all_updates
            
        except Exception as e:
            logger.error(f"Error updating zone states: {e}")
            return []
    
    def detect_zone_tests(
        self,
        zones: List[SupplyDemandZone],
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> List[ZoneTestEvent]:
        """
        Detect zone test events based on price interaction.
        
        Args:
            zones: List of zones to check
            price_data: Recent OHLC price data
            current_time: Current timestamp
            
        Returns:
            List of zone test events
        """
        if not zones or price_data.empty:
            return []
        
        test_events = []
        
        for zone in zones:
            if zone.status not in ['active', 'tested']:
                continue
            
            try:
                # Check for price interaction with zone
                zone_tests = self._analyze_zone_interaction(zone, price_data, current_time)
                test_events.extend(zone_tests)
                
            except Exception as e:
                logger.warning(f"Error analyzing zone {zone.id} interaction: {e}")
                continue
        
        # Store test events for history
        self._test_events.extend(test_events)
        
        return test_events
    
    def detect_zone_flips(
        self,
        zones: List[SupplyDemandZone],
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> List[ZoneStateUpdate]:
        """
        Detect zone flips (supply becomes demand or vice versa).
        
        Args:
            zones: List of zones to check
            price_data: Recent OHLC price data
            current_time: Current timestamp
            
        Returns:
            List of zone flip updates
        """
        if not zones or price_data.empty:
            return []
        
        if len(price_data) < self.flip_confirmation_bars:
            logger.debug(f"Insufficient data for flip confirmation: {len(price_data)} < {self.flip_confirmation_bars}")
            return []
        
        flip_updates = []
        
        for zone in zones:
            if zone.status not in ['active', 'tested']:
                continue
            
            try:
                # Check for zone flip conditions
                flip_update = self._detect_zone_flip(zone, price_data, current_time)
                if flip_update:
                    flip_updates.append(flip_update)
                    
            except Exception as e:
                logger.warning(f"Error detecting zone {zone.id} flip: {e}")
                continue
        
        return flip_updates
    
    def expire_old_zones(
        self,
        zones: List[SupplyDemandZone],
        current_time: datetime
    ) -> List[ZoneStateUpdate]:
        """
        Expire zones based on age threshold.
        
        Args:
            zones: List of zones to check
            current_time: Current timestamp
            
        Returns:
            List of expiry updates
        """
        if not zones:
            return []
        
        expiry_updates = []
        expiry_threshold = timedelta(hours=self.zone_expiry_hours)
        
        for zone in zones:
            if zone.status in ['expired', 'broken']:
                continue
            
            try:
                zone_age = current_time - zone.created_at
                
                if zone_age > expiry_threshold:
                    # Create expiry update
                    expiry_update = ZoneStateUpdate(
                        zone_id=zone.id,
                        old_status=zone.status,
                        new_status='expired',
                        update_time=current_time,
                        trigger_price=zone.center,
                        trigger_reason='age_expiry',
                        test_success=False
                    )
                    
                    expiry_updates.append(expiry_update)
                    logger.debug(f"Expired zone {zone.id} after {zone_age.total_seconds()/3600:.1f} hours")
                    
            except Exception as e:
                logger.warning(f"Error checking zone {zone.id} expiry: {e}")
                continue
        
        return expiry_updates
    
    def get_zone_history(self, zone_id: int) -> List[ZoneStateUpdate]:
        """
        Get complete history of zone state changes.
        
        Args:
            zone_id: Zone ID to get history for
            
        Returns:
            List of zone state updates in chronological order
        """
        zone_history = [
            update for update in self._zone_updates 
            if update.zone_id == zone_id
        ]
        
        # Sort by update time
        zone_history.sort(key=lambda x: x.update_time)
        
        return zone_history
    
    def get_test_statistics(self, zone_id: int) -> Dict[str, Any]:
        """
        Get zone test statistics.
        
        Args:
            zone_id: Zone ID to get statistics for
            
        Returns:
            Dictionary with test statistics
        """
        if zone_id in self._zone_statistics:
            return self._zone_statistics[zone_id].copy()
        
        # Return default statistics
        return {
            'test_count': 0,
            'success_count': 0,
            'success_rate': 0.0,
            'average_reaction_strength': 0.0,
            'last_test_time': None,
            'total_penetrations': 0
        }
    
    def _update_zone_cache(self, zones: List[SupplyDemandZone]) -> None:
        """Update internal zone cache for tracking"""
        for zone in zones:
            if zone.id is not None:
                self._zones[zone.id] = zone
    
    def _detect_zone_interactions(
        self,
        zones: List[SupplyDemandZone],
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> List[ZoneStateUpdate]:
        """
        Detect zone interactions and generate state updates.
        
        Args:
            zones: List of zones to analyze
            price_data: Price data for analysis
            current_time: Current timestamp
            
        Returns:
            List of state updates from zone interactions
        """
        state_updates = []
        
        for zone in zones:
            if zone.status not in ['active', 'tested']:
                continue
            
            try:
                # Analyze interaction
                interaction_result = self._analyze_zone_penetration(zone, price_data)
                
                if interaction_result:
                    penetration_pct, trigger_price, interaction_type = interaction_result
                    
                    # Determine new status based on penetration
                    new_status = self._classify_zone_interaction(
                        zone, penetration_pct, interaction_type
                    )
                    
                    if new_status != zone.status:
                        # Create state update
                        update = ZoneStateUpdate(
                            zone_id=zone.id,
                            old_status=zone.status,
                            new_status=new_status,
                            update_time=current_time,
                            trigger_price=trigger_price,
                            trigger_reason=self._get_trigger_reason(interaction_type, penetration_pct),
                            test_success=self._is_test_successful(zone, interaction_type, penetration_pct)
                        )
                        
                        state_updates.append(update)
                        
            except Exception as e:
                logger.warning(f"Error analyzing zone {zone.id} interaction: {e}")
                continue
        
        return state_updates
    
    def _analyze_zone_interaction(
        self,
        zone: SupplyDemandZone,
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> List[ZoneTestEvent]:
        """
        Analyze price interaction with a specific zone.
        
        Args:
            zone: Zone to analyze
            price_data: Price data for analysis
            current_time: Current timestamp
            
        Returns:
            List of test events for this zone
        """
        test_events = []
        
        for _, candle in price_data.iterrows():
            # Check if price interacts with zone
            interaction = self._check_price_zone_interaction(zone, candle)
            
            if interaction:
                test_type, test_price, penetration_pct = interaction
                
                # Calculate reaction strength
                reaction_strength = self._calculate_reaction_strength(
                    zone, candle, price_data, test_type
                )
                
                # Determine test success
                test_success = (
                    reaction_strength >= self.reaction_strength_threshold and
                    penetration_pct < self.break_threshold
                )
                
                # Create test event
                test_event = ZoneTestEvent(
                    zone_id=zone.id,
                    test_time=candle['time'],
                    test_price=test_price,
                    test_type=test_type,
                    success=test_success,
                    reaction_strength=reaction_strength
                )
                
                test_events.append(test_event)
        
        return test_events
    
    def _analyze_zone_penetration(
        self,
        zone: SupplyDemandZone,
        price_data: pd.DataFrame
    ) -> Optional[Tuple[float, float, str]]:
        """
        Analyze the deepest penetration of zone by price.
        
        Args:
            zone: Zone to analyze
            price_data: Price data for analysis
            
        Returns:
            Tuple of (penetration_percentage, trigger_price, interaction_type) or None
        """
        max_penetration = 0.0
        trigger_price = zone.center
        interaction_type = 'touch'
        
        zone_height = zone.height
        if zone_height <= 0:
            return None
        
        for _, candle in price_data.iterrows():
            # Check penetration based on zone type
            if zone.zone_type == 'supply':
                # For supply zones, check upward penetration
                if candle['high'] > zone.bottom_price:
                    if candle['high'] >= zone.top_price:
                        # Complete penetration
                        penetration = 1.0
                        trigger_price = candle['high']
                        interaction_type = 'break'
                    else:
                        # Partial penetration
                        penetration = (candle['high'] - zone.bottom_price) / zone_height
                        trigger_price = candle['high']
                        interaction_type = 'penetration' if penetration > self.test_penetration_threshold else 'touch'
                    
                    max_penetration = max(max_penetration, penetration)
            
            elif zone.zone_type == 'demand':
                # For demand zones, check downward penetration
                if candle['low'] < zone.top_price:
                    if candle['low'] <= zone.bottom_price:
                        # Complete penetration
                        penetration = 1.0
                        trigger_price = candle['low']
                        interaction_type = 'break'
                    else:
                        # Partial penetration
                        penetration = (zone.top_price - candle['low']) / zone_height
                        trigger_price = candle['low']
                        interaction_type = 'penetration' if penetration > self.test_penetration_threshold else 'touch'
                    
                    max_penetration = max(max_penetration, penetration)
        
        if max_penetration > 0:
            return max_penetration, trigger_price, interaction_type
        
        return None
    
    def _check_price_zone_interaction(
        self,
        zone: SupplyDemandZone,
        candle: pd.Series
    ) -> Optional[Tuple[str, float, float]]:
        """
        Check if a single candle interacts with zone.
        
        Args:
            zone: Zone to check
            candle: Single candle data
            
        Returns:
            Tuple of (test_type, test_price, penetration_pct) or None
        """
        zone_height = zone.height
        if zone_height <= 0:
            return None
        
        if zone.zone_type == 'supply':
            # Check upward interaction with supply zone
            if candle['high'] >= zone.bottom_price:
                test_price = candle['high']
                
                if candle['high'] >= zone.top_price:
                    # Complete break
                    penetration_pct = 1.0
                    test_type = 'break'
                else:
                    # Partial penetration
                    penetration_pct = (candle['high'] - zone.bottom_price) / zone_height
                    test_type = 'penetration' if penetration_pct > self.test_penetration_threshold else 'touch'
                
                return test_type, test_price, penetration_pct
        
        elif zone.zone_type == 'demand':
            # Check downward interaction with demand zone
            if candle['low'] <= zone.top_price:
                test_price = candle['low']
                
                if candle['low'] <= zone.bottom_price:
                    # Complete break
                    penetration_pct = 1.0
                    test_type = 'break'
                else:
                    # Partial penetration
                    penetration_pct = (zone.top_price - candle['low']) / zone_height
                    test_type = 'penetration' if penetration_pct > self.test_penetration_threshold else 'touch'
                
                return test_type, test_price, penetration_pct
        
        return None
    
    def _calculate_reaction_strength(
        self,
        zone: SupplyDemandZone,
        test_candle: pd.Series,
        price_data: pd.DataFrame,
        test_type: str
    ) -> float:
        """
        Calculate reaction strength after zone test.
        
        Args:
            zone: Zone that was tested
            test_candle: Candle that tested the zone
            price_data: Full price data for context
            test_type: Type of test ('touch', 'penetration', 'break')
            
        Returns:
            Reaction strength (0.0 to 1.0)
        """
        try:
            # Find test candle index
            test_time = test_candle['time']
            test_index = None
            
            for i, (_, candle) in enumerate(price_data.iterrows()):
                if candle['time'] == test_time:
                    test_index = i
                    break
            
            if test_index is None or test_index >= len(price_data) - 2:
                return 0.5  # Default if can't find context
            
            # Analyze reaction in next 3 candles
            reaction_candles = price_data.iloc[test_index + 1:test_index + 4]
            
            if len(reaction_candles) == 0:
                return 0.5
            
            # Calculate reaction strength based on zone type
            if zone.zone_type == 'supply':
                # For supply zones, expect downward reaction
                test_price = test_candle['high']
                reaction_moves = []
                
                for _, candle in reaction_candles.iterrows():
                    move = (test_price - candle['close']) / zone.atr_at_creation
                    reaction_moves.append(max(0, move))  # Only positive reactions
                
            elif zone.zone_type == 'demand':
                # For demand zones, expect upward reaction
                test_price = test_candle['low']
                reaction_moves = []
                
                for _, candle in reaction_candles.iterrows():
                    move = (candle['close'] - test_price) / zone.atr_at_creation
                    reaction_moves.append(max(0, move))  # Only positive reactions
            
            else:
                return 0.5
            
            # Calculate average reaction strength
            if reaction_moves:
                avg_reaction = np.mean(reaction_moves)
                # Normalize to 0-1 scale (2 ATR = 1.0)
                normalized_reaction = min(1.0, avg_reaction / 2.0)
                return normalized_reaction
            
            return 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating reaction strength: {e}")
            return 0.5
    
    def _classify_zone_interaction(
        self,
        zone: SupplyDemandZone,
        penetration_pct: float,
        interaction_type: str
    ) -> str:
        """
        Classify zone interaction and determine new status.
        
        Args:
            zone: Zone being analyzed
            penetration_pct: Percentage of zone penetration
            interaction_type: Type of interaction
            
        Returns:
            New zone status
        """
        if interaction_type == 'break' or penetration_pct >= self.break_threshold:
            return 'broken'
        elif interaction_type in ['touch', 'penetration']:
            if zone.status == 'active':
                return 'tested'
            else:
                return zone.status  # Keep current status
        
        return zone.status
    
    def _get_trigger_reason(self, interaction_type: str, penetration_pct: float) -> str:
        """Get trigger reason based on interaction type"""
        if interaction_type == 'break' or penetration_pct >= self.break_threshold:
            return 'price_break'
        elif interaction_type in ['touch', 'penetration']:
            return 'zone_test'
        else:
            return 'price_interaction'
    
    def _is_test_successful(
        self,
        zone: SupplyDemandZone,
        interaction_type: str,
        penetration_pct: float
    ) -> bool:
        """
        Determine if zone test was successful.
        
        Args:
            zone: Zone being tested
            interaction_type: Type of interaction
            penetration_pct: Penetration percentage
            
        Returns:
            True if test was successful
        """
        # Break is never successful
        if interaction_type == 'break' or penetration_pct >= self.break_threshold:
            return False
        
        # Touch or light penetration can be successful
        # (Real success determined by reaction strength in full analysis)
        return penetration_pct < self.break_threshold
    
    def _detect_zone_flip(
        self,
        zone: SupplyDemandZone,
        price_data: pd.DataFrame,
        current_time: datetime
    ) -> Optional[ZoneStateUpdate]:
        """
        Detect if zone has flipped from supply to demand or vice versa.
        
        Args:
            zone: Zone to check for flip
            price_data: Recent price data
            current_time: Current timestamp
            
        Returns:
            Zone flip update or None
        """
        if len(price_data) < self.flip_confirmation_bars:
            return None
        
        try:
            # Get recent candles for flip confirmation
            recent_candles = price_data.tail(self.flip_confirmation_bars)
            
            # Analyze flip conditions based on zone type
            if zone.zone_type == 'supply':
                # Supply zone flips to demand if price consistently holds above zone
                flip_confirmed = self._check_supply_to_demand_flip(zone, recent_candles)
                new_type = 'demand' if flip_confirmed else None
                
            elif zone.zone_type == 'demand':
                # Demand zone flips to supply if price consistently holds below zone
                flip_confirmed = self._check_demand_to_supply_flip(zone, recent_candles)
                new_type = 'supply' if flip_confirmed else None
                
            else:
                return None
            
            if flip_confirmed and new_type:
                # Create flip update
                flip_update = ZoneStateUpdate(
                    zone_id=zone.id,
                    old_status=zone.status,
                    new_status='flipped',
                    update_time=current_time,
                    trigger_price=recent_candles['close'].iloc[-1],
                    trigger_reason='zone_flip',
                    test_success=False
                )
                
                logger.debug(f"Detected zone {zone.id} flip from {zone.zone_type} to {new_type}")
                return flip_update
            
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting zone {zone.id} flip: {e}")
            return None
    
    def _check_supply_to_demand_flip(
        self,
        zone: SupplyDemandZone,
        recent_candles: pd.DataFrame
    ) -> bool:
        """
        Check if supply zone flips to demand zone.
        
        Args:
            zone: Supply zone to check
            recent_candles: Recent candle data
            
        Returns:
            True if flip is confirmed
        """
        # Supply flips to demand if price consistently closes above zone top
        closes_above_zone = (recent_candles['close'] > zone.top_price).all()
        
        # Additional confirmation: recent lows should not break below zone top
        lows_respect_zone = (recent_candles['low'] >= zone.top_price * 0.995).all()  # 0.5% tolerance
        
        return closes_above_zone and lows_respect_zone
    
    def _check_demand_to_supply_flip(
        self,
        zone: SupplyDemandZone,
        recent_candles: pd.DataFrame
    ) -> bool:
        """
        Check if demand zone flips to supply zone.
        
        Args:
            zone: Demand zone to check
            recent_candles: Recent candle data
            
        Returns:
            True if flip is confirmed
        """
        # Demand flips to supply if price consistently closes below zone bottom
        closes_below_zone = (recent_candles['close'] < zone.bottom_price).all()
        
        # Additional confirmation: recent highs should not break above zone bottom
        highs_respect_zone = (recent_candles['high'] <= zone.bottom_price * 1.005).all()  # 0.5% tolerance
        
        return closes_below_zone and highs_respect_zone
    
    def _update_zone_statistics(
        self,
        zones: List[SupplyDemandZone],
        updates: List[ZoneStateUpdate]
    ) -> None:
        """
        Update zone statistics based on recent updates.
        
        Args:
            zones: List of zones to update statistics for
            updates: Recent zone state updates
        """
        for zone in zones:
            if zone.id is None:
                continue
            
            # Initialize statistics if not present
            if zone.id not in self._zone_statistics:
                self._zone_statistics[zone.id] = {
                    'test_count': zone.test_count,
                    'success_count': zone.success_count,
                    'success_rate': 0.0,
                    'average_reaction_strength': 0.0,
                    'last_test_time': None,
                    'total_penetrations': 0
                }
            
            stats = self._zone_statistics[zone.id]
            
            # Update statistics based on recent updates
            zone_updates = [update for update in updates if update.zone_id == zone.id]
            
            for update in zone_updates:
                if update.trigger_reason == 'zone_test':
                    stats['test_count'] += 1
                    stats['last_test_time'] = update.update_time
                    
                    if update.test_success:
                        stats['success_count'] += 1
            
            # Calculate success rate
            if stats['test_count'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['test_count']
            
            # Update average reaction strength from test events
            zone_test_events = [event for event in self._test_events if event.zone_id == zone.id]
            if zone_test_events:
                avg_reaction = np.mean([event.reaction_strength for event in zone_test_events])
                stats['average_reaction_strength'] = avg_reaction


def create_test_state_manager() -> ZoneStateManager:
    """Create state manager with test-friendly parameters"""
    return ZoneStateManager(
        test_penetration_threshold=0.1,
        break_threshold=0.3,
        flip_confirmation_bars=3,
        max_test_attempts=5,
        zone_expiry_hours=168,
        reaction_strength_threshold=0.6
    )