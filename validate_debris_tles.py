"""
Validate Debris TLE Data
Checks which debris objects have valid, propagatable TLE data
"""

import sqlite3
from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta

def validate_debris_tles():
    """Check which debris have valid TLE data that can be propagated"""
    
    # Connect to database
    db_path = 'data/astrocleanai.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all debris with TLE data
    cursor.execute("""
        SELECT norad_id, name, tle_line1, tle_line2 
        FROM debris 
        WHERE tle_line1 IS NOT NULL AND tle_line2 IS NOT NULL
    """)
    debris_list = cursor.fetchall()
    
    print(f"\n{'='*70}")
    print(f"VALIDATING DEBRIS TLE DATA")
    print(f"{'='*70}")
    print(f"Found {len(debris_list)} debris objects with TLE data")
    print(f"Testing propagation validity...")
    print(f"{'='*70}\n")
    
    ts = load.timescale()
    now = ts.now()
    future = ts.utc(datetime.utcnow() + timedelta(hours=24))
    
    valid_count = 0
    invalid_count = 0
    invalid_debris = []
    
    for norad_id, name, tle1, tle2 in debris_list:
        try:
            # Try to create satellite and propagate
            satellite = EarthSatellite(tle1, tle2, name, ts)
            
            # Test propagation at current time
            geocentric = satellite.at(now)
            position = geocentric.position.km
            
            # Test propagation 24 hours ahead
            geocentric_future = satellite.at(future)
            position_future = geocentric_future.position.km
            
            # Check if positions are reasonable (not NaN, within Earth orbit range)
            if (all(abs(p) < 100000 for p in position) and 
                all(abs(p) < 100000 for p in position_future)):
                valid_count += 1
                print(f"✓ {name} (NORAD: {norad_id})")
            else:
                invalid_count += 1
                invalid_debris.append((norad_id, name, "Position out of range"))
                print(f"✗ {name} (NORAD: {norad_id}) - Position out of range")
                
        except Exception as e:
            invalid_count += 1
            invalid_debris.append((norad_id, name, str(e)))
            print(f"✗ {name} (NORAD: {norad_id}) - {str(e)[:50]}")
    
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"VALIDATION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Valid TLEs: {valid_count} debris objects")
    print(f"✗ Invalid TLEs: {invalid_count} debris objects")
    print(f"{'='*70}\n")
    
    if invalid_debris:
        print("Invalid Debris Objects:")
        for norad_id, name, reason in invalid_debris[:20]:  # Show first 20
            print(f"  - {name} (NORAD: {norad_id}): {reason[:60]}")
        if len(invalid_debris) > 20:
            print(f"  ... and {len(invalid_debris) - 20} more")
    
    return valid_count, invalid_count

if __name__ == '__main__':
    validate_debris_tles()
