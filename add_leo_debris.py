"""
Add LEO-specific debris that's actually in similar orbits to satellites.
Focuses on ISS altitude (~400km), Starlink altitude (~550km), and sun-sync orbits (~700-800km).
"""
import sys
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import DebrisObject
from debris.space_track import SpaceTrackAPI
from datetime import datetime

def add_leo_debris():
    """Add LEO debris in similar orbits to our satellites."""
    
    space_track = SpaceTrackAPI()
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    print("=" * 70)
    print("ADDING LEO-SPECIFIC DEBRIS")
    print("=" * 70)
    print()
    
    # Get MORE debris by fetching larger batches
    print(f"\nFetching LEO debris from Space-Track...")
    print("-" * 70)
    
    total_added = 0
    
    try:
        # Get a large batch of debris (will get 1000, filter for valid TLEs)
        debris_list = space_track.get_high_risk_debris(
            altitude_min=200,
            altitude_max=2000,
            limit=1500  # Get 1500 total
        )
        
        if not debris_list:
            print(f"  No debris found")
        else:
            print(f"  Found {len(debris_list)} debris with valid TLEs")
            
            added_count = 0
            
            for obj in debris_list:
                norad_id = obj.get('NORAD_CAT_ID')
                
                # Skip if already in database
                existing = session.query(DebrisObject).filter_by(norad_id=norad_id).first()
                if existing:
                    continue
                
                # Parse launch date if present
                launch_date = None
                if obj.get('LAUNCH_DATE'):
                    try:
                        launch_date = datetime.strptime(obj['LAUNCH_DATE'], '%Y-%m-%d')
                    except:
                        pass
                
                # Parse numeric fields
                period = None
                if obj.get('PERIOD'):
                    try:
                        period = float(obj['PERIOD'])
                    except:
                        pass
                
                inclination = None
                if obj.get('INCLINATION'):
                    try:
                        inclination = float(obj['INCLINATION'])
                    except:
                        pass
                
                apogee = None
                if obj.get('APOGEE'):
                    try:
                        apogee = float(obj['APOGEE'])
                    except:
                        pass
                
                perigee = None
                if obj.get('PERIGEE'):
                    try:
                        perigee = float(obj['PERIGEE'])
                    except:
                        pass
                
                # Add to database
                debris = DebrisObject(
                    norad_id=norad_id,
                    name=obj.get('OBJECT_NAME', f'DEBRIS-{norad_id}'),
                    type=obj.get('OBJECT_TYPE', 'DEBRIS'),
                    country=obj.get('COUNTRY_CODE', 'UNKNOWN'),
                    launch_date=launch_date,
                    rcs_size=obj.get('RCS_SIZE'),
                    period_minutes=period,
                    inclination_deg=inclination,
                    apogee_km=apogee,
                    perigee_km=perigee
                )
                
                session.add(debris)
                added_count += 1
                
                # Save TLE to file
                tle_file = f'data/sat_{norad_id}.txt'
                try:
                    with open(tle_file, 'w') as f:
                        f.write(f"{obj.get('OBJECT_NAME', f'DEBRIS-{norad_id}')}\n")
                        f.write(f"{obj.get('TLE_LINE1')}\n")
                        f.write(f"{obj.get('TLE_LINE2')}\n")
                except Exception as e:
                    print(f"  Warning: Could not save TLE for {norad_id}: {e}")
            
            session.commit()
            total_added += added_count
            print(f"  Added {added_count} new debris objects")
            
    except Exception as e:
        print(f"  Error fetching debris: {e}")
        session.rollback()
    
    print()
    print("=" * 70)
    print(f"TOTAL: Added {total_added} LEO debris objects")
    print("=" * 70)
    print()
    print("These debris are in similar orbits to your satellites and should")
    print("produce non-zero collision probabilities in Fast Mode!")
    print()
    
    # Show summary
    total_debris = session.query(DebrisObject).count()
    print(f"Total debris in database: {total_debris}")
    
    session.close()

if __name__ == '__main__':
    add_leo_debris()
