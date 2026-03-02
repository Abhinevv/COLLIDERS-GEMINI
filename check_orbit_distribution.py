"""
Check the actual orbital distribution of satellites and debris
to understand why no matches are found
"""

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject
import math

def check_orbits():
    """Check orbital distribution"""
    
    print("=" * 80)
    print("ORBITAL DISTRIBUTION CHECK")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get satellites
        satellites = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line2.isnot(None)
        ).all()
        
        # Get debris
        debris_list = session.query(DebrisObject).filter(
            DebrisObject.apogee_km.isnot(None),
            DebrisObject.perigee_km.isnot(None)
        ).all()
        
        print(f"\nSatellites with TLEs: {len(satellites)}")
        print(f"Debris with orbital params: {len(debris_list)}")
        
        # Analyze satellite orbits
        print("\n" + "=" * 80)
        print("SATELLITE ORBITS (Sample of 10)")
        print("=" * 80)
        
        for sat in satellites[:10]:
            try:
                # Extract inclination
                sat_inc = float(sat.tle_line2[8:16].strip())
                
                # Extract mean motion
                mean_motion_str = sat.tle_line2[52:63].strip()
                mean_motion = float(mean_motion_str)
                
                # Calculate altitude
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400
                GM = 398600.4418
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                sat_alt = semi_major_axis - 6371
                
                print(f"{sat.name[:40]:40s} Alt: {sat_alt:7.0f} km  Inc: {sat_inc:6.2f}°")
                
            except Exception as e:
                print(f"{sat.name[:40]:40s} Error: {e}")
        
        # Analyze debris orbits
        print("\n" + "=" * 80)
        print("DEBRIS ORBITS (Sample of 10)")
        print("=" * 80)
        
        for debris in debris_list[:10]:
            deb_alt = (debris.apogee_km + debris.perigee_km) / 2
            deb_inc = debris.inclination_deg
            print(f"{debris.name[:40]:40s} Alt: {deb_alt:7.0f} km  Inc: {deb_inc:6.2f}°")
        
        # Calculate ranges
        print("\n" + "=" * 80)
        print("ORBITAL RANGES")
        print("=" * 80)
        
        sat_alts = []
        sat_incs = []
        for sat in satellites:
            try:
                sat_inc = float(sat.tle_line2[8:16].strip())
                mean_motion = float(sat.tle_line2[52:63].strip())
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400
                GM = 398600.4418
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                sat_alt = semi_major_axis - 6371
                sat_alts.append(sat_alt)
                sat_incs.append(sat_inc)
            except:
                continue
        
        deb_alts = [(d.apogee_km + d.perigee_km) / 2 for d in debris_list]
        deb_incs = [d.inclination_deg for d in debris_list]
        
        print("\nSATELLITES:")
        print(f"  Altitude: {min(sat_alts):.0f} - {max(sat_alts):.0f} km")
        print(f"  Inclination: {min(sat_incs):.1f}° - {max(sat_incs):.1f}°")
        
        print("\nDEBRIS:")
        print(f"  Altitude: {min(deb_alts):.0f} - {max(deb_alts):.0f} km")
        print(f"  Inclination: {min(deb_incs):.1f}° - {max(deb_incs):.1f}°")
        
        # Check for overlap
        print("\n" + "=" * 80)
        print("OVERLAP ANALYSIS")
        print("=" * 80)
        
        sat_alt_min, sat_alt_max = min(sat_alts), max(sat_alts)
        deb_alt_min, deb_alt_max = min(deb_alts), max(deb_alts)
        
        alt_overlap = not (sat_alt_max < deb_alt_min or deb_alt_max < sat_alt_min)
        
        print(f"\nAltitude overlap: {'YES' if alt_overlap else 'NO'}")
        if alt_overlap:
            overlap_min = max(sat_alt_min, deb_alt_min)
            overlap_max = min(sat_alt_max, deb_alt_max)
            print(f"  Overlap range: {overlap_min:.0f} - {overlap_max:.0f} km")
        
        sat_inc_min, sat_inc_max = min(sat_incs), max(sat_incs)
        deb_inc_min, deb_inc_max = min(deb_incs), max(deb_incs)
        
        inc_overlap = not (sat_inc_max < deb_inc_min or deb_inc_max < sat_inc_min)
        
        print(f"\nInclination overlap: {'YES' if inc_overlap else 'NO'}")
        if inc_overlap:
            overlap_min = max(sat_inc_min, deb_inc_min)
            overlap_max = min(sat_inc_max, deb_inc_max)
            print(f"  Overlap range: {overlap_min:.1f}° - {overlap_max:.1f}°")
        
        if not alt_overlap or not inc_overlap:
            print("\n⚠ WARNING: Satellites and debris are in completely different orbits!")
            print("This is why no close pairs are found.")
            print("\nRecommendation: Add debris in satellite orbital regions:")
            print(f"  - LEO debris at {sat_alt_min:.0f}-{sat_alt_max:.0f} km altitude")
            print(f"  - With inclinations {sat_inc_min:.1f}°-{sat_inc_max:.1f}°")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_orbits()
