"""
Test Space Debris API Endpoints
Run this to verify the new space debris tracking features
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url, params=None):
    """Test an API endpoint"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    print('='*70)
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Status: {response.status_code}")
            print(f"\nResponse Preview:")
            print(json.dumps(data, indent=2)[:500] + "...")
            return True
        else:
            print(f"⚠️  Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("🛰️  ASTROCLEANAI SPACE DEBRIS API TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Health Check
    results.append(test_endpoint(
        "Health Check",
        f"{BASE_URL}/health"
    ))
    
    # Test 2: List Satellites
    results.append(test_endpoint(
        "List Satellites",
        f"{BASE_URL}/api/satellites"
    ))
    
    # Test 3: Search Space Debris (requires Space-Track credentials)
    results.append(test_endpoint(
        "Search Space Debris",
        f"{BASE_URL}/api/space_debris/search",
        params={'type': 'debris', 'limit': 5}
    ))
    
    # Test 4: High-Risk Debris
    results.append(test_endpoint(
        "High-Risk Debris in LEO",
        f"{BASE_URL}/api/space_debris/high_risk",
        params={'altitude_min': 400, 'altitude_max': 600, 'limit': 5}
    ))
    
    # Test 5: Recent Debris
    results.append(test_endpoint(
        "Recently Cataloged Debris",
        f"{BASE_URL}/api/space_debris/recent",
        params={'days': 7, 'limit': 5}
    ))
    
    # Test 6: Specific Debris Details (ISS)
    results.append(test_endpoint(
        "ISS Details",
        f"{BASE_URL}/api/space_debris/25544"
    ))
    
    # Test 7: TLE Data
    results.append(test_endpoint(
        "ISS TLE Data",
        f"{BASE_URL}/api/space_debris/25544/tle"
    ))
    
    # Test 8: Debris Search (asteroids)
    results.append(test_endpoint(
        "Search Asteroids",
        f"{BASE_URL}/api/debris_search",
        params={'q': 'Eros'}
    ))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    elif passed >= total - 2:
        print("\n⚠️  MOSTLY WORKING - Some features may require Space-Track credentials")
        print("   Set SPACETRACK_USER and SPACETRACK_PASS environment variables")
        print("   Get free account at: https://www.space-track.org/auth/createAccount")
    else:
        print("\n❌ MULTIPLE FAILURES - Check if API server is running")
        print("   Start server with: python api.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
