"""
Add satellites directly to database from Space-Track.org
"""
import sys
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import Satellite
from debris.space_track import SpaceTrackAPI
from datetime import datetime

def add_satellites():
    """Add important satellites from Space-Track."""
    
    space_track = SpaceTrackAPI()
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    print("=" * 70)
    print("ADDING SATELLITES FROM SPACE-TRACK")
    print("=" * 70)
    print()
    
    # Authenticate
    if not space_track.authenticate():
        print("Failed to authenticate with Space-Track")
        return
    
    # Get active satellites (payloads)
    print("Fetching active satellites...")
    
    try:
        # Query for active payload objects
        query_url = (
            f"{space_track.base_url}/basicspacedata/query/class/gp/"
            f"OBJECT_TYPE/PAYLOAD/"
            f"orderby/NORAD_CAT_ID desc/limit/100/format/json"
        )
        
        response = space_track.session.get(query_url, timeout=30)
        
        if response.status_code == 200:
            satellites = response.json()
            print(f"✓ Found {len(satellites)} satellites")
            
            added_count = 0
            
            for sat in satellites:
                norad_id = sat.get('NORAD_CAT_ID')
                
                # Skip if already in database
                existing = session.query(Satellite).filter_by(norad_id=norad_id).first()
                if existing:
                    continue
                
                # Parse launch date if present
                launch_date = None
                if sat.get('LAUNCH_DATE'):
                    try:
                        launch_date = datetime.strptime(sat['LAUNCH_DATE'], '%Y-%m-%d')
                    except:
                        pass
                
                # Add to database
                satellite = Satellite(
                    norad_id=norad_id,
                    name=sat.get('OBJECT_NAME', f'SAT-{norad_id}'),
                    type='PAYLOAD',
                    operator=sat.get('COUNTRY_CODE', 'UNKNOWN'),
                    launch_date=launch_date
                )
                
                session.add(satellite)
                added_count += 1
                
                # Save TLE to file
                tle_file = f'data/sat_{norad_id}.txt'
                try:
                    with open(tle_file, 'w') as f:
                        f.write(f"{sat.get('OBJECT_NAME', f'SAT-{norad_id}')}\n")
                        f.write(f"{sat.get('TLE_LINE1')}\n")
                        f.write(f"{sat.get('TLE_LINE2')}\n")
                except Exception as e:
                    print(f"  Warning: Could not save TLE for {norad_id}: {e}")
            
            session.commit()
            print(f"✓ Added {added_count} satellites")
            
            # Show summary
            total_satellites = session.query(Satellite).count()
            print(f"\nTotal satellites in database: {total_satellites}")
            
        else:
            print(f"✗ Query failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        session.rollback()
    
    session.close()
    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

if __name__ == '__main__':
    add_satellites()
