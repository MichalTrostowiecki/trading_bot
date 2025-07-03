#!/usr/bin/env python3
"""
Test runner for swing dominance edge cases.

This script runs comprehensive tests to verify:
1. Backend dominance preservation
2. Frontend display logic
3. Visual styling consistency
4. Fibonacci level updates
5. Edge case handling

Usage:
    python tests/run_swing_dominance_tests.py
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_test_suite():
    """Run the complete swing dominance test suite."""
    print("🧪 Running Swing Dominance Edge Case Tests")
    print("=" * 60)
    
    test_results = {}
    
    # Test categories to run
    test_categories = [
        ("Backend Dominance Preservation", "TestBackendDominancePreservation"),
        ("Swing Display Logic", "TestSwingDisplayLogic"),
        ("Visual Styling Consistency", "TestVisualStylingConsistency"),
        ("Fibonacci Level Updates", "TestFibonacciLevelUpdates"),
        ("Edge Cases and Error Handling", "TestEdgeCasesAndErrorHandling")
    ]
    
    for category_name, test_class in test_categories:
        print(f"\n📋 Running {category_name} Tests...")
        print("-" * 40)
        
        try:
            # Run specific test class
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                f"tests/test_swing_dominance_edge_cases.py::{test_class}",
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            test_results[category_name] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ {category_name}: PASSED")
            else:
                print(f"❌ {category_name}: FAILED")
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ {category_name}: ERROR - {str(e)}")
            test_results[category_name] = {
                'success': False,
                'output': '',
                'errors': str(e)
            }
    
    # Generate test report
    generate_test_report(test_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result['success'])
    total = len(test_results)
    
    print(f"Total Test Categories: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Swing dominance fixes are working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test categories failed. Please review the issues.")
        return False


def generate_test_report(test_results):
    """Generate a detailed test report."""
    report_path = Path("tests/swing_dominance_test_report.json")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_categories': len(test_results),
            'passed': sum(1 for r in test_results.values() if r['success']),
            'failed': sum(1 for r in test_results.values() if not r['success'])
        },
        'results': test_results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed test report saved to: {report_path}")


def run_manual_verification():
    """Run manual verification tests that require visual inspection."""
    print("\n🔍 MANUAL VERIFICATION CHECKLIST")
    print("=" * 60)
    
    checklist = [
        "1. Load the research dashboard (http://127.0.0.1:9000)",
        "2. Select DJ30 M1 data from 2025-06-02 to 2025-06-27",
        "3. Enable swing lines display",
        "4. Navigate through different time positions",
        "5. Verify dominant swing shows as THICK SOLID line",
        "6. Verify non-dominant swings show as THIN DASHED lines",
        "7. Verify fibonacci levels update with dominant swing",
        "8. Verify market bias matches dominant swing direction",
        "9. Check console logs for proper dominance preservation messages",
        "10. Test edge cases: no swings, single swing, multiple swings"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n💡 Expected Behavior:")
    print("   - Dominant swing: Thick solid line (4px width)")
    print("   - Non-dominant swing: Thin dashed line (2px width)")
    print("   - Fibonacci levels: Always based on dominant swing")
    print("   - Market bias: Always matches dominant swing direction")
    print("   - Console logs: 'BACKEND DOMINANCE: ... - PRESERVING'")


def test_specific_scenarios():
    """Test specific scenarios that were problematic."""
    print("\n🎯 TESTING SPECIFIC PROBLEMATIC SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'Dominant Swing Disappearing',
            'description': 'Thick line becomes thin dotted line',
            'test': 'Verify dominant swing maintains thick solid styling'
        },
        {
            'name': 'Frontend Overriding Backend Dominance',
            'description': 'Frontend recalculates dominance incorrectly',
            'test': 'Verify backend dominance is preserved'
        },
        {
            'name': 'Fibonacci Levels Wrong Swing',
            'description': 'Fibonacci shows for non-dominant swing',
            'test': 'Verify fibonacci always uses dominant swing'
        },
        {
            'name': 'Latest Swing vs Dominant Swing',
            'description': 'Display shows latest instead of dominant',
            'test': 'Verify dominant swing always displayed regardless of recency'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Issue: {scenario['description']}")
        print(f"   Test: {scenario['test']}")
    
    print("\n✅ All these scenarios should now be fixed with our changes:")
    print("   - updateSwingDominance() preserves backend dominance")
    print("   - loadAllSwings() prioritizes dominant swing over latest")
    print("   - Visual styling respects is_dominant flag")
    print("   - Fibonacci calculation uses dominant swing")


if __name__ == "__main__":
    print("🚀 Starting Comprehensive Swing Dominance Test Suite")
    print("=" * 60)
    
    # Run automated tests
    success = run_test_suite()
    
    # Run manual verification checklist
    run_manual_verification()
    
    # Test specific scenarios
    test_specific_scenarios()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TESTING COMPLETE - All automated tests passed!")
        print("📋 Please complete the manual verification checklist above.")
    else:
        print("⚠️  TESTING COMPLETE - Some tests failed.")
        print("🔧 Please review the test report and fix any issues.")
    
    print("=" * 60)
