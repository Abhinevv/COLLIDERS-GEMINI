# Space-Track.org API Setup Guide

## Overview
AstroCleanAI now includes real orbital debris tracking using Space-Track.org, the official US Space Surveillance Network database.

## Features Added
- ✅ Search for real space debris (defunct satellites, rocket bodies, etc.)
- ✅ Track high-risk debris in LEO (Low Earth Orbit)
- ✅ Monitor recently cataloged debris
- ✅ Get detailed TLE (Two-Line Element) data for any tracked object
- ✅ Access 27,000+ tracked objects in Earth orbit

## Setup Instructions

### 1. Create Free Space-Track Account
1. Go to: https://www.space-track.org/auth/createAccount
2. Fill out the registration form
3. Verify your email
4. Login to confirm account is active

### 2. Set Environment Variables

**Windows (PowerShell):**
```powershell
$env:SPACETRACK_USER="your_username"
$env:SPACETRACK_PASS="your_password"
```

**Windows (Command Prompt):**
```cmd
set SPACETRACK_USER=your_username
set SPACETRACK_PASS=your_password
```

**Linux/Mac:**
```bash
export SPACETRACK_USER="your_username"
export SPACETRACK_PASS="your_password"
```

**Permanent Setup (Windows):**
1. Search for "Environment Variables" in Windows
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Add `SPACETRACK_USER` with your username
6. Add `SPACETRACK_PASS` with your password

### 3. Restart API Server
After setting environment variables, restart the API server:
```bash
python api.py
```

## New API Endpoints

### 1. Search Space Debris
```
GET /api/space_debris/search?type=debris&limit=50
```

**Parameters:**
- `type`: debris, rocket_body, payload, unknown (default: debris)
- `limit`: max results (default: 50)

**Example Response:**
```json
{
  "status": "success",
  "count": 50,
  "debris": [
    {
      "norad_id": "12345",
      "name": "COSMOS 1408 DEB",
      "type": "DEBRIS",
      "country": "CIS",
      "launch_date": "1982-09-20",
      "apogee_km": 485.2,
      "perigee_km": 462.8,
      "period_minutes": 93.5,
      "inclination_deg": 82.5
    }
  ]
}
```

### 2. Get High-Risk Debris
```
GET /api/space_debris/high_risk?altitude_min=200&altitude_max=2000&limit=50
```

**Parameters:**
- `altitude_min`: minimum altitude in km (default: 200)
- `altitude_max`: maximum altitude in km (default: 2000)
- `limit`: max results (default: 50)

### 3. Get Recent Debris
```
GET /api/space_debris/recent?days=30&limit=50
```

**Parameters:**
- `days`: number of days to look back (default: 30)
- `limit`: max results (default: 50)

### 4. Get Debris Details
```
GET /api/space_debris/<norad_id>
```

**Example:**
```
GET /api/space_debris/25544
```

### 5. Get Debris TLE Data
```
GET /api/space_debris/<norad_id>/tle
```

Returns Two-Line Element orbital data for propagation.

## Testing the API

### Using curl:
```bash
# Search for debris
curl "http://localhost:5000/api/space_debris/search?type=debris&limit=10"

# Get high-risk debris
curl "http://localhost:5000/api/space_debris/high_risk?limit=10"

# Get recent debris
curl "http://localhost:5000/api/space_debris/recent?days=7"

# Get specific debris details
curl "http://localhost:5000/api/space_debris/25544"
```

### Using Python:
```python
import requests

# Search for debris
response = requests.get('http://localhost:5000/api/space_debris/search', 
                       params={'type': 'debris', 'limit': 10})
debris_list = response.json()

print(f"Found {debris_list['count']} debris objects")
for debris in debris_list['debris']:
    print(f"- {debris['name']} at {debris['apogee_km']} km")
```

## Data Sources

### Space-Track.org provides:
- **27,000+ tracked objects** in Earth orbit
- **Real-time TLE data** updated multiple times per day
- **Historical tracking data**
- **Debris from collisions** (e.g., Cosmos-Iridium collision, Chinese ASAT test)
- **Rocket bodies** from launches
- **Defunct satellites**

### Object Types:
- `DEBRIS` - Fragmentation debris from collisions/explosions
- `ROCKET BODY` - Spent rocket stages
- `PAYLOAD` - Active or inactive satellites
- `UNKNOWN` - Unidentified objects

## Rate Limits
- Space-Track.org allows reasonable API usage
- Recommended: Cache results and don't query too frequently
- Typical limit: ~30 requests per minute

## Troubleshooting

### "Authentication failed"
- Check username and password are correct
- Verify account is activated via email
- Ensure environment variables are set correctly

### "No debris found"
- Check if Space-Track.org is accessible
- Verify your account has API access enabled
- Try with different search parameters

### "Connection timeout"
- Space-Track.org may be temporarily unavailable
- Check your internet connection
- Try again in a few minutes

## Security Notes
- **Never commit credentials to git**
- Use environment variables only
- Consider using a `.env` file with python-dotenv
- Rotate passwords periodically

## Additional Resources
- Space-Track.org Documentation: https://www.space-track.org/documentation
- API Query Builder: https://www.space-track.org/basicspacedata/query/class/gp
- TLE Format Guide: https://en.wikipedia.org/wiki/Two-line_element_set

## Next Steps
Once configured, you can:
1. Track real orbital debris
2. Analyze collision risks with actual space junk
3. Monitor debris clouds from satellite breakups
4. Track rocket bodies and defunct satellites
5. Build early warning systems for conjunctions
