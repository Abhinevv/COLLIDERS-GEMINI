# 🛰️ AstroCleanAI Space Debris Tracking API

## ✅ COMPLETE - Your Project Now Has Real Space Debris Data Collection!

Your AstroCleanAI project now includes comprehensive space debris tracking capabilities using official data sources.

---

## 📊 Data Sources

### 1. **Space-Track.org** (NEW! ⭐)
- **Official US Space Surveillance Network database**
- **27,000+ tracked objects** in Earth orbit
- Real orbital debris, defunct satellites, rocket bodies
- Updated multiple times daily
- **Requires free account**: https://www.space-track.org/auth/createAccount

### 2. **NASA JPL Horizons**
- Near-Earth asteroids and comets
- Real-time ephemeris data
- High-precision orbital calculations

### 3. **NASA JPL SBDB**
- Small-Body Database
- Search asteroids by name/designation
- Orbital parameters and physical properties

### 4. **Celestrak**
- Active satellite TLE data
- ISS, Hubble, weather satellites
- NORAD catalog

---

## 🚀 New API Endpoints

### 1. Search Space Debris
**Endpoint:** `GET /api/space_debris/search`

**Parameters:**
- `type`: debris, rocket_body, payload, unknown (default: debris)
- `limit`: max results (default: 50)

**Example:**
```bash
curl "http://localhost:5000/api/space_debris/search?type=debris&limit=10"
```

**Response:**
```json
{
  "status": "success",
  "count": 10,
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

---

### 2. Get High-Risk Debris in LEO
**Endpoint:** `GET /api/space_debris/high_risk`

**Parameters:**
- `altitude_min`: minimum altitude in km (default: 200)
- `altitude_max`: maximum altitude in km (default: 2000)
- `limit`: max results (default: 50)

**Example:**
```bash
curl "http://localhost:5000/api/space_debris/high_risk?altitude_min=400&altitude_max=600&limit=20"
```

**Use Case:** Find debris in ISS orbit range (400-420 km)

---

### 3. Get Recently Cataloged Debris
**Endpoint:** `GET /api/space_debris/recent`

**Parameters:**
- `days`: number of days to look back (default: 30)
- `limit`: max results (default: 50)

**Example:**
```bash
curl "http://localhost:5000/api/space_debris/recent?days=7&limit=10"
```

**Use Case:** Monitor new debris from recent collisions or breakups

---

### 4. Get Specific Debris Details
**Endpoint:** `GET /api/space_debris/<norad_id>`

**Example:**
```bash
curl "http://localhost:5000/api/space_debris/25544"
```

**Response:**
```json
{
  "status": "success",
  "debris": {
    "norad_id": "25544",
    "name": "ISS (ZARYA)",
    "type": "PAYLOAD",
    "country": "ISS",
    "launch_date": "1998-11-20",
    "apogee_km": 421.5,
    "perigee_km": 418.2,
    "period_minutes": 92.8,
    "inclination_deg": 51.6,
    "eccentricity": 0.0002,
    "rcs_size": "LARGE",
    "tle_line1": "1 25544U 98067A   ...",
    "tle_line2": "2 25544  51.6... "
  }
}
```

---

### 5. Get TLE Data for Debris
**Endpoint:** `GET /api/space_debris/<norad_id>/tle`

**Example:**
```bash
curl "http://localhost:5000/api/space_debris/25544/tle"
```

**Response:**
```json
{
  "status": "success",
  "norad_id": "25544",
  "tle": {
    "line1": "1 25544U 98067A   24055.12345678  .00012345  00000-0  12345-3 0  9999",
    "line2": "2 25544  51.6416 123.4567 0002345  12.3456 347.7890 15.48919234123456"
  }
}
```

**Use Case:** Get orbital elements for propagation and collision analysis

---

## 🔧 Setup Instructions

### Step 1: Create Space-Track Account
1. Go to: https://www.space-track.org/auth/createAccount
2. Fill out registration (free)
3. Verify email
4. Login to activate

### Step 2: Set Environment Variables

**Windows (PowerShell):**
```powershell
$env:SPACETRACK_USER="your_username"
$env:SPACETRACK_PASS="your_password"
```

**Windows (Permanent):**
1. Search "Environment Variables" in Windows
2. Add `SPACETRACK_USER` = your username
3. Add `SPACETRACK_PASS` = your password
4. Restart terminal/IDE

**Linux/Mac:**
```bash
export SPACETRACK_USER="your_username"
export SPACETRACK_PASS="your_password"
```

### Step 3: Restart API Server
```bash
python api.py
```

---

## 📝 Complete API Endpoint List

### Space Debris (NEW!)
- `GET /api/space_debris/search` - Search orbital debris
- `GET /api/space_debris/high_risk` - High-risk debris in LEO
- `GET /api/space_debris/recent` - Recently cataloged debris
- `GET /api/space_debris/<norad_id>` - Debris details
- `GET /api/space_debris/<norad_id>/tle` - TLE data

### Debris Analysis (Existing)
- `POST /api/debris_analyze` - Analyze debris vs satellite
- `POST /api/debris_job` - Start async analysis job
- `GET /api/debris_job/<job_id>` - Check job status
- `GET /api/debris_search` - Search asteroids/NEOs

### Satellites
- `GET /api/satellites` - List satellites
- `GET /api/satellites/<norad_id>` - Satellite info
- `POST /api/tle/download` - Download TLE data

### Collision Analysis
- `POST /api/analyze` - Analyze collision scenario
- `POST /api/visualize` - Generate 3D visualization
- `POST /api/maneuver/optimize` - Optimize avoidance maneuver

### Visualizations
- `GET /api/visualization/` - List visualizations
- `GET /api/visualization/<filename>` - View visualization

---

## 💡 Example Use Cases

### 1. Monitor ISS Collision Risks
```python
import requests

# Get high-risk debris near ISS altitude (400-420 km)
response = requests.get('http://localhost:5000/api/space_debris/high_risk',
                       params={'altitude_min': 400, 'altitude_max': 420, 'limit': 50})

debris_list = response.json()['high_risk_debris']

for debris in debris_list:
    print(f"⚠️ {debris['name']} at {debris['apogee_km']} km")
```

### 2. Track Recent Debris Events
```python
# Get debris cataloged in last 7 days
response = requests.get('http://localhost:5000/api/space_debris/recent',
                       params={'days': 7})

recent = response.json()['recent_debris']

for obj in recent:
    print(f"🆕 {obj['name']} - Added: {obj['creation_date']}")
```

### 3. Analyze Specific Debris Threat
```python
# Get details for specific debris
debris_id = "12345"
response = requests.get(f'http://localhost:5000/api/space_debris/{debris_id}')

debris = response.json()['debris']
print(f"Name: {debris['name']}")
print(f"Altitude: {debris['apogee_km']} km")
print(f"Type: {debris['type']}")
```

### 4. Get TLE for Propagation
```python
# Get TLE data for collision analysis
response = requests.get(f'http://localhost:5000/api/space_debris/{debris_id}/tle')

tle = response.json()['tle']
# Use TLE lines for orbital propagation
line1 = tle['line1']
line2 = tle['line2']
```

---

## 🎯 What You Can Track

### Debris Types:
- ✅ **Fragmentation debris** from collisions (e.g., Cosmos-Iridium 2009)
- ✅ **ASAT test debris** (e.g., Chinese 2007, Russian 2021)
- ✅ **Rocket bodies** from launches
- ✅ **Defunct satellites**
- ✅ **Paint flecks and small debris**
- ✅ **Unknown objects**

### Notable Debris Clouds:
- Cosmos 1408 (Russian ASAT test 2021) - 1,500+ pieces
- Fengyun-1C (Chinese ASAT test 2007) - 3,500+ pieces
- Cosmos-Iridium collision (2009) - 2,000+ pieces

---

## 📊 Data Statistics

- **Total tracked objects**: 27,000+
- **Active satellites**: ~5,000
- **Debris objects**: ~20,000+
- **Rocket bodies**: ~2,000+
- **Update frequency**: Multiple times per day
- **Altitude range**: LEO to GEO (200 km - 36,000 km)

---

## 🔒 Security & Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** only
3. **Rate limiting**: ~30 requests/minute
4. **Cache results** to reduce API calls
5. **Rotate passwords** periodically

---

## 🐛 Troubleshooting

### "Authentication failed"
- Verify Space-Track account is activated
- Check environment variables are set
- Ensure username/password are correct

### "No debris found"
- Check Space-Track.org is accessible
- Try different search parameters
- Verify API access is enabled on your account

### "Connection timeout"
- Space-Track may be temporarily down
- Check internet connection
- Retry in a few minutes

---

## 📚 Additional Resources

- **Space-Track Documentation**: https://www.space-track.org/documentation
- **TLE Format Guide**: https://en.wikipedia.org/wiki/Two-line_element_set
- **Orbital Mechanics**: https://en.wikipedia.org/wiki/Orbital_elements
- **Space Debris Info**: https://www.esa.int/Safety_Security/Space_Debris

---

## ✨ Summary

Your AstroCleanAI project now has:

✅ **Real orbital debris tracking** from Space-Track.org  
✅ **27,000+ tracked objects** database access  
✅ **High-risk debris monitoring** in LEO  
✅ **Recent debris alerts** for new objects  
✅ **TLE data access** for any tracked object  
✅ **Collision analysis** with real space junk  
✅ **3D visualization** of debris encounters  

**Your project is now a complete space debris tracking and collision avoidance system!** 🚀
