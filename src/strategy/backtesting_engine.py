"""
Real-time Backtesting Engine
Integrates Fibonacci strategy with step-by-step replay functionality.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .fibonacci_strategy import FibonacciStrategy
from .trading_types import TradingSignal

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """
    Step-by-step backtesting engine for interactive analysis.
    Processes one bar at a time and updates strategy state.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital for backtesting
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Strategy instance
        self.strategy = FibonacciStrategy()
        
        # Trading state
        self.current_position = None  # 'long', 'short', or None
        self.position_size = 0.0
        self.position_entry_price = 0.0
        self.position_entry_time = None
        self.position_stop_loss = 0.0
        self.position_take_profit = 0.0
        
        # Performance tracking
        self.trades = []
        self.equity_curve = []
        self.current_bar_index = 0
        self.total_bars = 0
        
        # Market data
        self.data = None
        self.current_bar = None
        
    def load_data(self, df: pd.DataFrame):
        """Load market data for backtesting."""
        self.data = df.copy()
        self.total_bars = len(df)
        self.current_bar_index = 0
        
        # Reset all state
        self.reset()
        
        logger.info(f"Loaded {len(df)} bars for backtesting")
        
    def reset(self):
        """Reset all backtesting state."""
        self.strategy.reset()
        self.current_capital = self.initial_capital
        self.current_position = None
        self.position_size = 0.0
        self.position_entry_price = 0.0
        self.position_entry_time = None
        self.position_stop_loss = 0.0
        self.position_take_profit = 0.0
        self.trades.clear()
        self.equity_curve.clear()
        self.current_bar_index = 0
        
    def calculate_position_size(self, signal: TradingSignal, current_price: float) -> float:
        """
        Calculate position size based on risk management.
        Using 2% risk per trade.
        """
        risk_per_trade = 0.02  # 2% risk
        risk_amount = self.current_capital * risk_per_trade
        
        # Calculate stop distance
        stop_distance = abs(current_price - signal.stop_loss)
        
        if stop_distance > 0:
            # Position size = Risk Amount / Stop Distance
            position_size = risk_amount / stop_distance
            
            # Ensure we don't use more capital than available
            max_position = self.current_capital * 0.95  # Use max 95% of capital
            position_size = min(position_size, max_position / current_price)
            
            return position_size
        
        return 0.0
    
    def enter_position(self, signal: TradingSignal, current_price: float, timestamp: pd.Timestamp):
        """Enter a new position based on signal."""
        if self.current_position is not None:
            return  # Already in position
            
        position_size = self.calculate_position_size(signal, current_price)
        
        if position_size > 0:
            self.current_position = 'long' if signal.signal_type == 'buy' else 'short'
            self.position_size = position_size
            self.position_entry_price = current_price
            self.position_entry_time = timestamp
            self.position_stop_loss = signal.stop_loss
            self.position_take_profit = signal.take_profit
            
            logger.info(f"Entered {self.current_position} position: {position_size:.2f} units at {current_price:.5f}")
    
    def exit_position(self, exit_price: float, timestamp: pd.Timestamp, exit_reason: str):
        """Exit current position and record trade."""
        if self.current_position is None:
            return
            
        # Calculate P&L
        if self.current_position == 'long':
            pnl = (exit_price - self.position_entry_price) * self.position_size
        else:  # short
            pnl = (self.position_entry_price - exit_price) * self.position_size
            
        # Update capital
        self.current_capital += pnl
        
        # Record trade
        trade = {
            'entry_time': self.position_entry_time,
            'exit_time': timestamp,
            'position_type': self.current_position,
            'size': self.position_size,
            'entry_price': self.position_entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'exit_reason': exit_reason,
            'bars_held': self.current_bar_index - self.get_bar_index(self.position_entry_time)
        }
        
        self.trades.append(trade)
        
        logger.info(f"Exited {self.current_position} position: P&L = {pnl:.2f}, Reason = {exit_reason}")
        
        # Reset position
        self.current_position = None
        self.position_size = 0.0
        self.position_entry_price = 0.0
        self.position_entry_time = None
        self.position_stop_loss = 0.0
        self.position_take_profit = 0.0
    
    def get_bar_index(self, timestamp: pd.Timestamp) -> int:
        """Get bar index for given timestamp."""
        try:
            return self.data.index.get_loc(timestamp)
        except KeyError:
            return self.current_bar_index
    
    def check_exit_conditions(self, current_bar: pd.Series, timestamp: pd.Timestamp):
        """Check if current position should be exited."""
        if self.current_position is None:
            return
            
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        if self.current_position == 'long':
            # Check stop loss
            if current_low <= self.position_stop_loss:
                self.exit_position(self.position_stop_loss, timestamp, 'stop_loss')
                return
            # Check take profit  
            if current_high >= self.position_take_profit:
                self.exit_position(self.position_take_profit, timestamp, 'take_profit')
                return
                
        elif self.current_position == 'short':
            # Check stop loss
            if current_high >= self.position_stop_loss:
                self.exit_position(self.position_stop_loss, timestamp, 'stop_loss')
                return
            # Check take profit
            if current_low <= self.position_take_profit:
                self.exit_position(self.position_take_profit, timestamp, 'take_profit')
                return
    
    def process_next_bar(self) -> Dict[str, Any]:
        """
        Process the next bar in sequence.
        This is called when user clicks 'Next' button.
        
        Returns:
            Dictionary with all analysis results for dashboard update
        """
        if self.data is None or self.current_bar_index >= len(self.data):
            return {'error': 'No more bars to process'}
            
        # Get current bar
        self.current_bar = self.data.iloc[self.current_bar_index]
        timestamp = self.data.index[self.current_bar_index]
        
        # 1. Check exit conditions first (before processing new signals)
        self.check_exit_conditions(self.current_bar, timestamp)
        
        # 2. Process bar through strategy
        try:
            strategy_results = self.strategy.process_bar(self.data, self.current_bar_index)
            if strategy_results is None:
                return {'error': f'Strategy returned None at bar {self.current_bar_index}'}
        except Exception as e:
            return {'error': f'Strategy error at bar {self.current_bar_index}: {str(e)}'}
        
        # 3. Handle new signals (convert dict signals to TradingSignal objects)
        new_trades = []
        for signal_dict in strategy_results.get('new_signals', []):
            if self.current_position is None:  # Only enter if not in position
                # Convert dict to TradingSignal object for backtesting engine
                from .fibonacci_strategy import TradingSignal
                signal = TradingSignal(
                    timestamp=pd.Timestamp(signal_dict['timestamp']),
                    signal_type=signal_dict['signal_type'],
                    price=signal_dict['price'],
                    fibonacci_level=signal_dict['fibonacci_level'],
                    swing_direction=signal_dict['swing_direction'],
                    confidence=signal_dict['confidence'],
                    stop_loss=signal_dict['stop_loss'],
                    take_profit=signal_dict['take_profit']
                )
                self.enter_position(signal, self.current_bar['close'], timestamp)
                new_trades.append({
                    'type': 'entry',
                    'signal': signal_dict,  # Keep dict for JSON serialization
                    'price': self.current_bar['close']
                })
        
        # 4. Update equity curve
        current_equity = self.current_capital
        if self.current_position is not None:
            # Add unrealized P&L
            current_price = self.current_bar['close']
            if self.current_position == 'long':
                unrealized_pnl = (current_price - self.position_entry_price) * self.position_size
            else:
                unrealized_pnl = (self.position_entry_price - current_price) * self.position_size
            current_equity += unrealized_pnl
            
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': current_equity,
            'bar_index': self.current_bar_index
        })
        
        # 5. Prepare results for dashboard
        results = {
            'bar_index': self.current_bar_index,
            'total_bars': self.total_bars,
            'timestamp': timestamp.isoformat(),
            'current_bar': {
                'open': float(self.current_bar['open']),
                'high': float(self.current_bar['high']),
                'low': float(self.current_bar['low']),
                'close': float(self.current_bar['close']),
                'volume': float(self.current_bar['volume'])
            },
            'strategy_results': strategy_results,
            'new_trades': new_trades,
            'current_position': {
                'type': self.current_position,
                'size': self.position_size,
                'entry_price': self.position_entry_price,
                'entry_time': self.position_entry_time.isoformat() if self.position_entry_time else None,
                'stop_loss': self.position_stop_loss,
                'take_profit': self.position_take_profit,
                'unrealized_pnl': current_equity - self.current_capital if self.current_position else 0.0
            } if self.current_position else None,
            'performance': self.get_performance_metrics(),
            'progress': (self.current_bar_index + 1) / self.total_bars * 100
        }
        
        # Move to next bar
        self.current_bar_index += 1
        
        return results
    
    def jump_to_bar(self, target_index: int) -> Dict[str, Any]:
        """
        Jump to specific bar index.
        Processes all bars up to target to maintain strategy state.
        """
        if target_index < 0 or target_index >= len(self.data):
            return {'error': 'Invalid bar index'}
            
        # If jumping backwards, reset and replay
        if target_index < self.current_bar_index:
            self.reset()
            
        # Process bars up to target
        while self.current_bar_index <= target_index:
            result = self.process_next_bar()
            if 'error' in result:
                break
                
        return result
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate current performance metrics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0
            }
            
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        total_profit = sum(t['pnl'] for t in self.trades)
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        # Calculate maximum drawdown
        max_equity = self.initial_capital
        max_drawdown = 0.0
        
        for equity_point in self.equity_curve:
            equity = equity_point['equity']
            if equity > max_equity:
                max_equity = equity
            else:
                drawdown = (max_equity - equity) / max_equity * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if self.trades else 0.0,
            'total_profit': total_profit,
            'max_drawdown': max_drawdown,
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0.0,
            'sharpe_ratio': 0.0  # TODO: Implement Sharpe ratio calculation
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get complete current state for dashboard."""
        return {
            'bar_index': self.current_bar_index,
            'total_bars': self.total_bars,
            'current_position': self.current_position,
            'capital': self.current_capital,
            'strategy_state': self.strategy.get_current_state(),
            'performance': self.get_performance_metrics(),
            'trades': self.trades[-10:],  # Last 10 trades
            'equity_curve': self.equity_curve[-100:]  # Last 100 equity points
        }