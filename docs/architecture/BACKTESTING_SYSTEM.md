# Comprehensive Visual Backtesting & Research System Plan

## Overview
Build a Python-based visual backtesting system with PostgreSQL storage that allows:
1. Visual verification of swing/fractal detection with TradingView-like charts
2. Replay functionality to step through historical data
3. Complete data storage for ML/AI training
4. Research dashboard separate from live trading

## Architecture Decision: Python + VectorBT + PostgreSQL + Lightweight Charts
- **VectorBT**: Fastest backtesting engine (1000x faster than alternatives)
- **PostgreSQL**: Store all data for historical analysis and ML training
- **Python**: Full control over visual verification and debugging
- **Lightweight Charts**: TradingView's open-source charting library
- **Data Sources**: MT4 (Nov 2024-present), expandable to other sources

## Phase 1: Enhanced Database Schema
Extend existing PostgreSQL database with new tables:

### New Tables:
1. **backtest_runs**
   ```sql
   - id: UUID primary key
   - run_date: timestamp
   - strategy_name: varchar
   - strategy_version: varchar
   - parameters: jsonb
   - date_range_start: timestamp
   - date_range_end: timestamp
   - symbol: varchar
   - timeframe: varchar
   - total_trades: integer
   - profit_factor: float
   - sharpe_ratio: float
   - max_drawdown: float
   - notes: text
   ```

2. **market_fractals**
   ```sql
   - id: UUID primary key
   - symbol: varchar
   - timeframe: varchar
   - timestamp: timestamp
   - fractal_type: varchar ('high', 'low')
   - price: float
   - strength: integer
   - validation_bars: integer
   - is_valid: boolean
   - created_at: timestamp
   ```

3. **market_swings**
   ```sql
   - id: UUID primary key
   - symbol: varchar
   - timeframe: varchar
   - start_timestamp: timestamp
   - end_timestamp: timestamp
   - start_price: float
   - end_price: float
   - direction: varchar ('up', 'down')
   - magnitude: float
   - fibonacci_levels: jsonb
   - fractal_start_id: UUID foreign key
   - fractal_end_id: UUID foreign key
   ```

4. **backtest_signals**
   ```sql
   - id: UUID primary key
   - backtest_run_id: UUID foreign key
   - timestamp: timestamp
   - signal_type: varchar ('entry', 'exit')
   - direction: varchar ('buy', 'sell')
   - price: float
   - fibonacci_level: float
   - swing_id: UUID foreign key
   - confidence: float
   - executed: boolean
   - outcome: varchar ('win', 'loss', 'breakeven', 'cancelled')
   - profit_loss: float
   ```

5. **market_context**
   ```sql
   - id: UUID primary key
   - symbol: varchar
   - timestamp: timestamp
   - market_regime: varchar ('trending', 'ranging', 'volatile')
   - volatility_level: float
   - session: varchar ('london', 'new_york', 'asian', 'overlap')
   - major_news: boolean
   - sentiment_score: float
   ```

## Phase 2: Data Import System
Build MT4/MT5 data importer:

### Implementation:
```python
# src/data/importers/mt4_importer.py
class MT4DataImporter:
    def __init__(self, mt4_history_path: str):
        self.history_path = mt4_history_path
        
    def import_data(self, symbol: str, timeframe: str, 
                   start_date: datetime, end_date: datetime):
        """Import historical data from MT4 history files"""
        
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate imported data"""
        
    def store_to_postgres(self, df: pd.DataFrame):
        """Store validated data in PostgreSQL"""
```

### Features:
- Import from MT4 history files (HST format)
- Support multiple timeframes (M1, M5, M15, H1, H4, D1)
- Data validation and gap filling
- Duplicate detection
- Progress tracking
- Error recovery

## Phase 3: TradingView-Style Visual Verification System
Create research dashboard at http://localhost:8001:

### Chart Features (Using Lightweight Charts):
1. **Professional Charting**
   - Full-screen mode (90% of viewport)
   - Candlestick/bar/line chart types
   - Multiple timeframe support
   - Smooth zooming and panning
   - Crosshair with OHLC display
   - Price and time scales

2. **Drawing Tools**
   - Horizontal lines (support/resistance)
   - Trend lines
   - Fibonacci retracement tool
   - Rectangle zones
   - Text annotations

3. **Technical Overlays**
   - Fractals with proper symbols (▲ for lows, ▼ for highs)
   - Swing highs/lows with directional arrows
   - Fibonacci levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
   - Entry/exit signals with labels
   - Stop loss/take profit lines

4. **Chart Controls**
   ```
   [<<] [<] [Play/Pause] [>] [>>] Speed: [1x▼]
   Jump to: [____-__-__ __:__] [Go]
   ```

### Layout Design:
```
+----------------------------------------------------------+
| Research Dashboard - Fibonacci Trading Bot               X |
+----------------------------------------------------------+
| File  View  Tools  Help                    [Full Screen]  |
+----------------------------------------------------------+
| Symbol: [EURUSD▼] Timeframe: [H1▼] | Connected ● | Settings|
+----------------------------------------------------------+
|                                                           |
|                    MAIN CHART AREA                        |
|                      (80% height)                         |
|                 [TradingView Charts]                      |
|                                                           |
+---------------------------+------------------------------+
| Debug Panel (Collapsible) | Data Inspector              |
| ▼ Fractal Detection      | Click any candle for details |
|   - High @ 1.0950        | Current Bar: 2024-01-15 14:00|
|   - Validation: 5 bars   | Open: 1.0920                 |
| ▼ Swing Analysis         | High: 1.0950                 |
|   - Upswing confirmed    | Low: 1.0915                  |
|   - Length: 120 pips     | Close: 1.0945                |
+---------------------------+------------------------------+
| Performance Metrics (Bottom Panel - Collapsible)          |
| P&L: +$1,250 | Trades: 45 | Win Rate: 65% | PF: 1.8     |
+----------------------------------------------------------+
```

### Additional Panels:
1. **Debug Panel** (Left sidebar - collapsible)
   - Real-time calculation display
   - Step-by-step logic explanation
   - Parameter values at each bar
   - Decision tree visualization

2. **Data Inspector** (Right sidebar)
   - Click any candle for full details
   - All indicators at that timestamp
   - Historical signals at that point
   - Export functionality

3. **Performance Metrics** (Bottom panel)
   - Running P&L chart
   - Trade list with entry/exit details
   - Statistics updated in real-time
   - Equity curve visualization

## Phase 4: Backtesting Engine
Implement VectorBT-based backtester:

### Core Components:
```python
# src/backtesting/engine.py
class FibonacciBacktester:
    def __init__(self, data: pd.DataFrame, parameters: dict):
        self.data = data
        self.parameters = parameters
        
    def detect_fractals(self) -> pd.DataFrame:
        """Vectorized fractal detection"""
        
    def identify_swings(self, fractals: pd.DataFrame) -> pd.DataFrame:
        """Vectorized swing identification"""
        
    def generate_signals(self, swings: pd.DataFrame) -> pd.DataFrame:
        """Generate entry/exit signals based on Fibonacci levels"""
        
    def run_backtest(self) -> BacktestResults:
        """Execute full backtest with VectorBT"""
```

### Features:
1. **Strategy Executor**
   - Vectorized operations for speed
   - Parameter optimization grid search
   - Walk-forward analysis
   - Multi-timeframe support
   - Slippage and commission modeling

2. **Performance Analytics**
   - Sharpe ratio, Sortino ratio
   - Maximum drawdown analysis
   - Win rate by market condition
   - Monte Carlo simulations
   - Risk-adjusted returns

3. **Database Integration**
   - Store every backtest run
   - Save all intermediate calculations
   - Track parameter evolution
   - Version control for strategies
   - Performance comparison tools

## Phase 5: Research Tools
Advanced analysis capabilities:

### Pattern Discovery
```python
# src/research/pattern_analysis.py
class PatternAnalyzer:
    def find_best_setups(self) -> List[TradingSetup]:
        """Identify highest probability setups"""
        
    def analyze_failures(self) -> List[FailurePattern]:
        """Find common failure patterns"""
        
    def market_regime_analysis(self) -> MarketRegimeReport:
        """Performance by market conditions"""
```

### Statistical Analysis
1. **Entry Analysis**
   - Success rate by Fibonacci level
   - Optimal entry timing
   - Price action confirmation patterns

2. **Risk Management**
   - Optimal stop loss placement
   - Position sizing effectiveness
   - Maximum adverse excursion analysis

3. **Session Analysis**
   - Performance by trading session
   - Best times to trade
   - Session overlap opportunities

### Export Features
- PDF reports with charts
- Excel workbooks with detailed data
- CSV exports for external analysis
- ML-ready datasets
- Chart snapshots and annotations

## Phase 6: Confluence Factor Testing Infrastructure ✅ NEW
Implement comprehensive factor testing and validation system:

### Factor Testing Architecture
```python
# src/backtesting/factor_tester.py
class FactorTester:
    """Systematic testing of confluence factor combinations"""
    
    def __init__(self, backtesting_engine: BacktestingEngine):
        self.engine = backtesting_engine
        self.factor_registry = FactorRegistry()
        self.test_results = TestResultsDatabase()
    
    def test_single_factor(self, factor_name: str, test_periods: List[DateRange]) -> FactorTestResult:
        """Test individual factor across multiple time periods"""
        
    def test_factor_combination(self, factors: List[str], weights: Dict[str, float]) -> CombinationTestResult:
        """Test specific factor combination with given weights"""
        
    def run_exhaustive_testing(self, max_factors: int = 5) -> ExhaustiveTestResults:
        """Test all possible combinations up to max_factors"""
        
    def factor_importance_analysis(self, factors: List[str]) -> FactorImportanceReport:
        """Analyze individual factor contributions using statistical methods"""
        
    def optimal_weight_discovery(self, factors: List[str]) -> OptimalWeights:
        """Find optimal weights using grid search or optimization algorithms"""
```

### Testing Methodologies

#### 1. A/B Testing Framework 🧪
```python
class ABTestFramework:
    """Statistical A/B testing for factors"""
    
    def compare_factors(self, factor_a: str, factor_b: str) -> ABTestResult:
        """Head-to-head factor comparison with statistical significance"""
        
    def baseline_vs_enhanced(self, baseline_factors: List[str], 
                           enhancement_factor: str) -> BaselineTestResult:
        """Test if adding enhancement factor improves baseline performance"""
        
    def multi_arm_bandit_test(self, factor_combinations: List[Dict]) -> BanditTestResult:
        """Dynamic allocation testing for multiple factor combinations"""
```

#### 2. Walk-Forward Analysis 📈
```python
class WalkForwardTester:
    """Time-series specific testing with proper temporal validation"""
    
    def walk_forward_optimization(self, factors: List[str], 
                                in_sample_period: int, 
                                out_sample_period: int) -> WalkForwardResults:
        """Rolling optimization with out-of-sample validation"""
        
    def regime_based_testing(self, factors: List[str]) -> RegimeTestResults:
        """Test factor performance across different market regimes"""
        
    def stability_analysis(self, factors: List[str]) -> StabilityReport:
        """Analyze factor performance stability over time"""
```

### Factor Performance Metrics

#### 1. Statistical Validation 📊
```python
class FactorMetrics:
    """Comprehensive factor performance measurement"""
    
    def calculate_factor_significance(self, factor_results: FactorTestResult) -> SignificanceTest:
        """Statistical significance testing (t-test, Mann-Whitney U, etc.)"""
        
    def information_ratio(self, factor_returns: List[float], benchmark_returns: List[float]) -> float:
        """Risk-adjusted excess return measurement"""
        
    def factor_turnover(self, factor_signals: List[Signal]) -> TurnoverMetrics:
        """Signal frequency and transaction cost impact"""
        
    def regime_robustness(self, factor_results: List[FactorTestResult]) -> RobustnessScore:
        """Performance consistency across market conditions"""
```

#### 2. Risk Assessment 🛡️
```python
class FactorRiskAnalysis:
    """Risk-focused factor evaluation"""
    
    def drawdown_analysis(self, factor_equity_curve: List[float]) -> DrawdownMetrics:
        """Maximum drawdown, recovery time, drawdown frequency"""
        
    def tail_risk_assessment(self, factor_returns: List[float]) -> TailRiskMetrics:
        """VaR, CVaR, extreme loss probability"""
        
    def correlation_analysis(self, factors: List[str]) -> CorrelationMatrix:
        """Factor correlation and diversification benefits"""
        
    def overfitting_detection(self, in_sample: TestResult, out_sample: TestResult) -> OverfitScore:
        """Detect overfitting through performance degradation"""
```

### Testing Database Schema

#### Extended Database Tables for Factor Testing
```sql
-- Factor test runs and results
CREATE TABLE factor_test_runs (
    id UUID PRIMARY KEY,
    test_type VARCHAR(50) NOT NULL, -- 'single_factor', 'combination', 'exhaustive'
    factors_tested JSONB NOT NULL,
    factor_weights JSONB,
    test_period_start TIMESTAMP NOT NULL,
    test_period_end TIMESTAMP NOT NULL,
    market_regime VARCHAR(20), -- 'bull', 'bear', 'sideways', 'volatile'
    total_trades INTEGER,
    win_rate FLOAT,
    profit_factor FLOAT,
    sharpe_ratio FLOAT,
    sortino_ratio FLOAT,
    max_drawdown FLOAT,
    calmar_ratio FLOAT,
    statistical_significance FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual factor performance tracking
CREATE TABLE factor_performance (
    id UUID PRIMARY KEY,
    factor_name VARCHAR(100) NOT NULL,
    test_run_id UUID REFERENCES factor_test_runs(id),
    individual_contribution FLOAT,
    correlation_with_returns FLOAT,
    signal_frequency INTEGER,
    avg_signal_strength FLOAT,
    factor_stability_score FLOAT,
    implementation_cost_ms FLOAT
);

-- Factor combination optimization results
CREATE TABLE factor_combinations (
    id UUID PRIMARY KEY,
    combination_hash VARCHAR(64) UNIQUE, -- Hash of factor names + weights
    factors JSONB NOT NULL,
    optimal_weights JSONB NOT NULL,
    performance_score FLOAT,
    risk_score FLOAT,
    combined_score FLOAT,
    optimization_method VARCHAR(50), -- 'grid_search', 'genetic_algorithm', 'bayesian'
    validation_score FLOAT, -- Out-of-sample performance
    last_tested TIMESTAMP DEFAULT NOW()
);

-- A/B test results for statistical comparison
CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY,
    test_name VARCHAR(200) NOT NULL,
    factor_a JSONB NOT NULL,
    factor_b JSONB NOT NULL,
    test_duration_days INTEGER,
    trades_a INTEGER,
    trades_b INTEGER,
    returns_a FLOAT,
    returns_b FLOAT,
    p_value FLOAT,
    confidence_level FLOAT,
    winner VARCHAR(1), -- 'A', 'B', or 'N' (no significant difference)
    effect_size FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Factor Testing Workflows

#### 1. New Factor Integration Workflow 🔄
```python
class FactorIntegrationPipeline:
    """Standardized process for adding new factors"""
    
    def validate_new_factor(self, factor: ConfluenceFactor) -> ValidationResult:
        """
        1. Interface compliance check
        2. Performance benchmarking
        3. Data requirement validation
        4. Computational cost assessment
        """
        
    def baseline_performance_test(self, factor: ConfluenceFactor) -> BaselineTest:
        """
        Test factor in isolation against random signals and 
        basic Fibonacci-only signals
        """
        
    def integration_test(self, factor: ConfluenceFactor, 
                        existing_factors: List[str]) -> IntegrationTest:
        """
        Test factor in combination with existing best-performing factors
        """
        
    def production_readiness_check(self, factor: ConfluenceFactor) -> ReadinessReport:
        """
        Final validation before production deployment
        """
```

#### 2. Continuous Factor Monitoring 📡
```python
class FactorMonitor:
    """Real-time monitoring of factor performance in production"""
    
    def real_time_performance_tracking(self) -> PerformanceMetrics:
        """Track factor performance in live trading"""
        
    def regime_change_detection(self) -> RegimeChangeAlert:
        """Detect when market regime changes affect factor performance"""
        
    def factor_decay_analysis(self) -> DecayReport:
        """Monitor for factor performance degradation over time"""
        
    def auto_rebalancing_suggestions(self) -> RebalancingRecommendations:
        """Suggest factor weight adjustments based on recent performance"""
```

## Phase 7: ML/AI Integration Preparation
Enhanced ML infrastructure building on factor testing foundation:

### Feature Engineering Pipeline
```python
# src/ml/feature_engineering.py
class FeatureEngineer:
    def extract_price_features(self) -> pd.DataFrame:
        """Price-based features"""
        
    def extract_indicator_features(self) -> pd.DataFrame:
        """Technical indicator features"""
        
    def extract_pattern_features(self) -> pd.DataFrame:
        """Chart pattern features"""
        
    def create_training_dataset(self) -> pd.DataFrame:
        """Combine all features for ML"""
```

### Infrastructure:
1. **Feature Store**
   - Versioned feature sets
   - Feature importance tracking
   - Automated feature extraction
   - Feature validation

2. **Training Pipeline**
   - Data preprocessing
   - Train/test/validation splits
   - Cross-validation setup
   - Hyperparameter tracking

3. **Model Management**
   - Model versioning
   - A/B testing framework
   - Performance monitoring
   - Model explainability

## Technical Stack Details

### Frontend (Research Dashboard):
- **Framework**: React with TypeScript
- **Charting**: TradingView Lightweight Charts
- **UI Components**: Material-UI
- **State Management**: Redux Toolkit
- **WebSocket**: Socket.io for real-time updates
- **Build Tool**: Vite

### Backend:
- **API**: FastAPI (existing, extend with new endpoints)
- **Backtesting**: VectorBT
- **Database**: PostgreSQL with TimescaleDB
- **Task Queue**: Celery with Redis
- **Caching**: Redis for chart data

### Data Pipeline:
- **MT4 Import**: Custom Python parser
- **Data Validation**: Pandas + Great Expectations
- **Storage**: TimescaleDB for time-series optimization
- **Compression**: Native PostgreSQL compression

## Implementation Timeline
- **Week 1-2**: Database schema + MT4 data import ✅ COMPLETED
- **Week 3-4**: TradingView-style charting system ✅ COMPLETED
- **Week 5-6**: VectorBT integration + replay engine ✅ COMPLETED
- **Week 7-8**: Signal generation + factor testing infrastructure 🎯 CURRENT
- **Week 9-10**: Factor library + A/B testing framework
- **Week 11-12**: ML preparation + automated optimization

## Key Success Factors
1. **Visual First**: TradingView-quality charts for verification
2. **Store Everything**: Every calculation for debugging/ML
3. **Fast Iteration**: Sub-second backtests with VectorBT
4. **User Experience**: Professional, intuitive interface
5. **Production Ready**: Same algorithms for research and live

## File Structure
```
trading_bot/
├── src/
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── engine.py          # VectorBT integration ✅
│   │   ├── replay.py          # Chart replay system ✅
│   │   ├── analysis.py        # Statistical tools
│   │   ├── factor_tester.py   # Factor testing framework ✅ NEW
│   │   ├── signal_generator.py # Signal generation system 🎯 NEW
│   │   └── ml_prep.py         # ML data preparation
│   ├── research/
│   │   ├── __init__.py
│   │   ├── dashboard/         # Research web interface
│   │   │   ├── frontend/      # React application
│   │   │   └── api/          # FastAPI endpoints
│   │   ├── charts/           # TradingView integration
│   │   └── reports/          # Report generation
│   └── data/
│       └── importers/        # MT4/MT5 data importers
│           ├── __init__.py
│           ├── mt4_importer.py
│           └── mt5_importer.py
└── docs/
    ├── BACKTESTING_SYSTEM.md  # This document
    ├── VISUAL_VERIFICATION.md # Visual testing guide
    └── ML_PREPARATION.md      # ML integration guide
```

## Current Implementation Status (July 2025)

### ✅ Completed Components

#### 1. **Research Dashboard** - FULLY OPERATIONAL
- **Location**: http://localhost:8001 
- **TradingView Integration**: Complete with Lightweight Charts
- **Progressive Replay**: Step-by-step bar navigation with play/pause controls
- **Data Inspector**: Real-time OHLCV display for current bar
- **Professional Tools**: Cursor, crosshair, trend lines, zoom controls

#### 2. **Fractal Visualization System** - FULLY OPERATIONAL
- **Real-time Detection**: 5-bar fractal pattern recognition
- **Visual Display**: Red arrows (↑) for highs, blue arrows (↓) for lows
- **TradingView Markers**: Proper marker state management following official best practices
- **Progressive Loading**: Fractals accumulate correctly during navigation
- **Timing Synchronization**: Backend-frontend timestamp alignment resolved

#### 3. **Backend Strategy Engine** - FULLY OPERATIONAL
- **Fractal Detection**: 5-bar pattern with configurable period
- **Strategy Integration**: Real-time analysis with jump-to-bar functionality
- **Data Processing**: Handles 25k+ bars efficiently
- **API Endpoints**: `/api/backtest/jump/{position}`, `/api/backtest/load`

#### 4. **Database Integration** - OPERATIONAL
- **PostgreSQL**: TimescaleDB with market data storage
- **Data Import**: MT4 historical data successfully imported
- **Data Range**: DJ30 M1 (219k bars), EURUSD H1 (98 bars)
- **Query Performance**: Optimized for real-time backtesting

#### 5. **Technical Achievements** - COMPLETED
- **Position Synchronization**: Fixed critical timestamp mismatch issues
- **Performance Optimization**: Request throttling, stale response filtering
- **Error Handling**: Resource exhaustion prevention, robust error recovery
- **Navigation Stability**: Eliminated chart jumping and position calculation bugs

### 🔨 Recent Major Fixes (July 1, 2025)

#### Critical Issues Resolved:
1. **4-Day Timestamp Discrepancy**: Frontend showing June 2nd while backend processed June 6th
2. **TradingView Marker Loss**: Improper `setMarkers()` usage causing fractal disappearance
3. **Position Calculation Jumps**: Fixed massive position jumps (5→6662) in replay controls
4. **Resource Exhaustion**: Added throttling to prevent `ERR_INSUFFICIENT_RESOURCES` errors
5. **Fractal Arrow Directions**: Corrected high fractals pointing up, low fractals pointing down

### 🎯 Current Capabilities

The system now provides:
- **Stable fractal visualization** with correct timing and positioning
- **Real-time strategy analysis** with live fractal detection during navigation
- **Professional-grade charting** following TradingView best practices
- **Robust error handling** with comprehensive debugging capabilities
- **Scalable architecture** ready for additional strategy components

### 🔄 Next Implementation Phase

#### Immediate Priorities:
1. **Swing Detection Visualization**: Add swing line display between fractals
2. **Fibonacci Level Display**: Show retracement levels on chart
3. **Signal Generation**: Implement entry/exit signal detection and display
4. **Performance Analytics**: Add real-time strategy statistics
5. **ML Data Export**: Prepare fractal/swing data for machine learning

#### Technical Debt:
- Optimize fractal detection algorithm for larger datasets
- Add caching layer for frequently accessed fractals
- Implement historical fractal pattern analysis
- Add automated testing for fractal detection accuracy

The visual backtesting system is now production-ready for fractal analysis and serves as a solid foundation for advanced strategy development and machine learning integration.

## Legacy Planning - Next Steps
~~1. Set up database schema extensions~~ ✅ COMPLETED
~~2. Build MT4 data importer~~ ✅ COMPLETED  
~~3. Create basic research dashboard~~ ✅ COMPLETED
~~4. Integrate TradingView Lightweight Charts~~ ✅ COMPLETED
~~5. Implement replay functionality~~ ✅ COMPLETED
6. Add VectorBT backtesting engine ⏳ IN PROGRESS
7. Build statistical analysis tools
8. Prepare ML infrastructure

This comprehensive plan ensures professional-grade visual verification with TradingView-like functionality before any ML optimization, while building a robust foundation for future AI enhancements.