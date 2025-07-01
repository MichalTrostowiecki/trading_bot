# Dependencies Matrix - Fibonacci Trading Bot Project

## Overview
This document outlines all dependencies between project phases, tasks, and components to ensure proper sequencing and avoid blocking issues during development.

## Phase Dependencies

### Phase Dependency Chain
```
Phase 1: Foundation & Research Infrastructure
├── 1.1: Environment Setup (No dependencies)
├── 1.2: Data Pipeline Implementation (Depends on 1.1)
└── 1.3: Research Tools Development (Depends on 1.1, 1.2)

Phase 2: Core Algorithm Development
├── 2.1: Fractal Detection System (Depends on 1.2, 1.3)
├── 2.2: Fibonacci Calculation Engine (Depends on 2.1)
└── 2.3: Session Analysis Framework (Depends on 2.1, 2.2)

Phase 3: Machine Learning Integration
├── 3.1: Feature Engineering Pipeline (Depends on 2.1, 2.2, 2.3)
└── 3.2: ML Model Development (Depends on 3.1)

Phase 4: Strategy Assembly & Optimization
├── 4.1: Strategy Composition Framework (Depends on 3.2)
└── 4.2: Backtesting System (Depends on 4.1)

Phase 5: Risk Management & Execution
├── 5.1: Risk Management System (Depends on 4.2)
└── 5.2: Trade Execution Engine (Depends on 5.1)

Phase 6: Testing & Validation
├── 6.1: Comprehensive Testing Suite (Depends on 5.2)
└── 6.2: Paper Trading Implementation (Depends on 6.1)

Phase 7: Deployment & Production
├── 7.1: Production Deployment (Depends on 6.2)
└── 7.2: Monitoring & Alerting (Depends on 7.1)
```

## Task-Level Dependencies

### Phase 1 Task Dependencies

#### Phase 1.1: Environment Setup
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 1.1.1: Python Environment Setup | None | All subsequent tasks |
| 1.1.2: Project Structure Creation | 1.1.1 | All development tasks |
| 1.1.3: Configuration System | 1.1.1, 1.1.2 | All configuration-dependent tasks |
| 1.1.4: Logging System Setup | 1.1.3 | All tasks requiring logging |
| 1.1.5: Git Repository Setup | 1.1.2 | Version control for all tasks |

#### Phase 1.2: Data Pipeline Implementation
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 1.2.1: MT5 Interface Implementation | 1.1.3, 1.1.4 | All data-dependent tasks |
| 1.2.2: Historical Data Collection | 1.2.1 | Algorithm development, backtesting |
| 1.2.3: Real-time Data Streaming | 1.2.1 | Live trading, monitoring |
| 1.2.4: Data Validation System | 1.2.2, 1.2.3 | Quality assurance |
| 1.2.5: Data Storage Management | 1.2.2 | Data persistence |

#### Phase 1.3: Research Tools Development
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 1.3.1: Interactive Analysis Tools | 1.2.2 | Strategy research |
| 1.3.2: Statistical Framework | 1.2.2 | Hypothesis testing |
| 1.3.3: Visualization Components | 1.2.2 | Data analysis |
| 1.3.4: Hypothesis Testing Tools | 1.3.1, 1.3.2 | Strategy validation |

### Phase 2 Task Dependencies

#### Phase 2.1: Fractal Detection System
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 2.1.1: Core Fractal Algorithm | 1.2.2 | All fractal-dependent features |
| 2.1.2: Parameter Configuration | 2.1.1, 1.1.3 | Algorithm optimization |
| 2.1.3: Performance Optimization | 2.1.1 | Real-time processing |
| 2.1.4: Unit Testing | 2.1.1 | Quality assurance |

#### Phase 2.2: Fibonacci Calculation Engine
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 2.2.1: Retracement Calculator | 2.1.1 | Entry signal generation |
| 2.2.2: Extension Calculator | 2.1.1 | Exit signal generation |
| 2.2.3: Dynamic Level Adjustment | 2.2.1, 2.2.2 | Adaptive strategies |
| 2.2.4: Swing Integration | 2.1.1, 2.2.1 | Complete Fibonacci system |

#### Phase 2.3: Session Analysis Framework
| Task | Dependencies | Blocking For |
|------|-------------|--------------|
| 2.3.1: Session Detection | 1.2.2 | Time-based analysis |
| 2.3.2: NY Open Analysis | 2.3.1 | Session-specific strategies |
| 2.3.3: Price Level Confluence | 2.2.4, 2.3.1 | Enhanced signal quality |
| 2.3.4: Statistical Validation | 2.3.2, 1.3.2 | Strategy validation |

## Component Dependencies

### Core Components
```
MT5Interface
├── Requires: MetaTrader5 package, configuration system
├── Provides: Market data, connection management
└── Used by: All data-dependent components

DataCollector
├── Requires: MT5Interface, logging system
├── Provides: Historical data, caching
└── Used by: Research tools, backtesting, ML features

RealTimeStream
├── Requires: MT5Interface, event system
├── Provides: Live data, tick processing
└── Used by: Live trading, monitoring

FractalDetector
├── Requires: DataCollector, numpy/pandas
├── Provides: Fractal points, swing analysis
└── Used by: Fibonacci calculator, ML features

FibonacciCalculator
├── Requires: FractalDetector, mathematical libraries
├── Provides: Retracement/extension levels
└── Used by: Strategy signals, ML features

SessionAnalyzer
├── Requires: DataCollector, datetime utilities
├── Provides: Session information, timing analysis
└── Used by: Strategy filters, ML features
```

### Machine Learning Components
```
FeatureEngineer
├── Requires: All core components, scikit-learn
├── Provides: ML-ready features
└── Used by: Model training, inference

ModelTrainer
├── Requires: FeatureEngineer, ML frameworks
├── Provides: Trained models
└── Used by: Strategy optimization, live trading

ModelInference
├── Requires: ModelTrainer, real-time data
├── Provides: Predictions, confidence scores
└── Used by: Strategy decisions, risk management
```

### Trading Components
```
StrategyComposer
├── Requires: All core + ML components
├── Provides: Trading signals, strategy logic
└── Used by: Trade execution, backtesting

RiskManager
├── Requires: StrategyComposer, account information
├── Provides: Position sizing, risk controls
└── Used by: Trade execution

TradeExecutor
├── Requires: RiskManager, MT5Interface
├── Provides: Order execution, position management
└── Used by: Live trading system

BacktestEngine
├── Requires: StrategyComposer, historical data
├── Provides: Performance metrics, validation
└── Used by: Strategy optimization, validation
```

## External Dependencies

### System Requirements
| Component | Requirement | Version | Critical Path |
|-----------|------------|---------|---------------|
| Windows OS | Operating System | 10/11 | All MT5 operations |
| MetaTrader 5 | Trading Platform | Latest | All trading operations |
| Python | Runtime | 3.9+ | All development |
| Git | Version Control | 2.30+ | Development workflow |

### Python Package Dependencies
| Package | Version | Required By | Critical For |
|---------|---------|-------------|--------------|
| pandas | >=1.5.0 | Data processing | All data operations |
| numpy | >=1.21.0 | Numerical computing | All calculations |
| MetaTrader5 | >=5.0.37 | MT5 integration | All trading operations |
| scikit-learn | >=1.1.0 | Machine learning | ML components |
| tensorflow | >=2.10.0 | Deep learning | Advanced ML models |
| plotly | >=5.11.0 | Visualization | Research tools |
| fastapi | >=0.85.0 | Web API | Monitoring dashboard |
| pytest | >=7.2.0 | Testing | Quality assurance |

### Development Tool Dependencies
| Tool | Purpose | Required For | Alternative |
|------|---------|--------------|-------------|
| VS Code / PyCharm | IDE | Development | Any Python IDE |
| Black | Code formatting | Code quality | autopep8 |
| Flake8 | Linting | Code quality | pylint |
| MyPy | Type checking | Code quality | None |
| Jupyter | Research notebooks | Analysis | None |

## Dependency Installation Order

### Phase 1 Installation Sequence
1. **System Prerequisites**
   ```bash
   # Install Python 3.9+
   # Install Git
   # Install MetaTrader 5
   # Install VS Code/PyCharm
   ```

2. **Python Environment**
   ```bash
   python -m venv fibonacci-trading-bot
   cd fibonacci-trading-bot
   Scripts\activate
   ```

3. **Core Dependencies**
   ```bash
   pip install pandas numpy scipy
   pip install MetaTrader5
   pip install python-dotenv pydantic
   pip install loguru rich click
   ```

4. **Development Dependencies**
   ```bash
   pip install pytest pytest-cov pytest-mock
   pip install black flake8 mypy
   pip install jupyter ipywidgets
   ```

5. **Analysis Dependencies**
   ```bash
   pip install plotly matplotlib seaborn
   pip install scikit-learn
   pip install vectorbt backtrader
   ```

6. **Web/API Dependencies**
   ```bash
   pip install fastapi uvicorn
   pip install requests websockets
   ```

7. **Database Dependencies**
   ```bash
   pip install sqlalchemy
   pip install redis pymongo
   ```

8. **ML Dependencies (Phase 3)**
   ```bash
   pip install tensorflow torch
   pip install xgboost lightgbm
   pip install optuna hyperopt
   ```

## Risk Mitigation

### Dependency Conflicts
- **Issue**: Package version conflicts
- **Mitigation**: Use exact version pinning in requirements.txt
- **Fallback**: Create separate virtual environments for conflicting packages

### Missing Dependencies
- **Issue**: Required packages not installed
- **Mitigation**: Automated dependency checking in setup scripts
- **Fallback**: Detailed installation documentation with troubleshooting

### Version Incompatibilities
- **Issue**: Package versions incompatible with Python version
- **Mitigation**: Test all combinations in CI/CD pipeline
- **Fallback**: Maintain compatibility matrix

### External Service Dependencies
- **Issue**: MT5 terminal not available or configured
- **Mitigation**: Connection health monitoring and fallback data sources
- **Fallback**: Demo/simulation mode for development

## Dependency Validation

### Automated Checks
```python
# scripts/validate_dependencies.py
def validate_environment():
    """Validate all dependencies are properly installed."""
    
    # Check Python version
    assert sys.version_info >= (3, 9), "Python 3.9+ required"
    
    # Check critical packages
    critical_packages = [
        'pandas', 'numpy', 'MetaTrader5', 
        'scikit-learn', 'plotly', 'fastapi'
    ]
    
    for package in critical_packages:
        try:
            __import__(package)
        except ImportError:
            raise ImportError(f"Critical package {package} not installed")
    
    # Check MT5 connection
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise ConnectionError("MT5 terminal not available")
    
    print("✅ All dependencies validated successfully")
```

### Manual Verification Checklist
- [ ] Python 3.9+ installed and accessible
- [ ] Virtual environment created and activated
- [ ] All packages from requirements.txt installed
- [ ] MT5 terminal installed and configured
- [ ] Git repository initialized
- [ ] IDE configured with Python interpreter
- [ ] All import statements work without errors
- [ ] Basic MT5 connection test passes
- [ ] Configuration files load correctly
- [ ] Logging system writes to files

## Troubleshooting Guide

### Common Issues
1. **MT5 Package Installation Fails**
   - Ensure Windows OS (MT5 package is Windows-only)
   - Install Visual C++ Redistributable
   - Use pip install --upgrade MetaTrader5

2. **TA-Lib Installation Issues**
   - Download pre-compiled wheel from unofficial binaries
   - Install Visual Studio Build Tools
   - Use conda install ta-lib as alternative

3. **TensorFlow GPU Issues**
   - Install CUDA toolkit and cuDNN
   - Verify GPU compatibility
   - Use CPU version for development

4. **Import Path Issues**
   - Add project root to PYTHONPATH
   - Use relative imports correctly
   - Verify __init__.py files exist

### Support Resources
- **Documentation**: docs/ directory
- **Issue Tracking**: GitHub issues
- **Community**: Trading development forums
- **Vendor Support**: MetaQuotes for MT5 issues
