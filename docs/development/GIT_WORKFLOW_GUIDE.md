# Git Workflow Guide - Fibonacci Trading Bot Project

## Overview
This document establishes the Git workflow and best practices for the Fibonacci-based AI trading bot project, ensuring consistent collaboration, code quality, and release management across the development team.

## Repository Information
- **Repository URL**: `git@github.com:MichalTrostowiecki/trading_bot.git`
- **Primary Branch**: `main`
- **Workflow Model**: GitHub Flow (simplified GitFlow for agile development)
- **License**: MIT License

## 1. Repository Setup

### Initial Clone and Setup
```bash
# Clone the repository
git clone git@github.com:MichalTrostowiecki/trading_bot.git
cd trading_bot

# Verify remote configuration
git remote -v
# origin  git@github.com:MichalTrostowiecki/trading_bot.git (fetch)
# origin  git@github.com:MichalTrostowiecki/trading_bot.git (push)

# Set up user configuration (if not already configured globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Set up GPG signing (recommended for security)
git config commit.gpgsign true
git config user.signingkey YOUR_GPG_KEY_ID
```

### Development Environment Setup
```bash
# Create and activate Python virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Verify setup
python -c "import MetaTrader5; print('MT5 package available')"
pytest --version
```

### IDE Configuration
```bash
# VS Code settings (create .vscode/settings.json)
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "git.enableCommitSigning": true
}
```

## 2. Branch Strategy

### GitHub Flow Model
We use a simplified GitHub Flow model optimized for continuous integration and rapid development:

```
main (production-ready)
├── feature/fibonacci-calculation-engine
├── feature/mt5-integration
├── bugfix/fractal-detection-edge-case
├── hotfix/critical-position-sizing-bug
└── release/v1.0.0
```

### Branch Types and Naming Conventions

#### Main Branch
- **Branch**: `main`
- **Purpose**: Production-ready code
- **Protection**: Protected branch with required reviews
- **Deployment**: Automatically deploys to production

#### Feature Branches
- **Naming**: `feature/short-description`
- **Purpose**: New features and enhancements
- **Lifetime**: Created from `main`, merged back to `main`
- **Examples**:
  ```
  feature/fibonacci-calculation-engine
  feature/ai-signal-confidence-scoring
  feature/risk-management-system
  feature/real-time-data-streaming
  ```

#### Bugfix Branches
- **Naming**: `bugfix/short-description`
- **Purpose**: Non-critical bug fixes
- **Lifetime**: Created from `main`, merged back to `main`
- **Examples**:
  ```
  bugfix/fractal-detection-edge-case
  bugfix/memory-leak-data-collector
  bugfix/fibonacci-level-calculation-precision
  ```

#### Hotfix Branches
- **Naming**: `hotfix/critical-issue-description`
- **Purpose**: Critical production fixes
- **Lifetime**: Created from `main`, merged to `main` with immediate release
- **Examples**:
  ```
  hotfix/position-sizing-calculation-error
  hotfix/mt5-connection-timeout
  hotfix/stop-loss-execution-bug
  ```

#### Release Branches
- **Naming**: `release/vX.Y.Z`
- **Purpose**: Prepare releases, final testing, and documentation
- **Lifetime**: Created from `main`, merged back to `main` with tag
- **Examples**:
  ```
  release/v1.0.0
  release/v1.1.0
  release/v2.0.0-beta
  ```

### Branch Creation Commands
```bash
# Create and switch to feature branch
git checkout main
git pull origin main
git checkout -b feature/fibonacci-calculation-engine

# Create bugfix branch
git checkout -b bugfix/fractal-detection-edge-case

# Create hotfix branch
git checkout -b hotfix/position-sizing-calculation-error

# Create release branch
git checkout -b release/v1.0.0
```

## 3. Commit Guidelines

### Conventional Commit Format
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system or dependency changes
- **ci**: CI/CD configuration changes
- **chore**: Maintenance tasks

### Commit Examples
```bash
# Feature commits
git commit -m "feat(fibonacci): implement retracement level calculation"
git commit -m "feat(ai): add confidence scoring for trading signals"
git commit -m "feat(risk): implement dynamic position sizing algorithm"

# Bug fix commits
git commit -m "fix(fractals): handle edge case with insufficient data"
git commit -m "fix(mt5): resolve connection timeout issues"
git commit -m "fix(trading): correct stop loss calculation precision"

# Documentation commits
git commit -m "docs(api): update REST endpoint documentation"
git commit -m "docs(setup): add MT5 configuration instructions"

# Test commits
git commit -m "test(fibonacci): add unit tests for edge cases"
git commit -m "test(integration): add MT5 connection integration tests"
```

### Commit Message Guidelines
1. **Use imperative mood**: "Add feature" not "Added feature"
2. **Limit subject line**: 50 characters or less
3. **Capitalize subject line**: Start with capital letter
4. **No period**: Don't end subject line with period
5. **Separate subject and body**: Use blank line
6. **Wrap body**: 72 characters per line
7. **Explain what and why**: Not how

### Detailed Commit Example
```
feat(ai): implement machine learning signal confidence scoring

Add TensorFlow-based model to score trading signal quality based on:
- Market volatility indicators
- Fibonacci level confluence strength
- Historical success rate at similar setups
- Time-based market regime classification

The model achieves 73% accuracy on validation data and improves
overall strategy performance by 15% in backtesting.

Closes #42
Refs #38, #41
```

## 4. Pull Request Process

### PR Creation Workflow
```bash
# 1. Ensure branch is up to date
git checkout feature/fibonacci-calculation-engine
git fetch origin
git rebase origin/main

# 2. Run local tests
pytest tests/ -v
black src/ tests/
flake8 src/ tests/

# 3. Push branch
git push origin feature/fibonacci-calculation-engine

# 4. Create PR via GitHub UI or CLI
gh pr create --title "feat(fibonacci): implement retracement calculation engine" \
             --body "Implements core Fibonacci retracement calculation with configurable levels"
```

### PR Template
Create `.github/pull_request_template.md`:
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance benchmarks met

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation updated
- [ ] No new warnings introduced

## Related Issues
Closes #(issue_number)
Refs #(issue_number)

## Screenshots/Logs
If applicable, add screenshots or log outputs.
```

### Code Review Requirements
1. **Minimum Reviewers**: 1 for features, 2 for critical components
2. **Required Checks**: All CI/CD checks must pass
3. **Review Criteria**:
   - Code quality and style compliance
   - Test coverage (minimum 90%)
   - Documentation completeness
   - Performance impact assessment
   - Security considerations

### Automated Checks
```yaml
# .github/workflows/pr-checks.yml
name: PR Checks
on: [pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Code quality checks
        run: |
          black --check src/ tests/
          flake8 src/ tests/
          mypy src/
      
      - name: Security scan
        run: bandit -r src/
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Merge Strategies
- **Squash and Merge**: Default for feature branches (clean history)
- **Merge Commit**: For release branches (preserve branch history)
- **Rebase and Merge**: For small, clean commits

## 5. Release Management

### Semantic Versioning
We follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process
```bash
# 1. Create release branch
git checkout main
git pull origin main
git checkout -b release/v1.0.0

# 2. Update version numbers
# Update version in src/__init__.py, setup.py, etc.

# 3. Update CHANGELOG.md
# Add release notes and changes

# 4. Commit version bump
git add .
git commit -m "chore(release): bump version to v1.0.0"

# 5. Push and create PR
git push origin release/v1.0.0
gh pr create --title "Release v1.0.0" --body "Release version 1.0.0"

# 6. After PR approval and merge, create tag
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 7. Create GitHub release
gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG.md
```

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Deployment tested in staging
- [ ] Release notes prepared

### Hotfix Release Process
```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-position-sizing-bug

# 2. Fix the issue
# Make necessary changes

# 3. Test thoroughly
pytest tests/ -v
# Run specific tests for the fix

# 4. Commit fix
git add .
git commit -m "fix(trading): correct position sizing calculation precision"

# 5. Create PR for immediate review
git push origin hotfix/critical-position-sizing-bug
gh pr create --title "HOTFIX: Critical position sizing bug" \
             --body "Fixes critical bug in position sizing calculation" \
             --label "hotfix,critical"

# 6. After merge, create patch release
git checkout main
git pull origin main
git tag -a v1.0.1 -m "Hotfix release v1.0.1"
git push origin v1.0.1
```

## 6. Collaboration Guidelines

### Code Ownership
- **Core Strategy**: Lead Developer + Strategy Expert
- **Data Pipeline**: Data Engineer + Lead Developer  
- **ML Components**: ML Engineer + Lead Developer
- **Testing**: All team members
- **Documentation**: All team members

### Conflict Resolution
1. **Merge Conflicts**: Resolve locally before pushing
2. **Design Disagreements**: Escalate to Lead Developer
3. **Code Style**: Follow automated tools (Black, Flake8)
4. **Architecture Decisions**: Document in ADR (Architecture Decision Records)

### Communication Protocols
- **Daily Standups**: Discuss current work and blockers
- **PR Reviews**: Complete within 24 hours
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for design questions

### Branch Protection Rules
```yaml
# GitHub branch protection settings for main
required_status_checks:
  strict: true
  contexts:
    - "test"
    - "code-quality"
    - "security-scan"

enforce_admins: true
required_pull_request_reviews:
  required_approving_review_count: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: true

restrictions:
  users: []
  teams: ["core-developers"]
```

## 7. CI/CD Integration

### GitHub Actions Workflows

#### Continuous Integration
```yaml
# .github/workflows/ci.yml
name: Continuous Integration
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Lint with flake8
        run: |
          flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
      
      - name: Format check with black
        run: black --check src/ tests/
      
      - name: Type check with mypy
        run: mypy src/
      
      - name: Security check with bandit
        run: bandit -r src/
      
      - name: Test with pytest
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=html
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

#### Continuous Deployment
```yaml
# .github/workflows/cd.yml
name: Continuous Deployment
on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: windows-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --max-complexity=10]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/]
```

### Quality Gates
All the following must pass before merge:
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] Code style checks (Black, Flake8)
- [ ] Type checking (MyPy)
- [ ] Security scan (Bandit)
- [ ] Performance benchmarks
- [ ] Documentation build
- [ ] Manual review approval

This Git workflow ensures enterprise-level code quality, security, and collaboration while maintaining development velocity and team productivity.
