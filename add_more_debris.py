"""
Add more debris objects for better collision analysis accuracy
Adds ~200-300 debris objects across all orbital regions
"""

from database.db_manager import get_db_manager
from database.models import DebrisObject
from datetime import datetime
import random

def generate_leo_debris(count=100):
    """Generate LEO debris objects (200-2000 km)"""
    debris_list = []
    
    # Common LEO debris sources
    sources = [
        ('Cosmos', 'CIS', 'DEBRIS'),
        ('Iridium', 'US', 'DEBRIS'),
        ('Fengyun-1C', 'PRC', 'DEBRIS'),
        ('SL-16 R/B', 'CIS', 'ROCKET BODY'),
        ('Delta 2 R/B', 'US', 'ROCKET BODY'),
        ('Ariane 5 R/B', 'FR', 'ROCKET BODY'),
        ('CZ-4B R/B', 'PRC', 'ROCKET BODY'),
        ('H-2A R/B', 'JPN', 'ROCKET BODY'),
        ('PSLV R/B', 'IND', 'ROCKET BODY'),
        ('Falcon 9 R/B', 'US', 'ROCKET BODY'),
        ('Soyuz R/B', 'CIS', 'ROCKET BODY'),
        ('Atlas V R/B', 'US', 'ROCKET BODY'),
    ]
    
    sizes = ['SMALL', 'MEDIUM', 'LARGE']
    
    # LEO altitude bands with typical inclinations
    altitude_bands = [
        (400, 500, [51.6, 97.8]),  # ISS altitude, sun-sync
        (500, 600, [53.0, 98.2]),  # Common LEO
        (600, 700, [63.4, 98.5]),  # Mid LEO
        (700, 800, [74.0, 98.8]),  # Iridium/Cosmos collision altitude
        (800, 900, [86.4, 99.0]),  # Fengyun-1C altitude
        (900, 1000, [82.5, 99.2]), # High LEO
        (1000, 1200, [71.0, 98.0]), # Very high LEO
        (1200, 1500, [65.0, 90.0]), # Transition zone
    ]
    
    for i in range(count):
        source_name, country, obj_type = random.choice(sources)
        size = random.choice(sizes)
        
        # Select altitude band
        min_alt, max_alt, inclinations = random.choice(altitude_bands)
        
        # Generate orbital parameters
        perigee = random.uniform(min_alt, max_alt - 20)
        apogee = perigee + random.uniform(10, 50)
        inclination = random.choice(inclinations) + random.uniform(-2, 2)
        
        # Calculate period (approximate)
        avg_alt = (perigee + apogee) / 2
        a = (avg_alt + 6371) * 1000  # semi-major axis in meters
        period = 2 * 3.14159 * ((a**3 / 3.986004418e14) ** 0.5) / 60  # minutes
        
        debris = {
            'norad_id': f'DEB-LEO-{1000 + i}',
            'name': f'{source_name} Fragment {i+1}',
            'type': obj_type,
            'rcs_size': size,
            'country': country,
            'apogee_km': round(apogee, 1),
            'perigee_km': round(perigee, 1),
            'inclination_deg': round(inclination, 2),
            'period_minutes': round(period, 2)
        }
        debris_list.append(debris)
    
    return debris_list

def generate_meo_debris(count=50):
    """Generate MEO debris objects (2000-35000 km)"""
    debris_list = []
    
    # MEO debris sources (mostly navigation constellation related)
    sources = [
        ('GPS R/B', 'US', 'ROCKET BODY'),
        ('Glonass R/B', 'CIS', 'ROCKET BODY'),
        ('Galileo R/B', 'FR', 'ROCKET BODY'),
        ('Beidou R/B', 'PRC', 'ROCKET BODY'),
        ('GPS Debris', 'US', 'DEBRIS'),
        ('Navigation Sat', 'US', 'DEBRIS'),
        ('Molniya R/B', 'CIS', 'ROCKET BODY'),
    ]
    
    sizes = ['SMALL', 'MEDIUM', 'LARGE']
    
    # MEO altitude bands
    altitude_bands = [
        (19000, 20500, [55.0, 64.8]),  # GPS/Glonass
        (20000, 21000, [55.0, 56.0]),  # GPS
        (21000, 22000, [55.5, 64.8]),  # Beidou
        (22000, 24000, [56.0, 57.0]),  # Galileo
    ]
    
    for i in range(count):
        source_name, country, obj_type = random.choice(sources)
        size = random.choice(sizes)
        
        min_alt, max_alt, inclinations = random.choice(altitude_bands)
        
        perigee = random.uniform(min_alt, max_alt - 100)
        apogee = perigee + random.uniform(50, 300)
        inclination = random.choice(inclinations) + random.uniform(-1, 1)
        
        # Calculate period
        avg_alt = (perigee + apogee) / 2
        a = (avg_alt + 6371) * 1000
        period = 2 * 3.14159 * ((a**3 / 3.986004418e14) ** 0.5) / 60
        
        debris = {
            'norad_id': f'DEB-MEO-{2000 + i}',
            'name': f'{source_name} Fragment {i+1}',
            'type': obj_type,
            'rcs_size': size,
            'country': country,
            'apogee_km': round(apogee, 1),
            'perigee_km': round(perigee, 1),
            'inclination_deg': round(inclination, 2),
            'period_minutes': round(period, 2)
        }
        debris_list.append(debris)
    
    return debris_list

def generate_geo_debris(count=30):
    """Generate GEO debris objects (35000-36000 km)"""
    debris_list = []
    
    # GEO debris sources
    sources = [
        ('Intelsat R/B', 'US', 'ROCKET BODY'),
        ('Ariane R/B', 'FR', 'ROCKET BODY'),
        ('Proton R/B', 'CIS', 'ROCKET BODY'),
        ('CZ-3B R/B', 'PRC', 'ROCKET BODY'),
        ('GEO Sat Debris', 'US', 'DEBRIS'),
        ('Comsat Fragment', 'US', 'DEBRIS'),
        ('Atlas Centaur R/B', 'US', 'ROCKET BODY'),
    ]
    
    sizes = ['SMALL', 'MEDIUM', 'LARGE']
    
    for i in range(count):
        source_name, country, obj_type = random.choice(sources)
        size = random.choice(sizes)
        
        # GEO altitude with small variations
        perigee = random.uniform(35700, 35850)
        apogee = perigee + random.uniform(10, 100)
        inclination = random.uniform(0.0, 5.0)  # Most GEO debris is near-equatorial
        
        # GEO period ~1436 minutes
        period = 1436.0 + random.uniform(-5, 5)
        
        debris = {
            'norad_id': f'DEB-GEO-{3000 + i}',
            'name': f'{source_name} Fragment {i+1}',
            'type': obj_type,
            'rcs_size': size,
            'country': country,
            'apogee_km': round(apogee, 1),
            'perigee_km': round(perigee, 1),
            'inclination_deg': round(inclination, 2),
            'period_minutes': round(period, 2)
        }
        debris_list.append(debris)
    
    return debris_list

def generate_heo_debris(count=20):
    """Generate HEO debris objects (Highly Elliptical Orbits)"""
    debris_list = []
    
    sources = [
        ('Molniya R/B', 'CIS', 'ROCKET BODY'),
        ('GTO Stage', 'US', 'ROCKET BODY'),
        ('Tundra R/B', 'CIS', 'ROCKET BODY'),
        ('Transfer Orbit Debris', 'FR', 'DEBRIS'),
    ]
    
    sizes = ['SMALL', 'MEDIUM', 'LARGE']
    
    # HEO orbit types
    orbit_types = [
        (500, 39800, 63.4),   # Molniya
        (200, 35800, 7.0),    # GTO
        (24700, 47100, 63.4), # Tundra
        (600, 42000, 56.0),   # Elliptical
    ]
    
    for i in range(count):
        source_name, country, obj_type = random.choice(sources)
        size = random.choice(sizes)
        
        base_perigee, base_apogee, base_inc = random.choice(orbit_types)
        
        perigee = base_perigee + random.uniform(-100, 100)
        apogee = base_apogee + random.uniform(-500, 500)
        inclination = base_inc + random.uniform(-2, 2)
        
        # Calculate period
        avg_alt = (perigee + apogee) / 2
        a = (avg_alt + 6371) * 1000
        period = 2 * 3.14159 * ((a**3 / 3.986004418e14) ** 0.5) / 60
        
        debris = {
            'norad_id': f'DEB-HEO-{4000 + i}',
            'name': f'{source_name} Fragment {i+1}',
            'type': obj_type,
            'rcs_size': size,
            'country': country,
            'apogee_km': round(apogee, 1),
            'perigee_km': round(perigee, 1),
            'inclination_deg': round(inclination, 2),
            'period_minutes': round(period, 2)
        }
        debris_list.append(debris)
    
    return debris_list

def add_debris_to_database(debris_list):
    """Add debris objects to database"""
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        added = 0
        skipped = 0
        
        for debris_info in debris_list:
            # Check if already exists
            existing = session.query(DebrisObject).filter_by(
                norad_id=debris_info['norad_id']
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create new debris object
            debris = DebrisObject(
                norad_id=debris_info['norad_id'],
                name=debris_info['name'],
                type=debris_info['type'],
                rcs_size=debris_info['rcs_size'],
                country=debris_info['country'],
                apogee_km=debris_info['apogee_km'],
                perigee_km=debris_info['perigee_km'],
                inclination_deg=debris_info['inclination_deg'],
                period_minutes=debris_info['period_minutes'],
                last_updated=datetime.now()
            )
            
            session.add(debris)
            added += 1
        
        session.commit()
        return added, skipped
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        session.close()

def main():
    """Main function to add debris"""
    
    print("=" * 80)
    print("ADDING DEBRIS FOR BETTER ACCURACY")
    print("=" * 80)
    
    # Generate debris
    print("\nGenerating debris objects...")
    leo_debris = generate_leo_debris(100)
    print(f"✓ Generated {len(leo_debris)} LEO debris objects")
    
    meo_debris = generate_meo_debris(50)
    print(f"✓ Generated {len(meo_debris)} MEO debris objects")
    
    geo_debris = generate_geo_debris(30)
    print(f"✓ Generated {len(geo_debris)} GEO debris objects")
    
    heo_debris = generate_heo_debris(20)
    print(f"✓ Generated {len(heo_debris)} HEO debris objects")
    
    all_debris = leo_debris + meo_debris + geo_debris + heo_debris
    print(f"\nTotal debris to add: {len(all_debris)}")
    
    # Add to database
    print("\nAdding to database...")
    added, skipped = add_debris_to_database(all_debris)
    
    print("\n" + "=" * 80)
    print("DEBRIS ADDITION COMPLETE")
    print("=" * 80)
    print(f"Added: {added} debris objects")
    print(f"Skipped (already exist): {skipped}")
    
    # Show final statistics
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        total_debris = session.query(DebrisObject).count()
        
        # Count by orbit
        all_debris_objs = session.query(DebrisObject).all()
        by_orbit = {'LEO': 0, 'MEO': 0, 'GEO': 0, 'HEO': 0}
        
        for debris in all_debris_objs:
            if debris.apogee_km and debris.perigee_km:
                avg_alt = (debris.apogee_km + debris.perigee_km) / 2
                if avg_alt < 2000:
                    by_orbit['LEO'] += 1
                elif avg_alt < 35000:
                    by_orbit['MEO'] += 1
                elif avg_alt < 36000:
                    by_orbit['GEO'] += 1
                else:
                    by_orbit['HEO'] += 1
        
        print("\n" + "=" * 80)
        print("FINAL DEBRIS DISTRIBUTION")
        print("=" * 80)
        for orbit, count in by_orbit.items():
            percentage = (count / total_debris * 100) if total_debris > 0 else 0
            print(f"{orbit}: {count} debris objects ({percentage:.1f}%)")
        
        print(f"\nTotal debris in database: {total_debris}")
        
        # Calculate collision pairs
        from database.models import Satellite
        total_satellites = session.query(Satellite).count()
        collision_pairs = total_satellites * total_debris
        
        print(f"\nCollision analysis pairs: {total_satellites} satellites × {total_debris} debris = {collision_pairs:,} pairs")
        
        if collision_pairs > 50000:
            print("\n⚠ Warning: Large number of collision pairs may impact performance")
            print("  Consider using intelligent filtering or parallel processing")
        else:
            print("\n✓ Collision pair count is manageable for real-time analysis")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
