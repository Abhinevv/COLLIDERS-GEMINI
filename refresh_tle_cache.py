"""
Manual TLE Cache Refresh Script
Run this ONLY during off-peak hours and MAX once per hour
"""

import requests
import sys
from tle_cache_manager import get_cache_manager
from debris.space_track import SpaceTrackAPI


def main():
    print("="*70)
    print("TLE CACHE REFRESH - Space-Track.org Compliant")
    print("="*70)
    
    cache = get_cache_manager()
    
    # Check cache status
    stats = cache.get_cache_stats()
    print(f"\nCurrent Cache Status:")
    print(f"  Fresh: {stats['cache_fresh']}")
    print(f"  Age: {stats['cache_age_minutes']} minutes" if stats['cache_age_minutes'] else "  Age: Never updated")
    print(f"  Objects: {stats['object_count']}")
    print(f"  Queries Today: {stats['queries_today']}")
    
    # Check if we can query
    can_query, reason = cache.can_query_spacetrack()
    print(f"\n  Can Query: {can_query}")
    print(f"  Status: {reason}")
    
    if not can_query:
        print("\n❌ Cannot refresh cache at this time.")
        print(f"   Reason: {reason}")
        return 1
    
    # Confirm with user
    print("\n⚠️  WARNING: This will query Space-Track.org")
    print("   - Uses bulk query (compliant)")
    print("   - Fetches ALL active objects")
    print("   - Should only be done once per hour")
    print("   - Only during off-peak times")
    
    response = input("\nProceed with cache refresh? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return 0
    
    # Initialize Space-Track API
    print("\nInitializing Space-Track API...")
    api = SpaceTrackAPI()
    
    if not api.authenticate():
        print("❌ Authentication failed")
        return 1
    
    print("✓ Authenticated")
    
    # Use bulk query (Space-Track compliant)
    print("\nFetching TLE data (bulk query)...")
    print("Query: /basicspacedata/query/class/gp/decay_date/null-val/CREATION_DATE/>now-0.042/format/json")
    
    try:
        query_url = (
            f"{api.base_url}/basicspacedata/query/class/gp/"
            f"decay_date/null-val/CREATION_DATE/>now-0.042/format/json"
        )
        
        response = api.session.get(query_url, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Received {len(data)} objects")
            
            # Save to cache
            print("\nSaving to cache...")
            count = cache.save_bulk_tles(data)
            print(f"✓ Saved {count} TLEs to cache")
            
            # Show updated stats
            stats = cache.get_cache_stats()
            print(f"\nUpdated Cache Status:")
            print(f"  Fresh: {stats['cache_fresh']}")
            print(f"  Age: {stats['cache_age_minutes']:.1f} minutes")
            print(f"  Objects: {stats['object_count']}")
            print(f"  Queries Today: {stats['queries_today']}")
            
            print("\n✅ Cache refresh complete!")
            print("   Next refresh allowed in 60 minutes")
            
            return 0
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
