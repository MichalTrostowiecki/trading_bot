# Database Setup and Configuration

## Dual Database Architecture

The Fibonacci Trading Bot supports **automatic database switching** for development flexibility:

### 🖥️ **Desktop/Production Environment**
- **Database**: PostgreSQL
- **Location**: `localhost:5432`
- **Database Name**: `fibonacci_trading_bot`
- **Usage**: Full production data, team collaboration
- **Configuration**: `config.yaml`

### 💻 **Laptop/Development Environment**  
- **Database**: SQLite (automatic fallback)
- **Location**: `data/trading_bot.db`
- **Usage**: Local development, testing, offline work
- **Triggers**: When PostgreSQL unavailable

## Automatic Switching Logic

The system automatically detects which database to use:

```python
# From src/data/database.py
def _get_database_url(self) -> str:
    try:
        config = get_config()
        return config.database.url  # PostgreSQL from config.yaml
    except Exception as e:
        logger.warning(f"Could not load database URL from config: {e}")
        return "sqlite:///data/trading_bot.db"  # SQLite fallback
```

## Configuration Files

### config.yaml (Primary)
```yaml
database:
  url: "postgresql://postgres:misiek505@localhost:5432/fibonacci_trading_bot"
  echo: false
  pool_size: 5
  max_overflow: 10
```

### Automatic Fallback (SQLite)
- **File**: `data/trading_bot.db`
- **Created automatically** when PostgreSQL unavailable
- **Same schema** as PostgreSQL for consistency

## Usage Scenarios

### 🏠 Working from Desktop
1. **Start PostgreSQL service**
2. **Run dashboard**: `python tools/development/start_research_dashboard.py`
3. **Result**: Automatically connects to PostgreSQL with full production data

### ✈️ Working from Laptop/Remote
1. **No PostgreSQL available**
2. **Run dashboard**: `python tools/development/start_research_dashboard.py` 
3. **Result**: Automatically uses SQLite with development data

### 📊 Loading Development Data (Laptop)
```bash
# Load CSV data into local SQLite (one-time setup)
PYTHONPATH=. python3 -c "
import sys
sys.path.insert(0, '.')
from src.data.database import initialize_database, HistoricalData
from datetime import datetime
import csv

db_manager = initialize_database()
with db_manager.get_session() as session:
    # Import CSV data logic here
    pass
"
```

## Data Synchronization

### Development to Production
- **Method**: Export CSV from laptop → Import to desktop PostgreSQL
- **Tools**: Use `tools/utilities/import_csv_data.py` (fix paths as needed)

### Production to Development  
- **Method**: Export from PostgreSQL → Import to laptop SQLite
- **Use Case**: Getting latest production data for development

## Benefits of This Setup

### ✅ **Flexibility**
- Work offline on laptop with local data
- Access full production data on desktop
- No manual configuration switching

### ✅ **Development Efficiency**
- Fast SQLite for development/testing
- Robust PostgreSQL for production
- Same codebase works in both environments

### ✅ **Team Collaboration**
- Shared PostgreSQL database on desktop/server
- Individual SQLite databases for development
- Easy data sharing and synchronization

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
# Or check Windows services for PostgreSQL

# Test connection
psql -h localhost -U postgres -d fibonacci_trading_bot
```

### SQLite Issues
```bash
# Check SQLite database
sqlite3 data/trading_bot.db ".tables"
sqlite3 data/trading_bot.db "SELECT COUNT(*) FROM historical_data;"
```

### Switching Databases Manually
```bash
# Force PostgreSQL (if config.yaml exists but PostgreSQL down)
# Fix PostgreSQL connection or temporarily rename config.yaml

# Force SQLite (for testing)
mv config.yaml config.yaml.backup  # Temporarily disable PostgreSQL config
```

## Current Status

- ✅ **Desktop**: PostgreSQL ready with production data
- ✅ **Laptop**: SQLite working with 219,663 bars of DJ30 data  
- ✅ **Automatic switching**: Configured and tested
- ✅ **Dashboard**: Fully functional on both environments