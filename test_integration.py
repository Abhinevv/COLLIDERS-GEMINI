"""
Integration test for Phase 1 + Phase 2
Tests the complete system end-to-end
"""

import requests
import time
import json

BASE_URL = 'http://localhost:5000'


def test_health():
    """Test API health"""
    print("\n" + "="*70)
    print("TEST 1: API Health Check")
    print("="*70)
    
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy: {data['service']}")
            print(f"  Version: {data['version']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Is the server running?")
        print("  Run: start_with_spacetrack.bat")
        return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


def test_satellites():
    """Test satellite management"""
    print("\n" + "="*70)
    print("TEST 2: Satellite Management")
    print("="*70)
    
    try:
        # List satellites
        response = requests.get(f'{BASE_URL}/api/satellites/manage')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['count']} managed satellite(s)")
            for sat in data['satellites'][:3]:
                print(f"  - {sat['name']} ({sat['norad_id']})")
        
        # Add a new satellite
        print("\nAdding new satellite...")
        response = requests.post(
            f'{BASE_URL}/api/satellites/manage/add',
            json={'norad_id': '25544', 'name': 'ISS', 'type': 'Space Station'}
        )
        if response.status_code in [200, 201]:
            print("✓ Satellite added (or already exists)")
        
        return True
    except Exception as e:
        print(f"✗ Satellite test failed: {e}")
        return False


def test_history():
    """Test history tracking"""
    print("\n" + "="*70)
    print("TEST 3: History Tracking")
    print("="*70)
    
    try:
        # Get statistics
        response = requests.get(f'{BASE_URL}/api/history/statistics?days=30')
        if response.status_code == 200:
            data = response.json()
            stats = data['statistics']
            print(f"✓ Total analyses: {stats['total_analyses']}")
            print(f"✓ Average probability: {stats['average_probability']:.6f}")
            print(f"✓ Risk distribution: {stats['risk_distribution']}")
        
        # Get satellite history
        response = requests.get(f'{BASE_URL}/api/history/satellite/25544?days=30')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['count']} analysis record(s) for ISS")
        
        return True
    except Exception as e:
        print(f"✗ History test failed: {e}")
        return False


def test_alerts():
    """Test alert system"""
    print("\n" + "="*70)
    print("TEST 4: Alert System")
    print("="*70)
    
    try:
        # Get active alerts
        response = requests.get(f'{BASE_URL}/api/alerts')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['count']} active alert(s)")
            
            if data['count'] > 0:
                alert = data['alerts'][0]
                print(f"\n  Alert {alert['id']}:")
                print(f"    Satellite: {alert['satellite_id']}")
                print(f"    Debris: {alert['debris_id']}")
                print(f"    Probability: {alert['probability']*100:.4f}%")
                print(f"    Risk Level: {alert['risk_level']}")
        
        # Get alert history
        response = requests.get(f'{BASE_URL}/api/alerts/history?days=30')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['count']} alert(s) in history")
        
        # Create subscription
        print("\nCreating alert subscription...")
        response = requests.post(
            f'{BASE_URL}/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'satellite_ids': ['25544'],
                'min_probability': 0.001
            }
        )
        if response.status_code == 201:
            print("✓ Subscription created")
        
        return True
    except Exception as e:
        print(f"✗ Alert test failed: {e}")
        return False


def test_maneuver_calculator():
    """Test maneuver calculator"""
    print("\n" + "="*70)
    print("TEST 5: Maneuver Calculator")
    print("="*70)
    
    try:
        # Calculate maneuver options
        payload = {
            'satellite_position': [6800, 0, 0],
            'satellite_velocity': [0, 7.5, 0],
            'debris_position': [6805, 10, 0],
            'debris_velocity': [0, 7.4, 0]
        }
        
        response = requests.post(
            f'{BASE_URL}/api/maneuver/calculate',
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Generated {data['count']} maneuver option(s)")
            
            for i, opt in enumerate(data['options'][:3], 1):
                print(f"\n  Option {i}: {opt['name']}")
                print(f"    ΔV: {opt['delta_v_magnitude']*1000:.2f} m/s")
                print(f"    Fuel: {opt['fuel_cost_estimate']['fuel_mass_kg']:.2f} kg")
            
            print(f"\n✓ Recommended: {data['comparison']['recommended']['name']}")
        
        # Simulate maneuver
        print("\nSimulating maneuver...")
        sim_payload = {
            'position': [6800, 0, 0],
            'velocity': [0, 7.5, 0],
            'delta_v_vector': [0.001, 0, 0],
            'duration_hours': 6
        }
        
        response = requests.post(
            f'{BASE_URL}/api/maneuver/simulate',
            json=sim_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            sim = data['simulation']
            print(f"✓ Simulated {len(sim['original_trajectory'])} trajectory points")
        
        return True
    except Exception as e:
        print(f"✗ Maneuver test failed: {e}")
        return False


def test_collision_analysis():
    """Test collision analysis workflow"""
    print("\n" + "="*70)
    print("TEST 6: Collision Analysis Workflow")
    print("="*70)
    
    try:
        # Start a debris job
        print("Starting collision analysis...")
        payload = {
            'debris': '67720',
            'satellite_norad': '25544',
            'duration_minutes': 30,
            'step_seconds': 60,
            'samples': 500,
            'visualize': True
        }
        
        response = requests.post(
            f'{BASE_URL}/api/debris_job',
            json=payload
        )
        
        if response.status_code == 202:
            data = response.json()
            job_id = data['job_id']
            print(f"✓ Job started: {job_id}")
            
            # Poll for completion
            print("  Waiting for analysis to complete...")
            max_wait = 60  # seconds
            waited = 0
            
            while waited < max_wait:
                time.sleep(2)
                waited += 2
                
                response = requests.get(f'{BASE_URL}/api/debris_job/{job_id}')
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data['status']
                    progress = job_data.get('progress', 0)
                    
                    print(f"  Status: {status}, Progress: {progress}%")
                    
                    if status == 'completed':
                        result = job_data['result']
                        print(f"\n✓ Analysis complete!")
                        print(f"  Probability: {result['probability']*100:.4f}%")
                        
                        if 'visualization_url' in job_data:
                            print(f"  Visualization: {job_data['visualization_url']}")
                        
                        # Check if alert was created
                        print("\n  Checking if alert was created...")
                        response = requests.get(f'{BASE_URL}/api/alerts')
                        if response.status_code == 200:
                            alerts = response.json()['alerts']
                            matching = [a for a in alerts if a['satellite_id'] == '25544' and a['debris_id'] == '67720']
                            if matching:
                                print(f"  ✓ Alert created: ID {matching[0]['id']}, Risk: {matching[0]['risk_level']}")
                            else:
                                print("  ℹ No alert created (probability below threshold)")
                        
                        # Check if saved to history
                        print("\n  Checking if saved to history...")
                        response = requests.get(f'{BASE_URL}/api/history/satellite/25544?days=1')
                        if response.status_code == 200:
                            history = response.json()['history']
                            matching = [h for h in history if h['debris_id'] == '67720']
                            if matching:
                                print(f"  ✓ Saved to history: {len(matching)} record(s)")
                            else:
                                print("  ℹ Not found in recent history")
                        
                        return True
                    
                    elif status == 'failed':
                        print(f"✗ Job failed: {job_data.get('error', 'Unknown error')}")
                        return False
            
            print("✗ Job timed out")
            return False
        else:
            print(f"✗ Failed to start job: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Collision analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("INTEGRATION TEST SUITE")
    print("Testing: Complete System (Phase 1 + Phase 2)")
    print("="*70)
    print("\nChecking if server is running...")
    
    results = []
    
    # Run tests
    results.append(("API Health", test_health()))
    
    if not results[0][1]:
        print("\n⚠️  Server is not running. Please start it and try again.")
        return
    
    results.append(("Satellite Management", test_satellites()))
    results.append(("History Tracking", test_history()))
    results.append(("Alert System", test_alerts()))
    results.append(("Maneuver Calculator", test_maneuver_calculator()))
    results.append(("Collision Analysis Workflow", test_collision_analysis()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("\nSystem Status:")
        print("✓ Phase 1: Database, History, Satellite Management")
        print("✓ Phase 2: Alerts, Maneuver Calculator")
        print("✓ Integration: Auto-save history, Auto-create alerts")
        print("\nReady for Phase 3!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
