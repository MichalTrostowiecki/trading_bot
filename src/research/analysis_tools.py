"""
Interactive Analysis Tools
Comprehensive market analysis and research utilities for strategy development.
"""

import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats, signal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from src.data import get_historical_data, TimeFrame, validate_data
from src.monitoring import get_logger

logger = get_logger("analysis_tools")


@dataclass
class AnalysisResult:
    """Container for analysis results."""
    name: str
    symbol: str
    timeframe: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_metric(self, key: str, value: Any, description: str = ""):
        """Add a metric to the analysis result."""
        self.data[key] = value
        if description:
            self.metadata[f"{key}_description"] = description
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics."""
        summary = {
            'analysis': self.name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp
        }
        summary.update(self.data)
        return summary


class TechnicalIndicators:
    """Technical analysis indicators collection."""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands."""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev),
            'width': (sma + (std * std_dev)) - (sma - (std * std_dev)),
            'position': (data - sma) / std
        }
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)."""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }


class MarketStructureAnalyzer:
    """Market structure and trend analysis."""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_trend(self, data: pd.DataFrame, period: int = 20) -> AnalysisResult:
        """Comprehensive trend analysis."""
        result = AnalysisResult(
            name="trend_analysis",
            symbol=data.get('symbol', 'unknown')[0] if 'symbol' in data.columns else 'unknown',
            timeframe="unknown"
        )
        
        close_price = data['Close'] if 'Close' in data.columns else data['close']
        
        # Moving averages
        sma_short = self.indicators.sma(close_price, period // 2)
        sma_long = self.indicators.sma(close_price, period)
        ema_short = self.indicators.ema(close_price, period // 2)
        
        # Trend direction
        trend_sma = np.where(sma_short > sma_long, 1, -1)
        trend_strength = abs(sma_short - sma_long) / sma_long * 100
        
        # Price position relative to moving averages
        price_vs_sma = (close_price - sma_long) / sma_long * 100
        
        # Trend consistency (how often price stays above/below MA)
        above_ma = (close_price > sma_long).rolling(window=period).mean()
        
        # Recent trend (last 10 periods)
        recent_trend = trend_sma.tail(10).mean()
        recent_strength = trend_strength.tail(10).mean()
        
        result.add_metric('current_trend', trend_sma.iloc[-1], "Current trend direction (1=up, -1=down)")
        result.add_metric('trend_strength', trend_strength.iloc[-1], "Trend strength percentage")
        result.add_metric('recent_trend_consistency', recent_trend, "Recent trend consistency (-1 to 1)")
        result.add_metric('recent_trend_strength', recent_strength, "Recent average trend strength")
        result.add_metric('price_vs_ma', price_vs_sma.iloc[-1], "Price position vs moving average (%)")
        result.add_metric('trend_consistency', above_ma.iloc[-1], "Trend consistency (0-1)")
        
        # Add technical data
        result.metadata['sma_short'] = sma_short
        result.metadata['sma_long'] = sma_long
        result.metadata['ema_short'] = ema_short
        result.metadata['trend_direction'] = trend_sma
        result.metadata['trend_strength_series'] = trend_strength
        
        return result
    
    def analyze_volatility(self, data: pd.DataFrame, period: int = 20) -> AnalysisResult:
        """Volatility analysis."""
        result = AnalysisResult(
            name="volatility_analysis", 
            symbol=data.get('symbol', 'unknown')[0] if 'symbol' in data.columns else 'unknown',
            timeframe="unknown"
        )
        
        close_price = data['Close'] if 'Close' in data.columns else data['close']
        high_price = data['High'] if 'High' in data.columns else data['high']
        low_price = data['Low'] if 'Low' in data.columns else data['low']
        
        # Price-based volatility
        returns = close_price.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        
        # Average True Range
        atr = self.indicators.atr(high_price, low_price, close_price, period)
        atr_percent = atr / close_price * 100
        
        # Bollinger Bands
        bb = self.indicators.bollinger_bands(close_price, period)
        bb_width = bb['width'] / bb['middle'] * 100
        bb_position = bb['position']
        
        # High-Low range volatility
        hl_range = (high_price - low_price) / close_price * 100
        hl_volatility = hl_range.rolling(window=period).mean()
        
        # Volatility percentiles
        vol_percentile = volatility.rolling(window=period*5).rank(pct=True)
        
        result.add_metric('current_volatility', volatility.iloc[-1], "Current annualized volatility")
        result.add_metric('atr_percent', atr_percent.iloc[-1], "ATR as percentage of price")
        result.add_metric('bb_width_percent', bb_width.iloc[-1], "Bollinger Band width percentage")
        result.add_metric('bb_position', bb_position.iloc[-1], "Position within Bollinger Bands")
        result.add_metric('hl_volatility', hl_volatility.iloc[-1], "High-Low range volatility")
        result.add_metric('volatility_percentile', vol_percentile.iloc[-1], "Volatility percentile (0-1)")
        
        # Volatility regime
        vol_regime = "high" if vol_percentile.iloc[-1] > 0.8 else "low" if vol_percentile.iloc[-1] < 0.2 else "normal"
        result.add_metric('volatility_regime', vol_regime, "Current volatility regime")
        
        # Add technical data
        result.metadata['volatility_series'] = volatility
        result.metadata['atr_series'] = atr
        result.metadata['bollinger_bands'] = bb
        result.metadata['returns'] = returns
        
        return result
    
    def analyze_momentum(self, data: pd.DataFrame) -> AnalysisResult:
        """Momentum analysis."""
        result = AnalysisResult(
            name="momentum_analysis",
            symbol=data.get('symbol', 'unknown')[0] if 'symbol' in data.columns else 'unknown',
            timeframe="unknown"
        )
        
        close_price = data['Close'] if 'Close' in data.columns else data['close']
        high_price = data['High'] if 'High' in data.columns else data['high']
        low_price = data['Low'] if 'Low' in data.columns else data['low']
        
        # RSI
        rsi = self.indicators.rsi(close_price)
        
        # MACD
        macd_data = self.indicators.macd(close_price)
        
        # Stochastic
        stoch = self.indicators.stochastic(high_price, low_price, close_price)
        
        # Price momentum (rate of change)
        roc_10 = close_price.pct_change(10) * 100
        roc_20 = close_price.pct_change(20) * 100
        
        # Momentum divergence (price vs momentum)
        price_peaks = signal.find_peaks(close_price.values)[0]
        rsi_peaks = signal.find_peaks(rsi.values)[0]
        
        result.add_metric('rsi', rsi.iloc[-1], "Relative Strength Index")
        result.add_metric('macd', macd_data['macd'].iloc[-1], "MACD line")
        result.add_metric('macd_signal', macd_data['signal'].iloc[-1], "MACD signal line")
        result.add_metric('macd_histogram', macd_data['histogram'].iloc[-1], "MACD histogram")
        result.add_metric('stoch_k', stoch['k'].iloc[-1], "Stochastic %K")
        result.add_metric('stoch_d', stoch['d'].iloc[-1], "Stochastic %D")
        result.add_metric('roc_10', roc_10.iloc[-1], "10-period rate of change")
        result.add_metric('roc_20', roc_20.iloc[-1], "20-period rate of change")
        
        # Momentum signals
        rsi_overbought = rsi.iloc[-1] > 70
        rsi_oversold = rsi.iloc[-1] < 30
        macd_bullish = macd_data['macd'].iloc[-1] > macd_data['signal'].iloc[-1]
        stoch_overbought = stoch['k'].iloc[-1] > 80
        stoch_oversold = stoch['k'].iloc[-1] < 20
        
        result.add_metric('rsi_overbought', rsi_overbought, "RSI indicates overbought")
        result.add_metric('rsi_oversold', rsi_oversold, "RSI indicates oversold")
        result.add_metric('macd_bullish', macd_bullish, "MACD bullish crossover")
        result.add_metric('stoch_overbought', stoch_overbought, "Stochastic overbought")
        result.add_metric('stoch_oversold', stoch_oversold, "Stochastic oversold")
        
        # Add technical data
        result.metadata['rsi_series'] = rsi
        result.metadata['macd_data'] = macd_data
        result.metadata['stochastic'] = stoch
        
        return result


class PatternDetector:
    """Chart pattern detection and analysis."""
    
    def detect_support_resistance(self, data: pd.DataFrame, window: int = 20, 
                                 min_touches: int = 2) -> AnalysisResult:
        """Detect support and resistance levels."""
        result = AnalysisResult(
            name="support_resistance",
            symbol=data.get('symbol', 'unknown')[0] if 'symbol' in data.columns else 'unknown',
            timeframe="unknown"
        )
        
        high_price = data['High'] if 'High' in data.columns else data['high']
        low_price = data['Low'] if 'Low' in data.columns else data['low']
        close_price = data['Close'] if 'Close' in data.columns else data['close']
        
        # Find local maxima and minima
        high_peaks = signal.find_peaks(high_price.values, distance=window//2)[0]
        low_peaks = signal.find_peaks(-low_price.values, distance=window//2)[0]
        
        # Resistance levels (from highs)
        resistance_levels = []
        for peak in high_peaks:
            level = high_price.iloc[peak]
            touches = self._count_touches(high_price, level, tolerance=0.002)
            if touches >= min_touches:
                resistance_levels.append({
                    'level': level,
                    'touches': touches,
                    'index': peak,
                    'timestamp': high_price.index[peak]
                })
        
        # Support levels (from lows)
        support_levels = []
        for peak in low_peaks:
            level = low_price.iloc[peak]
            touches = self._count_touches(low_price, level, tolerance=0.002)
            if touches >= min_touches:
                support_levels.append({
                    'level': level,
                    'touches': touches,
                    'index': peak,
                    'timestamp': low_price.index[peak]
                })
        
        # Find nearest levels to current price
        current_price = close_price.iloc[-1]
        
        nearest_resistance = None
        nearest_support = None
        
        if resistance_levels:
            resistance_above = [r for r in resistance_levels if r['level'] > current_price]
            if resistance_above:
                nearest_resistance = min(resistance_above, key=lambda x: x['level'])
        
        if support_levels:
            support_below = [s for s in support_levels if s['level'] < current_price]
            if support_below:
                nearest_support = max(support_below, key=lambda x: x['level'])
        
        result.add_metric('resistance_levels_count', len(resistance_levels), "Number of resistance levels found")
        result.add_metric('support_levels_count', len(support_levels), "Number of support levels found")
        
        if nearest_resistance:
            result.add_metric('nearest_resistance', nearest_resistance['level'], "Nearest resistance level")
            result.add_metric('resistance_distance', 
                            (nearest_resistance['level'] - current_price) / current_price * 100,
                            "Distance to resistance (%)")
        
        if nearest_support:
            result.add_metric('nearest_support', nearest_support['level'], "Nearest support level")
            result.add_metric('support_distance',
                            (current_price - nearest_support['level']) / current_price * 100,
                            "Distance to support (%)")
        
        result.metadata['resistance_levels'] = resistance_levels
        result.metadata['support_levels'] = support_levels
        result.metadata['high_peaks'] = high_peaks
        result.metadata['low_peaks'] = low_peaks
        
        return result
    
    def _count_touches(self, series: pd.Series, level: float, tolerance: float = 0.002) -> int:
        """Count how many times price touched a level within tolerance."""
        level_range = level * tolerance
        touches = ((series >= level - level_range) & (series <= level + level_range)).sum()
        return touches
    
    def detect_fractals(self, data: pd.DataFrame, periods: int = 5) -> AnalysisResult:
        """Detect fractal patterns."""
        result = AnalysisResult(
            name="fractals",
            symbol=data.get('symbol', 'unknown')[0] if 'symbol' in data.columns else 'unknown',
            timeframe="unknown"
        )
        
        high_price = data['High'] if 'High' in data.columns else data['high']
        low_price = data['Low'] if 'Low' in data.columns else data['low']
        
        # Up fractals (highest high in the middle)
        up_fractals = []
        for i in range(periods, len(high_price) - periods):
            current_high = high_price.iloc[i]
            left_highs = high_price.iloc[i-periods:i]
            right_highs = high_price.iloc[i+1:i+periods+1]
            
            if (current_high > left_highs.max()) and (current_high > right_highs.max()):
                up_fractals.append({
                    'index': i,
                    'timestamp': high_price.index[i],
                    'price': current_high,
                    'type': 'up'
                })
        
        # Down fractals (lowest low in the middle)
        down_fractals = []
        for i in range(periods, len(low_price) - periods):
            current_low = low_price.iloc[i]
            left_lows = low_price.iloc[i-periods:i]
            right_lows = low_price.iloc[i+1:i+periods+1]
            
            if (current_low < left_lows.min()) and (current_low < right_lows.min()):
                down_fractals.append({
                    'index': i,
                    'timestamp': low_price.index[i],
                    'price': current_low,
                    'type': 'down'
                })
        
        result.add_metric('up_fractals_count', len(up_fractals), "Number of up fractals")
        result.add_metric('down_fractals_count', len(down_fractals), "Number of down fractals")
        
        # Recent fractals (last 50 periods)
        recent_up = [f for f in up_fractals if f['index'] >= len(high_price) - 50]
        recent_down = [f for f in down_fractals if f['index'] >= len(low_price) - 50]
        
        result.add_metric('recent_up_fractals', len(recent_up), "Recent up fractals (last 50 periods)")
        result.add_metric('recent_down_fractals', len(recent_down), "Recent down fractals (last 50 periods)")
        
        result.metadata['up_fractals'] = up_fractals
        result.metadata['down_fractals'] = down_fractals
        result.metadata['periods'] = periods
        
        return result


class MarketAnalyzer:
    """Comprehensive market analysis orchestrator."""
    
    def __init__(self):
        self.structure_analyzer = MarketStructureAnalyzer()
        self.pattern_detector = PatternDetector()
        self.indicators = TechnicalIndicators()
    
    def comprehensive_analysis(self, symbol: str, timeframe: TimeFrame,
                             days_back: int = 365) -> Dict[str, AnalysisResult]:
        """Perform comprehensive market analysis."""
        logger.info(f"Starting comprehensive analysis for {symbol} {timeframe.name}")
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        data = get_historical_data(symbol, timeframe, start_date, end_date)
        
        if data is None or data.empty:
            logger.error(f"No data available for {symbol} {timeframe.name}")
            return {}
        
        # Validate data quality
        validation_result = validate_data(data, symbol)
        if not validation_result.is_valid:
            logger.warning(f"Data quality issues for {symbol}: {validation_result.get_summary()}")
        
        results = {}
        
        try:
            # Trend analysis
            results['trend'] = self.structure_analyzer.analyze_trend(data)
            results['trend'].symbol = symbol
            results['trend'].timeframe = timeframe.name
            
            # Volatility analysis  
            results['volatility'] = self.structure_analyzer.analyze_volatility(data)
            results['volatility'].symbol = symbol
            results['volatility'].timeframe = timeframe.name
            
            # Momentum analysis
            results['momentum'] = self.structure_analyzer.analyze_momentum(data)
            results['momentum'].symbol = symbol
            results['momentum'].timeframe = timeframe.name
            
            # Support/Resistance
            results['support_resistance'] = self.pattern_detector.detect_support_resistance(data)
            results['support_resistance'].symbol = symbol
            results['support_resistance'].timeframe = timeframe.name
            
            # Fractals
            results['fractals'] = self.pattern_detector.detect_fractals(data)
            results['fractals'].symbol = symbol
            results['fractals'].timeframe = timeframe.name
            
            logger.info(f"Comprehensive analysis completed for {symbol} {timeframe.name}")
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
        
        return results
    
    def quick_analysis(self, symbol: str, timeframe: TimeFrame) -> AnalysisResult:
        """Quick market analysis with key metrics."""
        logger.info(f"Starting quick analysis for {symbol} {timeframe.name}")
        
        # Get recent data (last 100 periods)
        data = get_historical_data(symbol, timeframe)
        if data is not None and len(data) > 100:
            data = data.tail(100)
        
        if data is None or data.empty:
            logger.error(f"No data available for {symbol} {timeframe.name}")
            return AnalysisResult("quick_analysis", symbol, timeframe.name)
        
        result = AnalysisResult("quick_analysis", symbol, timeframe.name)
        
        try:
            close_price = data['Close'] if 'Close' in data.columns else data['close']
            
            # Current price info
            current_price = close_price.iloc[-1]
            price_change = close_price.pct_change().iloc[-1] * 100
            
            # Basic indicators
            sma_20 = self.indicators.sma(close_price, 20).iloc[-1]
            rsi = self.indicators.rsi(close_price).iloc[-1]
            
            # Volatility
            volatility = close_price.pct_change().rolling(20).std().iloc[-1] * 100
            
            result.add_metric('current_price', current_price, "Current price")
            result.add_metric('price_change_percent', price_change, "Price change (%)")
            result.add_metric('sma_20', sma_20, "20-period SMA")
            result.add_metric('price_vs_sma', (current_price - sma_20) / sma_20 * 100, "Price vs SMA (%)")
            result.add_metric('rsi', rsi, "RSI")
            result.add_metric('volatility', volatility, "20-period volatility (%)")
            
            # Market bias
            bias = "bullish" if current_price > sma_20 and rsi < 70 else "bearish" if current_price < sma_20 and rsi > 30 else "neutral"
            result.add_metric('market_bias', bias, "Market bias assessment")
            
            logger.info(f"Quick analysis completed for {symbol} {timeframe.name}")
            
        except Exception as e:
            logger.error(f"Error in quick analysis for {symbol}: {e}")
        
        return result


# Global market analyzer instance
market_analyzer = MarketAnalyzer()

# Convenience functions
def analyze_symbol(symbol: str, timeframe: TimeFrame, comprehensive: bool = True) -> Union[Dict[str, AnalysisResult], AnalysisResult]:
    """Analyze a symbol with specified timeframe."""
    if comprehensive:
        return market_analyzer.comprehensive_analysis(symbol, timeframe)
    else:
        return market_analyzer.quick_analysis(symbol, timeframe)

def get_technical_indicators(data: pd.DataFrame) -> Dict[str, pd.Series]:
    """Get common technical indicators for data."""
    indicators = TechnicalIndicators()
    close_price = data['Close'] if 'Close' in data.columns else data['close']
    
    return {
        'sma_20': indicators.sma(close_price, 20),
        'ema_20': indicators.ema(close_price, 20),
        'rsi': indicators.rsi(close_price),
        'bollinger_bands': indicators.bollinger_bands(close_price),
        'macd': indicators.macd(close_price)
    }