"""
Enhanced Fractal Detection System
Implements configurable fractal detection based on strategy requirements.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.monitoring import get_logger

logger = get_logger("fractal_detection")


class FractalType(Enum):
    """Fractal types."""
    UP = "up"
    DOWN = "down"


@dataclass
class Fractal:
    """Fractal data structure."""
    type: FractalType
    index: int
    timestamp: datetime
    price: float
    periods: int  # Number of periods used for detection
    strength: float = 0.0  # Fractal strength (price difference)
    
    def __str__(self) -> str:
        return f"{self.type.value.upper()} Fractal at {self.timestamp}: {self.price:.2f}"


@dataclass
class FractalDetectionConfig:
    """
    Configuration for fractal detection.
    
    Fractal Detection Logic:
    - A fractal high requires the high to be greater than N bars before AND N bars after
    - A fractal low requires the low to be less than N bars before AND N bars after
    - This creates a (2N+1) bar pattern with N-bar confirmation delay
    
    Examples:
    - periods=3: 7-bar pattern, fractal appears 3 bars after actual high/low
    - periods=5: 11-bar pattern, fractal appears 5 bars after actual high/low  
    - periods=11: 23-bar pattern, fractal appears 11 bars after actual high/low
    """
    periods: int = 5  # Number of bars to check on each side (creates N-bar detection delay)
    min_strength_pips: float = 0.0  # Minimum fractal strength in pips
    handle_equal_prices: bool = True  # Handle same high/low edge cases
    require_closes_beyond: bool = False  # Require closes beyond fractal level
    
    def validate(self) -> bool:
        """Validate configuration."""
        if self.periods < 1:
            logger.error("Fractal periods must be >= 1")
            return False
        if self.periods % 2 == 0:
            logger.warning("Even periods may cause symmetry issues - consider odd numbers")
        return True


class FractalDetector:
    """Enhanced fractal detection with configurable parameters."""
    
    def __init__(self, config: Optional[FractalDetectionConfig] = None):
        self.config = config or FractalDetectionConfig()
        if not self.config.validate():
            raise ValueError("Invalid fractal detection configuration")
        
        logger.info(f"Fractal detector initialized with {self.config.periods} periods")
    
    def detect_fractals(self, data: pd.DataFrame) -> List[Fractal]:
        """
        Detect all fractals in the given data.
        
        Args:
            data: OHLC data with High/Low columns and datetime index
                  Supports column names: 'High'/'Low', 'HIGH'/'LOW', or 'high'/'low'
            
        Returns:
            List of detected fractals
        """
        if len(data) < (self.config.periods * 2 + 1):
            logger.warning(f"Insufficient data for fractal detection: {len(data)} bars, need at least {self.config.periods * 2 + 1}")
            return []
        
        # Validate required columns exist
        high_col = None
        low_col = None
        
        for col_name in ['High', 'HIGH', 'high']:
            if col_name in data.columns:
                high_col = col_name
                break
        
        for col_name in ['Low', 'LOW', 'low']:
            if col_name in data.columns:
                low_col = col_name
                break
        
        if high_col is None:
            raise KeyError("High price column not found. Expected one of: 'High', 'HIGH', 'high'")
        if low_col is None:
            raise KeyError("Low price column not found. Expected one of: 'Low', 'LOW', 'low'")
        
        fractals = []
        
        # Detect up fractals (highest highs)
        up_fractals = self._detect_up_fractals(data)
        fractals.extend(up_fractals)
        
        # Detect down fractals (lowest lows)
        down_fractals = self._detect_down_fractals(data)
        fractals.extend(down_fractals)
        
        # Sort by index
        fractals.sort(key=lambda f: f.index)
        
        logger.debug(f"Detected {len(up_fractals)} up fractals and {len(down_fractals)} down fractals")
        return fractals
    
    def _detect_up_fractals(self, data: pd.DataFrame) -> List[Fractal]:
        """Detect up fractals (highest highs)."""
        fractals = []
        # Handle both title case and uppercase column names
        high_col = 'High' if 'High' in data.columns else ('HIGH' if 'HIGH' in data.columns else 'high')
        high_prices = data[high_col].values
        timestamps = data.index
        
        # Check each potential fractal point
        for i in range(self.config.periods, len(high_prices) - self.config.periods):
            current_high = high_prices[i]
            
            # Check left side (must be higher than all previous periods)
            left_condition = all(
                current_high > high_prices[j] 
                for j in range(i - self.config.periods, i)
            )
            
            # Check right side (must be higher than all following periods)
            right_condition = all(
                current_high > high_prices[j] 
                for j in range(i + 1, i + self.config.periods + 1)
            )
            
            # Handle equal prices if configured
            if self.config.handle_equal_prices:
                left_condition = self._check_left_with_equal_handling(high_prices, i, current_high, 'high')
                right_condition = self._check_right_with_equal_handling(high_prices, i, current_high, 'high')
            
            if left_condition and right_condition:
                # Calculate fractal strength
                left_max = max(high_prices[i - self.config.periods:i])
                right_max = max(high_prices[i + 1:i + self.config.periods + 1])
                strength = current_high - max(left_max, right_max)
                
                # Check minimum strength requirement
                if strength >= self.config.min_strength_pips:
                    fractal = Fractal(
                        type=FractalType.UP,
                        index=i,
                        timestamp=timestamps[i],
                        price=current_high,
                        periods=self.config.periods,
                        strength=strength
                    )
                    fractals.append(fractal)
        
        return fractals
    
    def _detect_down_fractals(self, data: pd.DataFrame) -> List[Fractal]:
        """Detect down fractals (lowest lows)."""
        fractals = []
        # Handle both title case and uppercase column names
        low_col = 'Low' if 'Low' in data.columns else ('LOW' if 'LOW' in data.columns else 'low')
        low_prices = data[low_col].values
        timestamps = data.index
        
        # Check each potential fractal point
        for i in range(self.config.periods, len(low_prices) - self.config.periods):
            current_low = low_prices[i]
            
            # Check left side (must be lower than all previous periods)
            left_condition = all(
                current_low < low_prices[j] 
                for j in range(i - self.config.periods, i)
            )
            
            # Check right side (must be lower than all following periods)
            right_condition = all(
                current_low < low_prices[j] 
                for j in range(i + 1, i + self.config.periods + 1)
            )
            
            # Handle equal prices if configured
            if self.config.handle_equal_prices:
                left_condition = self._check_left_with_equal_handling(low_prices, i, current_low, 'low')
                right_condition = self._check_right_with_equal_handling(low_prices, i, current_low, 'low')
            
            if left_condition and right_condition:
                # Calculate fractal strength
                left_min = min(low_prices[i - self.config.periods:i])
                right_min = min(low_prices[i + 1:i + self.config.periods + 1])
                strength = min(left_min, right_min) - current_low
                
                # Check minimum strength requirement
                if strength >= self.config.min_strength_pips:
                    fractal = Fractal(
                        type=FractalType.DOWN,
                        index=i,
                        timestamp=timestamps[i],
                        price=current_low,
                        periods=self.config.periods,
                        strength=strength
                    )
                    fractals.append(fractal)
        
        return fractals
    
    def _check_left_with_equal_handling(self, prices: np.ndarray, center_idx: int, 
                                      center_price: float, price_type: str) -> bool:
        """Check left side with equal price handling."""
        for j in range(center_idx - self.config.periods, center_idx):
            if price_type == 'high':
                if prices[j] >= center_price:  # Equal or higher invalidates up fractal
                    return False
            else:  # low
                if prices[j] <= center_price:  # Equal or lower invalidates down fractal
                    return False
        return True
    
    def _check_right_with_equal_handling(self, prices: np.ndarray, center_idx: int, 
                                       center_price: float, price_type: str) -> bool:
        """Check right side with equal price handling."""
        for j in range(center_idx + 1, center_idx + self.config.periods + 1):
            if price_type == 'high':
                if prices[j] >= center_price:  # Equal or higher invalidates up fractal
                    return False
            else:  # low
                if prices[j] <= center_price:  # Equal or lower invalidates down fractal
                    return False
        return True
    
    def get_fractals_in_range(self, fractals: List[Fractal], 
                            start_idx: int, end_idx: int) -> List[Fractal]:
        """Get fractals within a specific index range."""
        return [f for f in fractals if start_idx <= f.index <= end_idx]
    
    def get_latest_fractals(self, fractals: List[Fractal], count: int = 10) -> List[Fractal]:
        """Get the most recent fractals."""
        return sorted(fractals, key=lambda f: f.index)[-count:]
    
    def get_fractals_by_type(self, fractals: List[Fractal], 
                           fractal_type: FractalType) -> List[Fractal]:
        """Get fractals of a specific type."""
        return [f for f in fractals if f.type == fractal_type]
    
    def calculate_fractal_statistics(self, fractals: List[Fractal]) -> Dict[str, Any]:
        """Calculate statistics about detected fractals."""
        if not fractals:
            return {}
        
        up_fractals = self.get_fractals_by_type(fractals, FractalType.UP)
        down_fractals = self.get_fractals_by_type(fractals, FractalType.DOWN)
        
        stats = {
            'total_fractals': len(fractals),
            'up_fractals': len(up_fractals),
            'down_fractals': len(down_fractals),
            'up_percentage': len(up_fractals) / len(fractals) * 100 if fractals else 0,
            'down_percentage': len(down_fractals) / len(fractals) * 100 if fractals else 0,
        }
        
        if up_fractals:
            up_strengths = [f.strength for f in up_fractals]
            stats.update({
                'up_avg_strength': np.mean(up_strengths),
                'up_max_strength': max(up_strengths),
                'up_min_strength': min(up_strengths),
            })
        
        if down_fractals:
            down_strengths = [f.strength for f in down_fractals]
            stats.update({
                'down_avg_strength': np.mean(down_strengths),
                'down_max_strength': max(down_strengths),
                'down_min_strength': min(down_strengths),
            })
        
        # Time-based statistics
        if len(fractals) > 1:
            time_gaps = []
            sorted_fractals = sorted(fractals, key=lambda f: f.index)
            for i in range(1, len(sorted_fractals)):
                gap = sorted_fractals[i].index - sorted_fractals[i-1].index
                time_gaps.append(gap)
            
            stats.update({
                'avg_time_between_fractals': np.mean(time_gaps),
                'min_time_between_fractals': min(time_gaps),
                'max_time_between_fractals': max(time_gaps),
            })
        
        return stats


class MultiTimeframeFractalDetector:
    """Detect fractals across multiple timeframes."""
    
    def __init__(self, configs: Dict[str, FractalDetectionConfig]):
        """
        Initialize with different configs for different periods.
        
        Args:
            configs: Dictionary mapping config names to FractalDetectionConfig
        """
        self.detectors = {
            name: FractalDetector(config) 
            for name, config in configs.items()
        }
        logger.info(f"Multi-timeframe detector initialized with {len(self.detectors)} configurations")
    
    def detect_all_fractals(self, data: pd.DataFrame) -> Dict[str, List[Fractal]]:
        """Detect fractals using all configured detectors."""
        results = {}
        
        for name, detector in self.detectors.items():
            try:
                fractals = detector.detect_fractals(data)
                results[name] = fractals
                logger.debug(f"Config '{name}': {len(fractals)} fractals detected")
            except Exception as e:
                logger.error(f"Error detecting fractals with config '{name}': {e}")
                results[name] = []
        
        return results
    
    def get_consensus_fractals(self, data: pd.DataFrame, 
                             min_confirmations: int = 2) -> List[Fractal]:
        """
        Get fractals that are confirmed by multiple detectors.
        
        Args:
            data: OHLC data
            min_confirmations: Minimum number of detectors that must agree
            
        Returns:
            List of consensus fractals
        """
        all_results = self.detect_all_fractals(data)
        
        # Group fractals by approximate location
        fractal_groups = {}
        tolerance = 2  # Allow 2-bar tolerance for grouping
        
        for config_name, fractals in all_results.items():
            for fractal in fractals:
                # Find if this fractal is close to an existing group
                group_key = None
                for existing_idx in fractal_groups.keys():
                    if abs(fractal.index - existing_idx) <= tolerance and fractal.type.value in existing_idx:
                        group_key = existing_idx
                        break
                
                if group_key is None:
                    # Create new group
                    group_key = f"{fractal.type.value}_{fractal.index}"
                    fractal_groups[group_key] = []
                
                fractal_groups[group_key].append((config_name, fractal))
        
        # Filter groups by minimum confirmations
        consensus_fractals = []
        for group_key, group_fractals in fractal_groups.items():
            if len(group_fractals) >= min_confirmations:
                # Use the fractal from the most restrictive config (highest periods)
                best_fractal = max(group_fractals, key=lambda x: x[1].periods)[1]
                consensus_fractals.append(best_fractal)
        
        return sorted(consensus_fractals, key=lambda f: f.index)


# Convenience functions
def detect_fractals_simple(data: pd.DataFrame, periods: int = 5) -> List[Fractal]:
    """Simple fractal detection with default settings."""
    config = FractalDetectionConfig(periods=periods)
    detector = FractalDetector(config)
    return detector.detect_fractals(data)

def detect_fractals_with_strength(data: pd.DataFrame, periods: int = 5, 
                                min_strength: float = 10.0) -> List[Fractal]:
    """Fractal detection with minimum strength requirement."""
    config = FractalDetectionConfig(periods=periods, min_strength_pips=min_strength)
    detector = FractalDetector(config)
    return detector.detect_fractals(data)