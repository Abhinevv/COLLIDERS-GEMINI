"""Populate ALL debris from TLE files (not just the 500 LEO ones)"""
import sys
import os
import glob
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import DebrisObject, Satellite

def main():
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    print("\n" + "="*70)
    print("POPULATING ALL DEBRIS FROM TLE FILES")
    print("="*70)
    
    # Get all satellite NORAD IDs (so we don't add satellites as debris)
    satellite_ids = set()
    for sat in session.query(Satellite).all():
        satellite_ids.add(sat.norad_id)
    
    print(f"Found {len(satellite_ids)} satellites (will skip these)")
    
    # Find all sat_*.txt files
    tle_files = glob.glob('data/sat_*.txt')
    print(f"Found {len(tle_files)} TLE files total")
    
    added = 0
    skipped_satellite = 0
    skipped_exists = 0
    
    for tle_file in tle_files:
        filename = os.path.basename(tle_file)
        if filename == 'sat_manage.txt':
            continue
            
        norad_id = filename.replace('sat_', '').replace('.txt', '')
        
        # Skip if it's a satellite
        if norad_id in satellite_ids:
            skipped_satellite += 1
            continue
        
        # Skip if already in debris database
        if session.query(DebrisObject).filter_by(norad_id=norad_id).first():
            skipped_exists += 1
            continue
        
        # Read name from TLE file
        try:
            with open(tle_file, 'r') as f:
                name = f.readline().strip()
        except:
            name = f'DEBRIS-{norad_id}'
        
        # Add as debris
        debris = DebrisObject(
            norad_id=norad_id,
            name=name,
            type='DEBRIS'
        )
        
        session.add(debris)
        added += 1
        
        if added % 100 == 0:
            print(f"  Added {added} debris...")
    
    session.commit()
    
    print()
    print(f"✓ Added {added} new debris")
    print(f"⊙ Skipped {skipped_satellite} (are satellites)")
    print(f"⊙ Skipped {skipped_exists} (already in database)")
    
    total_debris = session.query(DebrisObject).count()
    print(f"\nTotal debris in database now: {total_debris}")
    
    session.close()
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
