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
- **Phase**: Phase 1 - Foundation & Research Infrastructure (COMPLETED)
- **Next Phase**: Strategy Requirements Gathering & Phase 2 Planning
- **Repository**: Complete foundation with data pipeline, MT5 integration, and research tools
- **Structure**: Full implementation ready for strategy-specific development
- **Strategy Status**: Requirements gathering in progress

### Strategy Context
- **Core Strategy**: Fibonacci Retracement Continuation Strategy
- **Approach**: Fractal-based swing identification with Fibonacci entry levels
- **Direction**: Trade in direction of dominant swing for continuation moves
- **Requirements Doc**: `docs/STRATEGY_REQUIREMENTS.md` - **CRITICAL REFERENCE**
- **Status**: Detailed Q&A in progress to capture exact strategy specifications

### AI Agent Instructions
When working on this project:
1. **ALWAYS read `docs/STRATEGY_REQUIREMENTS.md` first** - contains specific strategy details
2. Check current phase and task status in todo list
3. Commit changes after each completed task
4. Update relevant documentation files
5. Follow the testing strategy outlined in docs
6. Use the dependency matrix for installation order
7. Reference the git workflow guide for procedures
8. **For strategy implementation**: Must follow exact specifications from requirements doc