# Comprehensive Testing Guide for Fibonacci Trading Bot

## 🎯 Overview

This guide covers the complete testing strategy for the Fibonacci Trading Bot, ensuring all trading logic is sound and reliable.

## 📁 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (70% of test effort)
│   ├── test_comprehensive_trading_logic.py
│   ├── test_frontend_logic.py
│   ├── test_strategy_edge_cases.py
│   └── test_fractal_detection.py
├── integration/                   # Integration tests (20% of test effort)
│   ├── test_backtesting_db.py
│   ├── test_research_dashboard.py
│   └── verify_fractal_system.py
└── performance/                   # Performance tests (10% of test effort)
    └── test_strategy_performance.py
```

## 🚀 Quick Start

### Install Test Dependencies
```bash
python run_tests.py --install-deps
```

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Categories
```bash
# Fractal detection tests
python run_tests.py --category fractal

# Swing detection tests  
python run_tests.py --category swing

# ABC pattern tests
python run_tests.py --category abc

# Frontend logic tests
python run_tests.py --category frontend
```

### Run with Coverage
```bash
python run_tests.py --unit --parallel
```

## 📊 Test Categories

### 1. Fractal Detection Tests (`@pytest.mark.fractal`)

**What's Tested:**
- Basic fractal detection with known patterns
- Fractal strength calculation
- Edge cases (minimal data, flat markets)
- Multi-timeframe fractal detection
- Fractal validation and filtering

**Key Test Cases:**
```python
def test_basic_fractal_detection():
    # Tests detection of clear high/low points
    
def test_fractal_strength_calculation():
    # Tests fractal strength metrics
    
def test_edge_case_handling():
    # Tests minimal data, empty data scenarios
```

### 2. Swing Detection Tests (`@pytest.mark.swing`)

**What's Tested:**
- Swing formation between fractals
- Dominant swing identification logic
- Swing invalidation when price extends beyond
- Swing size filtering (minimum points)
- Lookback window limits

**Key Test Cases:**
```python
def test_swing_formation():
    # Tests basic swing creation from fractals
    
def test_dominant_swing_logic():
    # Tests Elliott Wave dominance rules
    
def test_swing_invalidation():
    # Tests swing invalidation scenarios
```

### 3. ABC Pattern Tests (`@pytest.mark.abc`)

**What's Tested:**
- ABC pattern validation rules
- Fibonacci confluence detection
- Wave relationship validation (A≠B≠C directions)
- Pattern completion detection
- Time-based pattern filtering

**Key Test Cases:**
```python
def test_abc_pattern_validation():
    # Tests ABC structure validation
    
def test_abc_fibonacci_confluence():
    # Tests Fibonacci level confluence
    
def test_future_pattern_filtering():
    # Tests prevention of future pattern display
```

### 4. Frontend Logic Tests (`@pytest.mark.frontend`)

**What's Tested:**
- Dominant swing assignment logic
- ABC pattern clearing on direction change
- UI update throttling
- Data validation before updates
- Market bias calculation

**Key Test Cases:**
```python
def test_dominant_swing_assignment():
    # Tests JavaScript-equivalent logic
    
def test_abc_clearing_logic():
    # Tests ABC clearing on swing direction change
    
def test_ui_throttling():
    # Tests UI update rate limiting
```

### 5. Fibonacci Calculation Tests (`@pytest.mark.fibonacci`)

**What's Tested:**
- Retracement level calculations
- Extension level calculations
- Level ordering and validation
- Price-to-level mapping

### 6. Edge Case Tests (`@pytest.mark.edge_case`)

**What's Tested:**
- Empty/minimal data handling
- Invalid data handling (NaN, Inf values)
- Extreme volatility scenarios
- Flat market conditions
- Memory/performance limits

## 🔧 Running Tests

### Basic Commands

```bash
# Run all tests with coverage
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run tests in parallel (faster)
python run_tests.py --parallel

# Generate comprehensive report
python run_tests.py --report
```

### Advanced Options

```bash
# Run specific test file
pytest tests/unit/test_comprehensive_trading_logic.py -v

# Run tests matching pattern
pytest -k "fractal" -v

# Run tests with specific marker
pytest -m "swing and not slow" -v

# Run with detailed output
pytest --tb=long --capture=no -v

# Run with coverage threshold
pytest --cov=src --cov-fail-under=90
```

## 📈 Coverage Requirements

| Component | Minimum Coverage | Target Coverage |
|-----------|------------------|-----------------|
| Core Trading Logic | 95% | 98% |
| Fractal Detection | 90% | 95% |
| Swing Detection | 90% | 95% |
| ABC Patterns | 85% | 90% |
| Frontend Logic | 80% | 85% |
| Utilities | 70% | 80% |

## 🎯 Test Data Fixtures

### Available Fixtures (from `conftest.py`)

```python
@pytest.fixture
def sample_ohlc_data():
    # Realistic OHLC data with 0.1% volatility

@pytest.fixture  
def trending_up_data():
    # Clear uptrending market data

@pytest.fixture
def trending_down_data():
    # Clear downtrending market data

@pytest.fixture
def sideways_data():
    # Ranging/sideways market data

@pytest.fixture
def abc_pattern_data():
    # Data with clear ABC correction pattern

@pytest.fixture
def fibonacci_strategy():
    # Pre-configured FibonacciStrategy instance
```

## 🔍 Custom Assertions

```python
def test_fractal_validation(trading_assertions):
    fractal = detect_fractal(data)
    trading_assertions.assert_valid_fractal(fractal)

def test_swing_validation(trading_assertions):
    swing = detect_swing(fractals)
    trading_assertions.assert_valid_swing(swing)

def test_abc_validation(trading_assertions):
    pattern = detect_abc_pattern(swings)
    trading_assertions.assert_valid_abc_pattern(pattern)
```

## 🚨 Regression Testing

### Recently Fixed Issues (Covered by Tests)

1. **Dominant Swing Detection Bug**
   - Test: `test_dominant_swing_assignment()`
   - Ensures `accumulatedDominantSwing` updates correctly

2. **ABC Pattern Direction Clearing**
   - Test: `test_abc_clearing_logic()`
   - Ensures ABC patterns clear on swing direction change

3. **Future ABC Pattern Display**
   - Test: `test_future_pattern_filtering()`
   - Prevents showing patterns before they start

4. **UI Flashing Issues**
   - Test: `test_ui_throttling()`
   - Ensures UI updates are throttled properly

## 📊 Performance Testing

```bash
# Run performance tests
python run_tests.py --performance

# Profile test execution
pytest --profile

# Memory usage testing
pytest --memray
```

## 🔧 Continuous Integration

### GitHub Actions Workflow

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: python run_tests.py --install-deps
      - name: Run tests
        run: python run_tests.py --parallel
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 🎯 Best Practices

### Writing New Tests

1. **Use descriptive test names**
   ```python
   def test_dominant_swing_updates_when_larger_swing_detected():
   ```

2. **Follow AAA pattern**
   ```python
   def test_example():
       # Arrange
       data = create_test_data()
       
       # Act
       result = process_data(data)
       
       # Assert
       assert result.is_valid()
   ```

3. **Use appropriate markers**
   ```python
   @pytest.mark.swing
   @pytest.mark.edge_case
   def test_swing_with_minimal_data():
   ```

4. **Test edge cases**
   - Empty data
   - Invalid data
   - Boundary conditions
   - Error scenarios

### Debugging Failed Tests

```bash
# Run with detailed output
pytest --tb=long --capture=no -v

# Run single test with debugging
pytest tests/unit/test_file.py::test_function -s -v

# Use pdb for interactive debugging
pytest --pdb tests/unit/test_file.py::test_function
```

## 📋 Test Checklist

Before deploying changes:

- [ ] All unit tests pass
- [ ] Integration tests pass  
- [ ] Coverage meets requirements
- [ ] No regression in existing functionality
- [ ] Edge cases are covered
- [ ] Performance tests pass (if applicable)
- [ ] Documentation is updated

## 🎯 Next Steps

1. **Run the test suite**: `python run_tests.py`
2. **Check coverage**: Open `htmlcov/index.html`
3. **Fix any failures**: Review test output and fix issues
4. **Add missing tests**: Identify untested code paths
5. **Optimize performance**: Profile slow tests and optimize

Your trading logic is now comprehensively tested! 🚀
