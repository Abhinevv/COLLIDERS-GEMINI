import sys
sys.path.insert(0, 'database')
from db_manager import DatabaseManager
from models import Satellite, DebrisObject

db = DatabaseManager()
session = db.get_session()

sat_count = session.query(Satellite).count()
debris_count = session.query(DebrisObject).count()

print(f"Satellites: {sat_count}")
print(f"Debris: {debris_count}")

session.close()
