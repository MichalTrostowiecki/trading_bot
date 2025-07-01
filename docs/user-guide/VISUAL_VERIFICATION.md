# Visual Verification Guide for Fibonacci Trading Strategy

## Overview
This guide outlines the systematic approach to visually verify that the Fibonacci trading strategy is working correctly before applying any ML/AI optimizations. Visual verification is critical to ensure the foundation is solid.

## Why Visual Verification Matters
- **Catch Logic Errors**: See if fractals/swings are detected correctly
- **Validate Entry Points**: Ensure Fibonacci levels are calculated properly
- **Debug Edge Cases**: Identify scenarios where the strategy fails
- **Build Confidence**: Know exactly how your strategy behaves
- **Create Training Data**: Verified signals become ML training data

## Visual Verification Workflow

### Step 1: Data Preparation
1. **Import Historical Data**
   ```python
   # Load data from MT4 (Nov 2024 - present)
   python src/data/importers/mt4_importer.py --symbol EURUSD --timeframe H1
   ```

2. **Verify Data Quality**
   - Check for gaps
   - Validate OHLC relationships (High >= Low, etc.)
   - Ensure consistent timestamps
   - Look for anomalies

### Step 2: Fractal Detection Verification

#### Visual Checks:
1. **Load Chart with Fractals**
   - Open research dashboard: http://localhost:8001
   - Select symbol and timeframe
   - Enable fractal overlay

2. **Verify Each Fractal**
   - **High Fractal** (▼): Center bar high > surrounding bars
   - **Low Fractal** (▲): Center bar low < surrounding bars
   - Check validation period (default: 2 bars each side)

3. **Common Issues to Check**:
   - [ ] Fractals at the correct price points
   - [ ] No missing fractals in obvious locations
   - [ ] No false fractals on flat areas
   - [ ] Proper handling of equal highs/lows

#### Debug Panel Checks:
```
Fractal Detection @ 2024-01-15 14:00
Type: High Fractal
Price: 1.0950
Validation: 
  Left bars: 1.0945, 1.0940
  Right bars: 1.0948, 1.0943
Status: VALID ✓
```

### Step 3: Swing Identification Verification

#### Visual Checks:
1. **Verify Swing Connections**
   - Swings connect fractal lows to fractal highs
   - No crossing of swing lines
   - Proper alternation (up-down-up-down)

2. **Swing Validation Rules**:
   - Minimum swing size (e.g., 50 pips)
   - Time duration requirements
   - Proper fractal-to-fractal connections

3. **Visual Indicators**:
   - Upswing: Green arrow from low to high
   - Downswing: Red arrow from high to low
   - Swing magnitude displayed

#### Common Issues:
- [ ] Swings skipping valid fractals
- [ ] Too many micro-swings in ranging markets
- [ ] Incorrect swing direction identification
- [ ] Missing major swings

### Step 4: Fibonacci Level Verification

#### Visual Checks:
1. **Fibonacci Retracement Levels**
   ```
   0.0%   - Swing start
   23.6%  - First retracement
   38.2%  - Shallow retracement
   50.0%  - Mid-point
   61.8%  - Golden ratio
   78.6%  - Deep retracement
   100.0% - Swing end
   ```

2. **Verify Calculations**:
   - Levels drawn from correct swing points
   - Accurate percentage calculations
   - Proper direction (retracement vs extension)

3. **Entry Zone Validation**:
   - Entry zones highlighted at key Fib levels
   - Proper buffer around levels (e.g., ±5 pips)
   - Clear visual distinction

### Step 5: Signal Generation Verification

#### Entry Signal Checks:
1. **Continuation Trade Setup**
   - Price retraces to Fibonacci level
   - In direction of dominant swing
   - Proper confirmation (e.g., candlestick pattern)

2. **Visual Signal Markers**:
   - Entry: Green/Red arrow with "ENTRY" label
   - Stop Loss: Red horizontal line
   - Take Profit: Green horizontal line

3. **Signal Information Display**:
   ```
   Signal Generated @ 2024-01-15 14:00
   Type: BUY
   Entry: 1.0920 (38.2% retracement)
   Stop: 1.0900 (below 50%)
   Target: 1.0960 (previous high)
   Risk/Reward: 1:2
   ```

### Step 6: Replay Mode Testing

#### Replay Controls:
```
[<<] Previous Signal
[<]  Previous Bar
[▶]  Play/Pause
[>]  Next Bar
[>>] Next Signal
Speed: [0.5x] [1x] [2x] [5x] [10x]
```

#### Replay Verification Process:
1. **Start from Beginning**
   - Set date range for testing period
   - Begin replay at slowest speed

2. **Step Through Each Bar**
   - Watch fractal formation in real-time
   - Observe swing development
   - See Fibonacci levels adjust

3. **Document Issues**:
   - Screenshot problematic scenarios
   - Note timestamp and conditions
   - Export data for debugging

### Step 7: Edge Case Testing

#### Scenarios to Test:
1. **Ranging Markets**
   - How does strategy handle sideways movement?
   - Are false signals filtered out?

2. **Strong Trends**
   - Does strategy catch major moves?
   - Proper handling of extended trends

3. **News Events**
   - Behavior during high volatility
   - Gap handling

4. **Session Transitions**
   - Asian → London transition
   - London → New York transition

### Step 8: Performance Verification

#### Metrics to Track Visually:
1. **Trade Accuracy**
   - Win rate at each Fib level
   - Average risk/reward achieved
   - Drawdown periods

2. **Statistical Validation**:
   ```
   38.2% Retracement Stats:
   - Total Signals: 150
   - Win Rate: 65%
   - Avg Winner: +45 pips
   - Avg Loser: -20 pips
   - Profit Factor: 1.46
   ```

## Visual Verification Checklist

### Pre-Verification:
- [ ] Historical data imported and validated
- [ ] Research dashboard running
- [ ] Debug panel enabled
- [ ] Known good/bad examples identified

### Fractal Verification:
- [ ] All fractals correctly identified
- [ ] No false fractals
- [ ] Proper validation period
- [ ] Edge cases handled

### Swing Verification:
- [ ] Swings connect proper fractals
- [ ] Direction correctly identified
- [ ] Minimum size requirements met
- [ ] No invalid swings

### Fibonacci Verification:
- [ ] Levels calculated correctly
- [ ] Proper retracement direction
- [ ] Entry zones properly defined
- [ ] Visual clarity

### Signal Verification:
- [ ] Signals at correct Fib levels
- [ ] Proper entry direction
- [ ] Stop loss placement logical
- [ ] Take profit reasonable

### Overall Strategy:
- [ ] Behaves as expected in trends
- [ ] Filters out ranging markets
- [ ] Risk management consistent
- [ ] Performance metrics reasonable

## Debugging Guide

### When Fractals Look Wrong:
1. Check bar count for validation
2. Verify high/low comparison logic
3. Look for equal highs/lows handling
4. Check timeframe consistency

### When Swings Don't Connect:
1. Verify fractal alternation logic
2. Check minimum swing size
3. Look for skipped fractals
4. Verify time requirements

### When Signals Don't Fire:
1. Check Fibonacci level tolerance
2. Verify confirmation requirements
3. Look for filter conditions
4. Check market regime filters

## Export and Documentation

### What to Export:
1. **Problem Scenarios**
   - Chart screenshots
   - Data CSV for time period
   - Debug log output

2. **Successful Patterns**
   - Best performing setups
   - Ideal market conditions
   - Entry/exit examples

3. **Statistical Reports**
   - Performance by Fib level
   - Win rate by market condition
   - Risk/reward distribution

### Documentation Format:
```markdown
## Issue: Fractal Detection Failure
Date: 2024-01-15 14:00
Symbol: EURUSD
Timeframe: H1

### Description:
Fractal not detected at obvious swing high

### Data:
- Price: 1.0950
- Previous: 1.0945, 1.0940
- Next: 1.0948, 1.0943

### Resolution:
Adjusted validation logic to handle equal highs
```

## Next Steps After Verification

1. **If Issues Found**:
   - Document thoroughly
   - Fix logic errors
   - Re-run verification
   - Update test cases

2. **If Verification Passes**:
   - Export verified dataset
   - Create performance baseline
   - Document strategy parameters
   - Prepare for ML enhancement

3. **Continuous Verification**:
   - Set up automated visual tests
   - Create regression test suite
   - Monitor live performance
   - Compare with backtest results

## Conclusion
Visual verification is not a one-time process but an ongoing practice. Every strategy modification should go through visual verification before deployment. This ensures that the foundation remains solid as we build more sophisticated ML/AI enhancements on top.