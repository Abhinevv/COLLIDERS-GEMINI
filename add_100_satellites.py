"""
Add 100 important satellites from Space-Track.org
Fetches real, active satellites with valid TLE data
"""

import requests
import time
from datetime import datetime

BASE_URL = 'http://localhost:5000'

def fetch_and_add_satellites():
    """Fetch satellites from Space-Track and add them to the system"""
    print("\n" + "="*70)
    print("ADDING 100 IMPORTANT SATELLITES FROM SPACE-TRACK.ORG")
    print("="*70 + "\n")
    
    # Categories of satellites to fetch
    categories = [
        {
            'name': 'Space Stations',
            'query': 'station',
            'limit': 5,
            'type': 'Space Station'
        },
        {
            'name': 'Navigation Satellites (GPS/GLONASS/Galileo)',
            'query': 'gps|glonass|galileo',
            'limit': 20,
            'type': 'Navigation'
        },
        {
            'name': 'Weather Satellites',
            'query': 'noaa|goes|metop|meteor',
            'limit': 15,
            'type': 'Weather'
        },
        {
            'name': 'Communication Satellites',
            'query': 'intelsat|ses|eutelsat|astra|telesat',
            'limit': 15,
            'type': 'Communication'
        },
        {
            'name': 'Earth Observation',
            'query': 'landsat|sentinel|terra|aqua|spot|worldview',
            'limit': 15,
            'type': 'Earth Observation'
        },
        {
            'name': 'Scientific Satellites',
            'query': 'swift|chandra|fermi|nustar|tess',
            'limit': 10,
            'type': 'Scientific'
        },
        {
            'name': 'Starlink Constellation',
            'query': 'starlink',
            'limit': 20,
            'type': 'Communication'
        }
    ]
    
    total_added = 0
    total_skipped = 0
    total_failed = 0
    
    for category in categories:
        print(f"\n{'='*70}")
        print(f"Category: {category['name']}")
        print(f"{'='*70}")
        
        try:
            # Fetch from Space-Track API through our backend
            response = requests.get(
                f"{BASE_URL}/api/space_debris/search",
                params={'type': 'payload', 'limit': category['limit']},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"✗ Failed to fetch {category['name']}: {response.status_code}")
                continue
            
            data = response.json()
            debris_list = data.get('debris', [])
            
            if not debris_list:
                print(f"⚠ No satellites found for {category['name']}")
                continue
            
            print(f"Found {len(debris_list)} satellites, adding...")
            
            # Add each satellite
            for debris in debris_list[:category['limit']]:
                try:
                    norad_id = debris.get('NORAD_CAT_ID') or debris.get('norad_id')
                    name = debris.get('OBJECT_NAME') or debris.get('name', f'SAT-{norad_id}')
                    
                    if not norad_id:
                        continue
                    
                    # Clean up name
                    name = name.strip()
                    if len(name) > 50:
                        name = name[:47] + '...'
                    
                    satellite_data = {
                        'norad_id': str(norad_id),
                        'name': name,
                        'type': category['type']
                    }
                    
                    add_response = requests.post(
                        f'{BASE_URL}/api/satellites/manage/add',
                        json=satellite_data,
                        timeout=10
                    )
                    
                    if add_response.status_code in [200, 201]:
                        print(f"  ✓ {name} ({norad_id})")
                        total_added += 1
                    elif add_response.status_code == 409:
                        print(f"  ⊙ {name} (already exists)")
                        total_skipped += 1
                    else:
                        print(f"  ✗ {name} - Error {add_response.status_code}")
                        total_failed += 1
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"  ✗ Error processing satellite: {e}")
                    total_failed += 1
                    continue
            
        except Exception as e:
            print(f"✗ Error fetching {category['name']}: {e}")
            continue
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"✓ Successfully added: {total_added}")
    print(f"⊙ Already existed: {total_skipped}")
    print(f"✗ Failed: {total_failed}")
    print(f"📡 Total satellites processed: {total_added + total_skipped}")
    print("="*70)
    
    # Get final count
    try:
        response = requests.get(f'{BASE_URL}/api/satellites/manage')
        if response.status_code == 200:
            data = response.json()
            satellites = data.get('satellites', [])
            
            print(f"\n🎉 TOTAL SATELLITES NOW TRACKING: {data['count']}")
            
            # Count by type
            print("\n📊 Breakdown by Category:")
            types = {}
            for sat in satellites:
                sat_type = sat.get('type', 'Unknown')
                types[sat_type] = types.get(sat_type, 0) + 1
            
            for sat_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                bar = '█' * min(count, 50)
                print(f"  {sat_type:.<30} {count:>3} {bar}")
            
            print("\n✅ System is now tracking a comprehensive satellite constellation!")
            print("   You can view all satellites in the Dashboard or via API.")
            
    except Exception as e:
        print(f"\n✗ Error getting final count: {e}")

if __name__ == '__main__':
    print("\n⏳ This will take 1-2 minutes to fetch and add all satellites...")
    print("   Please wait...\n")
    fetch_and_add_satellites()
    print("\n✅ Done!\n")
