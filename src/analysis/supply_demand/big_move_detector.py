"""
BigMoveDetector - Professional Impulse Move Identification

Detects significant price movements that follow base candle consolidation
using institutional order execution analysis through momentum and volume.

Performance Target: <30ms per detection cycle
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .base_candle_detector import BaseCandleRange

logger = logging.getLogger(__name__)


@dataclass
class BigMove:
    """
    Represents a significant price movement after base candles.
    
    Identifies institutional order execution through momentum and volume analysis.
    """
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    direction: str  # 'bullish' or 'bearish'
    magnitude: float  # ATR multiples
    momentum_score: float  # 0.0 to 1.0
    breakout_level: float
    volume_confirmation: bool


class BigMoveDetector:
    """
    Detects significant price movements that follow base candle consolidation.
    
    Identifies institutional order execution through momentum and volume analysis.
    Performance Target: <30ms per detection cycle
    """
    
    def __init__(
        self,
        move_threshold: float = 2.0,           # ATR multiple
        min_move_candles: int = 3,             # Minimum move duration
        momentum_threshold: float = 0.6,       # Momentum quality
        volume_multiplier: float = 1.5,        # Volume spike threshold
        breakout_confirmation: bool = True      # Require level break
    ):
        """
        Initialize big move detector parameters.
        
        Args:
            move_threshold: Minimum move size as ATR multiple
            min_move_candles: Minimum candles for valid move
            momentum_threshold: Minimum momentum score (0.0-1.0)
            volume_multiplier: Volume spike threshold vs average
            breakout_confirmation: Require break of previous levels
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_parameters(
            move_threshold, min_move_candles, momentum_threshold, 
            volume_multiplier
        )
        
        self.move_threshold = move_threshold
        self.min_move_candles = min_move_candles
        self.momentum_threshold = momentum_threshold
        self.volume_multiplier = volume_multiplier
        self.breakout_confirmation = breakout_confirmation
        
        logger.debug(f"BigMoveDetector initialized with move_threshold={move_threshold}")
    
    def _validate_parameters(
        self, 
        move_threshold: float, 
        min_move_candles: int, 
        momentum_threshold: float,
        volume_multiplier: float
    ) -> None:
        """Validate initialization parameters"""
        if move_threshold <= 0:
            raise ValueError(f"move_threshold must be > 0, got {move_threshold}")
        
        if min_move_candles < 1:
            raise ValueError(f"min_move_candles must be >= 1, got {min_move_candles}")
        
        if not 0.0 <= momentum_threshold <= 1.0:
            raise ValueError(f"momentum_threshold must be 0.0-1.0, got {momentum_threshold}")
        
        if volume_multiplier < 1.0:
            raise ValueError(f"volume_multiplier must be >= 1.0, got {volume_multiplier}")
    
    def detect_big_moves(
        self,
        df: pd.DataFrame,
        base_ranges: List[BaseCandleRange],
        fractal_levels: Optional[List[float]] = None
    ) -> List[BigMove]:
        """
        Detect significant moves following base candle ranges.
        
        Args:
            df: OHLC DataFrame with volume data
            base_ranges: List of detected base candle ranges
            fractal_levels: Optional fractal levels for breakout validation
            
        Returns:
            List of BigMove objects representing institutional moves
            
        Performance: <30ms for 1000 bars with 50 base ranges
        """
        if df is None or len(df) == 0:
            return []
        
        if not base_ranges:
            logger.debug("No base ranges provided for big move detection")
            return []
        
        self._validate_input_data(df)
        
        big_moves = []
        
        for base_range in base_ranges:
            try:
                # Look for moves starting after each base range
                move = self._detect_move_after_base(df, base_range, fractal_levels)
                
                if move is not None:
                    big_moves.append(move)
                    logger.debug(f"Detected big move: {move.direction} from {move.start_index} to {move.end_index}")
            
            except Exception as e:
                logger.warning(f"Error detecting move after base range {base_range.start_index}: {e}")
                continue
        
        logger.info(f"Detected {len(big_moves)} big moves from {len(base_ranges)} base ranges")
        return big_moves
    
    def _validate_input_data(self, df: pd.DataFrame) -> None:
        """Validate input OHLC data"""
        required_columns = ['open', 'high', 'low', 'close', 'time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise KeyError(f"Missing required columns: {missing_columns}")
    
    def _detect_move_after_base(
        self, 
        df: pd.DataFrame, 
        base_range: BaseCandleRange,
        fractal_levels: Optional[List[float]] = None
    ) -> Optional[BigMove]:
        """
        Detect big move starting after a base range.
        
        Args:
            df: OHLC DataFrame
            base_range: Base candle range to analyze
            fractal_levels: Optional fractal levels for breakout validation
            
        Returns:
            BigMove object if significant move detected, None otherwise
        """
        # Start looking for move after base range ends
        move_start_index = base_range.end_index + 1
        
        if move_start_index >= len(df):
            return None
        
        # Look for potential move end (scan forward)
        max_scan_distance = min(20, len(df) - move_start_index)  # Limit scan range
        
        best_move = None
        best_magnitude = 0
        
        for potential_end in range(move_start_index + self.min_move_candles - 1, 
                                  move_start_index + max_scan_distance):
            if potential_end >= len(df):
                break
            
            # Calculate move metrics
            magnitude = self._calculate_move_magnitude(df, move_start_index, potential_end, base_range)
            
            if magnitude >= self.move_threshold:
                momentum_score = self._calculate_momentum_score(df, move_start_index, potential_end)
                
                if momentum_score >= self.momentum_threshold:
                    # Determine direction
                    start_price = df.iloc[move_start_index]['close']
                    end_price = df.iloc[potential_end]['close']
                    direction = "bullish" if end_price > start_price else "bearish"
                    
                    # Check volume confirmation
                    volume_confirmation = self._check_volume_confirmation(df, move_start_index, potential_end)
                    
                    # Determine breakout level
                    breakout_level = base_range.high if direction == "bullish" else base_range.low
                    
                    # Validate breakout if required
                    if self.breakout_confirmation and fractal_levels:
                        if not self._validate_breakout_level(breakout_level, direction, fractal_levels):
                            continue
                    
                    # Create move object
                    move = BigMove(
                        start_index=move_start_index,
                        end_index=potential_end,
                        start_time=df.iloc[move_start_index]['time'],
                        end_time=df.iloc[potential_end]['time'],
                        direction=direction,
                        magnitude=magnitude,
                        momentum_score=momentum_score,
                        breakout_level=breakout_level,
                        volume_confirmation=volume_confirmation
                    )
                    
                    # Keep the best move (highest magnitude)
                    if magnitude > best_magnitude:
                        best_move = move
                        best_magnitude = magnitude
        
        return best_move
    
    def _calculate_move_magnitude(
        self, 
        df: pd.DataFrame, 
        start_index: int, 
        end_index: int,
        base_range: BaseCandleRange
    ) -> float:
        """
        Calculate move magnitude in ATR multiples.
        
        Args:
            df: OHLC DataFrame
            start_index: Move start index
            end_index: Move end index
            base_range: Reference base candle range
            
        Returns:
            Move magnitude as ATR multiple
        """
        if start_index >= len(df) or end_index >= len(df) or start_index >= end_index:
            return 0.0
        
        start_price = df.iloc[start_index]['close']
        end_price = df.iloc[end_index]['close']
        
        price_move = abs(end_price - start_price)
        atr_baseline = base_range.atr_at_creation
        
        if atr_baseline <= 0:
            return 0.0
        
        magnitude = price_move / atr_baseline
        return magnitude
    
    def _calculate_momentum_score(
        self, 
        df: pd.DataFrame, 
        start_index: int, 
        end_index: int
    ) -> float:
        """
        Calculate momentum quality score (0.0 to 1.0).
        
        Measures consistency and strength of directional movement.
        
        Args:
            df: OHLC DataFrame
            start_index: Move start index
            end_index: Move end index
            
        Returns:
            Momentum score (0.0 = weak, 1.0 = perfect momentum)
        """
        if start_index >= end_index or end_index >= len(df):
            return 0.0
        
        move_data = df.iloc[start_index:end_index+1]
        
        if len(move_data) < 2:
            return 0.0
        
        # Calculate directional consistency
        closes = move_data['close'].values
        price_changes = np.diff(closes)
        
        if len(price_changes) == 0:
            return 0.0
        
        # Determine primary direction
        total_move = closes[-1] - closes[0]
        if total_move == 0:
            return 0.0
        
        expected_direction = 1 if total_move > 0 else -1
        
        # Count moves in expected direction
        consistent_moves = np.sum((price_changes * expected_direction) > 0)
        total_moves = len(price_changes)
        
        directional_consistency = consistent_moves / total_moves if total_moves > 0 else 0
        
        # Calculate body strength (close vs open)
        body_strengths = []
        for _, candle in move_data.iterrows():
            body_size = abs(candle['close'] - candle['open'])
            candle_range = candle['high'] - candle['low']
            
            if candle_range > 0:
                body_ratio = body_size / candle_range
                body_strengths.append(body_ratio)
        
        avg_body_strength = np.mean(body_strengths) if body_strengths else 0.5
        
        # Calculate momentum persistence
        momentum_values = []
        for i in range(1, len(closes)):
            if i > 0:
                momentum = (closes[i] - closes[i-1]) * expected_direction
                momentum_values.append(max(0, momentum))
        
        momentum_persistence = np.mean(momentum_values) / abs(total_move) if momentum_values and total_move != 0 else 0
        momentum_persistence = min(1.0, momentum_persistence * len(closes))
        
        # Combined momentum score
        momentum_score = (
            directional_consistency * 0.4 +
            avg_body_strength * 0.3 +
            momentum_persistence * 0.3
        )
        
        return max(0.0, min(1.0, momentum_score))
    
    def _check_volume_confirmation(
        self, 
        df: pd.DataFrame, 
        start_index: int, 
        end_index: int
    ) -> bool:
        """
        Check for volume spike confirmation during move.
        
        Args:
            df: OHLC DataFrame with volume
            start_index: Move start index
            end_index: Move end index
            
        Returns:
            True if volume spike detected
        """
        if 'volume' not in df.columns:
            return False
        
        if start_index >= end_index or end_index >= len(df):
            return False
        
        # Calculate average volume before the move (lookback period)
        lookback_start = max(0, start_index - 20)
        baseline_volume = df.iloc[lookback_start:start_index]['volume'].mean()
        
        if baseline_volume <= 0:
            return False
        
        # Check volume during the move
        move_volume = df.iloc[start_index:end_index+1]['volume'].mean()
        
        volume_ratio = move_volume / baseline_volume
        
        return volume_ratio >= self.volume_multiplier
    
    def _validate_breakout_level(
        self, 
        breakout_level: float, 
        direction: str, 
        fractal_levels: List[float]
    ) -> bool:
        """
        Validate breakout against fractal levels.
        
        Args:
            breakout_level: Price level being broken
            direction: Move direction ('bullish' or 'bearish')
            fractal_levels: List of significant fractal levels
            
        Returns:
            True if breakout is valid
        """
        if not fractal_levels:
            return True  # No levels to validate against
        
        # For bullish moves, check if we're breaking above resistance
        # For bearish moves, check if we're breaking below support
        
        tolerance = 0.00001  # Small tolerance for floating point comparison
        
        if direction == "bullish":
            # Check if breakout level is above recent highs
            relevant_levels = [level for level in fractal_levels if level <= breakout_level + tolerance]
            return len(relevant_levels) > 0
        else:
            # Check if breakout level is below recent lows
            relevant_levels = [level for level in fractal_levels if level >= breakout_level - tolerance]
            return len(relevant_levels) > 0
    
    def _validate_breakout(
        self, 
        move: BigMove, 
        fractal_levels: List[float]
    ) -> bool:
        """
        Validate move breaks through previous significant levels.
        
        Args:
            move: BigMove object to validate
            fractal_levels: List of fractal high/low levels
            
        Returns:
            True if move represents valid breakout
        """
        return self._validate_breakout_level(move.breakout_level, move.direction, fractal_levels)


def create_test_detector() -> BigMoveDetector:
    """Create detector with test-friendly parameters"""
    return BigMoveDetector(
        move_threshold=2.0,
        min_move_candles=3,
        momentum_threshold=0.6,
        volume_multiplier=1.5,
        breakout_confirmation=True
    )