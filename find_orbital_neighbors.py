"""
Find satellite-debris pairs in similar orbits (orbital neighbors)
This is more useful than instantaneous distance for collision analysis
"""

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject

def find_orbital_neighbors(max_satellites=50, altitude_threshold_km=200, inclination_threshold_deg=20):
    """
    Find satellites with debris in similar orbits
    
    Args:
        max_satellites: Maximum number of satellites to return
        altitude_threshold_km: Altitude difference threshold
        inclination_threshold_deg: Inclination difference threshold
        
    Returns:
        List of (satellite, debris_list) tuples for top satellites
    """
    
    print("=" * 80)
    print("FINDING ORBITAL NEIGHBORS")
    print("=" * 80)
    print(f"Altitude threshold: ±{altitude_threshold_km} km")
    print(f"Inclination threshold: ±{inclination_threshold_deg}°")
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get satellites with TLEs
        satellites = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line2.isnot(None)
        ).all()
        
        # Get debris with orbital parameters
        debris_list = session.query(DebrisObject).filter(
            DebrisObject.apogee_km.isnot(None),
            DebrisObject.perigee_km.isnot(None),
            DebrisObject.inclination_deg.isnot(None)
        ).all()
        
        print(f"\nSatellites: {len(satellites)}")
        print(f"Debris: {len(debris_list)}")
        
        satellite_neighbors = []
        
        for sat in satellites:
            try:
                # Extract satellite orbital parameters from TLE
                # Line 2: inclination is at positions 8-16
                sat_inc = float(sat.tle_line2[8:16].strip())
                
                # Calculate mean motion from TLE line 2 (positions 52-63)
                mean_motion_str = sat.tle_line2[52:63].strip()
                mean_motion = float(mean_motion_str)
                
                # Calculate altitude from mean motion
                # Using Kepler's third law
                import math
                n_rad_per_sec = mean_motion * 2 * math.pi / 86400
                GM = 398600.4418  # km^3/s^2
                semi_major_axis = (GM / (n_rad_per_sec ** 2)) ** (1/3)
                sat_alt = semi_major_axis - 6371
                
                # Find debris in similar orbits
                close_debris = []
                
                for debris in debris_list:
                    deb_alt = (debris.apogee_km + debris.perigee_km) / 2
                    deb_inc = debris.inclination_deg
                    
                    alt_diff = abs(sat_alt - deb_alt)
                    inc_diff = abs(sat_inc - deb_inc)
                    
                    if alt_diff < altitude_threshold_km and inc_diff < inclination_threshold_deg:
                        close_debris.append({
                            'debris': {
                                'norad_id': debris.norad_id,
                                'name': debris.name
                            },
                            'altitude_diff_km': alt_diff,
                            'inclination_diff_deg': inc_diff
                        })
                
                if close_debris:
                    satellite_neighbors.append({
                        'satellite': {
                            'norad_id': sat.norad_id,
                            'name': sat.name
                        },
                        'close_debris': close_debris,
                        'count': len(close_debris)
                    })
                    
                    if len(satellite_neighbors) <= 5:
                        print(f"  {sat.name}: {len(close_debris)} orbital neighbors")
                
            except Exception as e:
                continue
        
        # Sort by debris count
        satellite_neighbors.sort(key=lambda x: x['count'], reverse=True)
        
        # Take top N
        top_satellites = satellite_neighbors[:max_satellites]
        
        total_pairs = sum(s['count'] for s in top_satellites)
        
        print(f"\n✓ Found {len(top_satellites)} satellites with orbital neighbors")
        print(f"✓ Total pairs to analyze: {total_pairs}")
        
        return top_satellites
        
    finally:
        session.close()

if __name__ == "__main__":
    results = find_orbital_neighbors(max_satellites=50)
    
    if results:
        print("\nTop 10 satellites by orbital neighbor count:")
        for i, item in enumerate(results[:10], 1):
            print(f"{i}. {item['satellite']['name']}: {item['count']} neighbors")
    else:
        print("\nNo orbital neighbors found")
