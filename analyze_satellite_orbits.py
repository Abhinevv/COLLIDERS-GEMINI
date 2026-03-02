"""
Analyze satellite orbital distribution
Shows which orbits contain the most satellites
"""

import sys
from database.db_manager import get_db_manager
from database.models import Satellite
import math

def classify_orbit(semi_major_axis_km, eccentricity, inclination_deg):
    """
    Classify orbit type based on orbital parameters
    
    Args:
        semi_major_axis_km: Semi-major axis in km
        inclination_deg: Inclination in degrees
        
    Returns:
        Orbit classification string
    """
    altitude_km = semi_major_axis_km - 6371  # Earth radius
    
    # Altitude-based classification
    if altitude_km < 2000:
        altitude_class = "LEO (Low Earth Orbit)"
    elif altitude_km < 35586:
        altitude_class = "MEO (Medium Earth Orbit)"
    elif 35586 <= altitude_km <= 35986:
        altitude_class = "GEO (Geostationary Orbit)"
    else:
        altitude_class = "HEO (High Earth Orbit)"
    
    # Inclination-based classification
    if inclination_deg < 10:
        inclination_class = "Equatorial"
    elif 10 <= inclination_deg < 45:
        inclination_class = "Low Inclination"
    elif 45 <= inclination_deg < 80:
        inclination_class = "Mid Inclination"
    elif 80 <= inclination_deg < 100:
        inclination_class = "Polar"
    else:
        inclination_class = "Retrograde"
    
    return f"{altitude_class} - {inclination_class}"

def analyze_orbits():
    """Analyze and display satellite orbital distribution"""
    
    print("=" * 80)
    print("SATELLITE ORBITAL DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Get database session
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
            print("\nNo satellites found in database!")
            return
        
        # Analyze each satellite
        orbit_distribution = {}
        altitude_list = []
        inclination_list = []
        
        print("\nAnalyzing orbital parameters...")
        
        for sat in satellites:
            try:
                # Extract mean motion from TLE line 2 (columns 52-63)
                mean_motion_str = sat.tle_line2[52:63].strip()
                mean_motion = float(mean_motion_str)  # revolutions per day
                
                # Calculate semi-major axis using Kepler's third law
                # n = sqrt(GM/a^3), where n is mean motion in rad/s
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400  # convert to rad/s
                GM = 398600.4418  # Earth's gravitational parameter (km^3/s^2)
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                
                # Extract inclination from TLE line 2 (columns 8-16)
                inclination_str = sat.tle_line2[8:16].strip()
                inclination = float(inclination_str)
                
                # Extract eccentricity from TLE line 2 (columns 26-33)
                # Format is assumed decimal point, so 1234567 means 0.1234567
                eccentricity_str = sat.tle_line2[26:33].strip()
                eccentricity = float("0." + eccentricity_str) if eccentricity_str else 0.0
                
                # Calculate altitude
                altitude = semi_major_axis - 6371
                
                # Classify orbit
                orbit_type = classify_orbit(semi_major_axis, eccentricity, inclination)
                
                # Store in distribution
                if orbit_type not in orbit_distribution:
                    orbit_distribution[orbit_type] = []
                orbit_distribution[orbit_type].append({
                    'name': sat.name,
                    'norad_id': sat.norad_id,
                    'altitude': altitude,
                    'inclination': inclination
                })
                
                altitude_list.append(altitude)
                inclination_list.append(inclination)
                
            except Exception as e:
                print(f"Error processing {sat.name}: {e}")
                continue
        
        # Display results
        print("\n" + "=" * 80)
        print("ORBITAL DISTRIBUTION SUMMARY")
        print("=" * 80)
        
        # Sort by count
        sorted_orbits = sorted(orbit_distribution.items(), key=lambda x: len(x[1]), reverse=True)
        
        for orbit_type, satellites_in_orbit in sorted_orbits:
            count = len(satellites_in_orbit)
            percentage = (count / len(satellites)) * 100
            print(f"\n{orbit_type}: {count} satellites ({percentage:.1f}%)")
            
            # Show altitude range
            altitudes = [s['altitude'] for s in satellites_in_orbit]
            inclinations = [s['inclination'] for s in satellites_in_orbit]
            print(f"  Altitude range: {min(altitudes):.0f} - {max(altitudes):.0f} km")
            print(f"  Inclination range: {min(inclinations):.1f}° - {max(inclinations):.1f}°")
            
            # Show top 5 satellites in this orbit
            print(f"  Sample satellites:")
            for sat in satellites_in_orbit[:5]:
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
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze_orbits()
