nvm install --lts# Testing Strategy - Fibonacci Trading Bot Project

## Overview
This document outlines the comprehensive testing strategy for the Fibonacci-based AI trading bot, covering all testing levels from unit tests to production validation.

## Testing Philosophy

### Testing Principles
1. **Test-Driven Development (TDD)**: Write tests before implementation
2. **Continuous Testing**: Automated testing in CI/CD pipeline
3. **Risk-Based Testing**: Focus on high-risk, high-impact components
4. **Performance Testing**: Ensure system meets latency and throughput requirements
5. **Financial Accuracy**: Zero tolerance for calculation errors in trading logic

### Testing Pyramid
```
                    /\
                   /  \
                  /E2E \     End-to-End Tests (5%)
                 /______\
                /        \
               /Integration\ Integration Tests (25%)
              /__________\
             /            \
            /   Unit Tests  \  Unit Tests (70%)
           /________________\
```

## Testing Levels

### 1. Unit Testing (70% of test effort)

#### Scope
- Individual functions and methods
- Core algorithms (fractals, Fibonacci calculations)
- Data processing functions
- Mathematical computations
- Configuration handling

#### Framework
- **Primary**: pytest
- **Coverage**: pytest-cov
- **Mocking**: pytest-mock
- **Async**: pytest-asyncio

#### Coverage Requirements
- **Minimum**: 90% line coverage
- **Target**: 95% line coverage
- **Critical Components**: 100% coverage (trading calculations, risk management)

#### Unit Test Structure
```python
# tests/unit/test_fractal_detector.py
import pytest
import pandas as pd
import numpy as np
from src.core.fractals import FractalDetector

class TestFractalDetector:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLC data for testing."""
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'Open': np.random.uniform(1.0, 1.1, 100),
            'High': np.random.uniform(1.05, 1.15, 100),
            'Low': np.random.uniform(0.95, 1.05, 100),
            'Close': np.random.uniform(1.0, 1.1, 100),
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
        data['High'] = np.maximum(data['High'], np.maximum(data['Open'], data['Close']))
        data['Low'] = np.minimum(data['Low'], np.minimum(data['Open'], data['Close']))
        
        return data
    
    @pytest.fixture
    def fractal_detector(self):
        """Create FractalDetector instance."""
        return FractalDetector(bars_range=2)
    
    def test_detect_up_fractals(self, fractal_detector, sample_data):
        """Test up fractal detection."""
        up_fractals = fractal_detector.detect_up_fractals(sample_data)
        
        assert isinstance(up_fractals, list)
        assert all(isinstance(f, tuple) and len(f) == 3 for f in up_fractals)
        assert all(f[2] == 'up' for f in up_fractals)
    
    def test_detect_down_fractals(self, fractal_detector, sample_data):
        """Test down fractal detection."""
        down_fractals = fractal_detector.detect_down_fractals(sample_data)
        
        assert isinstance(down_fractals, list)
        assert all(isinstance(f, tuple) and len(f) == 3 for f in down_fractals)
        assert all(f[2] == 'down' for f in down_fractals)
    
    def test_fractal_validation(self, fractal_detector):
        """Test fractal validation with known data."""
        # Create data with known fractal at index 2
        data = pd.DataFrame({
            'High': [1.0, 1.1, 1.2, 1.1, 1.0],  # Peak at index 2
            'Low': [0.9, 0.8, 0.9, 0.8, 0.9],
            'Open': [0.95, 0.95, 0.95, 0.95, 0.95],
            'Close': [0.95, 0.95, 0.95, 0.95, 0.95]
        })
        
        up_fractals = fractal_detector.detect_up_fractals(data)
        assert len(up_fractals) == 1
        assert up_fractals[0][1] == 1.2  # Price at fractal
    
    def test_empty_data(self, fractal_detector):
        """Test behavior with empty data."""
        empty_data = pd.DataFrame()
        
        up_fractals = fractal_detector.detect_up_fractals(empty_data)
        down_fractals = fractal_detector.detect_down_fractals(empty_data)
        
        assert up_fractals == []
        assert down_fractals == []
    
    def test_insufficient_data(self, fractal_detector):
        """Test behavior with insufficient data."""
        small_data = pd.DataFrame({
            'High': [1.0, 1.1],
            'Low': [0.9, 0.8],
            'Open': [0.95, 0.95],
            'Close': [0.95, 0.95]
        })
        
        up_fractals = fractal_detector.detect_up_fractals(small_data)
        assert up_fractals == []
    
    @pytest.mark.parametrize("bars_range", [1, 2, 3, 4, 5])
    def test_different_bars_range(self, sample_data, bars_range):
        """Test fractal detection with different bars_range values."""
        detector = FractalDetector(bars_range=bars_range)
        
        up_fractals = detector.detect_up_fractals(sample_data)
        down_fractals = detector.detect_down_fractals(sample_data)
        
        # Should return valid results for all ranges
        assert isinstance(up_fractals, list)
        assert isinstance(down_fractals, list)
```

### 2. Integration Testing (25% of test effort)

#### Scope
- Component interactions
- Data pipeline integration
- MT5 interface integration
- Database operations
- API endpoints

#### Integration Test Categories

##### Data Pipeline Integration
```python
# tests/integration/test_data_pipeline.py
import pytest
from src.data.mt5_interface import mt5_interface
from src.data.data_collector import data_collector
from src.data.realtime_stream import realtime_stream

class TestDataPipelineIntegration:
    
    @pytest.mark.integration
    async def test_mt5_to_collector_integration(self):
        """Test MT5 interface integration with data collector."""
        
        # Connect to MT5
        assert mt5_interface.connect()
        
        # Collect data
        symbol_data = data_collector.collect_symbol_data(
            symbol="EURUSD",
            timeframes=["M1", "M5"],
            days_back=1
        )
        
        assert "M1" in symbol_data
        assert "M5" in symbol_data
        assert not symbol_data["M1"].empty
        assert not symbol_data["M5"].empty
        
        # Verify data quality
        for timeframe, data in symbol_data.items():
            assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
            assert data['High'].ge(data[['Open', 'Close']].max(axis=1)).all()
            assert data['Low'].le(data[['Open', 'Close']].min(axis=1)).all()
    
    @pytest.mark.integration
    async def test_realtime_stream_integration(self):
        """Test real-time streaming integration."""
        
        # Start streaming
        await realtime_stream.start_streaming()
        
        # Wait for some data
        await asyncio.sleep(5)
        
        # Check data received
        current_prices = realtime_stream.get_current_prices()
        assert len(current_prices) > 0
        
        for symbol, price_data in current_prices.items():
            assert 'bid' in price_data
            assert 'ask' in price_data
            assert price_data['ask'] >= price_data['bid']
        
        await realtime_stream.stop_streaming()
```

##### Algorithm Integration
```python
# tests/integration/test_algorithm_integration.py
class TestAlgorithmIntegration:
    
    @pytest.mark.integration
    def test_fractal_to_fibonacci_integration(self):
        """Test integration between fractal detection and Fibonacci calculation."""
        
        # Get historical data
        data = data_collector.load_data("EURUSD", "H1")
        assert data is not None
        
        # Detect fractals
        fractal_detector = FractalDetector()
        fractals = fractal_detector.detect_fractals(data)
        assert len(fractals) > 0
        
        # Calculate Fibonacci levels
        fibonacci_calc = FibonacciCalculator()
        swings = fibonacci_calc.identify_swings(fractals)
        assert len(swings) > 0
        
        # Get Fibonacci levels
        if swings:
            latest_swing = swings[-1]
            fib_levels = fibonacci_calc.calculate_retracements(
                latest_swing['start_price'],
                latest_swing['end_price']
            )
            
            assert 'retracements' in fib_levels
            assert 'extensions' in fib_levels
            assert len(fib_levels['retracements']) == 5  # Standard levels
```

### 3. End-to-End Testing (5% of test effort)

#### Scope
- Complete trading workflows
- System integration scenarios
- User journey testing
- Performance under load

#### E2E Test Scenarios

##### Complete Trading Workflow
```python
# tests/e2e/test_trading_workflow.py
@pytest.mark.e2e
class TestTradingWorkflow:
    
    async def test_complete_trading_cycle(self):
        """Test complete trading cycle from signal to execution."""
        
        # 1. Initialize system
        await system_startup()
        
        # 2. Wait for market data
        await wait_for_market_data()
        
        # 3. Generate trading signal
        signal = await strategy_engine.generate_signal("EURUSD")
        
        if signal and signal['action'] != 'HOLD':
            # 4. Risk management check
            risk_check = risk_manager.validate_trade(signal)
            assert risk_check['approved']
            
            # 5. Execute trade (paper trading)
            trade_result = await trade_executor.execute_paper_trade(signal)
            assert trade_result['status'] == 'EXECUTED'
            
            # 6. Monitor position
            position = await position_manager.get_position(trade_result['order_id'])
            assert position is not None
            
            # 7. Close position
            close_result = await trade_executor.close_position(position['id'])
            assert close_result['status'] == 'CLOSED'
```

## Performance Testing

### Performance Requirements
| Component | Metric | Requirement | Test Method |
|-----------|--------|-------------|-------------|
| Fractal Detection | Processing Speed | 1M bars in <10s | Load testing |
| Fibonacci Calculation | Latency | <100ms per calculation | Stress testing |
| Real-time Data | Tick Processing | >1000 ticks/second | Volume testing |
| Trade Execution | Order Latency | <500ms | Latency testing |
| Memory Usage | RAM Consumption | <8GB under load | Memory profiling |
| Database Operations | Query Response | <50ms average | Database testing |

### Performance Test Implementation
```python
# tests/performance/test_performance.py
import time
import psutil
import pytest
from memory_profiler import profile

class TestPerformance:
    
    @pytest.mark.performance
    def test_fractal_detection_performance(self):
        """Test fractal detection performance with large dataset."""
        
        # Generate large dataset (1M bars)
        large_data = generate_large_dataset(1_000_000)
        
        fractal_detector = FractalDetector()
        
        start_time = time.time()
        fractals = fractal_detector.detect_fractals(large_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 10.0, f"Processing took {processing_time:.2f}s, expected <10s"
        
        # Verify results quality
        assert len(fractals) > 0
        assert len(fractals) < len(large_data) * 0.1  # Reasonable fractal density
    
    @pytest.mark.performance
    @profile
    def test_memory_usage(self):
        """Test memory usage under normal operation."""
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate normal operation
        for _ in range(100):
            data = data_collector.load_data("EURUSD", "M1")
            fractals = fractal_detector.detect_fractals(data)
            fib_levels = fibonacci_calc.calculate_levels(fractals)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
    
    @pytest.mark.performance
    async def test_realtime_throughput(self):
        """Test real-time data processing throughput."""
        
        tick_count = 0
        start_time = time.time()
        
        def count_ticks(tick_data):
            nonlocal tick_count
            tick_count += 1
        
        realtime_stream.subscribe('tick', count_ticks)
        await realtime_stream.start_streaming()
        
        # Run for 10 seconds
        await asyncio.sleep(10)
        
        await realtime_stream.stop_streaming()
        end_time = time.time()
        
        ticks_per_second = tick_count / (end_time - start_time)
        assert ticks_per_second > 100, f"Only processed {ticks_per_second:.2f} ticks/second"
```

## Test Data Management

### Test Data Strategy
1. **Synthetic Data**: Generated data for unit tests
2. **Historical Data**: Real market data for integration tests
3. **Mock Data**: Simulated responses for external services
4. **Edge Cases**: Boundary conditions and error scenarios

### Test Data Generation
```python
# tests/fixtures/data_generators.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TestDataGenerator:
    
    @staticmethod
    def generate_trending_data(bars: int = 1000, trend_strength: float = 0.7):
        """Generate trending market data."""
        dates = pd.date_range('2023-01-01', periods=bars, freq='H')
        
        # Generate trending price series
        trend = np.cumsum(np.random.normal(0.0001 * trend_strength, 0.0001, bars))
        base_price = 1.1000
        
        close_prices = base_price + trend
        
        # Generate OHLC from close prices
        data = pd.DataFrame(index=dates)
        data['Close'] = close_prices
        data['Open'] = data['Close'].shift(1).fillna(close_prices[0])
        
        # Add realistic high/low with some noise
        hl_range = np.random.uniform(0.0005, 0.002, bars)
        data['High'] = np.maximum(data['Open'], data['Close']) + hl_range * 0.7
        data['Low'] = np.minimum(data['Open'], data['Close']) - hl_range * 0.3
        
        data['Volume'] = np.random.randint(1000, 10000, bars)
        
        return data
    
    @staticmethod
    def generate_ranging_data(bars: int = 1000, range_size: float = 0.01):
        """Generate ranging market data."""
        dates = pd.date_range('2023-01-01', periods=bars, freq='H')
        base_price = 1.1000
        
        # Generate ranging price series
        noise = np.random.normal(0, range_size/4, bars)
        sine_wave = np.sin(np.linspace(0, 4*np.pi, bars)) * range_size/2
        
        close_prices = base_price + noise + sine_wave
        
        data = pd.DataFrame(index=dates)
        data['Close'] = close_prices
        data['Open'] = data['Close'].shift(1).fillna(close_prices[0])
        
        hl_range = np.random.uniform(0.0002, 0.001, bars)
        data['High'] = np.maximum(data['Open'], data['Close']) + hl_range * 0.6
        data['Low'] = np.minimum(data['Open'], data['Close']) - hl_range * 0.4
        
        data['Volume'] = np.random.randint(500, 5000, bars)
        
        return data
```

## Test Automation

### CI/CD Pipeline Testing
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v -m "not mt5_required"
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v --benchmark-only
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Test Execution Strategy

#### Local Development
```bash
# Quick unit tests
pytest tests/unit/ -v

# Integration tests (requires MT5)
pytest tests/integration/ -v -m "mt5_required"

# Performance tests
pytest tests/performance/ -v --benchmark

# Full test suite
pytest tests/ -v --cov=src --cov-report=html
```

#### Continuous Integration
- **On every commit**: Unit tests + fast integration tests
- **On pull request**: Full test suite including performance tests
- **Nightly builds**: Extended test suite with real market data
- **Release candidates**: Complete E2E testing including manual verification

## Quality Gates

### Test Coverage Requirements
- **Unit Tests**: 90% minimum, 95% target
- **Integration Tests**: 80% of integration points covered
- **E2E Tests**: All critical user journeys covered
- **Performance Tests**: All performance requirements validated

### Test Quality Metrics
- **Test Execution Time**: Unit tests <5 minutes, full suite <30 minutes
- **Test Reliability**: <1% flaky test rate
- **Test Maintenance**: Tests updated with code changes
- **Bug Detection**: 90% of bugs caught by automated tests

### Release Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Performance benchmarks met
- [ ] Code coverage targets achieved
- [ ] No critical security vulnerabilities
- [ ] Manual testing checklist completed
- [ ] Documentation updated

## Risk-Based Testing

### High-Risk Components (Extra Testing Focus)
1. **Trading Calculations**: Fibonacci levels, position sizing
2. **Risk Management**: Stop loss, position limits
3. **Order Execution**: Trade placement, modification
4. **Data Accuracy**: Price feeds, historical data
5. **Connection Handling**: MT5 connectivity, reconnection

### Testing Priorities
1. **Critical**: Trading logic, risk management, data accuracy
2. **High**: User interface, performance, security
3. **Medium**: Reporting, monitoring, configuration
4. **Low**: Documentation, logging, non-critical features

This comprehensive testing strategy ensures the trading bot is thoroughly validated at all levels, from individual components to complete trading workflows, with special attention to financial accuracy and system reliability.
