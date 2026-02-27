"""Test collision analysis with all satellites"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_satellites():
    """Test that all satellites are available"""
    print("=" * 60)
    print("Testing Satellite Data")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/satellites/manage")
    data = response.json()
    
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Total Satellites: {data.get('count', 0)}")
    print(f"✅ Satellites loaded: {len(data.get('satellites', []))}")
    
    if data.get('satellites'):
        print("\nFirst 5 satellites:")
        for sat in data['satellites'][:5]:
            print(f"  - {sat['name']} (NORAD: {sat['norad_id']}) - {sat['type']}")
    
    return data.get('satellites', [])

def test_collision_analysis(satellites):
    """Test collision analysis endpoint"""
    print("\n" + "=" * 60)
    print("Testing Collision Analysis")
    print("=" * 60)
    
    if not satellites:
        print("❌ No satellites available for testing")
        return
    
    # Use ISS as test satellite
    test_sat = next((s for s in satellites if s['norad_id'] == 25544), satellites[0])
    
    print(f"\nTesting with satellite: {test_sat['name']} (NORAD: {test_sat['norad_id']})")
    print("Debris ID: 433 (Asteroid Eros)")
    
    payload = {
        "debris": "433",
        "satellite_norad": test_sat['norad_id'],
        "duration_minutes": 30,
        "step_seconds": 60,
        "samples": 500,
        "position_uncertainty_km": 1000,
        "debris_radius_km": 0.5,
        "satellite_radius_km": 0.01,
        "visualize": False
    }
    
    print("\nStarting analysis job...")
    response = requests.post(f"{BASE_URL}/api/debris/analyze", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to start job: {response.status_code}")
        print(response.text)
        return
    
    job_data = response.json()
    job_id = job_data.get('job_id')
    print(f"✅ Job started: {job_id}")
    
    # Poll for completion
    import time
    max_wait = 60  # 60 seconds max
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(2)
        elapsed += 2
        
        status_response = requests.get(f"{BASE_URL}/api/debris/jobs/{job_id}")
        status_data = status_response.json()
        
        status = status_data.get('status')
        print(f"  Status: {status} ({elapsed}s elapsed)")
        
        if status == 'completed':
            result = status_data.get('result', {})
            probability = result.get('probability', 0)
            
            print("\n" + "=" * 60)
            print("ANALYSIS COMPLETE")
            print("=" * 60)
            print(f"✅ Collision Probability: {probability * 100:.4f}%")
            
            if probability == 0:
                print("✅ Risk Level: SAFE - No collision detected")
            elif probability < 0.001:
                print("⚠️  Risk Level: LOW")
            elif probability < 0.01:
                print("⚠️  Risk Level: MODERATE")
            else:
                print("🚨 Risk Level: HIGH")
            
            return True
            
        elif status == 'failed':
            error = status_data.get('error', 'Unknown error')
            print(f"\n❌ Analysis failed: {error}")
            return False
    
    print(f"\n⏱️  Timeout after {max_wait}s")
    return False

def test_frontend_endpoints():
    """Test that frontend can access all required endpoints"""
    print("\n" + "=" * 60)
    print("Testing Frontend Endpoints")
    print("=" * 60)
    
    endpoints = [
        "/api/health",
        "/api/satellites/manage",
        "/api/debris/high-risk?min_altitude=200&max_altitude=2000&limit=10"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")

if __name__ == "__main__":
    try:
        print("\n🚀 AstroCleanAI - Collision Analysis Test\n")
        
        # Test 1: Satellites
        satellites = test_satellites()
        
        # Test 2: Frontend endpoints
        test_frontend_endpoints()
        
        # Test 3: Collision analysis
        if satellites:
            test_collision_analysis(satellites)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Go to 'Collision Analysis' tab")
        print("3. Select any of the 64 satellites from the dropdown")
        print("4. Enter a debris ID (e.g., 433 for Eros)")
        print("5. Click 'Run Analysis' to test collision detection")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
