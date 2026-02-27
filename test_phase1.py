"""
Test script for Phase 1 features
Tests database, history tracking, and satellite management
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_db_manager
from history.history_service import HistoryService
from satellites.satellite_manager import SatelliteManager
from datetime import datetime

def test_database():
    """Test database initialization"""
    print("\n" + "="*70)
    print("TEST 1: Database Initialization")
    print("="*70)
    
    try:
        db_manager = get_db_manager()
        print("✓ Database manager initialized")
        print(f"✓ Database location: {db_manager.db_path}")
        
        # Test session
        session = db_manager.get_session()
        print("✓ Database session created")
        db_manager.close_session(session)
        print("✓ Database session closed")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_satellite_manager():
    """Test satellite management"""
    print("\n" + "="*70)
    print("TEST 2: Satellite Management")
    print("="*70)
    
    try:
        sat_manager = SatelliteManager()
        print("✓ Satellite manager initialized")
        
        # Test adding a satellite
        print("\nAdding ISS (25544)...")
        satellite = sat_manager.add_satellite(
            norad_id='25544',
            name='ISS (ZARYA)',
            sat_type='Space Station',
            description='International Space Station'
        )
        print(f"✓ Added satellite: {satellite['name']}")
        
        # Test getting satellite
        print("\nRetrieving satellite...")
        retrieved = sat_manager.get_satellite('25544')
        print(f"✓ Retrieved: {retrieved['name']}")
        
        # Test listing satellites
        print("\nListing all satellites...")
        all_sats = sat_manager.get_all_satellites()
        print(f"✓ Found {len(all_sats)} satellite(s)")
        for sat in all_sats:
            print(f"  - {sat['name']} ({sat['norad_id']})")
        
        # Test export to JSON
        print("\nExporting to JSON...")
        json_data = sat_manager.export_to_json()
        print(f"✓ Exported {len(json_data)} characters")
        
        # Test export to CSV
        print("\nExporting to CSV...")
        csv_data = sat_manager.export_to_csv()
        print(f"✓ Exported {len(csv_data)} characters")
        
        return True
    except Exception as e:
        print(f"✗ Satellite manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_history_service():
    """Test history tracking"""
    print("\n" + "="*70)
    print("TEST 3: History Tracking")
    print("="*70)
    
    try:
        history = HistoryService()
        print("✓ History service initialized")
        
        # Test saving analysis
        print("\nSaving test analysis...")
        analysis = history.save_analysis(
            satellite_id='25544',
            debris_id='12345',
            probability=0.00123,
            closest_distance_km=5.5,
            duration_minutes=60,
            samples=1000
        )
        print(f"✓ Saved analysis with ID: {analysis['id']}")
        print(f"  - Probability: {analysis['probability']}")
        print(f"  - Risk Level: {analysis['risk_level']}")
        
        # Test retrieving history
        print("\nRetrieving satellite history...")
        sat_history = history.get_satellite_history('25544', days=30)
        print(f"✓ Found {len(sat_history)} analysis record(s)")
        
        # Test statistics
        print("\nGetting statistics...")
        stats = history.get_statistics(days=30)
        print(f"✓ Total analyses: {stats['total_analyses']}")
        print(f"✓ Average probability: {stats['average_probability']:.6f}")
        print(f"✓ Risk distribution: {stats['risk_distribution']}")
        
        # Test export
        print("\nExporting to CSV...")
        csv_data = history.export_to_csv(days=30)
        print(f"✓ Exported {len(csv_data)} characters")
        
        return True
    except Exception as e:
        print(f"✗ History service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between services"""
    print("\n" + "="*70)
    print("TEST 4: Integration Test")
    print("="*70)
    
    try:
        sat_manager = SatelliteManager()
        history = HistoryService()
        
        # Add multiple satellites
        print("\nAdding multiple satellites...")
        satellites = [
            ('25544', 'ISS (ZARYA)', 'Space Station'),
            ('43013', 'HST', 'Space Telescope'),
            ('20580', 'NOAA-19', 'Weather Satellite')
        ]
        
        for norad_id, name, sat_type in satellites:
            try:
                sat_manager.add_satellite(norad_id, name, sat_type)
                print(f"✓ Added: {name}")
            except Exception as e:
                print(f"  (Already exists or error: {e})")
        
        # Save multiple analyses
        print("\nSaving multiple analyses...")
        for sat_id, _, _ in satellites:
            history.save_analysis(
                satellite_id=sat_id,
                debris_id='TEST_DEBRIS',
                probability=0.001,
                duration_minutes=30,
                samples=500
            )
        print(f"✓ Saved {len(satellites)} analyses")
        
        # Get overall statistics
        print("\nGetting overall statistics...")
        stats = history.get_statistics(days=30)
        print(f"✓ Total analyses in database: {stats['total_analyses']}")
        
        # List all satellites
        all_sats = sat_manager.get_all_satellites()
        print(f"✓ Total satellites tracked: {len(all_sats)}")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PHASE 1 TEST SUITE")
    print("Testing: Database, History Tracking, Satellite Management")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Database", test_database()))
    results.append(("Satellite Manager", test_satellite_manager()))
    results.append(("History Service", test_history_service()))
    results.append(("Integration", test_integration()))
    
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
        print("\n🎉 All tests passed! Phase 1 is working correctly.")
        print("\nNext steps:")
        print("1. Install SQLAlchemy: pip install sqlalchemy==2.0.23")
        print("2. Restart your server")
        print("3. Try the new API endpoints")
        print("4. Ready for Phase 2!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
