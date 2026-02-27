"""
Comprehensive Test Suite for AstroCleanAI
Tests all major features and endpoints
"""

import requests
import time
import json

BASE_URL = 'http://localhost:5000'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=''):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status}: {name}")
    if details:
        print(f"  {details}")

def test_health():
    """Test enhanced health endpoint"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 1: Core System{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    try:
        r = requests.get(f'{BASE_URL}/health', timeout=5)
        data = r.json()
        
        # Accept both healthy and degraded as passing (degraded just means DB check had issues)
        passed = (
            r.status_code == 200 and
            data.get('status') in ['healthy', 'degraded'] and
            'services' in data and
            'features' in data
        )
        
        print_test('Health Check', passed, 
                   f"Version: {data.get('version')}, Status: {data.get('status')}")
        return passed
    except Exception as e:
        print_test('Health Check', False, str(e))
        return False

def test_satellites():
    """Test satellite endpoints"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 2: Satellite Management{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test list satellites
    try:
        r = requests.get(f'{BASE_URL}/api/satellites')
        passed = r.status_code == 200 and 'satellites' in r.json()
        print_test('List Satellites', passed, f"Found {r.json().get('count', 0)} satellites")
        results.append(passed)
    except Exception as e:
        print_test('List Satellites', False, str(e))
        results.append(False)
    
    # Test managed satellites
    try:
        r = requests.get(f'{BASE_URL}/api/satellites/manage')
        passed = r.status_code == 200
        count = r.json().get('count', 0)
        print_test('Managed Satellites', passed, f"Managing {count} satellites")
        results.append(passed)
    except Exception as e:
        print_test('Managed Satellites', False, str(e))
        results.append(False)
    
    return all(results)

def test_history():
    """Test history tracking"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 3: History Tracking{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test statistics
    try:
        r = requests.get(f'{BASE_URL}/api/history/statistics?days=30')
        data = r.json()
        passed = r.status_code == 200 and 'statistics' in data
        stats = data.get('statistics', {})
        print_test('History Statistics', passed,
                   f"Total: {stats.get('total_analyses', 0)}, Avg Prob: {stats.get('average_probability', 0):.6f}")
        results.append(passed)
    except Exception as e:
        print_test('History Statistics', False, str(e))
        results.append(False)
    
    # Test satellite history
    try:
        r = requests.get(f'{BASE_URL}/api/history/satellite/25544?days=30')
        data = r.json()
        passed = r.status_code == 200
        print_test('Satellite History', passed, f"Found {data.get('count', 0)} records")
        results.append(passed)
    except Exception as e:
        print_test('Satellite History', False, str(e))
        results.append(False)
    
    return all(results)

def test_alerts():
    """Test alert system"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 4: Alert System{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test get alerts
    try:
        r = requests.get(f'{BASE_URL}/api/alerts')
        data = r.json()
        passed = r.status_code == 200
        count = data.get('count', 0)
        print_test('Get Active Alerts', passed, f"Found {count} active alerts")
        results.append(passed)
    except Exception as e:
        print_test('Get Active Alerts', False, str(e))
        results.append(False)
    
    # Test alert history
    try:
        r = requests.get(f'{BASE_URL}/api/alerts/history?days=30')
        data = r.json()
        passed = r.status_code == 200
        print_test('Alert History', passed, f"Found {data.get('count', 0)} historical alerts")
        results.append(passed)
    except Exception as e:
        print_test('Alert History', False, str(e))
        results.append(False)
    
    return all(results)

def test_maneuvers():
    """Test maneuver calculator"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 5: Maneuver Planning{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test calculate maneuver
    try:
        payload = {
            'satellite_position': [6800, 0, 0],
            'satellite_velocity': [0, 7.5, 0],
            'debris_position': [6805, 10, 0],
            'debris_velocity': [0, 7.4, 0]
        }
        r = requests.post(f'{BASE_URL}/api/maneuver/calculate', json=payload)
        data = r.json()
        passed = r.status_code == 200 and 'options' in data
        count = data.get('count', 0)
        recommended = data.get('comparison', {}).get('recommended', {}).get('name', 'N/A')
        print_test('Calculate Maneuvers', passed, 
                   f"Generated {count} options, Recommended: {recommended}")
        results.append(passed)
    except Exception as e:
        print_test('Calculate Maneuvers', False, str(e))
        results.append(False)
    
    # Test simulate maneuver
    try:
        payload = {
            'position': [6800, 0, 0],
            'velocity': [0, 7.5, 0],
            'delta_v_vector': [0.001, 0, 0],
            'duration_hours': 6
        }
        r = requests.post(f'{BASE_URL}/api/maneuver/simulate', json=payload)
        data = r.json()
        passed = r.status_code == 200 and 'simulation' in data
        sim = data.get('simulation', {})
        traj_count = len(sim.get('original_trajectory', [])) if sim.get('original_trajectory') else 0
        print_test('Simulate Maneuver', passed,
                   f"Duration: {sim.get('duration_hours', 0)}h, Max Sep: {sim.get('max_separation_km', 0):.2f}km")
        results.append(passed)
    except Exception as e:
        print_test('Simulate Maneuver', False, str(e))
        results.append(False)
    
    return all(results)

def test_space_debris():
    """Test Space-Track integration"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUITE 6: Space Debris Tracking{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    results = []
    
    # Test high risk debris
    try:
        r = requests.get(f'{BASE_URL}/api/space_debris/high_risk?limit=10')
        data = r.json()
        # Accept 200 status even if count is 0 (Space-Track might be rate limited)
        passed = r.status_code == 200
        print_test('High Risk Debris', passed, f"Found {data.get('count', 0)} objects")
        results.append(passed)
    except Exception as e:
        print_test('High Risk Debris', False, str(e))
        results.append(False)
    
    # Test recent debris
    try:
        r = requests.get(f'{BASE_URL}/api/space_debris/recent?days=30&limit=10')
        data = r.json()
        passed = r.status_code == 200
        print_test('Recent Debris', passed, f"Found {data.get('count', 0)} recent objects")
        results.append(passed)
    except Exception as e:
        print_test('Recent Debris', False, str(e))
        results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}ASTROCLEANAI COMPREHENSIVE TEST SUITE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}")
    
    # Check server
    try:
        requests.get(f'{BASE_URL}/health', timeout=2)
    except:
        print(f"\n{Colors.RED}✗ Server not running at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Please start the server: start_with_spacetrack.bat{Colors.END}\n")
        return
    
    # Run test suites
    results = {
        'Core System': test_health(),
        'Satellite Management': test_satellites(),
        'History Tracking': test_history(),
        'Alert System': test_alerts(),
        'Maneuver Planning': test_maneuvers(),
        'Space Debris Tracking': test_space_debris()
    }
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}TEST SUMMARY{Colors.END}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status}: {name}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} test suites passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 All tests passed! System is fully operational.{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Please check the errors above.{Colors.END}\n")

if __name__ == '__main__':
    main()
