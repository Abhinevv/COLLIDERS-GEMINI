"""
Populate satellite database from existing TLE files
"""
import sys
import os
import glob
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import Satellite

def populate_satellites():
    """Add satellites to database from existing TLE files."""
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    print("=" * 70)
    print("POPULATING SATELLITES FROM TLE FILES")
    print("=" * 70)
    print()
    
    # Find all sat_*.txt files
    tle_files = glob.glob('data/sat_*.txt')
    print(f"Found {len(tle_files)} TLE files")
    
    added_count = 0
    skipped_count = 0
    
    for tle_file in tle_files:
        # Extract NORAD ID from filename
        filename = os.path.basename(tle_file)
        if filename == 'sat_manage.txt':
            continue
            
        norad_id = filename.replace('sat_', '').replace('.txt', '')
        
        # Skip if already in database
        existing = session.query(Satellite).filter_by(norad_id=norad_id).first()
        if existing:
            skipped_count += 1
            continue
        
        # Read TLE file to get name
        try:
            with open(tle_file, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    name = lines[0].strip()
                else:
                    name = f'SAT-{norad_id}'
        except:
            name = f'SAT-{norad_id}'
        
        # Add to database
        satellite = Satellite(
            norad_id=norad_id,
            name=name,
            type='SATELLITE'
        )
        
        session.add(satellite)
        added_count += 1
        
        if added_count % 50 == 0:
            print(f"  Added {added_count} satellites...")
    
    session.commit()
    
    print()
    print(f"✓ Added {added_count} satellites")
    print(f"⊙ Skipped {skipped_count} (already in database)")
    
    # Show summary
    total_satellites = session.query(Satellite).count()
    print(f"\nTotal satellites in database: {total_satellites}")
    
    session.close()
    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

if __name__ == '__main__':
    populate_satellites()
