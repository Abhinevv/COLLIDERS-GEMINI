"""
TLE Cache Manager - Space-Track.org Compliant
Implements proper caching to avoid API violations
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


class TLECacheManager:
    """
    Manages local TLE cache with Space-Track.org compliance
    - Maximum 1 query per hour
    - Bulk fetching only
    - Off-peak timing
    """
    
    def __init__(self, cache_dir='data/tle_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / 'cache_metadata.json'
        self.min_cache_age_seconds = 3600  # 1 hour minimum
        
    def get_cache_metadata(self):
        """Get cache metadata (last update time, object count)"""
        if not self.metadata_file.exists():
            return {
                'last_update': None,
                'last_update_timestamp': 0,
                'object_count': 0,
                'query_count_today': 0,
                'last_query_date': None
            }
        
        with open(self.metadata_file, 'r') as f:
            return json.load(f)
    
    def save_cache_metadata(self, metadata):
        """Save cache metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def is_cache_fresh(self):
        """Check if cache is fresh (less than 1 hour old)"""
        metadata = self.get_cache_metadata()
        if not metadata['last_update']:
            return False
        
        last_update = metadata['last_update_timestamp']
        age_seconds = time.time() - last_update
        
        return age_seconds < self.min_cache_age_seconds
    
    def get_cache_age_minutes(self):
        """Get cache age in minutes"""
        metadata = self.get_cache_metadata()
        if not metadata['last_update']:
            return float('inf')
        
        age_seconds = time.time() - metadata['last_update_timestamp']
        return age_seconds / 60
    
    def can_query_spacetrack(self):
        """Check if we can query Space-Track (respects 1-hour limit)"""
        if not self.is_cache_fresh():
            # Check if we're in off-peak time (not XX:00 or XX:30)
            now = datetime.now()
            minute = now.minute
            
            # Avoid busy periods (within 5 min of top/bottom of hour)
            if (0 <= minute <= 5) or (25 <= minute <= 35) or (55 <= minute <= 59):
                return False, "Busy period - wait for off-peak time (10-20 min past hour)"
            
            return True, "Cache expired and off-peak time"
        
        age_min = self.get_cache_age_minutes()
        return False, f"Cache is fresh ({age_min:.1f} min old, need 60+ min)"
    
    def get_tle_from_cache(self, norad_id):
        """Get TLE for specific NORAD ID from cache"""
        tle_file = self.cache_dir / f'tle_{norad_id}.txt'
        
        if not tle_file.exists():
            return None
        
        # Check if cache is stale
        if not self.is_cache_fresh():
            return None
        
        with open(tle_file, 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 3:
                return {
                    'name': lines[0],
                    'tle_line1': lines[1],
                    'tle_line2': lines[2]
                }
        
        return None
    
    def save_tle_to_cache(self, norad_id, name, tle_line1, tle_line2):
        """Save individual TLE to cache"""
        tle_file = self.cache_dir / f'tle_{norad_id}.txt'
        
        with open(tle_file, 'w') as f:
            f.write(f"{name}\n")
            f.write(f"{tle_line1}\n")
            f.write(f"{tle_line2}\n")
    
    def save_bulk_tles(self, tle_data_list):
        """
        Save bulk TLE data to cache
        
        Args:
            tle_data_list: List of dicts with NORAD_CAT_ID, OBJECT_NAME, TLE_LINE1, TLE_LINE2
        """
        count = 0
        for obj in tle_data_list:
            norad_id = obj.get('NORAD_CAT_ID')
            name = obj.get('OBJECT_NAME', f'OBJECT {norad_id}')
            tle1 = obj.get('TLE_LINE1')
            tle2 = obj.get('TLE_LINE2')
            
            if norad_id and tle1 and tle2:
                self.save_tle_to_cache(norad_id, name, tle1, tle2)
                count += 1
        
        # Update metadata
        metadata = self.get_cache_metadata()
        metadata['last_update'] = datetime.now().isoformat()
        metadata['last_update_timestamp'] = time.time()
        metadata['object_count'] = count
        
        # Track daily query count
        today = datetime.now().date().isoformat()
        if metadata.get('last_query_date') == today:
            metadata['query_count_today'] = metadata.get('query_count_today', 0) + 1
        else:
            metadata['query_count_today'] = 1
            metadata['last_query_date'] = today
        
        self.save_cache_metadata(metadata)
        
        return count
    
    def get_cache_stats(self):
        """Get cache statistics"""
        metadata = self.get_cache_metadata()
        age_min = self.get_cache_age_minutes()
        is_fresh = self.is_cache_fresh()
        can_query, reason = self.can_query_spacetrack()
        
        return {
            'cache_fresh': is_fresh,
            'cache_age_minutes': age_min if age_min != float('inf') else None,
            'last_update': metadata.get('last_update'),
            'object_count': metadata.get('object_count', 0),
            'can_query_spacetrack': can_query,
            'query_status': reason,
            'queries_today': metadata.get('query_count_today', 0)
        }


# Global cache manager instance
_cache_manager = None

def get_cache_manager():
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = TLECacheManager()
    return _cache_manager


if __name__ == '__main__':
    # Test cache manager
    cache = TLECacheManager()
    stats = cache.get_cache_stats()
    
    print("TLE Cache Statistics:")
    print(f"  Fresh: {stats['cache_fresh']}")
    print(f"  Age: {stats['cache_age_minutes']} minutes")
    print(f"  Objects: {stats['object_count']}")
    print(f"  Can Query: {stats['can_query_spacetrack']}")
    print(f"  Status: {stats['query_status']}")
    print(f"  Queries Today: {stats['queries_today']}")
