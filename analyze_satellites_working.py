"""
Analyze satellite orbital distribution
Works with the actual TLE format in the database
"""

from database.db_manager import get_db_manager
from database.models import Satellite
import math
import re

def parse_tle(tle_line):
    """
    Parse TLE line to extract orbital parameters
    TLE Line 2 format:
    2 NNNNN III.IIII EEE.EEEE MMM.MMMMMMMM ...
    """
    try:
        parts = tle_line.split()
        
        # Find inclination (should be around position 2-3, format: nn.nnnn)
        inclination = None
        mean_motion = None
        
        for i, part in enumerate(parts):
            # Inclination is typically 0-180 degrees with decimal
            if '.' in part and not any(c in part for c in ['+', '-', 'U', 'A']):
                val = float(part)
                if 0 <= val <= 180 and inclination is None:
                    inclination = val
                # Mean motion is typically 10-16 revs/day for LEO
                elif 0.5 <= val <= 20 and mean_motion is None and inclination is not None:
                    mean_motion = val
        
        return inclination, mean_motion
    except:
        return None, None

def classify_orbit(altitude_km, inclination_deg):
    """Classify orbit based on altitude and inclination"""
    
    # Altitude classification
    if altitude_km < 2000:
        alt_class = "LEO"
    elif altitude_km < 35586:
        alt_class = "MEO"
    elif 35586 <= altitude_km <= 35986:
        alt_class = "GEO"
    else:
        alt_class = "HEO"
    
    # Inclination classification
    if inclination_deg < 10:
        inc_class = "Equatorial"
    elif 10 <= inclination_deg < 45:
        inc_class = "Low-Inc"
    elif 45 <= inclination_deg < 80:
        inc_class = "Mid-Inc"
    elif 80 <= inclination_deg < 100:
        inc_class = "Polar"
    else:
        inc_class = "Retrograde"
    
    return f"{alt_class} - {inc_class}"

def analyze_satellites():
    """Analyze satellite orbital distribution"""
    
    print("=" * 80)
    print("SATELLITE ORBITAL DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all satellites
        satellites = session.query(Satellite).all()
        
        print(f"\nTotal satellites in database: {len(satellites)}")
        
        # Group by type first
        by_type = {}
        for sat in satellites:
            sat_type = sat.type or "Unknown"
            by_type[sat_type] = by_type.get(sat_type, 0) + 1
        
        print("\n" + "=" * 80)
        print("SATELLITES BY TYPE")
        print("=" * 80)
        for sat_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(satellites)) * 100
            print(f"{sat_type}: {count} satellites ({percentage:.1f}%)")
        
        # Now try to analyze orbits from TLE data
        satellites_with_tle = [s for s in satellites if s.tle_line2]
        print(f"\n\nSatellites with TLE data: {len(satellites_with_tle)}")
        
        orbit_distribution = {}
        altitude_list = []
        inclination_list = []
        successful = 0
        
        for sat in satellites_with_tle:
            try:
                inclination, mean_motion = parse_tle(sat.tle_line2)
                
                if inclination is None or mean_motion is None:
                    continue
                
                # Calculate altitude from mean motion
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400
                GM = 398600.4418
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                altitude = semi_major_axis - 6371
                
                # Classify orbit
                orbit_type = classify_orbit(altitude, inclination)
                
                if orbit_type not in orbit_distribution:
                    orbit_distribution[orbit_type] = []
                
                orbit_distribution[orbit_type].append({
                    'name': sat.name,
                    'norad_id': sat.norad_id,
                    'altitude': altitude,
                    'inclination': inclination,
                    'type': sat.type
                })
                
                altitude_list.append(altitude)
                inclination_list.append(inclination)
                successful += 1
                
            except Exception as e:
                continue
        
        print(f"Successfully analyzed orbital parameters: {successful} satellites")
        
        if successful > 0:
            print("\n" + "=" * 80)
            print("ORBITAL DISTRIBUTION")
            print("=" * 80)
            
            sorted_orbits = sorted(orbit_distribution.items(), key=lambda x: len(x[1]), reverse=True)
            
            for orbit_type, sats in sorted_orbits:
                count = len(sats)
                percentage = (count / successful) * 100
                print(f"\n{orbit_type}: {count} satellites ({percentage:.1f}%)")
                
                altitudes = [s['altitude'] for s in sats]
                inclinations = [s['inclination'] for s in sats]
                print(f"  Altitude range: {min(altitudes):.0f} - {max(altitudes):.0f} km")
                print(f"  Inclination range: {min(inclinations):.1f}° - {max(inclinations):.1f}°")
                
                # Show sample satellites
                print(f"  Sample satellites:")
                for sat in sats[:5]:
                    print(f"    - {sat['name']}: {sat['altitude']:.0f} km, {sat['inclination']:.1f}°")
            
            # Overall statistics
            print("\n" + "=" * 80)
            print("OVERALL ORBITAL STATISTICS")
            print("=" * 80)
            print(f"Altitude range: {min(altitude_list):.0f} - {max(altitude_list):.0f} km")
            print(f"Mean altitude: {sum(altitude_list)/len(altitude_list):.0f} km")
            sorted_alt = sorted(altitude_list)
            median_alt = sorted_alt[len(sorted_alt)//2]
            print(f"Median altitude: {median_alt:.0f} km")
            print(f"\nInclination range: {min(inclination_list):.1f}° - {max(inclination_list):.1f}°")
            print(f"Mean inclination: {sum(inclination_list)/len(inclination_list):.1f}°")
            sorted_inc = sorted(inclination_list)
            median_inc = sorted_inc[len(sorted_inc)//2]
            print(f"Median inclination: {median_inc:.1f}°")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze_satellites()
