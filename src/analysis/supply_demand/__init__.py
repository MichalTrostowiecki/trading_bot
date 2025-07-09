"""
Supply & Demand Zone Detection System

Professional-grade institutional order flow analysis based on eWavesHarmonics methodology.
Identifies areas where large institutional orders create supply/demand imbalances.
"""

from .base_candle_detector import BaseCandleDetector, BaseCandleRange
from .big_move_detector import BigMoveDetector, BigMove
from .zone_detector import SupplyDemandZoneDetector, SupplyDemandZone
from .zone_state_manager import ZoneStateManager, ZoneStateUpdate, ZoneTestEvent
from .repository import SupplyDemandRepository, ZoneQueryFilter, ZoneHistoryQuery
from .confluence_integration import SupplyDemandConfluence, SDZoneConfluenceScore, SDZoneProximity
# from .rectangle_manager import SupplyDemandRectangleManager  # Module not yet implemented

__version__ = "1.0.0"
__author__ = "Claude AI Agent"

__all__ = [
    "BaseCandleDetector",
    "BaseCandleRange", 
    "BigMoveDetector",
    "BigMove",
    "SupplyDemandZoneDetector",
    "SupplyDemandZone",
    "ZoneStateManager",
    "ZoneStateUpdate",
    "ZoneTestEvent",
    "SupplyDemandRepository",
    "ZoneQueryFilter",
    "ZoneHistoryQuery",
    "SupplyDemandConfluence",
    "SDZoneConfluenceScore",
    "SDZoneProximity",
    # "SupplyDemandRectangleManager"  # Module not yet implemented
]