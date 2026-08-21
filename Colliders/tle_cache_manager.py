"""
TLE Cache Manager for COLLIDERS
Manages cached TLE data to avoid excessive Space-Track API calls
"""

import os
import json
from datetime import datetime, timedelta


class TLECacheManager:
    """Manages TLE data caching"""

    # Minimum minutes between Space-Track queries (rate-limit compliance)
    MIN_QUERY_INTERVAL_MINUTES = 60

    def __init__(self, cache_file='data/tle_cache/tle_cache.json'):
        self.cache_file = cache_file
        self.cache_data = {}
        self._load_cache()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache_data = json.load(f)
            else:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                self.cache_data = {
                    'last_updated': None,
                    'satellites': {},
                    'debris': {}
                }
                self._save_cache()
        except Exception as e:
            print(f"Warning: Could not load TLE cache: {e}")
            self.cache_data = {
                'last_updated': None,
                'satellites': {},
                'debris': {}
            }

    def _save_cache(self):
        """Persist cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save TLE cache: {e}")

    # ------------------------------------------------------------------ #
    # Simple get/set (original API — kept for backwards compat)
    # ------------------------------------------------------------------ #

    def get_tle(self, norad_id):
        """Return raw TLE dict for a NORAD ID, or None."""
        norad_str = str(norad_id)
        if norad_str in self.cache_data.get('satellites', {}):
            return self.cache_data['satellites'][norad_str].get('tle')
        if norad_str in self.cache_data.get('debris', {}):
            return self.cache_data['debris'][norad_str].get('tle')
        return None

    def cache_tle(self, norad_id, tle_data, object_type='satellite'):
        """Store a TLE dict for the given NORAD ID."""
        norad_str = str(norad_id)
        bucket = 'satellites' if object_type == 'satellite' else 'debris'
        if bucket not in self.cache_data:
            self.cache_data[bucket] = {}
        self.cache_data[bucket][norad_str] = {
            'tle': tle_data,
            'cached_at': datetime.now().isoformat()
        }
        self._save_cache()

    # ------------------------------------------------------------------ #
    # Extended API — used by api.py debris job worker & refresh endpoint
    # ------------------------------------------------------------------ #

    def get_tle_from_cache(self, norad_id):
        """
        Return a TLE dict for *norad_id* if it is present in the cache,
        otherwise return None.

        The returned dict has the shape:
            {
                'name':     str,
                'tle_line1': str,
                'tle_line2': str,
                'cached_at': str  (ISO-8601)
            }
        """
        norad_str = str(norad_id)

        # Check debris bucket first (most common caller path)
        for bucket in ('debris', 'satellites'):
            entry = self.cache_data.get(bucket, {}).get(norad_str)
            if entry:
                tle = entry.get('tle') or entry  # handle both nested and flat
                if isinstance(tle, dict) and ('tle_line1' in tle or 'line1' in tle):
                    return {
                        'name': tle.get('name', f'OBJECT {norad_str}'),
                        'tle_line1': tle.get('tle_line1') or tle.get('line1', ''),
                        'tle_line2': tle.get('tle_line2') or tle.get('line2', ''),
                        'cached_at': entry.get('cached_at', '')
                    }
        return None

    def get_cache_age_minutes(self):
        """
        Return how many minutes have elapsed since the cache was last
        bulk-updated via save_bulk_tles().  Returns a very large number
        (9999) when the cache has never been updated so callers treat it
        as stale.
        """
        last = self.cache_data.get('last_updated')
        if not last:
            return 9999.0
        try:
            updated_dt = datetime.fromisoformat(last)
            delta = datetime.now() - updated_dt
            return delta.total_seconds() / 60.0
        except Exception:
            return 9999.0

    def can_query_spacetrack(self):
        """
        Return (bool, reason_str).

        Returns (True, 'ok') when a Space-Track bulk query is permitted,
        or (False, <reason>) when it should be skipped to comply with
        Space-Track's usage policy (max ~1 bulk request per hour).
        """
        age_min = self.get_cache_age_minutes()
        if age_min < self.MIN_QUERY_INTERVAL_MINUTES:
            remaining = int(self.MIN_QUERY_INTERVAL_MINUTES - age_min)
            return False, (
                f"Cache refreshed {age_min:.1f} min ago — "
                f"please wait {remaining} more minute(s) "
                f"(Space-Track rate-limit compliance)."
            )
        return True, 'ok'

    def save_bulk_tles(self, data):
        """
        Ingest a list of GP records returned by the Space-Track bulk API
        and store them in the cache.

        Each record is expected to be a dict with at minimum:
            NORAD_CAT_ID, OBJECT_NAME, TLE_LINE1, TLE_LINE2

        Returns the number of objects successfully stored.
        """
        if not isinstance(data, list):
            return 0

        count = 0
        now_iso = datetime.now().isoformat()

        for record in data:
            norad_id = str(record.get('NORAD_CAT_ID', '')).strip()
            line1 = str(record.get('TLE_LINE1', '')).strip()
            line2 = str(record.get('TLE_LINE2', '')).strip()
            name = str(record.get('OBJECT_NAME', f'OBJECT {norad_id}')).strip()

            if not norad_id or not line1 or not line2:
                continue

            # Determine bucket by object type
            obj_type = str(record.get('OBJECT_TYPE', '')).upper()
            bucket = 'satellites' if obj_type in ('PAYLOAD',) else 'debris'

            if bucket not in self.cache_data:
                self.cache_data[bucket] = {}

            self.cache_data[bucket][norad_id] = {
                'tle': {
                    'name': name,
                    'tle_line1': line1,
                    'tle_line2': line2
                },
                'cached_at': now_iso
            }
            count += 1

        if count > 0:
            self.cache_data['last_updated'] = now_iso
            self._save_cache()

        return count

    # ------------------------------------------------------------------ #
    # Stats / admin
    # ------------------------------------------------------------------ #

    def get_cache_stats(self):
        """Return a summary dict for the /api/tle_cache/status endpoint."""
        satellites_count = len(self.cache_data.get('satellites', {}))
        debris_count = len(self.cache_data.get('debris', {}))
        last_updated = self.cache_data.get('last_updated')
        age_min = self.get_cache_age_minutes()

        return {
            'satellites_cached': satellites_count,
            'debris_cached': debris_count,
            'total_objects': satellites_count + debris_count,
            'last_updated': last_updated or 'Never',
            'cache_age_minutes': round(age_min, 1) if age_min < 9999 else None,
            'cache_file': self.cache_file,
            'cache_exists': os.path.exists(self.cache_file),
            'can_query_spacetrack': self.can_query_spacetrack()[0]
        }

    def refresh_cache(self):
        """Update the last_updated timestamp (placeholder for manual refresh)."""
        self.cache_data['last_updated'] = datetime.now().isoformat()
        self._save_cache()
        return {
            'status': 'success',
            'message': 'Cache timestamp updated',
            'updated_at': self.cache_data['last_updated']
        }


# Global singleton
_cache_manager = None


def get_cache_manager():
    """Return the global TLECacheManager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = TLECacheManager()
    return _cache_manager
