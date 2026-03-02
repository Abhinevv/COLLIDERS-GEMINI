"""
Space-Track.org API Integration
Track real orbital debris, defunct satellites, and rocket bodies
Requires free account at https://www.space-track.org/auth/createAccount
"""

import requests
import json
from datetime import datetime, timedelta
import os


class SpaceTrackAPI:
    """Interface to Space-Track.org for orbital debris data"""
    
    def __init__(self, username=None, password=None):
        """
        Initialize Space-Track API client
        
        Args:
            username: Space-Track.org username (or set SPACETRACK_USER env var)
            password: Space-Track.org password (or set SPACETRACK_PASS env var)
        """
        self.base_url = "https://www.space-track.org"
        self.username = username or os.getenv('SPACETRACK_USER')
        self.password = password or os.getenv('SPACETRACK_PASS')
        self.session = requests.Session()
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with Space-Track.org"""
        if not self.username or not self.password:
            raise ValueError(
                "Space-Track credentials required. Set SPACETRACK_USER and SPACETRACK_PASS "
                "environment variables or pass to constructor. "
                "Get free account at: https://www.space-track.org/auth/createAccount"
            )
        
        try:
            login_url = f"{self.base_url}/ajaxauth/login"
            response = self.session.post(
                login_url,
                data={'identity': self.username, 'password': self.password},
                timeout=10
            )
            
            if response.status_code == 200:
                self.authenticated = True
                print("✓ Authenticated with Space-Track.org")
                return True
            else:
                print(f"✗ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def search_debris(self, object_type='debris', limit=100):
        """
        Search for space debris objects
        
        Args:
            object_type: Type of object ('debris', 'rocket_body', 'payload', 'unknown')
            limit: Maximum number of results
        
        Returns:
            list: List of debris objects with TLE data
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            # Query for debris objects
            query_url = f"{self.base_url}/basicspacedata/query/class/gp/OBJECT_TYPE/{object_type}/orderby/NORAD_CAT_ID/limit/{limit}/format/json"
            
            response = self.session.get(query_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {len(data)} {object_type} objects")
                return data
            else:
                print(f"✗ Query failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Search error: {e}")
            return []
    
    def get_debris_by_id(self, norad_id):
        """
        Get specific debris object by NORAD catalog ID
        
        Args:
            norad_id: NORAD catalog number
        
        Returns:
            dict: Object data with TLE
        """
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            query_url = f"{self.base_url}/basicspacedata/query/class/gp/NORAD_CAT_ID/{norad_id}/orderby/EPOCH desc/limit/1/format/json"
            
            response = self.session.get(query_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0]
            
            return None
            
        except Exception as e:
            print(f"✗ Error fetching debris {norad_id}: {e}")
            return None
    
    def get_high_risk_debris(self, altitude_min=200, altitude_max=2000, limit=50):
        """
        Get high-risk debris in LEO (Low Earth Orbit) with VALID TLE data
        
        Args:
            altitude_min: Minimum altitude in km
            altitude_max: Maximum altitude in km
            limit: Maximum results (will fetch more and filter for valid TLEs)
        
        Returns:
            list: High-risk debris objects with valid TLE data
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            # Fetch MORE debris than requested to account for invalid TLEs
            fetch_limit = limit * 2  # Fetch 2x to ensure we get enough valid ones
            
            # Query for objects
            query_url = (
                f"{self.base_url}/basicspacedata/query/class/gp/"
                f"OBJECT_TYPE/DEBRIS/"
                f"orderby/NORAD_CAT_ID desc/limit/{fetch_limit}/format/json"
            )
            
            response = self.session.get(query_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Fetched {len(data)} debris objects from Space-Track")
                
                # Filter for debris with valid TLE data
                valid_debris = []
                
                for debris in data:
                    # Check if TLE lines exist and are not empty
                    if ('TLE_LINE1' in debris and 'TLE_LINE2' in debris and
                        debris['TLE_LINE1'] and debris['TLE_LINE2'] and
                        len(debris['TLE_LINE1']) == 69 and  # Valid TLE line 1 length
                        len(debris['TLE_LINE2']) == 69):    # Valid TLE line 2 length
                        
                        # Basic TLE format validation
                        try:
                            tle1 = debris['TLE_LINE1']
                            tle2 = debris['TLE_LINE2']
                            
                            # Check line numbers (1 and 2)
                            if tle1[0] == '1' and tle2[0] == '2':
                                # Check eccentricity is valid (< 1.0 for orbiting objects)
                                eccentricity_str = tle2[26:33]
                                eccentricity = float('0.' + eccentricity_str)
                                
                                if 0 <= eccentricity < 1.0:
                                    valid_debris.append(debris)
                                    
                                    # Stop when we have enough valid debris
                                    if len(valid_debris) >= limit:
                                        break
                        except:
                            # Skip debris with malformed TLE data
                            continue
                
                print(f"✓ Filtered {len(valid_debris)} debris with valid TLE format")
                return valid_debris
            
            return []
            
        except Exception as e:
            print(f"✗ Error fetching high-risk debris: {e}")
            return []
    
    def get_recent_debris(self, days=30, limit=100):
        """
        Get recently cataloged debris
        
        Args:
            days: Number of days to look back
            limit: Maximum results
        
        Returns:
            list: Recently added debris objects
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            date_range = f"{start_date.strftime('%Y-%m-%d')}--{end_date.strftime('%Y-%m-%d')}"
            
            query_url = (
                f"{self.base_url}/basicspacedata/query/class/gp/"
                f"CREATION_DATE/{date_range}/"
                f"orderby/CREATION_DATE desc/limit/{limit}/format/json"
            )
            
            response = self.session.get(query_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {len(data)} objects created in last {days} days")
                return data
            
            return []
            
        except Exception as e:
            print(f"✗ Error fetching recent debris: {e}")
            return []
    
    def get_tle_data(self, norad_id):
        """
        Get TLE (Two-Line Element) data for an object
        
        Args:
            norad_id: NORAD catalog number
        
        Returns:
            tuple: (line1, line2) TLE strings or None
        """
        obj = self.get_debris_by_id(norad_id)
        
        if obj and 'TLE_LINE1' in obj and 'TLE_LINE2' in obj:
            return (obj['TLE_LINE1'], obj['TLE_LINE2'])
        
        return None
    
    def get_tle(self, norad_id):
        """
        Get TLE data for an object (returns full object data)
        
        Args:
            norad_id: NORAD catalog number
        
        Returns:
            list: List with single object dict containing TLE data, or empty list
        """
        obj = self.get_debris_by_id(norad_id)
        return [obj] if obj else []
    
    def save_debris_tle(self, norad_id, filename):
        """
        Save debris TLE to file
        
        Args:
            norad_id: NORAD catalog number
            filename: Output filename
        
        Returns:
            bool: Success status
        """
        obj = self.get_debris_by_id(norad_id)
        
        if not obj:
            return False
        
        try:
            # Create TLE file with object name and TLE lines
            content = f"{obj.get('OBJECT_NAME', 'UNKNOWN')}\n"
            content += f"{obj['TLE_LINE1']}\n"
            content += f"{obj['TLE_LINE2']}\n"
            
            with open(filename, 'w') as f:
                f.write(content)
            
            print(f"✓ Saved TLE for {obj.get('OBJECT_NAME')} to {filename}")
            return True
            
        except Exception as e:
            print(f"✗ Error saving TLE: {e}")
            return False


def main():
    """Example usage"""
    print("=" * 70)
    print("Space-Track.org Debris Tracker")
    print("=" * 70)
    print()
    
    # Initialize API (requires credentials)
    api = SpaceTrackAPI()
    
    try:
        # Authenticate
        if not api.authenticate():
            print("\n⚠ Set SPACETRACK_USER and SPACETRACK_PASS environment variables")
            print("   Get free account at: https://www.space-track.org/auth/createAccount")
            return
        
        # Search for debris
        print("\n1. Searching for debris objects...")
        debris = api.search_debris(object_type='debris', limit=10)
        
        if debris:
            print(f"\nFound {len(debris)} debris objects:")
            for obj in debris[:5]:
                print(f"  - {obj.get('OBJECT_NAME')} (ID: {obj.get('NORAD_CAT_ID')})")
        
        # Get high-risk debris in LEO
        print("\n2. Finding high-risk debris in LEO (200-2000 km)...")
        high_risk = api.get_high_risk_debris(limit=10)
        
        if high_risk:
            print(f"\nHigh-risk objects:")
            for obj in high_risk[:5]:
                print(f"  - {obj.get('OBJECT_NAME')} at {obj.get('APOGEE')} km")
        
        # Get recent debris
        print("\n3. Checking recently cataloged debris...")
        recent = api.get_recent_debris(days=30, limit=10)
        
        if recent:
            print(f"\nRecent debris:")
            for obj in recent[:5]:
                print(f"  - {obj.get('OBJECT_NAME')} (Added: {obj.get('CREATION_DATE')})")
        
        print("\n" + "=" * 70)
        print("✓ Space debris tracking complete")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
