"""
Test script to find close satellite-debris pairs
Uses database TLE data instead of files
"""

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject
from skyfield.api import load, EarthSatellite
from datetime import datetime
import numpy as np

def test_close_pairs():
    """Test finding close pairs using database TLEs"""
    
    print("=" * 80)
    print("TESTING CLOSE PAIR DETECTION")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get satellites with TLEs
        satellites = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line2.isnot(None)
        ).all()
        
        # Get debris with TLEs
        debris_list = session.query(DebrisObject).filter(
            DebrisObject.tle_line1.isnot(None),
            DebrisObject.tle_line2.isnot(None)
        ).all()
        
        print(f"\nSatellites with TLEs: {len(satellites)}")
        print(f"Debris with TLEs: {len(debris_list)}")
        
        if len(satellites) == 0:
            print("\n✗ No satellites have TLE data!")
            return
        
        if len(debris_list) == 0:
            print("\n✗ No debris have TLE data!")
            return
        
        # Load timescale
        ts = load.timescale()
        t = ts.now()
        
        print(f"\nChecking distances at {t.utc_iso()}...")
        print("Threshold: 100km (realistic for collision analysis)")
        
        close_pairs = []
        checked = 0
        errors = 0
        
        # Check first 5 satellites against all debris
        for sat in satellites[:5]:
            try:
                # Create satellite object
                sat_obj = EarthSatellite(sat.tle_line1, sat.tle_line2, sat.name, ts)
                sat_pos = sat_obj.at(t)
                sat_geocentric = sat_pos.position.km
                
                print(f"\n{sat.name}:")
                print(f"  Position: {sat_geocentric}")
                
                for debris in debris_list[:20]:  # Check against first 20 debris
                    try:
                        # Create debris object
                        deb_obj = EarthSatellite(debris.tle_line1, debris.tle_line2, debris.name, ts)
                        deb_pos = deb_obj.at(t)
                        deb_geocentric = deb_pos.position.km
                        
                        # Calculate distance
                        distance = np.linalg.norm(sat_geocentric - deb_geocentric)
                        
                        checked += 1
                        
                        if distance < 100:  # Within 100km
                            close_pairs.append({
                                'satellite': sat.name,
                                'debris': debris.name,
                                'distance_km': distance
                            })
                            print(f"  ✓ Close to {debris.name}: {distance:.1f} km")
                        
                    except Exception as e:
                        errors += 1
                        if errors <= 3:
                            print(f"  ✗ Error with {debris.name}: {e}")
                
            except Exception as e:
                print(f"✗ Error with {sat.name}: {e}")
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Pairs checked: {checked}")
        print(f"Errors: {errors}")
        print(f"Close pairs found (< 100km): {len(close_pairs)}")
        
        if close_pairs:
            print("\nClosest pairs:")
            sorted_pairs = sorted(close_pairs, key=lambda x: x['distance_km'])
            for pair in sorted_pairs[:10]:
                print(f"  {pair['satellite']} <-> {pair['debris']}: {pair['distance_km']:.1f} km")
        else:
            print("\n⚠ No close pairs found within 100km")
            print("\nThis is normal! Satellites and debris are usually far apart.")
            print("Collision analysis should use:")
            print("  1. Orbital filtering (same altitude ±200km, similar inclination)")
            print("  2. Time-based closest approach calculation")
            print("  3. Monte Carlo simulation for probability")
        
    finally:
        session.close()

if __name__ == "__main__":
    test_close_pairs()
