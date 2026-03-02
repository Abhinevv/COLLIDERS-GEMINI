"""Test Space-Track connection with new account"""
from debris.space_track import SpaceTrackAPI

api = SpaceTrackAPI()

print("Testing Space-Track connection...")
print(f"Username: {api.username}")

if api.authenticate():
    print("✓ Authentication successful!")
    
    # Try a simple query
    print("\nTrying to fetch 5 debris objects...")
    try:
        debris = api.search_debris(object_type='debris', limit=5)
        if debris:
            print(f"✓ Got {len(debris)} debris objects")
            print(f"First object: {debris[0].get('OBJECT_NAME', 'Unknown')}")
        else:
            print("✗ No debris returned (empty list)")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("✗ Authentication failed")
