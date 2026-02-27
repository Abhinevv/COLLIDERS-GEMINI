"""
Add more satellites to the system
Popular and important satellites from various categories
"""

import requests

BASE_URL = 'http://localhost:5000'

# List of important satellites to add
satellites = [
    # Space Stations
    {'norad_id': '25544', 'name': 'ISS (ZARYA)', 'type': 'Space Station'},
    {'norad_id': '48274', 'name': 'Tiangong Space Station', 'type': 'Space Station'},
    
    # Space Telescopes
    {'norad_id': '20580', 'name': 'Hubble Space Telescope', 'type': 'Space Telescope'},
    {'norad_id': '50463', 'name': 'James Webb Space Telescope', 'type': 'Space Telescope'},
    
    # Navigation Satellites (GPS)
    {'norad_id': '40294', 'name': 'GPS BIIR-13', 'type': 'Navigation'},
    {'norad_id': '41019', 'name': 'GPS BIIF-2', 'type': 'Navigation'},
    {'norad_id': '43873', 'name': 'GPS BIIF-9', 'type': 'Navigation'},
    
    # Communication Satellites
    {'norad_id': '48915', 'name': 'Starlink-1007', 'type': 'Communication'},
    {'norad_id': '48916', 'name': 'Starlink-1008', 'type': 'Communication'},
    {'norad_id': '48917', 'name': 'Starlink-1009', 'type': 'Communication'},
    
    # Weather Satellites
    {'norad_id': '33591', 'name': 'NOAA-18', 'type': 'Weather'},
    {'norad_id': '28654', 'name': 'NOAA-17', 'type': 'Weather'},
    {'norad_id': '43226', 'name': 'NOAA-20', 'type': 'Weather'},
    
    # Earth Observation
    {'norad_id': '39084', 'name': 'Landsat 8', 'type': 'Earth Observation'},
    {'norad_id': '49260', 'name': 'Landsat 9', 'type': 'Earth Observation'},
    {'norad_id': '42063', 'name': 'Sentinel-3A', 'type': 'Earth Observation'},
    
    # Scientific Satellites
    {'norad_id': '27424', 'name': 'Aqua', 'type': 'Scientific'},
    {'norad_id': '25994', 'name': 'Terra', 'type': 'Scientific'},
    {'norad_id': '37849', 'name': 'OCO-2', 'type': 'Scientific'},
    
    # Military/Reconnaissance
    {'norad_id': '25730', 'name': 'USA-186', 'type': 'Military'},
    {'norad_id': '37348', 'name': 'USA-245', 'type': 'Military'},
]

def add_satellites():
    """Add satellites to the system"""
    print("\n" + "="*70)
    print("ADDING SATELLITES TO ASTROCLEANAI")
    print("="*70 + "\n")
    
    added = 0
    skipped = 0
    failed = 0
    
    for sat in satellites:
        try:
            response = requests.post(
                f'{BASE_URL}/api/satellites/manage/add',
                json=sat,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Added: {sat['name']} ({sat['norad_id']}) - {sat['type']}")
                added += 1
            elif response.status_code == 409:
                print(f"⊙ Exists: {sat['name']} ({sat['norad_id']})")
                skipped += 1
            else:
                print(f"✗ Failed: {sat['name']} - {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"✗ Error adding {sat['name']}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Added: {added}")
    print(f"⊙ Already existed: {skipped}")
    print(f"✗ Failed: {failed}")
    print(f"Total satellites: {added + skipped}")
    print("="*70 + "\n")
    
    # Show current satellite list
    try:
        response = requests.get(f'{BASE_URL}/api/satellites/manage')
        if response.status_code == 200:
            data = response.json()
            print(f"\n📡 Total satellites now being tracked: {data['count']}")
            print("\nCategories:")
            types = {}
            for sat in data['satellites']:
                sat_type = sat.get('type', 'Unknown')
                types[sat_type] = types.get(sat_type, 0) + 1
            
            for sat_type, count in sorted(types.items()):
                print(f"  - {sat_type}: {count}")
    except Exception as e:
        print(f"Error getting satellite list: {e}")

if __name__ == '__main__':
    add_satellites()
