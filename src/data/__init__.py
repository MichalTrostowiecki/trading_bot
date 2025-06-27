"""
Data Module
MT5 interface, data collection, and data management components.
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

__all__ = [
    "MT5Interface",
    "MT5ConnectionManager", 
    "ConnectionStatus",
    "TimeFrame",
    "ConnectionInfo",
    "SymbolInfo",
    "connection_manager",
    "get_connection",
    "initialize_mt5",
    "shutdown_mt5"
]