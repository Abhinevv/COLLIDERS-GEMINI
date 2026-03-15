# Colliders API Endpoints

## Base URL
```
http://localhost:5000
```

## Core Endpoints

### Health Check
```
GET /health
```
Returns system health status and service availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "Colliders API",
  "version": "2.0.0",
  "timestamp": "2026-02-25T00:00:00+00:00",
  "services": {
    "database": "operational",
    "history": "operational",
    "alerts": "operational",
    "maneuvers": "operational",
    "space_track": "operational"
  },
  "features": {
    "collision_analysis": true,
    "debris_tracking": true,
    "alert_system": true,
    "maneuver_planning": true,
    "history_tracking": true
  }
}
```

### List Satellites
```
GET /api/satellites
```
Returns list of available satellites.

### Start Debris Analysis Job
```
POST /api/debris_job
```
Start a collision analysis job.

**Request Body:**
```json
{
  "debris": "67720",
  "satellite_norad": "25544",
  "duration_minutes": 60,
  "step_seconds": 60,
  "samples": 1000,
  "visualize": true
}
```

**Response:**
```json
{
  "status": "accepted",
  "job_id": "uuid",
  "message": "Analysis started"
}
```

### Get Job Status
```
GET /api/debris_job/{job_id}
```
Get status of a running analysis job.

## Phase 1: History & Satellite Management

### Get Analysis Statistics
```
GET /api/history/statistics?days=30
```
Get statistical summary of analyses.

### Get Satellite History
```
GET /api/history/satellite/{norad_id}?days=30&limit=100
```
Get analysis history for a specific satellite.

### Get Managed Satellites
```
GET /api/satellites/manage
```
List all managed satellites.

### Add Satellite
```
POST /api/satellites/manage/add
```
Add a new satellite to tracking.

**Request Body:**
```json
{
  "norad_id": "25544",
  "name": "ISS",
  "type": "Space Station"
}
```

### Remove Satellite
```
DELETE /api/satellites/manage/{norad_id}
```
Remove a satellite from tracking.

## Phase 2: Alerts & Maneuvers

### Get Active Alerts
```
GET /api/alerts?satellite_id=25544&min_risk_level=HIGH
```
Get all active collision alerts.

**Response:**
```json
{
  "status": "success",
  "alerts": [
    {
      "id": 1,
      "satellite_id": "25544",
      "debris_id": "67720",
      "probability": 0.05,
      "risk_level": "HIGH",
      "closest_distance_km": 2.5,
      "created_at": "2026-02-25T00:00:00+00:00"
    }
  ],
  "count": 1
}
```

### Dismiss Alert
```
PUT /api/alerts/{alert_id}/dismiss
```
Dismiss an alert.

**Request Body:**
```json
{
  "notes": "False positive"
}
```

### Resolve Alert
```
PUT /api/alerts/{alert_id}/resolve
```
Mark an alert as resolved.

### Subscribe to Alerts
```
POST /api/alerts/subscribe
```
Subscribe to alert notifications.

**Request Body:**
```json
{
  "email": "user@example.com",
  "satellite_ids": ["25544"],
  "min_probability": 0.001
}
```

### Calculate Maneuver
```
POST /api/maneuver/calculate
```
Calculate collision avoidance maneuver options.

**Request Body:**
```json
{
  "satellite_position": [6800, 0, 0],
  "satellite_velocity": [0, 7.5, 0],
  "debris_position": [6805, 10, 0],
  "debris_velocity": [0, 7.4, 0]
}
```

**Response:**
```json
{
  "status": "success",
  "options": [
    {
      "name": "Radial Boost (Increase Altitude)",
      "description": "Increase orbital altitude to avoid collision",
      "delta_v_magnitude": 0.001,
      "delta_v_vector": [0.001, 0, 0],
      "fuel_cost_estimate": {
        "fuel_mass_kg": 5.2,
        "delta_v_ms": 1.0
      },
      "execution_time_minutes": 30
    }
  ],
  "comparison": {
    "recommended": {
      "name": "Radial Boost (Increase Altitude)",
      "reason": "Lowest fuel cost"
    }
  },
  "count": 3
}
```

### Simulate Maneuver
```
POST /api/maneuver/simulate
```
Simulate the effects of a maneuver.

**Request Body:**
```json
{
  "position": [6800, 0, 0],
  "velocity": [0, 7.5, 0],
  "delta_v_vector": [0.001, 0, 0],
  "duration_hours": 24
}
```

## Space Debris Endpoints

### Search Debris
```
GET /api/space_debris/search?type=debris&limit=50
```
Search for orbital debris.

### Get High Risk Debris
```
GET /api/space_debris/high_risk?altitude_min=200&altitude_max=2000&limit=50
```
Get high-risk debris in LEO.

### Get Recent Debris
```
GET /api/space_debris/recent?days=30&limit=50
```
Get recently cataloged debris.

### Get Debris Details
```
GET /api/space_debris/{norad_id}
```
Get detailed information about a debris object.

### Get Debris TLE
```
GET /api/space_debris/{norad_id}/tle
```
Get TLE orbital data for a debris object.

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "type": "ErrorType"
}
```

**HTTP Status Codes:**
- 200: Success
- 201: Created
- 202: Accepted (async job started)
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

## Rate Limiting

No rate limiting currently implemented. For production use, consider implementing rate limiting.

## Authentication

No authentication currently required. For production use, implement API key or OAuth authentication.

## CORS

CORS is enabled for all origins in development mode.

## Notes

- All timestamps are in UTC ISO 8601 format
- All distances are in kilometers
- All velocities are in km/s
- All probabilities are decimal values (0.0 to 1.0)
- Job IDs are UUIDs
- NORAD IDs are strings
