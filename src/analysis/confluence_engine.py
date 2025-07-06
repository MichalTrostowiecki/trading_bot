"""
Comprehensive Confluence Testing Engine
Designed for testing multiple confluence factors and ML/AI integration.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ConfluenceFactorType(Enum):
    """Types of confluence factors for testing."""
    FIBONACCI = "fibonacci"
    VOLUME = "volume"
    CANDLESTICK = "candlestick"
    RSI = "rsi"
    MACD = "macd"
    ABC_PATTERN = "abc_pattern"
    SWING_LEVEL = "swing_level"
    SUPPORT_RESISTANCE = "support_resistance"
    TIMEFRAME = "timeframe"
    MOMENTUM = "momentum"

class ConfluenceStrength(Enum):
    """Confluence strength levels for visual representation."""
    WEAK = "weak"        # 1-2 factors
    MODERATE = "moderate"  # 3-4 factors
    STRONG = "strong"    # 5+ factors

@dataclass
class ConfluenceFactor:
    """Individual confluence factor with scoring."""
    factor_type: ConfluenceFactorType
    value: float
    weight: float = 1.0
    confidence: float = 0.0
    description: str = ""
    price_level: Optional[float] = None
    timestamp: Optional[pd.Timestamp] = None

@dataclass
class ConfluenceZone:
    """Confluence zone combining multiple factors."""
    price_level: float
    timestamp: pd.Timestamp
    factors: List[ConfluenceFactor]
    total_score: float
    weighted_score: float
    strength: ConfluenceStrength
    direction: str  # 'bullish' or 'bearish'
    symbol: str
    timeframe: str

@dataclass
class CandlestickPattern:
    """Candlestick pattern detection result."""
    pattern_type: str
    timestamp: pd.Timestamp
    price: float
    reliability: float
    direction: str  # 'bullish' or 'bearish'
    strength: str   # 'weak', 'moderate', 'strong'
    confirmation: bool = False

class ConfluenceEngine:
    """
    Comprehensive confluence testing engine for multi-factor analysis.
    
    Features:
    - Multiple confluence factor types
    - Configurable weights and thresholds
    - Visual marker generation
    - ML feature extraction
    - Performance tracking
    """
    
    def __init__(self, 
                 confluence_distance: float = 0.1,  # % price distance to group factors
                 min_factors: int = 2,
                 factor_weights: Dict[ConfluenceFactorType, float] = None):
        """
        Initialize confluence engine.
        
        Args:
            confluence_distance: Price distance % to group factors into zones
            min_factors: Minimum factors required for confluence
            factor_weights: Custom weights for different factor types
        """
        self.confluence_distance = confluence_distance
        self.min_factors = min_factors
        
        # Default factor weights (can be optimized via ML)
        self.factor_weights = factor_weights or {
            ConfluenceFactorType.FIBONACCI: 1.5,
            ConfluenceFactorType.VOLUME: 1.2,
            ConfluenceFactorType.CANDLESTICK: 1.0,
            ConfluenceFactorType.RSI: 0.8,
            ConfluenceFactorType.MACD: 0.8,
            ConfluenceFactorType.ABC_PATTERN: 2.0,
            ConfluenceFactorType.SWING_LEVEL: 1.3,
            ConfluenceFactorType.SUPPORT_RESISTANCE: 1.1,
            ConfluenceFactorType.TIMEFRAME: 1.8,
            ConfluenceFactorType.MOMENTUM: 0.9
        }
        
        # Testing configuration
        self.test_configs = {
            'fibonacci_levels': [0.236, 0.382, 0.500, 0.618, 0.786],
            'volume_spike_threshold': 1.5,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'candlestick_patterns': [
                'hammer', 'engulfing', 'doji', 'pin_bar', 'shooting_star',
                'hanging_man', 'dark_cloud', 'piercing_line'
            ]
        }
        
        # Storage for analysis
        self.confluence_zones: List[ConfluenceZone] = []
        self.individual_factors: List[ConfluenceFactor] = []
        self.candlestick_patterns: List[CandlestickPattern] = []
        
    def detect_fibonacci_confluence(self, 
                                   fibonacci_levels: List[Dict],
                                   current_price: float,
                                   timestamp: pd.Timestamp) -> List[ConfluenceFactor]:
        """Detect Fibonacci level confluence factors."""
        factors = []
        
        for fib_level in fibonacci_levels:
            price_diff = abs(current_price - fib_level['price']) / current_price
            if price_diff <= self.confluence_distance:
                # Higher weight for key levels
                weight = 1.5 if fib_level['level'] in [0.382, 0.618] else 1.0
                confidence = 1.0 - (price_diff / self.confluence_distance)
                
                factors.append(ConfluenceFactor(
                    factor_type=ConfluenceFactorType.FIBONACCI,
                    value=fib_level['level'],
                    weight=weight,
                    confidence=confidence,
                    description=f"Fibonacci {fib_level['level']*100:.1f}%",
                    price_level=fib_level['price'],
                    timestamp=timestamp
                ))
        
        return factors
    
    def detect_volume_confluence(self, 
                                df: pd.DataFrame,
                                current_index: int,
                                lookback_periods: int = 20) -> List[ConfluenceFactor]:
        """Detect volume-based confluence factors."""
        factors = []
        
        if current_index < lookback_periods:
            return factors
        
        # Calculate volume metrics
        current_volume = df.iloc[current_index]['volume']
        avg_volume = df.iloc[current_index-lookback_periods:current_index]['volume'].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Volume spike detection
        if volume_ratio >= self.test_configs['volume_spike_threshold']:
            confidence = min(volume_ratio / 3.0, 1.0)  # Cap at 1.0
            factors.append(ConfluenceFactor(
                factor_type=ConfluenceFactorType.VOLUME,
                value=volume_ratio,
                weight=self.factor_weights[ConfluenceFactorType.VOLUME],
                confidence=confidence,
                description=f"Volume spike {volume_ratio:.1f}x",
                timestamp=df.index[current_index]
            ))
        
        return factors
    
    def detect_candlestick_patterns(self, 
                                   df: pd.DataFrame,
                                   current_index: int) -> List[CandlestickPattern]:
        """Detect candlestick patterns at current position."""
        patterns = []
        
        if current_index < 2:
            return patterns
        
        current_bar = df.iloc[current_index]
        prev_bar = df.iloc[current_index - 1]
        
        # Hammer pattern detection
        hammer_pattern = self._detect_hammer_pattern(current_bar)
        if hammer_pattern:
            patterns.append(hammer_pattern)
        
        # Engulfing pattern detection
        engulfing_pattern = self._detect_engulfing_pattern(current_bar, prev_bar)
        if engulfing_pattern:
            patterns.append(engulfing_pattern)
        
        # Doji pattern detection
        doji_pattern = self._detect_doji_pattern(current_bar)
        if doji_pattern:
            patterns.append(doji_pattern)
        
        # Pin bar pattern detection
        pin_bar_pattern = self._detect_pin_bar_pattern(current_bar)
        if pin_bar_pattern:
            patterns.append(pin_bar_pattern)
        
        return patterns
    
    def _detect_hammer_pattern(self, bar: pd.Series) -> Optional[CandlestickPattern]:
        """Detect hammer candlestick pattern."""
        open_price = bar['open']
        high_price = bar['high']
        low_price = bar['low']
        close_price = bar['close']
        
        body_size = abs(close_price - open_price)
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)
        
        # Hammer criteria: lower shadow >= 2x body, small upper shadow
        if (body_size > 0 and 
            lower_shadow >= 2 * body_size and 
            upper_shadow <= 0.5 * body_size):
            
            reliability = min(lower_shadow / body_size / 2, 1.0)
            strength = "strong" if reliability > 0.8 else "moderate" if reliability > 0.5 else "weak"
            
            return CandlestickPattern(
                pattern_type="hammer",
                timestamp=bar.name,
                price=close_price,
                reliability=reliability,
                direction="bullish",
                strength=strength
            )
        
        return None
    
    def _detect_engulfing_pattern(self, current_bar: pd.Series, prev_bar: pd.Series) -> Optional[CandlestickPattern]:
        """Detect engulfing candlestick pattern."""
        curr_open = current_bar['open']
        curr_close = current_bar['close']
        prev_open = prev_bar['open']
        prev_close = prev_bar['close']
        
        # Bullish engulfing: previous red, current green, current body engulfs previous
        if (prev_close < prev_open and  # Previous bar bearish
            curr_close > curr_open and  # Current bar bullish
            curr_open < prev_close and  # Current opens below previous close
            curr_close > prev_open):    # Current closes above previous open
            
            engulfing_ratio = abs(curr_close - curr_open) / abs(prev_close - prev_open)
            reliability = min(engulfing_ratio, 1.0)
            strength = "strong" if reliability > 0.8 else "moderate" if reliability > 0.5 else "weak"
            
            return CandlestickPattern(
                pattern_type="bullish_engulfing",
                timestamp=current_bar.name,
                price=curr_close,
                reliability=reliability,
                direction="bullish",
                strength=strength
            )
        
        # Bearish engulfing: previous green, current red, current body engulfs previous
        elif (prev_close > prev_open and  # Previous bar bullish
              curr_close < curr_open and  # Current bar bearish
              curr_open > prev_close and  # Current opens above previous close
              curr_close < prev_open):    # Current closes below previous open
            
            engulfing_ratio = abs(curr_open - curr_close) / abs(prev_open - prev_close)
            reliability = min(engulfing_ratio, 1.0)
            strength = "strong" if reliability > 0.8 else "moderate" if reliability > 0.5 else "weak"
            
            return CandlestickPattern(
                pattern_type="bearish_engulfing",
                timestamp=current_bar.name,
                price=curr_close,
                reliability=reliability,
                direction="bearish",
                strength=strength
            )
        
        return None
    
    def _detect_doji_pattern(self, bar: pd.Series) -> Optional[CandlestickPattern]:
        """Detect doji candlestick pattern."""
        open_price = bar['open']
        close_price = bar['close']
        high_price = bar['high']
        low_price = bar['low']
        
        body_size = abs(close_price - open_price)
        total_range = high_price - low_price
        
        # Doji criteria: body size < 5% of total range
        if total_range > 0 and body_size / total_range < 0.05:
            reliability = 1.0 - (body_size / total_range / 0.05)
            strength = "strong" if reliability > 0.8 else "moderate"
            
            return CandlestickPattern(
                pattern_type="doji",
                timestamp=bar.name,
                price=close_price,
                reliability=reliability,
                direction="neutral",
                strength=strength
            )
        
        return None
    
    def _detect_pin_bar_pattern(self, bar: pd.Series) -> Optional[CandlestickPattern]:
        """Detect pin bar candlestick pattern."""
        open_price = bar['open']
        high_price = bar['high']
        low_price = bar['low']
        close_price = bar['close']
        
        body_size = abs(close_price - open_price)
        total_range = high_price - low_price
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        
        if total_range == 0:
            return None
        
        # Pin bar criteria: one shadow >= 66% of total range
        if lower_shadow >= 0.66 * total_range:
            # Bullish pin bar (long lower shadow)
            reliability = lower_shadow / total_range
            strength = "strong" if reliability > 0.8 else "moderate"
            
            return CandlestickPattern(
                pattern_type="bullish_pin_bar",
                timestamp=bar.name,
                price=close_price,
                reliability=reliability,
                direction="bullish",
                strength=strength
            )
        
        elif upper_shadow >= 0.66 * total_range:
            # Bearish pin bar (long upper shadow)
            reliability = upper_shadow / total_range
            strength = "strong" if reliability > 0.8 else "moderate"
            
            return CandlestickPattern(
                pattern_type="bearish_pin_bar",
                timestamp=bar.name,
                price=close_price,
                reliability=reliability,
                direction="bearish",
                strength=strength
            )
        
        return None
    
    def calculate_confluence_zones(self, 
                                  factors: List[ConfluenceFactor],
                                  symbol: str,
                                  timeframe: str) -> List[ConfluenceZone]:
        """Group factors into confluence zones based on price proximity."""
        if not factors:
            return []
        
        zones = []
        used_factors = set()
        
        for i, factor in enumerate(factors):
            if i in used_factors or not factor.price_level:
                continue
            
            # Find nearby factors
            zone_factors = [factor]
            zone_price = factor.price_level
            
            for j, other_factor in enumerate(factors[i+1:], i+1):
                if j in used_factors or not other_factor.price_level:
                    continue
                
                price_diff = abs(other_factor.price_level - zone_price) / zone_price
                if price_diff <= self.confluence_distance:
                    zone_factors.append(other_factor)
                    used_factors.add(j)
            
            used_factors.add(i)
            
            # Only create zone if minimum factors met
            if len(zone_factors) >= self.min_factors:
                # Calculate zone metrics
                total_score = len(zone_factors)
                weighted_score = sum(f.weight * f.confidence for f in zone_factors)
                
                # Determine strength
                if total_score >= 5:
                    strength = ConfluenceStrength.STRONG
                elif total_score >= 3:
                    strength = ConfluenceStrength.MODERATE
                else:
                    strength = ConfluenceStrength.WEAK
                
                # Determine direction (majority vote)
                bullish_factors = sum(1 for f in zone_factors if f.factor_type in [
                    ConfluenceFactorType.FIBONACCI, ConfluenceFactorType.VOLUME
                ])
                direction = "bullish" if bullish_factors > len(zone_factors) / 2 else "bearish"
                
                zones.append(ConfluenceZone(
                    price_level=zone_price,
                    timestamp=factor.timestamp,
                    factors=zone_factors,
                    total_score=total_score,
                    weighted_score=weighted_score,
                    strength=strength,
                    direction=direction,
                    symbol=symbol,
                    timeframe=timeframe
                ))
        
        return zones
    
    def generate_visual_markers(self, 
                               confluence_zones: List[ConfluenceZone],
                               candlestick_patterns: List[CandlestickPattern]) -> Dict[str, List[Dict]]:
        """Generate visual markers for TradingView chart."""
        markers = {
            'confluence_zones': [],
            'candlestick_patterns': []
        }
        
        # Confluence zone markers
        for zone in confluence_zones:
            color = {
                ConfluenceStrength.WEAK: '#FFA500',      # Orange
                ConfluenceStrength.MODERATE: '#FF6347',  # Red-Orange
                ConfluenceStrength.STRONG: '#FF0000'     # Red
            }.get(zone.strength, '#808080')
            
            markers['confluence_zones'].append({
                'time': zone.timestamp.isoformat(),
                'position': 'aboveBar' if zone.direction == 'bullish' else 'belowBar',
                'color': color,
                'shape': 'circle',
                'text': f"{zone.total_score}x",
                'size': 1 if zone.strength == ConfluenceStrength.WEAK else 2
            })
        
        # Candlestick pattern markers
        for pattern in candlestick_patterns:
            color = '#00FF00' if pattern.direction == 'bullish' else '#FF0000'
            if pattern.direction == 'neutral':
                color = '#FFD700'  # Gold for doji
            
            shape = {
                'hammer': 'arrowUp',
                'bullish_engulfing': 'arrowUp',
                'bearish_engulfing': 'arrowDown',
                'doji': 'circle',
                'bullish_pin_bar': 'arrowUp',
                'bearish_pin_bar': 'arrowDown'
            }.get(pattern.pattern_type, 'circle')
            
            markers['candlestick_patterns'].append({
                'time': pattern.timestamp.isoformat(),
                'position': 'aboveBar' if pattern.direction == 'bullish' else 'belowBar',
                'color': color,
                'shape': shape,
                'text': pattern.pattern_type.upper()[:3],
                'size': 1 if pattern.strength == 'weak' else 2
            })
        
        return markers
    
    def extract_ml_features(self, confluence_zones: List[ConfluenceZone]) -> Dict[str, Any]:
        """Extract features for ML/AI training."""
        if not confluence_zones:
            return {}
        
        features = {}
        
        # Basic confluence metrics
        features['total_zones'] = len(confluence_zones)
        features['avg_zone_score'] = np.mean([zone.total_score for zone in confluence_zones])
        features['max_zone_score'] = max([zone.total_score for zone in confluence_zones])
        features['strong_zones'] = sum(1 for zone in confluence_zones if zone.strength == ConfluenceStrength.STRONG)
        
        # Factor distribution
        factor_counts = {}
        for zone in confluence_zones:
            for factor in zone.factors:
                factor_type = factor.factor_type.value
                factor_counts[factor_type] = factor_counts.get(factor_type, 0) + 1
        
        features['factor_distribution'] = factor_counts
        
        # Directional bias
        bullish_zones = sum(1 for zone in confluence_zones if zone.direction == 'bullish')
        features['bullish_bias'] = bullish_zones / len(confluence_zones)
        
        return features
    
    def process_bar(self, 
                   df: pd.DataFrame,
                   current_index: int,
                   fibonacci_levels: List[Dict],
                   abc_patterns: List[Dict],
                   symbol: str,
                   timeframe: str) -> Dict[str, Any]:
        """Process single bar for confluence analysis."""
        results = {
            'confluence_zones': [],
            'candlestick_patterns': [],
            'visual_markers': {},
            'ml_features': {},
            'total_factors': 0
        }
        
        if current_index < 2:
            return results
        
        current_bar = df.iloc[current_index]
        current_price = current_bar['close']
        timestamp = current_bar.name
        
        # Collect all confluence factors
        all_factors = []
        
        # 1. Fibonacci confluence
        if fibonacci_levels:
            fib_factors = self.detect_fibonacci_confluence(fibonacci_levels, current_price, timestamp)
            all_factors.extend(fib_factors)
        
        # 2. Volume confluence
        volume_factors = self.detect_volume_confluence(df, current_index)
        all_factors.extend(volume_factors)
        
        # 3. Candlestick patterns
        candlestick_patterns = self.detect_candlestick_patterns(df, current_index)
        
        # Convert candlestick patterns to confluence factors
        for pattern in candlestick_patterns:
            all_factors.append(ConfluenceFactor(
                factor_type=ConfluenceFactorType.CANDLESTICK,
                value=pattern.reliability,
                weight=self.factor_weights[ConfluenceFactorType.CANDLESTICK],
                confidence=pattern.reliability,
                description=pattern.pattern_type,
                price_level=pattern.price,
                timestamp=pattern.timestamp
            ))
        
        # Calculate confluence zones
        confluence_zones = self.calculate_confluence_zones(all_factors, symbol, timeframe)
        
        # Generate visual markers
        visual_markers = self.generate_visual_markers(confluence_zones, candlestick_patterns)
        
        # Extract ML features
        ml_features = self.extract_ml_features(confluence_zones)
        
        # Store results
        self.confluence_zones.extend(confluence_zones)
        self.individual_factors.extend(all_factors)
        self.candlestick_patterns.extend(candlestick_patterns)
        
        results.update({
            'confluence_zones': [self._serialize_confluence_zone(zone) for zone in confluence_zones],
            'candlestick_patterns': [self._serialize_candlestick_pattern(pattern) for pattern in candlestick_patterns],
            'visual_markers': visual_markers,
            'ml_features': ml_features,
            'total_factors': len(all_factors)
        })
        
        return results
    
    def _serialize_confluence_zone(self, zone: ConfluenceZone) -> Dict:
        """Serialize confluence zone for JSON response."""
        return {
            'price_level': zone.price_level,
            'timestamp': zone.timestamp.isoformat(),
            'total_score': zone.total_score,
            'weighted_score': zone.weighted_score,
            'strength': zone.strength.value,
            'direction': zone.direction,
            'factors': [
                {
                    'type': factor.factor_type.value,
                    'value': factor.value,
                    'weight': factor.weight,
                    'confidence': factor.confidence,
                    'description': factor.description
                } for factor in zone.factors
            ]
        }
    
    def _serialize_candlestick_pattern(self, pattern: CandlestickPattern) -> Dict:
        """Serialize candlestick pattern for JSON response."""
        return {
            'pattern_type': pattern.pattern_type,
            'timestamp': pattern.timestamp.isoformat(),
            'price': pattern.price,
            'reliability': pattern.reliability,
            'direction': pattern.direction,
            'strength': pattern.strength,
            'confirmation': pattern.confirmation
        }
    
    def reset(self):
        """Reset engine state for new analysis."""
        self.confluence_zones.clear()
        self.individual_factors.clear()
        self.candlestick_patterns.clear()