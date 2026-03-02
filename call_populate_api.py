import requests

print("Calling populate API endpoint...")
try:
    response = requests.post('http://localhost:5000/api/populate_satellites')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
