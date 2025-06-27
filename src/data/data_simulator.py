"""
Market Data Simulator
Generates realistic market data for testing when MT5 is not available.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass
import random

from src.monitoring import get_logger

logger = get_logger("data_simulator")


@dataclass
class SimulationConfig:
    """Configuration for market data simulation."""
    symbol: str = "DJ30"
    initial_price: float = 35000.0
    volatility: float = 0.02  # Daily volatility (2%)
    trend_strength: float = 0.001  # Daily trend strength
    noise_level: float = 0.0005  # Random noise level
    spread_pips: float = 2.0
    bars_per_day: int = 1440  # M1 timeframe


class MarketDataSimulator:
    """Generates realistic market data for testing purposes."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.random_state = np.random.RandomState(42)  # Reproducible results
        
    def generate_ohlc_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate OHLC data for the specified date range."""
        logger.info(f"Generating {self.config.symbol} data from {start_date} to {end_date}")
        
        # Calculate number of bars needed
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        
        # Generate timestamps
        timestamps = pd.date_range(start=start_date, periods=total_minutes, freq='1min')
        
        # Generate price movements using geometric Brownian motion with trends
        prices = self._generate_price_series(total_minutes)
        
        # Create OHLC data from price series
        ohlc_data = self._create_ohlc_from_prices(prices, timestamps)
        
        logger.info(f"Generated {len(ohlc_data)} bars of {self.config.symbol} data")
        return ohlc_data
    
    def _generate_price_series(self, num_bars: int) -> np.ndarray:
        """Generate realistic price movements with trends and volatility."""
        # Initialize price series
        prices = np.zeros(num_bars)
        prices[0] = self.config.initial_price
        
        # Generate market cycles (trending and ranging periods)
        cycle_length = 2000  # Average cycle length in minutes
        trend_cycles = self._generate_trend_cycles(num_bars, cycle_length)
        
        # Generate price movements
        for i in range(1, num_bars):
            # Get current trend and volatility
            current_trend = trend_cycles[i]
            current_vol = self._get_dynamic_volatility(i, num_bars)
            
            # Calculate price change
            # Trend component
            trend_change = current_trend * self.config.trend_strength
            
            # Volatility component (random walk)
            volatility_change = self.random_state.normal(0, current_vol)
            
            # Noise component
            noise_change = self.random_state.normal(0, self.config.noise_level)
            
            # Total change
            total_change = trend_change + volatility_change + noise_change
            
            # Apply change
            prices[i] = prices[i-1] * (1 + total_change)
        
        return prices
    
    def _generate_trend_cycles(self, num_bars: int, cycle_length: int) -> np.ndarray:
        """Generate trending and ranging market cycles."""
        cycles = np.zeros(num_bars)
        
        i = 0
        while i < num_bars:
            # Random cycle length with variation
            current_cycle_length = int(cycle_length * (0.5 + self.random_state.random()))
            
            # Random trend strength (-1 to 1)
            trend_strength = self.random_state.uniform(-1, 1)
            
            # Apply trend over cycle
            end_idx = min(i + current_cycle_length, num_bars)
            cycles[i:end_idx] = trend_strength
            
            i = end_idx
        
        return cycles
    
    def _get_dynamic_volatility(self, current_bar: int, total_bars: int) -> float:
        """Get dynamic volatility that changes over time."""
        # Base volatility
        base_vol = self.config.volatility / np.sqrt(self.config.bars_per_day)
        
        # Add volatility clustering (high vol periods followed by high vol)
        vol_cycle = np.sin(current_bar / 500) * 0.5 + 0.5  # 0 to 1
        volatility_multiplier = 0.5 + vol_cycle * 1.5  # 0.5 to 2.0
        
        return base_vol * volatility_multiplier
    
    def _create_ohlc_from_prices(self, prices: np.ndarray, timestamps: pd.DatetimeIndex) -> pd.DataFrame:
        """Create realistic OHLC data from price series."""
        num_bars = len(prices)
        
        # Initialize OHLC arrays
        opens = np.zeros(num_bars)
        highs = np.zeros(num_bars)
        lows = np.zeros(num_bars)
        closes = np.zeros(num_bars)
        volumes = np.zeros(num_bars)
        
        for i in range(num_bars):
            # Close price is the main price
            closes[i] = prices[i]
            
            # Open price (previous close or gap)
            if i == 0:
                opens[i] = prices[i]
            else:
                # Small gap possibility
                gap_factor = 1 + self.random_state.normal(0, 0.0001)
                opens[i] = closes[i-1] * gap_factor
            
            # High and low based on intrabar volatility
            intrabar_vol = self.config.volatility / np.sqrt(self.config.bars_per_day) * 0.5
            
            # Calculate potential high and low
            price_range = max(opens[i], closes[i]) * intrabar_vol
            
            highs[i] = max(opens[i], closes[i]) + self.random_state.exponential(price_range)
            lows[i] = min(opens[i], closes[i]) - self.random_state.exponential(price_range)
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            highs[i] = max(highs[i], opens[i], closes[i])
            lows[i] = min(lows[i], opens[i], closes[i])
            
            # Generate volume (log-normal distribution)
            volumes[i] = self.random_state.lognormal(mean=8, sigma=1)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes.astype(int)
        }, index=timestamps)
        
        return df
    
    def add_fractal_patterns(self, data: pd.DataFrame, num_patterns: int = 20) -> pd.DataFrame:
        """Add deliberate fractal patterns to make testing more interesting."""
        data = data.copy()
        
        # Add some deliberate swing patterns
        for _ in range(num_patterns):
            # Random position for pattern
            start_idx = self.random_state.randint(100, len(data) - 200)
            
            # Random pattern type
            pattern_type = self.random_state.choice(['upswing', 'downswing', 'double_top', 'double_bottom'])
            
            if pattern_type == 'upswing':
                data = self._add_upswing_pattern(data, start_idx)
            elif pattern_type == 'downswing':
                data = self._add_downswing_pattern(data, start_idx)
            elif pattern_type == 'double_top':
                data = self._add_double_top_pattern(data, start_idx)
            elif pattern_type == 'double_bottom':
                data = self._add_double_bottom_pattern(data, start_idx)
        
        return data
    
    def _add_upswing_pattern(self, data: pd.DataFrame, start_idx: int) -> pd.DataFrame:
        """Add a clear upswing pattern."""
        swing_length = self.random_state.randint(30, 100)
        end_idx = min(start_idx + swing_length, len(data))
        
        # Create uptrend
        start_price = data.iloc[start_idx]['Close']
        end_price = start_price * (1 + self.random_state.uniform(0.02, 0.08))  # 2-8% move
        
        for i in range(start_idx, end_idx):
            progress = (i - start_idx) / swing_length
            target_price = start_price + (end_price - start_price) * progress
            
            # Apply with some noise
            noise = self.random_state.normal(0, 0.002)
            data.iloc[i, data.columns.get_loc('Close')] = target_price * (1 + noise)
            
            # Adjust OHLC to be consistent
            self._adjust_ohlc_consistency(data, i)
        
        return data
    
    def _add_downswing_pattern(self, data: pd.DataFrame, start_idx: int) -> pd.DataFrame:
        """Add a clear downswing pattern."""
        swing_length = self.random_state.randint(30, 100)
        end_idx = min(start_idx + swing_length, len(data))
        
        # Create downtrend
        start_price = data.iloc[start_idx]['Close']
        end_price = start_price * (1 - self.random_state.uniform(0.02, 0.08))  # 2-8% move
        
        for i in range(start_idx, end_idx):
            progress = (i - start_idx) / swing_length
            target_price = start_price + (end_price - start_price) * progress
            
            # Apply with some noise
            noise = self.random_state.normal(0, 0.002)
            data.iloc[i, data.columns.get_loc('Close')] = target_price * (1 + noise)
            
            # Adjust OHLC to be consistent
            self._adjust_ohlc_consistency(data, i)
        
        return data
    
    def _add_double_top_pattern(self, data: pd.DataFrame, start_idx: int) -> pd.DataFrame:
        """Add a double top pattern."""
        pattern_length = 150
        end_idx = min(start_idx + pattern_length, len(data))
        
        if end_idx - start_idx < 100:
            return data
        
        # Create double top
        base_price = data.iloc[start_idx]['Close']
        peak_price = base_price * 1.05  # 5% higher
        
        quarter = (end_idx - start_idx) // 4
        
        # First peak
        for i in range(start_idx, start_idx + quarter * 2):
            progress = abs((i - start_idx) - quarter) / quarter
            target_price = base_price + (peak_price - base_price) * (1 - progress)
            data.iloc[i, data.columns.get_loc('Close')] = target_price
            self._adjust_ohlc_consistency(data, i)
        
        # Second peak
        for i in range(start_idx + quarter * 2, end_idx):
            progress = abs((i - start_idx - quarter * 2) - quarter) / quarter
            target_price = base_price + (peak_price - base_price) * (1 - progress)
            data.iloc[i, data.columns.get_loc('Close')] = target_price
            self._adjust_ohlc_consistency(data, i)
        
        return data
    
    def _add_double_bottom_pattern(self, data: pd.DataFrame, start_idx: int) -> pd.DataFrame:
        """Add a double bottom pattern."""
        pattern_length = 150
        end_idx = min(start_idx + pattern_length, len(data))
        
        if end_idx - start_idx < 100:
            return data
        
        # Create double bottom
        base_price = data.iloc[start_idx]['Close']
        trough_price = base_price * 0.95  # 5% lower
        
        quarter = (end_idx - start_idx) // 4
        
        # First trough
        for i in range(start_idx, start_idx + quarter * 2):
            progress = abs((i - start_idx) - quarter) / quarter
            target_price = base_price - (base_price - trough_price) * (1 - progress)
            data.iloc[i, data.columns.get_loc('Close')] = target_price
            self._adjust_ohlc_consistency(data, i)
        
        # Second trough
        for i in range(start_idx + quarter * 2, end_idx):
            progress = abs((i - start_idx - quarter * 2) - quarter) / quarter
            target_price = base_price - (base_price - trough_price) * (1 - progress)
            data.iloc[i, data.columns.get_loc('Close')] = target_price
            self._adjust_ohlc_consistency(data, i)
        
        return data
    
    def _adjust_ohlc_consistency(self, data: pd.DataFrame, idx: int):
        """Ensure OHLC data is consistent (H >= max(O,C), L <= min(O,C))."""
        close_price = data.iloc[idx]['Close']
        
        if idx > 0:
            open_price = data.iloc[idx-1]['Close']  # Open = previous close
        else:
            open_price = close_price
        
        # Set open
        data.iloc[idx, data.columns.get_loc('Open')] = open_price
        
        # Adjust high and low
        high_price = max(open_price, close_price) * (1 + abs(self.random_state.normal(0, 0.001)))
        low_price = min(open_price, close_price) * (1 - abs(self.random_state.normal(0, 0.001)))
        
        data.iloc[idx, data.columns.get_loc('High')] = high_price
        data.iloc[idx, data.columns.get_loc('Low')] = low_price


# Convenience function
def generate_sample_data(symbol: str = "DJ30", days: int = 90) -> pd.DataFrame:
    """Generate sample market data for testing."""
    config = SimulationConfig(symbol=symbol)
    simulator = MarketDataSimulator(config)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate base data
    data = simulator.generate_ohlc_data(start_date, end_date)
    
    # Add interesting patterns for testing
    data = simulator.add_fractal_patterns(data, num_patterns=30)
    
    logger.info(f"Generated {len(data)} bars of sample {symbol} data")
    return data