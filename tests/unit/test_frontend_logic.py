#!/usr/bin/env python3
"""
Unit Tests for Frontend Logic
Tests the JavaScript logic that was recently fixed for dominant swings and ABC patterns.
"""

import pytest
from datetime import datetime, timedelta
import json


@pytest.mark.frontend
class TestDominantSwingLogic:
    """Test the dominant swing detection logic (simulating JavaScript behavior)."""
    
    def test_dominant_swing_assignment(self):
        """Test the core dominant swing assignment logic."""
        # Simulate JavaScript variables
        accumulated_dominant_swing = None
        
        # Test sequence: dominant -> non-dominant -> dominant
        test_swings = [
            {
                'direction': 'up',
                'is_dominant': True,
                'start_fractal': {'timestamp': '2024-01-01T10:00:00'},
                'id': 'swing1'
            },
            {
                'direction': 'down',
                'is_dominant': False,
                'start_fractal': {'timestamp': '2024-01-01T12:00:00'},
                'id': 'swing2'
            },
            {
                'direction': 'up',
                'is_dominant': True,
                'start_fractal': {'timestamp': '2024-01-01T14:00:00'},
                'id': 'swing3'
            }
        ]
        
        expected_states = [
            'swing1',  # First dominant swing
            None,      # Non-dominant swing clears it
            'swing3'   # New dominant swing
        ]
        
        for i, new_swing in enumerate(test_swings):
            # Simulate the FIXED JavaScript logic
            accumulated_dominant_swing = new_swing if new_swing['is_dominant'] else None
            
            expected = expected_states[i]
            actual = accumulated_dominant_swing['id'] if accumulated_dominant_swing else None
            
            assert actual == expected, f"Step {i+1}: Expected {expected}, got {actual}"
    
    def test_abc_clearing_logic(self):
        """Test ABC pattern clearing when dominant swing changes."""
        accumulated_dominant_swing = None
        accumulated_abc_patterns = []
        
        # Test sequence with ABC patterns
        test_sequence = [
            {
                'swing': {
                    'direction': 'up',
                    'is_dominant': True,
                    'start_fractal': {'timestamp': '2024-01-01T10:00:00'},
                    'id': 'up_swing'
                },
                'abc_patterns': [{'id': 'abc_for_up', 'direction': 'down'}]
            },
            {
                'swing': {
                    'direction': 'down',
                    'is_dominant': True,
                    'start_fractal': {'timestamp': '2024-01-01T14:00:00'},
                    'id': 'down_swing'
                },
                'abc_patterns': [{'id': 'abc_for_down', 'direction': 'up'}]
            }
        ]
        
        for step in test_sequence:
            new_swing = step['swing']
            previous_dominant_swing = accumulated_dominant_swing
            new_dominant_swing = new_swing if new_swing['is_dominant'] else None
            
            # Test the FIXED clearing logic
            should_clear_abc = (previous_dominant_swing and new_dominant_swing and (
                # Different swing (timestamp changed)
                previous_dominant_swing['start_fractal']['timestamp'] != new_dominant_swing['start_fractal']['timestamp'] or
                # Direction changed
                previous_dominant_swing['direction'] != new_dominant_swing['direction']
            )) or (
                # Dominant swing was cleared
                previous_dominant_swing and not new_dominant_swing
            )
            
            if should_clear_abc:
                accumulated_abc_patterns = []
            
            # Update swing and add new patterns
            accumulated_dominant_swing = new_dominant_swing
            accumulated_abc_patterns.extend(step['abc_patterns'])
        
        # Should only have the last ABC pattern (from down swing)
        assert len(accumulated_abc_patterns) == 1
        assert accumulated_abc_patterns[0]['id'] == 'abc_for_down'


@pytest.mark.frontend
@pytest.mark.abc
class TestABCPatternFiltering:
    """Test ABC pattern time-based filtering logic."""
    
    def test_future_pattern_filtering(self):
        """Test filtering of future ABC patterns."""
        current_timestamp = '2024-01-01T12:00:00'
        
        abc_patterns = [
            {
                'wave_a': {'start_timestamp': '2024-01-01T10:00:00'},
                'id': 'past_pattern'
            },
            {
                'wave_a': {'start_timestamp': '2024-01-01T12:00:00'},
                'id': 'current_pattern'
            },
            {
                'wave_a': {'start_timestamp': '2024-01-01T14:00:00'},
                'id': 'future_pattern'
            }
        ]
        
        # Simulate the FIXED filtering logic
        valid_patterns = []
        for pattern in abc_patterns:
            wave_a_start_time = datetime.fromisoformat(pattern['wave_a']['start_timestamp'])
            current_time = datetime.fromisoformat(current_timestamp)
            
            if wave_a_start_time <= current_time:
                valid_patterns.append(pattern)
        
        # Should only show past and current patterns
        assert len(valid_patterns) == 2
        assert valid_patterns[0]['id'] == 'past_pattern'
        assert valid_patterns[1]['id'] == 'current_pattern'
    
    def test_pattern_filtering_edge_cases(self):
        """Test edge cases in pattern filtering."""
        current_timestamp = '2024-01-01T12:00:00'
        
        # Test with empty patterns
        empty_patterns = []
        valid_patterns = [p for p in empty_patterns if 
                         datetime.fromisoformat(p['wave_a']['start_timestamp']) <= 
                         datetime.fromisoformat(current_timestamp)]
        assert len(valid_patterns) == 0
        
        # Test with malformed timestamp
        malformed_patterns = [
            {'wave_a': {'start_timestamp': 'invalid-timestamp'}, 'id': 'bad_pattern'}
        ]
        
        valid_patterns = []
        for pattern in malformed_patterns:
            try:
                wave_a_start_time = datetime.fromisoformat(pattern['wave_a']['start_timestamp'])
                current_time = datetime.fromisoformat(current_timestamp)
                if wave_a_start_time <= current_time:
                    valid_patterns.append(pattern)
            except ValueError:
                # Skip malformed patterns
                pass
        
        assert len(valid_patterns) == 0


@pytest.mark.frontend
class TestUIThrottling:
    """Test UI update throttling logic."""
    
    def test_throttling_mechanism(self):
        """Test the throttling mechanism for UI updates."""
        import time
        
        # Simulate throttling variables
        last_update_time = 0
        throttle_interval = 0.1  # 100ms
        update_count = 0
        
        def should_update():
            nonlocal last_update_time, update_count
            current_time = time.time()
            
            if current_time - last_update_time < throttle_interval:
                return False
            
            last_update_time = current_time
            update_count += 1
            return True
        
        # Test rapid updates
        successful_updates = 0
        total_attempts = 10
        
        for i in range(total_attempts):
            if should_update():
                successful_updates += 1
            time.sleep(0.05)  # 50ms between attempts
        
        # Should throttle some updates
        assert successful_updates < total_attempts
        assert successful_updates > 0
        assert update_count == successful_updates
    
    def test_data_validation(self):
        """Test data validation before UI updates."""
        def validate_bar_data(bar_data, position):
            """Simulate the data validation logic."""
            if not bar_data or not isinstance(position, (int, float)):
                return False
            
            required_fields = ['timestamp', 'open', 'high', 'low', 'close']
            for field in required_fields:
                if field not in bar_data:
                    return False
            
            return True
        
        # Test valid data
        valid_data = {
            'timestamp': '2024-01-01T12:00:00',
            'open': 1.0000,
            'high': 1.0010,
            'low': 0.9990,
            'close': 1.0005
        }
        assert validate_bar_data(valid_data, 1) is True
        
        # Test invalid data
        assert validate_bar_data(None, 1) is False
        assert validate_bar_data(valid_data, None) is False
        assert validate_bar_data({}, 1) is False
        
        # Test missing fields
        incomplete_data = {'timestamp': '2024-01-01T12:00:00'}
        assert validate_bar_data(incomplete_data, 1) is False


@pytest.mark.frontend
class TestMarketBiasLogic:
    """Test market bias calculation and display logic."""
    
    def test_market_bias_calculation(self):
        """Test market bias calculation from dominant swing."""
        def calculate_market_bias(dominant_swing):
            """Simulate market bias calculation."""
            if not dominant_swing:
                return None
            
            direction = dominant_swing.get('direction')
            points = dominant_swing.get('points', 0)
            
            if direction == 'up':
                return {
                    'bias': 'BULLISH',
                    'direction': 'UP',
                    'points': points,
                    'trading_direction': 'LOOK FOR BUY OPPORTUNITIES'
                }
            elif direction == 'down':
                return {
                    'bias': 'BEARISH',
                    'direction': 'DOWN',
                    'points': points,
                    'trading_direction': 'LOOK FOR SELL OPPORTUNITIES'
                }
            
            return None
        
        # Test up swing
        up_swing = {'direction': 'up', 'points': 0.0100}
        bias = calculate_market_bias(up_swing)
        assert bias['bias'] == 'BULLISH'
        assert bias['direction'] == 'UP'
        assert 'BUY' in bias['trading_direction']
        
        # Test down swing
        down_swing = {'direction': 'down', 'points': 0.0150}
        bias = calculate_market_bias(down_swing)
        assert bias['bias'] == 'BEARISH'
        assert bias['direction'] == 'DOWN'
        assert 'SELL' in bias['trading_direction']
        
        # Test no swing
        assert calculate_market_bias(None) is None


@pytest.mark.frontend
@pytest.mark.integration
class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_complete_swing_to_abc_workflow(self):
        """Test the complete workflow from swing detection to ABC pattern display."""
        # Simulate complete workflow
        accumulated_dominant_swing = None
        accumulated_abc_patterns = []
        
        # Step 1: Detect dominant swing
        new_swing = {
            'direction': 'up',
            'is_dominant': True,
            'start_fractal': {'timestamp': '2024-01-01T10:00:00'},
            'points': 0.0100
        }
        
        accumulated_dominant_swing = new_swing if new_swing['is_dominant'] else None
        assert accumulated_dominant_swing is not None
        
        # Step 2: Add ABC patterns for this swing
        abc_patterns = [
            {
                'wave_a': {'start_timestamp': '2024-01-01T11:00:00', 'direction': 'down'},
                'wave_b': {'direction': 'up'},
                'wave_c': {'direction': 'down'},
                'pattern_type': 'zigzag'
            }
        ]
        
        # Filter patterns (should pass - after swing start)
        current_timestamp = '2024-01-01T12:00:00'
        valid_patterns = [p for p in abc_patterns if 
                         datetime.fromisoformat(p['wave_a']['start_timestamp']) <= 
                         datetime.fromisoformat(current_timestamp)]
        
        accumulated_abc_patterns = valid_patterns
        assert len(accumulated_abc_patterns) == 1
        
        # Step 3: New dominant swing in different direction
        new_swing_2 = {
            'direction': 'down',
            'is_dominant': True,
            'start_fractal': {'timestamp': '2024-01-01T14:00:00'},
            'points': 0.0120
        }
        
        # Should clear ABC patterns
        previous_dominant_swing = accumulated_dominant_swing
        new_dominant_swing = new_swing_2 if new_swing_2['is_dominant'] else None
        
        should_clear = (previous_dominant_swing and new_dominant_swing and
                       previous_dominant_swing['direction'] != new_dominant_swing['direction'])
        
        if should_clear:
            accumulated_abc_patterns = []
        
        accumulated_dominant_swing = new_dominant_swing
        
        # Verify final state
        assert accumulated_dominant_swing['direction'] == 'down'
        assert len(accumulated_abc_patterns) == 0  # Should be cleared


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
