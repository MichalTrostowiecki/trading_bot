# TradingView Lightweight Charts Marker Fix

## Problem
Markers were appearing on the current/latest candle instead of their correct historical positions when using progressive chart updates during backtesting.

## Root Cause
The issue was caused by calling `candlestickSeries.setData(visibleData)` with progressively sliced data. This **replaced the entire chart dataset** with only the bars up to the current position, making historical timestamps unavailable for marker placement.

When TradingView tries to place a marker at a timestamp that doesn't exist in the current dataset, it defaults to placing it on the nearest available timestamp (usually the last/current bar).

## Solution
Changed from **progressive data replacement** to **full dataset with position filtering**:

### Before (Broken)
```javascript
// Progressive data replacement - BREAKS MARKERS
const visibleData = marketData.slice(0, position + 1).map(bar => ({
    time: Math.floor(new Date(bar.timestamp).getTime() / 1000),
    open: bar.open, high: bar.high, low: bar.low, close: bar.close
}));
candlestickSeries.setData(visibleData); // Replaces entire dataset!
```

### After (Fixed)
```javascript
// Full dataset approach - PRESERVES ALL TIMESTAMPS
if (!window.fullChartData) {
    window.fullChartData = marketData.map(bar => ({
        time: Math.floor(new Date(bar.timestamp).getTime() / 1000),
        open: bar.open, high: bar.high, low: bar.low, close: bar.close
    }));
    candlestickSeries.setData(window.fullChartData); // Set once with full data
}

// Filter markers by position instead of replacing data
const currentTime = window.fullChartData[position].time;
const visibleMarkers = allMarkers.filter(marker => marker.time <= currentTime);
candlestickSeries.setMarkers(visibleMarkers);
```

## Key Changes Made

1. **Full Dataset Loading**: Chart now loads complete dataset once and keeps it
2. **Position-Based Marker Filtering**: Markers are filtered by current backtest position
3. **Position Indicator**: Added visual indicator showing current backtest position
4. **Cache Management**: Proper cleanup of cached data when loading new datasets

## Files Modified
- `src/research/dashboard/research_api.py`: Main fix implementation
- `test_marker_fix.html`: Test file to verify the fix

## Benefits
- ✅ Markers appear at correct historical positions
- ✅ Maintains backtesting realism (only shows markers up to current position)
- ✅ Better performance (no repeated data conversion)
- ✅ Preserves all chart functionality (zoom, pan, etc.)
- ✅ Adds visual position indicator for better UX

## Testing
Run the test file `test_marker_fix.html` to see the fix in action:
1. Initialize test with full dataset
2. Add historical markers at various positions
3. Simulate progression - markers should appear only up to current position
4. Verify markers stay at their correct historical positions
