"""
Fetch TLE (Two-Line Element) data from Celestrak API
TLE contains orbital parameters for satellite position tracking
"""

import requests
import os

class TLEFetcher:
    """Download and save satellite TLE data from Celestrak"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.base_url = "https://celestrak.org/NORAD/elements/gp.php"
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_tle(self, satellite_id, filename=None):
        """
        Fetch TLE data for a specific satellite
        
        Args:
            satellite_id: NORAD catalog number or satellite name
            filename: Output filename to save TLE data (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if filename is None:
            filename = f"sat_{satellite_id}.txt"
        try:
            # Celestrak API endpoint
            params = {
                'CATNR': satellite_id,
                'FORMAT': 'TLE'
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
            except requests.exceptions.SSLError:
                # Fallback: retry without SSL verification (self-signed / missing cert chain)
                import warnings
                warnings.warn("SSL verification failed, retrying without verification", stacklevel=2)
                response = requests.get(self.base_url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            
            # Save to file — strip blank lines so the file is always exactly 3 lines
            filepath = os.path.join(self.data_dir, filename)
            clean_lines = [l for l in response.text.splitlines() if l.strip()]
            with open(filepath, 'w') as f:
                f.write('\n'.join(clean_lines) + '\n')
            
            print(f"[OK] Successfully downloaded TLE data for {satellite_id}")
            print(f"  Saved to: {filepath}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching TLE data: {e}")
            return False
    
    def fetch_multiple(self, satellites):
        """
        Fetch TLE data for multiple satellites
        
        Args:
            satellites: Dict of {satellite_id: filename}
        """
        print("=" * 50)
        print("Fetching TLE Data from Celestrak")
        print("=" * 50)
        
        success_count = 0
        for sat_id, filename in satellites.items():
            if self.fetch_tle(sat_id, filename):
                success_count += 1
            print()
        
        print(f"Downloaded {success_count}/{len(satellites)} TLE files successfully")
        print("=" * 50)

def main():
    """Download TLE data for ISS and debris objects"""
    
    fetcher = TLEFetcher()
    
    # Define satellites to track
    # NORAD IDs: Using active, well-tracked satellites
    satellites = {
        '25544': 'iss.txt',           # International Space Station
        '43013': 'debris1.txt',        # HST (Hubble Space Telescope) - active, well-tracked
    }
    
    fetcher.fetch_multiple(satellites)

if __name__ == "__main__":
    main()
