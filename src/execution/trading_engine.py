"""
Automated Trading Engine
Core engine for automated Fibonacci strategy execution with MT5 integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from src.core.fractal_detection import FractalDetector, Fractal
from src.data.mt5_interface import MT5Interface, get_connection
from src.utils.config import get_config
from src.monitoring import get_logger

logger = get_logger("trading_engine")


class TradingState(Enum):
    """Trading engine states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class TradeSignal(Enum):
    """Trade signal types."""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    NONE = "none"


@dataclass
class TradingParameters:
    """Trading parameters configuration."""
    enabled_symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframe: str = "M1"
    risk_per_trade: float = 0.01
    max_positions: int = 3
    max_daily_loss: float = 0.05
    fibonacci_levels: Dict[str, List[float]] = field(default_factory=lambda: {
        "retracements": [0.236, 0.382, 0.5, 0.618, 0.786],
        "extensions": [1.0, 1.272, 1.618, 2.0]
    })
    fractal_periods: int = 5
    swing_lookback: int = 100
    stop_buffer_pips: int = 2
    
    # Trading session controls
    london_session: bool = True
    new_york_session: bool = True
    asian_session: bool = False
    news_filter: bool = True
    
    # AI Enhancement flags
    ai_pattern_recognition: bool = False
    ai_parameter_optimization: bool = False
    ai_entry_timing: bool = False


@dataclass
class Position:
    """Trading position representation."""
    symbol: str
    ticket: int
    type: str  # "buy" or "sell"
    volume: float
    open_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    profit: float
    timestamp: datetime
    strategy_signal: str = ""
    fibonacci_level: Optional[float] = None


@dataclass
class TradingSession:
    """Trading session information."""
    symbol: str
    start_time: datetime
    daily_pnl: float = 0.0
    daily_trades: int = 0
    max_drawdown: float = 0.0
    is_active: bool = True


class TradingEngine:
    """
    Core automated trading engine with Fibonacci strategy implementation.
    
    Features:
    - Automated MT5 trade execution
    - Real-time fractal and Fibonacci analysis
    - Risk management and position sizing
    - Multi-symbol trading support
    - Web dashboard integration
    """
    
    def __init__(self, mt5_interface: Optional[MT5Interface]):
        self.mt5 = mt5_interface
        # Use more responsive fractal detection for real-time trading
        from src.core.fractal_detection import FractalDetectionConfig
        fractal_config = FractalDetectionConfig(
            periods=3,  # Reduced from 5 to 3 for faster detection
            min_strength_pips=0.0,  # No minimum strength requirement
            handle_equal_prices=True,
            require_closes_beyond=False
        )
        self.fractal_detector = FractalDetector(fractal_config)
        
        # Trading state
        self.state = TradingState.STOPPED
        self.parameters = TradingParameters()
        self.positions: Dict[str, Position] = {}
        self.sessions: Dict[str, TradingSession] = {}
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_trades = 0
        self.winning_trades = 0
        
        # Strategy data cache
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.fractals_cache: Dict[str, List[Fractal]] = {}
        self.fibonacci_levels_cache: Dict[str, Dict] = {}
        
        # Control flags
        self.emergency_stop = False
        self.pause_trading = False
        
        logger.info("Trading engine initialized")
    
    async def start(self) -> bool:
        """Start the trading engine."""
        try:
            if not self.mt5:
                logger.error("MT5 interface not available - cannot start trading")
                return False
            
            if not self.mt5.connect():
                logger.error("Failed to connect to MT5")
                return False
            
            # Initialize symbols and verify they're available
            import MetaTrader5 as mt5
            import time
            
            for symbol in self.parameters.enabled_symbols:
                # Select symbol and wait for it to load
                if not mt5.symbol_select(symbol, True):
                    logger.warning(f"Could not select symbol {symbol}")
                    continue
                
                # Wait a moment for symbol to initialize
                time.sleep(0.2)
                
                # Verify we can get tick data
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    logger.info(f"✅ Symbol {symbol} ready: bid={tick.bid}, ask={tick.ask}")
                else:
                    logger.warning(f"⚠️ Symbol {symbol} selected but no tick data yet")
            
            # Initialize trading sessions
            for symbol in self.parameters.enabled_symbols:
                self.sessions[symbol] = TradingSession(
                    symbol=symbol,
                    start_time=datetime.now()
                )
            
            self.state = TradingState.RUNNING
            logger.info("Trading engine started successfully")
            
            # Start main trading loop
            asyncio.create_task(self._trading_loop())
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            self.state = TradingState.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the trading engine."""
        try:
            self.state = TradingState.STOPPED
            
            # Close all positions if requested
            if hasattr(self, '_close_all_on_stop') and self._close_all_on_stop:
                await self.close_all_positions()
            
            self.mt5.disconnect()
            logger.info("Trading engine stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
            return False
    
    async def pause(self) -> bool:
        """Pause trading (keep positions, stop new trades)."""
        self.state = TradingState.PAUSED
        logger.info("Trading engine paused")
        return True
    
    async def resume(self) -> bool:
        """Resume trading."""
        if self.state == TradingState.PAUSED:
            self.state = TradingState.RUNNING
            logger.info("Trading engine resumed")
            return True
        return False
    
    async def emergency_stop_all(self) -> bool:
        """Emergency stop - close all positions immediately."""
        try:
            self.emergency_stop = True
            self.state = TradingState.STOPPED
            
            # Close all positions immediately
            success = await self.close_all_positions()
            
            logger.warning("Emergency stop executed")
            return success
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False
    
    async def _trading_loop(self):
        """Main trading loop."""
        while self.state == TradingState.RUNNING:
            try:
                if self.emergency_stop or self.pause_trading:
                    await asyncio.sleep(1)
                    continue
                
                # Check daily loss limits
                if await self._check_daily_limits():
                    logger.warning("Daily loss limit reached, stopping trading")
                    await self.pause()
                    continue
                
                # Process each enabled symbol
                for symbol in self.parameters.enabled_symbols:
                    if symbol not in self.sessions or not self.sessions[symbol].is_active:
                        continue
                    
                    # Update market data
                    await self._update_market_data(symbol)
                    
                    # Analyze fractals and Fibonacci levels
                    await self._analyze_market_structure(symbol)
                    
                    # Check for trading signals
                    signal = await self._generate_trading_signal(symbol)
                    
                    # Execute trades based on signals
                    if signal != TradeSignal.NONE:
                        await self._execute_trade(symbol, signal)
                    
                    # Update existing positions
                    await self._update_positions(symbol)
                
                # Sleep between iterations - reduced for more responsive fractal detection
                await asyncio.sleep(2)  # 2-second intervals for better responsiveness
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)  # Longer pause on error
    
    async def _update_market_data(self, symbol: str):
        """Update market data for symbol."""
        try:
            # Get recent data (last 200 bars for analysis)
            connection = get_connection()
            if connection:
                from src.data.mt5_interface import TimeFrame
                timeframe = TimeFrame.M1  # Use M1 for real-time analysis
                data = connection.get_rates(symbol, timeframe, 200)
            else:
                data = None
            
            if data is not None and not data.empty:
                # Check if we have new data
                old_data_len = len(self.market_data.get(symbol, []))
                new_data_len = len(data)
                
                if new_data_len != old_data_len:
                    logger.info(f"📈 Market data updated for {symbol}: {old_data_len} → {new_data_len} bars")
                    latest_candle = data.iloc[-1]
                    logger.debug(f"Latest candle: O:{latest_candle['Open']:.5f} H:{latest_candle['High']:.5f} L:{latest_candle['Low']:.5f} C:{latest_candle['Close']:.5f}")
                
                self.market_data[symbol] = data
            else:
                logger.warning(f"No market data received for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to update market data for {symbol}: {e}")
    
    async def _analyze_market_structure(self, symbol: str):
        """Analyze fractals and calculate Fibonacci levels."""
        try:
            if symbol not in self.market_data:
                return
            
            data = self.market_data[symbol]
            logger.debug(f"Analyzing market structure for {symbol}: {len(data)} bars available")
            
            # Detect fractals
            fractals = self.fractal_detector.detect_fractals(data)
            
            # Log fractal detection results
            old_fractal_count = len(self.fractals_cache.get(symbol, []))
            new_fractal_count = len(fractals)
            
            if new_fractal_count != old_fractal_count:
                logger.info(f"📊 Fractals updated for {symbol}: {old_fractal_count} → {new_fractal_count}")
                if fractals:
                    latest_fractal = fractals[-1]
                    logger.info(f"Latest fractal: {latest_fractal.type.value} at {latest_fractal.price:.5f} ({latest_fractal.timestamp})")
            
            self.fractals_cache[symbol] = fractals
            
            # Calculate Fibonacci levels if we have fractals
            if len(fractals) >= 2:
                fibonacci_levels = self._calculate_fibonacci_levels(data, fractals)
                self.fibonacci_levels_cache[symbol] = fibonacci_levels
                logger.debug(f"Fibonacci levels calculated: {len(fibonacci_levels.get('retracements', {}))} retracements")
            else:
                logger.debug(f"Not enough fractals for Fibonacci calculation: {len(fractals)}")
            
        except Exception as e:
            logger.error(f"Failed to analyze market structure for {symbol}: {e}")
    
    def _calculate_fibonacci_levels(self, data: pd.DataFrame, fractals: List[Fractal]) -> Dict:
        """Calculate Fibonacci retracement and extension levels."""
        try:
            if len(fractals) < 2:
                return {}
            
            # Find the dominant swing (largest swing among recent fractals)
            dominant_swing = self._find_dominant_swing(fractals)
            if not dominant_swing:
                return {}
            
            swing_start, swing_end = dominant_swing
            
            # Determine swing direction
            if swing_end.price > swing_start.price:
                # Upward swing
                swing_high = swing_end.price
                swing_low = swing_start.price
                swing_direction = "up"
            else:
                # Downward swing
                swing_high = swing_start.price
                swing_low = swing_end.price
                swing_direction = "down"
            
            swing_range = swing_high - swing_low
            
            # Calculate retracement levels
            retracement_levels = {}
            for level in self.parameters.fibonacci_levels["retracements"]:
                if swing_direction == "up":
                    # For upward swing, retracements are below the high
                    price = swing_high - (swing_range * level)
                else:
                    # For downward swing, retracements are above the low
                    price = swing_low + (swing_range * level)
                
                retracement_levels[f"{level:.1%}"] = price
            
            # Calculate extension levels
            extension_levels = {}
            for level in self.parameters.fibonacci_levels["extensions"]:
                if swing_direction == "up":
                    # Extensions beyond the high
                    price = swing_high + (swing_range * (level - 1))
                else:
                    # Extensions beyond the low
                    price = swing_low - (swing_range * (level - 1))
                
                extension_levels[f"{level:.1%}"] = price
            
            return {
                "swing_direction": swing_direction,
                "swing_high": swing_high,
                "swing_low": swing_low,
                "swing_range": swing_range,
                "retracements": retracement_levels,
                "extensions": extension_levels,
                "swing_start": swing_start,
                "swing_end": swing_end
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate Fibonacci levels: {e}")
            return {}
    
    async def _generate_trading_signal(self, symbol: str) -> TradeSignal:
        """Generate trading signal based on Fibonacci analysis."""
        try:
            if symbol not in self.fibonacci_levels_cache:
                return TradeSignal.NONE
            
            fibonacci_data = self.fibonacci_levels_cache[symbol]
            if not fibonacci_data:
                return TradeSignal.NONE
            
            current_price = self.market_data[symbol]['Close'].iloc[-1]
            swing_direction = fibonacci_data["swing_direction"]
            retracements = fibonacci_data["retracements"]
            
            # Check if we're at a key Fibonacci level
            for level_name, level_price in retracements.items():
                tolerance = 0.0005  # 5 pips tolerance
                
                if abs(current_price - level_price) / level_price < tolerance:
                    # We're at a Fibonacci level, check for entry signal
                    
                    if swing_direction == "up":
                        # Look for long entry on retracement in uptrend
                        if level_name in ["38.2%", "50.0%", "61.8%"]:
                            # Additional confluence checks can be added here
                            return TradeSignal.BUY
                    
                    elif swing_direction == "down":
                        # Look for short entry on retracement in downtrend
                        if level_name in ["38.2%", "50.0%", "61.8%"]:
                            # Additional confluence checks can be added here
                            return TradeSignal.SELL
            
            return TradeSignal.NONE
            
        except Exception as e:
            logger.error(f"Failed to generate trading signal for {symbol}: {e}")
            return TradeSignal.NONE
    
    async def _execute_trade(self, symbol: str, signal: TradeSignal):
        """Execute trade based on signal."""
        try:
            # Check if we can open new position
            if len(self.positions) >= self.parameters.max_positions:
                return
            
            # Check if we already have position for this symbol
            if any(pos.symbol == symbol for pos in self.positions.values()):
                return
            
            # Quick check if symbol has prices before attempting trade
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logger.debug(f"No tick data for {symbol}, skipping trade")
                return
            
            # Calculate position size
            volume = self._calculate_position_size(symbol)
            if volume <= 0:
                return
            
            # Get current price
            current_price = self.market_data[symbol]['Close'].iloc[-1]
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_take_profit(symbol, signal, current_price)
            
            # Execute market order with risk management
            ticket = self.mt5.place_order(
                symbol=symbol,
                order_type="buy" if signal == TradeSignal.BUY else "sell",
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if ticket:
                # Create position record
                position = Position(
                    symbol=symbol,
                    ticket=ticket,
                    type="buy" if signal == TradeSignal.BUY else "sell",
                    volume=volume,
                    open_price=current_price,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    profit=0.0,
                    timestamp=datetime.now(),
                    strategy_signal=f"Fibonacci {signal.value}",
                    fibonacci_level=self._get_nearest_fibonacci_level(symbol, current_price)
                )
                
                self.positions[str(ticket)] = position
                self.daily_trades += 1
                self.total_trades += 1
                
                logger.info(f"Trade executed: {signal.value} {symbol} at {current_price}")
            
        except Exception as e:
            logger.error(f"Failed to execute trade for {symbol}: {e}")
    
    def _calculate_position_size(self, symbol: str) -> float:
        """Calculate position size based on risk parameters."""
        try:
            # Get account balance
            account_info = self.mt5.get_account_info()
            if not account_info:
                return 0.0
            
            balance = account_info['balance'] if isinstance(account_info, dict) else account_info.balance
            risk_amount = balance * self.parameters.risk_per_trade
            
            # Calculate position size based on stop loss
            current_price = self.market_data[symbol]['Close'].iloc[-1]
            stop_distance = self.parameters.stop_buffer_pips * 0.0001  # Convert pips to price
            
            if stop_distance > 0:
                # Calculate lot size
                pip_value = 10  # USD per pip for standard lot (simplified)
                position_size = risk_amount / (self.parameters.stop_buffer_pips * pip_value)
                
                # Ensure minimum lot size
                min_lot = 0.01
                max_lot = 1.0
                
                return max(min_lot, min(position_size, max_lot))
            
            return 0.01  # Default minimum lot size (0.01 = micro lot)
            
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            return 0.01
    
    def _calculate_stop_take_profit(self, symbol: str, signal: TradeSignal, current_price: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels."""
        try:
            pip_size = 0.0001  # For 4-digit brokers
            stop_buffer = self.parameters.stop_buffer_pips * pip_size
            
            if signal == TradeSignal.BUY:
                stop_loss = current_price - stop_buffer
                # Use Fibonacci extension for take profit
                if symbol in self.fibonacci_levels_cache:
                    extensions = self.fibonacci_levels_cache[symbol].get("extensions", {})
                    if "127.2%" in extensions:
                        take_profit = extensions["127.2%"]
                    else:
                        take_profit = current_price + (stop_buffer * 2)  # 2:1 RR
                else:
                    take_profit = current_price + (stop_buffer * 2)
            
            elif signal == TradeSignal.SELL:
                stop_loss = current_price + stop_buffer
                # Use Fibonacci extension for take profit
                if symbol in self.fibonacci_levels_cache:
                    extensions = self.fibonacci_levels_cache[symbol].get("extensions", {})
                    if "127.2%" in extensions:
                        take_profit = extensions["127.2%"]
                    else:
                        take_profit = current_price - (stop_buffer * 2)  # 2:1 RR
                else:
                    take_profit = current_price - (stop_buffer * 2)
            
            else:
                return 0.0, 0.0
            
            return round(stop_loss, 5), round(take_profit, 5)
            
        except Exception as e:
            logger.error(f"Failed to calculate stop/take profit: {e}")
            return 0.0, 0.0
    
    def _get_nearest_fibonacci_level(self, symbol: str, price: float) -> Optional[float]:
        """Get the nearest Fibonacci level to the given price."""
        try:
            if symbol not in self.fibonacci_levels_cache:
                return None
            
            retracements = self.fibonacci_levels_cache[symbol].get("retracements", {})
            if not retracements:
                return None
            
            # Find nearest level
            min_distance = float('inf')
            nearest_level = None
            
            for level_name, level_price in retracements.items():
                distance = abs(price - level_price)
                if distance < min_distance:
                    min_distance = distance
                    nearest_level = float(level_name.rstrip('%')) / 100
            
            return nearest_level
            
        except Exception as e:
            logger.error(f"Failed to get nearest Fibonacci level: {e}")
            return None
    
    def _find_dominant_swing(self, fractals: List[Fractal]) -> Optional[Tuple[Fractal, Fractal]]:
        """Find the dominant (largest) swing among recent fractals."""
        try:
            if len(fractals) < 2:
                return None
            
            # Look at the last 8 fractals (or all if fewer) to find dominant swing
            recent_fractals = fractals[-8:] if len(fractals) >= 8 else fractals
            
            largest_swing = None
            largest_range = 0.0
            
            # Check all consecutive pairs to find the largest swing
            for i in range(len(recent_fractals) - 1):
                start_fractal = recent_fractals[i]
                end_fractal = recent_fractals[i + 1]
                
                # Calculate swing range
                swing_range = abs(end_fractal.price - start_fractal.price)
                
                # Keep track of the largest swing
                if swing_range > largest_range:
                    largest_range = swing_range
                    largest_swing = (start_fractal, end_fractal)
            
            # Only change dominant swing if new swing is significantly larger (10% more)
            if hasattr(self, '_current_dominant_swing') and self._current_dominant_swing:
                current_start, current_end = self._current_dominant_swing
                current_range = abs(current_end.price - current_start.price)
                
                # Require new swing to be at least 10% larger to become dominant
                if largest_range < current_range * 1.1:
                    logger.debug(f"Keeping existing dominant swing: {current_range:.5f} vs new {largest_range:.5f}")
                    return self._current_dominant_swing
            
            # Update current dominant swing
            if largest_swing:
                self._current_dominant_swing = largest_swing
                logger.info(f"New dominant swing: {largest_swing[0].type.value} at {largest_swing[0].price:.5f} → {largest_swing[1].type.value} at {largest_swing[1].price:.5f} (range: {largest_range:.5f})")
            
            return largest_swing
            
        except Exception as e:
            logger.error(f"Failed to find dominant swing: {e}")
            return None
    
    async def _update_positions(self, symbol: str):
        """Update existing positions for symbol."""
        try:
            # Get current positions from MT5
            mt5_positions = self.mt5.get_positions(symbol)
            
            # Update our position records
            for ticket, position in list(self.positions.items()):
                if position.symbol != symbol:
                    continue
                
                # Check if position still exists in MT5
                mt5_pos = next((p for p in mt5_positions if p.ticket == position.ticket), None)
                
                if mt5_pos:
                    # Update position data
                    position.current_price = mt5_pos.price_current
                    position.profit = mt5_pos.profit
                else:
                    # Position was closed
                    if position.profit > 0:
                        self.winning_trades += 1
                    
                    self.daily_pnl += position.profit
                    
                    logger.info(f"Position closed: {position.symbol} ticket {position.ticket} profit {position.profit}")
                    del self.positions[ticket]
            
        except Exception as e:
            logger.error(f"Failed to update positions for {symbol}: {e}")
    
    async def close_all_positions(self) -> bool:
        """Close all open positions."""
        try:
            success = True
            for ticket, position in list(self.positions.items()):
                if self.mt5.close_position(position.ticket):
                    logger.info(f"Closed position: {position.symbol} ticket {position.ticket}")
                    del self.positions[ticket]
                else:
                    logger.error(f"Failed to close position: {position.symbol} ticket {position.ticket}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return False
    
    async def _check_daily_limits(self) -> bool:
        """Check if daily loss limits are exceeded."""
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return False
            
            balance = account_info['balance'] if isinstance(account_info, dict) else account_info.balance
            max_loss = balance * self.parameters.max_daily_loss
            
            return self.daily_pnl < -max_loss
            
        except Exception as e:
            logger.error(f"Failed to check daily limits: {e}")
            return False
    
    # Configuration and status methods
    def update_parameters(self, new_params: Dict[str, Any]) -> bool:
        """Update trading parameters."""
        try:
            for key, value in new_params.items():
                if hasattr(self.parameters, key):
                    setattr(self.parameters, key, value)
                    logger.info(f"Updated parameter {key} to {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update parameters: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status."""
        return {
            "state": self.state.value,
            "enabled_symbols": self.parameters.enabled_symbols,
            "active_positions": len(self.positions),
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "total_trades": self.total_trades,
            "win_rate": self.winning_trades / max(self.total_trades, 1) * 100,
            "emergency_stop": self.emergency_stop,
            "pause_trading": self.pause_trading
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": pos.type,
                "volume": pos.volume,
                "open_price": pos.open_price,
                "current_price": pos.current_price,
                "profit": pos.profit,
                "stop_loss": pos.stop_loss,
                "take_profit": pos.take_profit,
                "timestamp": pos.timestamp.isoformat(),
                "strategy_signal": pos.strategy_signal,
                "fibonacci_level": pos.fibonacci_level
            }
            for pos in self.positions.values()
        ]
    
    def get_fibonacci_levels(self, symbol: str) -> Dict[str, Any]:
        """Get current Fibonacci levels for symbol."""
        return self.fibonacci_levels_cache.get(symbol, {})


# Global trading engine instance
trading_engine: Optional[TradingEngine] = None


def get_trading_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance."""
    return trading_engine


def initialize_trading_engine(mt5_interface: Optional[MT5Interface]) -> TradingEngine:
    """Initialize the global trading engine."""
    global trading_engine
    trading_engine = TradingEngine(mt5_interface)
    return trading_engine