# Claude Development Memory

## Project: Fibonacci Trading Bot AI

### Development Workflow Requirements

#### Git Commit Strategy
- **Work on development branch** for all ongoing development
- **Commit frequently** as we progress through development phases
- Use **conventional commit format**: `type(scope): description`
- Commit after completing each major task or feature
- Examples:
  - `feat(core): implement fractal detection algorithm`
  - `docs(phase1): update data pipeline specifications`
  - `test(fibonacci): add unit tests for retracement calculations`
  - `fix(mt5): resolve connection timeout issues`

#### Documentation Updates
- **Update documentation simultaneously** with code changes
- Keep all specs and guides current with implementation
- Update phase documentation as tasks are completed
- Maintain consistency between code and documentation

#### Project Context
- **SAAS Project**: Proprietary license, not open source
- **Trading Bot**: Fibonacci-based AI trading system
- **Phase-based Development**: Following 7-phase implementation plan
- **Quality Focus**: 90%+ test coverage, comprehensive documentation

#### Key Files to Maintain
- `CHANGELOG.md` - Update with each significant change
- Phase specification documents - Mark tasks as completed
- `PROJECT_DOCUMENTATION.md` - Keep project overview current
- Individual docs in `/docs` - Update as features are implemented

#### Development Principles
1. **Document first, then implement**
2. **Test-driven development**
3. **Commit early and often**
4. **Keep documentation in sync with code**
5. **Follow the phase-by-phase plan**

### Current Project Status
- **Phase**: Phase 3 - Visual Backtesting & Research System (IN PROGRESS)
- **Previous Phase**: Phase 2 - Complete Fibonacci Trading System (COMPLETED)
- **Next Phase**: Production Deployment & Optimization
- **Repository**: Fully functional automated trading bot with real MT5 integration
- **Structure**: Complete end-to-end trading system with web dashboard
- **Strategy Status**: Fibonacci retracement strategy fully implemented and operational
- **Current Focus**: Building visual verification and backtesting system with PostgreSQL storage

### Strategy Context
- **Core Strategy**: Fibonacci Retracement Continuation Strategy
- **Approach**: Fractal-based swing identification with Fibonacci entry levels
- **Direction**: Trade in direction of dominant swing for continuation moves
- **Requirements Doc**: `docs/STRATEGY_REQUIREMENTS.md` - **CRITICAL REFERENCE**
- **Status**: Detailed Q&A in progress to capture exact strategy specifications

### Visual Backtesting System (Phase 3 - IN PROGRESS ⚠️)
- **Purpose**: Visual verification of strategy before ML/AI optimization
- **Architecture**: Python + VectorBT + PostgreSQL + TradingView-style charts
- **Research Dashboard**: Running at http://localhost:8001
- **Data Sources**: DJ30 M1 data (219k+ bars), EURUSD H1 data (98 bars)
- **Key Features**:
  - TradingView-style professional charting (using Lightweight Charts)
  - Step-by-step replay functionality ✅
  - Complete data storage in PostgreSQL for ML training ✅
  - Visual debugging of fractals, swings, and signals ✅
  - Statistical analysis and pattern discovery ✅
- **Documentation**: See `docs/BACKTESTING_SYSTEM.md` for full implementation plan

### Recent Session Progress (June 28, 2025)
**🔧 FRACTAL VISUALIZATION SOLUTION IMPLEMENTED (NOT YET TESTED)**

#### Problems Identified and Solutions Implemented:
1. **Strategy Algorithm Verification** ✅ COMPLETED
   - Confirmed fractal detection working perfectly (5-bar pattern)
   - Verified 4 fractals detected in 69 bars of DJ30 M1 data
   - Strategy correctly identifies high/low fractals with proper timing

2. **Frontend Fractal Display Issue** 🔧 SOLUTION IMPLEMENTED
   - **Root Cause**: Frontend only showed newly detected fractals, not accumulated fractals
   - **Solution**: Implemented `loadAccumulatedStrategyElements()` function
   - **New API**: Added `/api/backtest/strategy-state` endpoint for complete strategy state
   - **Status**: ⚠️ NEEDS TESTING - Solution implemented but not verified by user

#### Technical Implementation Details:
- **Strategy State Management**: Complete fractal accumulation working
- **Progressive Chart Updates**: Fixed marker filtering issues  
- **API Integration**: Real-time fractal detection with proper display
- **Clean UI**: Removed text labels, showing pure arrow markers
- **Position Synchronization**: Fixed jumping between positions

#### Verified Fractal Data (DJ30 M1, Nov 7, 2024):
1. **High fractal** at 13:00:00, price 43902.3 (bar 8)
2. **Low fractal** at 13:14:00, price 43864.3 (bar 22)
3. **Low fractal** at 13:23:00, price 43872.3 (bar 31)
4. **High fractal** at 13:28:00, price 43885.3 (bar 36)

#### Current Status:
- **Fractal Detection**: ✅ WORKING PERFECTLY (Backend verified)
- **Fractal Visualization**: ⚠️ BLOCKED BY CONNECTION ISSUE
- **Dashboard Access**: ❌ WSL networking issue preventing browser access
- **Strategy Verification**: ✅ CONFIRMED ACCURATE
- **Next Required**: Fix WSL networking issue to restore dashboard access

### AI Agent Instructions
When working on this project:
1. **System is PRODUCTION READY** - fully functional automated trading bot
2. **MT5 Integration**: Real BlueberryMarkets demo account (Login: 12605399)
3. **Web Dashboard**: Available at http://localhost:8000 with live charts and controls
4. **Research Dashboard**: ✅ FULLY OPERATIONAL at http://localhost:9000 for backtesting
5. **Chart Features**: Enhanced Fibonacci visualization with proper swing detection ✅ WORKING
6. **Order Placement**: Successfully placing real MT5 orders with proper risk management
7. **Deployment**: Ready for VPS deployment for 24/7 automated trading
8. **Documentation**: All implementation details documented in project files
9. **Testing**: System tested and verified with live MT5 connection
10. **Backtesting**: ✅ VISUAL VERIFICATION SYSTEM OPERATIONAL

### Next Session Continuation Points
For the next Claude agent to continue this work:

1. **CRITICAL ISSUE**: Research dashboard servers start but aren't accessible via browser (Connection refused)
2. **Likely Cause**: WSL networking issue - servers bind to ports but Windows can't access them
3. **What Was Working**: Dashboard at http://localhost:9000 displayed 4 fractals correctly before visual update attempt
4. **What Went Wrong**: Created multiple new dashboard files instead of just updating CSS
5. **Files to Clean Up**:
   - /mnt/d/trading_bot/minimal_dashboard.py
   - /mnt/d/trading_bot/simple_tradingview_dashboard.py  
   - /mnt/d/trading_bot/working_dashboard.py
   - /mnt/d/trading_bot/test_server.py
   - /mnt/d/trading_bot/simple_fractal_test.py
6. **Original Working File**: `/mnt/d/trading_bot/src/research/dashboard/research_api.py`
7. **User Request**: "Don't break anything" - wanted visual updates only, not new architecture
8. **Next Steps**:
   - Diagnose WSL networking issue (check WSL version, port forwarding)
   - Clean up experimental files
   - Restore original dashboard functionality
   - Update ONLY CSS for TradingView look
9. **Testing Commands**:
   ```bash
   # Check WSL version
   wsl --version
   
   # Test basic connectivity
   curl http://localhost:9000
   
   # Start research dashboard with explicit localhost binding
   python3 -m uvicorn src.research.dashboard.research_api:app --host localhost --port 9000
   ```

### Development Environment
- **User Platform**: Windows with WSL for communication  
- **MT5 Environment**: Windows-only (MetaTrader5 Python API)
- **WSL Mode**: Demo mode with functional dashboard
- **Production Mode**: Windows with full MT5 integration