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

## Round 2: Fibonacci Application ✅ PARTIALLY COMPLETED

### Confirmed Details:

#### Fibonacci Direction Logic ✅
**Q: When you find dominant swing (UP), do you apply Fibonacci retracements from swing LOW to swing HIGH?**
**A: YES - Apply Fibonacci from swing low to swing high, look for retracements to 38.2%, 50%, 61.8% levels, enter LONG on bounces (expecting Wave 5 up).**

#### Entry Triggers 🔄 NEEDS ML DEVELOPMENT
**Q: What triggers actual entry when price reaches Fibonacci level?**
**A: Currently looking for candlestick patterns, but this is exactly why ML is needed - to find optimal entry triggers through data analysis.**

### Questions Still Needed:
- Specific Fibonacci retracement levels to use (23.6%, 38.2%, 50%, 61.8%, 78.6%?)
- Extension levels for profit targets
- Multiple entries or single entry per swing
- Level tolerance (how close to exact level)

---

## Round 3: Trade Management (TO BE COMPLETED)

### Questions Planned:
- Entry execution methods
- Stop loss placement rules
- Take profit targeting approach
- Position sizing methodology

---

## Round 4: Filters & Context (TO BE COMPLETED)

### Questions Planned:
- Market condition filters
- Session preferences
- Time-based restrictions
- Risk management rules

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
- **ML Integration**: System must support training entry trigger models

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

## Next Steps

1. Complete Round 1 Q&A about fractals and swings
2. Proceed to Round 2 Fibonacci application details
3. Continue through all rounds systematically
4. Update configuration parameters based on responses
5. Implement strategy-specific algorithms

---

## Document Status

- [x] Round 1: Core Mechanics - **COMPLETED** ✅
- [x] Round 2: Fibonacci Application - **PARTIALLY COMPLETED** 🔄 
- [ ] Round 3: Trade Management - Pending  
- [ ] Round 4: Filters & Context - Pending
- [ ] Configuration Parameters - In Progress
- [ ] Implementation Specifications - In Progress

---

*This document will be updated continuously as strategy requirements are gathered and refined.*