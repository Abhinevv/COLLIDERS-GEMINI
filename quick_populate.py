"""Quick script to populate database and check counts"""
import sys
import os
import glob
sys.path.insert(0, 'database')

from database.db_manager import DatabaseManager
from database.models import Satellite, DebrisObject

def main():
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    print("\n" + "="*70)
    print("CURRENT DATABASE STATUS")
    print("="*70)
    
    sat_count = session.query(Satellite).count()
    debris_count = session.query(DebrisObject).count()
    
    print(f"Satellites: {sat_count}")
    print(f"Debris: {debris_count}")
    
    if sat_count == 0:
        print("\n" + "="*70)
        print("POPULATING SATELLITES FROM TLE FILES")
        print("="*70)
        
        tle_files = glob.glob('data/sat_*.txt')
        print(f"Found {len(tle_files)} TLE files")
        
        added = 0
        for tle_file in tle_files:
            filename = os.path.basename(tle_file)
            if filename == 'sat_manage.txt':
                continue
                
            norad_id = filename.replace('sat_', '').replace('.txt', '')
            
            # Skip if exists
            if session.query(Satellite).filter_by(norad_id=norad_id).first():
                continue
            
            # Read name
            try:
                with open(tle_file, 'r') as f:
                    name = f.readline().strip()
            except:
                name = f'SAT-{norad_id}'
            
            # Add satellite
            sat = Satellite(norad_id=norad_id, name=name, type='SATELLITE')
            session.add(sat)
            added += 1
            
            if added % 100 == 0:
                print(f"  Added {added}...")
        
        session.commit()
        print(f"\n✓ Added {added} satellites")
        
        sat_count = session.query(Satellite).count()
        print(f"Total satellites now: {sat_count}")
    
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)
    print(f"Satellites: {sat_count}")
    print(f"Debris: {debris_count}")
    print("="*70 + "\n")
    
    session.close()

if __name__ == '__main__':
    main()
