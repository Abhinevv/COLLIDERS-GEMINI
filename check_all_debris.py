"""Check all debris in database"""
import sys
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import DebrisObject

db_manager = DatabaseManager()
session = db_manager.get_session()

# Count all debris
total = session.query(DebrisObject).count()
print(f"Total debris in database: {total}")

# Show first 10
debris_list = session.query(DebrisObject).limit(10).all()
print(f"\nFirst 10 debris:")
for d in debris_list:
    print(f"  {d.norad_id}: {d.name}")

session.close()
