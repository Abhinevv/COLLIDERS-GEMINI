"""Generate individual TLE cache files"""
import os

cache_dir = 'data/tle_cache'
os.makedirs(cache_dir, exist_ok=True)

# Generate TLE files for debris IDs 67700-67850
for norad_id in range(67700, 67851):
    tle_file = os.path.join(cache_dir, f'tle_{norad_id}.txt')
    with open(tle_file, 'w') as f:
        f.write(f"DEBRIS-{norad_id}\n")
        f.write(f"1 {norad_id}U 24001A   26060.50000000  .00000000  00000-0  00000-0 0  9999\n")
        f.write(f"2 {norad_id}  53.1600 180.0000 0001000   0.0000   0.0000 15.50000000000000\n")

# ISS
with open(os.path.join(cache_dir, 'tle_25544.txt'), 'w') as f:
    f.write("ISS (ZARYA)\n")
    f.write("1 25544U 98067A   26060.50000000  .00016717  00000-0  10270-3 0  9999\n")
    f.write("2 25544  51.6400 180.0000 0002000   0.0000   0.0000 15.50000000000000\n")

print(f"Created {151 + 1} TLE cache files")
print("Cache is ready!")
