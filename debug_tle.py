"""Debug TLE parsing"""

from database.db_manager import get_db_manager
from database.models import Satellite

db_manager = get_db_manager()
session = db_manager.get_session()

sat = session.query(Satellite).filter(Satellite.tle_line2.isnot(None)).first()

print(f"Satellite: {sat.name}")
print(f"TLE Line 1: [{sat.tle_line1}]")
print(f"TLE Line 2: [{sat.tle_line2}]")
print(f"Line 2 length: {len(sat.tle_line2)}")
print()
print("Character positions:")
for i, char in enumerate(sat.tle_line2):
    print(f"{i:2d}: '{char}'")

print("\nMean motion field (52-63):")
print(f"[{sat.tle_line2[52:63]}]")

print("\nInclination field (8-16):")
print(f"[{sat.tle_line2[8:16]}]")

session.close()
