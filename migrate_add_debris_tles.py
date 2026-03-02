"""
Migrate database to add TLE fields to debris_objects table
and populate them with generated TLEs from orbital parameters
"""

from database.db_manager import get_db_manager
from database.models import DebrisObject
from datetime import datetime
import sqlite3
import math

def add_tle_columns():
    """Add TLE columns to debris_objects table"""
    
    print("=" * 80)
    print("DATABASE MIGRATION: Adding TLE fields to debris_objects")
    print("=" * 80)
    
    db_path = 'data/astrocleanai.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(debris_objects)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'tle_line1' in columns:
            print("\n✓ TLE columns already exist")
            return True
        
        print("\nAdding TLE columns...")
        
        # Add TLE columns
        cursor.execute("ALTER TABLE debris_objects ADD COLUMN tle_line1 VARCHAR(200)")
        cursor.execute("ALTER TABLE debris_objects ADD COLUMN tle_line2 VARCHAR(200)")
        cursor.execute("ALTER TABLE debris_objects ADD COLUMN tle_epoch DATETIME")
        
        conn.commit()
        print("✓ TLE columns added successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error adding columns: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def generate_tle_from_params(debris):
    """Generate TLE lines from orbital parameters"""
    
    # Calculate mean motion from period
    mean_motion = 1440.0 / debris.period_minutes  # revolutions per day
    
    # Calculate eccentricity from apogee and perigee
    earth_radius = 6371.0  # km
    apogee_radius = debris.apogee_km + earth_radius
    perigee_radius = debris.perigee_km + earth_radius
    semi_major_axis = (apogee_radius + perigee_radius) / 2
    eccentricity = (apogee_radius - perigee_radius) / (2 * semi_major_axis)
    
    # Format eccentricity for TLE (remove decimal point, 7 digits)
    ecc_str = f"{int(eccentricity * 10000000):07d}"
    
    # Get current epoch
    now = datetime.utcnow()
    year = now.year % 100  # Last 2 digits
    day_of_year = now.timetuple().tm_yday
    fraction_of_day = (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    epoch_str = f"{day_of_year:03d}.{int(fraction_of_day * 100000000):08d}"
    
    # Extract numeric NORAD ID
    norad_str = str(debris.norad_id)
    try:
        # Try to extract numbers from the ID
        nums = ''.join(filter(str.isdigit, norad_str))
        if nums:
            norad_id = int(nums) % 100000  # Keep last 5 digits
        else:
            norad_id = abs(hash(norad_str)) % 100000
    except:
        norad_id = abs(hash(norad_str)) % 100000
    
    # Generate TLE Line 1
    line1 = (
        f"1 {norad_id:05d}U 00000A   "
        f"{year:02d}{epoch_str} "
        f" .00000000  00000-0  00000-0 0  9999"
    )
    
    # Generate TLE Line 2
    line2 = (
        f"2 {norad_id:05d} "
        f"{debris.inclination_deg:8.4f} "
        f"000.0000 "  # RAAN (unknown, set to 0)
        f"{ecc_str} "
        f"000.0000 "  # Argument of perigee (unknown, set to 0)
        f"000.0000 "  # Mean anomaly (unknown, set to 0)
        f"{mean_motion:11.8f}00000"
    )
    
    return line1, line2, now

def populate_debris_tles():
    """Populate TLE data for all debris objects"""
    
    print("\n" + "=" * 80)
    print("POPULATING TLE DATA FOR DEBRIS OBJECTS")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get all debris with orbital parameters
        debris_list = session.query(DebrisObject).filter(
            DebrisObject.apogee_km.isnot(None),
            DebrisObject.perigee_km.isnot(None),
            DebrisObject.inclination_deg.isnot(None),
            DebrisObject.period_minutes.isnot(None)
        ).all()
        
        print(f"\nDebris objects with orbital parameters: {len(debris_list)}")
        print("Generating TLEs...")
        
        updated = 0
        errors = 0
        
        for debris in debris_list:
            try:
                line1, line2, epoch = generate_tle_from_params(debris)
                
                debris.tle_line1 = line1
                debris.tle_line2 = line2
                debris.tle_epoch = epoch
                
                updated += 1
                
                if updated <= 3:
                    print(f"\n{debris.name}:")
                    print(f"  {line1}")
                    print(f"  {line2}")
                
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"✗ Error processing {debris.name}: {e}")
        
        session.commit()
        
        print(f"\n✓ Successfully generated TLEs for {updated} debris objects")
        if errors > 0:
            print(f"✗ Failed to process {errors} debris objects")
        
        return updated, errors
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        return 0, 0
    finally:
        session.close()

def verify_tles():
    """Verify TLE data was added"""
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        total_debris = session.query(DebrisObject).count()
        with_tles = session.query(DebrisObject).filter(
            DebrisObject.tle_line1.isnot(None)
        ).count()
        
        print(f"\nTotal debris objects: {total_debris}")
        print(f"Debris with TLEs: {with_tles}")
        print(f"Coverage: {(with_tles/total_debris*100):.1f}%")
        
        if with_tles > 0:
            print("\n✓ Migration successful!")
            print("✓ Collision analysis can now calculate debris positions")
        else:
            print("\n⚠ Warning: No TLEs were added")
        
    finally:
        session.close()

def main():
    """Run migration"""
    
    # Step 1: Add columns
    if not add_tle_columns():
        print("\n✗ Migration failed at column addition step")
        return
    
    # Step 2: Populate TLEs
    updated, errors = populate_debris_tles()
    
    if updated == 0:
        print("\n✗ Migration failed at TLE generation step")
        return
    
    # Step 3: Verify
    verify_tles()
    
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Restart your API server")
    print("2. Test collision analysis")
    print("3. Verify close pairs are now detected")

if __name__ == "__main__":
    main()
