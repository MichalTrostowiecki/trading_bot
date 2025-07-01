# Test Suite

This directory contains all tests for the Fibonacci Trading Bot.

## Test Structure

### 🔬 Unit Tests (`unit/`)
Tests for individual components and functions:
- `test_fractal_detection.py` - Fractal detection algorithm tests
- `test_fractal_console.py` - Console output tests  
- `dashboard_test_fix.py` - Dashboard component tests

### 🔗 Integration Tests (`integration/`)
Tests for component interactions and system integration:
- `test_backtesting_db.py` - Database integration tests
- `test_research_dashboard.py` - Dashboard integration tests
- `test_windows_mt5.py` - MT5 integration tests
- `verify_fractal_system.py` - System verification tests

### 🎭 End-to-End Tests (`e2e/`)
Full system tests (to be implemented):
- Complete trading workflow tests
- Dashboard user journey tests

### 📋 Fixtures (`fixtures/`)
Test data and HTML fixtures:
- `test_marker_fix.html` - Chart marker test fixtures
- `test_markers.html` - Additional marker test data

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run integration tests only  
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/unit/test_fractal_detection.py

# Run with coverage
python -m pytest tests/ --cov=src/
```

## Test Guidelines

1. **Unit tests** should be fast and test single functions
2. **Integration tests** can use databases and external services
3. **All tests** should be deterministic and independent
4. **Use fixtures** for test data to avoid duplication
5. **Mock external services** in unit tests

For detailed testing guidelines, see [development/TESTING_STRATEGY.md](../docs/development/TESTING_STRATEGY.md).