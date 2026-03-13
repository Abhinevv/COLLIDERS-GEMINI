"""
TLE Cache Manager for AstroCleanAI
Manages cached TLE data to avoid excessive Space-Track API calls
"""

import os
import json
from datetime import datetime, timedelta


class TLECacheManager:
    """Manages TLE data caching"""
    
    def __init__(self, cache_file='data/tle_cache/tle_cache.json'):
        """Initialize cache manager"""
        self.cache_file = cache_file
        self.cache_data = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache_data = json.load(f)
            else:
                # Create empty cache
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                self.cache_data = {
                    'last_updated': datetime.now().isoformat(),
                    'satellites': {},
                    'debris': {}
                }
                self._save_cache()
        except Exception as e:
            print(f"Warning: Could not load TLE cache: {e}")
            self.cache_data = {
                'last_updated': datetime.now().isoformat(),
                'satellites': {},
                'debris': {}
            }
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save TLE cache: {e}")
    
    def get_tle(self, norad_id):
        """Get TLE data for a NORAD ID"""
        norad_str = str(norad_id)
        
        # Check satellites first
        if norad_str in self.cache_data.get('satellites', {}):
            return self.cache_data['satellites'][norad_str].get('tle')
        
        # Check debris
        if norad_str in self.cache_data.get('debris', {}):
            return self.cache_data['debris'][norad_str].get('tle')
        
        return None
    
    def cache_tle(self, norad_id, tle_data, object_type='satellite'):
        """Cache TLE data"""
        norad_str = str(norad_id)
        
        if object_type not in self.cache_data:
            self.cache_data[object_type] = {}
        
        self.cache_data[object_type][norad_str] = {
            'tle': tle_data,
            'cached_at': datetime.now().isoformat()
        }
        
        self._save_cache()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        satellites_count = len(self.cache_data.get('satellites', {}))
        debris_count = len(self.cache_data.get('debris', {}))
        
        return {
            'satellites_cached': satellites_count,
            'debris_cached': debris_count,
            'total_objects': satellites_count + debris_count,
            'last_updated': self.cache_data.get('last_updated', 'Never'),
            'cache_file': self.cache_file,
            'cache_exists': os.path.exists(self.cache_file)
        }
    
    def refresh_cache(self):
        """Refresh cache (placeholder - would normally fetch from Space-Track)"""
        # For now, just update the timestamp
        self.cache_data['last_updated'] = datetime.now().isoformat()
        self._save_cache()
        
        return {
            'status': 'success',
            'message': 'Cache timestamp updated',
            'updated_at': self.cache_data['last_updated']
        }


# Global cache manager instance
_cache_manager = None

def get_cache_manager():
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = TLECacheManager()
    return _cache_manager