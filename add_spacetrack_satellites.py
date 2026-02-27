"""
Add active satellites from Space-Track.org
Query for operational satellites and add them to the database
"""

import requests
import time
from debris.space_track import SpaceTrackAPI

BASE_URL = 'http://localhost:5000'

def get_active_satellites_from_spacetrack(limit=500):
    """Get active satellites from Space-Track.org"""
    api = SpaceTrackAPI()
    
    if not api.authenticate():
        print("Failed to authenticate with Space-Track")
        return []
    
    try:
        # Query for active payloads (operational satellites)
        query_url = (
            f"{api.base_url}/basicspacedata/query/class/gp/"
            f"OBJECT_TYPE/PAYLOAD/"
            f"DECAY_DATE/null-val/"  # Not decayed (still in orbit)
            f"orderby/NORAD_CAT_ID desc/limit/{limit}/format/json"
        )
        
        response = api.session.get(query_url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {len(data)} active satellites from Space-Track")
            return data
        else:
            print(f"✗ Query failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def categorize_satellite(name):
    """Categorize satellite by name"""
    name_upper = name.upper()
    
    if 'STARLINK' in name_upper:
        return 'Communication'
    elif any(x in name_upper for x in ['GPS', 'GLONASS', 'GALILEO', 'BEIDOU']):
        return 'Navigation'
    elif any(x in name_upper for x in ['NOAA', 'GOES', 'METOP', 'FENGYUN', 'WEATHER']):
        return 'Weather'
    elif any(x in name_upper for x in ['LANDSAT', 'SENTINEL', 'WORLDVIEW', 'TERRA', 'AQUA']):
        return 'Earth Observation'
    elif any(x in name_upper for x in ['HUBBLE', 'CHANDRA', 'FERMI', 'TESS', 'KEPLER']):
        return 'Scientific'
    elif any(x in name_upper for x in ['ISS', 'TIANGONG', 'STATION']):
        return 'Space Station'
    elif any(x in name_upper for x in ['INTELSAT', 'SES', 'EUTELSAT', 'TELSTAR', 'VIASAT']):
        return 'Communication'
    elif 'USA' in name_upper or 'NROL' in name_upper:
        return 'Military'
    else:
        return 'Satellite'

def add_satellites_to_db(satellites):
    """Add satellites to the database"""
    print("\n" + "="*70)
    print("ADDING SATELLITES TO DATABASE")
    print("="*70 + "\n")
    
    added = 0
    skipped = 0
    failed = 0
    
    for i, sat in enumerate(satellites, 1):
        try:
            norad_id = sat.get('NORAD_CAT_ID')
            name = sat.get('OBJECT_NAME', 'UNKNOWN')
            sat_type = categorize_satellite(name)
            
            payload = {
                'norad_id': norad_id,
                'name': name,
                'type': sat_type
            }
            
            response = requests.post(
                f'{BASE_URL}/api/satellites/manage/add',
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"[{i:3d}/{len(satellites)}] ✓ {name[:45]:.<45} ({norad_id})")
                added += 1
            elif response.status_code == 409:
                skipped += 1
                if i % 50 == 0:  # Only print every 50th skip
                    print(f"[{i:3d}/{len(satellites)}] ⊙ Skipped {skipped} existing satellites...")
            else:
                print(f"[{i:3d}/{len(satellites)}] ✗ {name[:45]:.<45} Error {response.status_code}")
                failed += 1
            
            # Small delay to avoid overwhelming the server
            if i % 10 == 0:
                time.sleep(0.2)
            else:
                time.sleep(0.05)
                
        except Exception as e:
            print(f"[{i:3d}/{len(satellites)}] ✗ {name[:45]:.<45} {str(e)[:20]}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Successfully added: {added}")
    print(f"⊙ Already existed: {skipped}")
    print(f"✗ Failed: {failed}")
    print(f"📡 Total processed: {added + skipped}")
    print("="*70)
    
    # Get final count
    try:
        response = requests.get(f'{BASE_URL}/api/satellites/manage')
        if response.status_code == 200:
            data = response.json()
            satellites_in_db = data.get('satellites', [])
            
            print(f"\n🎉 TOTAL SATELLITES NOW TRACKING: {data['count']}")
            
            # Count by type
            print("\n📊 Breakdown by Category:")
            types = {}
            for sat in satellites_in_db:
                sat_type = sat.get('type', 'Unknown')
                types[sat_type] = types.get(sat_type, 0) + 1
            
            for sat_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                bar = '█' * min(count // 5, 50)
                print(f"  {sat_type:.<30} {count:>4} {bar}")
            
            print("\n✅ System is now tracking a comprehensive satellite constellation!")
            
    except Exception as e:
        print(f"\n✗ Error getting final count: {e}")

def main():
    print("="*70)
    print("SPACE-TRACK SATELLITE IMPORTER")
    print("="*70)
    print("\nThis will fetch active satellites from Space-Track.org")
    print("and add them to your AstroCleanAI database.\n")
    
    # Ask how many satellites to fetch
    print("How many satellites do you want to add?")
    print("  100 - Quick test")
    print("  500 - Good coverage")
    print("  1000 - Comprehensive")
    print("  2000 - Very comprehensive")
    print("  5000 - Maximum (may take a while)")
    
    try:
        limit = int(input("\nEnter limit (default 500): ") or "500")
    except:
        limit = 500
    
    print(f"\nFetching {limit} active satellites from Space-Track.org...")
    
    # Get satellites from Space-Track
    satellites = get_active_satellites_from_spacetrack(limit)
    
    if not satellites:
        print("\n✗ No satellites retrieved. Check your Space-Track credentials.")
        return
    
    print(f"\nRetrieved {len(satellites)} satellites. Adding to database...")
    
    # Add to database
    add_satellites_to_db(satellites)
    
    print("\n✅ Done!\n")

if __name__ == '__main__':
    main()
