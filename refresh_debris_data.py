"""
Refresh Debris Database with Valid TLE Data
Fetches fresh TLE data from Space-Track for all debris objects
"""

import os
import sys
import sqlite3
from debris.space_track import SpaceTrackAPI
from datetime import datetime

def refresh_debris_tle_data():
    """Refresh all debris objects with current TLE data from Space-Track"""
    
    # Initialize Space-Track API
    username = os.environ.get('SPACETRACK_USERNAME')
    password = os.environ.get('SPACETRACK_PASSWORD')
    
    if not username or not password:
        print("ERROR: Space-Track credentials not found in environment variables")
        print("Set SPACETRACK_USERNAME and SPACETRACK_PASSWORD")
        return False
    
    space_track = SpaceTrackAPI(username, password)
    
    # Connect to database
    db_path = 'data/astrocleanai.db'
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all debris NORAD IDs
    cursor.execute("SELECT norad_id, name FROM debris")
    debris_list = cursor.fetchall()
    
    print(f"\n{'='*70}")
    print(f"REFRESHING DEBRIS TLE DATA")
    print(f"{'='*70}")
    print(f"Found {len(debris_list)} debris objects in database")
    print(f"Fetching fresh TLE data from Space-Track.org...")
    print(f"{'='*70}\n")
    
    updated_count = 0
    failed_count = 0
    
    for norad_id, name in debris_list:
        try:
            print(f"Fetching TLE for {name} (NORAD: {norad_id})...", end=' ')
            
            # Get TLE from Space-Track
            tle_data = space_track.get_tle(norad_id)
            
            if tle_data and 'TLE_LINE1' in tle_data and 'TLE_LINE2' in tle_data:
                tle_line1 = tle_data['TLE_LINE1']
                tle_line2 = tle_data['TLE_LINE2']
                
                # Update database with fresh TLE
                cursor.execute("""
                    UPDATE debris 
                    SET tle_line1 = ?, tle_line2 = ?, last_updated = ?
                    WHERE norad_id = ?
                """, (tle_line1, tle_line2, datetime.utcnow().isoformat(), norad_id))
                
                updated_count += 1
                print("✓ Updated")
            else:
                print("✗ No TLE data available")
                failed_count += 1
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            failed_count += 1
            continue
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"REFRESH COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successfully updated: {updated_count} debris objects")
    print(f"✗ Failed to update: {failed_count} debris objects")
    print(f"{'='*70}\n")
    
    return True

if __name__ == '__main__':
    success = refresh_debris_tle_data()
    sys.exit(0 if success else 1)
