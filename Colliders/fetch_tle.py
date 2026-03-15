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
    
    def fetch_tle(self, satellite_id, filename):
        """
        Fetch TLE data for a specific satellite
        
        Args:
            satellite_id: NORAD catalog number or satellite name
            filename: Output filename to save TLE data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Celestrak API endpoint
            params = {
                'CATNR': satellite_id,
                'FORMAT': 'TLE'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Save to file
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'w') as f:
                f.write(response.text)
            
            print(f"✓ Successfully downloaded TLE data for {satellite_id}")
            print(f"  Saved to: {filepath}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching TLE data: {e}")
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
