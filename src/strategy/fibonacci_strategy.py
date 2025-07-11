"""
Fibonacci Retracement Trading Strategy
Implements fractal detection, swing analysis, and Fibonacci-based entry signals.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# Import confluence engine
from ..analysis.confluence_engine import ConfluenceEngine, ConfluenceZone, CandlestickPattern

# Import enhanced signal generator
from .enhanced_signal_generator import EnhancedSignalGenerator, EnhancedTradingSignal

# Import signal performance tracker
from ..analysis.signal_performance import SignalPerformanceTracker

logger = logging.getLogger(__name__)

# Import shared data types
from .trading_types import Fractal, Swing, FibonacciLevel, TradingSignal, ABCWave, ABCPattern

class FibonacciStrategy:
    """
    Fibonacci Retracement Continuation Strategy
    
    Strategy Logic:
    1. Detect fractals (5-bar highs and lows)
    2. Identify swings between fractals
    3. Calculate Fibonacci retracement levels
    4. Generate signals when price retraces to key levels (38.2%, 50%, 61.8%)
    5. Trade in direction of dominant swing for continuation
    """
    
    def __init__(self, 
                 fractal_period: int = 5,
                 min_swing_points: float = 50.0,
                 fibonacci_levels: List[float] = None,
                 risk_reward_ratio: float = 2.0,
                 lookback_candles: int = 140,
                 enable_confluence_analysis: bool = True):
        """
        Initialize Fibonacci Strategy.
        
        Args:
            fractal_period: Number of bars to look back/forward for fractal detection
            min_swing_points: Minimum price movement to consider a valid swing
            fibonacci_levels: Fibonacci retracement levels to monitor
            risk_reward_ratio: Risk/reward ratio for trade management
            lookback_candles: Number of candles to look back for swing analysis
        """
        self.fractal_period = fractal_period
        self.min_swing_points = min_swing_points
        self.fibonacci_levels = fibonacci_levels or [0.236, 0.382, 0.500, 0.618, 0.786]
        self.lookback_candles = lookback_candles
        self.risk_reward_ratio = risk_reward_ratio
        
        # Strategy state
        self.fractals: List[Fractal] = []
        self.swings: List[Swing] = []
        self.fibonacci_zones: List[FibonacciLevel] = []
        self.signals: List[TradingSignal] = []
        self.abc_patterns: List[ABCPattern] = []
        
        # Current analysis state
        self.current_bar = 0
        self.dominant_trend = None  # 'up' or 'down'
        self.current_dominant_swing = None  # Track current dominant swing for invalidation
        
        # Confluence analysis engine
        self.enable_confluence_analysis = enable_confluence_analysis
        self.confluence_engine = ConfluenceEngine() if enable_confluence_analysis else None
        self.confluence_zones: List[ConfluenceZone] = []
        self.candlestick_patterns: List[CandlestickPattern] = []
        
        # Enhanced signal generator with pattern confirmation
        self.enhanced_signal_generator = EnhancedSignalGenerator()
        self.enhanced_signals: List[EnhancedTradingSignal] = []
        
        # Signal performance tracking for ML/AI development
        self.signal_performance_tracker = SignalPerformanceTracker()
        
    def detect_fractals(self, df: pd.DataFrame, current_index: int) -> Optional[Fractal]:
        """
        Detect fractal at specified index using 5-bar pattern.
        
        A fractal high: current high > 2 previous highs AND current high > 2 following highs
        A fractal low: current low < 2 previous lows AND current low < 2 following lows
        
        Args:
            df: OHLCV dataframe
            current_index: Index to check for fractal
            
        Returns:
            Fractal object if found, None otherwise
        """
        if current_index < self.fractal_period or current_index >= len(df) - self.fractal_period:
            return None
            
        current_high = df.iloc[current_index]['high']
        current_low = df.iloc[current_index]['low']
        
        # Check for fractal high
        is_fractal_high = True
        for i in range(1, self.fractal_period + 1):
            # Check previous bars
            if df.iloc[current_index - i]['high'] >= current_high:
                is_fractal_high = False
                break
            # Check following bars
            if df.iloc[current_index + i]['high'] >= current_high:
                is_fractal_high = False
                break
                
        # Check for fractal low
        is_fractal_low = True
        for i in range(1, self.fractal_period + 1):
            # Check previous bars
            if df.iloc[current_index - i]['low'] <= current_low:
                is_fractal_low = False
                break
            # Check following bars
            if df.iloc[current_index + i]['low'] <= current_low:
                is_fractal_low = False
                break
        
        # Create fractal object
        if is_fractal_high:
            return Fractal(
                timestamp=df.index[current_index],
                price=current_high,
                fractal_type='high',
                bar_index=current_index
            )
        elif is_fractal_low:
            return Fractal(
                timestamp=df.index[current_index],
                price=current_low,
                fractal_type='low',
                bar_index=current_index
            )
            
        return None
    
    def limit_to_two_swings(self, recent_swings: List[Swing]) -> None:
        """
        Limit display to maximum 2 swings: 1 dominant + 1 most recent opposite.
        This creates clean Elliott Wave market structure visualization.
        """
        if not self.current_dominant_swing:
            return
            
        # Find most recent swing in opposite direction to dominant
        dominant_direction = self.current_dominant_swing.direction
        opposite_direction = 'down' if dominant_direction == 'up' else 'up'
        
        most_recent_opposite = None
        for swing in reversed(recent_swings):
            if swing.direction == opposite_direction and swing != self.current_dominant_swing:
                most_recent_opposite = swing
                break
        
        # Mark swings for removal (those not in our clean 2-swing display)
        swings_to_keep = [self.current_dominant_swing]
        if most_recent_opposite:
            swings_to_keep.append(most_recent_opposite)
        
        # Remove excess swings from the main list - keep swings that are in our display OR within lookback window
        lookback_start = max(0, self.current_bar - self.lookback_candles) if hasattr(self, 'current_bar') and self.current_bar is not None else 0
        self.swings = [swing for swing in self.swings if swing in swings_to_keep or swing.end_fractal.bar_index >= lookback_start]
        
        logger.debug(f"📊 CLEAN DISPLAY: Keeping {len(swings_to_keep)} swings (1 dominant + {len(swings_to_keep)-1} opposite)")
    
    def identify_swing(self, new_fractal: Fractal) -> Optional[Swing]:
        """
        Identify swing when new fractal is detected.
        
        🚨 CRITICAL FIX: This method now only checks if we need to extend/update the dominant swing
        instead of creating multiple swings. All swing creation is handled by recalculate_swings_for_lookback_window.
        """
        if not self.fractals:
            return None

        # Find absolute extremes within lookback period
        if hasattr(self, 'current_bar') and self.current_bar is not None:
            lookback_start = max(0, self.current_bar - self.lookback_candles)
        else:
            lookback_start = 0

        # Check all fractals (including new one) within the lookback window
        all_fractals = self.fractals + [new_fractal]
        fractals_in_window = [f for f in all_fractals if f.bar_index >= lookback_start]

        if len(fractals_in_window) < 2:
            return None

        # Find absolute extremes
        highest_high_fractal = None
        lowest_low_fractal = None
        highest_price = float('-inf')
        lowest_price = float('inf')

        for fractal in fractals_in_window:
            if fractal.fractal_type == 'high' and fractal.price > highest_price:
                highest_price = fractal.price
                highest_high_fractal = fractal
            elif fractal.fractal_type == 'low' and fractal.price < lowest_price:
                lowest_price = fractal.price
                lowest_low_fractal = fractal

        if not highest_high_fractal or not lowest_low_fractal:
            return None

        # Check if current dominant swing needs to be updated/extended
        current_swing = self.current_dominant_swing
        
        # Determine what the swing should be (connecting absolute extremes)
        if highest_high_fractal.bar_index < lowest_low_fractal.bar_index:
            # High came first, then low = DOWN swing
            ideal_direction = 'down'
            ideal_start = highest_high_fractal
            ideal_end = lowest_low_fractal
        else:
            # Low came first, then high = UP swing
            ideal_direction = 'up'
            ideal_start = lowest_low_fractal
            ideal_end = highest_high_fractal

        ideal_points = abs(ideal_end.price - ideal_start.price)

        # Check minimum swing criteria
        if ideal_points < self.min_swing_points:
            logger.debug(f"⚠️ Ideal swing only {ideal_points:.1f} pts, below minimum {self.min_swing_points}")
            return None

        # If no current swing, or current swing doesn't match the ideal swing, create new one
        if (not current_swing or 
            current_swing.start_fractal.bar_index != ideal_start.bar_index or
            current_swing.end_fractal.bar_index != ideal_end.bar_index):
            
            swing = Swing(
                start_fractal=ideal_start,
                end_fractal=ideal_end,
                direction=ideal_direction,
                points=ideal_points,
                bars=abs(ideal_end.bar_index - ideal_start.bar_index),
                is_dominant=True
            )

            logger.debug(f"🔥 NEW/EXTENDED {ideal_direction} swing: {ideal_points:.1f} pts connecting absolute extremes")
            logger.debug(f"   Start: {ideal_start.price:.2f} at bar {ideal_start.bar_index}")
            logger.debug(f"   End: {ideal_end.price:.2f} at bar {ideal_end.bar_index}")
            
            return swing
        
        return None
    
    def is_dominant_swing_invalidated(self, df: pd.DataFrame, current_index: int) -> bool:
        """
        Check if current dominant swing has been invalidated by price action.
        
        ELLIOTT WAVE INVALIDATION RULES:
        - DOWN dominant swing: invalidated if price breaks ABOVE the swing's HIGH (end fractal)
        - UP dominant swing: invalidated if price breaks BELOW the swing's LOW (end fractal)
        
        This preserves market structure until the swing extreme is genuinely broken.
        """
        if not self.current_dominant_swing or current_index >= len(df):
            return False
            
        current_bar = df.iloc[current_index]
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        if self.current_dominant_swing.direction == 'down':
            # DOWN swing invalidated if price breaks ABOVE its starting high
            swing_high = self.current_dominant_swing.start_fractal.price
            if current_high > swing_high:
                logger.debug(f"🔄 DOWN dominant swing INVALIDATED: price {current_high:.2f} broke above swing start {swing_high:.2f}")
                return True
        elif self.current_dominant_swing.direction == 'up':
            # UP swing invalidated if price breaks BELOW its starting low
            swing_low = self.current_dominant_swing.start_fractal.price
            if current_low < swing_low:
                logger.debug(f"🔄 UP dominant swing INVALIDATED: price {current_low:.2f} broke below swing start {swing_low:.2f}")
                return True
                
        return False
    
    def update_dominant_swing(self):
        """
        Update dominant swing status using ELLIOTT WAVE + TIME-BASED logic.

        LOGIC:
        1. Find swings that are relevant within current lookback window
        2. Prioritize swings that start/end within the window (more recent)
        3. Choose the most significant swing that represents current market bias
        """
        if not self.swings:
            return

        # Reset all swings to non-dominant initially
        for swing in self.swings:
            swing.is_dominant = False

        # Filter swings within lookback period
        if hasattr(self, 'current_bar') and self.current_bar is not None:
            lookback_start = max(0, self.current_bar - self.lookback_candles)

            # Categorize swings by relevance to current window
            fully_within_swings = []  # Both start and end within window
            partially_within_swings = []  # Only end within window

            for swing in self.swings:
                if swing.start_fractal.bar_index >= lookback_start and swing.end_fractal.bar_index >= lookback_start:
                    fully_within_swings.append(swing)
                elif swing.end_fractal.bar_index >= lookback_start:
                    partially_within_swings.append(swing)
        else:
            fully_within_swings = self.swings
            partially_within_swings = []

        # 🚨 SIMPLIFIED DOMINANCE LOGIC: Always choose the largest swing by magnitude
        # This ensures the most visually obvious swing becomes dominant
        # Complex Elliott Wave logic was causing wrong swing selection

        all_relevant_swings = fully_within_swings + partially_within_swings
        if not all_relevant_swings:
            return

        # 🚨 CRITICAL DEBUG: Log all relevant swings before dominance selection
        logger.debug(f"🔍 DOMINANCE SELECTION: Found {len(all_relevant_swings)} relevant swings")
        for i, swing in enumerate(all_relevant_swings):
            relevance = "fully within" if swing in fully_within_swings else "partially within"
            logger.debug(f"   {i+1}. {swing.direction.upper()} swing: {swing.points:.1f} pts ({relevance})")
            logger.debug(f"      From {swing.start_fractal.price:.2f} to {swing.end_fractal.price:.2f}")

        # SIMPLIFIED: Just pick the largest swing by points (most obvious to user)
        dominant_swing = max(all_relevant_swings, key=lambda s: s.points)
        logger.debug(f"🎯 SIMPLIFIED SELECTION: Chose largest swing by magnitude ({dominant_swing.points:.1f} pts)")

        # Skip the complex extreme-connecting logic for now to fix the immediate issue
        # TODO: Re-implement Elliott Wave logic after basic dominance works correctly

        # 🚨 CRITICAL DEBUG: Log the selected dominant swing
        logger.debug(f"🎯 SELECTED DOMINANT: {dominant_swing.direction.upper()} swing ({dominant_swing.points:.1f} pts)")
        logger.debug(f"   From {dominant_swing.start_fractal.price:.2f} to {dominant_swing.end_fractal.price:.2f}")

        # Mark as dominant
        dominant_swing.is_dominant = True
        self.current_dominant_swing = dominant_swing
        logger.debug(f"🔒 DOMINANT SWING SET: {dominant_swing.direction} from {dominant_swing.start_fractal.price:.2f} to {dominant_swing.end_fractal.price:.2f}")
        logger.debug(f"   Swing relevance: {'fully within' if dominant_swing in fully_within_swings else 'partially within'} lookback window")

        # 🚨 CRITICAL: Recalculate Fibonacci levels for the new dominant swing
        self.fibonacci_zones = self.calculate_fibonacci_levels(dominant_swing)
        logger.debug(f"📐 FIBONACCI RECALCULATED: {len(self.fibonacci_zones)} levels for new dominant swing")

        # 🚨 CRITICAL DEBUG: Log all swings and their dominance status
        logger.debug(f"📊 ALL SWINGS AFTER DOMINANCE UPDATE:")
        for i, swing in enumerate(self.swings):
            status = "DOMINANT" if swing.is_dominant else "context"
            logger.debug(f"   {i+1}. {swing.direction.upper()} swing: {swing.points:.1f} pts - {status}")
            logger.debug(f"      From {swing.start_fractal.price:.2f} to {swing.end_fractal.price:.2f}")

        # Verify that only one swing is marked as dominant
        dominant_count = sum(1 for swing in self.swings if swing.is_dominant)
        if dominant_count != 1:
            logger.warning(f"⚠️ DOMINANCE ERROR: {dominant_count} swings marked as dominant (should be 1)")

        # 📊 CLEAN DISPLAY: Keep only dominant + 1 most recent opposite swing
        all_relevant_swings = fully_within_swings + partially_within_swings
        self.limit_to_two_swings(all_relevant_swings)

    def recalculate_swings_for_lookback_window(self):
        """
        Recalculate swings from scratch when lookback window moves.

        🚨 CRITICAL FIX: Focus on current 140-candle window and invalidate old swings
        when new extremes are found within this window.
        """
        if not self.fractals or not hasattr(self, 'current_bar') or self.current_bar is None:
            return

        lookback_start = max(0, self.current_bar - self.lookback_candles)
        logger.debug(f"🔄 LOOKBACK RECALC: Current window [{lookback_start} to {self.current_bar}]")

        # Find all fractals within the current 140-candle lookback window
        fractals_in_window = [f for f in self.fractals if f.bar_index >= lookback_start]

        if len(fractals_in_window) < 2:
            logger.debug(f"⚠️ Not enough fractals in lookback window ({len(fractals_in_window)}), clearing swings")
            self.swings.clear()
            self.current_dominant_swing = None
            return

        # Find absolute extremes within the current 140-candle window
        highest_high_fractal = None
        lowest_low_fractal = None
        highest_price = float('-inf')
        lowest_price = float('inf')

        for fractal in fractals_in_window:
            if fractal.fractal_type == 'high' and fractal.price > highest_price:
                highest_price = fractal.price
                highest_high_fractal = fractal
            elif fractal.fractal_type == 'low' and fractal.price < lowest_price:
                lowest_price = fractal.price
                lowest_low_fractal = fractal

        if not highest_high_fractal or not lowest_low_fractal:
            logger.debug(f"⚠️ Missing extreme fractals in current window")
            self.swings.clear()
            self.current_dominant_swing = None
            return

        # 🚨 CRITICAL FIX: Check if current swing is invalidated by new extremes in current window
        if self.current_dominant_swing:
            swing_invalidated = False
            invalidation_reason = ""

            if self.current_dominant_swing.direction == 'up':
                # UP swing: invalidated if we find a lower low than swing start within current window
                if lowest_low_fractal.price < self.current_dominant_swing.start_fractal.price:
                    swing_invalidated = True
                    invalidation_reason = f"New lower low {lowest_low_fractal.price:.2f} < swing start {self.current_dominant_swing.start_fractal.price:.2f}"
            else:
                # DOWN swing: invalidated if we find a higher high than swing start within current window
                if highest_high_fractal.price > self.current_dominant_swing.start_fractal.price:
                    swing_invalidated = True
                    invalidation_reason = f"New higher high {highest_high_fractal.price:.2f} > swing start {self.current_dominant_swing.start_fractal.price:.2f}"

            # Also invalidate if swing is completely outside current window
            if (self.current_dominant_swing.start_fractal.bar_index < lookback_start and
                self.current_dominant_swing.end_fractal.bar_index < lookback_start):
                swing_invalidated = True
                invalidation_reason = f"Swing completely outside current window (ends at bar {self.current_dominant_swing.end_fractal.bar_index})"

            if swing_invalidated:
                logger.debug(f"🔥 SWING INVALIDATED: {invalidation_reason}")
            else:
                logger.debug(f"✅ Current swing still VALID within current window")
                return

        # 🚨 CRITICAL FIX: Clear ALL existing swings and rebuild from scratch
        # This prevents accumulation of outdated swings
        self.swings.clear()
        self.current_dominant_swing = None
        logger.debug(f"🧹 CLEARED all existing swings for fresh recalculation")

        # Create THE swing connecting absolute extremes within current window
        # Determine direction based on which extreme comes first chronologically
        if highest_high_fractal.bar_index < lowest_low_fractal.bar_index:
            # High comes first, then low = DOWN swing
            start_fractal = highest_high_fractal
            end_fractal = lowest_low_fractal
            direction = 'down'
        else:
            # Low comes first, then high = UP swing
            start_fractal = lowest_low_fractal
            end_fractal = highest_high_fractal
            direction = 'up'

        points = abs(end_fractal.price - start_fractal.price)
        bars = abs(end_fractal.bar_index - start_fractal.bar_index)

        # Only create swing if it meets minimum criteria
        if points >= self.min_swing_points:
            # Create the ONE dominant swing connecting absolute extremes within current window
            dominant_swing = Swing(
                start_fractal=start_fractal,
                end_fractal=end_fractal,
                direction=direction,
                points=points,
                bars=bars,
                is_dominant=True  # Mark as dominant immediately
            )

            self.swings.append(dominant_swing)
            self.current_dominant_swing = dominant_swing

            logger.debug(f"🔥 LOOKBACK RECALC: Created DOMINANT {direction} swing in current window")
            logger.debug(f"   Start: {start_fractal.price:.2f} at bar {start_fractal.bar_index}")
            logger.debug(f"   End: {end_fractal.price:.2f} at bar {end_fractal.bar_index}")
            logger.debug(f"   Points: {points:.1f}")

            # Calculate new Fibonacci levels for the new dominant swing
            self.fibonacci_zones = self.calculate_fibonacci_levels(dominant_swing)
            logger.debug(f"📐 FIBONACCI RECALCULATED: {len(self.fibonacci_zones)} levels for new dominant swing")
        else:
            logger.debug(f"⚠️ Extreme swing only {points:.1f} pts, below minimum {self.min_swing_points}")
            self.current_dominant_swing = None
    
    def get_dominant_swing(self) -> Optional[Swing]:
        """Get the current dominant swing."""
        for swing in self.swings:
            if swing.is_dominant:
                return swing
        return None
    
    def get_market_bias(self) -> Dict[str, Any]:
        """
        Get current market bias based on dominant swing.
        
        Returns:
            Dictionary with bias direction and trading recommendation
        """
        dominant_swing = self.get_dominant_swing()
        
        if not dominant_swing:
            return {
                'bias': 'NEUTRAL',
                'direction': 'NEUTRAL',
                'trading_direction': 'No clear bias',
                'points': 0,
                'recommendation': 'Wait for clear swing structure'
            }
        
        if dominant_swing.direction == 'up':
            return {
                'bias': 'BULLISH',
                'direction': 'UP',
                'trading_direction': 'LOOK FOR BUY OPPORTUNITIES',
                'points': dominant_swing.points,
                'recommendation': 'Wait for retracements to Fibonacci levels for LONG entries'
            }
        else:
            return {
                'bias': 'BEARISH', 
                'direction': 'DOWN',
                'trading_direction': 'LOOK FOR SELL OPPORTUNITIES',
                'points': dominant_swing.points,
                'recommendation': 'Wait for retracements to Fibonacci levels for SHORT entries'
            }
    
    def calculate_fibonacci_levels(self, swing: Swing) -> List[FibonacciLevel]:
        """
        Calculate Fibonacci retracement levels for a swing.

        For UP swing: 0% = swing low, 100% = swing high, retracements go down from high
        For DOWN swing: 0% = swing high, 100% = swing low, retracements go up from low
        """
        swing_high = max(swing.start_fractal.price, swing.end_fractal.price)
        swing_low = min(swing.start_fractal.price, swing.end_fractal.price)
        swing_range = swing_high - swing_low

        fib_levels = []
        for level in self.fibonacci_levels:
            if swing.direction == 'up':
                # For UP swing: retracement levels go DOWN from the swing high
                # 0% = high, 23.6% = high - 23.6% of range, etc.
                price = swing_high - (swing_range * level)
            else:
                # For DOWN swing: retracement levels go UP from the swing low
                # 0% = low, 23.6% = low + 23.6% of range, etc.
                price = swing_low + (swing_range * level)

            fib_levels.append(FibonacciLevel(
                level=level,
                price=price,
                hit=False
            ))

        return fib_levels
    
    def generate_signal(self, df: pd.DataFrame, current_index: int, 
                       fib_level: FibonacciLevel, swing: Swing) -> Optional[TradingSignal]:
        """
        Generate trading signal when price hits Fibonacci level.
        """
        current_bar = df.iloc[current_index]
        current_price = current_bar['close']
        
        # Determine signal direction (trade in direction of swing for continuation)
        signal_type = 'buy' if swing.direction == 'up' else 'sell'
        
        # Calculate stop loss and take profit
        if signal_type == 'buy':
            # For buy signals, stop below recent low
            stop_loss = swing.start_fractal.price if swing.direction == 'up' else swing.end_fractal.price
            stop_loss *= 0.995  # Small buffer
            take_profit = current_price + (abs(current_price - stop_loss) * self.risk_reward_ratio)
        else:
            # For sell signals, stop above recent high
            stop_loss = swing.start_fractal.price if swing.direction == 'down' else swing.end_fractal.price
            stop_loss *= 1.005  # Small buffer
            take_profit = current_price - (abs(stop_loss - current_price) * self.risk_reward_ratio)
        
        # Calculate confidence based on Fibonacci level
        confidence_map = {0.382: 0.7, 0.500: 0.8, 0.618: 0.9}
        confidence = confidence_map.get(fib_level.level, 0.6)
        
        signal = TradingSignal(
            timestamp=df.index[current_index],
            signal_type=signal_type,
            price=current_price,
            fibonacci_level=fib_level.level,
            swing_direction=swing.direction,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return signal
    
    def check_fibonacci_hits(self, df: pd.DataFrame, current_index: int) -> List[TradingSignal]:
        """
        Check if current price hits any active Fibonacci levels.
        """
        if not self.fibonacci_zones or not self.swings:
            return []
            
        current_bar = df.iloc[current_index]
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        new_signals = []
        
        # Get the most recent swing for signal generation
        recent_swing = self.swings[-1]
        
        for fib_level in self.fibonacci_zones:
            if fib_level.hit:
                continue
                
            # Check if price touched this level
            if current_low <= fib_level.price <= current_high:
                fib_level.hit = True
                
                # Generate signal for key levels only
                if fib_level.level in [0.382, 0.500, 0.618]:
                    # Try enhanced signal generation first (with pattern confirmation)
                    enhanced_signal = self.enhanced_signal_generator.generate_enhanced_signal(
                        df, current_index, fib_level, recent_swing, self.get_market_bias()
                    )
                    
                    if enhanced_signal:
                        # Add enhanced signal to separate list for analysis
                        self.enhanced_signals.append(enhanced_signal)
                        
                        # Start tracking this signal for performance analysis
                        signal_dict = {
                            'timestamp': enhanced_signal.timestamp.isoformat(),
                            'signal_type': enhanced_signal.signal_type,
                            'price': enhanced_signal.price,
                            'fibonacci_level': enhanced_signal.fibonacci_level,
                            'pattern_type': enhanced_signal.confirmation_pattern.pattern_type,
                            'pattern_strength': enhanced_signal.confirmation_pattern.strength,
                            'confluence_score': enhanced_signal.confluence.total_score,
                            'quality': enhanced_signal.confluence.quality.value,
                            'stop_loss': enhanced_signal.stop_loss,
                            'take_profit': enhanced_signal.take_profit,
                            'factors': enhanced_signal.confluence.factors
                        }
                        signal_id = self.signal_performance_tracker.track_new_signal(signal_dict)
                        
                        logger.info(f"Enhanced signal generated: {enhanced_signal.signal_type} at "
                                   f"{enhanced_signal.fibonacci_level:.1%} with {enhanced_signal.confluence.quality.value} quality (tracking ID: {signal_id})")
                    
                    # Also generate traditional signal for comparison/fallback
                    traditional_signal = self.generate_signal(df, current_index, fib_level, recent_swing)
                    if traditional_signal:
                        new_signals.append(traditional_signal)
                        
        return new_signals
    
    def process_bar(self, df: pd.DataFrame, current_index: int) -> Dict:
        """
        Process single bar and update strategy state.
        
        Returns:
            Dictionary with current analysis results
        """
        # Validate input data
        if df.empty or current_index >= len(df) or current_index < 0:
            return {
                'bar_index': current_index,
                'timestamp': None,
                'new_fractal': None,
                'new_swing': None,
                'new_signals': [],
                'fibonacci_levels': [],
                'total_fractals': len(self.fractals),
                'total_swings': len(self.swings),
                'total_signals': len(self.signals),
                'market_bias': None
            }

        self.current_bar = current_index
        results = {
            'bar_index': current_index,
            'timestamp': df.index[current_index].isoformat(),
            'new_fractal': None,
            'new_swing': None,
            'new_signals': [],
            'fibonacci_levels': [],
            'total_fractals': len(self.fractals),
            'total_swings': len(self.swings),
            'total_signals': len(self.signals),
            'market_bias': self.get_market_bias()
        }
        
        # 0. Check if current dominant swing has been invalidated by price action
        if self.current_dominant_swing:
            if self.is_dominant_swing_invalidated(df, current_index):
                logger.debug(f"🔄 INVALIDATION TRIGGERED: Dominant {self.current_dominant_swing.direction} swing invalidated, recalculating...")
                self.current_dominant_swing = None  # Clear invalidated swing
                self.update_dominant_swing()  # Recalculate dominance
                results['swing_invalidated'] = True
                results['market_bias'] = self.get_market_bias()  # Update market bias after invalidation

        # 0.5. Check if swing needs recalculation due to lookback window changes OR new extremes
        # Only check this if we haven't already invalidated the swing above
        lookback_start = max(0, current_index - self.lookback_candles)
        should_recalculate = False
        recalc_reason = ""
        
        if self.current_dominant_swing and not results.get('swing_invalidated'):
            # Reason 1: Dominant swing's start fractal is now outside the lookback window
            if self.current_dominant_swing.start_fractal.bar_index < lookback_start:
                should_recalculate = True
                recalc_reason = f"start fractal (bar {self.current_dominant_swing.start_fractal.bar_index}) outside lookback window (starts at bar {lookback_start})"
            
            # Reason 2: Dominant swing's end fractal is now outside the lookback window
            elif self.current_dominant_swing.end_fractal.bar_index < lookback_start:
                should_recalculate = True
                recalc_reason = f"end fractal (bar {self.current_dominant_swing.end_fractal.bar_index}) outside lookback window (starts at bar {lookback_start})"
            
            # 🚨 CRITICAL FIX: Reason 3: New extremes within lookback window that create bigger swing
            elif len(self.fractals) > 0:
                # Find current extremes within lookback window
                fractals_in_window = [f for f in self.fractals if f.bar_index >= lookback_start]
                if len(fractals_in_window) >= 2:
                    # Find absolute extremes
                    highest_high = max([f for f in fractals_in_window if f.fractal_type == 'high'], key=lambda f: f.price, default=None)
                    lowest_low = min([f for f in fractals_in_window if f.fractal_type == 'low'], key=lambda f: f.price, default=None)
                    
                    if highest_high and lowest_low:
                        # Calculate what the swing should be
                        potential_points = abs(highest_high.price - lowest_low.price)
                        current_points = self.current_dominant_swing.points
                        
                        # Check if current swing doesn't connect to absolute extremes
                        current_connects_to_high = (self.current_dominant_swing.start_fractal.bar_index == highest_high.bar_index or 
                                                  self.current_dominant_swing.end_fractal.bar_index == highest_high.bar_index)
                        current_connects_to_low = (self.current_dominant_swing.start_fractal.bar_index == lowest_low.bar_index or 
                                                 self.current_dominant_swing.end_fractal.bar_index == lowest_low.bar_index)
                        
                        if not (current_connects_to_high and current_connects_to_low):
                            should_recalculate = True
                            recalc_reason = f"new extremes found - current swing doesn't connect absolute high ({highest_high.price:.2f}) to absolute low ({lowest_low.price:.2f})"
                        elif potential_points > current_points + 10:  # Allow small tolerance
                            should_recalculate = True
                            recalc_reason = f"bigger swing possible ({potential_points:.1f} pts vs current {current_points:.1f} pts)"
        
        # 🚨 CRITICAL FIX: Reason 4: Check if lookback window has shifted significantly and we need to recalculate
        # This handles cases where new extremes enter the lookback window that should change dominance
        elif not self.current_dominant_swing and len(self.fractals) > 0:
            # If we have no dominant swing but have fractals, try to establish one
            fractals_in_window = [f for f in self.fractals if f.bar_index >= lookback_start]
            if len(fractals_in_window) >= 2:
                should_recalculate = True
                recalc_reason = f"no dominant swing but {len(fractals_in_window)} fractals in lookback window"
        
        # 🚨 CRITICAL FIX: Reason 5: Periodic recalculation to ensure dominance is always based on current lookback window
        # This is the most robust fix - recalculate every N bars to ensure swing dominance is current
        elif self.current_dominant_swing and current_index % 10 == 0:  # Check every 10 bars
            # Quick check: ensure current swing is still the biggest in the lookback window
            fractals_in_window = [f for f in self.fractals if f.bar_index >= lookback_start]
            if len(fractals_in_window) >= 2:
                highest_high = max([f for f in fractals_in_window if f.fractal_type == 'high'], key=lambda f: f.price, default=None)
                lowest_low = min([f for f in fractals_in_window if f.fractal_type == 'low'], key=lambda f: f.price, default=None)
                
                if highest_high and lowest_low:
                    potential_points = abs(highest_high.price - lowest_low.price)
                    current_points = self.current_dominant_swing.points
                    
                    # If we find a significantly bigger swing (>5% larger), recalculate
                    if potential_points > current_points * 1.05:
                        should_recalculate = True
                        recalc_reason = f"periodic check found bigger swing ({potential_points:.1f} vs {current_points:.1f} pts)"
        
        # Trigger recalculation if needed
        if should_recalculate:
            logger.debug(f"🔄 LOOKBACK RECALC TRIGGERED: {recalc_reason}")
            self.current_dominant_swing = None  # Clear current swing
            self.recalculate_swings_for_lookback_window()  # Recalculate from scratch
            results['lookback_recalculation'] = True
            results['market_bias'] = self.get_market_bias()  # Update market bias after recalculation
        
        # 1. Check for new fractal (need future bars, so delay by fractal_period)
        if current_index >= self.fractal_period * 2:
            fractal_check_index = current_index - self.fractal_period
            new_fractal = self.detect_fractals(df, fractal_check_index)
            
            if new_fractal:
                self.fractals.append(new_fractal)
                results['new_fractal'] = {
                    'timestamp': new_fractal.timestamp.isoformat(),
                    'price': new_fractal.price,
                    'fractal_type': new_fractal.fractal_type,
                    'bar_index': new_fractal.bar_index
                }
                
                # 🚨 CRITICAL FIX: ALWAYS force recalculation when new fractal is detected
                # This ensures swing immediately extends to new extremes
                logger.debug(f"🔥 NEW FRACTAL DETECTED: {new_fractal.fractal_type} at {new_fractal.price:.2f}, forcing recalculation")
                self.current_dominant_swing = None  # Clear current swing
                self.recalculate_swings_for_lookback_window()  # Recalculate from scratch
                results['swing_recalculated_for_new_fractal'] = True
                results['market_bias'] = self.get_market_bias()  # Update market bias after recalculation
                
                # Add swing info to results if we have a new dominant swing
                if self.current_dominant_swing:
                    results['new_swing'] = {
                        'start_fractal': {
                            'timestamp': self.current_dominant_swing.start_fractal.timestamp.isoformat(),
                            'price': self.current_dominant_swing.start_fractal.price,
                            'fractal_type': self.current_dominant_swing.start_fractal.fractal_type,
                            'bar_index': self.current_dominant_swing.start_fractal.bar_index
                        },
                        'end_fractal': {
                            'timestamp': self.current_dominant_swing.end_fractal.timestamp.isoformat(),
                            'price': self.current_dominant_swing.end_fractal.price,
                            'fractal_type': self.current_dominant_swing.end_fractal.fractal_type,
                            'bar_index': self.current_dominant_swing.end_fractal.bar_index
                        },
                        'direction': self.current_dominant_swing.direction,
                        'points': self.current_dominant_swing.points,
                        'bars': self.current_dominant_swing.bars,
                        'is_dominant': self.current_dominant_swing.is_dominant
                    }
                    
                    # Calculate Fibonacci levels for the new dominant swing
                    self.fibonacci_zones = self.calculate_fibonacci_levels(self.current_dominant_swing)
                    logger.debug(f"🔍 FIBONACCI SOURCE: Using {self.current_dominant_swing.direction.upper()} swing for fibonacci levels")
                    logger.debug(f"   Swing: {self.current_dominant_swing.start_fractal.price:.2f} -> {self.current_dominant_swing.end_fractal.price:.2f}")
                    logger.debug(f"   Points: {self.current_dominant_swing.points:.1f}")

                    results['fibonacci_levels'] = [
                        {
                            'level': fib.level,
                            'price': fib.price,
                            'hit': fib.hit,
                            'swing_direction': self.current_dominant_swing.direction,
                            'swing_start_price': self.current_dominant_swing.start_fractal.price,
                            'swing_end_price': self.current_dominant_swing.end_fractal.price,
                            'swing_start_time': self.current_dominant_swing.start_fractal.timestamp.isoformat(),
                            'swing_end_time': self.current_dominant_swing.end_fractal.timestamp.isoformat()
                        } for fib in self.fibonacci_zones
                    ]
                else:
                    logger.debug("⚠️ FIBONACCI SOURCE: No dominant swing available after recalculation")
                    results['fibonacci_levels'] = []
        
        # 4. Check for Fibonacci level hits and generate signals
        new_signals = self.check_fibonacci_hits(df, current_index)
        if new_signals and len(new_signals) > 0:
            self.signals.extend(new_signals)
            results['new_signals'] = [
                {
                    'timestamp': signal.timestamp.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'fibonacci_level': signal.fibonacci_level,
                    'swing_direction': signal.swing_direction,
                    'confidence': signal.confidence,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit
                } for signal in new_signals if signal is not None
            ]
        else:
            results['new_signals'] = []
            
        # 4.5. Update signal performance tracking for active signals
        self.update_signal_performance_tracking(df, current_index)
        
        # 5. ABC Pattern Detection (now returns only the best pattern)
        abc_patterns = self.detect_abc_patterns(df, current_index)
        if abc_patterns:
            # We now get only the best pattern, so check if it's new
            best_pattern = abc_patterns[0]
            
            # Check if this is a new pattern (not already stored)
            is_new_pattern = True
            for existing_pattern in self.abc_patterns:
                if (existing_pattern.wave_a.start_timestamp == best_pattern.wave_a.start_timestamp and
                    existing_pattern.wave_c.end_timestamp == best_pattern.wave_c.end_timestamp):
                    is_new_pattern = False
                    break
            
            if is_new_pattern:
                # Store only new patterns to avoid duplicates
                self.abc_patterns.append(best_pattern)
                
                logger.debug(f"🌊 NEW ABC Pattern: {best_pattern.pattern_type} - Wave A: {best_pattern.wave_a.direction} {best_pattern.wave_a.points:.1f}pts, Wave B: {best_pattern.wave_b.direction} {best_pattern.wave_b.points:.1f}pts, Wave C: {best_pattern.wave_c.direction} {best_pattern.wave_c.points:.1f}pts")

                # Send new ABC pattern to frontend
                results['new_abc_pattern'] = {
                    'wave_a': {
                        'start_timestamp': best_pattern.wave_a.start_timestamp.isoformat(),
                        'end_timestamp': best_pattern.wave_a.end_timestamp.isoformat(),
                        'start_price': best_pattern.wave_a.start_price,
                        'end_price': best_pattern.wave_a.end_price,
                        'direction': best_pattern.wave_a.direction,
                        'points': best_pattern.wave_a.points,
                        'bars': best_pattern.wave_a.bars
                    },
                    'wave_b': {
                        'start_timestamp': best_pattern.wave_b.start_timestamp.isoformat(),
                        'end_timestamp': best_pattern.wave_b.end_timestamp.isoformat(),
                        'start_price': best_pattern.wave_b.start_price,
                        'end_price': best_pattern.wave_b.end_price,
                        'direction': best_pattern.wave_b.direction,
                        'points': best_pattern.wave_b.points,
                        'bars': best_pattern.wave_b.bars
                    },
                    'wave_c': {
                        'start_timestamp': best_pattern.wave_c.start_timestamp.isoformat(),
                        'end_timestamp': best_pattern.wave_c.end_timestamp.isoformat(),
                        'start_price': best_pattern.wave_c.start_price,
                        'end_price': best_pattern.wave_c.end_price,
                        'direction': best_pattern.wave_c.direction,
                        'points': best_pattern.wave_c.points,
                        'bars': best_pattern.wave_c.bars
                    },
                    'pattern_type': best_pattern.pattern_type,
                    'is_complete': best_pattern.is_complete,
                    'fibonacci_confluence': best_pattern.fibonacci_confluence,
                    # Add projection levels for incomplete patterns
                    'fe62_target': getattr(best_pattern, 'fe62_target', None),
                    'fe100_target': getattr(best_pattern, 'fe100_target', None),
                    'fe127_target': getattr(best_pattern, 'fe127_target', None)
                }
            else:
                results['new_abc_pattern'] = None
        else:
            results['new_abc_pattern'] = None

        # 6. Confluence Analysis
        if self.enable_confluence_analysis and self.confluence_engine:
            confluence_results = self.confluence_engine.process_bar(
                df=df,
                current_index=current_index,
                fibonacci_levels=results.get('fibonacci_levels', []),
                abc_patterns=[self._serialize_abc_pattern(p) for p in abc_patterns] if abc_patterns else [],
                symbol=getattr(df, 'symbol', 'UNKNOWN'),
                timeframe=getattr(df, 'timeframe', '1H')
            )

            # Store confluence results
            results['confluence_analysis'] = confluence_results

            # Store confluence zones and patterns for later analysis
            if confluence_results.get('confluence_zones'):
                self.confluence_zones.extend(confluence_results['confluence_zones'])
            if confluence_results.get('candlestick_patterns'):
                self.candlestick_patterns.extend(confluence_results['candlestick_patterns'])

            logger.debug(f"📊 CONFLUENCE: {confluence_results['total_factors']} factors, {len(confluence_results['confluence_zones'])} zones")
        
        # Note: ABC patterns are now sent individually as 'new_abc_pattern' when detected
        # This prevents showing all patterns at once and ensures progressive display
        
        results['total_fractals'] = len(self.fractals)
        results['total_swings'] = len(self.swings) 
        results['total_signals'] = len(self.signals)
        results['total_abc_patterns'] = len(self.abc_patterns)
        results['total_enhanced_signals'] = len(self.enhanced_signals)
        
        # Include enhanced signals in results for dashboard visualization
        results['enhanced_signals'] = [
            {
                'timestamp': signal.timestamp.isoformat(),
                'signal_type': signal.signal_type,
                'price': signal.price,
                'fibonacci_level': signal.fibonacci_level,
                'fibonacci_price': signal.fibonacci_price,
                'pattern_type': signal.confirmation_pattern.pattern_type,
                'pattern_strength': signal.confirmation_pattern.strength,
                'confluence_score': signal.confluence.total_score,
                'quality': signal.confluence.quality.value,
                'risk_reward_ratio': signal.risk_reward_ratio,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'factors': signal.confluence.factors
            } 
            for signal in self.enhanced_signals[-10:]  # Include last 10 enhanced signals
        ]
        
        # Include signal performance analytics
        results['signal_performance'] = self.signal_performance_tracker.get_real_time_stats()
        
        return results
    
    def update_signal_performance_tracking(self, df: pd.DataFrame, current_index: int):
        """Update performance tracking for all active enhanced signals."""
        if not df.empty and current_index < len(df):
            current_bar = df.iloc[current_index]
            current_price = current_bar['close']
            current_time = df.index[current_index]
            
            # Calculate bars elapsed from current signal timestamp
            for signal_id in list(self.signal_performance_tracker.active_signals.keys()):
                signal = self.signal_performance_tracker.active_signals[signal_id]
                bars_elapsed = current_index - df.index.get_loc(signal.timestamp)
                
                # Update signal performance
                self.signal_performance_tracker.update_signal_performance(
                    signal_id, current_price, current_time, bars_elapsed
                )
    
    def get_signal_analytics(self) -> Dict[str, Any]:
        """Get comprehensive signal analytics for ML/AI development."""
        return self.signal_performance_tracker.get_signal_analytics()
    
    def export_signal_performance_data(self) -> pd.DataFrame:
        """Export all signal performance data for external analysis."""
        return self.signal_performance_tracker.export_performance_data()
    
    def reset(self):
        """Reset strategy state for new backtest."""
        self.fractals.clear()
        self.swings.clear()
        self.fibonacci_zones.clear()
        self.signals.clear()
        self.abc_patterns.clear()
        self.confluence_zones.clear()
        self.candlestick_patterns.clear()
        self.enhanced_signals.clear()  # Clear enhanced signals
        self.current_bar = 0
        self.dominant_trend = None
        self.current_dominant_swing = None
        
        # Reset signal performance tracker
        self.signal_performance_tracker = SignalPerformanceTracker()
        
        # Reset confluence engine
        if self.confluence_engine:
            self.confluence_engine.reset()
    
    def _serialize_abc_pattern(self, pattern: ABCPattern) -> Dict:
        """Serialize ABC pattern for confluence analysis."""
        return {
            'wave_a': {
                'start_timestamp': pattern.wave_a.start_timestamp.isoformat(),
                'end_timestamp': pattern.wave_a.end_timestamp.isoformat(),
                'start_price': pattern.wave_a.start_price,
                'end_price': pattern.wave_a.end_price,
                'direction': pattern.wave_a.direction,
                'points': pattern.wave_a.points,
                'bars': pattern.wave_a.bars
            },
            'wave_b': {
                'start_timestamp': pattern.wave_b.start_timestamp.isoformat(),
                'end_timestamp': pattern.wave_b.end_timestamp.isoformat(),
                'start_price': pattern.wave_b.start_price,
                'end_price': pattern.wave_b.end_price,
                'direction': pattern.wave_b.direction,
                'points': pattern.wave_b.points,
                'bars': pattern.wave_b.bars
            },
            'wave_c': {
                'start_timestamp': pattern.wave_c.start_timestamp.isoformat(),
                'end_timestamp': pattern.wave_c.end_timestamp.isoformat(),
                'start_price': pattern.wave_c.start_price,
                'end_price': pattern.wave_c.end_price,
                'direction': pattern.wave_c.direction,
                'points': pattern.wave_c.points,
                'bars': pattern.wave_c.bars
            },
            'pattern_type': pattern.pattern_type,
            'is_complete': pattern.is_complete,
            'fibonacci_confluence': pattern.fibonacci_confluence
        }
    
    def detect_abc_patterns(self, df: pd.DataFrame, current_index: int) -> List[ABCPattern]:
        """
        Detect ABC correction patterns within the dominant swing structure.
        
        🚨 FIXED: Clean Single Pattern Detection Logic
        1. Only look for ABC patterns when we have a dominant swing (main trend)
        2. Find ABC corrections that are retracements/pullbacks within that dominant swing
        3. Wave A starts from dominant swing and moves against the trend
        4. Wave B retraces 38.2%-61.8% of Wave A  
        5. Wave C continues in Wave A direction (completing the correction)
        6. Return only the MOST RECENT/RELEVANT ABC pattern to avoid overlapping patterns
        """
        abc_patterns = []
        
        # Must have a dominant swing to find meaningful ABC corrections
        if not self.current_dominant_swing:
            return abc_patterns
        
        if len(self.fractals) < 4:  # Need at least 4 fractals for a complete ABC
            return abc_patterns
        
        # Get fractals that occur within the dominant swing timeframe
        swing_start_index = self.current_dominant_swing.start_fractal.bar_index
        swing_end_index = self.current_dominant_swing.end_fractal.bar_index
        
        # Find fractals within the dominant swing period
        swing_fractals = [f for f in self.fractals 
                         if swing_start_index <= f.bar_index <= current_index]
        
        if len(swing_fractals) < 4:  # Need at least 4 fractals for complete ABC
            return abc_patterns
        
        # 🚨 CRITICAL FIX: Find only the MOST RECENT complete ABC pattern
        # Look backwards from the most recent fractals to find the latest complete pattern
        best_pattern = None
        best_pattern_score = 0
        
        # Look for ABC corrections within the dominant swing
        # Start from the most recent possible pattern and work backwards
        for i in range(len(swing_fractals) - 4, -1, -1):  # Need 4 fractals, so stop at len-4
            if i + 3 >= len(swing_fractals):  # Safety check
                continue
                
            fractal_a = swing_fractals[i]      # Start of correction (from dominant swing)
            fractal_b = swing_fractals[i + 1]  # Peak of correction counter-move
            fractal_c = swing_fractals[i + 2]  # End of Wave B, start of Wave C
            fractal_c_end = swing_fractals[i + 3]  # End of Wave C (completion fractal)
            
            # Current price for Wave C completion check
            current_price = df.iloc[current_index]['close']
            current_timestamp = df.index[current_index]
            
            abc_pattern = self._validate_complete_abc_pattern(
                fractal_a, fractal_b, fractal_c, fractal_c_end, 
                current_price, current_timestamp, current_index
            )
            
            if abc_pattern:
                # Score pattern based on quality criteria
                pattern_score = self._score_abc_pattern(abc_pattern)
                
                if pattern_score > best_pattern_score:
                    best_pattern = abc_pattern
                    best_pattern_score = pattern_score
                
                # If we found a high-quality recent pattern, prefer it
                if pattern_score >= 0.8:  # High quality threshold
                    break
        
        # Return only the best pattern found
        if best_pattern:
            abc_patterns.append(best_pattern)
            logger.debug(f"🌊 BEST ABC Pattern selected: {best_pattern.pattern_type} with score {best_pattern_score:.2f}")
        
        return abc_patterns

    def _validate_complete_abc_pattern(self, fractal_a: Fractal, fractal_b: Fractal, fractal_c: Fractal, 
                                     fractal_c_end: Fractal, current_price: float, current_timestamp: pd.Timestamp, 
                                     current_index: int) -> Optional[ABCPattern]:
        """
        Validate if four fractals form a complete ABC correction pattern.
        
        🚨 FIXED: Only returns complete patterns that have ended at a fractal point.
        """
        
        # Step 1: Create Wave A
        wave_a = ABCWave(
            start_timestamp=fractal_a.timestamp,
            end_timestamp=fractal_b.timestamp,
            start_price=fractal_a.price,
            end_price=fractal_b.price,
            wave_type='A',
            direction='up' if fractal_b.price > fractal_a.price else 'down',
            points=abs(fractal_b.price - fractal_a.price),
            bars=fractal_b.bar_index - fractal_a.bar_index
        )
        
        # Step 2: Create Wave B
        wave_b = ABCWave(
            start_timestamp=fractal_b.timestamp,
            end_timestamp=fractal_c.timestamp,
            start_price=fractal_b.price,
            end_price=fractal_c.price,
            wave_type='B',
            direction='up' if fractal_c.price > fractal_b.price else 'down',
            points=abs(fractal_c.price - fractal_b.price),
            bars=fractal_c.bar_index - fractal_b.bar_index
        )
        
        # Step 3: Create Wave C (complete pattern using fractal_c_end)
        wave_c = ABCWave(
            start_timestamp=fractal_c.timestamp,
            end_timestamp=fractal_c_end.timestamp,
            start_price=fractal_c.price,
            end_price=fractal_c_end.price,
            wave_type='C',
            direction='up' if fractal_c_end.price > fractal_c.price else 'down',
            points=abs(fractal_c_end.price - fractal_c.price),
            bars=fractal_c_end.bar_index - fractal_c.bar_index
        )
        
        # Step 4: CRITICAL - Wave A must move AGAINST the dominant swing direction (correction)
        dominant_swing_direction = self.current_dominant_swing.direction
        if wave_a.direction == dominant_swing_direction:
            return None  # Wave A should be a correction, not continuation
        
        # Step 5: Validate Wave B retracement (must be 38.2%-61.8% of Wave A)
        wave_b_retracement = wave_b.points / wave_a.points
        if not (0.382 <= wave_b_retracement <= 0.618):
            return None
        
        # Step 6: Wave B must move opposite to Wave A (correction of the correction)
        if wave_a.direction == wave_b.direction:
            return None
        
        # Step 7: Wave C must move same direction as Wave A (continuation of correction)
        if wave_a.direction != wave_c.direction:
            return None
        
        # Step 8: Validate Wave C ratios (62%, 100%, 127% of Wave A)
        wave_c_ratio = wave_c.points / wave_a.points
        valid_ratios = [0.618, 1.0, 1.27]  # Fe62, Fe100, Fe127
        tolerance = 0.1  # 10% tolerance
        
        is_complete = any(abs(wave_c_ratio - ratio) <= tolerance for ratio in valid_ratios)
        
        # Only return patterns that are complete and meet Fibonacci criteria
        if not is_complete:
            return None
        
        # Step 9: Determine pattern type based on structure
        pattern_type = 'zigzag'  # Default to zigzag for now
        
        # Step 10: Check for Fibonacci confluence
        fibonacci_confluence = None
        if hasattr(self, 'current_dominant_swing') and self.current_dominant_swing:
            fib_levels = self.calculate_fibonacci_levels(self.current_dominant_swing)
            for fib_level in fib_levels:
                if abs(fractal_c_end.price - fib_level.price) <= 10:  # 10 point tolerance
                    fibonacci_confluence = fib_level.level
                    break
        
        return ABCPattern(
            wave_a=wave_a,
            wave_b=wave_b, 
            wave_c=wave_c,
            pattern_type=pattern_type,
            is_complete=True,  # Always complete in this method
            fibonacci_confluence=fibonacci_confluence
        )
    
    def _create_incomplete_abc_with_projections(self, wave_a: ABCWave, wave_b: ABCWave, 
                                               fractal_c: Fractal, current_price: float, 
                                               current_timestamp: pd.Timestamp) -> ABCPattern:
        """Create incomplete ABC pattern with C wave projection levels."""
        
        # Calculate projection levels for Wave C (Fe62, Fe100, Fe127)
        wave_a_points = wave_a.points
        
        # Project from fractal_c price
        if wave_a.direction == 'down':
            # For downward Wave A, C wave projects down
            fe62_target = fractal_c.price - (wave_a_points * 0.618)
            fe100_target = fractal_c.price - (wave_a_points * 1.0)
            fe127_target = fractal_c.price - (wave_a_points * 1.27)
        else:
            # For upward Wave A, C wave projects up
            fe62_target = fractal_c.price + (wave_a_points * 0.618)
            fe100_target = fractal_c.price + (wave_a_points * 1.0)
            fe127_target = fractal_c.price + (wave_a_points * 1.27)
        
        # Create incomplete Wave C showing current progress
        wave_c = ABCWave(
            start_timestamp=fractal_c.timestamp,
            end_timestamp=current_timestamp,
            start_price=fractal_c.price,
            end_price=current_price,
            wave_type='C',
            direction=wave_a.direction,  # Same direction as Wave A
            points=abs(current_price - fractal_c.price),
            bars=0  # Will be updated when pattern completes
        )
        
        # Store projection levels in the pattern
        pattern = ABCPattern(
            wave_a=wave_a,
            wave_b=wave_b,
            wave_c=wave_c,
            pattern_type='zigzag',
            is_complete=False,
            fibonacci_confluence=None
        )
        
        # Add projection levels as attributes
        pattern.fe62_target = fe62_target
        pattern.fe100_target = fe100_target
        pattern.fe127_target = fe127_target
        
        return pattern
    
    def _score_abc_pattern(self, pattern: ABCPattern) -> float:
        """
        Score ABC pattern based on quality criteria.
        
        Returns score between 0.0 and 1.0, where higher is better.
        """
        score = 0.0
        
        # Base score for complete patterns
        if pattern.is_complete:
            score += 0.3
        
        # Score based on Wave B retracement quality
        wave_b_retracement = pattern.wave_b.points / pattern.wave_a.points
        if 0.50 <= wave_b_retracement <= 0.618:  # Ideal retracement range
            score += 0.3
        elif 0.382 <= wave_b_retracement <= 0.50:  # Acceptable range
            score += 0.2
        
        # Score based on Wave C Fibonacci extension quality
        wave_c_ratio = pattern.wave_c.points / pattern.wave_a.points
        
        # Perfect Fibonacci ratios get highest score
        if abs(wave_c_ratio - 1.0) <= 0.05:  # Perfect 100% extension
            score += 0.3
        elif abs(wave_c_ratio - 0.618) <= 0.05:  # Perfect 62% extension
            score += 0.25
        elif abs(wave_c_ratio - 1.27) <= 0.05:  # Perfect 127% extension
            score += 0.25
        elif abs(wave_c_ratio - 1.0) <= 0.1:  # Close to 100%
            score += 0.2
        elif abs(wave_c_ratio - 0.618) <= 0.1:  # Close to 62%
            score += 0.15
        elif abs(wave_c_ratio - 1.27) <= 0.1:  # Close to 127%
            score += 0.15
        
        # Bonus for Fibonacci confluence
        if pattern.fibonacci_confluence:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_current_state(self) -> Dict:
        """Get current strategy state for dashboard display."""
        # Calculate Fibonacci levels for dominant swing if available
        fibonacci_levels = []
        if self.current_dominant_swing:
            fib_levels = self.calculate_fibonacci_levels(self.current_dominant_swing)

            # 🚨 CRITICAL DEBUG: Log fibonacci calculation in get_current_state
            logger.debug(f"🔍 GET_CURRENT_STATE: Fibonacci levels calculated from {self.current_dominant_swing.direction.upper()} swing")
            logger.debug(f"   Swing: {self.current_dominant_swing.start_fractal.price:.2f} -> {self.current_dominant_swing.end_fractal.price:.2f}")
            logger.debug(f"   Calculated {len(fib_levels)} fibonacci levels")

            fibonacci_levels = [
                {
                    'level': f.level,
                    'price': f.price,
                    'hit': f.hit,
                    'swing_direction': self.current_dominant_swing.direction,
                    'swing_start_price': self.current_dominant_swing.start_fractal.price,
                    'swing_end_price': self.current_dominant_swing.end_fractal.price,
                    'swing_start_time': self.current_dominant_swing.start_fractal.timestamp.isoformat(),
                    'swing_end_time': self.current_dominant_swing.end_fractal.timestamp.isoformat()
                } for f in fib_levels
            ]
        else:
            logger.debug("⚠️ GET_CURRENT_STATE: No dominant swing available for fibonacci calculation")

        return {
            'fractals': [
                {
                    'timestamp': f.timestamp.isoformat(),
                    'price': f.price,
                    'type': f.fractal_type,
                    'bar_index': f.bar_index
                } for f in self.fractals
            ],
            'swings': [
                {
                    'start_timestamp': s.start_fractal.timestamp.isoformat(),
                    'end_timestamp': s.end_fractal.timestamp.isoformat(),
                    'start_price': s.start_fractal.price,
                    'end_price': s.end_fractal.price,
                    'direction': s.direction,
                    'points': s.points,
                    'bars': s.bars,
                    'is_dominant': s.is_dominant
                } for s in self.swings
            ],
            'fibonacci_levels': fibonacci_levels,
            'dominant_swing': {
                'start_timestamp': self.current_dominant_swing.start_fractal.timestamp.isoformat(),
                'end_timestamp': self.current_dominant_swing.end_fractal.timestamp.isoformat(),
                'start_price': self.current_dominant_swing.start_fractal.price,
                'end_price': self.current_dominant_swing.end_fractal.price,
                'direction': self.current_dominant_swing.direction,
                'points': self.current_dominant_swing.points,
                'bars': self.current_dominant_swing.bars
            } if self.current_dominant_swing else None,
            'signals': [
                {
                    'timestamp': s.timestamp.isoformat(),
                    'type': s.signal_type,
                    'price': s.price,
                    'fibonacci_level': s.fibonacci_level,
                    'swing_direction': s.swing_direction,
                    'confidence': s.confidence,
                    'stop_loss': s.stop_loss,
                    'take_profit': s.take_profit
                } for s in self.signals
            ],
            'abc_patterns': [
                self._serialize_abc_pattern(pattern) for pattern in self.abc_patterns
            ]
        }