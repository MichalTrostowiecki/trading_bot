"""
SupplyDemandZoneDetector - Professional Zone Detection System

Main class for detecting supply and demand zones using eWavesHarmonics methodology.
Combines base candle detection, big move analysis, and zone classification
to identify institutional order flow areas.

Performance Target: <50ms per complete detection cycle
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from .base_candle_detector import BaseCandleDetector, BaseCandleRange
from .big_move_detector import BigMoveDetector, BigMove

logger = logging.getLogger(__name__)


@dataclass
class SupplyDemandZone:
    """
    Represents a supply or demand zone with complete metadata.
    
    Based on eWavesHarmonics zone identification methodology.
    """
    id: Optional[int]  # Database ID (None for new zones)
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
    base_range: BaseCandleRange
    big_move: BigMove
    atr_at_creation: float
    volume_at_creation: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def contains_price(self, price: float) -> bool:
        """Check if price is within zone boundaries"""
        return self.bottom_price <= price <= self.top_price
    
    def distance_from_price(self, price: float) -> float:
        """Calculate distance from price to nearest zone boundary"""
        if self.contains_price(price):
            return 0.0
        elif price < self.bottom_price:
            return self.bottom_price - price
        else:
            return price - self.top_price
    
    @property
    def height(self) -> float:
        """Zone height in price units"""
        return self.top_price - self.bottom_price
    
    @property
    def center(self) -> float:
        """Zone center price"""
        return (self.top_price + self.bottom_price) / 2.0
    
    @property
    def age_hours(self) -> float:
        """Zone age in hours"""
        return (datetime.now() - self.created_at).total_seconds() / 3600


class SupplyDemandZoneDetector:
    """
    Main class for detecting supply and demand zones using eWavesHarmonics methodology.
    
    Combines base candle detection, big move analysis, and zone classification
    to identify institutional order flow areas.
    
    Performance Target: <50ms per complete detection cycle
    """
    
    def __init__(
        self,
        base_detector: BaseCandleDetector,
        move_detector: BigMoveDetector,
        max_zones_per_timeframe: int = 100,
        zone_expiry_hours: int = 168,  # 1 week
        overlap_tolerance: float = 0.1  # 10% overlap allowed
    ):
        """
        Initialize supply/demand zone detector.
        
        Args:
            base_detector: Configured BaseCandleDetector instance
            move_detector: Configured BigMoveDetector instance
            max_zones_per_timeframe: Maximum zones to maintain
            zone_expiry_hours: Hours before zone expires
            overlap_tolerance: Allowed zone overlap percentage
            
        Raises:
            ValueError: If parameters are invalid
            TypeError: If detectors are None
        """
        self._validate_parameters(
            base_detector, move_detector, max_zones_per_timeframe, 
            zone_expiry_hours, overlap_tolerance
        )
        
        self.base_detector = base_detector
        self.move_detector = move_detector
        self.max_zones_per_timeframe = max_zones_per_timeframe
        self.zone_expiry_hours = zone_expiry_hours
        self.overlap_tolerance = overlap_tolerance
        self._zone_cache: List[SupplyDemandZone] = []
        
        logger.debug(f"SupplyDemandZoneDetector initialized with max_zones={max_zones_per_timeframe}")
    
    def _validate_parameters(
        self,
        base_detector: BaseCandleDetector,
        move_detector: BigMoveDetector,
        max_zones_per_timeframe: int,
        zone_expiry_hours: int,
        overlap_tolerance: float
    ) -> None:
        """Validate initialization parameters"""
        if base_detector is None:
            raise TypeError("base_detector cannot be None")
        
        if move_detector is None:
            raise TypeError("move_detector cannot be None")
        
        if max_zones_per_timeframe <= 0:
            raise ValueError(f"max_zones_per_timeframe must be > 0, got {max_zones_per_timeframe}")
        
        if zone_expiry_hours <= 0:
            raise ValueError(f"zone_expiry_hours must be > 0, got {zone_expiry_hours}")
        
        if not 0.0 <= overlap_tolerance <= 1.0:
            raise ValueError(f"overlap_tolerance must be 0.0-1.0, got {overlap_tolerance}")
    
    def detect_zones(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        fractal_levels: Optional[List[float]] = None,
        existing_zones: Optional[List[SupplyDemandZone]] = None
    ) -> List[SupplyDemandZone]:
        """
        Detect all supply and demand zones in price data.
        
        Args:
            df: OHLC DataFrame with required columns
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'M1', 'H1')
            fractal_levels: Optional fractal levels for context
            existing_zones: Optional existing zones to update
            
        Returns:
            List of detected SupplyDemandZone objects
            
        Raises:
            ValueError: If data is insufficient or invalid
            
        Performance: <50ms for 1000 bars
        """
        if df is None or len(df) == 0:
            logger.warning("Empty or None DataFrame provided for zone detection")
            return []
        
        self._validate_input_data(df)
        
        try:
            # Step 1: Detect base candle ranges
            logger.debug("Detecting base candle ranges...")
            base_ranges = self.base_detector.detect_base_candles(df)
            
            if not base_ranges:
                logger.debug("No base candle ranges detected")
                return []
            
            logger.debug(f"Detected {len(base_ranges)} base candle ranges")
            
            # Step 2: Detect big moves following base ranges
            logger.debug("Detecting big moves...")
            big_moves = self.move_detector.detect_big_moves(df, base_ranges, fractal_levels)
            
            if not big_moves:
                logger.debug("No big moves detected")
                return []
            
            logger.debug(f"Detected {len(big_moves)} big moves")
            
            # Step 3: Create zones from base ranges and big moves
            logger.debug("Creating supply/demand zones...")
            zones = self._create_zones_from_moves(df, base_ranges, big_moves, symbol, timeframe)
            
            # Step 4: Resolve overlapping zones
            logger.debug("Resolving overlapping zones...")
            resolved_zones = self._resolve_overlapping_zones(zones)
            
            # Step 5: Limit zone count
            final_zones = self._limit_zone_count(resolved_zones)
            
            logger.info(f"Successfully detected {len(final_zones)} supply/demand zones")
            return final_zones
            
        except Exception as e:
            logger.error(f"Error in zone detection: {e}")
            raise ValueError(f"Zone detection failed: {e}")
    
    def _validate_input_data(self, df: pd.DataFrame) -> None:
        """Validate input OHLC data"""
        required_columns = ['open', 'high', 'low', 'close', 'time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def _create_zones_from_moves(
        self,
        df: pd.DataFrame,
        base_ranges: List[BaseCandleRange],
        big_moves: List[BigMove],
        symbol: str,
        timeframe: str
    ) -> List[SupplyDemandZone]:
        """
        Create supply/demand zones from detected base ranges and big moves.
        
        Args:
            df: OHLC DataFrame
            base_ranges: List of base candle ranges
            big_moves: List of big moves
            symbol: Trading symbol
            timeframe: Chart timeframe
            
        Returns:
            List of created zones
        """
        zones = []
        
        # Match big moves with their corresponding base ranges
        for big_move in big_moves:
            # Find the base range that precedes this big move
            corresponding_base = None
            
            for base_range in base_ranges:
                # Big move should start after base range ends
                if base_range.end_index < big_move.start_index:
                    # Check if this is the closest preceding base range
                    if (corresponding_base is None or 
                        base_range.end_index > corresponding_base.end_index):
                        corresponding_base = base_range
            
            if corresponding_base is not None:
                try:
                    zone = self._create_zone_from_base_and_move(
                        df, corresponding_base, big_move, symbol, timeframe
                    )
                    zones.append(zone)
                    logger.debug(f"Created {zone.zone_type} zone at {zone.center:.5f}")
                    
                except Exception as e:
                    logger.warning(f"Failed to create zone from base {corresponding_base.start_index}: {e}")
                    continue
        
        return zones
    
    def _create_zone_from_base_and_move(
        self,
        df: pd.DataFrame,
        base_range: BaseCandleRange,
        big_move: BigMove,
        symbol: str,
        timeframe: str
    ) -> SupplyDemandZone:
        """
        Create a single zone from base range and big move.
        
        Args:
            df: OHLC DataFrame
            base_range: Base candle range
            big_move: Following big move
            symbol: Trading symbol
            timeframe: Chart timeframe
            
        Returns:
            SupplyDemandZone object
        """
        # Classify zone type based on move direction
        zone_type = self._classify_zone_type(base_range, big_move)
        
        # Calculate zone boundaries using eWavesHarmonics rules
        top_price, bottom_price = self._calculate_zone_boundaries(df, base_range, zone_type)
        
        # Calculate zone strength
        zone_strength = self._calculate_zone_strength_from_context(
            df, base_range, big_move, top_price, bottom_price
        )
        
        # Calculate volume at creation
        volume_at_creation = self._calculate_creation_volume(df, base_range, big_move)
        
        # Create zone object
        current_time = datetime.now()
        
        zone = SupplyDemandZone(
            id=None,  # Will be assigned by database
            symbol=symbol,
            timeframe=timeframe,
            zone_type=zone_type,
            top_price=top_price,
            bottom_price=bottom_price,
            left_time=base_range.start_time,
            right_time=base_range.end_time,
            strength_score=zone_strength,
            test_count=0,
            success_count=0,
            status='active',
            base_range=base_range,
            big_move=big_move,
            atr_at_creation=base_range.atr_at_creation,
            volume_at_creation=volume_at_creation,
            created_at=current_time,
            updated_at=current_time
        )
        
        return zone
    
    def _classify_zone_type(
        self, 
        base_range: BaseCandleRange, 
        big_move: BigMove
    ) -> str:
        """
        Classify zone as supply, demand, or continuation.
        
        Args:
            base_range: Base candle consolidation range
            big_move: Following big move data
            
        Returns:
            Zone type: 'supply', 'demand', or 'continuation'
        """
        # Simple classification based on move direction
        # Bullish moves create demand zones (where buyers were)
        # Bearish moves create supply zones (where sellers were)
        
        if big_move.direction == "bullish":
            return "demand"
        elif big_move.direction == "bearish":
            return "supply"
        else:
            # Fallback to continuation zone
            return "continuation"
    
    def _calculate_zone_boundaries(
        self, 
        df: pd.DataFrame,
        base_range: BaseCandleRange, 
        zone_type: str
    ) -> Tuple[float, float]:
        """
        Calculate precise zone boundaries using eWavesHarmonics rules.
        
        For demand zones: 
        - Top: Highest high of base candles
        - Bottom: Lowest open of red candles in base range
        
        For supply zones:
        - Top: Highest open of green candles in base range  
        - Bottom: Lowest low of base candles
        
        Args:
            df: OHLC DataFrame
            base_range: Base candle range data
            zone_type: 'supply' or 'demand'
            
        Returns:
            Tuple of (top_price, bottom_price)
        """
        # Extract base candle data
        base_data = df.iloc[base_range.start_index:base_range.end_index + 1]
        
        if zone_type == "demand":
            # Demand zone boundaries (eWavesHarmonics rules)
            top_price = base_data['high'].max()
            
            # Find red candles (bearish: close < open) and get lowest open
            red_candles = base_data[base_data['close'] < base_data['open']]
            if len(red_candles) > 0:
                bottom_price = red_candles['open'].min()
            else:
                # Fallback if no red candles: use lowest low
                bottom_price = base_data['low'].min()
                
        elif zone_type == "supply":
            # Supply zone boundaries (eWavesHarmonics rules)
            bottom_price = base_data['low'].min()
            
            # Find green candles (bullish: close >= open) and get highest open
            green_candles = base_data[base_data['close'] >= base_data['open']]
            if len(green_candles) > 0:
                top_price = green_candles['open'].max()
            else:
                # Fallback if no green candles: use highest high
                top_price = base_data['high'].max()
                
        else:
            # Continuation zone: simple high/low boundaries
            top_price = base_data['high'].max()
            bottom_price = base_data['low'].min()
        
        # Ensure valid boundaries
        if top_price <= bottom_price:
            # Fallback to simple boundaries if calculation fails
            top_price = base_data['high'].max()
            bottom_price = base_data['low'].min()
            
            # Add small buffer if still equal
            if top_price == bottom_price:
                buffer = top_price * 0.0001  # 0.01% buffer
                top_price += buffer
                bottom_price -= buffer
        
        return top_price, bottom_price
    
    def _calculate_zone_strength_from_context(
        self,
        df: pd.DataFrame,
        base_range: BaseCandleRange,
        big_move: BigMove,
        top_price: float,
        bottom_price: float
    ) -> float:
        """
        Calculate zone strength score from creation context.
        
        Factors:
        - Volume at creation (40%)
        - Move magnitude (30%)
        - Base candle quality (20%)
        - Breakout confirmation (10%)
        
        Args:
            df: OHLC DataFrame
            base_range: Base candle range
            big_move: Big move data
            top_price: Zone top boundary
            bottom_price: Zone bottom boundary
            
        Returns:
            Strength score (0.0 to 1.0)
        """
        # Volume component (40% weight)
        volume_score = 0.5  # Default if no volume data
        if 'volume' in df.columns:
            try:
                # Calculate volume ratio during move vs baseline
                baseline_volume = df.iloc[max(0, base_range.start_index - 20):base_range.start_index]['volume'].mean()
                move_volume = df.iloc[big_move.start_index:big_move.end_index + 1]['volume'].mean()
                
                if baseline_volume > 0:
                    volume_ratio = move_volume / baseline_volume
                    volume_score = min(1.0, volume_ratio / 2.0)  # Normalize to 2x volume = 1.0
                    
            except Exception:
                volume_score = 0.5  # Fallback
        
        # Move magnitude component (30% weight)
        magnitude_score = min(1.0, big_move.magnitude / 5.0)  # Normalize to 5x ATR = 1.0
        
        # Base candle quality component (20% weight)
        base_quality_score = base_range.consolidation_score
        
        # Momentum component (10% weight)
        momentum_score = big_move.momentum_score
        
        # Combined strength score
        strength_score = (
            volume_score * 0.4 +
            magnitude_score * 0.3 +
            base_quality_score * 0.2 +
            momentum_score * 0.1
        )
        
        return max(0.0, min(1.0, strength_score))
    
    def _calculate_creation_volume(
        self,
        df: pd.DataFrame,
        base_range: BaseCandleRange,
        big_move: BigMove
    ) -> float:
        """Calculate average volume during zone creation"""
        if 'volume' not in df.columns:
            return 0.0
        
        try:
            # Volume during the big move (breakout)
            move_volume = df.iloc[big_move.start_index:big_move.end_index + 1]['volume'].mean()
            return move_volume
            
        except Exception:
            return 0.0
    
    def _resolve_overlapping_zones(
        self, 
        zones: List[SupplyDemandZone]
    ) -> List[SupplyDemandZone]:
        """
        Resolve overlapping zones by merging or prioritizing.
        
        Args:
            zones: List of potentially overlapping zones
            
        Returns:
            List of resolved zones without conflicts
        """
        if len(zones) <= 1:
            return zones
        
        resolved_zones = []
        
        for zone in zones:
            # Check for overlaps with already resolved zones
            overlapping_zones = []
            
            for resolved_zone in resolved_zones:
                overlap = self._calculate_zone_overlap(zone, resolved_zone)
                if overlap > self.overlap_tolerance:
                    overlapping_zones.append(resolved_zone)
            
            if overlapping_zones:
                # Remove overlapping zones and create merged zone
                for overlapping_zone in overlapping_zones:
                    resolved_zones.remove(overlapping_zone)
                
                # Merge zones (keep strongest)
                strongest_zone = zone
                for overlapping_zone in overlapping_zones:
                    if overlapping_zone.strength_score > strongest_zone.strength_score:
                        strongest_zone = overlapping_zone
                
                resolved_zones.append(strongest_zone)
            else:
                # No overlap, add zone
                resolved_zones.append(zone)
        
        return resolved_zones
    
    def _calculate_zone_overlap(
        self, 
        zone1: SupplyDemandZone, 
        zone2: SupplyDemandZone
    ) -> float:
        """
        Calculate overlap percentage between two zones.
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            Overlap percentage (0.0 to 1.0)
        """
        # Calculate price overlap
        overlap_top = min(zone1.top_price, zone2.top_price)
        overlap_bottom = max(zone1.bottom_price, zone2.bottom_price)
        
        if overlap_top <= overlap_bottom:
            return 0.0  # No overlap
        
        overlap_height = overlap_top - overlap_bottom
        
        # Calculate as percentage of smaller zone
        zone1_height = zone1.height
        zone2_height = zone2.height
        
        if zone1_height <= 0 or zone2_height <= 0:
            return 0.0
        
        min_height = min(zone1_height, zone2_height)
        overlap_percentage = overlap_height / min_height
        
        return min(1.0, overlap_percentage)
    
    def _limit_zone_count(
        self, 
        zones: List[SupplyDemandZone]
    ) -> List[SupplyDemandZone]:
        """
        Limit zone count to maximum per timeframe.
        
        Args:
            zones: List of zones to limit
            
        Returns:
            Limited list of best zones
        """
        if len(zones) <= self.max_zones_per_timeframe:
            return zones
        
        # Sort by strength score (descending) and keep best zones
        sorted_zones = sorted(zones, key=lambda z: z.strength_score, reverse=True)
        limited_zones = sorted_zones[:self.max_zones_per_timeframe]
        
        logger.debug(f"Limited zones from {len(zones)} to {len(limited_zones)}")
        return limited_zones
    
    def _calculate_zone_strength(
        self, 
        zone: SupplyDemandZone,
        df: pd.DataFrame
    ) -> float:
        """
        Calculate zone strength score (0.0 to 1.0).
        
        This method is for compatibility and calls the context-based method.
        
        Args:
            zone: SupplyDemandZone object
            df: OHLC DataFrame with volume
            
        Returns:
            Strength score (0.0 to 1.0)
        """
        return zone.strength_score  # Already calculated during creation


def create_test_detector() -> SupplyDemandZoneDetector:
    """Create detector with test-friendly parameters"""
    from .base_candle_detector import create_test_detector as create_base_detector
    from .big_move_detector import create_test_detector as create_move_detector
    
    base_detector = create_base_detector()
    move_detector = create_move_detector()
    
    return SupplyDemandZoneDetector(
        base_detector=base_detector,
        move_detector=move_detector,
        max_zones_per_timeframe=100,
        zone_expiry_hours=168,
        overlap_tolerance=0.1
    )