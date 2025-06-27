# Core Strategy Specification - Fibonacci Retracement Continuation Strategy

## Overview
This document defines the core Fibonacci retracement continuation strategy that identifies major market swings and enters trades in the direction of the dominant swing using Fibonacci retracement levels.

## Strategy Logic

### Core Concept
The strategy is based on the principle that markets tend to continue in the direction of the dominant trend after retracing to key Fibonacci levels. By identifying the most significant recent swing and waiting for retracements, we can enter high-probability continuation trades.

### Strategy Flow
```
1. Analyze Recent Price Action (X candles lookback)
   ↓
2. Identify All Major Swings Using Fractals
   ↓
3. Determine Dominant Swing (largest/most recent)
   ↓
4. Calculate Fibonacci Retracement Levels
   ↓
5. Wait for Price to Retrace to Key Levels (38.2%-61.8%)
   ↓
6. Enter Trade in Direction of Dominant Swing
   ↓
7. Target Fibonacci Extension Levels for Exits
```

## Detailed Implementation

### 1. Swing Identification System

#### Fractal Detection
```python
class FractalDetector:
    def __init__(self, bars_range=2):
        self.bars_range = bars_range
    
    def detect_fractals(self, ohlc_data):
        """
        Detect swing highs and lows using fractal analysis
        
        Up Fractal: high[i] >= max(high[i-range:i+range+1])
        Down Fractal: low[i] <= min(low[i-range:i+range+1])
        """
        up_fractals = []
        down_fractals = []
        
        for i in range(self.bars_range, len(ohlc_data) - self.bars_range):
            # Check for up fractal (swing high)
            if self._is_up_fractal(ohlc_data, i):
                up_fractals.append({
                    'timestamp': ohlc_data.index[i],
                    'price': ohlc_data.iloc[i]['High'],
                    'type': 'high',
                    'index': i
                })
            
            # Check for down fractal (swing low)
            if self._is_down_fractal(ohlc_data, i):
                down_fractals.append({
                    'timestamp': ohlc_data.index[i],
                    'price': ohlc_data.iloc[i]['Low'],
                    'type': 'low',
                    'index': i
                })
        
        return self._combine_fractals(up_fractals, down_fractals)
```

#### Swing Construction
```python
class SwingAnalyzer:
    def __init__(self):
        self.min_swing_size = 0.0020  # Minimum 20 pips for major pairs
    
    def identify_swings(self, fractals):
        """
        Convert fractals into swing movements
        Swing = movement between alternating fractal types
        """
        swings = []
        
        for i in range(len(fractals) - 1):
            current_fractal = fractals[i]
            next_fractal = fractals[i + 1]
            
            # Ensure alternating fractal types
            if current_fractal['type'] != next_fractal['type']:
                swing = {
                    'start_time': current_fractal['timestamp'],
                    'end_time': next_fractal['timestamp'],
                    'start_price': current_fractal['price'],
                    'end_price': next_fractal['price'],
                    'type': 'bullish' if next_fractal['price'] > current_fractal['price'] else 'bearish',
                    'magnitude': abs(next_fractal['price'] - current_fractal['price']),
                    'duration': (next_fractal['timestamp'] - current_fractal['timestamp']).total_seconds() / 3600,  # hours
                    'start_fractal': current_fractal,
                    'end_fractal': next_fractal
                }
                
                # Only include significant swings
                if swing['magnitude'] >= self.min_swing_size:
                    swings.append(swing)
        
        return swings
```

### 2. Dominant Swing Selection

#### Swing Scoring Algorithm
```python
class DominantSwingSelector:
    def __init__(self):
        self.magnitude_weight = 0.4    # 40% weight for swing size
        self.recency_weight = 0.3      # 30% weight for how recent
        self.momentum_weight = 0.2     # 20% weight for momentum
        self.duration_weight = 0.1     # 10% weight for duration
    
    def select_dominant_swing(self, swings, current_time):
        """
        Select the most dominant swing based on multiple factors
        """
        if not swings:
            return None
        
        scored_swings = []
        
        for swing in swings:
            score = self._calculate_swing_score(swing, current_time, swings)
            scored_swings.append({
                'swing': swing,
                'score': score
            })
        
        # Return swing with highest score
        dominant = max(scored_swings, key=lambda x: x['score'])
        return dominant['swing']
    
    def _calculate_swing_score(self, swing, current_time, all_swings):
        """Calculate composite score for swing dominance"""
        
        # Magnitude score (normalized)
        max_magnitude = max(s['magnitude'] for s in all_swings)
        magnitude_score = swing['magnitude'] / max_magnitude
        
        # Recency score (more recent = higher score)
        hours_ago = (current_time - swing['end_time']).total_seconds() / 3600
        recency_score = max(0, 1 - (hours_ago / 168))  # Decay over 1 week
        
        # Momentum score (price change per hour)
        momentum = swing['magnitude'] / max(swing['duration'], 1)
        max_momentum = max(s['magnitude'] / max(s['duration'], 1) for s in all_swings)
        momentum_score = momentum / max_momentum if max_momentum > 0 else 0
        
        # Duration score (prefer swings that took reasonable time)
        optimal_duration = 24  # 24 hours optimal
        duration_score = 1 - abs(swing['duration'] - optimal_duration) / optimal_duration
        duration_score = max(0, min(1, duration_score))
        
        # Composite score
        total_score = (
            magnitude_score * self.magnitude_weight +
            recency_score * self.recency_weight +
            momentum_score * self.momentum_weight +
            duration_score * self.duration_weight
        )
        
        return total_score
```

### 3. Fibonacci Level Calculation

#### Retracement and Extension Calculator
```python
class FibonacciCalculator:
    def __init__(self):
        self.retracement_levels = [0.236, 0.382, 0.500, 0.618, 0.786]
        self.extension_levels = [1.000, 1.272, 1.618, 2.000]
    
    def calculate_levels(self, dominant_swing):
        """Calculate Fibonacci retracement and extension levels"""
        
        start_price = dominant_swing['start_price']
        end_price = dominant_swing['end_price']
        swing_range = end_price - start_price
        
        # Calculate retracement levels
        retracements = {}
        for level in self.retracement_levels:
            if dominant_swing['type'] == 'bullish':
                # For bullish swings, retracements go down from the high
                retracements[level] = end_price - (swing_range * level)
            else:
                # For bearish swings, retracements go up from the low
                retracements[level] = end_price + (abs(swing_range) * level)
        
        # Calculate extension levels
        extensions = {}
        for level in self.extension_levels:
            if dominant_swing['type'] == 'bullish':
                # For bullish swings, extensions go up from the high
                extensions[level] = end_price + (swing_range * (level - 1))
            else:
                # For bearish swings, extensions go down from the low
                extensions[level] = end_price - (abs(swing_range) * (level - 1))
        
        return {
            'swing': dominant_swing,
            'retracements': retracements,
            'extensions': extensions,
            'calculation_time': datetime.now()
        }
```

### 4. Entry Signal Generation

#### Entry Condition Checker
```python
class EntrySignalGenerator:
    def __init__(self):
        self.entry_levels = [0.382, 0.618]  # Key retracement levels for entry
        self.level_tolerance = 0.0010       # 10 pip tolerance around levels
        self.min_risk_reward = 2.0          # Minimum 1:2 risk-reward ratio
    
    def check_entry_conditions(self, current_price, fibonacci_levels, market_data):
        """
        Check if current market conditions meet entry criteria
        """
        dominant_swing = fibonacci_levels['swing']
        retracements = fibonacci_levels['retracements']
        extensions = fibonacci_levels['extensions']
        
        # Check if price is near key retracement levels
        entry_level = self._find_nearest_entry_level(current_price, retracements)
        
        if not entry_level:
            return None
        
        # Determine trade direction based on dominant swing
        trade_direction = 'long' if dominant_swing['type'] == 'bullish' else 'short'
        
        # Calculate stop loss and take profit
        stop_loss = self._calculate_stop_loss(dominant_swing, trade_direction)
        take_profit = self._calculate_take_profit(extensions, trade_direction)
        
        # Validate risk-reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        if risk_reward_ratio < self.min_risk_reward:
            return None
        
        # Generate signal
        signal = {
            'symbol': market_data['symbol'],
            'direction': trade_direction,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': risk_reward_ratio,
            'fibonacci_level': entry_level['level'],
            'dominant_swing': dominant_swing,
            'confidence': self._calculate_confidence(entry_level, dominant_swing),
            'timestamp': datetime.now()
        }
        
        return signal
    
    def _find_nearest_entry_level(self, current_price, retracements):
        """Find if current price is near any entry-worthy retracement level"""
        
        for level_ratio in self.entry_levels:
            level_price = retracements[level_ratio]
            distance = abs(current_price - level_price)
            
            if distance <= self.level_tolerance:
                return {
                    'level': level_ratio,
                    'price': level_price,
                    'distance': distance
                }
        
        return None
    
    def _calculate_stop_loss(self, dominant_swing, direction):
        """Calculate stop loss based on swing extremes"""
        buffer = 0.0005  # 5 pip buffer
        
        if direction == 'long':
            # Stop below the swing low
            return dominant_swing['start_price'] - buffer
        else:
            # Stop above the swing high
            return dominant_swing['start_price'] + buffer
    
    def _calculate_take_profit(self, extensions, direction):
        """Calculate take profit at first extension level"""
        
        if direction == 'long':
            return extensions[1.272]  # 127.2% extension
        else:
            return extensions[1.272]  # 127.2% extension
    
    def _calculate_confidence(self, entry_level, dominant_swing):
        """Calculate signal confidence based on various factors"""
        
        base_confidence = 0.6  # Base confidence
        
        # Boost confidence for 61.8% level (golden ratio)
        if entry_level['level'] == 0.618:
            base_confidence += 0.1
        
        # Boost confidence for larger swings
        if dominant_swing['magnitude'] > 0.0050:  # > 50 pips
            base_confidence += 0.1
        
        # Boost confidence for recent swings
        hours_ago = (datetime.now() - dominant_swing['end_time']).total_seconds() / 3600
        if hours_ago < 24:  # Within last 24 hours
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
```

### 5. Strategy Configuration

#### Configurable Parameters
```yaml
# config/fibonacci_strategy.yaml
strategy:
  name: "Fibonacci Retracement Continuation"
  
  # Swing Analysis
  lookback_candles: 140
  fractal_bars_range: 2
  min_swing_size_pips: 20
  
  # Fibonacci Levels
  retracement_levels: [0.236, 0.382, 0.500, 0.618, 0.786]
  extension_levels: [1.000, 1.272, 1.618, 2.000]
  entry_levels: [0.382, 0.618]  # Only enter at these levels
  
  # Entry Criteria
  level_tolerance_pips: 10
  min_risk_reward_ratio: 2.0
  min_confidence_score: 0.7
  
  # Risk Management
  stop_loss_buffer_pips: 5
  position_size_risk_percent: 1.0
  max_positions: 3
  
  # Dominant Swing Scoring
  scoring_weights:
    magnitude: 0.4
    recency: 0.3
    momentum: 0.2
    duration: 0.1
```

## Strategy Advantages

### Why This Strategy Works
1. **Trend Following**: Trades in direction of dominant market movement
2. **High Probability Entries**: Fibonacci levels are widely watched by traders
3. **Clear Risk Management**: Well-defined stop losses and targets
4. **Objective Rules**: Removes emotional decision-making
5. **Scalable**: Works across multiple timeframes and instruments

### Expected Performance Characteristics
- **Win Rate**: 60-70% (trend-following nature)
- **Risk-Reward**: 1:2 minimum, often 1:3 or better
- **Drawdown**: Moderate during ranging markets
- **Best Markets**: Trending markets with clear swings
- **Worst Markets**: Choppy, sideways markets

## Implementation Priority

### Phase 1: Core Components
1. Fractal detection algorithm
2. Swing identification system
3. Basic Fibonacci calculation
4. Simple entry signal generation

### Phase 2: Enhancement
1. Dominant swing selection algorithm
2. Advanced confidence scoring
3. Risk management integration
4. Performance optimization

### Phase 3: AI Integration
1. Machine learning for swing scoring
2. Dynamic parameter optimization
3. Market regime detection
4. Adaptive confidence scoring

This strategy provides a solid foundation that can be enhanced with AI/ML components while maintaining clear, testable logic throughout the development process.
