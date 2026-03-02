"""
Curate satellite database to keep only high-value satellites
Reduces from 928 to ~100-150 important satellites for better performance
"""

from database.db_manager import get_db_manager
from database.models import Satellite
from sqlalchemy import func

# High-priority satellites to keep (by name pattern or exact match)
PRIORITY_SATELLITES = {
    # Space Stations (highest priority - human lives)
    'space_stations': [
        'ISS (ZARYA)', 'Tiangong Space Station', 'Tiangong-2'
    ],
    
    # Space Telescopes & Major Science
    'science': [
        'HST', 'Chandra X-ray Observatory', 'Fermi Gamma-ray Space Telescope',
        'CALIPSO', 'OCO-2', 'VANGUARD 1', 'VANGUARD 2', 'VANGUARD 3',
        'EXPLORER 7', 'TIROS 1', 'TRANSIT 2A'
    ],
    
    # Navigation (GPS, GLONASS, Galileo)
    'navigation_patterns': [
        'GPS', 'GLONASS', 'GALILEO', 'NAVSTAR', 'BEIDOU'
    ],
    
    # Weather Satellites
    'weather': [
        'NOAA-19', 'NOAA-18', 'NOAA-17', 'NOAA-20',
        'GOES-16', 'GOES-18', 'METOP-A', 'METOP-B', 'METOP-C',
        'Fengyun 3A', 'Fengyun 3B', 'Fengyun 3D'
    ],
    
    # Earth Observation
    'earth_obs': [
        'Landsat 8', 'Landsat 9', 'Sentinel-1A', 'Sentinel-2A', 'Sentinel-3A',
        'Aqua', 'Terra', 'WorldView-1', 'WorldView-2', 'WorldView-3'
    ],
    
    # Major Communication Satellites (GEO)
    'communication': [
        'Intelsat 37e', 'SES-10', 'SES-12', 
        'Eutelsat 8 West B', 'Eutelsat 117 West B',
        'Astra 2G'
    ],
    
    # Military/Reconnaissance
    'military': [
        'USA-186', 'NAVSTAR 85 (USA 581)'
    ],
    
    # Representative Starlink (keep some, not all 600+)
    'starlink_keep': [
        'Starlink-1007', 'Starlink-1008', 'Starlink-1023', 
        'Starlink-1028', 'Starlink-1029', 'Starlink-1030'
    ],
    
    # Representative Kuiper (keep some)
    'kuiper_keep': [
        'KUIPER-00279', 'KUIPER-00276', 'KUIPER-00275'
    ],
    
    # Other Notable
    'other': [
        'DRAGON FREEDOM 3', 'PRC TEST SPACECRAFT 4', 'COSMOS 2600',
        'NEONSAT-1A', 'MR-1', 'MR-2'
    ]
}

def should_keep_satellite(sat):
    """Determine if a satellite should be kept"""
    
    # Check exact name matches
    for category, names in PRIORITY_SATELLITES.items():
        if category.endswith('_patterns'):
            # Pattern matching
            for pattern in names:
                if pattern.upper() in sat.name.upper():
                    return True, category
        else:
            # Exact matching
            if sat.name in names:
                return True, category
    
    return False, None

def curate_database(dry_run=True):
    """
    Curate the satellite database
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    
    print("=" * 80)
    print("SATELLITE DATABASE CURATION")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all satellites
        all_satellites = session.query(Satellite).all()
        print(f"\nCurrent total satellites: {len(all_satellites)}")
        
        # Categorize satellites
        keep_satellites = []
        remove_satellites = []
        keep_by_category = {}
        
        for sat in all_satellites:
            should_keep, category = should_keep_satellite(sat)
            
            if should_keep:
                keep_satellites.append(sat)
                if category not in keep_by_category:
                    keep_by_category[category] = []
                keep_by_category[category].append(sat.name)
            else:
                remove_satellites.append(sat)
        
        # Display results
        print("\n" + "=" * 80)
        print("SATELLITES TO KEEP")
        print("=" * 80)
        print(f"Total to keep: {len(keep_satellites)}")
        
        for category, names in sorted(keep_by_category.items()):
            print(f"\n{category.upper().replace('_', ' ')} ({len(names)} satellites):")
            for name in sorted(names)[:10]:  # Show first 10
                print(f"  - {name}")
            if len(names) > 10:
                print(f"  ... and {len(names) - 10} more")
        
        print("\n" + "=" * 80)
        print("SATELLITES TO REMOVE")
        print("=" * 80)
        print(f"Total to remove: {len(remove_satellites)}")
        
        # Group removals by type
        remove_by_type = {}
        for sat in remove_satellites:
            sat_type = sat.type or "Unknown"
            if sat_type not in remove_by_type:
                remove_by_type[sat_type] = []
            remove_by_type[sat_type].append(sat.name)
        
        for sat_type, names in sorted(remove_by_type.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n{sat_type} ({len(names)} satellites):")
            for name in names[:5]:  # Show first 5
                print(f"  - {name}")
            if len(names) > 5:
                print(f"  ... and {len(names) - 5} more")
        
        # Perform deletion if not dry run
        if not dry_run:
            print("\n" + "=" * 80)
            print("PERFORMING DELETION")
            print("=" * 80)
            
            for sat in remove_satellites:
                session.delete(sat)
            
            session.commit()
            print(f"\n✓ Successfully removed {len(remove_satellites)} satellites")
            print(f"✓ Kept {len(keep_satellites)} high-priority satellites")
            
            # Verify
            remaining = session.query(Satellite).count()
            print(f"\nFinal satellite count: {remaining}")
        else:
            print("\n" + "=" * 80)
            print("DRY RUN - NO CHANGES MADE")
            print("=" * 80)
            print("\nTo actually perform the curation, run:")
            print("  python curate_satellites.py --execute")
        
        return len(keep_satellites), len(remove_satellites)
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        session.close()

def backup_database():
    """Create a backup before curation"""
    import shutil
    from datetime import datetime
    
    db_path = 'data/astrocleanai.db'
    backup_path = f'data/astrocleanai_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check for execute flag
    execute = '--execute' in sys.argv or '-e' in sys.argv
    
    if execute:
        print("EXECUTING SATELLITE CURATION")
        print("Creating backup first...")
        if backup_database():
            print("\nProceeding with curation...\n")
            curate_database(dry_run=False)
        else:
            print("\n✗ Aborting - backup failed")
    else:
        print("DRY RUN MODE - Showing what would be changed\n")
        curate_database(dry_run=True)
