"""
Fix satellite TLE data by fetching from Celestrak
Celestrak is free and doesn't require authentication
"""

from database.db_manager import get_db_manager
from database.models import Satellite
import requests
import time
from datetime import datetime

def fetch_tle_from_celestrak(norad_id):
    """
    Fetch TLE from Celestrak (free, no authentication required)
    
    Args:
        norad_id: NORAD catalog ID
        
    Returns:
        dict with 'line1' and 'line2', or None if not found
    """
    try:
        # Celestrak GP (General Perturbations) endpoint
        url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().split('\n')
            
            # TLE format: Name, Line 1, Line 2
            if len(lines) >= 3:
                return {
                    'name': lines[0].strip(),
                    'line1': lines[1].strip(),
                    'line2': lines[2].strip()
                }
            elif len(lines) == 2:
                # Sometimes name is omitted
                return {
                    'line1': lines[0].strip(),
                    'line2': lines[1].strip()
                }
        
        return None
        
    except Exception as e:
        print(f"  ✗ Error fetching TLE: {e}")
        return None

def fix_all_satellite_tles():
    """Fix TLE data for all satellites"""
    
    print("=" * 80)
    print("FIXING SATELLITE TLE DATA")
    print("=" * 80)
    print("Fetching TLEs from Celestrak (free, no login required)")
    print()
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all satellites
        satellites = session.query(Satellite).all()
        
        print(f"Total satellites: {len(satellites)}")
        print()
        
        updated = 0
        failed = 0
        skipped = 0
        
        for i, sat in enumerate(satellites, 1):
            print(f"[{i}/{len(satellites)}] {sat.name[:50]:50s} ", end='')
            
            # Check if already has proper TLEs
            if sat.tle_line1 and sat.tle_line2 and len(sat.tle_line1) > 50:
                print("✓ Already has TLEs")
                skipped += 1
                continue
            
            # Extract NORAD ID (remove any non-numeric characters)
            norad_id = ''.join(filter(str.isdigit, sat.norad_id))
            
            if not norad_id:
                print("✗ Invalid NORAD ID")
                failed += 1
                continue
            
            # Fetch TLE from Celestrak
            tle_data = fetch_tle_from_celestrak(norad_id)
            
            if tle_data and 'line1' in tle_data and 'line2' in tle_data:
                # Update satellite
                sat.tle_line1 = tle_data['line1']
                sat.tle_line2 = tle_data['line2']
                sat.tle_epoch = datetime.utcnow()
                sat.last_updated = datetime.utcnow()
                
                print(f"✓ Updated")
                updated += 1
                
                # Show first 3 as examples
                if updated <= 3:
                    print(f"     Line 1: {tle_data['line1']}")
                    print(f"     Line 2: {tle_data['line2']}")
            else:
                print("✗ Not found on Celestrak")
                failed += 1
            
            # Be nice to Celestrak - small delay between requests
            time.sleep(0.5)
        
        # Commit changes
        session.commit()
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Updated: {updated}")
        print(f"Skipped (already had TLEs): {skipped}")
        print(f"Failed: {failed}")
        print(f"Total: {len(satellites)}")
        
        if updated > 0:
            print()
            print("✓ TLE data updated successfully!")
            print("✓ Collision analysis should now work")
            print()
            print("Next steps:")
            print("1. Restart your API server")
            print("2. Test collision analysis in the frontend")
            print("3. Should now find orbital neighbors")
        
        return updated, failed
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        return 0, 0
    finally:
        session.close()

def verify_tles():
    """Verify TLE data after update"""
    
    print()
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        total = session.query(Satellite).count()
        with_line1 = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line1 != ''
        ).count()
        with_line2 = session.query(Satellite).filter(
            Satellite.tle_line2.isnot(None),
            Satellite.tle_line2 != ''
        ).count()
        with_both = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line1 != '',
            Satellite.tle_line2.isnot(None),
            Satellite.tle_line2 != ''
        ).count()
        
        print(f"Total satellites: {total}")
        print(f"With Line 1: {with_line1} ({with_line1/total*100:.1f}%)")
        print(f"With Line 2: {with_line2} ({with_line2/total*100:.1f}%)")
        print(f"With BOTH lines: {with_both} ({with_both/total*100:.1f}%)")
        
        if with_both == total:
            print("\n✓ All satellites have complete TLE data!")
        elif with_both > total * 0.9:
            print(f"\n✓ Most satellites have TLE data ({with_both}/{total})")
        else:
            print(f"\n⚠ Only {with_both}/{total} satellites have complete TLEs")
        
        # Show a sample
        print("\nSample satellite TLEs:")
        sample = session.query(Satellite).filter(
            Satellite.tle_line1.isnot(None),
            Satellite.tle_line2.isnot(None)
        ).first()
        
        if sample:
            print(f"\n{sample.name}:")
            print(f"  Line 1: {sample.tle_line1}")
            print(f"  Line 2: {sample.tle_line2}")
        
    finally:
        session.close()

if __name__ == "__main__":
    print("This will fetch TLE data from Celestrak for all satellites.")
    print("Celestrak is free and doesn't require authentication.")
    print("This will take about 2-3 minutes for 74 satellites.")
    print()
    
    updated, failed = fix_all_satellite_tles()
    
    if updated > 0:
        verify_tles()
        
        print()
        print("=" * 80)
        print("COMPLETE!")
        print("=" * 80)
        print("Your satellites now have proper TLE data.")
        print("Collision analysis should work correctly.")
        print()
        print("Restart your API server and test!")
