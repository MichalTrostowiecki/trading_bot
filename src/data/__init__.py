"""
Data Module
MT5 interface, data collection, real-time streaming, and data management components.
"""

from .mt5_interface import (
    MT5Interface,
    MT5ConnectionManager,
    ConnectionStatus,
    TimeFrame,
    ConnectionInfo,
    SymbolInfo,
    connection_manager,
    get_connection,
    initialize_mt5,
    shutdown_mt5
)

from .historical_data import (
    HistoricalDataCollector,
    DataStorage,
    FileStorage,
    DataRequest,
    DataInfo,
    historical_collector,
    collect_historical_data,
    get_historical_data
)

from .realtime_data import (
    RealTimeDataStream,
    MarketDataManager,
    Tick,
    Quote,
    StreamStatus,
    market_data_manager,
    subscribe_to_symbol,
    unsubscribe_from_symbol,
    get_current_quote,
    start_market_data_stream,
    stop_market_data_stream
)

from .validation import (
    DataValidator,
    DataCleaner,
    ValidationResult,
    ValidationIssue,
    ValidationLevel,
    ValidationSeverity,
    data_validator,
    validate_data,
    clean_data
)

__all__ = [
    # MT5 Interface
    "MT5Interface",
    "MT5ConnectionManager", 
    "ConnectionStatus",
    "TimeFrame",
    "ConnectionInfo",
    "SymbolInfo",
    "connection_manager",
    "get_connection",
    "initialize_mt5",
    "shutdown_mt5",
    
    # Historical Data
    "HistoricalDataCollector",
    "DataStorage",
    "FileStorage",
    "DataRequest",
    "DataInfo",
    "historical_collector",
    "collect_historical_data",
    "get_historical_data",
    
    # Real-time Data
    "RealTimeDataStream",
    "MarketDataManager",
    "Tick",
    "Quote",
    "StreamStatus",
    "market_data_manager",
    "subscribe_to_symbol",
    "unsubscribe_from_symbol",
    "get_current_quote",
    "start_market_data_stream",
    "stop_market_data_stream",
    
    # Validation
    "DataValidator",
    "DataCleaner",
    "ValidationResult",
    "ValidationIssue",
    "ValidationLevel",
    "ValidationSeverity",
    "data_validator",
    "validate_data",
    "clean_data"
]