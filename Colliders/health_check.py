#!/usr/bin/env python3
"""
COLLIDERS Health Check Script
Verifies that all core components can be imported and initialized
"""

import sys
import os

def check_imports():
    """Check if all required modules can be imported"""
    print("🔔” Checking imports...")
    
    try:
        # Core dependencies
        import numpy
        import flask
        import sqlalchemy
        print("✅ Core dependencies (numpy, flask, sqlalchemy)")
        
        # Database modules
        from database.db_manager import get_db_manager
        from database.models import Base, Satellite, DebrisObject
        print("✅ Database modules")
        
        # Service modules
        from satellites.satellite_manager import SatelliteManager
        from alerts.alert_service import AlertService
        from history.history_service import HistoryService
        print("✅ Service modules")
        
        # Analysis modules
        from debris.analyze import analyze_debris_vs_satellite
        from debris.space_track import SpaceTrackAPI
        print("✅ Analysis modules")
        
        return True
        
    except ImportError as e:
        print(f"âŒ Import error: {e}")
        return False
    except Exception as e:
        print(f"âŒ Unexpected error: {e}")
        return False

def check_database():
    """Check database connectivity"""
    print("\n🗄️ Checking database...")
    
    try:
        from database.db_manager import get_db_manager
        from sqlalchemy import text
        
        db = get_db_manager()
        session = db.get_session()
        
        # Test basic query
        result = session.execute(text('SELECT 1')).scalar()
        session.close()
        
        if result == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("âŒ Database query failed")
            return False
            
    except Exception as e:
        print(f"âŒ Database error: {e}")
        return False

def check_files():
    """Check if essential files exist"""
    print("\n🔔“ Checking essential files...")
    
    essential_files = [
        'api.py',
        'main.py',
        'fetch_tle.py',
        'requirements.txt',
        'frontend/dist/index.html',
        'database/models.py',
        'database/db_manager.py'
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"âŒ Missing files: {missing_files}")
        return False
    else:
        print("✅ All essential files present")
        return True

def main():
    """Run all health checks"""
    print("🛰️ COLLIDERS Health Check")
    print("=" * 40)
    
    checks = [
        check_files(),
        check_imports(),
        check_database()
    ]
    
    print("\n" + "=" * 40)
    
    if all(checks):
        print("🎉 All health checks passed!")
        print("✅ COLLIDERS is ready to run")
        return 0
    else:
        print("âš ï¸ Some health checks failed")
        print("âŒ Please fix the issues above before running")
        return 1

if __name__ == '__main__':
    sys.exit(main())
