"""
Generate TLE data for debris objects that only have orbital parameters
This allows collision analysis to calculate precise positions
"""

from database.db_manager import get_db_manager
from database.models import DebrisObject
from datetime import datetime
import math

def orbital_params_to_tle(debris):
    """
    Generate approximate TLE from orbital parameters
    Note: This is a simplified TLE generation for testing purposes
    Real TLEs should come from Space-Track.org
    """
    
    # Calculate mean motion from period
    mean_motion = 1440.0 / debris.period_minutes  # revolutions per day
    
    # Calculate eccentricity from apogee and perigee
    earth_radius = 6371.0  # km
    apogee_radius = debris.apogee_km + earth_radius
    perigee_radius = debris.perigee_km + earth_radius
    semi_major_axis = (apogee_radius + perigee_radius) / 2
    eccentricity = (apogee_radius - perigee_radius) / (2 * semi_major_axis)
    
    # Format eccentricity for TLE (remove decimal point)
    ecc_str = f"{int(eccentricity * 10000000):07d}"
    
    # Get current epoch
    now = datetime.utcnow()
    year = now.year % 100  # Last 2 digits
    day_of_year = now.timetuple().tm_yday
    fraction_of_day = (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    epoch = f"{day_of_year:03d}.{int(fraction_of_day * 100000000):08d}"
    
    # Extract NORAD ID (use last 5 digits if longer)
    norad_str = debris.norad_id.replace('DEB-', '').replace('LEO-', '').replace('MEO-', '').replace('GEO-', '').replace('HEO-', '')
    try:
        norad_num = int(''.join(filter(str.isdigit, norad_str)))
        norad_id = norad_num % 100000  # Keep last 5 digits
    except:
        norad_id = hash(debris.norad_id) % 100000
    
    # Generate TLE Line 1
    # Format: 1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N NNNNN
    line1 = (
        f"1 {norad_id:05d}U 00000A   "
        f"{year:02d}{epoch} "
        f" .00000000  00000-0  00000-0 0  9999"
    )
    
    # Generate TLE Line 2
    # Format: 2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
    line2 = (
        f"2 {norad_id:05d} "
        f"{debris.inclination_deg:8.4f} "
        f"000.0000 "  # RAAN (unknown, set to 0)
        f"{ecc_str} "
        f"000.0000 "  # Argument of perigee (unknown, set to 0)
        f"000.0000 "  # Mean anomaly (unknown, set to 0)
        f"{mean_motion:11.8f}00000"
    )
    
    return line1, line2

def add_tles_to_debris():
    """Add TLE data to debris objects that don't have it"""
    
    print("=" * 80)
    print("GENERATING TLE DATA FOR DEBRIS OBJECTS")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all debris objects
        all_debris = session.query(DebrisObject).all()
        print(f"\nTotal debris objects: {len(all_debris)}")
        
        # Check which ones need TLEs
        need_tles = []
        have_params = []
        
        for debris in all_debris:
            if debris.apogee_km and debris.perigee_km and debris.inclination_deg and debris.period_minutes:
                have_params.append(debris)
        
        print(f"Debris with orbital parameters: {len(have_params)}")
        print("\nGenerating TLEs...")
        
        updated = 0
        for debris in have_params:
            try:
                line1, line2 = orbital_params_to_tle(debris)
                
                # Note: DebrisObject model doesn't have TLE fields
                # We need to add them to the model first
                # For now, just print sample
                if updated < 5:
                    print(f"\n{debris.name}:")
                    print(f"  Line 1: {line1}")
                    print(f"  Line 2: {line2}")
                
                updated += 1
                
            except Exception as e:
                print(f"Error processing {debris.name}: {e}")
                continue
        
        print(f"\n✓ Generated TLEs for {updated} debris objects")
        print("\n" + "=" * 80)
        print("NOTE: DebrisObject model needs TLE fields added")
        print("=" * 80)
        print("The model currently has:")
        print("  - apogee_km, perigee_km, inclination_deg, period_minutes")
        print("\nNeeds to add:")
        print("  - tle_line1, tle_line2, tle_epoch")
        print("\nThis will allow collision analysis to calculate positions.")
        
    finally:
        session.close()

if __name__ == "__main__":
    add_tles_to_debris()
