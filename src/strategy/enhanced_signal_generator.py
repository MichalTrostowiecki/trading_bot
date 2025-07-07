"""
Enhanced Signal Generator with Bar Pattern Confirmation
Transforms basic Fibonacci touches into professional entry signals with price action confirmation.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .trading_types import FibonacciLevel, Swing, TradingSignal
from ..analysis.confluence_engine import ConfluenceEngine, CandlestickPattern, ConfluenceFactorType

logger = logging.getLogger(__name__)

class SignalQuality(Enum):
    """Signal quality levels based on confluence score."""
    WEAK = "weak"           # 0-40%: Skip these trades
    MODERATE = "moderate"   # 40-70%: Acceptable trades
    STRONG = "strong"       # 70-100%: High-quality trades

@dataclass
class BarPatternConfirmation:
    """Bar pattern confirmation for entry signals."""
    pattern_type: str       # e.g., "bullish_engulfing", "hammer", "pin_bar"
    strength: str          # "weak", "moderate", "strong"
    reliability: float     # 0.0 to 1.0
    direction: str         # "bullish", "bearish", "neutral"
    description: str       # Human-readable description
    
@dataclass
class SignalConfluence:
    """Confluence factors for signal quality scoring."""
    fibonacci_score: float      # Quality of Fibonacci level (0-30 points)
    pattern_score: float        # Bar pattern strength (0-35 points)
    volume_score: float         # Volume confirmation (0-20 points)
    swing_score: float          # Swing structure quality (0-15 points)
    total_score: float          # Combined score (0-100)
    quality: SignalQuality      # Overall signal quality
    factors: List[str]          # List of supporting factors

@dataclass
class EnhancedTradingSignal:
    """Enhanced trading signal with pattern confirmation and quality scoring."""
    # Basic signal info
    timestamp: pd.Timestamp
    signal_type: str            # 'buy' or 'sell'
    price: float
    
    # Fibonacci context
    fibonacci_level: float      # e.g., 0.618
    fibonacci_price: float      # Actual Fibonacci price level
    
    # Pattern confirmation
    confirmation_pattern: BarPatternConfirmation
    
    # Quality assessment
    confluence: SignalConfluence
    
    # Risk management
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    # Additional context
    swing_direction: str
    swing_strength: float
    market_bias: str

class EnhancedSignalGenerator:
    """
    Enhanced signal generator that combines Fibonacci levels with bar pattern confirmation
    to create high-quality entry signals.
    """
    
    def __init__(self):
        self.confluence_engine = ConfluenceEngine()
        
        # Signal quality thresholds
        self.quality_thresholds = {
            SignalQuality.WEAK: 40,
            SignalQuality.MODERATE: 70,
            SignalQuality.STRONG: 100
        }
        
        # Fibonacci level weights (higher = more important)
        self.fibonacci_weights = {
            0.236: 15,  # Weak level
            0.382: 25,  # Good level
            0.500: 20,  # Psychological level
            0.618: 30,  # Golden ratio - strongest
            0.786: 20   # Deep retracement
        }
        
        # Pattern strength multipliers
        self.pattern_multipliers = {
            "strong": 1.0,
            "moderate": 0.7,
            "weak": 0.4
        }
    
    def generate_enhanced_signal(self, 
                                df: pd.DataFrame, 
                                current_index: int,
                                fib_level: FibonacciLevel, 
                                swing: Swing,
                                market_bias: str = "neutral") -> Optional[EnhancedTradingSignal]:
        """
        Generate enhanced trading signal with pattern confirmation and quality scoring.
        
        Args:
            df: Price data DataFrame
            current_index: Current bar index
            fib_level: Fibonacci level that was touched
            swing: Recent swing context
            market_bias: Overall market direction
            
        Returns:
            Enhanced trading signal or None if quality too low
        """
        if current_index < 3:  # Need at least 3 bars for pattern detection
            return None
            
        current_bar = df.iloc[current_index]
        
        # Step 1: Validate Fibonacci touch
        if not self._validate_fibonacci_touch(current_bar, fib_level):
            return None
        
        # Step 2: Detect and validate bar pattern confirmation
        pattern_confirmation = self._detect_confirmation_pattern(df, current_index, swing.direction)
        if not pattern_confirmation:
            return None
        
        # Step 3: Calculate signal confluence and quality
        confluence = self._calculate_signal_confluence(
            df, current_index, fib_level, pattern_confirmation, swing
        )
        
        # Step 4: Quality filter - skip low quality signals
        if confluence.quality == SignalQuality.WEAK:
            logger.debug(f"Skipping weak signal (score: {confluence.total_score:.1f})")
            return None
        
        # Step 5: Determine signal direction
        signal_type = self._determine_signal_direction(swing.direction, pattern_confirmation.direction)
        if not signal_type:
            return None
        
        # Step 6: Calculate risk management levels
        stop_loss, take_profit, risk_reward = self._calculate_risk_levels(
            current_bar['close'], signal_type, fib_level, swing
        )
        
        # Step 7: Create enhanced signal
        enhanced_signal = EnhancedTradingSignal(
            timestamp=current_bar.name,
            signal_type=signal_type,
            price=current_bar['close'],
            fibonacci_level=fib_level.level,
            fibonacci_price=fib_level.price,
            confirmation_pattern=pattern_confirmation,
            confluence=confluence,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            swing_direction=swing.direction,
            swing_strength=swing.points,
            market_bias=market_bias
        )
        
        logger.info(f"Generated enhanced {signal_type} signal at {fib_level.level:.1%} "
                   f"with {confluence.quality.value} quality (score: {confluence.total_score:.1f})")
        
        return enhanced_signal
    
    def _validate_fibonacci_touch(self, current_bar: pd.Series, fib_level: FibonacciLevel) -> bool:
        """Validate that price actually touched the Fibonacci level properly."""
        current_high = current_bar['high']
        current_low = current_bar['low']
        fib_price = fib_level.price
        
        # Check if price touched the level (with small tolerance)
        tolerance = abs(current_high - current_low) * 0.1  # 10% of bar range
        return (current_low - tolerance) <= fib_price <= (current_high + tolerance)
    
    def _detect_confirmation_pattern(self, 
                                   df: pd.DataFrame, 
                                   current_index: int, 
                                   expected_direction: str) -> Optional[BarPatternConfirmation]:
        """
        Detect bar pattern confirmation that aligns with expected trade direction.
        
        Args:
            df: Price data
            current_index: Current bar index
            expected_direction: Expected trade direction ('up' or 'down')
            
        Returns:
            Bar pattern confirmation or None
        """
        # Get candlestick patterns from confluence engine
        patterns = self.confluence_engine.detect_candlestick_patterns(df, current_index)
        
        if not patterns:
            return None
        
        # Find patterns that confirm the expected direction
        confirming_patterns = []
        
        for pattern in patterns:
            pattern_direction = self._get_pattern_direction(pattern.pattern_type)
            
            # Check if pattern direction aligns with expected trade direction
            if self._patterns_align(expected_direction, pattern_direction):
                confirming_patterns.append(pattern)
        
        if not confirming_patterns:
            return None
        
        # Use the strongest confirming pattern
        best_pattern = max(confirming_patterns, key=lambda p: p.reliability)
        
        return BarPatternConfirmation(
            pattern_type=best_pattern.pattern_type,
            strength=best_pattern.strength,
            reliability=best_pattern.reliability,
            direction=best_pattern.direction,
            description=f"{best_pattern.pattern_type.title()} pattern ({best_pattern.strength} strength)"
        )
    
    def _get_pattern_direction(self, pattern_type: str) -> str:
        """Get the directional bias of a candlestick pattern."""
        bullish_patterns = ["hammer", "bullish_engulfing", "bullish_pin_bar"]
        bearish_patterns = ["shooting_star", "bearish_engulfing", "bearish_pin_bar"]
        
        if any(p in pattern_type.lower() for p in bullish_patterns):
            return "bullish"
        elif any(p in pattern_type.lower() for p in bearish_patterns):
            return "bearish"
        else:
            return "neutral"
    
    def _patterns_align(self, swing_direction: str, pattern_direction: str) -> bool:
        """Check if swing direction and pattern direction align for continuation trade."""
        if swing_direction == "up" and pattern_direction == "bullish":
            return True
        elif swing_direction == "down" and pattern_direction == "bearish":
            return True
        return False
    
    def _calculate_signal_confluence(self, 
                                   df: pd.DataFrame,
                                   current_index: int,
                                   fib_level: FibonacciLevel,
                                   pattern: BarPatternConfirmation,
                                   swing: Swing) -> SignalConfluence:
        """Calculate confluence score and quality assessment."""
        
        # 1. Fibonacci Level Score (0-30 points)
        fibonacci_score = self.fibonacci_weights.get(fib_level.level, 15)
        
        # 2. Pattern Score (0-35 points)
        base_pattern_score = 35
        pattern_multiplier = self.pattern_multipliers.get(pattern.strength, 0.4)
        pattern_score = base_pattern_score * pattern_multiplier * pattern.reliability
        
        # 3. Volume Score (0-20 points)
        volume_score = self._calculate_volume_score(df, current_index)
        
        # 4. Swing Quality Score (0-15 points)
        swing_score = self._calculate_swing_score(swing)
        
        # Total score (0-100)
        total_score = fibonacci_score + pattern_score + volume_score + swing_score
        
        # Determine quality
        if total_score >= self.quality_thresholds[SignalQuality.STRONG]:
            quality = SignalQuality.STRONG
        elif total_score >= self.quality_thresholds[SignalQuality.MODERATE]:
            quality = SignalQuality.MODERATE
        else:
            quality = SignalQuality.WEAK
        
        # Build factor list
        factors = []
        if fibonacci_score > 20:
            factors.append(f"Key Fibonacci level ({fib_level.level:.1%})")
        if pattern_score > 20:
            factors.append(f"{pattern.pattern_type} pattern")
        if volume_score > 15:
            factors.append("High volume confirmation")
        if swing_score > 10:
            factors.append("Strong swing structure")
        
        return SignalConfluence(
            fibonacci_score=fibonacci_score,
            pattern_score=pattern_score,
            volume_score=volume_score,
            swing_score=swing_score,
            total_score=total_score,
            quality=quality,
            factors=factors
        )
    
    def _calculate_volume_score(self, df: pd.DataFrame, current_index: int) -> float:
        """Calculate volume confirmation score."""
        if 'volume' not in df.columns:
            return 10  # Default moderate score if no volume data
        
        current_volume = df.iloc[current_index]['volume']
        
        # Calculate average volume over last 20 bars
        start_idx = max(0, current_index - 20)
        avg_volume = df.iloc[start_idx:current_index]['volume'].mean()
        
        if avg_volume == 0:
            return 10
        
        # Volume ratio
        volume_ratio = current_volume / avg_volume
        
        # Score based on volume ratio
        if volume_ratio >= 2.0:      # Very high volume
            return 20
        elif volume_ratio >= 1.5:   # High volume
            return 15
        elif volume_ratio >= 1.2:   # Above average
            return 12
        elif volume_ratio >= 0.8:   # Normal volume
            return 8
        else:                        # Low volume
            return 3
    
    def _calculate_swing_score(self, swing: Swing) -> float:
        """Calculate swing quality score."""
        # Base score for having a swing
        score = 5
        
        # Bonus for dominant swing
        if swing.is_dominant:
            score += 5
        
        # Bonus for significant swing (relative to average)
        if swing.points > 100:  # Adjust threshold based on instrument
            score += 5
        
        return min(score, 15)  # Cap at 15 points
    
    def _determine_signal_direction(self, swing_direction: str, pattern_direction: str) -> Optional[str]:
        """Determine final signal direction based on swing and pattern."""
        # For continuation strategy, trade in direction of swing
        if swing_direction == "up" and pattern_direction == "bullish":
            return "buy"
        elif swing_direction == "down" and pattern_direction == "bearish":
            return "sell"
        return None
    
    def _calculate_risk_levels(self, 
                             entry_price: float, 
                             signal_type: str, 
                             fib_level: FibonacciLevel,
                             swing: Swing) -> Tuple[float, float, float]:
        """Calculate stop loss and take profit levels."""
        
        # Use swing-based stops
        if signal_type == "buy":
            # Stop below swing low
            stop_loss = swing.start_fractal.price - (swing.points * 0.1)  # 10% buffer
            # Target: 2x risk
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * 2.0)
        else:  # sell
            # Stop above swing high
            stop_loss = swing.start_fractal.price + (swing.points * 0.1)  # 10% buffer
            # Target: 2x risk
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * 2.0)
        
        # Calculate risk-reward ratio
        if signal_type == "buy":
            risk_amount = entry_price - stop_loss
            reward_amount = take_profit - entry_price
        else:
            risk_amount = stop_loss - entry_price
            reward_amount = entry_price - take_profit
        
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        return stop_loss, take_profit, risk_reward_ratio