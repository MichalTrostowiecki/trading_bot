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

## Round 1: Core Mechanics (Fractals & Swings)

### Questions for Strategy Owner

#### 1. Fractal Definition & Detection
**Q: How many bars do you use to define a fractal?**
- Standard 5-bar fractal (middle bar highest/lowest of 5)?
- Different periods for different timeframes?
- Any minimum distance requirement between fractals?

**A: [AWAITING RESPONSE]**

**Q: Do you use different fractal periods for different timeframes?**
**A: [AWAITING RESPONSE]**

**Q: Any minimum distance requirement between fractals?**
**A: [AWAITING RESPONSE]**

#### 2. Swing Identification
**Q: How do you define a "major swing"?**
- Fractal-to-fractal movement?
- Minimum percentage move required?
- Time-based filters?

**A: [AWAITING RESPONSE]**

**Q: What's your lookback period for identifying swings?**
- Last N bars?
- Last N fractals?
- Dynamic based on volatility?

**A: [AWAITING RESPONSE]**

**Q: Do you filter swings by minimum size/percentage move?**
**A: [AWAITING RESPONSE]**

#### 3. Dominant Swing Selection
**Q: How do you determine which swing is "dominant"?**
- Size/magnitude priority?
- Recency weight?
- Volume confirmation?
- Momentum factors?

**A: [AWAITING RESPONSE]**

**Q: Do you prioritize recent swings over larger but older ones?**
**A: [AWAITING RESPONSE]**

---

## Round 2: Fibonacci Application (TO BE COMPLETED)

### Questions Planned:
- Specific Fibonacci retracement levels used
- Extension levels for targets
- Entry trigger conditions at levels
- Direction determination logic

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
- Strategy focuses on swing continuation rather than reversal
- Fibonacci levels used as entry points in trending markets
- Fractal-based swing identification is core to the approach

### Key Implementation Considerations:
- Real-time fractal detection with configurable parameters
- Swing analysis with multiple weighting factors
- Dynamic Fibonacci level calculation
- Market structure context integration

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

- [ ] Round 1: Core Mechanics - **IN PROGRESS**
- [ ] Round 2: Fibonacci Application - Pending
- [ ] Round 3: Trade Management - Pending  
- [ ] Round 4: Filters & Context - Pending
- [ ] Configuration Parameters - Pending
- [ ] Implementation Specifications - Pending

---

*This document will be updated continuously as strategy requirements are gathered and refined.*