"""
Add 500 active satellites from Space-Track.org (non-interactive)
"""

import requests
import time
from debris.space_track import SpaceTrackAPI

BASE_URL = 'http://localhost:5000'

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

print("="*70)
print("ADDING 500 ACTIVE SATELLITES FROM SPACE-TRACK")
print("="*70)

# Get satellites from Space-Track
api = SpaceTrackAPI()

if not api.authenticate():
    print("✗ Failed to authenticate with Space-Track")
    exit(1)

print("\nFetching active satellites...")

query_url = (
    f"{api.base_url}/basicspacedata/query/class/gp/"
    f"OBJECT_TYPE/PAYLOAD/"
    f"DECAY_DATE/null-val/"
    f"orderby/NORAD_CAT_ID desc/limit/500/format/json"
)

response = api.session.get(query_url, timeout=60)

if response.status_code != 200:
    print(f"✗ Query failed: {response.status_code}")
    exit(1)

satellites = response.json()
print(f"✓ Retrieved {len(satellites)} satellites\n")

# Add to database
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
            print(f"[{i:3d}/500] ✓ {name[:50]:.<50} ({norad_id})")
            added += 1
        elif response.status_code == 409:
            skipped += 1
            if i % 50 == 0:
                print(f"[{i:3d}/500] ⊙ Skipped {skipped} existing...")
        else:
            failed += 1
        
        if i % 10 == 0:
            time.sleep(0.2)
        else:
            time.sleep(0.05)
            
    except Exception as e:
        failed += 1

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"✓ Added: {added}")
print(f"⊙ Skipped: {skipped}")
print(f"✗ Failed: {failed}")

# Get final count
response = requests.get(f'{BASE_URL}/api/satellites/manage')
data = response.json()
print(f"\n🎉 TOTAL SATELLITES: {data['count']}")
print("="*70)
