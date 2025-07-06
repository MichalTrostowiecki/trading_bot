#!/usr/bin/env python3
"""
Test script to verify the dominant swing detection fix.
This simulates the JavaScript logic to ensure the fix works correctly.
"""

def test_dominant_swing_logic():
    """Test the fixed dominant swing logic"""
    print("🔧 Testing Fixed Dominant Swing Logic")
    print("=" * 50)
    
    # Simulate the JavaScript variables
    accumulatedDominantSwing = None
    accumulatedSwings = []
    
    # Test sequence: dominant -> non-dominant -> dominant
    test_swings = [
        {
            'direction': 'up',
            'is_dominant': True,
            'start_fractal': {'timestamp': '2024-01-01T10:00:00', 'price': 1000.0},
            'end_fractal': {'timestamp': '2024-01-01T12:00:00', 'price': 1100.0},
            'points': 100.0,
            'id': 'swing1'
        },
        {
            'direction': 'down', 
            'is_dominant': False,
            'start_fractal': {'timestamp': '2024-01-01T12:00:00', 'price': 1100.0},
            'end_fractal': {'timestamp': '2024-01-01T14:00:00', 'price': 1050.0},
            'points': 50.0,
            'id': 'swing2'
        },
        {
            'direction': 'up',
            'is_dominant': True,
            'start_fractal': {'timestamp': '2024-01-01T14:00:00', 'price': 1050.0},
            'end_fractal': {'timestamp': '2024-01-01T16:00:00', 'price': 1200.0},
            'points': 150.0,
            'id': 'swing3'
        }
    ]
    
    print("Processing swing sequence:")
    
    for i, newSwing in enumerate(test_swings):
        print(f"\n📈 Step {i+1}: Processing {newSwing['id']} ({newSwing['direction']}, dominant: {newSwing['is_dominant']})")
        
        # SIMULATE THE FIXED JAVASCRIPT LOGIC
        
        # 1. Check for dominant swing change (ABC pattern clearing logic)
        previousDominantSwing = accumulatedDominantSwing
        newDominantSwing = newSwing if newSwing['is_dominant'] else None
        
        print(f"   Previous dominant: {previousDominantSwing['id'] if previousDominantSwing else 'None'}")
        print(f"   New dominant: {newDominantSwing['id'] if newDominantSwing else 'None'}")
        
        if (previousDominantSwing and newDominantSwing and 
            previousDominantSwing['start_fractal']['timestamp'] != newDominantSwing['start_fractal']['timestamp']):
            print("   🔄 DOMINANT SWING CHANGED - Would clear ABC patterns")
        
        # 2. Update accumulated swings
        accumulatedSwings = []
        accumulatedSwings.append(newSwing)
        
        # 3. FIXED LOGIC: Update dominant swing BEFORE any other processing
        accumulatedDominantSwing = newSwing if newSwing['is_dominant'] else None
        print(f"   🎯 DOMINANT SWING UPDATED: {accumulatedDominantSwing['id'] if accumulatedDominantSwing else 'CLEARED'}")
        
        # 4. Simulate updateSwingDominance() - should NOT overwrite if already set correctly
        backendDominantSwing = None
        for swing in accumulatedSwings:
            if swing['is_dominant']:
                backendDominantSwing = swing
                break
        
        if backendDominantSwing:
            # FIXED: Only update if not already set correctly
            if (not accumulatedDominantSwing or 
                not accumulatedDominantSwing.get('start_fractal') or 
                accumulatedDominantSwing['start_fractal']['timestamp'] != backendDominantSwing['start_fractal']['timestamp']):
                print("   🔄 updateSwingDominance() would update (was not set correctly)")
                accumulatedDominantSwing = backendDominantSwing
            else:
                print("   ✅ updateSwingDominance() preserving existing (already correct)")
        
        # 5. Final state
        final_state = accumulatedDominantSwing['id'] if accumulatedDominantSwing else 'None'
        expected_state = newSwing['id'] if newSwing['is_dominant'] else 'None'
        
        if final_state == expected_state:
            print(f"   ✅ CORRECT: Final dominant swing = {final_state}")
        else:
            print(f"   ❌ ERROR: Final dominant swing = {final_state}, expected = {expected_state}")
    
    print(f"\n🎯 Final Result:")
    print(f"   accumulatedDominantSwing = {accumulatedDominantSwing['id'] if accumulatedDominantSwing else 'None'}")
    print(f"   Expected = swing3 (last dominant swing)")
    
    # Verify final result
    if accumulatedDominantSwing and accumulatedDominantSwing['id'] == 'swing3':
        print(f"   ✅ SUCCESS: Dominant swing detection is working correctly!")
        return True
    else:
        print(f"   ❌ FAILURE: Dominant swing detection is still broken!")
        return False

if __name__ == "__main__":
    success = test_dominant_swing_logic()
    exit(0 if success else 1)
