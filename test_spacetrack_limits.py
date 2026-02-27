"""Test Space-Track API limits"""
import requests

# Test different limits
limits = [100, 500, 1000, 2000, 5000]

for limit in limits:
    try:
        response = requests.get(
            f'http://localhost:5000/api/space_debris/high_risk?min_altitude=200&max_altitude=2000&limit={limit}',
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('high_risk_debris', []))
            print(f"Limit {limit:5d}: Got {count:5d} debris objects")
            
            if count < limit:
                print(f"  → Maximum available: {count}")
                break
        else:
            print(f"Limit {limit:5d}: Error {response.status_code}")
            
    except Exception as e:
        print(f"Limit {limit:5d}: {str(e)[:50]}")

print("\nSpace-Track.org typically has:")
print("- ~25,000+ total tracked objects")
print("- ~10,000+ debris objects")
print("- API rate limits: 30 requests/minute, 300 requests/hour")
print("- Single query limit: Usually 2000-5000 objects")
