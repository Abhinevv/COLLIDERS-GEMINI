"""
Find satellite-debris pairs within specified distance threshold.
Used for intelligent Fast Mode analysis.
"""
import numpy as np
from datetime import datetime, timezone
from orbit_propagator import OrbitPropagator
import os
import json

def find_close_pairs(satellites, debris_list, threshold_km=25.0, max_satellites=50):
    """
    Find satellites with debris within threshold distance.
    
    Args:
        satellites: List of satellite dicts with norad_id
        debris_list: List of debris dicts with norad_id
        threshold_km: Distance threshold in km
        max_satellites: Maximum number of satellites to return
        
    Returns:
        List of (satellite, debris_list) tuples for top satellites
    """
    current_time = datetime.now(timezone.utc).replace(tzinfo=None)
    satellite_debris_counts = []
    
    print(f"Screening {len(satellites)} satellites against {len(debris_list)} debris...")
    print(f"Threshold: {threshold_km}km")
    
    for sat in satellites:
        sat_file = f'data/sat_{sat["norad_id"]}.txt'
        if not os.path.exists(sat_file):
            continue
            
        try:
            # Get satellite position at current time
            sat_prop = OrbitPropagator(sat_file)
            sat_traj = sat_prop.propagate_trajectory(current_time, 1, 60)  # 1 minute
            if not sat_traj:
                continue
            sat_pos = np.array(sat_traj[0]['position'])
            
            close_debris = []
            
            for debris in debris_list:
                debris_file = f'data/sat_{debris["norad_id"]}.txt'
                if not os.path.exists(debris_file):
                    continue
                    
                try:
                    # Get debris position at current time
                    debris_prop = OrbitPropagator(debris_file)
                    debris_traj = debris_prop.propagate_trajectory(current_time, 1, 60)
                    if not debris_traj:
                        continue
                    debris_pos = np.array(debris_traj[0]['position'])
                    
                    # Calculate distance
                    distance = np.linalg.norm(sat_pos - debris_pos)
                    
                    if distance <= threshold_km:
                        close_debris.append({
                            'debris': debris,
                            'distance': float(distance)
                        })
                        
                except Exception as e:
                    continue
            
            if close_debris:
                satellite_debris_counts.append({
                    'satellite': sat,
                    'close_debris': close_debris,
                    'count': len(close_debris)
                })
                print(f"  {sat['name']}: {len(close_debris)} debris within {threshold_km}km")
                
        except Exception as e:
            continue
    
    # Sort by debris count (descending)
    satellite_debris_counts.sort(key=lambda x: x['count'], reverse=True)
    
    # Take top N satellites
    top_satellites = satellite_debris_counts[:max_satellites]
    
    print(f"\nFound {len(top_satellites)} satellites with close debris")
    print(f"Total pairs to analyze: {sum(s['count'] for s in top_satellites)}")
    
    return top_satellites

if __name__ == '__main__':
    # Test the screening
    import sys
    sys.path.insert(0, 'database')
    from db_manager import get_db_session
    from models import Satellite, Debris
    
    session = get_db_session()
    
    # Get all satellites
    satellites = session.query(Satellite).all()
    sat_list = [{'norad_id': s.norad_id, 'name': s.name} for s in satellites]
    
    # Get all debris
    debris = session.query(Debris).limit(2000).all()
    debris_list = [{'norad_id': d.norad_id, 'name': d.name} for d in debris]
    
    # Find close pairs
    results = find_close_pairs(sat_list, debris_list, threshold_km=25.0, max_satellites=50)
    
    # Save results
    with open('close_pairs_cache.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to close_pairs_cache.json")
