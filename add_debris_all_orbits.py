"""
Add debris objects from all orbital regions (LEO, MEO, GEO)
Provides comprehensive debris coverage for collision analysis
"""

from database.db_manager import get_db_manager
from database.models import DebrisObject
from datetime import datetime
import requests
import time

# Space-Track.org credentials (you'll need to set these)
SPACETRACK_USERNAME = "your_username"  # Replace with your username
SPACETRACK_PASSWORD = "your_password"  # Replace with your password

def login_spacetrack():
    """Login to Space-Track.org and get session"""
    session = requests.Session()
    login_url = 'https://www.space-track.org/ajaxauth/login'
    
    try:
        response = session.post(login_url, data={
            'identity': SPACETRACK_USERNAME,
            'password': SPACETRACK_PASSWORD
        })
        
        if response.status_code == 200:
            print("✓ Logged in to Space-Track.org")
            return session
        else:
            print(f"✗ Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def get_debris_by_altitude(session, min_altitude, max_altitude, limit=50):
    """
    Get debris objects in a specific altitude range
    
    Args:
        session: Space-Track session
        min_altitude: Minimum altitude in km
        max_altitude: Maximum altitude in km
        limit: Maximum number of objects to retrieve
    """
    # Convert altitude to period (approximate)
    # Using Kepler's third law: T = 2π√(a³/μ)
    # where a = altitude + Earth radius (6371 km)
    import math
    
    def altitude_to_period(alt_km):
        """Convert altitude to orbital period in minutes"""
        a = (alt_km + 6371) * 1000  # semi-major axis in meters
        mu = 3.986004418e14  # Earth's gravitational parameter
        period_seconds = 2 * math.pi * math.sqrt(a**3 / mu)
        return period_seconds / 60  # convert to minutes
    
    min_period = altitude_to_period(min_altitude)
    max_period = altitude_to_period(max_altitude)
    
    # Query Space-Track for debris in this period range
    query_url = (
        f'https://www.space-track.org/basicspacedata/query/class/gp/'
        f'OBJECT_TYPE/DEBRIS/'
        f'PERIOD/{min_period:.2f}--{max_period:.2f}/'
        f'orderby/NORAD_CAT_ID/limit/{limit}/format/json'
    )
    
    try:
        response = session.get(query_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Query failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Query error: {e}")
        return []

def add_debris_manual():
    """
    Add representative debris manually (doesn't require Space-Track)
    This creates synthetic debris objects for testing
    """
    
    print("=" * 80)
    print("ADDING DEBRIS FROM ALL ORBITS (MANUAL MODE)")
    print("=" * 80)
    
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    # Representative debris objects across different orbits
    debris_data = [
        # LEO Debris (200-2000 km)
        {
            'norad_id': 'DEB-LEO-001',
            'name': 'Cosmos 2251 Debris Fragment',
            'type': 'DEBRIS',
            'rcs_size': 'MEDIUM',
            'country': 'CIS',
            'apogee_km': 850,
            'perigee_km': 780,
            'inclination_deg': 74.0,
            'period_minutes': 101.5
        },
        {
            'norad_id': 'DEB-LEO-002',
            'name': 'Iridium 33 Debris Fragment',
            'type': 'DEBRIS',
            'rcs_size': 'SMALL',
            'country': 'US',
            'apogee_km': 790,
            'perigee_km': 770,
            'inclination_deg': 86.4,
            'period_minutes': 100.4
        },
        {
            'norad_id': 'DEB-LEO-003',
            'name': 'Fengyun-1C Debris',
            'type': 'DEBRIS',
            'rcs_size': 'LARGE',
            'country': 'PRC',
            'apogee_km': 870,
            'perigee_km': 850,
            'inclination_deg': 98.8,
            'period_minutes': 102.8
        },
        {
            'norad_id': 'DEB-LEO-004',
            'name': 'SL-16 R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'CIS',
            'apogee_km': 650,
            'perigee_km': 620,
            'inclination_deg': 51.6,
            'period_minutes': 97.2
        },
        {
            'norad_id': 'DEB-LEO-005',
            'name': 'Delta 2 R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'US',
            'apogee_km': 720,
            'perigee_km': 700,
            'inclination_deg': 98.2,
            'period_minutes': 99.1
        },
        {
            'norad_id': 'DEB-LEO-006',
            'name': 'Ariane 5 R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'FR',
            'apogee_km': 580,
            'perigee_km': 560,
            'inclination_deg': 6.0,
            'period_minutes': 95.8
        },
        {
            'norad_id': 'DEB-LEO-007',
            'name': 'CZ-4B R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'PRC',
            'apogee_km': 800,
            'perigee_km': 780,
            'inclination_deg': 98.5,
            'period_minutes': 100.8
        },
        {
            'norad_id': 'DEB-LEO-008',
            'name': 'H-2A R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'JPN',
            'apogee_km': 680,
            'perigee_km': 660,
            'inclination_deg': 97.8,
            'period_minutes': 98.2
        },
        {
            'norad_id': 'DEB-LEO-009',
            'name': 'PSLV R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'IND',
            'apogee_km': 740,
            'perigee_km': 720,
            'inclination_deg': 98.6,
            'period_minutes': 99.5
        },
        {
            'norad_id': 'DEB-LEO-010',
            'name': 'Satellite Fragmentation Debris',
            'type': 'DEBRIS',
            'rcs_size': 'SMALL',
            'country': 'US',
            'apogee_km': 550,
            'perigee_km': 530,
            'inclination_deg': 53.0,
            'period_minutes': 95.2
        },
        
        # MEO Debris (2000-35000 km)
        {
            'norad_id': 'DEB-MEO-001',
            'name': 'GPS IIA R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'US',
            'apogee_km': 20350,
            'perigee_km': 20150,
            'inclination_deg': 55.0,
            'period_minutes': 717.9
        },
        {
            'norad_id': 'DEB-MEO-002',
            'name': 'Glonass R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'CIS',
            'apogee_km': 19200,
            'perigee_km': 19000,
            'inclination_deg': 64.8,
            'period_minutes': 675.5
        },
        {
            'norad_id': 'DEB-MEO-003',
            'name': 'Galileo R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'FR',
            'apogee_km': 23300,
            'perigee_km': 23200,
            'inclination_deg': 56.0,
            'period_minutes': 844.8
        },
        {
            'norad_id': 'DEB-MEO-004',
            'name': 'Beidou R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'PRC',
            'apogee_km': 21600,
            'perigee_km': 21500,
            'inclination_deg': 55.5,
            'period_minutes': 762.8
        },
        {
            'norad_id': 'DEB-MEO-005',
            'name': 'Navigation Satellite Debris',
            'type': 'DEBRIS',
            'rcs_size': 'SMALL',
            'country': 'US',
            'apogee_km': 20400,
            'perigee_km': 20200,
            'inclination_deg': 55.2,
            'period_minutes': 720.5
        },
        
        # GEO Debris (35000-36000 km)
        {
            'norad_id': 'DEB-GEO-001',
            'name': 'Intelsat R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'US',
            'apogee_km': 35900,
            'perigee_km': 35700,
            'inclination_deg': 0.1,
            'period_minutes': 1436.1
        },
        {
            'norad_id': 'DEB-GEO-002',
            'name': 'Ariane 4 R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'FR',
            'apogee_km': 35850,
            'perigee_km': 35750,
            'inclination_deg': 0.2,
            'period_minutes': 1435.8
        },
        {
            'norad_id': 'DEB-GEO-003',
            'name': 'Proton R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'CIS',
            'apogee_km': 35920,
            'perigee_km': 35780,
            'inclination_deg': 0.3,
            'period_minutes': 1436.3
        },
        {
            'norad_id': 'DEB-GEO-004',
            'name': 'CZ-3B R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'PRC',
            'apogee_km': 35880,
            'perigee_km': 35720,
            'inclination_deg': 0.4,
            'period_minutes': 1435.9
        },
        {
            'norad_id': 'DEB-GEO-005',
            'name': 'GEO Satellite Debris',
            'type': 'DEBRIS',
            'rcs_size': 'SMALL',
            'country': 'US',
            'apogee_km': 35800,
            'perigee_km': 35790,
            'inclination_deg': 0.1,
            'period_minutes': 1436.0
        },
        
        # HEO Debris (Highly Elliptical Orbits)
        {
            'norad_id': 'DEB-HEO-001',
            'name': 'Molniya R/B Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'CIS',
            'apogee_km': 39800,
            'perigee_km': 500,
            'inclination_deg': 63.4,
            'period_minutes': 717.8
        },
        {
            'norad_id': 'DEB-HEO-002',
            'name': 'GTO Transfer Stage Debris',
            'type': 'ROCKET BODY',
            'rcs_size': 'MEDIUM',
            'country': 'US',
            'apogee_km': 35800,
            'perigee_km': 200,
            'inclination_deg': 7.0,
            'period_minutes': 630.5
        },
        {
            'norad_id': 'DEB-HEO-003',
            'name': 'Tundra Orbit R/B Fragment',
            'type': 'ROCKET BODY',
            'rcs_size': 'LARGE',
            'country': 'CIS',
            'apogee_km': 47100,
            'perigee_km': 24700,
            'inclination_deg': 63.4,
            'period_minutes': 1436.1
        },
        {
            'norad_id': 'DEB-HEO-004',
            'name': 'Elliptical Orbit Debris',
            'type': 'DEBRIS',
            'rcs_size': 'SMALL',
            'country': 'FR',
            'apogee_km': 42000,
            'perigee_km': 600,
            'inclination_deg': 56.0,
            'period_minutes': 750.2
        },
        {
            'norad_id': 'DEB-HEO-005',
            'name': 'Supersync Orbit Debris',
            'type': 'DEBRIS',
            'rcs_size': 'MEDIUM',
            'country': 'US',
            'apogee_km': 38000,
            'perigee_km': 35600,
            'inclination_deg': 2.5,
            'period_minutes': 1480.3
        }
    ]
    
    try:
        added = 0
        skipped = 0
        
        for debris_info in debris_data:
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
                last_updated=datetime.utcnow()
            )
            
            session.add(debris)
            added += 1
            
            # Calculate average altitude for display
            avg_alt = (debris_info['apogee_km'] + debris_info['perigee_km']) / 2
            orbit_type = "LEO" if avg_alt < 2000 else "MEO" if avg_alt < 35000 else "GEO" if avg_alt < 36000 else "HEO"
            
            print(f"✓ Added: {debris_info['name']} ({orbit_type}, {avg_alt:.0f} km)")
        
        session.commit()
        
        print("\n" + "=" * 80)
        print("DEBRIS ADDITION COMPLETE")
        print("=" * 80)
        print(f"Added: {added} debris objects")
        print(f"Skipped (already exist): {skipped}")
        
        # Show distribution
        print("\n" + "=" * 80)
        print("DEBRIS DISTRIBUTION BY ORBIT")
        print("=" * 80)
        
        all_debris = session.query(DebrisObject).all()
        by_orbit = {'LEO': 0, 'MEO': 0, 'GEO': 0, 'HEO': 0}
        
        for debris in all_debris:
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
        
        for orbit, count in by_orbit.items():
            print(f"{orbit}: {count} debris objects")
        
        print(f"\nTotal debris in database: {len(all_debris)}")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if '--spacetrack' in sys.argv:
        print("Space-Track mode not yet implemented")
        print("Using manual mode instead...\n")
    
    add_debris_manual()
