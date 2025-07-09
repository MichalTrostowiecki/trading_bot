#!/usr/bin/env python3
"""
Test Runner for Fibonacci Trading Bot
Comprehensive test execution with reporting and coverage.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def install_test_dependencies():
    """Install required test dependencies."""
    dependencies = [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-mock>=3.10.0',
        'pytest-asyncio>=0.21.0',
        'pytest-html>=3.1.0',
        'pytest-xdist>=3.0.0'  # For parallel test execution
    ]
    
    for dep in dependencies:
        cmd = [sys.executable, '-m', 'pip', 'install', dep]
        if not run_command(cmd, f"Installing {dep}"):
            print(f"⚠️ Failed to install {dep}, continuing anyway...")


def run_unit_tests(coverage=True, parallel=False, verbose=True):
    """Run unit tests with optional coverage and parallel execution."""
    cmd = [sys.executable, '-m', 'pytest']
    
    # Test directories
    cmd.extend(['tests/unit/', '-v' if verbose else '-q'])
    
    # Coverage options
    if coverage:
        cmd.extend([
            '--cov=src',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-fail-under=80'  # Require 80% coverage
        ])
    
    # Parallel execution
    if parallel:
        cmd.extend(['-n', 'auto'])  # Auto-detect CPU cores
    
    # Additional options
    cmd.extend([
        '--tb=short',  # Shorter traceback format
        '--strict-markers',  # Strict marker validation
        '--disable-warnings'  # Reduce noise
    ])
    
    return run_command(cmd, "Running Unit Tests")


def run_integration_tests(verbose=True):
    """Run integration tests."""
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/integration/',
        '-v' if verbose else '-q',
        '--tb=short',
        '-m', 'not slow'  # Skip slow tests by default
    ]
    
    return run_command(cmd, "Running Integration Tests")


def run_specific_test_category(category, verbose=True):
    """Run tests for a specific category."""
    categories = {
        'fractal': 'fractal detection tests',
        'swing': 'swing detection tests',
        'abc': 'ABC pattern tests',
        'fibonacci': 'Fibonacci calculation tests',
        'frontend': 'frontend logic tests'
    }
    
    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return False
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v' if verbose else '-q',
        '-m', category,
        '--tb=short'
    ]
    
    return run_command(cmd, f"Running {categories[category]}")


def run_performance_tests():
    """Run performance/benchmark tests."""
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '-m', 'slow',
        '--tb=short'
    ]
    
    return run_command(cmd, "Running Performance Tests")


def generate_test_report():
    """Generate comprehensive test report."""
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--html=test_report.html',
        '--self-contained-html',
        '--cov=src',
        '--cov-report=html:htmlcov',
        '--tb=short'
    ]
    
    success = run_command(cmd, "Generating Test Report")
    
    if success:
        print("\n📊 Test Report Generated:")
        print("   HTML Report: test_report.html")
        print("   Coverage Report: htmlcov/index.html")
    
    return success


def validate_test_structure():
    """Validate test file structure and imports."""
    print("\n🔍 Validating Test Structure...")
    
    test_files = list(Path('tests').rglob('test_*.py'))
    
    if not test_files:
        print("❌ No test files found!")
        return False
    
    print(f"✅ Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"   - {test_file}")
    
    # Check for required test categories
    required_categories = ['fractal', 'swing', 'abc', 'fibonacci']
    found_categories = set()
    
    for test_file in test_files:
        try:
            content = test_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = test_file.read_text(encoding='latin-1')
            except UnicodeDecodeError:
                print(f"⚠️ Could not read {test_file} due to encoding issues")
                continue

        for category in required_categories:
            if category in content.lower():
                found_categories.add(category)
    
    missing_categories = set(required_categories) - found_categories
    if missing_categories:
        print(f"⚠️ Missing test categories: {', '.join(missing_categories)}")
    else:
        print("✅ All required test categories found")
    
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Fibonacci Trading Bot Test Runner')
    parser.add_argument('--category', choices=['fractal', 'swing', 'abc', 'fibonacci', 'frontend'],
                       help='Run tests for specific category')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage reporting')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--install-deps', action='store_true', help='Install test dependencies')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive test report')
    parser.add_argument('--validate', action='store_true', help='Validate test structure only')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(Path(__file__).parent)
    
    print("🚀 Fibonacci Trading Bot Test Runner")
    print("=" * 60)
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps:
        install_test_dependencies()
    
    # Validate test structure if requested
    if args.validate:
        return validate_test_structure()
    
    # Run specific test category
    if args.category:
        return run_specific_test_category(args.category, not args.quiet)
    
    # Run specific test types
    if args.unit:
        success &= run_unit_tests(
            coverage=not args.no_coverage,
            parallel=args.parallel,
            verbose=not args.quiet
        )
    elif args.integration:
        success &= run_integration_tests(not args.quiet)
    elif args.performance:
        success &= run_performance_tests()
    elif args.report:
        success &= generate_test_report()
    else:
        # Run all tests by default
        print("🔧 Running Complete Test Suite...")
        
        # Validate structure first
        if not validate_test_structure():
            return False
        
        # Run unit tests
        success &= run_unit_tests(
            coverage=not args.no_coverage,
            parallel=args.parallel,
            verbose=not args.quiet
        )
        
        # Run integration tests if unit tests pass
        if success:
            success &= run_integration_tests(not args.quiet)
    
    # Print final result
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("🎯 Your trading logic is sound and well-tested.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please review the failures and fix the issues.")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
