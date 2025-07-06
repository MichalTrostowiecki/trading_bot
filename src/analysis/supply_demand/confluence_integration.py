"""
SupplyDemandConfluence - Professional Confluence Integration

Integrates supply/demand zones with existing confluence system for enhanced
trading signal generation using institutional order flow analysis.

Performance Target: <100ms for 100 zones, <200ms for multi-timeframe analysis
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from .zone_detector import SupplyDemandZone
from .zone_state_manager import ZoneStateManager
from .repository import SupplyDemandRepository, ZoneQueryFilter

logger = logging.getLogger(__name__)


@dataclass
class SDZoneConfluenceScore:
    """
    Comprehensive confluence score for a supply/demand zone.
    
    Combines multiple factors to assess zone trading significance.
    """
    zone_id: int
    zone_type: str  # 'supply', 'demand'
    proximity_score: float  # 0.0 to 1.0 (1.0 = at zone center)
    strength_score: float   # 0.0 to 1.0 (zone creation strength)
    freshness_score: float  # 0.0 to 1.0 (age-based scoring)
    test_history_score: float  # 0.0 to 1.0 (success rate based)
    total_confluence_score: float  # 0.0 to 1.0 (weighted combination)
    distance_pips: float    # Distance from price in pips
    zone_center: float      # Zone center price
    zone_boundaries: Tuple[float, float]  # (top, bottom) prices
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'zone_id': self.zone_id,
            'zone_type': self.zone_type,
            'proximity_score': self.proximity_score,
            'strength_score': self.strength_score,
            'freshness_score': self.freshness_score,
            'test_history_score': self.test_history_score,
            'total_confluence_score': self.total_confluence_score,
            'distance_pips': self.distance_pips,
            'zone_center': self.zone_center,
            'zone_boundaries': self.zone_boundaries
        }


@dataclass
class SDZoneProximity:
    """
    Detailed proximity analysis for a zone relative to current price.
    
    Provides precise distance and penetration metrics.
    """
    zone_id: int
    distance_pips: float    # Distance in pips (0.0 if inside zone)
    proximity_score: float  # 1.0 at center, decreases with distance
    is_inside_zone: bool    # True if price is within zone boundaries
    penetration_percentage: float  # 0.0 to 1.0 if inside zone
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'zone_id': self.zone_id,
            'distance_pips': self.distance_pips,
            'proximity_score': self.proximity_score,
            'is_inside_zone': self.is_inside_zone,
            'penetration_percentage': self.penetration_percentage
        }


class SupplyDemandConfluence:
    """
    Professional confluence integration for supply/demand zones.
    
    Combines S&D zone analysis with existing confluence factors to generate
    enhanced trading signals using institutional order flow principles.
    
    Performance Target: <100ms for 100 zones, <200ms for multi-timeframe analysis
    """
    
    def __init__(
        self,
        proximity_threshold_pips: float = 50.0,     # Max distance for confluence
        min_zone_strength: float = 0.5,             # Minimum zone strength
        freshness_weight: float = 0.3,              # Weight for zone age
        strength_weight: float = 0.4,               # Weight for zone strength
        test_history_weight: float = 0.3,           # Weight for test success
        multi_timeframe_enabled: bool = True,       # Enable MTF analysis
        max_zone_age_hours: int = 168,              # 1 week maximum age
        pip_value_4_digit: float = 0.0001,          # 4-digit pip value
        pip_value_5_digit: float = 0.00001          # 5-digit pip value
    ):
        """
        Initialize supply/demand confluence system.
        
        Args:
            proximity_threshold_pips: Maximum distance for zone confluence
            min_zone_strength: Minimum zone strength to consider
            freshness_weight: Weight for zone freshness in scoring
            strength_weight: Weight for zone strength in scoring
            test_history_weight: Weight for zone test history in scoring
            multi_timeframe_enabled: Enable multi-timeframe analysis
            max_zone_age_hours: Maximum zone age before exclusion
            pip_value_4_digit: Pip value for 4-digit pairs (EURUSD, etc.)
            pip_value_5_digit: Pip value for 5-digit pairs (USDJPY, etc.)
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_parameters(
            proximity_threshold_pips, min_zone_strength, freshness_weight,
            strength_weight, test_history_weight, max_zone_age_hours
        )
        
        self.proximity_threshold_pips = proximity_threshold_pips
        self.min_zone_strength = min_zone_strength
        self.freshness_weight = freshness_weight
        self.strength_weight = strength_weight
        self.test_history_weight = test_history_weight
        self.multi_timeframe_enabled = multi_timeframe_enabled
        self.max_zone_age_hours = max_zone_age_hours
        self.pip_value_4_digit = pip_value_4_digit
        self.pip_value_5_digit = pip_value_5_digit
        
        # Internal zone cache for performance
        self._zone_cache: Dict[str, List[SupplyDemandZone]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_timeout_minutes = 5  # Cache zones for 5 minutes
        
        # Timeframe weights for multi-timeframe analysis
        self._timeframe_weights = {
            'M1': 0.1,   # Lower weight for M1
            'M5': 0.2,   # Medium weight for M5
            'M15': 0.3,  # Higher weight for M15
            'H1': 0.4,   # High weight for H1
            'H4': 0.5,   # Higher weight for H4
            'D1': 0.6    # Highest weight for daily
        }
        
        logger.debug(f"SupplyDemandConfluence initialized with proximity_threshold={proximity_threshold_pips}")
    
    def _validate_parameters(
        self,
        proximity_threshold_pips: float,
        min_zone_strength: float,
        freshness_weight: float,
        strength_weight: float,
        test_history_weight: float,
        max_zone_age_hours: int
    ) -> None:
        """Validate initialization parameters"""
        if proximity_threshold_pips <= 0:
            raise ValueError(f"proximity_threshold_pips must be > 0, got {proximity_threshold_pips}")
        
        if not 0.0 <= min_zone_strength <= 1.0:
            raise ValueError(f"min_zone_strength must be 0.0-1.0, got {min_zone_strength}")
        
        if not 0.0 <= freshness_weight <= 1.0:
            raise ValueError(f"freshness_weight must be 0.0-1.0, got {freshness_weight}")
        
        if not 0.0 <= strength_weight <= 1.0:
            raise ValueError(f"strength_weight must be 0.0-1.0, got {strength_weight}")
        
        if not 0.0 <= test_history_weight <= 1.0:
            raise ValueError(f"test_history_weight must be 0.0-1.0, got {test_history_weight}")
        
        # Validate weight sum
        weight_sum = freshness_weight + strength_weight + test_history_weight
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum:.3f}")
        
        if max_zone_age_hours <= 0:
            raise ValueError(f"max_zone_age_hours must be > 0, got {max_zone_age_hours}")
    
    def calculate_confluence_score(
        self,
        price: float,
        symbol: str,
        timeframes: Optional[List[str]] = None
    ) -> Optional[SDZoneConfluenceScore]:
        """
        Calculate confluence score for the strongest nearby zone.
        
        Args:
            price: Current price to analyze
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframes: List of timeframes to analyze (None = all cached)
            
        Returns:
            SDZoneConfluenceScore for strongest nearby zone or None
            
        Performance: <100ms for 100 zones
        """
        if timeframes is None:
            timeframes = list(self._zone_cache.keys())
        
        try:
            # Get nearby zones
            nearby_zones = self.get_nearby_zones(
                price, symbol, timeframes, self.proximity_threshold_pips
            )
            
            if not nearby_zones:
                return None
            
            # Find the zone with highest total confluence
            best_zone = None
            best_score = 0.0
            
            for zone_proximity in nearby_zones:
                zone = self._find_zone_by_id(zone_proximity.zone_id)
                if not zone:
                    continue
                
                # Calculate comprehensive confluence score
                confluence_score = self._calculate_comprehensive_score(
                    zone, zone_proximity, price
                )
                
                if confluence_score.total_confluence_score > best_score:
                    best_score = confluence_score.total_confluence_score
                    best_zone = confluence_score
            
            return best_zone
            
        except Exception as e:
            logger.error(f"Error calculating confluence score: {e}")
            return None
    
    def get_nearby_zones(
        self,
        price: float,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        max_distance_pips: Optional[float] = None
    ) -> List[SDZoneProximity]:
        """
        Get zones near the specified price.
        
        Args:
            price: Price to find zones near
            symbol: Trading symbol
            timeframes: Timeframes to search (None = all cached)
            max_distance_pips: Maximum distance in pips (None = use default)
            
        Returns:
            List of SDZoneProximity objects sorted by proximity
        """
        if max_distance_pips is None:
            max_distance_pips = self.proximity_threshold_pips
        
        if timeframes is None:
            timeframes = list(self._zone_cache.keys())
        
        nearby_zones = []
        
        try:
            for timeframe in timeframes:
                zones = self._get_zones_for_timeframe(symbol, timeframe)
                
                for zone in zones:
                    # Calculate proximity
                    proximity = self.calculate_zone_proximity(zone, price)
                    
                    # Check if within distance threshold
                    if (proximity.is_inside_zone or 
                        proximity.distance_pips <= max_distance_pips):
                        nearby_zones.append(proximity)
            
            # Sort by proximity score (highest first)
            nearby_zones.sort(key=lambda x: x.proximity_score, reverse=True)
            
            return nearby_zones
            
        except Exception as e:
            logger.error(f"Error getting nearby zones: {e}")
            return []
    
    def calculate_zone_proximity(
        self,
        zone: SupplyDemandZone,
        price: float
    ) -> SDZoneProximity:
        """
        Calculate detailed proximity analysis for a zone.
        
        Args:
            zone: SupplyDemandZone to analyze
            price: Current price
            
        Returns:
            SDZoneProximity with detailed proximity metrics
        """
        # Check if price is inside zone
        is_inside = zone.contains_price(price)
        
        if is_inside:
            # Calculate penetration percentage (0.0 = at bottom, 1.0 = at top)
            zone_height = zone.height
            if zone_height > 0:
                penetration_pct = (price - zone.bottom_price) / zone_height
            else:
                penetration_pct = 0.5  # Default to center if no height
            
            # Proximity score based on distance from center
            center_distance = abs(price - zone.center)
            max_distance_from_center = zone_height / 2
            
            if max_distance_from_center > 0:
                proximity_score = 1.0 - (center_distance / max_distance_from_center)
            else:
                proximity_score = 1.0  # Perfect score if no height
            
            return SDZoneProximity(
                zone_id=zone.id,
                distance_pips=0.0,
                proximity_score=max(0.0, min(1.0, proximity_score)),
                is_inside_zone=True,
                penetration_percentage=max(0.0, min(1.0, penetration_pct))
            )
        
        else:
            # Calculate distance in pips
            distance_price = zone.distance_from_price(price)
            distance_pips = self._price_to_pips(distance_price, zone.symbol)
            
            # Proximity score decreases with distance
            proximity_score = max(0.0, 1.0 - (distance_pips / self.proximity_threshold_pips))
            
            return SDZoneProximity(
                zone_id=zone.id,
                distance_pips=distance_pips,
                proximity_score=proximity_score,
                is_inside_zone=False,
                penetration_percentage=0.0
            )
    
    def get_confluence_factors(
        self,
        price: float,
        symbol: str,
        timeframes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive confluence factors for trading decisions.
        
        Args:
            price: Current price to analyze
            symbol: Trading symbol
            timeframes: Timeframes to analyze
            
        Returns:
            Dictionary with complete confluence analysis
        """
        try:
            # Get nearby zones
            nearby_zones = self.get_nearby_zones(price, symbol, timeframes)
            
            # Separate by zone type
            supply_zones = []
            demand_zones = []
            
            for zone_proximity in nearby_zones:
                zone = self._find_zone_by_id(zone_proximity.zone_id)
                if not zone:
                    continue
                
                confluence_score = self._calculate_comprehensive_score(
                    zone, zone_proximity, price
                )
                
                if zone.zone_type == 'supply':
                    supply_zones.append(confluence_score)
                elif zone.zone_type == 'demand':
                    demand_zones.append(confluence_score)
            
            # Calculate total confluence and determine dominance
            supply_total = sum(z.total_confluence_score for z in supply_zones)
            demand_total = sum(z.total_confluence_score for z in demand_zones)
            total_confluence = max(supply_total, demand_total)
            
            # Determine dominant zone type
            if supply_total > demand_total * 1.2:  # 20% threshold for dominance
                dominant_type = 'supply'
            elif demand_total > supply_total * 1.2:
                dominant_type = 'demand'
            else:
                dominant_type = 'neutral'
            
            return {
                'supply_zones': [z.to_dict() for z in supply_zones],
                'demand_zones': [z.to_dict() for z in demand_zones],
                'total_confluence_score': min(1.0, total_confluence),
                'dominant_zone_type': dominant_type,
                'supply_confluence': min(1.0, supply_total),
                'demand_confluence': min(1.0, demand_total),
                'zone_count': len(nearby_zones),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting confluence factors: {e}")
            return {
                'supply_zones': [],
                'demand_zones': [],
                'total_confluence_score': 0.0,
                'dominant_zone_type': None,
                'supply_confluence': 0.0,
                'demand_confluence': 0.0,
                'zone_count': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def get_multi_timeframe_confluence(
        self,
        price: float,
        symbol: str,
        timeframes: List[str]
    ) -> Dict[str, float]:
        """
        Calculate confluence scores across multiple timeframes.
        
        Args:
            price: Current price to analyze
            symbol: Trading symbol
            timeframes: List of timeframes to analyze
            
        Returns:
            Dictionary mapping timeframes to confluence scores
        """
        mtf_confluence = {}
        
        try:
            for timeframe in timeframes:
                # Get confluence for this timeframe
                tf_confluence = self.calculate_confluence_score(price, symbol, [timeframe])
                
                if tf_confluence:
                    # Apply timeframe weight
                    tf_weight = self._timeframe_weights.get(timeframe, 0.3)
                    weighted_score = tf_confluence.total_confluence_score * tf_weight
                    mtf_confluence[timeframe] = min(1.0, weighted_score)
                else:
                    mtf_confluence[timeframe] = 0.0
            
            return mtf_confluence
            
        except Exception as e:
            logger.error(f"Error calculating multi-timeframe confluence: {e}")
            return {tf: 0.0 for tf in timeframes}
    
    def update_zone_cache(self, zones: List[SupplyDemandZone]) -> None:
        """
        Update internal zone cache for performance.
        
        Args:
            zones: List of zones to cache
        """
        try:
            # Clear existing cache
            self._zone_cache.clear()
            
            # Group zones by timeframe
            for zone in zones:
                if zone.timeframe not in self._zone_cache:
                    self._zone_cache[zone.timeframe] = []
                
                # Only cache zones that meet minimum criteria
                if self._should_cache_zone(zone):
                    self._zone_cache[zone.timeframe].append(zone)
            
            # Update cache timestamp
            self._cache_timestamp = datetime.now()
            
            total_zones = sum(len(zones) for zones in self._zone_cache.values())
            logger.debug(f"Updated zone cache with {total_zones} zones across {len(self._zone_cache)} timeframes")
            
        except Exception as e:
            logger.error(f"Error updating zone cache: {e}")
    
    def _calculate_comprehensive_score(
        self,
        zone: SupplyDemandZone,
        proximity: SDZoneProximity,
        current_price: float
    ) -> SDZoneConfluenceScore:
        """
        Calculate comprehensive confluence score for a zone.
        
        Args:
            zone: SupplyDemandZone to score
            proximity: SDZoneProximity data
            current_price: Current price for context
            
        Returns:
            Complete SDZoneConfluenceScore
        """
        # Component scores
        proximity_score = proximity.proximity_score
        strength_score = zone.strength_score
        freshness_score = self._calculate_freshness_score(zone)
        test_history_score = self._calculate_test_history_score(zone)
        
        # Weighted total score
        total_score = (
            proximity_score * 0.0 +  # Proximity handled separately
            strength_score * self.strength_weight +
            freshness_score * self.freshness_weight +
            test_history_score * self.test_history_weight
        )
        
        # Apply proximity multiplier
        total_score *= proximity_score
        
        return SDZoneConfluenceScore(
            zone_id=zone.id,
            zone_type=zone.zone_type,
            proximity_score=proximity_score,
            strength_score=strength_score,
            freshness_score=freshness_score,
            test_history_score=test_history_score,
            total_confluence_score=max(0.0, min(1.0, total_score)),
            distance_pips=proximity.distance_pips,
            zone_center=zone.center,
            zone_boundaries=(zone.top_price, zone.bottom_price)
        )
    
    def _calculate_freshness_score(self, zone: SupplyDemandZone) -> float:
        """Calculate freshness score based on zone age"""
        try:
            age_hours = zone.age_hours
            max_age = self.max_zone_age_hours
            
            # Linear decay from 1.0 to 0.0 over max age
            freshness = max(0.0, 1.0 - (age_hours / max_age))
            
            return freshness
            
        except Exception:
            return 0.5  # Default freshness
    
    def _calculate_test_history_score(self, zone: SupplyDemandZone) -> float:
        """Calculate test history score based on success rate"""
        try:
            if zone.test_count == 0:
                return 0.8  # Untested zones get good score
            
            success_rate = zone.success_count / zone.test_count
            
            # Bonus for zones with multiple successful tests
            if zone.test_count >= 3 and success_rate >= 0.8:
                return min(1.0, success_rate + 0.1)  # 10% bonus
            
            return success_rate
            
        except Exception:
            return 0.5  # Default score
    
    def _should_cache_zone(self, zone: SupplyDemandZone) -> bool:
        """Determine if zone should be cached"""
        # Filter by strength
        if zone.strength_score < self.min_zone_strength:
            return False
        
        # Filter by status
        if zone.status in ['broken', 'expired']:
            return False
        
        # Filter by age
        if zone.age_hours > self.max_zone_age_hours:
            return False
        
        return True
    
    def _get_zones_for_timeframe(self, symbol: str, timeframe: str) -> List[SupplyDemandZone]:
        """Get cached zones for specific symbol and timeframe"""
        if timeframe not in self._zone_cache:
            return []
        
        # Filter by symbol
        symbol_zones = [
            zone for zone in self._zone_cache[timeframe]
            if zone.symbol == symbol
        ]
        
        return symbol_zones
    
    def _find_zone_by_id(self, zone_id: int) -> Optional[SupplyDemandZone]:
        """Find zone by ID in cache"""
        for timeframe_zones in self._zone_cache.values():
            for zone in timeframe_zones:
                if zone.id == zone_id:
                    return zone
        return None
    
    def _price_to_pips(self, price_diff: float, symbol: str) -> float:
        """Convert price difference to pips"""
        # Determine pip value based on symbol
        if 'JPY' in symbol:
            pip_value = self.pip_value_5_digit  # 5-digit for JPY pairs
        else:
            pip_value = self.pip_value_4_digit  # 4-digit for major pairs
        
        return abs(price_diff) / pip_value
    
    def _is_cache_valid(self) -> bool:
        """Check if zone cache is still valid"""
        if self._cache_timestamp is None:
            return False
        
        age_minutes = (datetime.now() - self._cache_timestamp).total_seconds() / 60
        return age_minutes < self._cache_timeout_minutes


def create_test_confluence_system() -> SupplyDemandConfluence:
    """Create confluence system with test-friendly parameters"""
    return SupplyDemandConfluence(
        proximity_threshold_pips=50.0,
        min_zone_strength=0.5,
        freshness_weight=0.3,
        strength_weight=0.4,
        test_history_weight=0.3,
        multi_timeframe_enabled=True,
        max_zone_age_hours=168
    )