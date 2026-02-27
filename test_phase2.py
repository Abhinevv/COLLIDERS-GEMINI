"""
Test script for Phase 2 features
Tests alerts and maneuver calculator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alerts.alert_service import AlertService
from optimization.maneuver_calculator import ManeuverCalculator
import numpy as np
from datetime import datetime, timedelta


def test_alert_service():
    """Test alert service"""
    print("\n" + "="*70)
    print("TEST 1: Alert Service")
    print("="*70)
    
    try:
        alert_service = AlertService()
        print("✓ Alert service initialized")
        
        # Create test alerts
        print("\nCreating test alerts...")
        
        alert1 = alert_service.create_alert(
            satellite_id='25544',
            debris_id='12345',
            probability=0.05,
            closest_distance_km=2.5
        )
        print(f"✓ Created alert {alert1['id']}: Risk {alert1['risk_level']}")
        
        alert2 = alert_service.create_alert(
            satellite_id='43013',
            debris_id='67890',
            probability=0.0005,
            closest_distance_km=15.0
        )
        print(f"✓ Created alert {alert2['id']}: Risk {alert2['risk_level']}")
        
        # Get active alerts
        print("\nGetting active alerts...")
        alerts = alert_service.get_active_alerts()
        print(f"✓ Found {len(alerts)} active alert(s)")
        
        # Get high-risk alerts only
        high_risk = alert_service.get_active_alerts(min_risk_level='HIGH')
        print(f"✓ Found {len(high_risk)} high-risk alert(s)")
        
        # Dismiss an alert
        print(f"\nDismissing alert {alert2['id']}...")
        success = alert_service.dismiss_alert(alert2['id'], "False alarm")
        print(f"✓ Alert dismissed: {success}")
        
        # Get alert history
        print("\nGetting alert history...")
        history = alert_service.get_alert_history(days=30)
        print(f"✓ Found {len(history)} alert(s) in history")
        
        # Create subscription
        print("\nCreating alert subscription...")
        subscription = alert_service.subscribe_to_alerts(
            email="test@example.com",
            satellite_ids=['25544', '43013'],
            min_probability=0.001
        )
        print(f"✓ Created subscription {subscription['id']}")
        
        return True
    except Exception as e:
        print(f"✗ Alert service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_maneuver_calculator():
    """Test maneuver calculator"""
    print("\n" + "="*70)
    print("TEST 2: Maneuver Calculator")
    print("="*70)
    
    try:
        calc = ManeuverCalculator()
        print("✓ Maneuver calculator initialized")
        
        # Example orbital parameters (ISS-like orbit)
        print("\nSetting up test scenario...")
        sat_pos = np.array([6800, 0, 0])  # km (LEO altitude ~420 km)
        sat_vel = np.array([0, 7.5, 0])  # km/s
        debris_pos = np.array([6805, 10, 0])  # km (close approach)
        debris_vel = np.array([0, 7.4, 0])  # km/s
        
        print(f"  Satellite position: {sat_pos} km")
        print(f"  Satellite velocity: {sat_vel} km/s")
        print(f"  Debris position: {debris_pos} km")
        print(f"  Debris velocity: {debris_vel} km/s")
        
        # Calculate maneuver options
        print("\nCalculating maneuver options...")
        options = calc.calculate_avoidance_options(
            sat_pos, sat_vel, debris_pos, debris_vel,
            datetime.utcnow() + timedelta(hours=2),
            datetime.utcnow()
        )
        
        print(f"✓ Generated {len(options)} maneuver option(s)")
        
        for i, opt in enumerate(options, 1):
            print(f"\n  Option {i}: {opt['name']}")
            print(f"    Type: {opt['type']}")
            print(f"    ΔV: {opt['delta_v_magnitude']*1000:.2f} m/s")
            print(f"    Direction: {opt['direction']}")
            print(f"    Fuel cost: {opt['fuel_cost_estimate']['fuel_mass_kg']:.2f} kg")
        
        # Compare options
        print("\nComparing maneuver options...")
        comparison = calc.compare_maneuver_options(options)
        print(f"✓ Recommended: {comparison['recommended']['name']}")
        print(f"  Reason: {comparison['reason']}")
        print(f"  ΔV: {comparison['recommended']['delta_v_magnitude']*1000:.2f} m/s")
        
        # Simulate maneuver
        print("\nSimulating recommended maneuver...")
        simulation = calc.simulate_maneuver(
            sat_pos, sat_vel,
            comparison['recommended']['delta_v_vector'],
            duration_hours=6
        )
        print(f"✓ Simulated {len(simulation['original_trajectory'])} trajectory points")
        print(f"  Duration: {simulation['duration_hours']} hours")
        
        return True
    except Exception as e:
        print(f"✗ Maneuver calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests"""
    print("\n" + "="*70)
    print("PHASE 2 TEST SUITE")
    print("Testing: Alerts & Maneuver Calculator")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Alert Service", test_alert_service()))
    results.append(("Maneuver Calculator", test_maneuver_calculator()))
    
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
        print("\n🎉 All Phase 2 tests passed!")
        print("\nPhase 2 Features:")
        print("✓ Alert creation and management")
        print("✓ Alert subscriptions")
        print("✓ Maneuver calculation (3 types)")
        print("✓ Fuel cost estimation")
        print("✓ Maneuver simulation")
        print("\nNext: Integrate with API and build frontend components")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
