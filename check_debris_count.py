import requests

# Check how many debris objects are available
debris_response = requests.get('http://localhost:5000/api/space_debris/high_risk?min_altitude=200&max_altitude=2000&limit=500')
debris_data = debris_response.json()

print(f"High-risk debris available (limit 500): {len(debris_data.get('high_risk_debris', []))}")

# Check different altitude ranges
ranges = [
    (200, 600, "LEO Low"),
    (600, 1000, "LEO Mid"),
    (1000, 2000, "LEO High"),
]

for min_alt, max_alt, name in ranges:
    response = requests.get(f'http://localhost:5000/api/space_debris/high_risk?min_altitude={min_alt}&max_altitude={max_alt}&limit=200')
    data = response.json()
    count = len(data.get('high_risk_debris', []))
    print(f"{name} ({min_alt}-{max_alt} km): {count} debris objects")
