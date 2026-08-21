#!/usr/bin/env python3
"""
COLLIDERS Health Check Script
Verifies that all core components can be imported and initialized
"""

import sys
import os


def check_imports():
    """Check if all required modules can be imported"""
    print("Checking imports...")

    try:
        import numpy
        import flask
        import sqlalchemy
        print("  [OK] Core dependencies (numpy, flask, sqlalchemy)")

        from database.db_manager import get_db_manager
        from database.models import Base, Satellite, DebrisObject
        print("  [OK] Database modules")

        from satellites.satellite_manager import SatelliteManager
        from alerts.alert_service import AlertService
        from history.history_service import HistoryService
        print("  [OK] Service modules")

        from debris.analyze import analyze_debris_vs_satellite
        from debris.space_track import SpaceTrackAPI
        print("  [OK] Analysis modules")

        from tle_cache_manager import get_cache_manager
        print("  [OK] TLE cache manager")

        return True

    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def check_database():
    """Check database connectivity"""
    print("\nChecking database...")

    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite, DebrisObject
        from sqlalchemy import text

        db = get_db_manager()
        session = db.get_session()

        result = session.execute(text('SELECT 1')).scalar()

        sat_count = session.query(Satellite).count()
        debris_count = session.query(DebrisObject).count()
        session.close()

        if result == 1:
            print(f"  [OK] Database connection successful")
            print(f"  [OK] Satellites in DB : {sat_count}")
            print(f"  [OK] Debris in DB     : {debris_count}")
            return True
        else:
            print("  [FAIL] Database query returned unexpected result")
            return False

    except Exception as e:
        print(f"  [FAIL] Database error: {e}")
        return False


def check_files():
    """Check if essential files exist"""
    print("\nChecking essential files...")

    essential_files = [
        'api.py',
        'fetch_tle.py',
        'tle_cache_manager.py',
        'database/models.py',
        'database/db_manager.py',
        'satellites/satellite_manager.py',
        'alerts/alert_service.py',
        'history/history_service.py',
    ]

    all_ok = True
    for file_path in essential_files:
        if os.path.exists(file_path):
            print(f"  [OK] {file_path}")
        else:
            print(f"  [MISSING] {file_path}")
            all_ok = False

    return all_ok


def check_dirs():
    """Ensure required runtime directories exist"""
    print("\nChecking runtime directories...")
    for d in ('data', 'output', 'data/tle_cache'):
        os.makedirs(d, exist_ok=True)
        print(f"  [OK] {d}/")
    return True


def main():
    """Run all health checks"""
    print("COLLIDERS Health Check")
    print("=" * 40)

    checks = [
        check_dirs(),
        check_files(),
        check_imports(),
        check_database(),
    ]

    print("\n" + "=" * 40)

    if all(checks):
        print("All health checks passed!")
        print("COLLIDERS is ready to run.")
        return 0
    else:
        print("Some health checks failed — fix the issues above before starting.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
