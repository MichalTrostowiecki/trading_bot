# Fibonacci Retracement Continuation Strategy - Requirements Specification

**Document Version**: 1.0  
**Created**: 2024-06-27  
**Last Updated**: 2024-06-27  
**Status**: In Development

## Overview

This document captures the detailed requirements for the Fibonacci-based AI trading bot strategy. It serves as the authoritative specification for implementation and ensures consistency across development sessions and AI agents.

## Strategy Summary

The system identifies major market swings using fractal analysis and applies Fibonacci retracement levels to enter trades in the direction of the dominant swing for continuation moves.

---

## Round 1: Core Mechanics (Fractals & Swings) ✅ COMPLETED

### Strategy Context: Elliott Wave Foundation
The strategy is based on Elliott Wave concepts, specifically:
- **Dominant Swing = Impulsive Move (potentially Wave 3)**
- **Fibonacci Retracements = Wave 4 correction levels**
- **Entry = Wave 5 continuation in direction of dominant swing**

### Questions and Answers

#### 1. Fractal Definition & Detection
**Q: How many bars do you use to define a fractal?**
**A: Variable/configurable for optimization testing. Standard 5-bar may not be significant enough to capture market structure. Need to test different periods to find optimal values.**

**Q: Do you use different fractal periods for different timeframes?**
**A: Focus on single timeframe (M1 initially). Higher timeframe confluence may be added later for testing.**

**Q: Any minimum distance requirement between fractals?**
**A: No minimum distance required. If using 21-bar lookback, need to find ALL fractals in that period.**

**Special Requirement:** Need logic to handle cases where two bars have exact same high/low price to avoid false fractals.

#### 2. Swing Identification
**Q: How do you define a "major swing"?**
**A: Swing = movement from one fractal to the next (up fractal to down fractal or vice versa). No minimum percentage move required - all fractal-to-fractal movements qualify as swings.**

**Q: What's your lookback period for identifying swings?**
**A: Variable/configurable for optimization (example: 140 candles). Go from newest candle backwards X candles and identify all swings, focusing on latest swings.**

**Q: Do you filter swings by minimum size/percentage move?**
**A: Variable/configurable for optimization. No fixed minimum - will test to find optimal values.**

#### 3. Dominant Swing Selection
**Q: How do you determine which swing is "dominant"?**
**A: SIZE/MAGNITUDE IS THE ONLY FACTOR. Dominant swing = biggest swing in lookback period (measured in pips/points). Rationale: corrections never go beyond impulsive moves.**

**Q: Do you prioritize recent swings over larger but older ones?**
**A: NO. Size is the only criterion. Every new candle triggers check for new fractals and swing comparison. If new swing is bigger than current dominant swing, it becomes the new dominant swing.**

### Swing Update Logic:
1. New fractal detected → new swing created
2. Compare new swing size with previous opposite-direction swing
3. Bigger swing becomes dominant
4. Keep only last swing in each direction for comparison

---

## Round 2: Fibonacci Application ✅ COMPLETED

### Confirmed Details:

#### Fibonacci Direction Logic ✅
**Q: When you find dominant swing (UP), do you apply Fibonacci retracements from swing LOW to swing HIGH?**
**A: YES - Apply Fibonacci from swing low to swing high, look for retracements to levels, enter LONG on bounces with confirmation (expecting Wave 5 up).**

#### Fibonacci Retracement Levels ✅
**Q: Which specific Fibonacci retracement levels do you want to use?**
**A: ALL LEVELS for testing optimization (23.6%, 38.2%, 50%, 61.8%, 78.6%). Usually best results between 38.2%-78.6%, but need testing capability for all levels.**

#### Fibonacci Extension Levels ✅  
**Q: Do you use Fibonacci extension levels for profit targets?**
**A: YES - Test all extension levels (100%, 127.2%, 161.8%, 261.8%) to find optimal targets. Need testing capability for all levels.**

#### Entry Strategy ✅
**Q: Do you enter at multiple Fibonacci levels or focus on one preferred level?**
**A: SINGLE TRADE ONLY. Look for confluence factors at Fibonacci levels (candlestick patterns, ABC corrections, etc.). Do NOT enter just because price touched level - need confirmation signals.**

#### Level Tolerance ✅
**Q: How close does price need to be to the exact Fibonacci level?**
**A: CONFIGURABLE for testing optimization. Need to test different tolerance values to find optimal setting.**

#### Trade Management ✅
**Q: Multiple entries management?**
**A: NO MULTIPLE ENTRIES. One trade at a time. System has two modes: "Trade Finding Mode" and "Trade Management Mode".**

#### Setup Invalidation ✅
**Q: When does Fibonacci setup become invalid?**
**A: When price breaks below swing low (for upward swings) or above swing high (for downward swings). This means price not respecting Fibonacci retracement and likely new swings forming.**

---

## Round 3: Trade Management ✅ COMPLETED

### Confirmed Details:

#### Stop Loss Placement ✅
**Q: Where and how do you place stop losses?**
**A: Signal bar-based placement:**
- **Long trades**: 2 pips below the signal bar
- **Short trades**: 2 pips + spread above the signal bar
- **Buffer configurable** for testing optimization

#### Position Sizing ✅
**Q: What position sizing method do you prefer?**
**A: Percentage-based position sizing. Configurable percentage for testing optimization.**

#### Take Profit Strategy ✅
**Q: Take profit approach?**
**A: Use Fibonacci extension levels (covered in Round 2) - test all extension levels (100%, 127.2%, 161.8%, 261.8%) for optimization.**

#### Testing Philosophy ✅
**All parameters configurable for testing to find optimal results across different market conditions.**

---

## Round 4: Filters & Context ✅ COMPLETED

### Strategic Approach: Broad Testing Framework

#### Market Condition Filters ✅
**Q: What market condition filters do you want to use?**
**A: START BROAD, TEST EVERYTHING. Build flexible filter framework where all filters are optional/configurable for optimization testing:**
- Volatility filters (min/max ATR ranges)
- Trend strength filters
- Market regime detection
- All parameters testable to find optimal combinations

#### Session Preferences ✅
**Q: Do you prefer specific trading sessions?**
**A: CONFIGURABLE for testing. Build capability to enable/disable sessions (London, New York, Asian) and test which combinations provide best results.**

#### News Event Filters ✅
**Q: How do you handle news events?**
**A: CONFIGURABLE for testing. Build capability to avoid trading around news events with configurable time buffers, then test if filtering improves performance.**

#### Testing Philosophy ✅
**Rather than pre-defining filters, build comprehensive testing framework to let data determine optimal filter combinations. This avoids premature filtering that might eliminate profitable opportunities.**

---

## Implementation Notes

### Current Understanding:
- **Elliott Wave Foundation**: Strategy targets Wave 5 continuation after Wave 4 correction
- **Dominant Swing = Impulsive Move**: Biggest swing in lookback period represents likely Wave 3
- **Size-Only Dominance**: No recency weighting - biggest swing always wins
- **Single Timeframe Focus**: M1 initially, higher timeframe confluence later
- **ML-Driven Entries**: Entry triggers to be determined through machine learning analysis

### Key Implementation Considerations:
- **Configurable Fractal Detection**: Variable periods for optimization
- **Real-time Swing Updates**: Compare new swings with current dominant on each candle
- **Edge Case Handling**: Logic for same-price high/low scenarios
- **Size-Based Comparison**: Measure swings in pips/points for dominance
- **Fibonacci Calculation**: Apply from swing extremes in dominant direction
- **All Fibonacci Levels**: Support testing all retracement (23.6%-78.6%) and extension (100%-261.8%) levels
- **Confluence Detection**: ML-based pattern recognition for entry confirmation
- **Mode-Based Logic**: Separate "Trade Finding" and "Trade Management" modes
- **Single Trade Management**: No multiple concurrent positions
- **Setup Invalidation**: Monitor swing extreme breaks for setup invalidation
- **Signal Bar Stop Losses**: 2-pip buffer below/above signal bar (+ spread for shorts)
- **Percentage Position Sizing**: Configurable risk percentage per trade
- **Extension Target Management**: Multiple configurable take profit levels
- **Flexible Filter Framework**: All market filters optional/configurable for testing optimization
- **Comprehensive Testing Engine**: Support A/B testing of filter combinations and parameter sets

---

## Configuration Parameters (TO BE POPULATED)

```yaml
# Strategy Parameters (to be defined based on Q&A)
fractals:
  periods: [TBD]
  min_distance: [TBD]
  
swings:
  lookback_periods: [TBD]
  min_size_percent: [TBD]
  
fibonacci:
  retracement_levels: [TBD]
  extension_levels: [TBD]
  
dominant_swing:
  size_weight: [TBD]
  recency_weight: [TBD]
  momentum_weight: [TBD]
```

---

## AI Enhancement & Automation Features

### Machine Learning Integration
- **Smart Pattern Recognition** - AI identifies optimal fractal patterns and swing structures
- **Dynamic Parameter Optimization** - ML adjusts Fibonacci levels and fractal periods based on market conditions
- **Entry Timing Optimization** - AI finds best entry points within Fibonacci zones using confluence factors
- **Market Regime Detection** - Strategy adapts behavior for trending vs ranging markets
- **Risk-Adjusted Position Sizing** - AI calculates optimal position sizes based on market volatility

### Automated Trading System
- **Full Automation** - Completely hands-free operation on VPS
- **Background Service** - Runs 24/7 as Windows service without GUI
- **Direct MT5 Integration** - Automatic trade execution via MetaTrader 5 API
- **Emergency Controls** - Remote stop/start capabilities and emergency position closure
- **Multi-Symbol Support** - Simultaneous trading across multiple currency pairs

### Web Control Dashboard
- **Remote Management** - Full control via web interface from any device
- **Real-time Monitoring** - Live charts, positions, and performance metrics
- **Trading Controls** - Start/stop bot, adjust risk parameters, enable/disable symbols
- **Performance Analytics** - Historical performance, trade analysis, and strategy metrics
- **Risk Management** - Daily loss limits, position sizing controls, and drawdown protection

### Database & Analytics
- **Historical Data Storage** - Complete price history and trade records
- **Performance Tracking** - Real-time and historical performance metrics
- **Backtest Integration** - Compare live performance with historical backtests
- **Trade Analytics** - Detailed analysis of all executed trades
- **Strategy Optimization** - Data-driven parameter optimization and improvement

---

## Next Steps

1. ✅ **STRATEGY REQUIREMENTS COMPLETE** 
2. 🔄 **CURRENT**: Implement automated trading engine with web dashboard
3. 📈 **NEXT**: Add machine learning enhancements and optimization
4. 🚀 **DEPLOY**: VPS deployment and production monitoring

---

## Document Status

- [x] Round 1: Core Mechanics - **COMPLETED** ✅
- [x] Round 2: Fibonacci Application - **COMPLETED** ✅ 
- [x] Round 3: Trade Management - **COMPLETED** ✅
- [x] Round 4: Filters & Context - **COMPLETED** ✅
- [x] **STRATEGY REQUIREMENTS COMPLETE** 🎉
- [x] AI Enhancement & Automation Features - **ADDED** 🤖
- [ ] Configuration Parameters - Ready to populate
- [x] Implementation Specifications - **READY TO BEGIN** ⚡

---

*This document serves as the complete specification for the AI-enhanced Fibonacci trading bot with full automation capabilities.*