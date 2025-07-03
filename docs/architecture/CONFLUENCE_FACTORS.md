# Confluence Factors Library - Complete Reference

**Document Version**: 1.0  
**Created**: 2025-07-03  
**Last Updated**: 2025-07-03  
**Status**: Foundation Specification

## Overview

This document provides the complete specification for the confluence factor library used in the Fibonacci trading strategy. Each factor is designed as an independent, testable module that can be combined with others to enhance signal quality and trading performance.

## Architecture Principles

### 1. Factor Independence 🧩
- Each factor operates independently of others
- No dependencies between factors (except base data requirements)
- Plug-and-play architecture allows easy addition/removal
- Standard interface ensures consistency across all factors

### 2. Extensibility by Design 🔧
- New factors can be added without modifying existing code
- Custom factor development supported through base class inheritance
- Configuration-driven factor parameters
- Runtime factor enabling/disabling without system restart

### 3. Scientific Validation 📊
- Every factor must demonstrate statistical significance
- A/B testing framework for factor comparison
- Out-of-sample validation required for production deployment
- Performance degradation monitoring in live trading

---

## Base Factor Interface

### Standard Factor Class
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ConfluenceDirection(Enum):
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

@dataclass
class ConfluenceScore:
    """Standardized factor output"""
    strength: float  # 0.0 to 1.0 (confidence level)
    direction: ConfluenceDirection  # Bullish, Bearish, or Neutral
    reason: str  # Human-readable explanation
    raw_value: Optional[float] = None  # Original calculation value
    metadata: Optional[Dict[str, Any]] = None  # Additional context

class ConfluenceFactor(ABC):
    """Base class for all confluence factors"""
    
    def __init__(self, name: str, enabled: bool = True, weight: float = 1.0):
        self.name = name
        self.enabled = enabled
        self.weight = weight
        self.version = "1.0"
        self.author = "Trading Bot System"
        self.last_calibrated = None
    
    @abstractmethod
    def evaluate(self, market_data: 'MarketData') -> ConfluenceScore:
        """
        Evaluate factor for current market conditions
        
        Args:
            market_data: Current and historical market data
            
        Returns:
            ConfluenceScore with strength (0.0-1.0), direction, and reasoning
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return human-readable factor description"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return configurable parameters with current values"""
        pass
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Update factor parameters (override in subclass if needed)"""
        pass
    
    def validate_data_requirements(self, market_data: 'MarketData') -> bool:
        """Check if required data is available for evaluation"""
        return True
    
    def get_computation_cost(self) -> float:
        """Return estimated computation time in milliseconds"""
        return 1.0  # Default 1ms
```

---

## Category 1: Time-Based Factors 🕐

### Market Session Factors

#### 1. LondonSessionFactor
```python
class LondonSessionFactor(ConfluenceFactor):
    """Enhanced volatility and breakout probability during London session"""
    
    def __init__(self, session_start: str = "08:00", session_end: str = "17:00", 
                 timezone: str = "Europe/London", volatility_multiplier: float = 1.5):
        super().__init__("london_session")
        self.session_start = session_start
        self.session_end = session_end
        self.timezone = timezone
        self.volatility_multiplier = volatility_multiplier
    
    def evaluate(self, market_data: 'MarketData') -> ConfluenceScore:
        """
        Evaluate based on:
        - Current time in London timezone
        - Historical volatility patterns during London session
        - Volume surge indicators during session start
        """
        # Implementation details...
        pass
    
    def get_description(self) -> str:
        return "Identifies enhanced volatility and breakout opportunities during London trading session"
```

**Key Features:**
- **Session Detection**: Automatic timezone conversion and session identification
- **Volatility Analysis**: Historical volatility patterns during London hours
- **Breakout Probability**: Statistical analysis of breakout success rates
- **Volume Correlation**: Session volume patterns and momentum confirmation

#### 2. NewYorkSessionFactor
```python
class NewYorkSessionFactor(ConfluenceFactor):
    """Momentum continuation and trend acceleration during NY session"""
    
    def __init__(self, pre_market_start: str = "13:00", main_session_end: str = "22:00",
                 overlap_bonus: float = 1.3):
        super().__init__("newyork_session")
        self.pre_market_start = pre_market_start
        self.main_session_end = main_session_end
        self.overlap_bonus = overlap_bonus  # London-NY overlap multiplier
```

**Capabilities:**
- **Trend Continuation**: NY session momentum analysis
- **Overlap Enhancement**: London-NY session overlap detection
- **Economic News Impact**: Integration with news event timing
- **Institution Flow**: Large player activity detection

#### 3. AsianSessionFactor
```python
class AsianSessionFactor(ConfluenceFactor):
    """Range-bound behavior and mean reversion opportunities"""
    
    def __init__(self, consolidation_threshold: float = 0.3, 
                 range_breakout_confirmation: int = 3):
        super().__init__("asian_session")
        self.consolidation_threshold = consolidation_threshold
        self.range_breakout_confirmation = range_breakout_confirmation
```

### Temporal Event Factors

#### 4. EconomicNewsFactor
```python
class EconomicNewsFactor(ConfluenceFactor):
    """News event impact analysis and volatility prediction"""
    
    def __init__(self, news_calendar_source: str = "forexfactory",
                 impact_levels: Dict[str, float] = None,
                 time_windows: Dict[str, int] = None):
        super().__init__("economic_news")
        self.news_calendar_source = news_calendar_source
        self.impact_levels = impact_levels or {
            "high": 0.8, "medium": 0.5, "low": 0.2
        }
        self.time_windows = time_windows or {
            "pre_event": 30,  # minutes before
            "post_event": 60  # minutes after
        }
```

**Advanced Features:**
- **News Calendar Integration**: Real-time economic calendar data
- **Impact Classification**: High/Medium/Low impact event categorization
- **Currency-Specific Events**: Factor relevance by currency pair
- **Surprise Factor**: Actual vs expected news impact analysis

---

## Category 2: Price-Level Factors 📈

### Daily Reference Points

#### 5. DayOpenPriceFactor
```python
class DayOpenPriceFactor(ConfluenceFactor):
    """Market bias relative to daily opening price"""
    
    def __init__(self, significance_threshold: float = 0.1,
                 momentum_confirmation_bars: int = 3):
        super().__init__("day_open_price")
        self.significance_threshold = significance_threshold  # % move from open
        self.momentum_confirmation_bars = momentum_confirmation_bars
    
    def evaluate(self, market_data: 'MarketData') -> ConfluenceScore:
        """
        Analysis includes:
        - Current price vs day open percentage
        - Intraday momentum direction
        - Historical day open behavior patterns
        - Gap analysis (weekend/overnight gaps)
        """
        current_price = market_data.current_bar.close
        day_open = market_data.get_day_open()
        
        price_delta_percent = (current_price - day_open) / day_open
        
        if abs(price_delta_percent) < self.significance_threshold:
            return ConfluenceScore(
                strength=0.3,
                direction=ConfluenceDirection.NEUTRAL,
                reason="Price near day open - neutral bias"
            )
        
        # Determine bullish/bearish bias
        if price_delta_percent > 0:
            strength = min(abs(price_delta_percent) * 2, 1.0)
            return ConfluenceScore(
                strength=strength,
                direction=ConfluenceDirection.BULLISH,
                reason=f"Price {price_delta_percent:.1%} above day open"
            )
        else:
            strength = min(abs(price_delta_percent) * 2, 1.0)
            return ConfluenceScore(
                strength=strength,
                direction=ConfluenceDirection.BEARISH,
                reason=f"Price {abs(price_delta_percent):.1%} below day open"
            )
```

#### 6. PreviousCloseFactor
```python
class PreviousCloseFactor(ConfluenceFactor):
    """Gap analysis and continuation vs mean reversion signals"""
    
    def __init__(self, gap_threshold: float = 0.05,
                 continuation_confirmation_period: int = 5):
        super().__init__("previous_close")
        self.gap_threshold = gap_threshold
        self.continuation_confirmation_period = continuation_confirmation_period
```

### Multi-Timeframe Reference Levels

#### 7. WeeklyLevelsFactor
```python
class WeeklyLevelsFactor(ConfluenceFactor):
    """Weekly high/low and pivot level confluence"""
    
    def __init__(self, lookback_weeks: int = 4,
                 proximity_threshold: float = 0.001):  # 10 pips for major pairs
        super().__init__("weekly_levels")
        self.lookback_weeks = lookback_weeks
        self.proximity_threshold = proximity_threshold
```

#### 8. VWAPFactor
```python
class VWAPFactor(ConfluenceFactor):
    """Volume-Weighted Average Price deviation analysis"""
    
    def __init__(self, vwap_period: str = "daily",
                 deviation_bands: List[float] = None):
        super().__init__("vwap")
        self.vwap_period = vwap_period  # daily, weekly, monthly
        self.deviation_bands = deviation_bands or [0.5, 1.0, 1.5, 2.0]
```

---

## Category 3: Technical Indicator Factors 📊

### Momentum Indicators

#### 9. RSIConfluenceFactor
```python
class RSIConfluenceFactor(ConfluenceFactor):
    """RSI overbought/oversold conditions with Fibonacci confluence"""
    
    def __init__(self, rsi_period: int = 14,
                 overbought_level: float = 70,
                 oversold_level: float = 30,
                 divergence_detection: bool = True):
        super().__init__("rsi_confluence")
        self.rsi_period = rsi_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.divergence_detection = divergence_detection
    
    def evaluate(self, market_data: 'MarketData') -> ConfluenceScore:
        """
        Advanced RSI analysis:
        - Current RSI level vs overbought/oversold zones
        - RSI divergence detection (price vs RSI direction)
        - Multi-timeframe RSI confluence
        - RSI trend analysis (rising/falling RSI)
        """
        # Implementation includes sophisticated RSI analysis
        pass
```

#### 10. MACDFactor
```python
class MACDFactor(ConfluenceFactor):
    """MACD trend confirmation and momentum analysis"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26,
                 signal_period: int = 9, histogram_analysis: bool = True):
        super().__init__("macd")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.histogram_analysis = histogram_analysis
```

### Volume Analysis

#### 11. VolumeSurgeFactor
```python
class VolumeSurgeFactor(ConfluenceFactor):
    """Unusual volume detection for breakout confirmation"""
    
    def __init__(self, volume_ma_period: int = 20,
                 surge_multiplier: float = 2.0,
                 confirmation_bars: int = 2):
        super().__init__("volume_surge")
        self.volume_ma_period = volume_ma_period
        self.surge_multiplier = surge_multiplier
        self.confirmation_bars = confirmation_bars
```

---

## Category 4: Market Structure Factors 🏗️

### Trend Analysis

#### 12. TrendStrengthFactor
```python
class TrendStrengthFactor(ConfluenceFactor):
    """ADX-based trend strength measurement"""
    
    def __init__(self, adx_period: int = 14,
                 strong_trend_threshold: float = 25,
                 very_strong_threshold: float = 40):
        super().__init__("trend_strength")
        self.adx_period = adx_period
        self.strong_trend_threshold = strong_trend_threshold
        self.very_strong_threshold = very_strong_threshold
```

#### 13. BreakoutConfirmationFactor
```python
class BreakoutConfirmationFactor(ConfluenceFactor):
    """Distinguishes valid breakouts from false breakouts"""
    
    def __init__(self, volume_confirmation: bool = True,
                 retest_analysis: bool = True,
                 momentum_threshold: float = 0.02):
        super().__init__("breakout_confirmation")
        self.volume_confirmation = volume_confirmation
        self.retest_analysis = retest_analysis
        self.momentum_threshold = momentum_threshold
```

### Market Regime Detection

#### 14. VolatilityRegimeFactor
```python
class VolatilityRegimeFactor(ConfluenceFactor):
    """Volatility environment classification and adaptation"""
    
    def __init__(self, volatility_lookback: int = 20,
                 low_vol_threshold: float = 0.5,
                 high_vol_threshold: float = 2.0):
        super().__init__("volatility_regime")
        self.volatility_lookback = volatility_lookback
        self.low_vol_threshold = low_vol_threshold
        self.high_vol_threshold = high_vol_threshold
```

---

## Factor Combination Strategies

### Combination Methods

#### 1. Weighted Average Method
```python
class WeightedAverageCombiner:
    """Combines factors using weighted average approach"""
    
    def combine_factors(self, factor_scores: List[ConfluenceScore], 
                       weights: Dict[str, float]) -> ConfluenceScore:
        """
        Weighted combination algorithm:
        1. Calculate weighted strength average
        2. Determine consensus direction
        3. Generate combined reasoning
        """
        pass
```

#### 2. Threshold Method
```python
class ThresholdCombiner:
    """Requires minimum number of factors to agree"""
    
    def combine_factors(self, factor_scores: List[ConfluenceScore],
                       min_factors: int = 3,
                       min_strength: float = 0.6) -> ConfluenceScore:
        """
        Threshold-based combination:
        1. Count factors above minimum strength
        2. Require minimum consensus
        3. Signal only when threshold met
        """
        pass
```

#### 3. Machine Learning Method
```python
class MLCombiner:
    """Uses trained ML model to combine factors optimally"""
    
    def __init__(self, model_path: str, feature_scaler_path: str):
        self.model = self.load_model(model_path)
        self.scaler = self.load_scaler(feature_scaler_path)
    
    def combine_factors(self, factor_scores: List[ConfluenceScore]) -> ConfluenceScore:
        """
        ML-based combination:
        1. Extract features from factor scores
        2. Scale features using trained scaler
        3. Predict optimal signal using trained model
        """
        pass
```

---

## Factor Testing Framework

### Performance Benchmarks

#### Statistical Requirements
```python
class FactorValidationCriteria:
    """Minimum performance standards for factor acceptance"""
    
    MIN_STATISTICAL_SIGNIFICANCE = 0.95  # 95% confidence
    MIN_SHARPE_IMPROVEMENT = 0.1  # 10% improvement
    MAX_DRAWDOWN_INCREASE = 0.05  # 5% maximum drawdown increase
    MIN_SAMPLE_SIZE = 100  # Minimum trades for validation
    MIN_TEST_PERIOD_DAYS = 90  # Minimum out-of-sample test period
```

#### Testing Protocols
```python
class FactorTestingProtocol:
    """Standardized testing procedures"""
    
    def run_factor_validation(self, factor: ConfluenceFactor) -> ValidationReport:
        """
        Complete factor validation process:
        1. Data requirement validation
        2. Computational cost assessment
        3. Baseline performance comparison
        4. Statistical significance testing
        5. Out-of-sample validation
        6. Robustness testing across market regimes
        """
        pass
    
    def run_combination_test(self, factors: List[str]) -> CombinationReport:
        """
        Factor combination testing:
        1. Individual factor performance
        2. Pairwise correlation analysis
        3. Optimal weight discovery
        4. Combined performance measurement
        5. Risk-adjusted return analysis
        """
        pass
```

---

## Implementation Guidelines

### Adding New Factors

#### Step 1: Factor Development
```python
# 1. Create new factor class inheriting from ConfluenceFactor
class CustomMarketSentimentFactor(ConfluenceFactor):
    def __init__(self, sentiment_source: str = "fear_greed_index"):
        super().__init__("market_sentiment")
        self.sentiment_source = sentiment_source
    
    def evaluate(self, market_data: 'MarketData') -> ConfluenceScore:
        # Custom implementation
        pass
    
    def get_description(self) -> str:
        return "Market sentiment analysis using fear/greed index"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {"sentiment_source": self.sentiment_source}
```

#### Step 2: Factor Registration
```python
# 2. Register factor with the system
factor_registry = FactorRegistry()
factor_registry.register_factor(CustomMarketSentimentFactor)
```

#### Step 3: Initial Testing
```python
# 3. Run initial validation tests
tester = FactorTester()
validation_result = tester.validate_new_factor(CustomMarketSentimentFactor())

if validation_result.passed:
    print("Factor passed initial validation")
    # Proceed to comprehensive testing
else:
    print(f"Factor failed validation: {validation_result.failure_reasons}")
```

### Configuration Management

#### Factor Configuration File
```yaml
# factors_config.yaml
factors:
  base_fibonacci:
    enabled: true
    weight: 1.0
    parameters: {}
  
  london_session:
    enabled: true
    weight: 0.3
    parameters:
      session_start: "08:00"
      session_end: "17:00"
      volatility_multiplier: 1.5
  
  rsi_confluence:
    enabled: true
    weight: 0.4
    parameters:
      rsi_period: 14
      overbought_level: 70
      oversold_level: 30
  
  custom_sentiment:
    enabled: false  # Disabled for testing
    weight: 0.2
    parameters:
      sentiment_source: "fear_greed_index"

combination_strategy:
  method: "weighted_average"  # Options: weighted_average, threshold, ml_model
  min_fibonacci_strength: 0.5  # Minimum base signal strength
  require_fibonacci: true  # Base signal always required
```

---

## Future Development Roadmap

### Phase 1: Core Factor Library (Weeks 7-8) 🎯
- Implement 10-15 essential factors
- Basic combination strategies
- Manual factor testing interface
- Performance measurement framework

### Phase 2: Advanced Testing (Weeks 9-10)
- Automated A/B testing system
- Statistical significance validation
- Factor importance ranking
- Optimization algorithms

### Phase 3: Machine Learning Integration (Weeks 11-12)
- ML-based factor combination
- Automated factor discovery
- Non-linear factor relationships
- Real-time factor adaptation

### Phase 4: Production Optimization (Future)
- Ultra-low latency factor evaluation
- Distributed factor testing
- Real-time performance monitoring
- Factor decay detection and replacement

---

## Quality Assurance Standards

### Code Quality Requirements
- **Unit Tests**: 100% coverage for all factor classes
- **Integration Tests**: Factor combination testing
- **Performance Tests**: Computational cost validation
- **Documentation**: Complete API documentation and examples

### Statistical Validation
- **Backtesting**: Minimum 2 years of out-of-sample data
- **Cross-Validation**: Time-series split validation
- **Regime Testing**: Performance across bull/bear/sideways markets
- **Significance Testing**: Statistical significance validation

### Production Readiness
- **Error Handling**: Graceful degradation when data unavailable
- **Monitoring**: Real-time performance tracking
- **Alerting**: Factor performance degradation alerts
- **Rollback**: Quick factor disable capability

---

*This document serves as the complete specification for the confluence factor system, providing the foundation for building a world-class quantitative trading strategy with unlimited extensibility and scientific validation.*