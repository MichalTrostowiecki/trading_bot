-- Confluence Testing Database Schema Extensions
-- Comprehensive schema for testing multiple confluence factors and ML integration

-- ============================================================================
-- CONFLUENCE FACTORS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES backtest_signals(id),
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    factor_type VARCHAR(50) NOT NULL,  -- 'fibonacci', 'volume', 'candlestick', etc.
    factor_value FLOAT NOT NULL,
    weight FLOAT NOT NULL DEFAULT 1.0,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    description TEXT,
    price_level FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_confluence_factors_timestamp (timestamp),
    INDEX idx_confluence_factors_symbol (symbol),
    INDEX idx_confluence_factors_type (factor_type),
    INDEX idx_confluence_factors_signal (signal_id)
);

-- ============================================================================
-- CONFLUENCE ZONES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    price_level FLOAT NOT NULL,
    total_factors INTEGER NOT NULL,
    total_score FLOAT NOT NULL,
    weighted_score FLOAT NOT NULL,
    strength VARCHAR(20) NOT NULL,  -- 'weak', 'moderate', 'strong'
    direction VARCHAR(10) NOT NULL, -- 'bullish', 'bearish', 'neutral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_confluence_zones_timestamp (timestamp),
    INDEX idx_confluence_zones_symbol (symbol),
    INDEX idx_confluence_zones_strength (strength),
    INDEX idx_confluence_zones_direction (direction)
);

-- ============================================================================
-- CONFLUENCE ZONE FACTORS RELATIONSHIP TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_zone_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES confluence_zones(id) ON DELETE CASCADE,
    factor_id UUID REFERENCES confluence_factors(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(zone_id, factor_id),
    INDEX idx_zone_factors_zone (zone_id),
    INDEX idx_zone_factors_factor (factor_id)
);

-- ============================================================================
-- CANDLESTICK PATTERNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS candlestick_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,  -- 'hammer', 'engulfing', 'doji', etc.
    price FLOAT NOT NULL,
    reliability FLOAT NOT NULL,
    direction VARCHAR(10) NOT NULL,     -- 'bullish', 'bearish', 'neutral'
    strength VARCHAR(20) NOT NULL,      -- 'weak', 'moderate', 'strong'
    confirmation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_candlestick_timestamp (timestamp),
    INDEX idx_candlestick_symbol (symbol),
    INDEX idx_candlestick_pattern (pattern_type),
    INDEX idx_candlestick_direction (direction)
);

-- ============================================================================
-- CONFLUENCE TEST CONFIGURATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_test_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    
    -- Confluence settings
    confluence_distance FLOAT NOT NULL DEFAULT 0.001,  -- % price distance
    min_factors INTEGER NOT NULL DEFAULT 2,
    
    -- Factor weights (JSON format)
    factor_weights JSON NOT NULL,
    
    -- Test parameters
    fibonacci_levels JSON NOT NULL,
    volume_spike_threshold FLOAT NOT NULL DEFAULT 1.5,
    rsi_overbought INTEGER NOT NULL DEFAULT 70,
    rsi_oversold INTEGER NOT NULL DEFAULT 30,
    
    -- Performance tracking
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_test_configs_name (config_name),
    INDEX idx_test_configs_active (is_active)
);

-- ============================================================================
-- CONFLUENCE TEST RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_config_id UUID REFERENCES confluence_test_configs(id),
    backtest_run_id UUID REFERENCES backtest_runs(id),
    
    -- Test period
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- Confluence metrics
    total_zones INTEGER NOT NULL DEFAULT 0,
    strong_zones INTEGER NOT NULL DEFAULT 0,
    moderate_zones INTEGER NOT NULL DEFAULT 0,
    weak_zones INTEGER NOT NULL DEFAULT 0,
    
    -- Trading performance
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    win_rate FLOAT NOT NULL DEFAULT 0.0,
    profit_factor FLOAT NOT NULL DEFAULT 0.0,
    max_drawdown FLOAT NOT NULL DEFAULT 0.0,
    total_return FLOAT NOT NULL DEFAULT 0.0,
    
    -- ML features (JSON format)
    ml_features JSON,
    
    -- Test metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_test_results_config (test_config_id),
    INDEX idx_test_results_backtest (backtest_run_id),
    INDEX idx_test_results_symbol (symbol),
    INDEX idx_test_results_period (start_date, end_date)
);

-- ============================================================================
-- CONFLUENCE ML FEATURES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_ml_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confluence_zone_id UUID REFERENCES confluence_zones(id),
    
    -- Basic features
    total_factors INTEGER NOT NULL,
    fibonacci_factors INTEGER NOT NULL DEFAULT 0,
    volume_factors INTEGER NOT NULL DEFAULT 0,
    candlestick_factors INTEGER NOT NULL DEFAULT 0,
    technical_factors INTEGER NOT NULL DEFAULT 0,
    
    -- Strength features
    avg_confidence FLOAT NOT NULL DEFAULT 0.0,
    max_confidence FLOAT NOT NULL DEFAULT 0.0,
    weighted_strength FLOAT NOT NULL DEFAULT 0.0,
    
    -- Price action features
    price_momentum FLOAT DEFAULT 0.0,
    volume_momentum FLOAT DEFAULT 0.0,
    volatility FLOAT DEFAULT 0.0,
    
    -- Market context features
    trend_strength FLOAT DEFAULT 0.0,
    market_session VARCHAR(20),
    time_of_day INTEGER, -- Hour of day
    
    -- Future outcome (for supervised learning)
    future_return_1h FLOAT,
    future_return_4h FLOAT,
    future_return_1d FLOAT,
    max_favorable_excursion FLOAT,
    max_adverse_excursion FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ml_features_zone (confluence_zone_id),
    INDEX idx_ml_features_factors (total_factors),
    INDEX idx_ml_features_outcome (future_return_1h)
);

-- ============================================================================
-- CONFLUENCE PERFORMANCE TRACKING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confluence_zone_id UUID REFERENCES confluence_zones(id),
    
    -- Entry details
    entry_timestamp TIMESTAMP NOT NULL,
    entry_price FLOAT NOT NULL,
    entry_direction VARCHAR(10) NOT NULL,
    
    -- Exit details
    exit_timestamp TIMESTAMP,
    exit_price FLOAT,
    exit_reason VARCHAR(50), -- 'target', 'stop', 'timeout', 'manual'
    
    -- Performance metrics
    pips_gained FLOAT,
    percentage_return FLOAT,
    trade_duration_minutes INTEGER,
    max_drawdown_pips FLOAT,
    max_runup_pips FLOAT,
    
    -- Risk metrics
    risk_amount FLOAT,
    reward_amount FLOAT,
    risk_reward_ratio FLOAT,
    
    -- Trade classification
    trade_outcome VARCHAR(10), -- 'win', 'loss', 'breakeven'
    trade_quality VARCHAR(20), -- 'excellent', 'good', 'poor'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_performance_zone (confluence_zone_id),
    INDEX idx_performance_entry (entry_timestamp),
    INDEX idx_performance_outcome (trade_outcome)
);

-- ============================================================================
-- DEFAULT CONFLUENCE TEST CONFIGURATIONS
-- ============================================================================
INSERT INTO confluence_test_configs (
    config_name, 
    description,
    confluence_distance,
    min_factors,
    factor_weights,
    fibonacci_levels,
    volume_spike_threshold,
    rsi_overbought,
    rsi_oversold
) VALUES 
(
    'default_confluence_test',
    'Default confluence testing configuration with balanced factor weights',
    0.001,
    2,
    '{
        "fibonacci": 1.5,
        "volume": 1.2,
        "candlestick": 1.0,
        "rsi": 0.8,
        "macd": 0.8,
        "abc_pattern": 2.0,
        "swing_level": 1.3,
        "support_resistance": 1.1,
        "timeframe": 1.8,
        "momentum": 0.9
    }',
    '[0.236, 0.382, 0.500, 0.618, 0.786]',
    1.5,
    70,
    30
),
(
    'fibonacci_heavy_test',
    'Fibonacci-focused confluence testing with higher Fibonacci weights',
    0.0015,
    3,
    '{
        "fibonacci": 2.5,
        "volume": 1.0,
        "candlestick": 1.2,
        "rsi": 0.6,
        "macd": 0.6,
        "abc_pattern": 1.8,
        "swing_level": 1.0,
        "support_resistance": 0.8,
        "timeframe": 1.5,
        "momentum": 0.7
    }',
    '[0.382, 0.500, 0.618, 0.786]',
    1.8,
    75,
    25
),
(
    'volume_price_action_test',
    'Volume and price action focused confluence testing',
    0.0008,
    2,
    '{
        "fibonacci": 1.2,
        "volume": 2.0,
        "candlestick": 2.2,
        "rsi": 1.0,
        "macd": 1.0,
        "abc_pattern": 1.5,
        "swing_level": 1.8,
        "support_resistance": 1.5,
        "timeframe": 1.2,
        "momentum": 1.3
    }',
    '[0.236, 0.382, 0.500, 0.618, 0.786]',
    2.0,
    80,
    20
);

-- ============================================================================
-- VIEWS FOR ANALYSIS
-- ============================================================================

-- View: Confluence zone summary with factor details
CREATE VIEW IF NOT EXISTS v_confluence_zone_summary AS
SELECT 
    cz.id,
    cz.timestamp,
    cz.symbol,
    cz.timeframe,
    cz.price_level,
    cz.total_factors,
    cz.total_score,
    cz.weighted_score,
    cz.strength,
    cz.direction,
    
    -- Factor breakdown
    COUNT(CASE WHEN cf.factor_type = 'fibonacci' THEN 1 END) as fibonacci_factors,
    COUNT(CASE WHEN cf.factor_type = 'volume' THEN 1 END) as volume_factors,
    COUNT(CASE WHEN cf.factor_type = 'candlestick' THEN 1 END) as candlestick_factors,
    COUNT(CASE WHEN cf.factor_type = 'rsi' THEN 1 END) as rsi_factors,
    
    -- Performance if available
    cp.trade_outcome,
    cp.percentage_return,
    cp.risk_reward_ratio
    
FROM confluence_zones cz
LEFT JOIN confluence_zone_factors czf ON cz.id = czf.zone_id
LEFT JOIN confluence_factors cf ON czf.factor_id = cf.id
LEFT JOIN confluence_performance cp ON cz.id = cp.confluence_zone_id
GROUP BY cz.id, cz.timestamp, cz.symbol, cz.timeframe, cz.price_level, 
         cz.total_factors, cz.total_score, cz.weighted_score, cz.strength, 
         cz.direction, cp.trade_outcome, cp.percentage_return, cp.risk_reward_ratio;

-- View: Daily confluence statistics
CREATE VIEW IF NOT EXISTS v_daily_confluence_stats AS
SELECT 
    DATE(timestamp) as trade_date,
    symbol,
    timeframe,
    COUNT(*) as total_zones,
    COUNT(CASE WHEN strength = 'strong' THEN 1 END) as strong_zones,
    COUNT(CASE WHEN strength = 'moderate' THEN 1 END) as moderate_zones,
    COUNT(CASE WHEN strength = 'weak' THEN 1 END) as weak_zones,
    AVG(total_score) as avg_score,
    AVG(weighted_score) as avg_weighted_score
FROM confluence_zones
GROUP BY DATE(timestamp), symbol, timeframe
ORDER BY trade_date DESC;

-- View: Confluence test performance summary
CREATE VIEW IF NOT EXISTS v_confluence_test_performance AS
SELECT 
    ctc.config_name,
    ctc.description,
    COUNT(ctr.id) as total_tests,
    AVG(ctr.win_rate) as avg_win_rate,
    AVG(ctr.profit_factor) as avg_profit_factor,
    AVG(ctr.total_return) as avg_return,
    AVG(ctr.max_drawdown) as avg_max_drawdown,
    SUM(ctr.total_trades) as total_trades,
    SUM(ctr.winning_trades) as total_winning_trades
FROM confluence_test_configs ctc
LEFT JOIN confluence_test_results ctr ON ctc.id = ctr.test_config_id
WHERE ctc.is_active = TRUE
GROUP BY ctc.id, ctc.config_name, ctc.description
ORDER BY avg_win_rate DESC;

-- ============================================================================
-- USEFUL QUERIES FOR ANALYSIS
-- ============================================================================

-- Query: Find strongest confluence zones by day
/*
SELECT 
    DATE(timestamp) as trade_date,
    symbol,
    COUNT(*) as strong_zones,
    AVG(weighted_score) as avg_score
FROM confluence_zones 
WHERE strength = 'strong'
GROUP BY DATE(timestamp), symbol
ORDER BY trade_date DESC, avg_score DESC;
*/

-- Query: Factor effectiveness analysis
/*
SELECT 
    cf.factor_type,
    COUNT(*) as total_occurrences,
    AVG(cf.confidence) as avg_confidence,
    AVG(cp.percentage_return) as avg_return,
    COUNT(CASE WHEN cp.trade_outcome = 'win' THEN 1 END) as winning_trades,
    COUNT(CASE WHEN cp.trade_outcome = 'loss' THEN 1 END) as losing_trades
FROM confluence_factors cf
JOIN confluence_zone_factors czf ON cf.id = czf.factor_id
JOIN confluence_zones cz ON czf.zone_id = cz.id
LEFT JOIN confluence_performance cp ON cz.id = cp.confluence_zone_id
GROUP BY cf.factor_type
ORDER BY avg_return DESC;
*/

-- Query: Best performing confluence combinations
/*
SELECT 
    GROUP_CONCAT(DISTINCT cf.factor_type ORDER BY cf.factor_type) as factor_combination,
    COUNT(*) as occurrences,
    AVG(cp.percentage_return) as avg_return,
    AVG(cp.risk_reward_ratio) as avg_risk_reward,
    COUNT(CASE WHEN cp.trade_outcome = 'win' THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM confluence_zones cz
JOIN confluence_zone_factors czf ON cz.id = czf.zone_id  
JOIN confluence_factors cf ON czf.factor_id = cf.id
LEFT JOIN confluence_performance cp ON cz.id = cp.confluence_zone_id
GROUP BY cz.id
HAVING COUNT(DISTINCT cf.factor_type) >= 2
ORDER BY avg_return DESC;
*/