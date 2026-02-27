"""Quick integration test - no prompts"""
import requests
import time

BASE_URL = 'http://localhost:5000'

print("\n" + "="*70)
print("QUICK INTEGRATION TEST")
print("="*70)

# Test 1: Health
print("\n1. Testing API Health...")
try:
    r = requests.get(f'{BASE_URL}/health', timeout=5)
    if r.status_code == 200:
        print(f"   ✓ API is healthy")
    else:
        print(f"   ✗ Health check failed: {r.status_code}")
        exit(1)
except Exception as e:
    print(f"   ✗ Cannot connect: {e}")
    print("   Make sure server is running!")
    exit(1)

# Test 2: Satellites
print("\n2. Testing Satellite Management...")
try:
    r = requests.get(f'{BASE_URL}/api/satellites/manage')
    if r.status_code == 200:
        data = r.json()
        print(f"   ✓ Found {data['count']} satellites")
    else:
        print(f"   ✗ Failed: {r.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: History
print("\n3. Testing History...")
try:
    r = requests.get(f'{BASE_URL}/api/history/statistics?days=30')
    if r.status_code == 200:
        data = r.json()
        stats = data['statistics']
        print(f"   ✓ Total analyses: {stats['total_analyses']}")
        print(f"   ✓ Avg probability: {stats['average_probability']:.6f}")
    else:
        print(f"   ✗ Failed: {r.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Alerts
print("\n4. Testing Alerts...")
try:
    r = requests.get(f'{BASE_URL}/api/alerts')
    if r.status_code == 200:
        data = r.json()
        print(f"   ✓ Found {data['count']} active alerts")
    else:
        print(f"   ✗ Failed: {r.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Maneuver Calculator
print("\n5. Testing Maneuver Calculator...")
try:
    payload = {
        'satellite_position': [6800, 0, 0],
        'satellite_velocity': [0, 7.5, 0],
        'debris_position': [6805, 10, 0],
        'debris_velocity': [0, 7.4, 0]
    }
    r = requests.post(f'{BASE_URL}/api/maneuver/calculate', json=payload)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✓ Generated {data['count']} maneuver options")
        print(f"   ✓ Recommended: {data['comparison']['recommended']['name']}")
    else:
        print(f"   ✗ Failed: {r.status_code} - {r.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 6: Collision Analysis
print("\n6. Testing Collision Analysis...")
try:
    payload = {
        'debris': '67720',
        'satellite_norad': '25544',
        'duration_minutes': 30,
        'step_seconds': 60,
        'samples': 500,
        'visualize': True
    }
    
    r = requests.post(f'{BASE_URL}/api/debris_job', json=payload)
    if r.status_code == 202:
        job_id = r.json()['job_id']
        print(f"   ✓ Job started: {job_id}")
        
        # Wait for completion
        for i in range(30):
            time.sleep(2)
            r = requests.get(f'{BASE_URL}/api/debris_job/{job_id}')
            if r.status_code == 200:
                job_data = r.json()
                status = job_data['status']
                progress = job_data.get('progress', 0)
                
                if status == 'completed':
                    result = job_data['result']
                    print(f"   ✓ Analysis complete!")
                    print(f"   ✓ Probability: {result['probability']*100:.4f}%")
                    break
                elif status == 'failed':
                    print(f"   ✗ Job failed: {job_data.get('error')}")
                    break
                elif i % 5 == 0:
                    print(f"   ... Progress: {progress}%")
        else:
            print(f"   ⚠ Job still running after 60s")
    else:
        print(f"   ✗ Failed to start: {r.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70 + "\n")
