# 🌐 AstroCleanAI REST API Documentation

## Overview

The AstroCleanAI API provides HTTP endpoints for satellite collision avoidance analysis, visualization, and maneuver optimization.

**Base URL**: `http://localhost:5000`

## Quick Start

### Start the API Server

```bash
python api.py
```

The server will start on `http://localhost:5000`

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "AstroCleanAI API",
  "version": "1.0.0",
  "timestamp": "2026-02-20T19:30:00Z"
}
```

---

### 2. List Satellites

**GET** `/api/satellites`

Get list of available satellites.

**Response:**
```json
{
  "satellites": {
    "25544": {
      "name": "ISS (ZARYA)",
      "norad_id": "25544",
      "type": "Space Station",
      "description": "International Space Station"
    },
    ...
  },
  "count": 3
}
```

---

### 3. Get Satellite Information

**GET** `/api/satellites/<norad_id>`

Get detailed information about a specific satellite.

**Example:** `GET /api/satellites/25544`

**Response:**
```json
{
  "satellite": {
    "name": "ISS (ZARYA)",
    "norad_id": "25544",
    "inclination": 51.64,
    "mean_altitude": 408.0,
    "orbital_period": 92.9,
    "eccentricity": 0.0001234
  },
  "status": "success"
}
```

---

### 4. Analyze Collision

**POST** `/api/analyze`

Analyze collision scenario between two satellites.

**Request Body:**
```json
{
  "satellite1_norad": "25544",
  "satellite2_norad": "43013",
  "duration_minutes": 180,
  "step_seconds": 60,
  "threshold_km": 10.0
}
```

**Response:**
```json
{
  "status": "success",
  "safe": true,
  "satellite1": {
    "name": "ISS (ZARYA)",
    "norad_id": "25544",
    "trajectory_points": 180
  },
  "satellite2": {
    "name": "HST",
    "norad_id": "43013",
    "trajectory_points": 180
  },
  "analysis": {
    "start_time": "2026-02-20T19:30:00",
    "duration_minutes": 180,
    "close_approaches": 0,
    "closest_approach": {
      "distance_km": 1250.5,
      "time": "2026-02-20T20:15:00",
      "relative_velocity_km_s": 7.2
    },
    "risk_assessment": {
      "probability_average": 0.000001,
      "risk_category": "LOW"
    }
  }
}
```

---

### 5. Generate Visualization

**POST** `/api/visualize`

Generate interactive 3D visualization HTML.

**Request Body:**
```json
{
  "satellite1_norad": "25544",
  "satellite2_norad": "43013",
  "duration_minutes": 180,
  "step_seconds": 60
}
```

**Response:**
```json
{
  "status": "success",
  "visualization_url": "/api/visualization/collision_20260220_193000.html",
  "filename": "collision_20260220_193000.html",
  "message": "Visualization generated successfully"
}
```

**Access visualization:** `GET /api/visualization/<filename>`

---

### 6. Download TLE Data

**POST** `/api/tle/download`

Download TLE data for a satellite.

**Request Body:**
```json
{
  "norad_id": "25544"
}
```

**Response:**
```json
{
  "status": "success",
  "norad_id": "25544",
  "filename": "sat_25544.txt",
  "message": "TLE data downloaded successfully"
}
```

---

### 7. Optimize Maneuver

**POST** `/api/maneuver/optimize`

Optimize collision avoidance maneuver.

**Request Body:**
```json
{
  "satellite1_norad": "25544",
  "satellite2_norad": "43013",
  "burn_time_minutes": 60,
  "dv_range": [0.1, 5.0],
  "dv_step": 0.2
}
```

**Response:**
```json
{
  "status": "success",
  "maneuver": {
    "burn_time": "2026-02-20T20:30:00",
    "magnitude_m_s": 2.5,
    "direction": "tangential",
    "dv_vector_m_s": [0.0, 2.5, 0.0],
    "min_distance_km": 15.3,
    "fuel_cost_m_s": 2.5
  }
}
```

---

## Example Usage

### Python Example

```python
import requests

# Analyze collision
response = requests.post('http://localhost:5000/api/analyze', json={
    'satellite1_norad': '25544',
    'satellite2_norad': '43013',
    'duration_minutes': 180
})

result = response.json()
print(f"Safe: {result['safe']}")
print(f"Closest distance: {result['analysis']['closest_approach']['distance_km']} km")
```

### JavaScript Example

```javascript
// Analyze collision
fetch('http://localhost:5000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    satellite1_norad: '25544',
    satellite2_norad: '43013',
    duration_minutes: 180
  })
})
.then(res => res.json())
.then(data => {
  console.log('Safe:', data.safe);
  console.log('Distance:', data.analysis.closest_approach.distance_km, 'km');
});
```

### cURL Example

```bash
# Health check
curl http://localhost:5000/health

# Analyze collision
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "satellite1_norad": "25544",
    "satellite2_norad": "43013",
    "duration_minutes": 180
  }'

# Generate visualization
curl -X POST http://localhost:5000/api/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "satellite1_norad": "25544",
    "satellite2_norad": "43013"
  }'
```

---

## Error Responses

All errors return JSON in this format:

```json
{
  "error": "Error message here",
  "type": "ErrorType"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (satellite/endpoint not found)
- `500` - Internal Server Error

---

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider adding rate limiting.

---

## CORS

CORS is enabled, so you can call the API from web browsers.

---

## Testing the API

### Using Postman/Insomnia

1. Import the endpoints
2. Set base URL: `http://localhost:5000`
3. Test each endpoint

### Using Python requests

```python
import requests

BASE_URL = 'http://localhost:5000'

# Health check
r = requests.get(f'{BASE_URL}/health')
print(r.json())

# Analyze
r = requests.post(f'{BASE_URL}/api/analyze', json={
    'satellite1_norad': '25544',
    'satellite2_norad': '43013'
})
print(r.json())
```

---

**Happy API coding! 🚀**
