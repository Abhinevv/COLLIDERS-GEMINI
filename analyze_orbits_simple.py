"""
Analyze satellite and debris orbital distribution
Shows which orbits contain the most objects
"""

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject

def classify_orbit_from_params(altitude_km, inclination_deg):
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

def analyze_debris():
    """Analyze debris orbital distribution"""
    
    print("=" * 80)
    print("DEBRIS ORBITAL DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all debris with orbital parameters
        debris_objects = session.query(DebrisObject).filter(
            DebrisObject.apogee_km.isnot(None),
            DebrisObject.perigee_km.isnot(None),
            DebrisObject.inclination_deg.isnot(None)
        ).all()
        
        print(f"\nTotal debris objects with orbital data: {len(debris_objects)}")
        
        if len(debris_objects) == 0:
            print("\nNo debris found with orbital parameters!")
            return
        
        orbit_distribution = {}
        altitude_list = []
        inclination_list = []
        
        for debris in debris_objects:
            # Calculate average altitude
            avg_altitude = (debris.apogee_km + debris.perigee_km) / 2
            inclination = debris.inclination_deg
            
            # Classify orbit
            orbit_type = classify_orbit_from_params(avg_altitude, inclination)
            
            if orbit_type not in orbit_distribution:
                orbit_distribution[orbit_type] = []
            
            orbit_distribution[orbit_type].append({
                'name': debris.name,
                'norad_id': debris.norad_id,
                'altitude': avg_altitude,
                'inclination': inclination,
                'type': debris.type
            })
            
            altitude_list.append(avg_altitude)
            inclination_list.append(inclination)
        
        # Display results
        print("\n" + "=" * 80)
        print("DEBRIS ORBITAL DISTRIBUTION")
        print("=" * 80)
        
        sorted_orbits = sorted(orbit_distribution.items(), key=lambda x: len(x[1]), reverse=True)
        
        for orbit_type, objects in sorted_orbits:
            count = len(objects)
            percentage = (count / len(debris_objects)) * 100
            print(f"\n{orbit_type}: {count} objects ({percentage:.1f}%)")
            
            altitudes = [o['altitude'] for o in objects]
            inclinations = [o['inclination'] for o in objects]
            print(f"  Altitude range: {min(altitudes):.0f} - {max(altitudes):.0f} km")
            print(f"  Inclination range: {min(inclinations):.1f}° - {max(inclinations):.1f}°")
            
            # Show sample objects
            print(f"  Sample objects:")
            for obj in objects[:3]:
                print(f"    - {obj['name']} ({obj['type']}): {obj['altitude']:.0f} km, {obj['inclination']:.1f}°")
        
        # Overall statistics
        print("\n" + "=" * 80)
        print("OVERALL DEBRIS STATISTICS")
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

def analyze_satellites():
    """Analyze satellite count by type"""
    
    print("\n" + "=" * 80)
    print("SATELLITE ANALYSIS")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        satellites = session.query(Satellite).all()
        print(f"\nTotal satellites in database: {len(satellites)}")
        
        # Group by type
        by_type = {}
        for sat in satellites:
            sat_type = sat.type or "Unknown"
            if sat_type not in by_type:
                by_type[sat_type] = []
            by_type[sat_type].append(sat.name)
        
        print("\nSatellites by type:")
        for sat_type, sats in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {sat_type}: {len(sats)} satellites")
            if len(sats) <= 5:
                for name in sats:
                    print(f"    - {name}")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze_debris()
    analyze_satellites()
