"""
Logging Configuration System
Advanced logging setup using loguru for the trading bot.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from src.utils.config import get_config, LoggingConfig


class LoggingManager:
    """Enhanced logging manager with multiple handlers and formatters."""
    
    def __init__(self):
        self.config: Optional[LoggingConfig] = None
        self.log_dir: Optional[Path] = None
        self.is_configured = False
    
    def setup_logging(self, config: Optional[LoggingConfig] = None) -> None:
        """Setup logging with configuration."""
        if config is None:
            try:
                main_config = get_config()
                self.config = main_config.logging
            except Exception:
                # Fallback to default config
                self.config = LoggingConfig()
        else:
            self.config = config
        
        # Remove default handler
        logger.remove()
        
        # Setup log directory
        self._setup_log_directory()
        
        # Add console handler
        self._add_console_handler()
        
        # Add file handlers
        self._add_file_handlers()
        
        # Add trade-specific handler
        self._add_trade_handler()
        
        # Add error handler
        self._add_error_handler()
        
        self.is_configured = True
        logger.info("Logging system initialized")
    
    def _setup_log_directory(self) -> None:
        """Create log directory structure."""
        log_file_path = Path(self.config.file)
        self.log_dir = log_file_path.parent
        
        # Create log directories
        directories = [
            self.log_dir,
            self.log_dir / "trades",
            self.log_dir / "errors",
            self.log_dir / "performance"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _add_console_handler(self) -> None:
        """Add colorized console handler."""
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=console_format,
            level=self.config.level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    def _add_file_handlers(self) -> None:
        """Add file handlers with rotation."""
        # Main application log
        main_log_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        logger.add(
            self.log_dir / "trading_bot.log",
            format=main_log_format,
            level=self.config.level,
            rotation=self.config.max_size,
            retention=self.config.backup_count,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # Debug log (everything)
        logger.add(
            self.log_dir / "debug.log",
            format=main_log_format,
            level="DEBUG",
            rotation="100 MB",
            retention=3,
            compression="zip",
            filter=lambda record: record["level"].name == "DEBUG"
        )
    
    def _add_trade_handler(self) -> None:
        """Add specialized trade logging handler."""
        trade_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{message}"
        )
        
        logger.add(
            self.log_dir / "trades" / "trades_{time:YYYY-MM-DD}.log",
            format=trade_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            filter=lambda record: "trade" in record["extra"]
        )
    
    def _add_error_handler(self) -> None:
        """Add error-specific handler."""
        error_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}\n"
            "{exception}"
        )
        
        logger.add(
            self.log_dir / "errors" / "errors_{time:YYYY-MM-DD}.log",
            format=error_format,
            level="ERROR",
            rotation="1 day",
            retention="90 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"]
        )
    
    def get_logger(self, name: str) -> logger:
        """Get a named logger instance."""
        if not self.is_configured:
            self.setup_logging()
        
        return logger.bind(name=name)
    
    def log_trade(self, message: str, **kwargs) -> None:
        """Log trade-specific information."""
        logger.bind(trade=True).info(message, **kwargs)
    
    def log_performance(self, metric: str, value: float, **kwargs) -> None:
        """Log performance metrics."""
        logger.bind(performance=True).info(
            f"PERFORMANCE: {metric}={value}",
            **kwargs
        )
    
    def log_market_data(self, symbol: str, action: str, **kwargs) -> None:
        """Log market data operations."""
        logger.bind(market_data=True).debug(
            f"MARKET_DATA: {symbol} - {action}",
            **kwargs
        )
    
    def log_strategy(self, strategy: str, signal: str, **kwargs) -> None:
        """Log strategy signals."""
        logger.bind(strategy=True).info(
            f"STRATEGY: {strategy} - {signal}",
            **kwargs
        )
    
    def log_risk(self, event: str, level: str, **kwargs) -> None:
        """Log risk management events."""
        log_level = getattr(logger, level.lower(), logger.warning)
        logger.bind(risk=True).__getattr__(level.lower())(
            f"RISK: {event}",
            **kwargs
        )


class TradeLogger:
    """Specialized logger for trade operations."""
    
    def __init__(self, logging_manager: LoggingManager):
        self.manager = logging_manager
        self.logger = logging_manager.get_logger("trade")
    
    def order_placed(self, order_id: str, symbol: str, side: str, 
                    quantity: float, price: float) -> None:
        """Log order placement."""
        self.manager.log_trade(
            f"ORDER_PLACED: {order_id} - {side} {quantity} {symbol} @ {price}"
        )
    
    def order_filled(self, order_id: str, fill_price: float, 
                    fill_quantity: float, commission: float) -> None:
        """Log order fill."""
        self.manager.log_trade(
            f"ORDER_FILLED: {order_id} - Filled {fill_quantity} @ {fill_price}, "
            f"Commission: {commission}"
        )
    
    def position_opened(self, position_id: str, symbol: str, side: str,
                       quantity: float, entry_price: float) -> None:
        """Log position opening."""
        self.manager.log_trade(
            f"POSITION_OPENED: {position_id} - {side} {quantity} {symbol} @ {entry_price}"
        )
    
    def position_closed(self, position_id: str, exit_price: float,
                       pnl: float, duration: str) -> None:
        """Log position closing."""
        self.manager.log_trade(
            f"POSITION_CLOSED: {position_id} - Exit @ {exit_price}, "
            f"PnL: {pnl:.2f}, Duration: {duration}"
        )


class PerformanceLogger:
    """Specialized logger for performance metrics."""
    
    def __init__(self, logging_manager: LoggingManager):
        self.manager = logging_manager
        self.logger = logging_manager.get_logger("performance")
    
    def daily_pnl(self, date: str, pnl: float, trades: int) -> None:
        """Log daily P&L."""
        self.manager.log_performance("daily_pnl", pnl, date=date, trades=trades)
    
    def drawdown(self, current_dd: float, max_dd: float) -> None:
        """Log drawdown metrics."""
        self.manager.log_performance("drawdown", current_dd, max_drawdown=max_dd)
    
    def sharpe_ratio(self, period: str, ratio: float) -> None:
        """Log Sharpe ratio."""
        self.manager.log_performance("sharpe_ratio", ratio, period=period)
    
    def win_rate(self, period: str, rate: float, total_trades: int) -> None:
        """Log win rate."""
        self.manager.log_performance("win_rate", rate, period=period, trades=total_trades)


# Global logging manager instance
logging_manager = LoggingManager()

# Convenience functions
def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup global logging configuration."""
    logging_manager.setup_logging(config)

def get_logger(name: str = "trading_bot") -> logger:
    """Get a named logger instance."""
    return logging_manager.get_logger(name)

def get_trade_logger() -> TradeLogger:
    """Get trade logger instance."""
    return TradeLogger(logging_manager)

def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance."""
    return PerformanceLogger(logging_manager)

# Initialize logging if config is available
try:
    setup_logging()
except Exception:
    # Will be setup when config is loaded
    pass