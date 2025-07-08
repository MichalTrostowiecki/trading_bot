# Claude Development Memory

## Project: Fibonacci Trading Bot AI

### 📋 Quick Navigation
- [Current Status](#current-project-status) | [Strategy Context](#strategy-context) | [Documentation](#documentation-tracker)
- [Phase 3 Progress](#visual-backtesting-system-phase-3---in-progress-⚠️) | [Next Steps](#next-development-phase-🎯)
- [Server Commands](#research-dashboard-server-startup---reliable-instructions) | [Key Files](#key-files-for-next-phase)

### 📚 Documentation Tracker
**🚨 ALWAYS UPDATE DOCS WHEN MAKING CHANGES - Documentation completeness is REQUIRED for task completion**

#### Core Documentation Files:
- **Architecture**: [`docs/architecture/`](docs/architecture/) - System design, strategy specs, phase plans
  - 🔗 [STRATEGY_REQUIREMENTS.md](docs/architecture/STRATEGY_REQUIREMENTS.md) - **CRITICAL REFERENCE**
  - 🔗 [BACKTESTING_SYSTEM.md](docs/architecture/BACKTESTING_SYSTEM.md) - Phase 3 implementation roadmap
  - 🔗 [ABC_CORRECTION_PATTERNS.md](docs/architecture/ABC_CORRECTION_PATTERNS.md) - **ABC Pattern Implementation**
  - 🔗 [CORE_STRATEGY_SPECIFICATION.md](docs/architecture/CORE_STRATEGY_SPECIFICATION.md)
- **API**: [`docs/api/`](docs/api/) - Endpoint specifications, dependencies
  - 🔗 [API_SPECIFICATION.md](docs/api/API_SPECIFICATION.md)
  - 🔗 [DEPENDENCIES_MATRIX.md](docs/api/DEPENDENCIES_MATRIX.md)
- **User Guides**: [`docs/user-guide/`](docs/user-guide/) - Dashboard usage, chart tools
  - 🔗 [RESEARCH_DASHBOARD_GUIDE.md](docs/user-guide/RESEARCH_DASHBOARD_GUIDE.md)
  - 🔗 [CHART_TOOLS_GUIDE.md](docs/user-guide/CHART_TOOLS_GUIDE.md)
- **Development**: [`docs/development/`](docs/development/) - Setup, testing, workflows
  - 🔗 [DATABASE_SETUP.md](docs/development/DATABASE_SETUP.md)
  - 🔗 [GIT_WORKFLOW_GUIDE.md](docs/development/GIT_WORKFLOW_GUIDE.md)
  - 🔗 [ABC_REIMPLEMENTATION_GUIDE.md](docs/development/ABC_REIMPLEMENTATION_GUIDE.md) - **ABC Re-implementation**
  - 🔗 [TESTING_STRATEGY.md](docs/development/TESTING_STRATEGY.md)
- **Deployment**: [`docs/deployment/`](docs/deployment/) - Production deployment guides
  - 🔗 [DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md)

#### Documentation Update Checklist:
- [ ] Update relevant architecture docs when changing system design
- [ ] Update API docs when modifying endpoints or data structures
- [ ] Update user guides when changing UI or functionality
- [ ] Update development docs when changing workflows or setup
- [ ] Update README files when adding new features or tools
- [ ] Update [CHANGELOG.md](CHANGELOG.md) with significant changes
- [ ] Update [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) project overview

### 🎯 Current Task Management
**Active Phase**: Phase 3 - Visual Backtesting & Research System - **CRITICAL MARKER ISSUE INVESTIGATION**
**Status**: Chart Marker Disappearing Issue - IN PROGRESS ⚠️
**Priority Tasks**: [Jump to Marker Testing Protocol](#marker-persistence-testing-protocol-🔍)

### Development Workflow Requirements

#### 🚨 MANDATORY CODE QUALITY STANDARDS - ENTERPRISE LEVEL REQUIRED 🚨

**🔒 ZERO TOLERANCE POLICY:**
- **NO duplicate functions, methods, or classes** - Each function defined ONCE only
- **NO unused/dead code** - Remove immediately upon detection
- **NO incomplete implementations** - Complete every function before committing
- **NO duplicate imports** - Organize imports at file top, deduplicate rigorously
- **NO copy-paste programming** - Reuse existing functions, don't duplicate
- **NO debug code in production** - Remove console.log, print statements before commit

**✅ PRE-COMMIT CHECKLIST - MANDATORY:**
1. **Scan entire file for duplicate function names** - Use search tools
2. **Check for unused variables/functions** - Remove immediately  
3. **Validate all imports** - No duplicates, proper organization
4. **Test all modified functions** - Ensure they work before commit
5. **Remove debug statements** - Clean professional code only
6. **Verify syntax** - No compilation errors allowed

**🛠️ CODE REVIEW REQUIREMENTS:**
- **Every change** must be reviewed for duplicates before implementation
- **Every function** must have single purpose and clear implementation
- **Every import** must be necessary and properly organized
- **Every line** of code must serve a purpose

**❌ IMMEDIATE REJECTION CRITERIA:**
- Duplicate function definitions in same file
- Unused imports or dead code
- Incomplete or broken function implementations  
- Debug code left in production files
- Copy-paste code without proper refactoring

#### Git Commit Strategy
- **Work on development branch** for all ongoing development
- **Commit frequently** as we progress through development phases
- Use **conventional commit format**: `type(scope): description`
- **MANDATORY**: Include "code quality verified" in commit messages
- Commit after completing each major task or feature
- Examples:
  - `feat(core): implement fractal detection algorithm - code quality verified`
  - `docs(phase1): update data pipeline specifications - no duplicates`
  - `test(fibonacci): add unit tests for retracement calculations - clean code`
  - `fix(mt5): resolve connection timeout issues - duplicates removed`

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
1. **🔒 ENTERPRISE CODE QUALITY FIRST** - Zero tolerance for duplicates or dead code
2. **Document first, then implement** - Plan before coding
3. **Test-driven development** - Verify before committing
4. **Commit early and often** - Small, clean commits
5. **CRITICAL: Keep documentation in sync with code - NO EXCEPTIONS**
6. **Follow the phase-by-phase plan** - Systematic development
7. **Documentation completeness is part of task completion**
8. **🚨 MANDATORY: Code quality verification before any commit**

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

### Swing Detection - Purpose & End Goal 🎯

#### **FUNDAMENTAL PURPOSE**
The swing detection system is the **CORE FOUNDATION** of our Fibonacci strategy. It identifies market structure to:
1. **Determine Market Bias**: Bullish/Bearish direction for trade entries
2. **Find Fibonacci Zones**: Calculate retracement levels for precise entries
3. **Trade Continuation**: Enter trades in direction of dominant swing movement
4. **Risk Management**: Set stops at swing invalidation points

#### **ELLIOTT WAVE MARKET STRUCTURE RULES**
Based on professional Elliott Wave analysis:

**🔒 SWING PRESERVATION RULES:**
- **Dominant swings stay connected** to original fractals (preserve market structure)
- **Only invalidate when price breaks** start/end points of swing (Elliott Wave invalidation)
- **Maximum 2 swings displayed**: 1 dominant (thick line) + 1 non-dominant (dotted line)
- **140-candle lookback window**: Remove outdated swings outside this range

**⚡ INVALIDATION TRIGGERS:**
- **DOWN dominant swing**: Invalidated when price breaks ABOVE swing START price
- **UP dominant swing**: Invalidated when price breaks BELOW swing START price
- **Break of Structure**: Only recalculate dominance after invalidation occurs

**🎯 END GOAL - FIBONACCI TRADING SETUP:**
1. **Identify Dominant Swing** → Determines market bias (bullish/bearish)
2. **Wait for Retracement** → Price pulls back against dominant swing
3. **Enter at Fibonacci Levels** → 38.2%, 50%, 61.8% continuation zones
4. **Trade in Swing Direction** → Follow dominant trend for continuation
5. **Stop at Invalidation** → Exit if swing structure breaks

#### **WHY THIS MATTERS**
- **Clean Market Structure**: No noise, only significant swings
- **Professional Analysis**: Based on Elliott Wave institutional methods
- **High Probability Setups**: Trade with dominant market structure
- **Clear Risk Rules**: Know exactly when setup is invalidated

**🚨 CRITICAL REMINDER**: Every swing detection change must serve this end goal - creating clean, professional market structure analysis for high-probability Fibonacci continuation trades.

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

### 🚨 CRITICAL ISSUE: MARKER PERSISTENCE PROBLEM (July 7, 2025)

#### **PROBLEM STATEMENT**
**Symptoms Reported by User:**
- Fractal markers (arrows) appear briefly when pressing "Next Bar" navigation button
- Markers immediately disappear within ~1 second of appearing
- Markers only visible during navigation transition, not when idle
- User confirmed: "they show only between navigation and don't stay visible on chart"
- Issue persisted through multiple previous fix attempts over several sessions

**Visual Evidence:**
- User provided 4 screenshots showing empty charts with console logs
- Console shows: "Applied 1 total markers" followed by "No fractals to display"
- Suggests markers are applied but immediately cleared

#### **ROOT CAUSE ANALYSIS**

**🔍 PRIMARY CAUSE: TradingView Lightweight Charts API Behavior**
1. **`candlestickSeries.setData(progressiveData)` operation CLEARS ALL MARKERS**
   - This is normal TradingView behavior - setData() resets the entire series
   - Called in `updateChartProgressive()` during navigation (line ~2907)
   - Happens on every "Next Bar" press when chart data is updated

2. **`chart.timeScale().setVisibleRange()` operation ALSO CLEARS MARKERS**
   - Called during chart range adjustments (line ~2982)
   - Another TradingView operation that removes markers

3. **Failed Save/Restore Mechanism**
   - Previous attempts to save/restore markers were incomplete
   - Timing issues between multiple chart operations
   - Race conditions between different restoration attempts

**🔍 TECHNICAL FLOW ANALYSIS**
```
User clicks "Next Bar" 
    ↓
replayAction('next') called (line 5162)
    ↓
updateChartProgressive(position) called (line 5196)
    ↓
candlestickSeries.setData(progressiveData) called (line 2907)
    ↓
*** ALL MARKERS CLEARED BY TRADINGVIEW ***
    ↓
updateAllMarkers() called (line 3046)
    ↓
UnifiedMarkerManager.loadFractals() called (line 3131)
    ↓
UnifiedMarkerManager.performUpdate() called (line 1134)
    ↓
candlestickSeries.setMarkers(markersArray) called (line 1134)
    ↓
*** MARKERS SHOULD BE VISIBLE BUT DISAPPEAR ***
```

**🔍 SECONDARY ISSUES IDENTIFIED**
- Multiple timeout delays (100ms, 500ms) causing restoration conflicts
- Double function calls in navigation flow
- Inconsistent data sources (local vs global accumulated arrays)
- No emergency recovery if manager state becomes corrupted

#### **COMPREHENSIVE SOLUTION IMPLEMENTED**

**🛠️ ENHANCED MARKER PERSISTENCE (File: `/src/research/dashboard/research_api.py`)**

**1. updateChartProgressive() - Lines 2895-2941**
```javascript
// BEFORE setData() - Save all current markers
let markersToRestore = [];
if (unifiedMarkerManager && unifiedMarkerManager.getMarkerCount() > 0) {
    markersToRestore = Array.from(unifiedMarkerManager.markers.values());
    console.log(`🔍 SAVING ${markersToRestore.length} markers before setData operation`);
}

// Call setData which will clear all markers
candlestickSeries.setData(progressiveData);

// IMMEDIATELY restore markers via direct API call
if (markersToRestore.length > 0) {
    candlestickSeries.setMarkers(markersToRestore);
    console.log(`✅ Direct setMarkers successful`);
    
    // Backup restoration via unified manager
    setTimeout(() => {
        unifiedMarkerManager.forceUpdate();
    }, 10);
}
```

**2. setVisibleRange() Protection - Lines 2975-3002**
```javascript
// Save markers before range change
let rangeChangeMarkers = [];
if (unifiedMarkerManager && unifiedMarkerManager.getMarkerCount() > 0) {
    rangeChangeMarkers = Array.from(unifiedMarkerManager.markers.values());
}

// Call setVisibleRange
chart.timeScale().setVisibleRange({ from: startTime, to: endTime });

// Immediately restore after range change
if (rangeChangeMarkers.length > 0) {
    candlestickSeries.setMarkers(rangeChangeMarkers);
}
```

**3. Emergency Recovery System - Lines 3051-3076**
```javascript
// Verify markers exist 100ms after navigation
setTimeout(() => {
    const managerCount = unifiedMarkerManager ? unifiedMarkerManager.getMarkerCount() : 0;
    
    if (managerCount > 0) {
        // Force markers visible if manager has them
        const allMarkers = Array.from(unifiedMarkerManager.markers.values());
        candlestickSeries.setMarkers(allMarkers);
    } else if (managerCount === 0) {
        // Emergency rebuild from accumulated data
        const fractalSource = accumulatedFractals.length > 0 ? accumulatedFractals : window.accumulatedFractals;
        if (document.getElementById('showFractals').checked && fractalSource && fractalSource.length > 0) {
            unifiedMarkerManager.loadFractals(fractalSource);
            unifiedMarkerManager.forceUpdate();
        }
    }
}, 100);
```

**4. Streamlined UnifiedMarkerManager - Lines 1138-1142**
```javascript
// Removed problematic 100ms timeout verification
// Immediate verification only
console.log(`🔍 IMMEDIATE VERIFY: Series valid=${!!currentSeries}, Manager has ${this.getMarkerCount()} markers`);
this.lastSuccessfulMarkerCount = markersArray.length;
```

#### **TESTING PROTOCOL**

**🧪 VERIFICATION STEPS**
1. **Start Research Dashboard**: `python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &`
2. **Load Data**: Select DJ30, M1, date range with fractal data
3. **Enable Fractals**: Check "Show Fractals" checkbox
4. **Test Navigation**: Press "Next Bar" multiple times
5. **Verify Persistence**: Markers should remain visible when idle
6. **Check Console**: Look for restoration success messages

**🔍 SUCCESS INDICATORS**
- Console shows: "✅ Direct setMarkers successful"
- Console shows: "✅ FINAL: X markers forcibly restored"
- Fractal arrows (red ↑, blue ↓) remain visible between navigation
- No "No fractals to display" messages after successful application

**❌ FAILURE INDICATORS**  
- Console shows: "❌ Direct setMarkers failed"
- Console shows: "🚨 EMERGENCY: Manager empty but should have X fractals"
- Markers disappear within 1-2 seconds of navigation
- User reports same symptoms as before

#### **FUTURE DEBUGGING GUIDE - IF ISSUE PERSISTS**

**🔧 DEBUGGING APPROACH**
1. **Console Analysis**
   - Check for "SAVING X markers before setData" messages
   - Verify "Direct setMarkers successful" appears
   - Look for emergency recovery triggers
   - Monitor accumulated fractal array sizes

2. **TradingView API Investigation**
   - Test if `candlestickSeries.setMarkers()` is actually persistent
   - Try alternative marker setting approaches
   - Check if series reference becomes invalid

3. **Data Flow Verification**
   - Confirm `accumulatedFractals` array maintains data
   - Verify `window.accumulatedFractals` synchronization
   - Check if `UnifiedMarkerManager.markers` Map stays populated

**🛠️ ALTERNATIVE APPROACHES IF CURRENT FIX FAILS**

**Approach 1: Completely Avoid setData() Operations**
```javascript
// Instead of setData(), use only incremental .update() calls
// This preserves markers but may be slower for large data sets
for (let i = lastPosition; i <= newPosition; i++) {
    candlestickSeries.update(chartData[i]);
}
```

**Approach 2: Marker Reconstruction After Every Chart Operation**
```javascript
// Always rebuild markers from source data after any chart change
function rebuildMarkersFromSource() {
    if (document.getElementById('showFractals').checked) {
        const markers = convertFractalsToMarkers(accumulatedFractals);
        candlestickSeries.setMarkers(markers);
    }
}
```

**Approach 3: TradingView Drawing Primitives**
```javascript
// Use TradingView's drawing primitive API instead of markers
// This may be more persistent across chart operations
const fractalPrimitive = {
    // Implement custom drawing primitive for fractals
};
chart.addPrimitive(fractalPrimitive);
```

**Approach 4: Chart Recreation Strategy**
```javascript
// Instead of updating existing chart, recreate entire chart instance
// More robust but slower performance
function recreateChartWithData(newData, markers) {
    chart.remove();
    chart = createChart(container, options);
    candlestickSeries = chart.addCandlestickSeries();
    candlestickSeries.setData(newData);
    candlestickSeries.setMarkers(markers);
}
```

#### **TECHNICAL REFERENCE**

**📁 Key Files:**
- `/src/research/dashboard/research_api.py` - Main implementation (lines 2858-3076, 1030-1214)
- `/mnt/d/trading_bot/CLAUDE.md` - This documentation

**🔧 Key Functions:**
- `updateChartProgressive()` - Handles chart data updates and marker persistence
- `UnifiedMarkerManager.performUpdate()` - Manages marker application to chart
- `updateAllMarkers()` - Orchestrates all marker updates
- `replayAction()` - Navigation button handler

**🔍 Debug Console Commands:**
```javascript
// Check manager state
console.log('Manager markers:', unifiedMarkerManager.getMarkerCount());
console.log('Accumulated fractals:', accumulatedFractals.length);

// Force marker restoration
unifiedMarkerManager.forceUpdate();

// Direct marker application
candlestickSeries.setMarkers(Array.from(unifiedMarkerManager.markers.values()));
```

**⚡ EXPECTED OUTCOME**
- Markers persist throughout navigation
- No disappearing behavior during chart operations  
- Robust recovery from any chart state corruption
- Eliminates user frustration with marker visibility

**📋 NEXT STEPS IF ISSUE PERSISTS**
1. Implement TradingView Drawing Primitives approach
2. Consider chart recreation strategy for maximum reliability
3. Add real-time marker state monitoring
4. Implement user notification system for marker restoration events

### Previous Session Progress (July 6, 2025)
**✅ SUPPLY & DEMAND ZONE IMPLEMENTATION PROGRESS**

#### Current Implementation Status:
1. **Supply & Demand Zone Manager** ✅ COMPLETED
2. **Zone Visualization** ⚠️ PARTIAL SUCCESS (price line boundaries functional)
3. **UI Controls Integration** ✅ COMPLETED

#### Research Dashboard Status:
- **Server**: Running successfully at http://localhost:8001
- **S&D Zones**: Price line boundaries functional (rectangular fill pending)
- **Other Features**: Fractals, swings, ABC patterns all operational ✅

### Previous Session Progress (July 3, 2025)
**✅ SWING DETECTION SYSTEM FULLY COMPLETED AND OPERATIONAL**

#### Major Achievements Completed:
1. **Swing Detection & Visualization** ✅ FULLY WORKING
   - Elliott Wave compliant swing structure with 140-candle lookback window
   - Automatic swing extension to new extremes within lookback period
   - Professional TradingView swing line drawing with anti-flashing optimizations
   - Real-time swing updates synchronized between backend and frontend

2. **Critical Swing Extension Bug Fixes** ✅ COMPLETED
   - **Lookback window blocking**: Fixed recalculation triggers for new extremes
   - **Frontend-backend gap**: Added missing swing processing in frontend
   - **Line flashing issue**: Implemented data change detection and debounce protection
   - **Performance optimization**: Smart caching to prevent unnecessary redraws

3. **Previous Fractal System** ✅ FULLY WORKING
   - 5-bar fractal pattern detection confirmed accurate
   - Red arrows (↑) for high fractals, blue arrows (↓) for low fractals
   - Perfect synchronization between backend detection and frontend display
   - TradingView marker management following official best practices

#### Technical Implementation Completed:
- **SwingLineManager**: Professional TradingView swing line drawing with data change detection
- **Backend Swing Processing**: Enterprise-level lookback window recalculation logic  
- **Frontend-Backend Synchronization**: Real-time swing update processing via WebSocket/API
- **FractalMarkerManager**: Professional TradingView marker handling class
- **Performance Optimization**: Anti-flashing, debounce protection, smart caching
- **Elliott Wave Compliance**: Professional market structure analysis rules implemented

#### Current System Status:
- **Fractal Detection**: ✅ WORKING PERFECTLY (Real-time fractal detection confirmed)
- **Fractal Visualization**: ✅ WORKING PERFECTLY (TradingView markers stable)
- **Swing Detection**: ✅ WORKING PERFECTLY (Elliott Wave compliant swing structure)
- **Swing Visualization**: ✅ WORKING PERFECTLY (Smooth line drawing, no flashing)
- **Dashboard Access**: ✅ FULLY OPERATIONAL at http://localhost:8001
- **Chart Navigation**: ✅ STABLE (Anti-flashing optimizations applied)
- **Strategy Verification**: ✅ CONFIRMED ACCURATE (User testing completed)

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

### 🚀 Quick Reference Commands
**Research Dashboard**: `python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &`
**Main Dashboard**: `python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &`
**Database**: PostgreSQL required - see [DATABASE_SETUP.md](docs/development/DATABASE_SETUP.md)
**Testing**: Check [TESTING_STRATEGY.md](docs/development/TESTING_STRATEGY.md) for test commands
**Git Workflow**: See [GIT_WORKFLOW_GUIDE.md](docs/development/GIT_WORKFLOW_GUIDE.md)

### 🔄 Session Handoff Protocol
**For next Claude agent to continue this work:**

#### **✅ COMPLETED STATUS (July 3, 2025)**
- **Research Dashboard**: FULLY OPERATIONAL at http://localhost:8001
- **Server Command**: `python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &`
- **Fractal Visualization**: Working perfectly with proper TradingView markers ✅
- **Swing Detection & Visualization**: FULLY WORKING with Elliott Wave compliance ✅
- **Performance**: All major issues resolved, anti-flashing optimizations applied ✅
- **Documentation**: Enhanced CLAUDE.md with comprehensive tracking and links ✅

#### **📋 TASK STATUS TRACKER**
- [x] **Phase 1**: Data Pipeline - COMPLETED
- [x] **Phase 2**: Fibonacci Trading System - COMPLETED  
- [x] **Phase 3.1**: Fractal Detection & Visualization - COMPLETED ✅
- [x] **Phase 3.2**: Swing Detection Visualization - COMPLETED ✅
- [⚠️] **Phase 3.2.5**: Supply & Demand Zone Visualization - PARTIAL (boundaries only)
- [ ] **Phase 3.3**: Fibonacci Level Display - NEXT PRIORITY 🎯
- [ ] **Phase 3.4**: Signal Generation Visualization - PENDING
- [ ] **Phase 4**: Production Deployment - PENDING

## **NEXT DEVELOPMENT PHASE 🎯**

### **IMMEDIATE NEXT STEPS (Priority Order):**

#### 1. **Complete Supply & Demand Zone Rectangles** 🟠 HIGH PRIORITY (OPTIONAL)
- **Current Status**: Zone boundaries showing with price lines (functional)
- **Goal**: Implement proper rectangular filled zones between top/bottom prices
- **Technical Challenge**: TradingView Lightweight Charts lacks native rectangle support
- **Solution Options**: Drawing primitives plugin (`npm create lwc-plugin@latest`)
- **Decision**: Continue with current price line approach OR implement plugin solution
- **Note**: Current implementation is functional for trading analysis

#### 2. **Fibonacci Level Display** 🔴 HIGH PRIORITY  
- **Goal**: Show Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- **Implementation**: Calculate and display horizontal lines at Fibonacci levels
- **Location**: Enhance existing FibonacciLevelManager class in research_api.py
- **Visual**: Professional horizontal lines with percentage labels
- **Status**: Basic implementation exists, needs enhancement and integration with swing updates

#### 3. **Signal Generation Visualization** 🟡 MEDIUM PRIORITY
- **Goal**: Display entry/exit signals based on Fibonacci touch points
- **Implementation**: Signal detection algorithm with visual markers
- **Visual**: Green/red circles for entry/exit points with labels

#### 4. **Optional: Fractal Timing Investigation** 🟢 LOW PRIORITY
- **Context**: User noticed potential 2-bar delay in fractal display
- **Task**: Use enhanced debugging system to analyze fractal timing behavior
- **Method**: Check console logs for "TIMING:" messages during navigation
- **Goal**: Confirm if delay is algorithm feature or display issue

## **RESEARCH DASHBOARD SERVER STARTUP - RELIABLE INSTRUCTIONS**

### **CRITICAL: Always Use Background Mode to Prevent Connection Issues**

#### **✅ CORRECT WAY - Start Server in Background:**
```bash
# Navigate to project directory
cd /mnt/d/trading_bot

# Start server in background (MANDATORY for reliable operation)
python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &

# Wait 2-3 seconds for initialization
sleep 3

# Verify server is running and responding
curl -s -o /dev/null -w "Server Status: %{time_total} seconds - HTTP %{http_code}" http://localhost:8001/
```

#### **❌ AVOID - Foreground Mode (Can Cause "Site Can't Be Reached" Issues):**
```bash
# DON'T USE: This can cause connection timeouts
python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001
```

#### **Server Management Commands:**
```bash
# Check if server is running
ps aux | grep "uvicorn.*8001" | grep -v grep

# Stop server if needed
pkill -f "uvicorn.*8001"

# Restart server (kill + start)
pkill -f "uvicorn.*8001" && sleep 2 && python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &
```

#### **Access Dashboard:**
- **URL**: http://localhost:8001
- **Expected Response**: Dashboard with symbol/date range dropdowns
- **Success Indicators**: 
  - "Found X symbols with data" in logs
  - WebSocket connections established
  - API calls responding (200 OK status)

#### **Troubleshooting:**
- **"Site can't be reached"**: Server likely stopped - restart in background mode
- **Connection timeout**: Check server logs for database connection issues
- **Port in use**: Kill existing process first with `pkill -f "uvicorn.*8001"`

## **🔑 KEY FILES FOR NEXT PHASE**
- **Main Implementation**: [`src/research/dashboard/research_api.py`](src/research/dashboard/research_api.py) - Dashboard API
- **Implementation Guide**: [`docs/architecture/BACKTESTING_SYSTEM.md`](docs/architecture/BACKTESTING_SYSTEM.md) - Roadmap
- **Strategy Logic**: [`src/strategy/backtesting_engine.py`](src/strategy/backtesting_engine.py) - Backend
- **Strategy Requirements**: [`docs/architecture/STRATEGY_REQUIREMENTS.md`](docs/architecture/STRATEGY_REQUIREMENTS.md) - **CRITICAL**
- **Testing Files**: [`tests/`](tests/) - Unit tests and verification
- **User Guide**: [`docs/user-guide/RESEARCH_DASHBOARD_GUIDE.md`](docs/user-guide/RESEARCH_DASHBOARD_GUIDE.md)

## **✅ SUCCESS CRITERIA FOR NEXT PHASE**
- [ ] **Swing Detection**: Lines connecting fractals with proper Elliott Wave rules
- [ ] **Fibonacci Levels**: Horizontal lines at 23.6%, 38.2%, 50%, 61.8%, 78.6% retracement levels
- [ ] **Signal Generation**: Entry/exit signals at Fibonacci touch points
- [ ] **Documentation**: All new features documented in relevant guides
- [ ] **Testing**: Unit tests for new visualization components
- [ ] **Performance**: Maintain ~160ms execution speed requirements

## **📖 DOCUMENTATION MAINTENANCE REMINDERS**
- **MANDATORY**: Update [`docs/architecture/BACKTESTING_SYSTEM.md`](docs/architecture/BACKTESTING_SYSTEM.md) when implementing new features
- **REQUIRED**: Update [`docs/user-guide/RESEARCH_DASHBOARD_GUIDE.md`](docs/user-guide/RESEARCH_DASHBOARD_GUIDE.md) for UI changes
- **CRITICAL**: Keep [`docs/architecture/STRATEGY_REQUIREMENTS.md`](docs/architecture/STRATEGY_REQUIREMENTS.md) aligned with implementation
- **IMPORTANT**: Update [CHANGELOG.md](CHANGELOG.md) with each significant change

---

## **MARKER PERSISTENCE TESTING PROTOCOL 🔍**

### **🚨 CRITICAL ISSUE: Chart Markers Disappearing (July 7, 2025)**

#### **Problem Summary:**
- **Symptoms**: Fractal markers appear briefly when pressing "Next Bar" but immediately disappear
- **User Report**: "Still fractals don't stay and others, when I move next bar (I can see it but it goes away."
- **Console Evidence**: Shows "Applied 1 total markers (1 fractals)" followed by "No fractals to display"
- **Status**: ACTIVE INVESTIGATION - Debug logging added, root cause identified

#### **Root Cause Analysis Completed:**
1. **Data Source Inconsistency**: `updateAllMarkers()` was checking empty local `accumulatedFractals` while `window.accumulatedFractals` had data
2. **Double Function Calls**: Both `restoreAllMarkersAfterChartUpdate()` and `updateAllMarkers()` were called, causing conflicts
3. **Sequence Issue**: Markers restored by first function, then cleared by second function checking wrong data source

#### **Fixes Applied (Session: July 7, 2025):**
1. **✅ Fixed Data Source Logic**: Modified `updateAllMarkers()` to check both local and global fractal arrays
2. **✅ Eliminated Double Calls**: Removed redundant `restoreAllMarkersAfterChartUpdate()` call during navigation
3. **✅ Added Debug Logging**: Enhanced console logging to trace exact data flow
4. **✅ Centralized Logging Control**: Implemented `debugLog()` system to reduce console spam
5. **✅ Fixed Infinite Recursion**: Removed recursive call in `loadAccumulatedStrategyElements`

#### **Testing Protocol for Next Session:**

##### **🔍 Step 1: Initial Verification**
1. **Start Research Dashboard**: `python3 -m uvicorn src.research.dashboard.research_api:app --host 127.0.0.1 --port 8001 &`
2. **Load Sample Data**: DJ30 M1 data with fractal checkbox CHECKED
3. **Verify Console Output**: Should see debug messages about fractal data sources

##### **🔍 Step 2: Navigation Testing**
1. **Press "Next Bar" button** and observe:
   - Console logs showing: `🔍 BEFORE updateAllMarkers: local=X, global=Y, checkbox=true`
   - Should see: `📍 Showing X fractals from global source` (if local is empty)
   - Should see: `🔍 AFTER updateAllMarkers: unified manager has X markers`
2. **Wait 5 seconds without interaction** - fractals should remain visible
3. **Press "Next Bar" again** - fractals should persist between navigation

##### **🔍 Step 3: Expected Console Output Pattern**
```
🔍 BEFORE updateAllMarkers: local=0, global=150, checkbox=true
🔍 loadFractals: Removing existing fractals, then loading 150 new fractals  
🔍 loadFractals: After processing, unified manager has 150 total markers
📍 Showing 150 fractals from global source
🔍 AFTER updateAllMarkers: unified manager has 150 markers
```

##### **🔍 Step 4: If Issue Persists**
Look for these specific patterns in console:
- **Data Source Issues**: Local and global both showing 0 fractals
- **Checkbox Issues**: `checkbox=false` when it should be true
- **Manager Issues**: Unified manager showing 0 markers after loading
- **Timing Issues**: Markers being loaded but immediately cleared

#### **Key Files Modified:**
- **Main File**: `src/research/dashboard/research_api.py`
- **Functions Changed**: `updateAllMarkers()`, `updateChartProgressive()`, `loadAllStrategyElements()`
- **Debug Logging**: Enhanced `UnifiedMarkerManager.loadFractals()` method

#### **Critical Code Changes to Verify:**
1. **Line ~3033**: `updateAllMarkers()` now checks both data sources
2. **Line ~2950**: Debug logs before/after `updateAllMarkers()` calls  
3. **Line ~1171**: Enhanced logging in `UnifiedMarkerManager.loadFractals()`
4. **Line ~4915**: Proper fractal accumulation in `loadAllStrategyElements()`

#### **Success Criteria:**
- [ ] Fractals remain visible when idle (no button pressing)
- [ ] Fractals persist during navigation between bars
- [ ] Console shows consistent marker counts
- [ ] No "No fractals to display" when fractals should be visible
- [ ] Debug logs confirm data flow from global arrays to unified manager

---

### 🔗 **MASTER DOCUMENTATION INDEX**
**Quick access to all project documentation:**
- 📋 [Project Overview](PROJECT_DOCUMENTATION.md) | 📝 [Main README](README.md) | 🔄 [Changelog](CHANGELOG.md)
- 🏗️ [Architecture Docs](docs/architecture/) | 🔌 [API Docs](docs/api/) | 👥 [User Guides](docs/user-guide/)
- 💻 [Development Docs](docs/development/) | 🚀 [Deployment Guides](docs/deployment/)
- 🧪 [Testing Docs](tests/README.md) | 🛠️ [Tools Docs](tools/README.md)

**Remember**: Documentation completeness is part of task completion. No task is complete until relevant docs are updated.

### Development Environment
- **User Platform**: Windows with WSL for communication  
- **MT5 Environment**: Windows-only (MetaTrader5 Python API)
- **WSL Mode**: Demo mode with functional dashboard
- **Production Mode**: Windows with full MT5 integration