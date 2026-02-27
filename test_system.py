"""
System Test Script
Verify all components are working correctly
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 70)
    print("TESTING MODULE IMPORTS")
    print("=" * 70)
    
    tests = [
        ("fetch_tle", "TLE Fetcher"),
        ("propagation.propagate", "Orbit Propagator"),
        ("propagation.distance_check", "Distance Checker"),
        ("probability.collision_probability", "Collision Probability"),
        ("optimization.avoidance", "Maneuver Optimizer"),
        ("visualization.plot_orbits", "Orbit Visualizer"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✓ {description:30s} - OK")
            passed += 1
        except ImportError as e:
            print(f"✗ {description:30s} - FAILED: {e}")
            failed += 1
    
    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()
    
    return failed == 0

def test_dependencies():
    """Test that all required packages are installed"""
    print("=" * 70)
    print("TESTING DEPENDENCIES")
    print("=" * 70)
    
    packages = [
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("pandas", "Pandas"),
        ("matplotlib", "Matplotlib"),
        ("plotly", "Plotly"),
        ("sgp4", "SGP4"),
        ("requests", "Requests"),
    ]
    
    passed = 0
    failed = 0
    
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name:30s} - Installed")
            passed += 1
        except ImportError:
            print(f"✗ {name:30s} - NOT INSTALLED")
            failed += 1
    
    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
    
    print("=" * 70)
    print()
    
    return failed == 0

def test_directory_structure():
    """Test that all required directories exist"""
    print("=" * 70)
    print("TESTING DIRECTORY STRUCTURE")
    print("=" * 70)
    
    directories = [
        "data",
        "propagation",
        "probability",
        "optimization",
        "visualization",
        "output"
    ]
    
    passed = 0
    failed = 0
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"✓ {directory:30s} - Exists")
            passed += 1
        else:
            print(f"✗ {directory:30s} - MISSING")
            failed += 1
    
    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()
    
    return failed == 0

def test_file_structure():
    """Test that all required files exist"""
    print("=" * 70)
    print("TESTING FILE STRUCTURE")
    print("=" * 70)
    
    files = [
        "README.md",
        "QUICKSTART.md",
        "TECHNICAL_DOCS.md",
        "ARCHITECTURE.md",
        "requirements.txt",
        "fetch_tle.py",
        "main.py",
        "propagation/__init__.py",
        "propagation/propagate.py",
        "propagation/distance_check.py",
        "probability/__init__.py",
        "probability/collision_probability.py",
        "optimization/__init__.py",
        "optimization/avoidance.py",
        "visualization/__init__.py",
        "visualization/plot_orbits.py",
    ]
    
    passed = 0
    failed = 0
    
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file:45s} - Exists")
            passed += 1
        else:
            print(f"✗ {file:45s} - MISSING")
            failed += 1
    
    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()
    
    return failed == 0

def run_all_tests():
    """Run all system tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "ASTROCLEANAI SYSTEM TEST" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = []
    
    # Test 1: Directory Structure
    results.append(("Directory Structure", test_directory_structure()))
    
    # Test 2: File Structure
    results.append(("File Structure", test_file_structure()))
    
    # Test 3: Dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Test 4: Module Imports
    results.append(("Module Imports", test_imports()))
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:30s} - {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - System is ready to use!")
        print("\nNext steps:")
        print("  1. Run: python fetch_tle.py")
        print("  2. Run: python main.py")
        print()
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Please fix the issues above")
        print("\nCommon fixes:")
        print("  • Missing packages: pip install -r requirements.txt")
        print("  • Missing files: Check git repository")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
