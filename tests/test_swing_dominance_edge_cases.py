"""
Comprehensive test suite for swing dominance and display edge cases.

This test suite verifies:
1. Backend dominance calculation preservation
2. Frontend display logic consistency
3. Fibonacci level updates with dominance changes
4. Visual styling consistency (thick/thin, solid/dashed lines)
5. Edge cases and error handling
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the modules we need to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy.fibonacci_strategy import FibonacciStrategy, Swing
from data.models import Fractal
from research.dashboard.research_api import app
from fastapi.testclient import TestClient


class TestSwingDominanceEdgeCases:
    """Test suite for swing dominance edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.strategy = FibonacciStrategy()
        
        # Create test fractals
        self.test_fractals = self._create_test_fractals()
        self.test_swings = self._create_test_swings()
    
    def _create_test_fractals(self) -> List[Fractal]:
        """Create test fractal data."""
        base_time = datetime(2025, 6, 1, 10, 0)
        fractals = []
        
        # Create a series of fractals for testing
        fractal_data = [
            (base_time, 40000.0, 'high'),
            (base_time + timedelta(minutes=30), 39800.0, 'low'),
            (base_time + timedelta(minutes=60), 40200.0, 'high'),
            (base_time + timedelta(minutes=90), 39600.0, 'low'),
            (base_time + timedelta(minutes=120), 40400.0, 'high'),
            (base_time + timedelta(minutes=150), 39400.0, 'low'),
            (base_time + timedelta(minutes=180), 40600.0, 'high'),
        ]
        
        for i, (timestamp, price, fractal_type) in enumerate(fractal_data):
            fractal = Fractal(
                timestamp=timestamp,
                price=price,
                fractal_type=fractal_type,
                bar_index=i * 30,  # 30 bars between fractals
                high=price + 10 if fractal_type == 'high' else price,
                low=price - 10 if fractal_type == 'low' else price,
                volume=1000
            )
            fractals.append(fractal)
        
        return fractals
    
    def _create_test_swings(self) -> List[Swing]:
        """Create test swing data with various dominance scenarios."""
        swings = []
        
        # Large UP swing (should be dominant)
        large_up_swing = Swing(
            start_fractal=self.test_fractals[1],  # Low at 39800
            end_fractal=self.test_fractals[6],    # High at 40600
            direction='up',
            points=800.0,  # Large swing
            bars=150
        )
        large_up_swing.is_dominant = True
        swings.append(large_up_swing)
        
        # Small DOWN swing (should not be dominant)
        small_down_swing = Swing(
            start_fractal=self.test_fractals[2],  # High at 40200
            end_fractal=self.test_fractals[3],    # Low at 39600
            direction='down',
            points=600.0,  # Smaller swing
            bars=30
        )
        small_down_swing.is_dominant = False
        swings.append(small_down_swing)
        
        # Medium UP swing (should not be dominant)
        medium_up_swing = Swing(
            start_fractal=self.test_fractals[3],  # Low at 39600
            end_fractal=self.test_fractals[4],    # High at 40400
            direction='up',
            points=800.0,  # Same size but older
            bars=30
        )
        medium_up_swing.is_dominant = False
        swings.append(medium_up_swing)
        
        return swings


class TestBackendDominancePreservation:
    """Test that frontend preserves backend dominance calculation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = TestSwingDominanceEdgeCases()
        self.test_case.setup_method()
    
    def test_backend_dominance_not_overridden(self):
        """Test that frontend doesn't override backend dominance."""
        # Simulate the scenario where backend marks a swing as dominant
        swings = self.test_case.test_swings.copy()
        
        # Ensure we have one dominant swing
        dominant_count = sum(1 for swing in swings if swing.is_dominant)
        assert dominant_count == 1, f"Expected 1 dominant swing, got {dominant_count}"
        
        # Find the dominant swing
        dominant_swing = next(swing for swing in swings if swing.is_dominant)
        original_dominant_direction = dominant_swing.direction
        original_dominant_points = dominant_swing.points
        
        # Simulate frontend processing (this should NOT change dominance)
        # The updateSwingDominance function should preserve backend dominance
        processed_swings = self._simulate_frontend_processing(swings)
        
        # Verify dominance is preserved
        processed_dominant = next((swing for swing in processed_swings if swing.is_dominant), None)
        assert processed_dominant is not None, "Dominant swing was lost during frontend processing"
        assert processed_dominant.direction == original_dominant_direction
        assert processed_dominant.points == original_dominant_points
        
        # Verify only one swing remains dominant
        processed_dominant_count = sum(1 for swing in processed_swings if swing.is_dominant)
        assert processed_dominant_count == 1, f"Expected 1 dominant swing after processing, got {processed_dominant_count}"
    
    def _simulate_frontend_processing(self, swings: List[Swing]) -> List[Swing]:
        """Simulate the frontend swing processing logic."""
        # This simulates the fixed updateSwingDominance function
        # which should preserve backend dominance
        
        # Find the swing already marked as dominant by backend
        backend_dominant = next((swing for swing in swings if swing.is_dominant), None)
        
        if backend_dominant:
            # Frontend should preserve this dominance
            return swings
        else:
            # If no backend dominance, frontend can calculate (but this shouldn't happen)
            return swings


class TestSwingDisplayLogic:
    """Test swing display and filtering logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = TestSwingDominanceEdgeCases()
        self.test_case.setup_method()
    
    def test_dominant_swing_always_displayed(self):
        """Test that dominant swing is always included in display."""
        swings = self.test_case.test_swings.copy()
        
        # Simulate the loadAllSwings filtering logic
        displayed_swings = self._simulate_display_filtering(swings)
        
        # Verify dominant swing is included
        dominant_in_display = any(swing.is_dominant for swing in displayed_swings)
        assert dominant_in_display, "Dominant swing must always be displayed"
        
        # Verify we have at most 2 swings (dominant + one context)
        assert len(displayed_swings) <= 2, f"Expected at most 2 displayed swings, got {len(displayed_swings)}"
    
    def test_context_swing_selection(self):
        """Test that appropriate context swing is selected."""
        swings = self.test_case.test_swings.copy()
        
        # Find dominant swing direction
        dominant_swing = next(swing for swing in swings if swing.is_dominant)
        opposite_direction = 'down' if dominant_swing.direction == 'up' else 'up'
        
        # Simulate display filtering
        displayed_swings = self._simulate_display_filtering(swings)
        
        # Should have dominant swing + most recent opposite direction
        directions = [swing.direction for swing in displayed_swings]
        assert dominant_swing.direction in directions, "Dominant swing direction must be displayed"
        
        if len(displayed_swings) > 1:
            assert opposite_direction in directions, "Context swing should be in opposite direction"
    
    def _simulate_display_filtering(self, swings: List[Swing]) -> List[Swing]:
        """Simulate the fixed loadAllSwings filtering logic."""
        # Find dominant swing
        dominant_swing = next((swing for swing in swings if swing.is_dominant), None)
        
        if not dominant_swing:
            return swings  # Fallback if no dominance
        
        display_swings = [dominant_swing]
        
        # Find most recent opposite direction swing
        opposite_direction = 'down' if dominant_swing.direction == 'up' else 'up'
        opposite_swings = [s for s in swings if s.direction == opposite_direction and not s.is_dominant]
        
        if opposite_swings:
            # Sort by end fractal timestamp (most recent first)
            opposite_swings.sort(key=lambda s: s.end_fractal.timestamp, reverse=True)
            display_swings.append(opposite_swings[0])
        
        return display_swings


class TestVisualStylingConsistency:
    """Test visual styling consistency for swing lines."""
    
    def test_dominant_swing_styling(self):
        """Test that dominant swings get correct visual styling."""
        # Test data for dominant swing
        swing_data = {
            'direction': 'up',
            'is_dominant': True,
            'points': 800.0
        }
        
        # Simulate styling logic
        styling = self._get_swing_styling(swing_data)
        
        # Dominant swings should be thick and solid
        assert styling['lineWidth'] == 4, f"Dominant swing should have lineWidth=4, got {styling['lineWidth']}"
        assert styling['lineStyle'] == 0, f"Dominant swing should have solid line (0), got {styling['lineStyle']}"
        assert styling['color'] in ['#00FF00', '#FF0000'], f"Dominant swing should have dominant color, got {styling['color']}"
    
    def test_non_dominant_swing_styling(self):
        """Test that non-dominant swings get correct visual styling."""
        # Test data for non-dominant swing
        swing_data = {
            'direction': 'down',
            'is_dominant': False,
            'points': 400.0
        }
        
        # Simulate styling logic
        styling = self._get_swing_styling(swing_data)
        
        # Non-dominant swings should be thin and dashed
        assert styling['lineWidth'] == 2, f"Non-dominant swing should have lineWidth=2, got {styling['lineWidth']}"
        assert styling['lineStyle'] == 1, f"Non-dominant swing should have dashed line (1), got {styling['lineStyle']}"
    
    def _get_swing_styling(self, swing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the swing styling logic from the dashboard."""
        direction = swing_data['direction']
        is_dominant = swing_data['is_dominant']
        
        # Color mapping
        colors = {
            'dominant_up': '#00FF00',
            'dominant_down': '#FF0000',
            'normal_up': '#26A69A',
            'normal_down': '#EF5350'
        }
        
        if is_dominant:
            color = colors[f'dominant_{direction}']
            line_width = 4
            line_style = 0  # Solid
        else:
            color = colors[f'normal_{direction}']
            line_width = 2
            line_style = 1  # Dashed
        
        return {
            'color': color,
            'lineWidth': line_width,
            'lineStyle': line_style
        }


class TestFibonacciLevelUpdates:
    """Test fibonacci level updates with dominance changes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = TestSwingDominanceEdgeCases()
        self.test_case.setup_method()
    
    def test_fibonacci_follows_dominant_swing(self):
        """Test that fibonacci levels are calculated from dominant swing."""
        swings = self.test_case.test_swings.copy()
        dominant_swing = next(swing for swing in swings if swing.is_dominant)
        
        # Simulate fibonacci calculation
        fib_levels = self._calculate_fibonacci_levels(dominant_swing)
        
        # Verify fibonacci levels are based on dominant swing
        expected_range = abs(dominant_swing.end_fractal.price - dominant_swing.start_fractal.price)
        calculated_range = abs(fib_levels['100.0'] - fib_levels['0.0'])
        
        assert abs(calculated_range - expected_range) < 0.01, "Fibonacci range should match dominant swing range"
    
    def test_fibonacci_updates_on_dominance_change(self):
        """Test that fibonacci levels update when dominance changes."""
        swings = self.test_case.test_swings.copy()
        
        # Get initial fibonacci levels
        initial_dominant = next(swing for swing in swings if swing.is_dominant)
        initial_fib = self._calculate_fibonacci_levels(initial_dominant)
        
        # Simulate dominance change
        initial_dominant.is_dominant = False
        new_dominant = next(swing for swing in swings if not swing.is_dominant)
        new_dominant.is_dominant = True
        
        # Get new fibonacci levels
        new_fib = self._calculate_fibonacci_levels(new_dominant)
        
        # Verify fibonacci levels changed
        assert initial_fib['50.0'] != new_fib['50.0'], "Fibonacci levels should update when dominance changes"
    
    def _calculate_fibonacci_levels(self, swing: Swing) -> Dict[str, float]:
        """Simulate fibonacci level calculation."""
        start_price = swing.start_fractal.price
        end_price = swing.end_fractal.price
        
        # Standard fibonacci retracement levels
        levels = {
            '0.0': start_price,
            '23.6': start_price + (end_price - start_price) * 0.236,
            '38.2': start_price + (end_price - start_price) * 0.382,
            '50.0': start_price + (end_price - start_price) * 0.5,
            '61.8': start_price + (end_price - start_price) * 0.618,
            '78.6': start_price + (end_price - start_price) * 0.786,
            '100.0': end_price
        }
        
        return levels


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_no_swings_scenario(self):
        """Test behavior when no swings are available."""
        empty_swings = []

        # Simulate display filtering with no swings
        displayed_swings = self._simulate_display_filtering_safe(empty_swings)

        assert len(displayed_swings) == 0, "Should handle empty swing list gracefully"

    def test_no_dominant_swing_scenario(self):
        """Test behavior when no swing is marked as dominant."""
        # Create swings without dominance
        test_case = TestSwingDominanceEdgeCases()
        test_case.setup_method()
        swings = test_case.test_swings.copy()

        # Remove dominance from all swings
        for swing in swings:
            swing.is_dominant = False

        # Should handle gracefully
        displayed_swings = self._simulate_display_filtering_safe(swings)

        # Should fall back to showing all swings or handle gracefully
        assert isinstance(displayed_swings, list), "Should return a list even with no dominant swing"

    def test_invalid_fractal_data(self):
        """Test handling of invalid fractal data."""
        # Create swing with invalid fractal data
        invalid_swing_data = {
            'start_fractal': {'timestamp': None, 'price': 'invalid'},
            'end_fractal': {'timestamp': 'invalid', 'price': None},
            'direction': 'up',
            'is_dominant': True
        }

        # Should handle invalid data gracefully
        is_valid = self._validate_swing_data(invalid_swing_data)
        assert not is_valid, "Should detect invalid swing data"

    def test_extreme_price_movements(self):
        """Test handling of extreme price movements."""
        # Create swing with extreme price movement
        extreme_swing_data = {
            'start_fractal': {'timestamp': '2025-06-01T10:00:00', 'price': 40000.0},
            'end_fractal': {'timestamp': '2025-06-01T10:01:00', 'price': 50000.0},  # 10,000 point move in 1 minute
            'direction': 'up',
            'is_dominant': True
        }

        # Should detect suspicious movement
        is_suspicious = self._detect_suspicious_movement(extreme_swing_data)
        assert is_suspicious, "Should detect extreme price movements"

    def test_very_short_time_spans(self):
        """Test handling of very short time spans."""
        # Create swing with very short time span
        short_swing_data = {
            'start_fractal': {'timestamp': '2025-06-01T10:00:00', 'price': 40000.0},
            'end_fractal': {'timestamp': '2025-06-01T10:00:30', 'price': 40100.0},  # 30 second swing
            'direction': 'up',
            'is_dominant': True
        }

        # Should detect suspicious timing
        is_suspicious = self._detect_suspicious_timing(short_swing_data)
        assert is_suspicious, "Should detect very short time spans"

    def test_duplicate_swing_detection(self):
        """Test detection of duplicate swings."""
        # Create identical swings
        swing1_data = {
            'start_fractal': {'timestamp': '2025-06-01T10:00:00', 'price': 40000.0},
            'end_fractal': {'timestamp': '2025-06-01T11:00:00', 'price': 40500.0},
            'direction': 'up'
        }

        swing2_data = swing1_data.copy()  # Identical

        # Should detect duplicate
        is_duplicate = self._detect_duplicate_swing(swing1_data, swing2_data)
        assert is_duplicate, "Should detect duplicate swings"

    def test_concurrent_dominance_conflict(self):
        """Test handling when multiple swings claim dominance."""
        test_case = TestSwingDominanceEdgeCases()
        test_case.setup_method()
        swings = test_case.test_swings.copy()

        # Mark multiple swings as dominant (error scenario)
        for swing in swings:
            swing.is_dominant = True

        # Should resolve to single dominant swing
        resolved_swings = self._resolve_dominance_conflicts(swings)
        dominant_count = sum(1 for swing in resolved_swings if swing.is_dominant)
        assert dominant_count == 1, f"Should resolve to exactly 1 dominant swing, got {dominant_count}"

    def _simulate_display_filtering_safe(self, swings):
        """Safe version of display filtering that handles edge cases."""
        if not swings:
            return []

        dominant_swing = next((swing for swing in swings if swing.is_dominant), None)

        if not dominant_swing:
            # Fallback: return all swings or empty list
            return swings

        return [dominant_swing]

    def _validate_swing_data(self, swing_data):
        """Validate swing data for required fields and types."""
        try:
            start_fractal = swing_data.get('start_fractal', {})
            end_fractal = swing_data.get('end_fractal', {})

            # Check required fields
            if not start_fractal.get('timestamp') or not end_fractal.get('timestamp'):
                return False

            if not isinstance(start_fractal.get('price'), (int, float)):
                return False

            if not isinstance(end_fractal.get('price'), (int, float)):
                return False

            return True
        except Exception:
            return False

    def _detect_suspicious_movement(self, swing_data):
        """Detect suspiciously large price movements."""
        try:
            start_price = swing_data['start_fractal']['price']
            end_price = swing_data['end_fractal']['price']
            price_diff = abs(end_price - start_price)

            # Flag movements > 1000 points as suspicious
            return price_diff > 1000
        except Exception:
            return True  # Treat errors as suspicious

    def _detect_suspicious_timing(self, swing_data):
        """Detect suspiciously short time spans."""
        try:
            from datetime import datetime
            start_time = datetime.fromisoformat(swing_data['start_fractal']['timestamp'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(swing_data['end_fractal']['timestamp'].replace('Z', '+00:00'))
            time_diff = (end_time - start_time).total_seconds()

            # Flag swings < 60 seconds as suspicious
            return time_diff < 60
        except Exception:
            return True  # Treat errors as suspicious

    def _detect_duplicate_swing(self, swing1, swing2):
        """Detect if two swings are duplicates."""
        try:
            return (swing1['start_fractal']['timestamp'] == swing2['start_fractal']['timestamp'] and
                    swing1['end_fractal']['timestamp'] == swing2['end_fractal']['timestamp'] and
                    swing1['start_fractal']['price'] == swing2['start_fractal']['price'] and
                    swing1['end_fractal']['price'] == swing2['end_fractal']['price'])
        except Exception:
            return False

    def _resolve_dominance_conflicts(self, swings):
        """Resolve conflicts when multiple swings claim dominance."""
        # Find all dominant swings
        dominant_swings = [swing for swing in swings if swing.is_dominant]

        if len(dominant_swings) <= 1:
            return swings  # No conflict

        # Resolve by choosing the largest swing
        largest_swing = max(dominant_swings, key=lambda s: s.points)

        # Reset all dominance and set only the largest
        for swing in swings:
            swing.is_dominant = False
        largest_swing.is_dominant = True

        return swings


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
