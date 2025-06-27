# Contributing to Fibonacci Trading Bot

Thank you for your interest in contributing to the Fibonacci Trading Bot project. This document provides guidelines and information for contributors.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Process](#contributing-process)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Guidelines](#documentation-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Windows 10/11 (for MetaTrader 5 compatibility)
- Python 3.9 or higher
- Git installed and configured
- MetaTrader 5 terminal (for testing)
- Basic understanding of trading concepts

### Understanding the Project

1. Read the [README.md](README.md) for project overview
2. Review [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for detailed specifications
3. Check [docs/GIT_WORKFLOW_GUIDE.md](docs/GIT_WORKFLOW_GUIDE.md) for our Git workflow

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/trading-bot-ai.git
cd trading-bot-ai

# Add upstream remote
git remote add upstream https://github.com/original-owner/trading-bot-ai.git
```

### 2. Environment Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy configuration template
copy config\development.yaml.template config\development.yaml
# Edit config\development.yaml with your settings
```

### 3. Verify Setup

```bash
# Run tests to ensure everything works
pytest tests/unit/ -v

# Check code quality
black --check src/
flake8 src/
mypy src/
```

## Contributing Process

### 1. Choose Your Contribution

- Check existing [issues](../../issues) for bug reports or feature requests
- Look for issues labeled `good first issue` or `help wanted`
- Propose new features by creating an issue first

### 2. Create a Branch

```bash
# Create feature branch from main
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 3. Development Workflow

1. Make your changes following our coding standards
2. Write tests for new functionality
3. Update documentation if needed
4. Run quality checks locally
5. Commit with conventional commit format

### 4. Stay Updated

```bash
# Regularly sync with upstream
git fetch upstream
git rebase upstream/main
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these tools:

- **Black**: Code formatting (line length: 88)
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **isort**: Import sorting

### Code Quality Requirements

- **Type Hints**: All functions must have type hints
- **Docstrings**: All public functions need Google-style docstrings
- **Error Handling**: Proper exception handling with specific exception types
- **Logging**: Use loguru for logging instead of print statements

### Example Code Style

```python
from typing import Optional, List, Dict
from loguru import logger

class TradingStrategy:
    """Fibonacci-based trading strategy implementation.
    
    This class implements the core Fibonacci retracement continuation
    strategy with ML-enhanced signal generation.
    
    Attributes:
        fibonacci_levels: List of Fibonacci retracement levels to use.
        confidence_threshold: Minimum ML confidence score for signals.
    """
    
    def __init__(self, fibonacci_levels: List[float]) -> None:
        """Initialize the trading strategy.
        
        Args:
            fibonacci_levels: List of Fibonacci levels (e.g., [0.382, 0.618]).
            
        Raises:
            ValueError: If fibonacci_levels is empty or contains invalid values.
        """
        if not fibonacci_levels:
            raise ValueError("Fibonacci levels cannot be empty")
        
        self.fibonacci_levels = fibonacci_levels
        logger.info(f"Initialized strategy with levels: {fibonacci_levels}")
    
    def generate_signal(self, market_data: Dict[str, float]) -> Optional[Dict]:
        """Generate trading signal based on market data.
        
        Args:
            market_data: Dictionary containing OHLC data.
            
        Returns:
            Trading signal dictionary or None if no signal.
            
        Raises:
            ValueError: If market_data is invalid.
        """
        try:
            # Implementation here
            pass
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            raise
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(fibonacci): add dynamic level calculation
fix(data): resolve MT5 connection timeout
docs(api): update endpoint documentation
test(core): add unit tests for fractal detection
```

## Testing Guidelines

### Test Categories

1. **Unit Tests** (tests/unit/): Test individual functions/classes
2. **Integration Tests** (tests/integration/): Test component interactions
3. **Performance Tests** (tests/performance/): Test system performance

### Writing Tests

```python
import pytest
from src.core.fibonacci import FibonacciCalculator

class TestFibonacciCalculator:
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance for testing."""
        return FibonacciCalculator()
    
    def test_calculate_retracements_valid_input(self, calculator):
        """Test retracement calculation with valid input."""
        start_price = 1.0800
        end_price = 1.0900
        
        result = calculator.calculate_retracements(start_price, end_price)
        
        assert 'retracements' in result
        assert len(result['retracements']) == 5  # Standard levels
        assert 0.382 in result['retracements']
    
    def test_calculate_retracements_invalid_input(self, calculator):
        """Test retracement calculation with invalid input."""
        with pytest.raises(ValueError, match="Invalid price range"):
            calculator.calculate_retracements(1.0900, 1.0800)  # start > end
```

### Test Requirements

- Minimum 90% code coverage for new code
- All tests must pass before merging
- Include both positive and negative test cases
- Mock external dependencies (MT5, databases, APIs)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

## Documentation Guidelines

### Documentation Types

1. **Code Documentation**: Docstrings for all public APIs
2. **User Documentation**: Guides and tutorials
3. **Developer Documentation**: Architecture and design docs
4. **API Documentation**: REST API specifications

### Docstring Format

Use Google-style docstrings:

```python
def calculate_position_size(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float
) -> float:
    """Calculate position size based on risk management rules.
    
    Args:
        account_balance: Current account balance in base currency.
        risk_percentage: Risk as decimal (e.g., 0.01 for 1%).
        entry_price: Planned entry price for the trade.
        stop_loss: Stop loss price for the trade.
        
    Returns:
        Position size in lots.
        
    Raises:
        ValueError: If any parameter is invalid or would result in
            negative position size.
            
    Example:
        >>> calc = PositionSizer()
        >>> size = calc.calculate_position_size(10000, 0.01, 1.0850, 1.0800)
        >>> print(f"Position size: {size} lots")
        Position size: 0.20 lots
    """
```

## Pull Request Process

### Before Creating a PR

1. Ensure your branch is up to date with main
2. Run the full test suite locally
3. Check code quality with all linting tools
4. Update documentation if needed
5. Add entry to CHANGELOG.md if applicable

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages follow conventional format
- [ ] PR description explains changes clearly
- [ ] Referenced related issues

### PR Template

When creating a PR, use this template:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented appropriately
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. Automated checks must pass
2. At least one code review required
3. Address all review feedback
4. Maintain clean commit history
5. Squash commits before merge if requested

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 10]
- Python Version: [e.g., 3.9.7]
- MT5 Version: [e.g., 5.0.45]

**Additional Context**
Any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the feature you'd like to see.

**Problem Statement**
What problem would this feature solve?

**Proposed Solution**
How you envision this feature working.

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Any other context or screenshots.
```

## Getting Help

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers at dev@fibonacci-trading-bot.com

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- Release notes for major features

Thank you for contributing to the Fibonacci Trading Bot project!