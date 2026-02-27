# New React Frontend Guide

## Overview
The AstroCleanAI frontend has been completely rebuilt with React, featuring a modern, dark-themed interface with three main sections:

1. **Dashboard** - System overview and satellite monitoring
2. **Debris Tracker** - Real-time space debris tracking using Space-Track.org
3. **Collision Analysis** - Advanced collision probability analysis

## Features

### Dashboard Tab
- System health monitoring
- Real-time statistics (satellites tracked, active monitoring, high-risk events)
- Satellite information cards
- Quick action buttons

### Debris Tracker Tab
Three views available:
- **Search**: Search for debris by type (debris, rocket_body, payload, unknown)
- **High Risk**: View high-risk debris in LEO (200-2000 km altitude)
- **Recent**: Recently cataloged debris from the last 30 days

Features:
- Click "View Details" on any debris to see complete orbital information
- Real-time data from Space-Track.org API
- Detailed debris information including NORAD ID, country, orbital parameters

### Collision Analysis Tab
- Select a satellite from the tracked list
- Enter debris ID (JPL Horizons ID or NORAD ID)
- Configure analysis parameters:
  - Duration (10-1440 minutes)
  - Monte Carlo samples (100-10,000)
- Real-time progress tracking
- Collision probability calculation with risk levels:
  - SAFE (0%)
  - LOW (<0.1%)
  - MODERATE (0.1-1%)
  - HIGH (1-10%)
  - CRITICAL (>10%)
- 3D visualization link for completed analyses

## Running the Application

### Start the Backend Server
```bash
cd AstroCleanAI
start_with_spacetrack.bat
```

The server will start on http://localhost:5000 with Space-Track credentials loaded.

### Access the Frontend
Open your browser and navigate to:
```
http://localhost:5000
```

The React frontend is automatically served from the `/` route.

## API Integration

The frontend integrates with these API endpoints:

### Core Endpoints
- `GET /health` - System health check
- `GET /api/satellites` - List tracked satellites
- `POST /api/analyze` - Satellite collision analysis
- `POST /api/visualize` - Generate 3D visualization

### Space Debris Endpoints
- `GET /api/space_debris/search?type=<type>&limit=<limit>` - Search debris
- `GET /api/space_debris/high_risk?altitude_min=<min>&altitude_max=<max>` - High-risk debris
- `GET /api/space_debris/recent?days=<days>` - Recent debris
- `GET /api/space_debris/<norad_id>` - Debris details
- `GET /api/space_debris/<norad_id>/tle` - TLE data

### Debris Analysis Endpoints
- `POST /api/debris_job` - Start async debris analysis
- `GET /api/debris_job/<job_id>` - Check job status

## Technology Stack

- **React** - UI framework
- **Vite** - Build tool and dev server
- **CSS3** - Modern styling with gradients and animations
- **Fetch API** - HTTP requests to backend

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx          # System overview
│   │   ├── DebrisTracker.jsx      # Space debris tracking
│   │   └── CollisionAnalysis.jsx  # Collision analysis
│   ├── App.jsx                     # Main app with tab navigation
│   ├── api.js                      # API client functions
│   ├── main.jsx                    # React entry point
│   └── styles.css                  # Global styles
├── dist/                           # Production build
├── index.html                      # HTML template
└── package.json                    # Dependencies
```

## Building for Production

To rebuild the frontend after making changes:

```bash
cd AstroCleanAI/frontend
npm run build
```

The production build will be created in `frontend/dist/` and automatically served by the Flask backend.

## Troubleshooting

### Frontend not loading
1. Make sure the backend server is running
2. Check that `frontend/dist/` exists and contains files
3. Rebuild the frontend: `npm run build`

### Space-Track data not loading
1. Verify Space-Track credentials are set in `start_with_spacetrack.bat`
2. Check server logs for authentication errors
3. Ensure you have an active Space-Track.org account

### Collision analysis stuck
1. Check browser console for errors
2. Verify the debris ID is valid (JPL Horizons or NORAD)
3. Reduce Monte Carlo samples for faster results

## Next Steps

1. Start the server: `start_with_spacetrack.bat`
2. Open browser: http://localhost:5000
3. Explore the Dashboard tab
4. Try searching for debris in the Debris Tracker
5. Run a collision analysis with debris ID "433" (Eros asteroid)

Enjoy your new space debris tracking system! 🛰️🚀
