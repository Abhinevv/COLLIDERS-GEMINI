import requests

# Check satellites
sat_response = requests.get('http://localhost:5000/api/satellites/manage')
sat_data = sat_response.json()
print(f"Satellites in DB: {sat_data['count']}")

# Check debris
debris_response = requests.get('http://localhost:5000/api/space_debris/high_risk?min_altitude=200&max_altitude=2000&limit=100')
debris_data = debris_response.json()
print(f"High-risk debris available: {len(debris_data.get('high_risk_debris', []))}")

print(f"\nTotal combinations: {sat_data['count']} x {len(debris_data.get('high_risk_debris', []))}")
