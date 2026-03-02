"""
Analyze satellite orbital distribution from TLE data
Shows which orbits contain the most satellites
"""

from database.db_manager import get_db_manager
from database.models import Satellite
import math
import re

def parse_tle_mean_motion(tle_line2):
    """Extract mean motion from TLE line 2"""
    # Mean motion is in columns 52-63
    # Format: nn.nnnnnnnn (revolutions per day)
    mean_motion_str = tle_line2[52:63].strip()
    # Remove any trailing characters after the number
    mean_motion_str = re.match(r'[\d.]+', mean_motion_str).group()
    return float(mean_motion_str)

def parse_tle_inclination(tle_line2):
    """Extract inclination from TLE line 2"""
    # Inclination is in columns 8-16
    # Format: nnn.nnnn (degrees)
    inclination_str = tle_line2[8:16].strip()
    return float(inclination_str)

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
        # Get all satellites with TLE data
        satellites = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line2.isnot(None)
        ).all()
        
        print(f"\nTotal satellites with TLE data: {len(satellites)}")
        
        if len(satellites) == 0:
            print("\nNo satellites found!")
            return
        
        orbit_distribution = {}
        altitude_list = []
        inclination_list = []
        successful = 0
        failed = 0
        
        print("\nAnalyzing orbital parameters...")
        
        for sat in satellites:
            try:
                # Parse TLE
                mean_motion = parse_tle_mean_motion(sat.tle_line2)
                inclination = parse_tle_inclination(sat.tle_line2)
                
                # Calculate semi-major axis using Kepler's third law
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400
                GM = 398600.4418  # km^3/s^2
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                
                # Calculate altitude
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
                failed += 1
                continue
        
        print(f"Successfully analyzed: {successful} satellites")
        print(f"Failed to parse: {failed} satellites")
        
        if successful == 0:
            print("\nNo satellites could be analyzed!")
            return
        
        # Display results
        print("\n" + "=" * 80)
        print("ORBITAL DISTRIBUTION SUMMARY")
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
                print(f"    - {sat['name']} (NORAD {sat['norad_id']}): {sat['altitude']:.0f} km, {sat['inclination']:.1f}°")
        
        # Overall statistics
        print("\n" + "=" * 80)
        print("OVERALL STATISTICS")
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
        
        # Satellite types in each orbit
        print("\n" + "=" * 80)
        print("SATELLITE TYPES BY ORBIT")
        print("=" * 80)
        for orbit_type, sats in sorted_orbits[:3]:  # Top 3 orbits
            print(f"\n{orbit_type}:")
            types = {}
            for sat in sats:
                sat_type = sat['type'] or "Unknown"
                types[sat_type] = types.get(sat_type, 0) + 1
            for sat_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {sat_type}: {count}")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze_satellites()
