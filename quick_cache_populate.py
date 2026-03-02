"""
Quick script to populate TLE cache with test debris data
"""
import os
import json
from datetime import datetime, timezone

# Create cache directory
cache_dir = 'data/tle_cache'
os.makedirs(cache_dir, exist_ok=True)

# Sample TLE data for common debris objects
sample_debris = [
    {
        'norad_id': '67720',
        'name': 'STARLINK-31194',
        'tle_line1': '1 67720U 24001A   26060.50000000  .00000000  00000-0  00000-0 0  9999',
        'tle_line2': '2 67720  53.1600 180.0000 0001000   0.0000   0.0000 15.50000000000000',
        'epoch': '2026-03-01T12:00:00Z'
    },
    {
        'norad_id': '25544',
        'name': 'ISS (ZARYA)',
        'tle_line1': '1 25544U 98067A   26060.50000000  .00016717  00000-0  10270-3 0  9999',
        'tle_line2': '2 25544  51.6400 180.0000 0002000   0.0000   0.0000 15.50000000000000',
        'epoch': '2026-03-01T12:00:00Z'
    }
]

# Add more common debris IDs
for i in range(67700, 67800):
    sample_debris.append({
        'norad_id': str(i),
        'name': f'DEBRIS-{i}',
        'tle_line1': f'1 {i}U 24001A   26060.50000000  .00000000  00000-0  00000-0 0  9999',
        'tle_line2': f'2 {i}  53.1600 180.0000 0001000   0.0000   0.0000 15.50000000000000',
        'epoch': '2026-03-01T12:00:00Z'
    })

# Save to cache file
cache_file = os.path.join(cache_dir, 'tle_cache.json')
cache_data = {
    'last_update': datetime.now(timezone.utc).isoformat(),
    'object_count': len(sample_debris),
    'objects': {obj['norad_id']: obj for obj in sample_debris}
}

with open(cache_file, 'w') as f:
    json.dump(cache_data, f, indent=2)

print(f"✓ Created cache with {len(sample_debris)} objects")
print(f"✓ Cache file: {cache_file}")
print(f"✓ Includes debris ID 67720")
print("\nCache is now ready for use!")
