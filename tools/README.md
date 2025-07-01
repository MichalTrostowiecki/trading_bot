# Tools and Utilities

This directory contains development tools, scripts, and utilities for the Fibonacci Trading Bot.

## Directory Structure

### 🔨 Scripts (`scripts/`)
Standalone scripts for system management:
- `install_core_dependencies.py` - Install required dependencies
- `setup_development_environment.py` - Set up development environment
- `setup_trading_bot.py` - Configure trading bot
- `simple_mt5_test.py` - Basic MT5 connection test
- `test_mt5_connection.py` - Comprehensive MT5 testing

### ⚙️ Utilities (`utilities/`)
Utility scripts for data and system management:
- `setup_postgres.py` - PostgreSQL database setup
- `import_csv_data.py` - Import historical data from CSV files

### 🛠️ Development (`development/`)
Development and debugging tools:
- `start_research_dashboard.py` - Start the research dashboard
- `run_dashboard.sh` - Dashboard runner script
- `stop_dashboard.sh` - Stop dashboard processes

## Usage Examples

### Environment Setup
```bash
# Install core dependencies
python tools/scripts/install_core_dependencies.py

# Set up development environment
python tools/scripts/setup_development_environment.py

# Configure trading bot
python tools/scripts/setup_trading_bot.py
```

### Database Management
```bash
# Set up PostgreSQL database
python tools/utilities/setup_postgres.py

# Import historical data
python tools/utilities/import_csv_data.py --symbol DJ30 --file data/DJ301.csv
```

### Development Tools
```bash
# Start research dashboard
python tools/development/start_research_dashboard.py

# Or use shell script
./tools/development/run_dashboard.sh
```

### Testing MT5 Connection
```bash
# Basic connection test
python tools/scripts/simple_mt5_test.py

# Comprehensive test
python tools/scripts/test_mt5_connection.py
```

## Guidelines

1. **Scripts** should be self-contained and documented
2. **Use proper error handling** and logging
3. **Include help messages** and usage examples
4. **Make scripts executable** where appropriate
5. **Keep tools organized** by purpose and complexity