# Supply & Demand Zone Detection - API Documentation

## Document Information
- **Version**: 1.0
- **Date**: July 6, 2025
- **Author**: Claude AI Agent
- **Status**: Draft
- **Dependencies**: SUPPLY_DEMAND_SYSTEM.md

---

## 1. Core Classes and Interfaces

### 1.1 BaseCandleDetector

```python
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class BaseCandleRange:
    """Represents a range of base candles before a big move"""
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    atr_at_creation: float
    candle_count: int
    consolidation_score: float  # 0.0 to 1.0

class BaseCandleDetector:
    """
    Detects consolidation areas (base candles) that precede significant price moves.
    
    Based on eWavesHarmonics methodology for identifying institutional accumulation zones.
    Performance Target: <20ms per detection cycle
    """
    
    def __init__(
        self,
        consolidation_threshold: float = 0.5,  # ATR percentage
        min_base_candles: int = 2,
        max_base_candles: int = 10,
        body_size_threshold: float = 0.3,      # Body/ATR ratio
        atr_period: int = 14
    ):
        """
        Initialize base candle detector with eWavesHarmonics parameters.
        
        Args:
            consolidation_threshold: Maximum candle range as % of ATR
            min_base_candles: Minimum consecutive consolidation candles
            max_base_candles: Maximum consecutive consolidation candles
            body_size_threshold: Maximum body size as % of ATR
            atr_period: Period for ATR calculation
        """
        self.consolidation_threshold = consolidation_threshold
        self.min_base_candles = min_base_candles
        self.max_base_candles = max_base_candles
        self.body_size_threshold = body_size_threshold
        self.atr_period = atr_period
        self._atr_cache: Optional[pd.Series] = None
    
    def detect_base_candles(
        self, 
        df: pd.DataFrame, 
        start_index: int = 0, 
        end_index: Optional[int] = None
    ) -> List[BaseCandleRange]:
        """
        Detect base candle ranges in OHLC data.
        
        Args:
            df: OHLC DataFrame with columns ['open', 'high', 'low', 'close', 'time']
            start_index: Starting index for detection
            end_index: Ending index for detection (None = end of data)
            
        Returns:
            List of BaseCandleRange objects representing consolidation areas
            
        Raises:
            ValueError: If data is insufficient or invalid
            
        Performance: <20ms for 1000 bars
        """
        
    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Average True Range for volatility baseline.
        
        Args:
            df: OHLC DataFrame
            
        Returns:
            Series with ATR values
        """
        
    def _is_consolidation_candle(
        self, 
        candle: pd.Series, 
        atr_value: float
    ) -> bool:
        """
        Determine if a single candle qualifies as consolidation.
        
        Args:
            candle: Single candle OHLC data
            atr_value: ATR value for size comparison
            
        Returns:
            True if candle meets consolidation criteria
        """
        
    def _validate_base_range(self, candles: pd.DataFrame) -> float:
        """
        Validate and score quality of base candle range.
        
        Args:
            candles: DataFrame of potential base candles
            
        Returns:
            Consolidation score (0.0 to 1.0)
        """
```

### 1.2 BigMoveDetector

```python
@dataclass
class BigMove:
    """Represents a significant price movement after base candles"""
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    direction: str  # 'bullish' or 'bearish'
    magnitude: float  # ATR multiples
    momentum_score: float  # 0.0 to 1.0
    breakout_level: float
    volume_confirmation: bool

class BigMoveDetector:
    """
    Detects significant price movements that follow base candle consolidation.
    
    Identifies institutional order execution through momentum and volume analysis.
    Performance Target: <30ms per detection cycle
    """
    
    def __init__(
        self,
        move_threshold: float = 2.0,           # ATR multiple
        min_move_candles: int = 3,             # Minimum move duration
        momentum_threshold: float = 0.6,       # Momentum quality
        volume_multiplier: float = 1.5,        # Volume spike threshold
        breakout_confirmation: bool = True      # Require level break
    ):
        """
        Initialize big move detector parameters.
        
        Args:
            move_threshold: Minimum move size as ATR multiple
            min_move_candles: Minimum candles for valid move
            momentum_threshold: Minimum momentum score (0.0-1.0)
            volume_multiplier: Volume spike threshold vs average
            breakout_confirmation: Require break of previous levels
        """
        
    def detect_big_moves(
        self,
        df: pd.DataFrame,
        base_ranges: List[BaseCandleRange],
        fractal_levels: Optional[List[float]] = None
    ) -> List[BigMove]:
        """
        Detect significant moves following base candle ranges.
        
        Args:
            df: OHLC DataFrame with volume data
            base_ranges: List of detected base candle ranges
            fractal_levels: Optional fractal levels for breakout validation
            
        Returns:
            List of BigMove objects representing institutional moves
            
        Performance: <30ms for 1000 bars with 50 base ranges
        """
        
    def _calculate_move_magnitude(
        self, 
        df: pd.DataFrame, 
        start_index: int, 
        end_index: int,
        base_range: BaseCandleRange
    ) -> float:
        """
        Calculate move magnitude in ATR multiples.
        
        Args:
            df: OHLC DataFrame
            start_index: Move start index
            end_index: Move end index
            base_range: Reference base candle range
            
        Returns:
            Move magnitude as ATR multiple
        """
        
    def _calculate_momentum_score(
        self, 
        df: pd.DataFrame, 
        start_index: int, 
        end_index: int
    ) -> float:
        """
        Calculate momentum quality score (0.0 to 1.0).
        
        Measures consistency and strength of directional movement.
        
        Args:
            df: OHLC DataFrame
            start_index: Move start index
            end_index: Move end index
            
        Returns:
            Momentum score (0.0 = weak, 1.0 = perfect momentum)
        """
        
    def _validate_breakout(
        self, 
        move: BigMove, 
        fractal_levels: List[float]
    ) -> bool:
        """
        Validate move breaks through previous significant levels.
        
        Args:
            move: BigMove object to validate
            fractal_levels: List of fractal high/low levels
            
        Returns:
            True if move represents valid breakout
        """
```

### 1.3 SupplyDemandZoneDetector

```python
@dataclass
class SupplyDemandZone:
    """
    Represents a supply or demand zone with complete metadata.
    
    Based on eWavesHarmonics zone identification methodology.
    """
    id: Optional[int]  # Database ID (None for new zones)
    symbol: str
    timeframe: str
    zone_type: str  # 'supply', 'demand', 'continuation'
    
    # Zone boundaries
    top_price: float
    bottom_price: float
    left_time: datetime
    right_time: datetime
    
    # Zone metadata
    strength_score: float  # 0.0 to 1.0
    test_count: int
    success_count: int
    status: str  # 'active', 'tested', 'broken', 'flipped'
    
    # Creation context
    base_range: BaseCandleRange
    big_move: BigMove
    atr_at_creation: float
    volume_at_creation: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def contains_price(self, price: float) -> bool:
        """Check if price is within zone boundaries"""
        return self.bottom_price <= price <= self.top_price
    
    def distance_from_price(self, price: float) -> float:
        """Calculate distance from price to nearest zone boundary"""
        if self.contains_price(price):
            return 0.0
        elif price < self.bottom_price:
            return self.bottom_price - price
        else:
            return price - self.top_price
    
    @property
    def height(self) -> float:
        """Zone height in price units"""
        return self.top_price - self.bottom_price
    
    @property
    def center(self) -> float:
        """Zone center price"""
        return (self.top_price + self.bottom_price) / 2.0
    
    @property
    def age_hours(self) -> float:
        """Zone age in hours"""
        return (datetime.now() - self.created_at).total_seconds() / 3600

class SupplyDemandZoneDetector:
    """
    Main class for detecting supply and demand zones using eWavesHarmonics methodology.
    
    Combines base candle detection, big move analysis, and zone classification
    to identify institutional order flow areas.
    
    Performance Target: <50ms per complete detection cycle
    """
    
    def __init__(
        self,
        base_detector: BaseCandleDetector,
        move_detector: BigMoveDetector,
        max_zones_per_timeframe: int = 100,
        zone_expiry_hours: int = 168,  # 1 week
        overlap_tolerance: float = 0.1  # 10% overlap allowed
    ):
        """
        Initialize supply/demand zone detector.
        
        Args:
            base_detector: Configured BaseCandleDetector instance
            move_detector: Configured BigMoveDetector instance
            max_zones_per_timeframe: Maximum zones to maintain
            zone_expiry_hours: Hours before zone expires
            overlap_tolerance: Allowed zone overlap percentage
        """
        self.base_detector = base_detector
        self.move_detector = move_detector
        self.max_zones_per_timeframe = max_zones_per_timeframe
        self.zone_expiry_hours = zone_expiry_hours
        self.overlap_tolerance = overlap_tolerance
        self._zone_cache: List[SupplyDemandZone] = []
    
    def detect_zones(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        fractal_levels: Optional[List[float]] = None,
        existing_zones: Optional[List[SupplyDemandZone]] = None
    ) -> List[SupplyDemandZone]:
        """
        Detect all supply and demand zones in price data.
        
        Args:
            df: OHLC DataFrame with required columns
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'M1', 'H1')
            fractal_levels: Optional fractal levels for context
            existing_zones: Optional existing zones to update
            
        Returns:
            List of detected SupplyDemandZone objects
            
        Raises:
            ValueError: If data is insufficient or invalid
            
        Performance: <50ms for 1000 bars
        """
        
    def _classify_zone_type(
        self, 
        base_range: BaseCandleRange, 
        big_move: BigMove
    ) -> str:
        """
        Classify zone as supply, demand, or continuation.
        
        Args:
            base_range: Base candle consolidation range
            big_move: Following big move data
            
        Returns:
            Zone type: 'supply', 'demand', or 'continuation'
        """
        
    def _calculate_zone_boundaries(
        self, 
        df: pd.DataFrame,
        base_range: BaseCandleRange, 
        zone_type: str
    ) -> Tuple[float, float]:
        """
        Calculate precise zone boundaries using eWavesHarmonics rules.
        
        For demand zones: 
        - Top: Highest high of base candles
        - Bottom: Lowest open of red candles in base range
        
        For supply zones:
        - Top: Highest open of green candles in base range  
        - Bottom: Lowest low of base candles
        
        Args:
            df: OHLC DataFrame
            base_range: Base candle range data
            zone_type: 'supply' or 'demand'
            
        Returns:
            Tuple of (top_price, bottom_price)
        """
        
    def _calculate_zone_strength(
        self, 
        zone: SupplyDemandZone,
        df: pd.DataFrame
    ) -> float:
        """
        Calculate zone strength score (0.0 to 1.0).
        
        Factors:
        - Volume at creation (40%)
        - Move magnitude (30%)
        - Base candle quality (20%)
        - Breakout confirmation (10%)
        
        Args:
            zone: SupplyDemandZone object
            df: OHLC DataFrame with volume
            
        Returns:
            Strength score (0.0 to 1.0)
        """
        
    def _resolve_overlapping_zones(
        self, 
        zones: List[SupplyDemandZone]
    ) -> List[SupplyDemandZone]:
        """
        Resolve overlapping zones by merging or prioritizing.
        
        Args:
            zones: List of potentially overlapping zones
            
        Returns:
            List of resolved zones without conflicts
        """
```

### 1.4 ZoneStateManager

```python
@dataclass
class ZoneTest:
    """Represents a test of a supply/demand zone"""
    zone_id: int
    test_time: datetime
    test_price: float
    test_type: str  # 'touch', 'penetration', 'break'
    rejection_strength: float  # 0.0 to 1.0
    outcome: str  # 'bounce', 'break', 'flip'

@dataclass
class ZoneFlip:
    """Represents a zone flip from supply to demand or vice versa"""
    original_zone_id: int
    new_zone_id: int
    flip_time: datetime
    flip_price: float
    confirmation_bars: int

class ZoneStateManager:
    """
    Manages supply/demand zone lifecycle and state transitions.
    
    Tracks zone tests, breaks, flips, and status updates in real-time.
    Performance Target: <20ms per state update
    """
    
    def __init__(
        self,
        test_proximity_pips: float = 2.0,      # Pips for zone test
        break_confirmation_bars: int = 3,       # Bars to confirm break
        flip_confirmation_bars: int = 5,        # Bars to confirm flip
        rejection_threshold: float = 0.3        # Minimum rejection strength
    ):
        """
        Initialize zone state manager.
        
        Args:
            test_proximity_pips: Distance considered as zone test
            break_confirmation_bars: Bars needed to confirm zone break
            flip_confirmation_bars: Bars needed to confirm zone flip
            rejection_threshold: Minimum rejection strength for bounce
        """
        
    def update_zone_states(
        self,
        zones: List[SupplyDemandZone],
        df: pd.DataFrame,
        current_index: int
    ) -> Tuple[List[SupplyDemandZone], List[ZoneTest], List[ZoneFlip]]:
        """
        Update all zone states based on current price action.
        
        Args:
            zones: List of active zones to update
            df: OHLC DataFrame
            current_index: Current bar index
            
        Returns:
            Tuple of (updated_zones, new_tests, new_flips)
            
        Performance: <20ms for 100 zones
        """
        
    def detect_zone_tests(
        self,
        zone: SupplyDemandZone,
        df: pd.DataFrame,
        current_index: int
    ) -> Optional[ZoneTest]:
        """
        Detect if current price action tests a zone.
        
        Args:
            zone: Zone to test
            df: OHLC DataFrame
            current_index: Current bar index
            
        Returns:
            ZoneTest object if test detected, None otherwise
        """
        
    def detect_zone_break(
        self,
        zone: SupplyDemandZone,
        df: pd.DataFrame,
        current_index: int
    ) -> bool:
        """
        Detect if zone has been broken with confirmation.
        
        Args:
            zone: Zone to check for break
            df: OHLC DataFrame
            current_index: Current bar index
            
        Returns:
            True if zone is broken and confirmed
        """
        
    def detect_zone_flip(
        self,
        broken_zone: SupplyDemandZone,
        df: pd.DataFrame,
        current_index: int
    ) -> Optional[Tuple[SupplyDemandZone, ZoneFlip]]:
        """
        Detect zone flip when broken zone becomes opposite type.
        
        Args:
            broken_zone: Zone that was broken
            df: OHLC DataFrame
            current_index: Current bar index
            
        Returns:
            Tuple of (new_flipped_zone, flip_record) if flip detected
        """
        
    def _calculate_rejection_strength(
        self,
        df: pd.DataFrame,
        test_index: int,
        zone: SupplyDemandZone
    ) -> float:
        """
        Calculate strength of price rejection at zone boundary.
        
        Measures wick length, subsequent momentum, and volume.
        
        Args:
            df: OHLC DataFrame
            test_index: Index where test occurred
            zone: Zone being tested
            
        Returns:
            Rejection strength (0.0 to 1.0)
        """
```

### 1.5 SupplyDemandRectangleManager

```python
from typing import Dict, Any

@dataclass
class RectangleStyle:
    """Style configuration for zone rectangles"""
    fill_color: str
    border_color: str
    transparency: int  # 0-100
    border_width: int
    label_text: str
    label_position: str  # 'top-left', 'bottom-left', 'center'

class SupplyDemandRectangleManager:
    """
    Manages TradingView rectangle drawing for supply/demand zones.
    
    Handles zone visualization, styling, and real-time updates.
    Performance Target: <30ms per chart update
    """
    
    def __init__(self, chart_instance):
        """
        Initialize rectangle manager with TradingView chart.
        
        Args:
            chart_instance: TradingView chart object
        """
        self.chart = chart_instance
        self.rectangles: Dict[int, Any] = {}  # zone_id -> rectangle
        self.labels: Dict[int, Any] = {}      # zone_id -> label
        self.styles = self._initialize_styles()
    
    def _initialize_styles(self) -> Dict[str, RectangleStyle]:
        """Initialize default rectangle styles for each zone type"""
        return {
            'supply': RectangleStyle(
                fill_color='#FF4444',
                border_color='#CC0000',
                transparency=80,
                border_width=2,
                label_text='S',
                label_position='top-left'
            ),
            'demand': RectangleStyle(
                fill_color='#44FF44',
                border_color='#00CC00',
                transparency=80,
                border_width=2,
                label_text='D',
                label_position='bottom-left'
            ),
            'continuation': RectangleStyle(
                fill_color='#4444FF',
                border_color='#0000CC',
                transparency=80,
                border_width=2,
                label_text='C',
                label_position='center'
            ),
            'flipped': RectangleStyle(
                fill_color='#FF8844',
                border_color='#CC4400',
                transparency=80,
                border_width=2,
                label_text='F',
                label_position='center'
            )
        }
    
    def draw_zone(self, zone: SupplyDemandZone) -> bool:
        """
        Draw supply/demand zone rectangle on chart.
        
        Args:
            zone: SupplyDemandZone to visualize
            
        Returns:
            True if successfully drawn
            
        Performance: <5ms per zone
        """
        
    def update_zone(self, zone: SupplyDemandZone) -> bool:
        """
        Update existing zone rectangle (color, status, etc.).
        
        Args:
            zone: Updated SupplyDemandZone
            
        Returns:
            True if successfully updated
        """
        
    def remove_zone(self, zone_id: int) -> bool:
        """
        Remove zone rectangle from chart.
        
        Args:
            zone_id: ID of zone to remove
            
        Returns:
            True if successfully removed
        """
        
    def update_all_zones(self, zones: List[SupplyDemandZone]) -> int:
        """
        Update all zone rectangles efficiently.
        
        Uses change detection to minimize unnecessary updates.
        
        Args:
            zones: Complete list of current zones
            
        Returns:
            Number of zones actually updated
            
        Performance: <30ms for 100 zones
        """
        
    def _get_zone_style(self, zone: SupplyDemandZone) -> RectangleStyle:
        """
        Get appropriate style for zone based on type and status.
        
        Args:
            zone: SupplyDemandZone to style
            
        Returns:
            RectangleStyle configuration
        """
        
    def _adjust_style_for_status(
        self, 
        style: RectangleStyle, 
        zone: SupplyDemandZone
    ) -> RectangleStyle:
        """
        Adjust style based on zone status (active, tested, broken).
        
        Args:
            style: Base rectangle style
            zone: Zone with current status
            
        Returns:
            Modified style for current status
        """
```

---

## 2. Confluence Integration Classes

### 2.1 SupplyDemandConfluence

```python
from src.analysis.confluence_engine import ConfluenceFactorType

class SupplyDemandConfluence:
    """
    Integrates supply/demand zones with existing confluence system.
    
    Provides scoring algorithm for Fibonacci + S&D zone confluence.
    Performance Target: <20ms per confluence calculation
    """
    
    def __init__(
        self,
        zone_detector: SupplyDemandZoneDetector,
        max_distance_pips: float = 5.0,        # Max distance for confluence
        fibonacci_weight: float = 0.6,         # Fibonacci importance
        zone_weight: float = 0.4               # Zone importance
    ):
        """
        Initialize S&D confluence calculator.
        
        Args:
            zone_detector: Configured SupplyDemandZoneDetector
            max_distance_pips: Maximum distance for confluence scoring
            fibonacci_weight: Weight for Fibonacci levels (0.0-1.0)
            zone_weight: Weight for S&D zones (0.0-1.0)
        """
        
    def calculate_confluence_score(
        self,
        price: float,
        zones: List[SupplyDemandZone],
        fibonacci_levels: List[float],
        symbol: str
    ) -> float:
        """
        Calculate confluence score for price vs S&D zones and Fibonacci.
        
        Scoring Algorithm:
        1. Find zones within max_distance_pips of price
        2. Find Fibonacci levels within max_distance_pips of price  
        3. Calculate combined proximity and strength score
        4. Apply weighting factors
        5. Normalize to 0.0-1.0 range
        
        Args:
            price: Current price level
            zones: List of active S&D zones
            fibonacci_levels: List of Fibonacci retracement levels
            symbol: Trading symbol for pip calculation
            
        Returns:
            Confluence score (0.0 to 1.0)
            
        Performance: <20ms per calculation
        """
        
    def get_confluence_factors(
        self,
        price: float,
        zones: List[SupplyDemandZone],
        fibonacci_levels: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Get detailed confluence factor breakdown for analysis.
        
        Args:
            price: Current price level
            zones: List of active S&D zones
            fibonacci_levels: List of Fibonacci levels
            
        Returns:
            List of confluence factor details with scores and metadata
        """
        
    def _calculate_zone_score(
        self, 
        price: float, 
        zone: SupplyDemandZone
    ) -> float:
        """
        Calculate individual zone confluence score.
        
        Factors:
        - Distance from zone boundary (closer = higher)
        - Zone strength rating
        - Zone freshness (fewer tests = higher)
        - Zone type alignment with price action
        
        Args:
            price: Current price level
            zone: SupplyDemandZone to score
            
        Returns:
            Zone score (0.0 to 1.0)
        """
        
    def _calculate_fibonacci_score(
        self, 
        price: float, 
        fibonacci_levels: List[float]
    ) -> float:
        """
        Calculate Fibonacci level confluence score.
        
        Args:
            price: Current price level
            fibonacci_levels: List of Fibonacci levels
            
        Returns:
            Fibonacci score (0.0 to 1.0)
        """
```

---

## 3. Database Integration Classes

### 3.1 SupplyDemandRepository

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg

class SupplyDemandRepository:
    """
    Database repository for supply/demand zone persistence.
    
    Handles CRUD operations for zones, tests, and flips.
    Performance Target: <10ms per database operation
    """
    
    def __init__(self, database_url: str):
        """
        Initialize repository with database connection.
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self._connection_pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        
    async def save_zone(self, zone: SupplyDemandZone) -> int:
        """
        Save supply/demand zone to database.
        
        Args:
            zone: SupplyDemandZone to save
            
        Returns:
            Database ID of saved zone
            
        Performance: <10ms per save
        """
        
    async def update_zone(self, zone: SupplyDemandZone) -> bool:
        """
        Update existing zone in database.
        
        Args:
            zone: SupplyDemandZone with updates
            
        Returns:
            True if successfully updated
        """
        
    async def get_zones(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        status_filter: Optional[List[str]] = None
    ) -> List[SupplyDemandZone]:
        """
        Retrieve zones from database with filters.
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            start_time: Start of time range
            end_time: End of time range
            status_filter: Optional list of statuses to include
            
        Returns:
            List of matching SupplyDemandZone objects
            
        Performance: <10ms per query
        """
        
    async def save_zone_test(self, test: ZoneTest) -> int:
        """
        Save zone test record to database.
        
        Args:
            test: ZoneTest to save
            
        Returns:
            Database ID of saved test
        """
        
    async def save_zone_flip(self, flip: ZoneFlip) -> int:
        """
        Save zone flip record to database.
        
        Args:
            flip: ZoneFlip to save
            
        Returns:
            Database ID of saved flip
        """
        
    async def get_zone_statistics(
        self,
        symbol: str,
        timeframe: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get zone performance statistics.
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with zone performance metrics
        """
        
    async def cleanup_expired_zones(self, hours_back: int = 168) -> int:
        """
        Remove zones older than specified hours.
        
        Args:
            hours_back: Hours threshold for cleanup
            
        Returns:
            Number of zones removed
        """
```

---

## 4. REST API Endpoints

### 4.1 Zone Detection Endpoints

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/supply-demand", tags=["supply-demand"])

class ZoneDetectionRequest(BaseModel):
    """Request model for zone detection"""
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime
    include_fibonacci: Optional[bool] = True
    include_fractals: Optional[bool] = True

class ZoneResponse(BaseModel):
    """Response model for zone data"""
    id: Optional[int]
    symbol: str
    timeframe: str
    zone_type: str
    top_price: float
    bottom_price: float
    left_time: datetime
    right_time: datetime
    strength_score: float
    test_count: int
    status: str
    created_at: datetime

@router.post("/zones/detect", response_model=List[ZoneResponse])
async def detect_zones(
    request: ZoneDetectionRequest,
    detector: SupplyDemandZoneDetector = Depends(get_zone_detector)
):
    """
    Detect supply/demand zones for given symbol and timeframe.
    
    Args:
        request: Zone detection parameters
        detector: Injected zone detector instance
        
    Returns:
        List of detected zones
        
    Raises:
        HTTPException: If detection fails
        
    Performance: <100ms for 1000 bars
    """

@router.get("/zones/{symbol}/{timeframe}", response_model=List[ZoneResponse])
async def get_zones(
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    status: Optional[str] = None,
    repository: SupplyDemandRepository = Depends(get_repository)
):
    """
    Retrieve existing zones from database.
    
    Args:
        symbol: Trading symbol
        timeframe: Chart timeframe  
        start_time: Start of time range
        end_time: End of time range
        status: Optional status filter
        repository: Injected repository instance
        
    Returns:
        List of zones matching criteria
    """

@router.get("/zones/{zone_id}/tests")
async def get_zone_tests(
    zone_id: int,
    repository: SupplyDemandRepository = Depends(get_repository)
):
    """
    Get all tests for a specific zone.
    
    Args:
        zone_id: Zone database ID
        repository: Injected repository instance
        
    Returns:
        List of zone tests
    """

@router.get("/zones/statistics/{symbol}/{timeframe}")
async def get_zone_statistics(
    symbol: str,
    timeframe: str,
    days_back: int = 30,
    repository: SupplyDemandRepository = Depends(get_repository)
):
    """
    Get zone performance statistics.
    
    Args:
        symbol: Trading symbol
        timeframe: Chart timeframe
        days_back: Analysis period in days
        repository: Injected repository instance
        
    Returns:
        Zone performance metrics
    """
```

### 4.2 Confluence Integration Endpoints

```python
class ConfluenceRequest(BaseModel):
    """Request model for confluence calculation"""
    symbol: str
    timeframe: str
    price: float
    fibonacci_levels: List[float]
    include_zones: Optional[bool] = True

class ConfluenceResponse(BaseModel):
    """Response model for confluence data"""
    total_score: float
    fibonacci_score: float
    zone_score: float
    factors: List[Dict[str, Any]]

@router.post("/confluence/calculate", response_model=ConfluenceResponse)
async def calculate_confluence(
    request: ConfluenceRequest,
    confluence_calc: SupplyDemandConfluence = Depends(get_confluence_calculator)
):
    """
    Calculate confluence score for price level.
    
    Args:
        request: Confluence calculation parameters
        confluence_calc: Injected confluence calculator
        
    Returns:
        Detailed confluence breakdown
        
    Performance: <20ms per calculation
    """

@router.get("/confluence/zones-near-price/{symbol}/{timeframe}/{price}")
async def get_zones_near_price(
    symbol: str,
    timeframe: str,
    price: float,
    max_distance_pips: float = 5.0,
    repository: SupplyDemandRepository = Depends(get_repository)
):
    """
    Get zones near specific price level.
    
    Args:
        symbol: Trading symbol
        timeframe: Chart timeframe
        price: Price level to check
        max_distance_pips: Maximum distance threshold
        repository: Injected repository instance
        
    Returns:
        List of nearby zones with distances
    """
```

---

## 5. Performance Monitoring Classes

### 5.1 PerformanceMonitor

```python
import time
from contextlib import contextmanager
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerformanceMetric:
    """Performance measurement data"""
    operation: str
    duration_ms: float
    timestamp: datetime
    metadata: Dict[str, Any]

class PerformanceMonitor:
    """
    Monitors and tracks performance of S&D zone operations.
    
    Ensures system maintains <100ms additional overhead target.
    """
    
    def __init__(self, max_metrics: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum metrics to keep in memory
        """
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics = max_metrics
        self.thresholds = {
            'zone_detection': 50.0,      # ms
            'rectangle_drawing': 30.0,   # ms
            'confluence_calc': 20.0,     # ms
            'database_query': 10.0       # ms
        }
    
    @contextmanager
    def measure(self, operation: str, **metadata):
        """
        Context manager for measuring operation performance.
        
        Args:
            operation: Name of operation being measured
            **metadata: Additional metadata to store
            
        Usage:
            with monitor.measure('zone_detection', symbol='EURUSD'):
                # Operation code here
                pass
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.record_metric(operation, duration_ms, metadata)
    
    def record_metric(
        self, 
        operation: str, 
        duration_ms: float, 
        metadata: Dict[str, Any]
    ):
        """
        Record performance metric.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            metadata: Additional context data
        """
        
    def get_performance_summary(self, hours_back: int = 1) -> Dict[str, Any]:
        """
        Get performance summary for recent operations.
        
        Args:
            hours_back: Hours of data to analyze
            
        Returns:
            Performance summary with averages and violations
        """
        
    def check_threshold_violations(self) -> List[PerformanceMetric]:
        """
        Check for recent threshold violations.
        
        Returns:
            List of metrics that exceeded thresholds
        """
```

---

## 6. Configuration Classes

### 6.1 SupplyDemandConfig

```python
from pydantic import BaseSettings, Field
from typing import Dict, Any

class SupplyDemandConfig(BaseSettings):
    """
    Configuration settings for supply/demand zone system.
    
    Supports environment variable overrides with SD_ prefix.
    """
    
    # Base Candle Detection
    consolidation_threshold: float = Field(0.5, description="ATR percentage for consolidation")
    min_base_candles: int = Field(2, description="Minimum base candles")
    max_base_candles: int = Field(10, description="Maximum base candles")
    body_size_threshold: float = Field(0.3, description="Body size threshold")
    atr_period: int = Field(14, description="ATR calculation period")
    
    # Big Move Detection
    move_threshold: float = Field(2.0, description="ATR multiple for big moves")
    min_move_candles: int = Field(3, description="Minimum move candles")
    momentum_threshold: float = Field(0.6, description="Momentum quality threshold")
    volume_multiplier: float = Field(1.5, description="Volume spike multiplier")
    breakout_confirmation: bool = Field(True, description="Require breakout confirmation")
    
    # Zone Management
    max_zones_per_timeframe: int = Field(100, description="Maximum zones per timeframe")
    zone_expiry_hours: int = Field(168, description="Zone expiry in hours")
    overlap_tolerance: float = Field(0.1, description="Zone overlap tolerance")
    
    # State Management
    test_proximity_pips: float = Field(2.0, description="Pips for zone test detection")
    break_confirmation_bars: int = Field(3, description="Bars to confirm break")
    flip_confirmation_bars: int = Field(5, description="Bars to confirm flip")
    rejection_threshold: float = Field(0.3, description="Minimum rejection strength")
    
    # Confluence Settings
    max_distance_pips: float = Field(5.0, description="Max distance for confluence")
    fibonacci_weight: float = Field(0.6, description="Fibonacci importance weight")
    zone_weight: float = Field(0.4, description="Zone importance weight")
    
    # Visual Settings
    zone_colors: Dict[str, str] = Field(
        default={
            'supply': '#FF4444',
            'demand': '#44FF44',
            'continuation': '#4444FF',
            'flipped': '#FF8844'
        },
        description="Zone rectangle colors"
    )
    default_transparency: int = Field(80, description="Default rectangle transparency")
    
    # Performance Settings
    performance_thresholds: Dict[str, float] = Field(
        default={
            'zone_detection': 50.0,
            'rectangle_drawing': 30.0,
            'confluence_calc': 20.0,
            'database_query': 10.0
        },
        description="Performance thresholds in milliseconds"
    )
    
    # Database Settings
    database_url: str = Field(..., description="PostgreSQL connection string")
    connection_pool_size: int = Field(10, description="Database connection pool size")
    query_timeout: int = Field(30, description="Database query timeout in seconds")
    
    class Config:
        env_prefix = "SD_"
        case_sensitive = False
```

---

## 7. Exception Classes

### 7.1 Supply Demand Exceptions

```python
class SupplyDemandError(Exception):
    """Base exception for supply/demand zone system"""
    pass

class ZoneDetectionError(SupplyDemandError):
    """Raised when zone detection fails"""
    pass

class InvalidZoneDataError(SupplyDemandError):
    """Raised when zone data is invalid"""
    pass

class InsufficientDataError(SupplyDemandError):
    """Raised when insufficient data for analysis"""
    pass

class PerformanceThresholdError(SupplyDemandError):
    """Raised when performance thresholds are exceeded"""
    pass

class DatabaseOperationError(SupplyDemandError):
    """Raised when database operations fail"""
    pass

class VisualizationError(SupplyDemandError):
    """Raised when chart visualization fails"""
    pass
```

---

## 8. Utility Functions

### 8.1 Zone Utilities

```python
def calculate_pip_value(symbol: str, price: float) -> float:
    """
    Calculate pip value for given symbol and price.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        price: Current price level
        
    Returns:
        Pip value in price units
    """

def price_to_pips(price_diff: float, symbol: str) -> float:
    """
    Convert price difference to pips for given symbol.
    
    Args:
        price_diff: Price difference
        symbol: Trading symbol
        
    Returns:
        Difference in pips
    """

def pips_to_price(pips: float, symbol: str) -> float:
    """
    Convert pips to price difference for given symbol.
    
    Args:
        pips: Pip difference
        symbol: Trading symbol
        
    Returns:
        Price difference
    """

def validate_zone_boundaries(
    top: float, 
    bottom: float, 
    left_time: datetime, 
    right_time: datetime
) -> bool:
    """
    Validate zone boundary data.
    
    Args:
        top: Top price boundary
        bottom: Bottom price boundary
        left_time: Left time boundary
        right_time: Right time boundary
        
    Returns:
        True if boundaries are valid
        
    Raises:
        InvalidZoneDataError: If boundaries are invalid
    """

def merge_overlapping_zones(
    zone1: SupplyDemandZone, 
    zone2: SupplyDemandZone
) -> SupplyDemandZone:
    """
    Merge two overlapping zones into single zone.
    
    Args:
        zone1: First zone to merge
        zone2: Second zone to merge
        
    Returns:
        Merged SupplyDemandZone
        
    Raises:
        InvalidZoneDataError: If zones cannot be merged
    """
```

---

## 9. Type Definitions

### 9.1 Type Aliases

```python
from typing import TypeAlias, Union, Literal

# Zone type definitions
ZoneType: TypeAlias = Literal['supply', 'demand', 'continuation']
ZoneStatus: TypeAlias = Literal['active', 'tested', 'broken', 'flipped']
TestType: TypeAlias = Literal['touch', 'penetration', 'break']
TestOutcome: TypeAlias = Literal['bounce', 'break', 'flip']

# Price and time types
Price: TypeAlias = float
Pips: TypeAlias = float
Timestamp: TypeAlias = datetime
BarIndex: TypeAlias = int

# Configuration types
SymbolStr: TypeAlias = str  # e.g., 'EURUSD', 'GBPUSD'
TimeframeStr: TypeAlias = str  # e.g., 'M1', 'M5', 'H1'
```

---

## 10. Usage Examples

### 10.1 Basic Zone Detection

```python
# Initialize components
config = SupplyDemandConfig()
base_detector = BaseCandleDetector(
    consolidation_threshold=config.consolidation_threshold,
    min_base_candles=config.min_base_candles,
    max_base_candles=config.max_base_candles
)
move_detector = BigMoveDetector(
    move_threshold=config.move_threshold,
    min_move_candles=config.min_move_candles
)
zone_detector = SupplyDemandZoneDetector(
    base_detector=base_detector,
    move_detector=move_detector
)

# Detect zones
zones = zone_detector.detect_zones(
    df=ohlc_data,
    symbol='EURUSD',
    timeframe='M1'
)

print(f"Detected {len(zones)} supply/demand zones")
```

### 10.2 Confluence Calculation

```python
# Initialize confluence calculator
confluence_calc = SupplyDemandConfluence(
    zone_detector=zone_detector,
    max_distance_pips=5.0
)

# Calculate confluence
current_price = 1.0850
fibonacci_levels = [1.0832, 1.0845, 1.0858]  # 38.2%, 50%, 61.8%

confluence_score = confluence_calc.calculate_confluence_score(
    price=current_price,
    zones=zones,
    fibonacci_levels=fibonacci_levels,
    symbol='EURUSD'
)

print(f"Confluence score: {confluence_score:.3f}")
```

### 10.3 Zone Visualization

```python
# Initialize rectangle manager (in frontend)
rect_manager = SupplyDemandRectangleManager(chart_instance)

# Draw all zones
for zone in zones:
    rect_manager.draw_zone(zone)

# Update zone states
state_manager = ZoneStateManager()
updated_zones, tests, flips = state_manager.update_zone_states(
    zones=zones,
    df=ohlc_data,
    current_index=len(ohlc_data) - 1
)

# Update visualizations
rect_manager.update_all_zones(updated_zones)
```

---

**Document Status**: Draft - Ready for Test Specifications
**Next Phase**: Comprehensive Test Documentation
**Dependencies**: Technical Specification (SUPPLY_DEMAND_SYSTEM.md)
**Performance Targets**: All API methods must meet specified timing requirements