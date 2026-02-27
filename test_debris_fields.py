import requests
import json

# Get one debris object to see its structure
response = requests.get('http://localhost:5000/api/space_debris/high_risk?altitude_min=200&altitude_max=2000&limit=1')
data = response.json()

if 'high_risk_debris' in data and len(data['high_risk_debris']) > 0:
    debris = data['high_risk_debris'][0]
    print("Debris fields available:")
    print(json.dumps(debris, indent=2))
else:
    print("No debris found")
    print(json.dumps(data, indent=2))
