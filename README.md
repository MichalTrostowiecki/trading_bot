# Fibonacci Trading Bot with Elliott Wave Analysis

## 🚀 Project Overview

A sophisticated trading system implementing Elliott Wave theory with ABC correction patterns. The system features real-time fractal detection, dominant swing analysis, and comprehensive backtesting capabilities. Built with professional-grade testing coverage and modern software engineering practices.

## ✅ **CURRENT STATUS: FULLY OPERATIONAL**

**All core trading logic implemented and tested with 32 passing unit tests!**

## ✨ Implemented Features

### ✅ **Core Trading Engine**
- **Fractal Detection**: 5-bar fractal pattern detection with strength calculation
- **Swing Analysis**: Elliott Wave compliant swing detection with dominance rules
- **ABC Patterns**: Complete ABC correction pattern detection with Fibonacci confluence
- **Fibonacci Levels**: Retracement (23.6%, 38.2%, 50%, 61.8%, 78.6%) and Extension (61.8%, 100%, 127.2%)
- **Market Bias**: Real-time market direction analysis based on dominant swings

### ✅ **Data Pipeline**
- **MT5 Integration**: Real-time and historical data from MetaTrader 5
- **Database System**: SQLite with market data, fractals, swings, and patterns storage
- **Data Validation**: Comprehensive OHLCV data validation and cleaning

### ✅ **Research Dashboard**
- **Visual Backtesting**: Interactive chart with fractal, swing, and ABC pattern visualization
- **Enhanced Signal Generation**: Pattern confirmation at Fibonacci levels with quality scoring
- **Signal Performance Analytics**: Real-time tracking and ML-ready data export
- **Progressive Backtesting**: Step-through historical data analysis
- **Chart Tools**: Zoom, pan, time navigation, and pattern toggles

### ✅ **Testing Framework**
- **32 Unit Tests**: Comprehensive coverage of all trading logic (100% pass rate)
- **Edge Case Testing**: Empty data, invalid data, extreme conditions
- **Frontend Logic Tests**: UI throttling, pattern filtering, data validation
- **Integration Tests**: Complete workflow validation
- **Professional Test Runner**: Coverage reporting and parallel execution

### 🔧 **Recent Fixes**
- **Dominant Swing Detection**: Fixed swing assignment logic for proper dominance updates
- **ABC Pattern Clearing**: Enhanced clearing when swing direction changes (UP ↔ DOWN)
- **Future Pattern Prevention**: Time-based filtering to prevent showing future patterns
- **UI Stability**: Throttling mechanism to prevent flashing in dashboard panels

## 📋 Quick Start

### Prerequisites
- Windows 10/11 (for MetaTrader 5 compatibility)
- Python 3.9 or higher
- MetaTrader 5 terminal installed
- 16GB RAM minimum (32GB recommended for production)
- PostgreSQL (production) or SQLite (development) - automatic switching

### Installation

#### Quick Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/trading-bot-ai.git
cd trading-bot-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy configuration template
copy config\development.yaml.template config\development.yaml
# Edit config\development.yaml with your MT5 credentials

# Run setup script
python scripts/setup_development_environment.py
```

### Quick Demo
```bash
# Run backtesting demo
python scripts/demo_backtest.py

# Start paper trading
python scripts/start_paper_trading.py

# Start research dashboard
python -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001

# Access dashboard at http://localhost:8001
```

## 🧪 Testing

The project includes a comprehensive testing framework with 32 unit tests covering all trading logic:

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --category frontend    # UI logic tests
python run_tests.py --category fractal     # Fractal detection tests
python run_tests.py --category swing       # Swing detection tests
python run_tests.py --category abc         # ABC pattern tests

# Run with coverage reporting
python run_tests.py --unit --parallel

# Generate comprehensive test report
python run_tests.py --report
```

### Test Coverage
- **Fractal Detection**: Basic detection, strength calculation, edge cases
- **Swing Detection**: Formation, dominance rules, invalidation scenarios
- **ABC Patterns**: Validation rules, Fibonacci confluence, time filtering
- **Frontend Logic**: UI updates, throttling, data validation
- **Edge Cases**: Empty data, invalid data, extreme market conditions
- **Integration**: Complete workflow validation

**Current Status: 32/32 tests passing ✅**

## 🏗️ Project Structure

```
trading-bot-ai/
├── src/                    # Source code
│   ├── core/              # Core trading algorithms
│   ├── data/              # Data management and MT5 interface
│   ├── ml/                # Machine learning models
│   ├── research/          # Research and analysis tools
│   ├── backtesting/       # Backtesting engine
│   ├── execution/         # Trade execution
│   ├── monitoring/        # System monitoring
│   └── utils/             # Utility functions
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance tests
├── config/                 # Configuration files
├── data/                   # Data storage
│   ├── historical/        # Historical market data
│   ├── models/            # Trained ML models
│   └── logs/              # System logs
├── notebooks/              # Jupyter notebooks for research
├── scripts/                # Utility scripts
├── docs/                   # Documentation
└── requirements.txt        # Python dependencies
```

## 📊 Strategy Overview

### Fibonacci Retracement Continuation Strategy
The core strategy identifies major market swings and enters trades in the direction of the dominant swing using Fibonacci retracement levels:

1. **Fractal Detection**: Identifies swing highs and lows using configurable bars range
2. **Swing Analysis**: Analyzes all recent swings to determine the most dominant one
3. **Dominant Swing Selection**: Uses magnitude, recency, and momentum to select the primary swing
4. **Fibonacci Calculation**: Computes retracement (23.6%, 38.2%, 50%, 61.8%, 78.6%) and extension levels
5. **Continuation Entry**: Enters trades at key retracement levels in the direction of the dominant swing
6. **AI Enhancement**: Machine learning models score signal quality and optimize parameters

## 🔧 Configuration

Configuration files are located in the `config/` directory. Copy the template and modify for your environment:

```bash
copy config\development.yaml.template config\development.yaml
```

Key configuration options:
- Database settings (PostgreSQL/SQLite automatic switching)
- MT5 connection settings
- Trading parameters (risk, position sizing)
- Fibonacci levels
- ML model parameters
- Logging and monitoring settings

### Database Configuration
The system automatically switches between databases:
- **Desktop/Production**: PostgreSQL (configured in `config.yaml`)
- **Laptop/Development**: SQLite (automatic fallback when PostgreSQL unavailable)

See [Database Setup Guide](docs/development/DATABASE_SETUP.md) for detailed configuration.

## 📚 Documentation

### Complete Documentation Suite
- **[Project Documentation](PROJECT_DOCUMENTATION.md)**: Complete project overview
- **[Documentation Index](docs/README.md)**: Organized documentation directory
- **[Core Strategy Specification](docs/architecture/CORE_STRATEGY_SPECIFICATION.md)**: Detailed Fibonacci strategy
- **[Git Workflow Guide](docs/development/GIT_WORKFLOW_GUIDE.md)**: Git workflow and collaboration best practices
- **[Git Commands Reference](docs/development/GIT_COMMANDS_REFERENCE.md)**: Quick Git commands reference
- **[Dependencies Matrix](docs/api/DEPENDENCIES_MATRIX.md)**: Complete dependency mapping
- **[Testing Strategy](docs/development/TESTING_STRATEGY.md)**: Comprehensive testing approach
- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)**: Production deployment instructions
- **[API Specification](docs/api/API_SPECIFICATION.md)**: Complete API documentation
- **[Quality Assurance](docs/development/QUALITY_ASSURANCE.md)**: QA framework and standards
- **[Chart Tools Guide](docs/user-guide/CHART_TOOLS_GUIDE.md)**: TradingView-style chart tools and navigation

## 🧪 Testing

Run the test suite:
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

## 🚀 Deployment

See [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Start
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This is proprietary software. All rights reserved. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading financial instruments involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always conduct thorough testing and risk assessment before deploying any automated trading system with real money.

---

**Built with ❤️ by the Fibonacci Trading Bot Team**
