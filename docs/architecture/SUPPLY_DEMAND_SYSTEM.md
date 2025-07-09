# Supply & Demand Zone Detection System - Technical Specification

## Document Information
- **Version**: 1.0
- **Date**: July 6, 2025
- **Author**: Claude AI Agent
- **Status**: Draft
- **Review Required**: Yes

---

## 1. Executive Summary

### 1.1 Purpose
The Supply & Demand Zone Detection System implements professional-grade institutional order flow analysis based on eWavesHarmonics methodology. This system identifies areas where large institutional orders create supply/demand imbalances, providing high-probability confluence zones for the existing Fibonacci trading strategy.

### 1.2 Key Features
- **Base Candle Detection**: Identifies consolidation areas before significant price moves
- **Zone Boundary Calculation**: Precise rectangle coordinates for supply/demand zones
- **Zone State Management**: Tracks zone lifecycle from creation to invalidation
- **Flip Zone Detection**: Identifies when supply becomes demand and vice versa
- **Confluence Integration**: Seamlessly integrates with existing confluence scoring system
- **TradingView Visualization**: Professional rectangle drawing with color coding
- **Performance Optimization**: <100ms execution time maintaining ~160ms total system budget

### 1.3 Business Value
- **Enhanced Trade Accuracy**: Institutional order flow confluence improves win rates
- **Risk Management**: Clear zone boundaries provide precise stop-loss levels
- **Professional Analysis**: Matches institutional trading methodologies
- **Scalable Architecture**: Supports multiple timeframes and instruments

---

## 2. System Overview

### 2.1 Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Supply & Demand Zone System                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Base Candle   │  │   Big Move      │  │   Zone          │ │
│  │   Detector      │─▶│   Detector      │─▶│   Classifier    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                ▼                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Zone State    │  │   Zone          │  │   Rectangle     │ │
│  │   Manager       │◀─│   Boundary      │◀─│   Drawer        │ │
│  └─────────────────┘  │   Calculator    │  └─────────────────┘ │
│                       └─────────────────┘                      │
├─────────────────────────────────────────────────────────────────┤
│                    Integration Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Confluence    │  │   Database      │  │   Research      │ │
│  │   Engine        │  │   Storage       │  │   Dashboard     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

1. **Input**: OHLC candlestick data from market feed
2. **Base Candle Detection**: Identify consolidation areas
3. **Big Move Detection**: Detect significant price movements
4. **Zone Classification**: Classify as supply, demand, or continuation zones
5. **Boundary Calculation**: Calculate precise zone coordinates
6. **Visualization**: Draw rectangles on TradingView charts
7. **Confluence Integration**: Score zones against Fibonacci levels
8. **Database Storage**: Persist zone data for historical analysis

---

## 3. Algorithm Specifications

### 3.1 Base Candle Detection Algorithm

#### 3.1.1 Methodology
Based on eWavesHarmonics principles, base candles are small consolidation areas that precede significant price moves. These represent periods where institutional orders accumulate.

#### 3.1.2 Detection Criteria
```python
# Base Candle Identification Rules
consolidation_threshold = 0.5  # Percentage of recent ATR
min_base_candles = 2           # Minimum candles in base
max_base_candles = 10          # Maximum candles in base
body_size_threshold = 0.3      # Body size relative to range
```

#### 3.1.3 Algorithm Steps
1. **Calculate ATR**: 14-period Average True Range for volatility baseline
2. **Identify Small Candles**: Bodies < 30% of ATR, total range < 50% of ATR
3. **Group Consecutive**: Find consecutive small candles (2-10 candles)
4. **Validate Consolidation**: Ensure price stays within tight range
5. **Mark Base Range**: Record start/end indices and price boundaries

#### 3.1.4 Mathematical Formula
```
Base Candle Criteria:
- Candle Body Size < (ATR_14 * 0.3)
- Candle Total Range < (ATR_14 * 0.5)
- Consecutive Count: 2 ≤ count ≤ 10
- Price Range: (High - Low) < (ATR_14 * 0.8)
```

### 3.2 Big Move Detection Algorithm

#### 3.2.1 Methodology
Identifies significant price movements that follow base candle consolidation, indicating institutional order execution.

#### 3.2.2 Detection Criteria
```python
# Big Move Identification Rules
move_threshold = 2.0        # ATR multiple for significant move
min_move_candles = 3        # Minimum candles in move
breakout_confirmation = True # Require level break
momentum_filter = True      # Filter for momentum continuation
```

#### 3.2.3 Algorithm Steps
1. **Measure Move Magnitude**: Calculate price movement from base end
2. **Confirm Breakout**: Ensure break of previous support/resistance
3. **Validate Momentum**: Check for follow-through candles
4. **Direction Classification**: Determine bullish/bearish direction
5. **Quality Assessment**: Score move quality and institutional signatures

#### 3.2.4 Mathematical Formula
```
Big Move Criteria:
- Move Magnitude > (ATR_14 * 2.0)
- Breakout Confirmation: Close beyond previous high/low
- Momentum Score: (Close - Open) / (High - Low) > 0.6
- Follow-through: Next 3 candles maintain direction
```

### 3.3 Zone Classification Algorithm

#### 3.3.1 Zone Types
- **Demand Zone**: Base candles before bullish impulse move
- **Supply Zone**: Base candles before bearish impulse move
- **Continuation Zone**: Mid-move consolidation during trending price action

#### 3.3.2 Classification Logic
```python
if impulse_direction == "bullish":
    zone_type = "demand"
    zone_color = "#44FF44"  # Green
elif impulse_direction == "bearish":
    zone_type = "supply"
    zone_color = "#FF4444"  # Red
else:
    zone_type = "continuation"
    zone_color = "#4444FF"  # Blue
```

### 3.4 Zone Boundary Calculation

#### 3.4.1 Demand Zone Boundaries
Based on eWavesHarmonics methodology:
```python
# Demand Zone Rectangle Coordinates
top = max(high for high in base_candles)
bottom = min(open for candle in base_candles if candle.color == "red")
left = base_start_time
right = current_time  # Extends to current bar
```

#### 3.4.2 Supply Zone Boundaries
```python
# Supply Zone Rectangle Coordinates
top = max(open for candle in base_candles if candle.color == "green")
bottom = min(low for low in base_candles)
left = base_start_time
right = current_time  # Extends to current bar
```

#### 3.4.3 Precision Requirements
- **Price Precision**: 0.1 pip accuracy for major pairs
- **Time Precision**: Exact candle timestamp alignment
- **Boundary Validation**: Ensure top > bottom, left < right

---

## 4. Performance Requirements

### 4.1 Speed Requirements
- **Zone Detection**: <50ms per update cycle
- **Rectangle Drawing**: <30ms per chart update
- **Confluence Calculation**: <20ms per bar analysis
- **Total System Impact**: <100ms (within ~160ms total budget)

### 4.2 Memory Requirements
- **Zone Storage**: <1MB per 1000 zones
- **Cache Management**: LRU cache with 500-zone limit
- **Database Queries**: <10ms per zone lookup

### 4.3 Accuracy Requirements
- **Zone Boundary Precision**: ±0.1 pip for major currency pairs
- **Detection Accuracy**: >95% match with manual analysis
- **False Positive Rate**: <5% invalid zone detection

### 4.4 Scalability Requirements
- **Multiple Timeframes**: Support M1, M5, M15, H1, H4, D1
- **Multiple Instruments**: 50+ currency pairs and indices
- **Historical Data**: Process 100,000+ bars efficiently

---

## 5. Integration Specifications

### 5.1 Confluence Engine Integration

#### 5.1.1 Confluence Factor Addition
```python
class ConfluenceFactorType(Enum):
    SUPPLY_DEMAND = "supply_demand"  # New factor type
```

#### 5.1.2 Scoring Algorithm
```python
def calculate_supply_demand_confluence(price, zones):
    """
    Calculate confluence score for supply/demand zones
    
    Scoring Criteria:
    - Distance from zone boundary (closer = higher score)
    - Zone strength (fresh zones = higher score)
    - Zone type alignment with trend direction
    - Historical test success rate
    """
    base_score = 0.0
    
    for zone in zones:
        if zone.contains_price(price):
            distance_score = 1.0 - (abs(price - zone.center) / zone.height)
            strength_score = zone.strength_rating
            freshness_score = 1.0 / (1.0 + zone.test_count)
            
            zone_score = (distance_score * 0.4 + 
                         strength_score * 0.4 + 
                         freshness_score * 0.2)
            
            base_score = max(base_score, zone_score)
    
    return min(base_score, 1.0)
```

### 5.2 Database Schema Integration

#### 5.2.1 New Tables
```sql
-- Supply & Demand Zones Table
CREATE TABLE supply_demand_zones (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    zone_type VARCHAR(20) NOT NULL CHECK (zone_type IN ('supply', 'demand', 'continuation')),
    top_price DECIMAL(12,5) NOT NULL,
    bottom_price DECIMAL(12,5) NOT NULL,
    left_time TIMESTAMP NOT NULL,
    right_time TIMESTAMP NOT NULL,
    strength_score DECIMAL(3,2) CHECK (strength_score >= 0 AND strength_score <= 1),
    test_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'tested', 'broken', 'flipped')),
    created_from_base_start INTEGER NOT NULL,
    created_from_base_end INTEGER NOT NULL,
    impulse_start INTEGER NOT NULL,
    impulse_end INTEGER NOT NULL,
    atr_at_creation DECIMAL(10,5),
    volume_at_creation DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zone Tests Table
CREATE TABLE zone_tests (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES supply_demand_zones(id),
    test_time TIMESTAMP NOT NULL,
    test_price DECIMAL(12,5) NOT NULL,
    test_type VARCHAR(20) NOT NULL CHECK (test_type IN ('touch', 'penetration', 'break')),
    rejection_strength DECIMAL(3,2),
    outcome VARCHAR(20) CHECK (outcome IN ('bounce', 'break', 'flip')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zone Flips Table
CREATE TABLE zone_flips (
    id SERIAL PRIMARY KEY,
    original_zone_id INTEGER REFERENCES supply_demand_zones(id),
    new_zone_id INTEGER REFERENCES supply_demand_zones(id),
    flip_time TIMESTAMP NOT NULL,
    flip_price DECIMAL(12,5) NOT NULL,
    flip_confirmation_bars INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.2.2 Indexes for Performance
```sql
-- Performance Indexes
CREATE INDEX idx_sd_zones_symbol_timeframe ON supply_demand_zones(symbol, timeframe);
CREATE INDEX idx_sd_zones_status ON supply_demand_zones(status);
CREATE INDEX idx_sd_zones_time_range ON supply_demand_zones(left_time, right_time);
CREATE INDEX idx_sd_zones_price_range ON supply_demand_zones(bottom_price, top_price);
CREATE INDEX idx_zone_tests_zone_id ON zone_tests(zone_id);
CREATE INDEX idx_zone_tests_time ON zone_tests(test_time);
```

### 5.3 Research Dashboard Integration

#### 5.3.1 API Endpoints
```python
# New API endpoints for S&D zones
@app.get("/api/supply-demand-zones/{symbol}/{timeframe}")
async def get_supply_demand_zones(symbol: str, timeframe: str, start_time: datetime, end_time: datetime):
    """Get all supply/demand zones for symbol and timeframe within time range"""

@app.post("/api/supply-demand-zones/detect")
async def detect_zones_realtime(request: ZoneDetectionRequest):
    """Detect zones in real-time for given price data"""

@app.get("/api/supply-demand-zones/{zone_id}/tests")
async def get_zone_tests(zone_id: int):
    """Get all tests for a specific zone"""
```

#### 5.3.2 Frontend Components
```javascript
// TradingView Rectangle Drawing
class SupplyDemandRectangleManager {
    constructor(chart) {
        this.chart = chart;
        this.rectangles = new Map();
        this.colors = {
            supply: '#FF4444',
            demand: '#44FF44',
            continuation: '#4444FF'
        };
    }
    
    drawZone(zoneData) {
        const rectangle = this.chart.createRectangle({
            time1: zoneData.left_time,
            time2: zoneData.right_time,
            price1: zoneData.top_price,
            price2: zoneData.bottom_price,
            color: this.colors[zoneData.zone_type],
            transparency: 80
        });
        
        this.rectangles.set(zoneData.id, rectangle);
    }
}
```

---

## 6. Visual Design Specifications

### 6.1 Zone Rectangle Styling

#### 6.1.1 Color Scheme
```javascript
const ZONE_COLORS = {
    supply: {
        fill: '#FF4444',      // Red
        border: '#CC0000',    // Dark Red
        transparency: 80
    },
    demand: {
        fill: '#44FF44',      // Green
        border: '#00CC00',    // Dark Green
        transparency: 80
    },
    continuation: {
        fill: '#4444FF',      // Blue
        border: '#0000CC',    // Dark Blue
        transparency: 80
    },
    flipped: {
        fill: '#FF8844',      // Orange
        border: '#CC4400',    // Dark Orange
        transparency: 80
    }
};
```

#### 6.1.2 Zone Labels
```javascript
const ZONE_LABELS = {
    supply: {
        text: 'S',
        position: 'top-left',
        font: 'bold 12px Arial',
        color: '#FFFFFF'
    },
    demand: {
        text: 'D',
        position: 'bottom-left',
        font: 'bold 12px Arial',
        color: '#FFFFFF'
    },
    continuation: {
        text: 'C',
        position: 'center',
        font: 'bold 12px Arial',
        color: '#FFFFFF'
    }
};
```

### 6.2 Zone State Visual Indicators

#### 6.2.1 Zone Status Colors
- **Active Zone**: Full opacity, bright colors
- **Tested Zone**: Reduced opacity (60%), slightly faded
- **Broken Zone**: Dashed border, very low opacity (30%)
- **Flipped Zone**: Orange color scheme, special "F" label

#### 6.2.2 Zone Strength Indicators
```javascript
function getZoneOpacity(strength) {
    return Math.max(0.3, Math.min(1.0, strength * 0.8 + 0.2));
}

function getZoneBorderWidth(strength) {
    return Math.max(1, Math.min(3, strength * 2 + 1));
}
```

---

## 7. Error Handling & Edge Cases

### 7.1 Data Quality Issues

#### 7.1.1 Missing Data Handling
```python
def validate_input_data(df):
    """
    Validate input OHLC data quality
    - Check for missing values
    - Validate price sequence
    - Ensure minimum data points
    """
    if df is None or len(df) < 50:
        raise ValueError("Insufficient data for zone detection")
    
    required_columns = ['open', 'high', 'low', 'close', 'volume', 'time']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
```

#### 7.1.2 Invalid Price Data
```python
def validate_price_data(df):
    """
    Validate price data integrity
    - Check for negative prices
    - Validate OHLC relationships
    - Identify data gaps
    """
    if (df[['open', 'high', 'low', 'close']] < 0).any().any():
        raise ValueError("Negative prices detected")
    
    if not (df['low'] <= df['open']).all():
        raise ValueError("Invalid OHLC relationship: low > open")
```

### 7.2 Algorithm Edge Cases

#### 7.2.1 No Base Candles Found
```python
def handle_no_base_candles(df, index):
    """
    Handle case where no base candles are detected
    - Log warning
    - Return empty zone list
    - Continue processing
    """
    logger.warning(f"No base candles found at index {index}")
    return []
```

#### 7.2.2 Overlapping Zones
```python
def resolve_overlapping_zones(zones):
    """
    Resolve overlapping zone conflicts
    - Merge similar zones
    - Prioritize by strength
    - Maintain zone hierarchy
    """
    resolved_zones = []
    for zone in zones:
        overlapping = find_overlapping_zones(zone, resolved_zones)
        if overlapping:
            merged_zone = merge_zones(zone, overlapping)
            resolved_zones.append(merged_zone)
        else:
            resolved_zones.append(zone)
    return resolved_zones
```

### 7.3 Performance Edge Cases

#### 7.3.1 Large Dataset Handling
```python
def process_large_dataset(df, max_zones=1000):
    """
    Handle large datasets efficiently
    - Implement sliding window
    - Limit zone count
    - Use memory-efficient processing
    """
    if len(df) > 10000:
        # Process in chunks
        chunk_size = 1000
        zones = []
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            chunk_zones = detect_zones_chunk(chunk)
            zones.extend(chunk_zones)
        return zones[-max_zones:]  # Keep only recent zones
```

#### 7.3.2 Memory Management
```python
def manage_zone_memory(zone_cache, max_size=500):
    """
    Implement LRU cache for zone storage
    - Remove oldest zones when limit reached
    - Prioritize active zones
    - Efficient memory usage
    """
    if len(zone_cache) >= max_size:
        # Remove oldest inactive zones
        inactive_zones = [z for z in zone_cache if z.status != 'active']
        if inactive_zones:
            oldest_zone = min(inactive_zones, key=lambda z: z.last_accessed)
            zone_cache.remove(oldest_zone)
```

---

## 8. Testing Requirements

### 8.1 Unit Test Categories

#### 8.1.1 Base Candle Detection Tests
- Test consolidation identification
- Test ATR calculation accuracy
- Test edge cases (single candle, no volatility)
- Test performance benchmarks

#### 8.1.2 Zone Boundary Tests
- Test coordinate calculation precision
- Test rectangle drawing accuracy
- Test boundary validation
- Test edge cases (zero height, invalid coordinates)

#### 8.1.3 Confluence Integration Tests
- Test scoring algorithm accuracy
- Test database integration
- Test API endpoint functionality
- Test real-time updates

### 8.2 Integration Test Categories

#### 8.2.1 End-to-End Workflow Tests
- Test complete zone detection pipeline
- Test visualization rendering
- Test database persistence
- Test performance under load

#### 8.2.2 Historical Data Validation
- Test against known supply/demand setups
- Validate zone accuracy vs manual analysis
- Test multi-timeframe consistency
- Test zone flip detection accuracy

### 8.3 Performance Test Categories

#### 8.3.1 Speed Benchmarks
- Zone detection: <50ms per update
- Rectangle drawing: <30ms per chart
- Confluence calculation: <20ms per bar
- Total system impact: <100ms

#### 8.3.2 Memory Benchmarks
- Zone storage: <1MB per 1000 zones
- Cache efficiency: >90% hit rate
- Database queries: <10ms per lookup
- Memory leak detection: 0% growth over 24h

---

## 9. Deployment Considerations

### 9.1 Environment Requirements

#### 9.1.1 Development Environment
- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (for frontend)
- TradingView Charting Library

#### 9.1.2 Production Environment
- High-frequency trading VPS
- 16GB+ RAM recommended
- SSD storage for database
- Low-latency network connection

### 9.2 Configuration Management

#### 9.2.1 Algorithm Parameters
```yaml
# supply_demand_config.yaml
base_candle_detection:
  consolidation_threshold: 0.5
  min_base_candles: 2
  max_base_candles: 10
  body_size_threshold: 0.3

big_move_detection:
  move_threshold: 2.0
  min_move_candles: 3
  breakout_confirmation: true
  momentum_filter: true

zone_management:
  max_zones_per_timeframe: 100
  zone_expiry_hours: 168  # 1 week
  auto_cleanup: true

visualization:
  default_colors:
    supply: "#FF4444"
    demand: "#44FF44"
    continuation: "#4444FF"
  default_transparency: 80
```

### 9.3 Monitoring & Logging

#### 9.3.1 Performance Monitoring
```python
# Performance metrics to track
PERFORMANCE_METRICS = {
    'zone_detection_time': 'ms',
    'rectangle_drawing_time': 'ms',
    'confluence_calculation_time': 'ms',
    'database_query_time': 'ms',
    'memory_usage': 'MB',
    'cache_hit_rate': '%'
}
```

#### 9.3.2 Business Logic Monitoring
```python
# Business metrics to track
BUSINESS_METRICS = {
    'zones_detected_per_hour': 'count',
    'zone_test_success_rate': '%',
    'zone_flip_detection_rate': '%',
    'confluence_accuracy': '%',
    'false_positive_rate': '%'
}
```

---

## 10. Future Enhancements

### 10.1 Advanced Features (Phase 2)

#### 10.1.1 Machine Learning Integration
- Zone quality prediction using ML models
- Automated parameter optimization
- Pattern recognition for zone validation
- Predictive zone expiry modeling

#### 10.1.2 Multi-Asset Correlation
- Cross-asset zone influence analysis
- Currency correlation impact on zones
- Index vs individual stock zone relationships
- Commodity zone impact on currencies

### 10.2 Scalability Improvements

#### 10.2.1 Distributed Processing
- Parallel zone detection across timeframes
- Distributed database sharding
- Load balancing for high-frequency updates
- Microservices architecture

#### 10.2.2 Real-time Streaming
- WebSocket-based zone updates
- Event-driven zone state changes
- Real-time confluence score updates
- Live zone flip notifications

---

## 11. Conclusion

The Supply & Demand Zone Detection System represents a professional-grade implementation of institutional order flow analysis. By following the eWavesHarmonics methodology and integrating seamlessly with the existing confluence architecture, this system will significantly enhance the trading strategy's accuracy and performance.

The system's modular design, comprehensive error handling, and performance optimization ensure it meets the demanding requirements of high-frequency trading environments while maintaining the flexibility needed for continuous improvement and enhancement.

---

## 12. Appendices

### Appendix A: eWavesHarmonics Reference Materials
- Base candle identification methodology
- Zone drawing precision requirements
- Institutional order flow concepts
- Elliott Wave integration principles

### Appendix B: Performance Benchmarks
- Speed requirements breakdown
- Memory usage calculations
- Database query optimization
- Cache efficiency targets

### Appendix C: Integration Points
- Confluence engine modifications
- Database schema changes
- API endpoint additions
- Frontend component updates

---

**Document Status**: Draft - Requires Review and Approval
**Next Steps**: API Documentation → Test Specifications → Implementation
**Dependencies**: Existing confluence system, PostgreSQL database, TradingView charts
**Timeline**: 2-3 weeks for complete implementation