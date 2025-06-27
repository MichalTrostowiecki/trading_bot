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
- **Phase**: Phase 2 - Complete Fibonacci Trading System (COMPLETED)
- **Next Phase**: Production Deployment & Optimization
- **Repository**: Fully functional automated trading bot with real MT5 integration
- **Structure**: Complete end-to-end trading system with web dashboard
- **Strategy Status**: Fibonacci retracement strategy fully implemented and operational

### Strategy Context
- **Core Strategy**: Fibonacci Retracement Continuation Strategy
- **Approach**: Fractal-based swing identification with Fibonacci entry levels
- **Direction**: Trade in direction of dominant swing for continuation moves
- **Requirements Doc**: `docs/STRATEGY_REQUIREMENTS.md` - **CRITICAL REFERENCE**
- **Status**: Detailed Q&A in progress to capture exact strategy specifications

### AI Agent Instructions
When working on this project:
1. **System is PRODUCTION READY** - fully functional automated trading bot
2. **MT5 Integration**: Real BlueberryMarkets demo account (Login: 12605399)
3. **Web Dashboard**: Available at http://localhost:8000 with live charts and controls
4. **Chart Features**: Enhanced Fibonacci visualization with proper swing detection
5. **Order Placement**: Successfully placing real MT5 orders with proper risk management
6. **Deployment**: Ready for VPS deployment for 24/7 automated trading
7. **Documentation**: All implementation details documented in project files
8. **Testing**: System tested and verified with live MT5 connection

### Development Environment
- **User Platform**: Windows with WSL for communication  
- **MT5 Environment**: Windows-only (MetaTrader5 Python API)
- **WSL Mode**: Demo mode with functional dashboard
- **Production Mode**: Windows with full MT5 integration