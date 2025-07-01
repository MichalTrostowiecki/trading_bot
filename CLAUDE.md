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

#### Documentation Updates - CRITICAL REQUIREMENT ⚠️
- **MANDATORY**: Update documentation simultaneously with ALL code changes
- **NEVER** complete a task without updating relevant documentation
- **ALWAYS** update the following when making changes:
  - Architecture docs when changing system design
  - API docs when modifying endpoints or data structures
  - User guides when changing UI or functionality
  - Development docs when changing workflows or setup
  - README files when adding new features or tools
- **Keep all specs and guides current** with implementation
- **Update phase documentation** as tasks are completed
- **Maintain consistency** between code and documentation
- **Documentation debt is technical debt** - treat it as such

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
4. **CRITICAL: Keep documentation in sync with code - NO EXCEPTIONS**
5. **Follow the phase-by-phase plan**
6. **Documentation completeness is part of task completion**

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
4. **Research Dashboard**: ✅ FULLY OPERATIONAL at http://localhost:8001 for backtesting
5. **Chart Features**: Enhanced Fibonacci visualization with proper swing detection ✅ WORKING
6. **Order Placement**: Successfully placing real MT5 orders with proper risk management
7. **Deployment**: Ready for VPS deployment for 24/7 automated trading
8. **Documentation**: All implementation details documented in project files
9. **Testing**: System tested and verified with live MT5 connection
10. **Backtesting**: ✅ VISUAL VERIFICATION SYSTEM OPERATIONAL

### 📚 DOCUMENTATION REQUIREMENTS - MANDATORY FOR ALL AGENTS

**🚨 CRITICAL: Documentation is NOT optional - it is REQUIRED for task completion**

#### Before Starting Any Task:
1. **Read relevant docs** to understand current state
2. **Identify which docs** will need updates based on your changes
3. **Plan documentation updates** as part of your task

#### During Implementation:
1. **Update docs in real-time** as you make changes
2. **Document new features, endpoints, or configuration changes**
3. **Update existing docs** if your changes affect them

#### Before Completing Any Task:
1. **VERIFY all relevant documentation is updated**
2. **Check that examples and code snippets still work**
3. **Update README files if you add new tools or features**
4. **Do NOT mark task as complete** until docs are updated

#### Documentation Categories to Update:
- **Architecture docs** (`docs/architecture/`) - For system design changes
- **API docs** (`docs/api/`) - For endpoint or data structure changes  
- **User guides** (`docs/user-guide/`) - For UI or functionality changes
- **Development docs** (`docs/development/`) - For workflow or setup changes
- **Main README** - For new features, tools, or major changes
- **Tool READMEs** (`tools/README.md`, `tests/README.md`) - For new utilities

#### Quality Standards:
- **Examples must work** - test all code examples in docs
- **Links must be valid** - verify all internal documentation links
- **Consistent formatting** - follow existing documentation style
- **Clear explanations** - write for both beginners and experts

**Remember: Undocumented features are broken features. Documentation debt is technical debt.**

### Next Session Continuation Points
For the next Claude agent to continue this work:

## **CURRENT DASHBOARD STATUS (July 1, 2025)**
- **Research Dashboard**: Running at http://localhost:8001 (port changed from 9000)
- **Server Command**: `python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001`
- **Performance**: TradingView-style optimizations implemented but issues remain

## **CRITICAL ISSUES TO FIX**

### 1. **Browser Refresh Problem** 🔴 HIGH PRIORITY
- **Issue**: Browser refresh is extremely slow/hangs (still not resolved)
- **Cause**: Unknown - server responds fast (0.004s) but browser refresh fails
- **Status**: Multiple attempts made, still problematic
- **Next Steps**: 
  - Investigate browser caching issues
  - Check for JavaScript memory leaks
  - Consider progressive data loading approach
  - Test with smaller data samples

### 2. **Chart Data Loading Logic** 🔴 HIGH PRIORITY  
- **Issue**: Chart loads ALL data instead of progressive loading up to user's start date
- **Current**: `candlestickSeries.setData(window.fullChartData)` loads everything
- **Required**: Progressive loading - show only data up to current backtesting position
- **Location**: `src/research/dashboard/research_api.py` lines 1083-1087
- **Fix Needed**: Revert to progressive data loading for backtesting experience

### 3. **Performance Optimization Needed**
- **Data Size**: 50k+ bars causing browser stress
- **Current Approach**: TradingView-style (loads all data)
- **Better Approach**: Hybrid - progressive for backtesting, full for analysis

## **RECENT CHANGES MADE**
1. ✅ Implemented TradingView-style data handling
2. ✅ Fixed chart zoom logic using `setVisibleRange()`
3. ✅ Added proper TradingView chart performance settings
4. ✅ Simplified data size warnings
5. ✅ Enhanced trend line drawing functionality
6. ❌ Browser refresh still problematic
7. ❌ Chart data loading not progressive

## **QUICK START COMMANDS**
```bash
# Start dashboard server
cd /mnt/c/Users/trost/OneDrive/Desktop/trading-bot/trading_bot
python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001

# Test server response
curl -s -o /dev/null -w "%{time_total} seconds - HTTP %{http_code}" http://localhost:8001/

# Check if server is running
ps aux | grep "uvicorn.*8001" | grep -v grep
```

## **PRIORITY FIXES FOR NEXT SESSION**
1. **Fix browser refresh performance** (investigate caching, memory leaks)
2. **Implement progressive chart data loading** (backtesting mode)
3. **Add data pagination/chunking** for large datasets
4. **Test with smaller data samples** to isolate performance issues

## **FILES TO FOCUS ON**
- `src/research/dashboard/research_api.py` (lines 1083-1087: chart data loading)
- Browser developer tools (check for memory leaks, network issues)
- Consider implementing data virtualization or lazy loading

### Development Environment
- **User Platform**: Windows with WSL for communication  
- **MT5 Environment**: Windows-only (MetaTrader5 Python API)
- **WSL Mode**: Demo mode with functional dashboard
- **Production Mode**: Windows with full MT5 integration