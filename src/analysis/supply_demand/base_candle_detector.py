"""
BaseCandleDetector - Professional Consolidation Detection

Detects consolidation areas (base candles) that precede significant price moves
using eWavesHarmonics methodology for identifying institutional accumulation zones.

Performance Target: <20ms per detection cycle
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BaseCandleRange:
    """
    Represents a range of base candles before a big move.
    
    Based on eWavesHarmonics methodology for identifying institutional order zones.
    """
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    atr_at_creation: float
    candle_count: int
    consolidation_score: float  # 0.0 to 1.0


class BaseCandleDetector:
    """
    Detects consolidation areas (base candles) that precede significant price moves.
    
    Based on eWavesHarmonics methodology for identifying institutional accumulation zones.
    Performance Target: <20ms per detection cycle
    """
    
    def __init__(
        self,
        consolidation_threshold: float = 0.5,  # ATR percentage
        min_base_candles: int = 2,
        max_base_candles: int = 10,
        body_size_threshold: float = 0.3,      # Body/ATR ratio
        atr_period: int = 14
    ):
        """
        Initialize base candle detector with eWavesHarmonics parameters.
        
        Args:
            consolidation_threshold: Maximum candle range as % of ATR
            min_base_candles: Minimum consecutive consolidation candles
            max_base_candles: Maximum consecutive consolidation candles
            body_size_threshold: Maximum body size as % of ATR
            atr_period: Period for ATR calculation
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_parameters(
            consolidation_threshold, min_base_candles, max_base_candles, 
            body_size_threshold, atr_period
        )
        
        self.consolidation_threshold = consolidation_threshold
        self.min_base_candles = min_base_candles
        self.max_base_candles = max_base_candles
        self.body_size_threshold = body_size_threshold
        self.atr_period = atr_period
        self._atr_cache: Optional[pd.Series] = None
        
        logger.debug(f"BaseCandleDetector initialized with consolidation_threshold={consolidation_threshold}")
    
    def _validate_parameters(
        self, 
        consolidation_threshold: float, 
        min_base_candles: int, 
        max_base_candles: int,
        body_size_threshold: float, 
        atr_period: int
    ) -> None:
        """Validate initialization parameters"""
        if not 0.1 <= consolidation_threshold <= 1.0:
            raise ValueError(f"consolidation_threshold must be 0.1-1.0, got {consolidation_threshold}")
        
        if min_base_candles < 1:
            raise ValueError(f"min_base_candles must be >= 1, got {min_base_candles}")
        
        if max_base_candles < min_base_candles:
            raise ValueError(f"max_base_candles ({max_base_candles}) must be >= min_base_candles ({min_base_candles})")
        
        if not 0.1 <= body_size_threshold <= 1.0:
            raise ValueError(f"body_size_threshold must be 0.1-1.0, got {body_size_threshold}")
        
        if atr_period < 1:
            raise ValueError(f"atr_period must be >= 1, got {atr_period}")
    
    def detect_base_candles(
        self, 
        df: pd.DataFrame, 
        start_index: int = 0, 
        end_index: Optional[int] = None
    ) -> List[BaseCandleRange]:
        """
        Detect base candle ranges in OHLC data.
        
        Args:
            df: OHLC DataFrame with columns ['open', 'high', 'low', 'close', 'time']
            start_index: Starting index for detection
            end_index: Ending index for detection (None = end of data)
            
        Returns:
            List of BaseCandleRange objects representing consolidation areas
            
        Raises:
            ValueError: If data is insufficient or invalid
            KeyError: If required columns are missing
            
        Performance: <20ms for 1000 bars
        """
        self._validate_input_data(df)
        
        if end_index is None:
            end_index = len(df) - 1
        
        if start_index >= len(df) or end_index >= len(df):
            logger.warning(f"Invalid index range: {start_index}-{end_index} for data length {len(df)}")
            return []
        
        if len(df) < self.atr_period:
            logger.warning(f"Insufficient data for ATR calculation: {len(df)} < {self.atr_period}")
            return []
        
        # Calculate ATR for volatility baseline
        atr_series = self._calculate_atr(df)
        
        # Find consolidation ranges
        ranges = []
        i = start_index
        
        while i <= end_index - self.min_base_candles:
            # Look for start of consolidation
            if self._is_consolidation_candle(df.iloc[i], atr_series.iloc[i]):
                # Found potential start, look for consecutive consolidation candles
                consolidation_end = self._find_consolidation_end(df, atr_series, i, end_index)
                
                if consolidation_end is not None:
                    candle_count = consolidation_end - i + 1
                    
                    # Validate minimum length
                    if candle_count >= self.min_base_candles:
                        # Create and validate range
                        base_range = self._create_base_range(df, atr_series, i, consolidation_end)
                        
                        if base_range.consolidation_score >= 0.3:  # Minimum quality threshold
                            ranges.append(base_range)
                            logger.debug(f"Detected base candle range: {i}-{consolidation_end} ({candle_count} candles)")
                    
                    # Move past this range
                    i = consolidation_end + 1
                else:
                    i += 1
            else:
                i += 1
        
        logger.info(f"Detected {len(ranges)} base candle ranges in {len(df)} bars")
        return ranges
    
    def _validate_input_data(self, df: pd.DataFrame) -> None:
        """Validate input OHLC data"""
        if df is None or len(df) == 0:
            raise ValueError("Input DataFrame is empty or None")
        
        required_columns = ['open', 'high', 'low', 'close', 'time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise KeyError(f"Missing required columns: {missing_columns}")
        
        # Validate OHLC relationships
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ).any()
        
        if invalid_ohlc:
            raise ValueError("Invalid OHLC data: high/low relationships violated")
    
    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Average True Range for volatility baseline.
        
        Args:
            df: OHLC DataFrame
            
        Returns:
            Series with ATR values
        """
        if self._atr_cache is not None and len(self._atr_cache) == len(df):
            return self._atr_cache
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        
        # Handle first bar (no previous close)
        true_range.iloc[0] = high_low.iloc[0]
        
        # Calculate ATR using exponential moving average
        atr_series = true_range.ewm(span=self.atr_period, adjust=False).mean()
        
        # For very early bars, use simple average to avoid extreme values
        for i in range(min(self.atr_period, len(atr_series))):
            if i > 0:
                atr_series.iloc[i] = true_range.iloc[:i+1].mean()
        
        # Ensure no zero ATR values (minimum threshold)
        atr_series = np.maximum(atr_series, 0.00001)
        
        self._atr_cache = atr_series
        return atr_series
    
    def _is_consolidation_candle(
        self, 
        candle: pd.Series, 
        atr_value: float
    ) -> bool:
        """
        Determine if a single candle qualifies as consolidation.
        
        Args:
            candle: Single candle OHLC data
            atr_value: ATR value for size comparison
            
        Returns:
            True if candle meets consolidation criteria
        """
        if atr_value <= 0:
            return False
        
        # Calculate candle metrics
        candle_range = candle['high'] - candle['low']
        candle_body = abs(candle['close'] - candle['open'])
        
        # Check range threshold
        range_ratio = candle_range / atr_value
        if range_ratio > self.consolidation_threshold:
            return False
        
        # Check body size threshold
        body_ratio = candle_body / atr_value
        if body_ratio > self.body_size_threshold:
            return False
        
        return True
    
    def _find_consolidation_end(
        self, 
        df: pd.DataFrame, 
        atr_series: pd.Series, 
        start_index: int, 
        max_end_index: int
    ) -> Optional[int]:
        """
        Find the end index of a consolidation range starting at start_index.
        
        Args:
            df: OHLC DataFrame
            atr_series: ATR values
            start_index: Start of potential consolidation
            max_end_index: Maximum end index to consider
            
        Returns:
            End index of consolidation or None if not found
        """
        end_index = start_index
        max_search_end = min(start_index + self.max_base_candles - 1, max_end_index)
        
        # Extend as long as candles qualify as consolidation
        for i in range(start_index + 1, max_search_end + 1):
            if i >= len(df) or i >= len(atr_series):
                break
                
            if self._is_consolidation_candle(df.iloc[i], atr_series.iloc[i]):
                end_index = i
            else:
                break
        
        # Return end index only if we have minimum candles
        if end_index - start_index + 1 >= self.min_base_candles:
            return end_index
        
        return None
    
    def _create_base_range(
        self, 
        df: pd.DataFrame, 
        atr_series: pd.Series, 
        start_index: int, 
        end_index: int
    ) -> BaseCandleRange:
        """
        Create BaseCandleRange object from detected consolidation.
        
        Args:
            df: OHLC DataFrame
            atr_series: ATR values
            start_index: Start of consolidation
            end_index: End of consolidation
            
        Returns:
            BaseCandleRange object
        """
        range_data = df.iloc[start_index:end_index+1]
        
        # Calculate range boundaries
        high = range_data['high'].max()
        low = range_data['low'].min()
        
        # Get time boundaries
        start_time = df.iloc[start_index]['time']
        end_time = df.iloc[end_index]['time']
        
        # Calculate average ATR for the range
        atr_at_creation = atr_series.iloc[start_index:end_index+1].mean()
        
        # Calculate candle count
        candle_count = end_index - start_index + 1
        
        # Calculate consolidation score
        consolidation_score = self._validate_base_range(range_data)
        
        return BaseCandleRange(
            start_index=start_index,
            end_index=end_index,
            start_time=start_time,
            end_time=end_time,
            high=high,
            low=low,
            atr_at_creation=atr_at_creation,
            candle_count=candle_count,
            consolidation_score=consolidation_score
        )
    
    def _validate_base_range(self, candles: pd.DataFrame) -> float:
        """
        Validate and score quality of base candle range.
        
        Args:
            candles: DataFrame of base candles
            
        Returns:
            Consolidation score (0.0 to 1.0)
        """
        if len(candles) == 0:
            return 0.0
        
        # Calculate range tightness
        price_range = candles['high'].max() - candles['low'].min()
        avg_price = (candles['high'].max() + candles['low'].min()) / 2
        
        if avg_price <= 0:
            return 0.0
        
        range_percentage = price_range / avg_price
        
        # Score based on range tightness (tighter = higher score)
        tightness_score = max(0.0, 1.0 - (range_percentage / 0.01))  # Normalize to 1% range
        
        # Calculate body size consistency
        body_sizes = abs(candles['close'] - candles['open'])
        body_consistency = 1.0 - (body_sizes.std() / (body_sizes.mean() + 0.00001))
        body_consistency = max(0.0, min(1.0, body_consistency))
        
        # Calculate time consistency (prefer consistent spacing)
        time_consistency = 0.8  # Assume good consistency for now
        
        # Combined score with weights
        consolidation_score = (
            tightness_score * 0.5 +
            body_consistency * 0.3 +
            time_consistency * 0.2
        )
        
        return max(0.0, min(1.0, consolidation_score))


def create_test_detector() -> BaseCandleDetector:
    """Create detector with test-friendly parameters"""
    return BaseCandleDetector(
        consolidation_threshold=0.5,
        min_base_candles=2,
        max_base_candles=10,
        body_size_threshold=0.3,
        atr_period=14
    )