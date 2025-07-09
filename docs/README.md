# Fibonacci Trading Bot Documentation

## Documentation Structure

This documentation is organized into the following categories:

### 📐 Architecture
- **[Core Strategy Specification](architecture/CORE_STRATEGY_SPECIFICATION.md)** - Complete strategy requirements and logic
- **[Strategy Requirements](architecture/STRATEGY_REQUIREMENTS.md)** - Detailed strategy specifications
- **[Backtesting System](architecture/BACKTESTING_SYSTEM.md)** - Visual backtesting architecture
- **[ML Preparation](architecture/ML_PREPARATION.md)** - Machine learning integration plans
- **Phase Documents** - Development phase specifications

### 🔌 API
- **[API Specification](api/API_SPECIFICATION.md)** - Complete API documentation
- **[Dependencies Matrix](api/DEPENDENCIES_MATRIX.md)** - System dependencies and versions

### 👥 User Guide
- **[Research Dashboard Guide](user-guide/RESEARCH_DASHBOARD_GUIDE.md)** - How to use the dashboard
- **[Chart Tools Guide](user-guide/CHART_TOOLS_GUIDE.md)** - TradingView-style chart tools and navigation
- **[Visual Verification](user-guide/VISUAL_VERIFICATION.md)** - Strategy verification guide

### 🛠️ Development
- **[Git Workflow Guide](development/GIT_WORKFLOW_GUIDE.md)** - Development workflow
- **[Git Commands Reference](development/GIT_COMMANDS_REFERENCE.md)** - Git command reference
- **[Database Setup](development/DATABASE_SETUP.md)** - Dual database configuration (PostgreSQL/SQLite)
- **[Testing Strategy](development/TESTING_STRATEGY.md)** - Testing guidelines
- **[Quality Assurance](development/QUALITY_ASSURANCE.md)** - QA standards

### 🧪 Testing
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive unit testing framework
- **[Test Runner](../run_tests.py)** - Professional test execution with coverage reporting

### 🚀 Deployment
- **[Deployment Guide](deployment/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Quick Deployment](deployment/DEPLOYMENT_GUIDE_QUICK.md)** - Quick start deployment

## Project Overview

This is a sophisticated Fibonacci-based trading system implementing Elliott Wave theory with ABC correction patterns. The system features:

### ✅ **COMPLETED FEATURES**
- **Fractal Detection**: 5-bar fractal pattern detection with strength calculation
- **Swing Analysis**: Elliott Wave compliant swing detection with dominance rules
- **ABC Patterns**: Complete ABC correction pattern detection with Fibonacci confluence
- **Visual Backtesting**: Interactive research dashboard with real-time pattern visualization
- **Comprehensive Testing**: 32 unit tests covering all trading logic with 100% pass rate
- **MT5 Integration**: Real-time and historical data from MetaTrader 5
- **Database System**: SQLite with market data, fractals, swings, and patterns storage

### 🔧 **RECENT FIXES**
- **Dominant Swing Detection**: Fixed swing assignment logic for proper dominance updates
- **ABC Pattern Clearing**: Enhanced clearing when swing direction changes (UP ↔ DOWN)
- **Future Pattern Prevention**: Time-based filtering to prevent showing future patterns
- **UI Stability**: Throttling mechanism to prevent flashing in dashboard panels

### 🎯 **CURRENT STATUS**
The trading bot is fully operational with professional-grade testing coverage. All core Elliott Wave and ABC pattern logic is implemented and validated. The system is ready for signal generation and trading automation development.

For detailed technical information, see the [main README](../README.md) and [.claude.md](../.claude.md) context file.