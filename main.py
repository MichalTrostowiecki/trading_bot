"""
Fibonacci Trading Bot - Main Application
Entry point for the automated trading system with web dashboard.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
import uvicorn

from src.utils.config import ConfigManager, get_config
from src.data.mt5_interface import MT5Interface, initialize_mt5_interface
from src.execution.trading_engine import initialize_trading_engine, get_trading_engine
from src.monitoring.web_dashboard import app as dashboard_app
from src.data.database import initialize_database, get_database_manager
from src.monitoring import get_logger

logger = get_logger("main")


class TradingBotApplication:
    """Main trading bot application orchestrator."""
    
    def __init__(self):
        self.mt5_interface: Optional[MT5Interface] = None
        self.trading_engine = None
        self.database_manager = None
        self.dashboard_server = None
        self.running = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    async def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("Initializing Fibonacci Trading Bot...")
            
            # Load configuration first
            logger.info("Loading configuration...")
            try:
                config_manager = ConfigManager()
                config = config_manager.load_config("development")
                logger.info(f"Configuration loaded for environment: {config.environment}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Creating default configuration...")
                # Create a minimal default config if file doesn't exist
                self._create_default_config()
                config_manager = ConfigManager()
                config = config_manager.load_config("development")
            
            # Initialize database
            logger.info("Initializing database...")
            self.database_manager = initialize_database()
            if not self.database_manager:
                logger.error("Failed to initialize database")
                return False
            
            # Initialize MT5 interface
            logger.info("Initializing MT5 interface...")
            self.mt5_interface = await initialize_mt5_interface()
            if not self.mt5_interface:
                logger.error("Failed to initialize MT5 interface")
                return False
            
            # Test MT5 connection
            if not await self.mt5_interface.connect():
                logger.error("Failed to connect to MT5")
                return False
            
            logger.info("MT5 connection established successfully")
            
            # Initialize trading engine
            logger.info("Initializing trading engine...")
            self.trading_engine = await initialize_trading_engine(self.mt5_interface)
            if not self.trading_engine:
                logger.error("Failed to initialize trading engine")
                return False
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the trading bot application."""
        try:
            if not await self.initialize():
                return False
            
            self.running = True
            
            # Start the web dashboard server
            logger.info("Starting web dashboard...")
            dashboard_task = asyncio.create_task(
                self._start_dashboard_server()
            )
            
            # Start the trading engine (will be controlled via dashboard)
            logger.info("Trading engine ready (not started - use dashboard to control)")
            
            # Log startup completion
            self.database_manager.log_system_event(
                level="INFO",
                component="main",
                message="Trading bot application started successfully",
                details={
                    "dashboard_url": f"http://{config.api.host}:{config.api.port}",
                    "mt5_connected": True,
                    "database_connected": True
                }
            )
            
            logger.info(f"🚀 Fibonacci Trading Bot started successfully!")
            config = get_config()
            logger.info(f"📊 Dashboard available at: http://{config.api.host}:{config.api.port}")
            logger.info(f"🔧 Use the dashboard to control trading operations")
            
            # Wait for shutdown signal
            await dashboard_task
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False
    
    async def _start_dashboard_server(self):
        """Start the web dashboard server."""
        try:
            config = get_config()
            dashboard_config = uvicorn.Config(
                app=dashboard_app,
                host=config.api.host,
                port=config.api.port,
                log_level="info",
                reload=False,
                access_log=True
            )
            
            server = uvicorn.Server(dashboard_config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the application."""
        try:
            logger.info("Shutting down trading bot...")
            self.running = False
            
            # Stop trading engine
            if self.trading_engine:
                logger.info("Stopping trading engine...")
                await self.trading_engine.stop()
            
            # Disconnect MT5
            if self.mt5_interface:
                logger.info("Disconnecting from MT5...")
                await self.mt5_interface.disconnect()
            
            # Close database connection
            if self.database_manager:
                logger.info("Closing database connection...")
                self.database_manager.disconnect()
            
            # Log shutdown
            if self.database_manager:
                self.database_manager.log_system_event(
                    level="INFO",
                    component="main",
                    message="Trading bot application shutdown completed"
                )
            
            logger.info("Shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        
        # Create shutdown task
        asyncio.create_task(self.shutdown())
        
        # Exit after a brief delay to allow cleanup
        asyncio.get_event_loop().call_later(5.0, sys.exit, 0)
    
    def _create_default_config(self):
        """Create a default configuration file."""
        try:
            from pathlib import Path
            try:
                import yaml
            except ImportError:
                logger.error("PyYAML not installed. Installing...")
                import subprocess
                import sys
                subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml>=6.0"], check=True)
                import yaml
            
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            default_config = {
                "environment": "development",
                "mt5": {
                    "server": "Demo-Server",
                    "login": 12345678,
                    "password": "demo_password",
                    "timeout": 10000
                },
                "data": {
                    "symbols": ["EURUSD", "GBPUSD"],
                    "timeframes": ["M1", "M5"],
                    "history_days": 365,
                    "cache_enabled": True,
                    "cache_ttl": 3600
                },
                "trading": {
                    "risk_per_trade": 0.01,
                    "max_positions": 3,
                    "max_daily_loss": 0.05,
                    "fibonacci_levels": {
                        "retracements": [0.236, 0.382, 0.5, 0.618, 0.786],
                        "extensions": [1.0, 1.272, 1.618, 2.0]
                    }
                },
                "ml": {
                    "model_retrain_days": 30,
                    "feature_lookback": 100,
                    "validation_split": 0.2,
                    "random_state": 42
                },
                "logging": {
                    "level": "INFO",
                    "file": "logs/trading_bot.log",
                    "max_size": "100MB",
                    "backup_count": 5
                },
                "database": {
                    "url": "sqlite:///data/trading_bot.db",
                    "echo": False
                },
                "api": {
                    "host": "localhost",
                    "port": 8000,
                    "debug": True
                }
            }
            
            config_file = config_dir / "development.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            logger.info(f"Created default configuration: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            raise


async def main():
    """Main application entry point."""
    try:
        # Print startup banner
        print("\n" + "="*60)
        print("🎯 FIBONACCI TRADING BOT - AI Enhanced")
        print("="*60)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔧 Environment: Initializing...")
        print("📊 Dashboard: http://localhost:8000 (default)")
        print("="*60 + "\n")
        
        # Create and start application
        app = TradingBotApplication()
        success = await app.start()
        
        if not success:
            logger.error("Failed to start trading bot application")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main application: {e}")
        sys.exit(1)


def run_trading_bot():
    """Convenience function to run the trading bot."""
    try:
        # Set up event loop for Windows compatibility
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the main application
        asyncio.run(main())
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_trading_bot()