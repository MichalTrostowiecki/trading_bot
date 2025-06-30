# Fibonacci-Based AI Trading Bot - Enterprise Project Documentation

## Project Overview

**Project Name**: Fibonacci-Based AI Trading Bot
**Version**: 2.5.3 - PRODUCTION READY + VISUAL BACKTESTING COMPLETE
**Project Type**: Fully Functional Automated Trading System with Visual Backtesting
**Target Platform**: Python + MetaTrader 5 Integration + PostgreSQL
**Status**: ✅ OPERATIONAL - Live trading system with web dashboard | ✅ COMPLETE - Visual backtesting system

## 🚀 CURRENT SYSTEM STATUS (Updated: 2025-06-28)

### ✅ COMPLETED FEATURES
- **Live MT5 Integration**: Successfully connects to BlueberryMarkets demo account
- **Real Order Placement**: Placing actual trades with proper risk management
- **Web Dashboard**: Professional trading interface at http://localhost:8000
- **Enhanced Chart Visualization**: Fibonacci lines, fractal markers, swing analysis
- **Stable Dominant Swing Detection**: 10% threshold prevents unnecessary changes
- **Cross-Platform Support**: WSL demo mode, Windows full functionality
- **Real-Time Updates**: 2-second trading loop, 3-second chart refresh
- **Comprehensive Logging**: Detailed fractal and trade execution logs

### ✅ COMPLETED - VISUAL BACKTESTING SYSTEM (Phase 2.5)
- **TradingView-Style Charts**: Professional charting with Lightweight Charts library ✅
- **Progressive Backtesting**: Step-by-step bar replay with full control ✅
- **PostgreSQL Integration**: Complete data storage with TimescaleDB ✅
- **MT4 Data Import**: Successfully imported DJ30 and EURUSD data ✅
- **Interactive Controls**: Play/pause, speed control, next/prev navigation ✅
- **Research Dashboard**: Fully functional at http://localhost:9000 ✅
- **Smart Chart Positioning**: Preserves user panning during replay ✅
- **Welcome Screen**: Intuitive UI with clear instructions ✅

### 🎯 KEY ACHIEVEMENTS
- Fixed "Invalid price" MT5 order placement errors
- Implemented proper swing line logic (high↔low connections only)
- Enhanced fractal positioning above/below candles for precise price visibility
- Added limited-width Fibonacci lines with right margin space
- Increased chart height and improved visual hierarchy
- Made fractal detection more responsive (3 periods vs 5)

### 📊 DASHBOARD FEATURES
- Live EURUSD chart with 800px height
- Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- Multiple swing context (current, previous, older)
- Fractal markers positioned for maximum visibility
- Real-time position tracking and P&L monitoring
- Start/stop/pause trading controls
- Risk management settings

## Core Strategy Overview

### Fibonacci Retracement Continuation Strategy
The system identifies major market swings using fractal analysis and applies Fibonacci retracement levels to enter trades in the direction of the dominant swing for continuation moves.

**Core Logic**:
1. **Swing Identification**: Detect major swings within a configurable lookback period using fractal analysis
2. **Dominant Swing Selection**: Determine which swing is dominant based on magnitude, recency, and momentum
3. **Fibonacci Application**: Calculate retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%) from the dominant swing
4. **Entry Execution**: Enter trades at key retracement levels (typically 38.2%-61.8%) in the direction of the dominant swing
5. **Exit Strategy**: Target Fibonacci extension levels (100%, 127.2%, 161.8%) for profit-taking

## Table of Contents

1. [Project Structure](#project-structure)
2. [Phase Overview](#phase-overview)
3. [Dependencies & Requirements](#dependencies--requirements)
4. [Development Phases](#development-phases)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Plan](#deployment-plan)
7. [Quality Assurance](#quality-assurance)
8. [Risk Management](#risk-management)
9. [Documentation References](#documentation-references)

## Project Structure

```
trading-bot-ai/
├── docs/                          # Complete documentation suite
│   ├── API_SPECIFICATION.md      # REST API and WebSocket documentation
│   ├── CORE_STRATEGY_SPECIFICATION.md # Fibonacci strategy details
│   ├── DEPENDENCIES_MATRIX.md    # Dependency mapping and installation
│   ├── DEPLOYMENT_GUIDE.md       # Production deployment instructions
│   ├── GIT_COMMANDS_REFERENCE.md # Git commands quick reference
│   ├── GIT_WORKFLOW_GUIDE.md     # Git workflow and collaboration
│   ├── PHASE_1_DETAILED_SPECIFICATION.md # Phase 1 implementation
│   ├── PHASE_1_2_DATA_PIPELINE_SPECIFICATION.md # Data pipeline specs
│   ├── QUALITY_ASSURANCE.md      # QA framework and standards
│   └── TESTING_STRATEGY.md       # Comprehensive testing approach
├── src/                           # Source code
│   ├── core/                      # Core trading algorithms
│   ├── data/                      # Data management and MT5 interface
│   ├── ml/                        # Machine learning models
│   ├── research/                  # Research and analysis tools
│   ├── backtesting/              # Backtesting engine
│   ├── execution/                # Trade execution
│   ├── monitoring/               # System monitoring
│   └── utils/                    # Utility functions
├── tests/                         # Test suites
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── performance/              # Performance tests
├── config/                        # Configuration files
│   ├── development.yaml.template # Development config template
│   └── production.yaml.template  # Production config template
├── data/                          # Data storage
│   ├── historical/               # Historical market data
│   ├── live/                     # Live data cache
│   ├── models/                   # Trained ML models
│   └── logs/                     # System logs
├── notebooks/                     # Jupyter notebooks
│   └── research/                 # Research notebooks
├── scripts/                       # Utility scripts
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore patterns
├── LICENSE                       # Proprietary software license
├── CONTRIBUTING.md               # Contribution guidelines
├── CHANGELOG.md                  # Version history and roadmap
├── README.md                     # Project overview and quick start
└── PROJECT_DOCUMENTATION.md      # This file - complete project docs
```

## System Architecture

### Complete AI Trading Platform
Python-based automated trading system with:
- **Background Trading Engine** - Automated MT5 trade execution
- **Web Control Dashboard** - Remote management and monitoring
- **Database Integration** - Historical data and performance analytics
- **Machine Learning Pipeline** - AI-enhanced strategy optimization
- **VPS Deployment** - 24/7 automated operation

## Phase Overview

### Phase 1: Foundation & Research Infrastructure ✅ COMPLETED
- [x] Development environment setup
- [x] Data pipeline implementation
- [x] Research tools development
- [x] Basic MT5 integration

### Phase 2: Core Trading System & Dashboard ✅ COMPLETED
- [x] Automated trading engine with MT5 integration
- [x] Web control dashboard with trading controls
- [x] Database system for historical data and trade logging
- [x] Fibonacci strategy implementation with fractal detection
- [x] Risk management and position sizing

### Phase 2.5: Visual Backtesting & Research System ⚡ IN PROGRESS
- [ ] TradingView-style charting with replay functionality
- [ ] PostgreSQL integration for complete data storage
- [ ] MT4 data import (Nov 2024-present)
- [ ] Visual verification of fractals, swings, and signals
- [ ] VectorBT integration for fast backtesting
- [ ] Research dashboard at http://localhost:8001

### Phase 3: Machine Learning Integration
- [ ] AI-enhanced pattern recognition
- [ ] Dynamic parameter optimization
- [ ] Market regime detection
- [ ] Entry timing optimization
- [ ] Performance prediction models

### Phase 4: Advanced Strategy Development
- [ ] Multi-timeframe analysis
- [ ] Advanced confluence detection
- [ ] Portfolio optimization
- [ ] Multi-symbol trading
- [ ] Adaptive strategy parameters

### Phase 5: Risk Management & Portfolio Optimization
- [ ] Advanced risk management system
- [ ] Portfolio-level position sizing
- [ ] Correlation analysis
- [ ] Drawdown protection
- [ ] Emergency stop systems

### Phase 6: Multi-Broker Integration
- [ ] Additional broker APIs
- [ ] Cross-broker arbitrage
- [ ] Liquidity aggregation
- [ ] Execution optimization
- [ ] Broker failover systems

### Phase 7: Production Deployment & Scaling
- [ ] Production VPS deployment
- [ ] Monitoring and alerting
- [ ] Performance optimization
- [ ] Scaling infrastructure
- [ ] Enterprise features

## Dependencies & Requirements

### System Requirements
- **Operating System**: Windows 10/11 (for MT5 compatibility)
- **Python Version**: 3.9+
- **Memory**: Minimum 16GB RAM (32GB recommended)
- **Storage**: 500GB SSD (for historical data and models)
- **Network**: Stable internet connection (low latency preferred)

### Core Dependencies
```
# Core Python packages
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0
scikit-learn>=1.1.0
tensorflow>=2.10.0
torch>=1.12.0

# Trading & Financial
MetaTrader5>=5.0.37
vectorbt>=0.25.0
backtrader>=1.9.76
ta-lib>=0.4.25
yfinance>=0.1.87

# Data & Analysis
plotly>=5.11.0
matplotlib>=3.6.0
seaborn>=0.12.0
jupyter>=1.0.0
ipywidgets>=8.0.0

# Database & Storage
sqlalchemy>=1.4.0
redis>=4.3.0
pymongo>=4.3.0

# Web & API
fastapi>=0.85.0
uvicorn>=0.18.0
requests>=2.28.0
websockets>=10.4

# Utilities
python-dotenv>=0.21.0
pydantic>=1.10.0
click>=8.1.0
rich>=12.6.0
loguru>=0.6.0

# Testing
pytest>=7.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.20.0

# Development
black>=22.10.0
flake8>=5.0.0
mypy>=0.991
pre-commit>=2.20.0
```

### External Dependencies
- **MetaTrader 5 Terminal**: Latest version installed
- **MT5 Python Package**: Official MetaQuotes package
- **Database**: PostgreSQL 14+ or MongoDB 6+
- **Message Queue**: Redis 7+
- **Monitoring**: Prometheus + Grafana (optional)

## Development Phases

### Phase 1: Foundation & Research Infrastructure

#### Phase 1.1: Environment Setup
**Duration**: 2 days  
**Dependencies**: None  
**Deliverables**:
- [ ] Python virtual environment configured
- [ ] All dependencies installed and verified
- [ ] MT5 connection established
- [ ] Project structure created
- [ ] Git repository initialized
- [ ] CI/CD pipeline basic setup

**Acceptance Criteria**:
- [ ] All tests pass in clean environment
- [ ] MT5 connection successful
- [ ] Basic data retrieval working
- [ ] Logging system operational

#### Phase 1.2: Data Pipeline Implementation
**Duration**: 3 days  
**Dependencies**: Phase 1.1 complete  
**Deliverables**:
- [ ] MT5 data interface module
- [ ] Historical data collection system
- [ ] Real-time data streaming
- [ ] Data validation and cleaning
- [ ] Data storage system

**Acceptance Criteria**:
- [ ] Can retrieve 1+ years of historical data
- [ ] Real-time data streaming functional
- [ ] Data quality validation passes
- [ ] Storage system handles 10GB+ data

#### Phase 1.3: Research Tools Development
**Duration**: 3 days  
**Dependencies**: Phase 1.2 complete  
**Deliverables**:
- [ ] Interactive Jupyter notebooks
- [ ] Statistical analysis tools
- [ ] Hypothesis testing framework
- [ ] Visualization components
- [ ] Research documentation templates

**Acceptance Criteria**:
- [ ] Can perform statistical analysis on market data
- [ ] Visualization tools generate publication-quality charts
- [ ] Hypothesis testing framework validates sample strategies
- [ ] Research workflow documented

### Phase 2: Core Algorithm Development

#### Phase 2.1: Fractal Detection System
**Duration**: 2 days  
**Dependencies**: Phase 1 complete  
**Deliverables**:
- [ ] Fractal detection algorithm
- [ ] Configurable parameters system
- [ ] Performance optimization
- [ ] Unit tests
- [ ] Documentation

**Acceptance Criteria**:
- [ ] Accurately detects fractals on historical data
- [ ] Processes 1M+ candles in <10 seconds
- [ ] Configurable bars_range parameter
- [ ] 95%+ test coverage

#### Phase 2.2: Fibonacci Calculation Engine
**Duration**: 2 days  
**Dependencies**: Phase 2.1 complete  
**Deliverables**:
- [ ] Fibonacci retracement calculator
- [ ] Fibonacci extension calculator
- [ ] Dynamic level adjustment
- [ ] Swing analysis integration
- [ ] Performance metrics

**Acceptance Criteria**:
- [ ] Calculates all standard Fibonacci levels
- [ ] Integrates with fractal detection
- [ ] Handles edge cases gracefully
- [ ] Performance benchmarks met

#### Phase 2.3: Swing Analysis and Dominant Swing Detection
**Duration**: 3 days
**Dependencies**: Phase 2.2 complete
**Deliverables**:
- [ ] Swing identification algorithm
- [ ] Dominant swing selection logic
- [ ] Swing magnitude and momentum calculation
- [ ] Market bias determination system
- [ ] Swing validation and filtering

**Acceptance Criteria**:
- [ ] Accurately identifies major market swings
- [ ] Correctly determines dominant swing based on multiple factors
- [ ] Provides clear market bias (bullish/bearish) for trade direction
- [ ] Handles edge cases (sideways markets, equal swings)

### Phase 2.5: Visual Backtesting & Research System

#### Phase 2.5.1: Database Schema Extension
**Duration**: 2 days
**Dependencies**: Phase 2 complete
**Deliverables**:
- [ ] Extended PostgreSQL schema for backtesting data
- [ ] Tables for fractals, swings, signals, and market context
- [ ] Optimized indexes for time-series queries
- [ ] Data migration scripts

**Acceptance Criteria**:
- [ ] All trading events stored with full context
- [ ] Sub-second query performance on large datasets
- [ ] Complete audit trail for ML training

#### Phase 2.5.2: MT4 Data Import System
**Duration**: 3 days
**Dependencies**: Phase 2.5.1 complete
**Deliverables**:
- [ ] MT4 history file parser
- [ ] Data validation and cleaning
- [ ] Multi-timeframe support
- [ ] Progress tracking and error recovery

**Acceptance Criteria**:
- [ ] Import data from Nov 2024 to present
- [ ] Handle gaps and anomalies gracefully
- [ ] Support M1, M5, M15, H1, H4, D1 timeframes

#### Phase 2.5.3: TradingView-Style Research Dashboard
**Duration**: 5 days
**Dependencies**: Phase 2.5.2 complete
**Deliverables**:
- [ ] Professional charting with Lightweight Charts
- [ ] Replay controls (play/pause/step)
- [ ] Visual overlays for fractals, swings, Fibonacci
- [ ] Debug panel showing calculations
- [ ] Data inspector for any candle

**Acceptance Criteria**:
- [ ] Chart quality matches TradingView standards
- [ ] Smooth performance with large datasets
- [ ] All strategy elements visually verifiable
- [ ] Export capabilities for documentation

#### Phase 2.5.4: VectorBT Integration
**Duration**: 3 days
**Dependencies**: Phase 2.5.3 complete
**Deliverables**:
- [ ] VectorBT backtesting engine
- [ ] Strategy performance analytics
- [ ] Parameter optimization framework
- [ ] Walk-forward analysis

**Acceptance Criteria**:
- [ ] Sub-second backtests on years of data
- [ ] Accurate performance metrics
- [ ] Reproducible results
- [ ] Database integration for all results

#### Phase 2.5.5: Research Tools & ML Preparation
**Duration**: 3 days
**Dependencies**: Phase 2.5.4 complete
**Deliverables**:
- [ ] Pattern discovery tools
- [ ] Statistical analysis suite
- [ ] Feature engineering pipeline
- [ ] ML-ready data exports

**Acceptance Criteria**:
- [ ] Identify best/worst performing setups
- [ ] Generate comprehensive reports
- [ ] Export clean datasets for ML training
- [ ] Document all findings

### Phase 3: Machine Learning Integration

#### Phase 3.1: Feature Engineering Pipeline
**Duration**: 3 days  
**Dependencies**: Phase 2 complete  
**Deliverables**:
- [ ] Automated feature extraction
- [ ] Technical indicator calculation
- [ ] Market regime features
- [ ] Session-based features
- [ ] Feature selection algorithms

**Acceptance Criteria**:
- [ ] Generates 100+ relevant features
- [ ] Feature selection reduces dimensionality
- [ ] Pipeline handles real-time data
- [ ] Feature importance analysis available

#### Phase 3.2: ML Model Development
**Duration**: 4 days  
**Dependencies**: Phase 3.1 complete  
**Deliverables**:
- [ ] Entry quality prediction model
- [ ] Market regime classifier
- [ ] Parameter optimization model
- [ ] Risk assessment model
- [ ] Model evaluation framework

**Acceptance Criteria**:
- [ ] Models achieve >60% accuracy on validation data
- [ ] Cross-validation scores stable
- [ ] Models handle real-time inference
- [ ] Model interpretability tools available

### Phase 4: Strategy Assembly & Optimization

#### Phase 4.1: Strategy Composition Framework
**Duration**: 3 days  
**Dependencies**: Phase 3 complete  
**Deliverables**:
- [ ] Strategy component system
- [ ] Signal combination logic
- [ ] Confidence scoring system
- [ ] Strategy ensemble manager
- [ ] Performance tracking

**Acceptance Criteria**:
- [ ] Can combine multiple strategy components
- [ ] Confidence scores correlate with performance
- [ ] Ensemble outperforms individual components
- [ ] Real-time strategy switching functional

#### Phase 4.2: Backtesting System
**Duration**: 4 days  
**Dependencies**: Phase 4.1 complete  
**Deliverables**:
- [ ] Vectorized backtesting engine
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Performance metrics calculation
- [ ] Report generation system

**Acceptance Criteria**:
- [ ] Backtests 1+ years of data in <60 seconds
- [ ] Walk-forward analysis validates robustness
- [ ] Monte Carlo provides confidence intervals
- [ ] Reports match industry standards

### Phase 5: Risk Management & Execution

#### Phase 5.1: Risk Management System
**Duration**: 3 days  
**Dependencies**: Phase 4 complete  
**Deliverables**:
- [ ] Position sizing calculator
- [ ] Drawdown controller
- [ ] Correlation manager
- [ ] Risk limit enforcement
- [ ] Emergency stop system

**Acceptance Criteria**:
- [ ] Position sizing respects risk limits
- [ ] Drawdown limits enforced in real-time
- [ ] Correlation limits prevent overexposure
- [ ] Emergency stops activate correctly

#### Phase 5.2: Trade Execution Engine
**Duration**: 4 days  
**Dependencies**: Phase 5.1 complete  
**Deliverables**:
- [ ] MT5 order execution interface
- [ ] Order management system
- [ ] Slippage handling
- [ ] Partial fill management
- [ ] Execution analytics

**Acceptance Criteria**:
- [ ] Orders execute within latency requirements
- [ ] Handles all MT5 order types
- [ ] Slippage tracking and reporting
- [ ] Execution quality metrics available

### Phase 6: Testing & Validation

#### Phase 6.1: Comprehensive Testing Suite
**Duration**: 3 days  
**Dependencies**: Phase 5 complete  
**Deliverables**:
- [ ] Unit test coverage >90%
- [ ] Integration test suite
- [ ] Performance benchmarks
- [ ] Stress testing framework
- [ ] Automated test reporting

**Acceptance Criteria**:
- [ ] All tests pass consistently
- [ ] Performance benchmarks met
- [ ] Stress tests validate stability
- [ ] Test reports generated automatically

#### Phase 6.2: Paper Trading Implementation
**Duration**: 4 days  
**Dependencies**: Phase 6.1 complete  
**Deliverables**:
- [ ] Paper trading system
- [ ] Real-time performance monitoring
- [ ] Trade simulation accuracy
- [ ] Performance comparison tools
- [ ] Live data validation

**Acceptance Criteria**:
- [ ] Paper trading matches backtesting results
- [ ] Real-time monitoring functional
- [ ] Performance tracking accurate
- [ ] Ready for live trading transition

### Phase 7: Deployment & Production

#### Phase 7.1: Production Deployment
**Duration**: 3 days  
**Dependencies**: Phase 6 complete  
**Deliverables**:
- [ ] Production environment setup
- [ ] Deployment automation
- [ ] Configuration management
- [ ] Security implementation
- [ ] Backup systems

**Acceptance Criteria**:
- [ ] System deploys automatically
- [ ] Security measures implemented
- [ ] Backup and recovery tested
- [ ] Production monitoring active

#### Phase 7.2: Monitoring & Alerting
**Duration**: 4 days  
**Dependencies**: Phase 7.1 complete  
**Deliverables**:
- [ ] Real-time dashboard
- [ ] Alert system
- [ ] Performance reporting
- [ ] System health monitoring
- [ ] User documentation

**Acceptance Criteria**:
- [ ] Dashboard provides real-time insights
- [ ] Alerts trigger appropriately
- [ ] Reports generated automatically
- [ ] System health monitored continuously
- [ ] Documentation complete and accurate

## Success Metrics

### Technical Metrics
- [ ] System uptime >99.5%
- [ ] Order execution latency <100ms
- [ ] Data processing latency <1 second
- [ ] Memory usage <8GB under normal load
- [ ] Test coverage >90%

### Trading Performance Metrics
- [ ] Sharpe ratio >1.5 in backtesting
- [ ] Maximum drawdown <15%
- [ ] Win rate >55%
- [ ] Profit factor >1.3
- [ ] Risk-adjusted returns >20% annually

### Operational Metrics
- [ ] Zero critical bugs in production
- [ ] Mean time to recovery <5 minutes
- [ ] Documentation completeness >95%
- [ ] User satisfaction >4.5/5
- [ ] Deployment success rate >98%

## Documentation References

### Core Documentation Files
- **[Core Strategy Specification](docs/CORE_STRATEGY_SPECIFICATION.md)** - Detailed Fibonacci retracement continuation strategy
- **[Git Workflow Guide](docs/GIT_WORKFLOW_GUIDE.md)** - Comprehensive Git workflow and collaboration best practices
- **[Git Commands Reference](docs/GIT_COMMANDS_REFERENCE.md)** - Quick reference for all Git commands and workflows
- **[Phase 1 Detailed Specification](docs/PHASE_1_DETAILED_SPECIFICATION.md)** - Complete Phase 1 implementation guide
- **[Phase 1.2 Data Pipeline Specification](docs/PHASE_1_2_DATA_PIPELINE_SPECIFICATION.md)** - MT5 integration and data management
- **[Dependencies Matrix](docs/DEPENDENCIES_MATRIX.md)** - Complete dependency mapping and installation order
- **[Testing Strategy](docs/TESTING_STRATEGY.md)** - Comprehensive testing framework and quality assurance
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment procedures and best practices
- **[Backtesting System](docs/BACKTESTING_SYSTEM.md)** - Visual backtesting and research system implementation plan
- **[Visual Verification](docs/VISUAL_VERIFICATION.md)** - Guide for visually verifying strategy correctness
- **[ML Preparation](docs/ML_PREPARATION.md)** - Machine learning integration preparation and roadmap
- **[API Specification](docs/API_SPECIFICATION.md)** - Complete REST API and WebSocket documentation
- **[Quality Assurance Framework](docs/QUALITY_ASSURANCE.md)** - QA standards and continuous improvement

### Quick Navigation
- **Strategy Overview**: Start with [Core Strategy Specification](docs/CORE_STRATEGY_SPECIFICATION.md)
- **Git Workflow**: Essential [Git Workflow Guide](docs/GIT_WORKFLOW_GUIDE.md) for team collaboration
- **Getting Started**: Continue with [Phase 1 Detailed Specification](docs/PHASE_1_DETAILED_SPECIFICATION.md)
- **Dependencies**: Check [Dependencies Matrix](docs/DEPENDENCIES_MATRIX.md) before beginning
- **Testing**: Follow [Testing Strategy](docs/TESTING_STRATEGY.md) for quality assurance
- **Deployment**: Use [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for production setup
- **API Integration**: Reference [API Specification](docs/API_SPECIFICATION.md) for external integrations

### File Structure Reference
```
trading-bot-ai/
├── PROJECT_DOCUMENTATION.md           # This file - main project overview
├── README.md                          # Project introduction and quick start
├── LICENSE                            # Proprietary software license
├── CONTRIBUTING.md                    # Contribution guidelines
├── CHANGELOG.md                       # Version history and roadmap
├── .gitignore                         # Git ignore patterns
├── .env.example                       # Environment variables template
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Development dependencies
├── config/
│   ├── development.yaml.template      # Development configuration template
│   └── production.yaml.template       # Production configuration template
├── src/                               # Source code (empty, ready for development)
├── tests/                             # Test suites (empty, ready for development)
├── data/                              # Data storage (empty, ready for development)
├── notebooks/                         # Jupyter notebooks (empty, ready for development)
├── scripts/                           # Utility scripts (empty, ready for development)
└── docs/
    ├── CORE_STRATEGY_SPECIFICATION.md         # Core Fibonacci strategy details
    ├── GIT_WORKFLOW_GUIDE.md                  # Git workflow and best practices
    ├── GIT_COMMANDS_REFERENCE.md              # Git commands quick reference
    ├── PHASE_1_DETAILED_SPECIFICATION.md      # Phase 1 implementation guide
    ├── PHASE_1_2_DATA_PIPELINE_SPECIFICATION.md # Data pipeline details
    ├── DEPENDENCIES_MATRIX.md                  # Dependency management
    ├── TESTING_STRATEGY.md                     # Testing framework
    ├── DEPLOYMENT_GUIDE.md                     # Deployment procedures
    ├── API_SPECIFICATION.md                    # API documentation
    └── QUALITY_ASSURANCE.md                    # QA framework
```
