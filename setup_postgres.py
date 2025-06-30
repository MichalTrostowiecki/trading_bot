#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
Creates the database and configures connection for the trading bot.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the trading bot database in PostgreSQL."""
    
    # Database connection details
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'misiek505'
    }
    
    database_name = 'fibonacci_trading_bot'
    
    print("🗄️  Setting up PostgreSQL database...")
    print("=" * 50)
    
    try:
        # Connect to PostgreSQL server (not to specific database)
        print("📡 Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL server")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️  Database '{database_name}' already exists")
            choice = input("Do you want to recreate it? (y/N): ").lower().strip()
            if choice == 'y':
                cursor.execute(f'DROP DATABASE "{database_name}"')
                print(f"🗑️  Dropped existing database '{database_name}'")
            else:
                print("✅ Using existing database")
                cursor.close()
                conn.close()
                return True
        
        # Create database
        if not exists or choice == 'y':
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            print(f"✅ Created database '{database_name}'")
        
        cursor.close()
        conn.close()
        
        # Test connection to new database
        test_conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=database_name
        )
        test_conn.close()
        print("✅ Database connection test successful")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_config_file():
    """Create configuration file with PostgreSQL settings."""
    
    config_content = '''# Fibonacci Trading Bot Configuration

# Database Configuration
database:
  url: "postgresql://postgres:misiek505@localhost:5432/fibonacci_trading_bot"
  echo: false
  pool_size: 5
  max_overflow: 10

# API Configuration  
api:
  host: "localhost"
  port: 8000
  debug: false

# Research Dashboard Configuration
research:
  host: "localhost"
  port: 8001
  debug: false

# MT5 Configuration
mt5:
  server: "BlueberryMarkets-Demo"
  login: 12605399
  password: "your_mt5_password"
  timeout: 10000

# Data Configuration
data:
  symbols: ["EURUSD", "GBPUSD", "USDJPY"]
  timeframes: ["M1", "M5", "M15", "H1", "H4", "D1"]
  history_days: 365
  cache_enabled: true
  cache_ttl: 3600

# Strategy Configuration
strategy:
  risk_per_trade: 0.02
  max_positions: 5
  max_daily_loss: 0.06
  fibonacci_levels:
    retracements: [23.6, 38.2, 50.0, 61.8, 78.6]
    extensions: [127.2, 161.8, 200.0, 261.8]

# Logging Configuration
logging:
  level: "INFO"
  file: "data/logs/trading_bot.log"
  max_size: "100MB"
  backup_count: 5

# ML Configuration
ml:
  model_retrain_days: 30
  feature_lookback: 100
  validation_split: 0.2
  random_state: 42
'''
    
    config_path = '/mnt/d/trading_bot/config.yaml'
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        print(f"✅ Created configuration file: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False

def test_database_connection():
    """Test the database connection with the trading bot."""
    
    print("\n🧪 Testing database integration...")
    
    try:
        # Add src to path
        sys.path.insert(0, '/mnt/d/trading_bot/src')
        
        from src.data.database import initialize_database
        
        # Initialize database with new PostgreSQL connection
        db_manager = initialize_database()
        
        if db_manager:
            print("✅ Database integration test successful")
            print("✅ All tables created in PostgreSQL")
            return True
        else:
            print("❌ Database integration test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database integration error: {e}")
        return False

def main():
    """Main setup function."""
    
    print("🚀 Fibonacci Trading Bot PostgreSQL Setup")
    print("=" * 60)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Database creation failed")
        return False
    
    # Step 2: Create config file
    if not create_config_file():
        print("❌ Configuration file creation failed")
        return False
    
    # Step 3: Test integration
    if not test_database_connection():
        print("❌ Database integration test failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 PostgreSQL setup completed successfully!")
    print("\n📋 What was configured:")
    print("   ✅ PostgreSQL database: fibonacci_trading_bot")
    print("   ✅ Configuration file: config.yaml") 
    print("   ✅ Database tables created")
    print("   ✅ Connection tested")
    
    print("\n🌐 Next steps:")
    print("   1. Import your MT4 data:")
    print("      python3 -m src.data.importers.mt4_importer --mt4-path data/data_from_mt4_dj30")
    print("   2. Launch research dashboard:")
    print("      python3 launch_research_dashboard.py")
    print("   3. Open http://localhost:8001")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)