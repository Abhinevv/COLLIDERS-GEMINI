# ðŸ“ CollidersAI Project Structure

## ðŸ—ï¸ Directory Layout

```
CollidersAI/
â”œâ”€â”€ ðŸ“„ Core Files
â”‚   â”œâ”€â”€ api.py                    # Main Flask API server (30+ endpoints)
â”‚   â”œâ”€â”€ main.py                   # CLI interface for direct usage
â”‚   â”œâ”€â”€ fetch_tle.py              # TLE data fetching utilities
â”‚   â”œâ”€â”€ requirements.txt          # Python dependencies
â”‚   â””â”€â”€ README.md                 # Project documentation
â”‚
â”œâ”€â”€ ðŸš€ Startup Scripts
â”‚   â”œâ”€â”€ start_with_spacetrack.bat # Production startup (with Space-Track)
â”‚   â”œâ”€â”€ start_api.bat             # Basic API startup
â”‚   â””â”€â”€ activate_env.bat          # Virtual environment activation
â”‚
â”œâ”€â”€ ðŸ—„ï¸ Backend Modules
â”‚   â”œâ”€â”€ alerts/                   # Real-time collision alert system
â”‚   â”‚   â”œâ”€â”€ alert_service.py      # Alert management and notifications
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ database/                 # Data persistence layer
â”‚   â”‚   â”œâ”€â”€ models.py             # SQLAlchemy database models (5 tables)
â”‚   â”‚   â”œâ”€â”€ db_manager.py         # Database connection and operations
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ debris/                   # Space debris analysis
â”‚   â”‚   â”œâ”€â”€ analyze.py            # Debris collision analysis algorithms
â”‚   â”‚   â”œâ”€â”€ space_track.py        # Space-Track.org API integration
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ history/                  # Historical data tracking
â”‚   â”‚   â”œâ”€â”€ history_service.py    # Analysis history and statistics
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ probability/              # Collision probability calculations
â”‚   â”‚   â”œâ”€â”€ collision_probability.py # Monte Carlo simulation
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ propagation/              # Orbital mechanics
â”‚   â”‚   â”œâ”€â”€ propagate.py          # SGP4 orbit propagation
â”‚   â”‚   â”œâ”€â”€ distance_check.py     # Close approach detection
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â”œâ”€â”€ satellites/               # Satellite fleet management
â”‚   â”‚   â”œâ”€â”€ satellite_manager.py  # Satellite CRUD operations
â”‚   â”‚   â””â”€â”€ __init__.py
â”‚   â”‚
â”‚   â””â”€â”€ visualization/            # Orbit plotting and visualization
â”‚       â”œâ”€â”€ plot_orbits.py        # 3D orbit visualization
â”‚       â””â”€â”€ __init__.py
â”‚
â”œâ”€â”€ ðŸŒ Frontend Application
â”‚   â”œâ”€â”€ src/                      # React source code
â”‚   â”‚   â”œâ”€â”€ components/           # UI components (7 main tabs)
â”‚   â”‚   â”‚   â”œâ”€â”€ Dashboard.jsx     # System overview
â”‚   â”‚   â”‚   â”œâ”€â”€ DebrisTracker.jsx # Space debris tracking
â”‚   â”‚   â”‚   â”œâ”€â”€ CollisionAnalysis.jsx # Monte Carlo analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ RiskRanking.jsx   # Risk assessment
â”‚   â”‚   â”‚   â”œâ”€â”€ SatelliteRiskProfile.jsx # Individual satellite analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ EnhancedFeatures.jsx # NASA-grade analysis tools
â”‚   â”‚   â”‚   â”œâ”€â”€ Alerts.jsx        # Alert management
â”‚   â”‚   â”‚   â””â”€â”€ Toast.jsx         # Notification system
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ api.js                # API client functions
â”‚   â”‚   â”œâ”€â”€ styles.css            # Modern CSS styling
â”‚   â”‚   â””â”€â”€ App.jsx               # Main application component
â”‚   â”‚
â”‚   â”œâ”€â”€ dist/                     # Built production files
â”‚   â”œâ”€â”€ package.json              # Node.js dependencies
â”‚   â”œâ”€â”€ vite.config.js            # Vite build configuration
â”‚   â””â”€â”€ index.html                # HTML entry point
â”‚
â”œâ”€â”€ ðŸ’¾ Data Storage
â”‚   â”œâ”€â”€ data/                     # Application data
â”‚   â”‚   â”œâ”€â”€ colliders.db       # SQLite database
â”‚   â”‚   â””â”€â”€ tle_cache/            # TLE data cache
â”‚   â”‚       â””â”€â”€ tle_cache.json    # Cached orbital elements
â”‚   â”‚
â”‚   â””â”€â”€ spaceenv/                 # Python virtual environment
â”‚
â”œâ”€â”€ ðŸ“š Documentation
â”‚   â”œâ”€â”€ API_DOCUMENTATION.md      # Complete API reference
â”‚   â”œâ”€â”€ API_ENDPOINTS.md          # Endpoint listing
â”‚   â”œâ”€â”€ ARCHITECTURE.md           # System architecture
â”‚   â”œâ”€â”€ BUILD.md                  # Build instructions
â”‚   â”œâ”€â”€ DEPLOYMENT_INSTRUCTIONS.md # Production deployment
â”‚   â””â”€â”€ IMPLEMENTATION_PLAN.md    # Feature roadmap
â”‚
â””â”€â”€ ðŸ”§ Configuration
    â”œâ”€â”€ .gitignore                # Git ignore patterns
    â”œâ”€â”€ .vscode/                  # VS Code settings
    â”œâ”€â”€ .git/                     # Git repository
    â””â”€â”€ LICENSE                   # MIT license
```

## ðŸŽ¯ Key Components

### ðŸ–¥ï¸ Backend (Python/Flask)
- **30+ REST API endpoints** for complete functionality
- **SQLite database** with 5 tables for data persistence
- **Space-Track.org integration** for real orbital debris data
- **Monte Carlo simulation** for collision probability
- **SGP4 orbit propagation** for accurate position calculation
- **Alert system** with real-time notifications

### ðŸŒ Frontend (React/Vite)
- **7 comprehensive tabs** for mission control
- **Modern React 18** with hooks and functional components
- **Real-time updates** and progress tracking
- **Responsive design** optimized for space operations
- **Dark theme** with professional aesthetics
- **Interactive visualizations** and data tables

### ðŸ—„ï¸ Database Schema
1. **analysis_history** - All collision analyses with results
2. **satellites** - Managed satellite fleet (74 satellites)
3. **debris_objects** - Tracked debris catalog (725+ objects)
4. **alerts** - Collision alerts and notifications
5. **alert_subscriptions** - User alert preferences

### ðŸ”Œ External Integrations
- **Space-Track.org API** - Official orbital debris data
- **NASA algorithms** - Standard collision models
- **TLE data feeds** - Two-Line Element orbital parameters
- **NORAD catalog** - Satellite identification system

## ðŸš€ Startup Flow

1. **Environment Setup** - Virtual environment activation
2. **Dependency Loading** - Python packages and modules
3. **Database Initialization** - SQLite connection and tables
4. **Space-Track Authentication** - API credentials validation
5. **Flask Server Start** - API endpoints activation
6. **Frontend Serving** - React application delivery
7. **Health Check** - System status verification

## ðŸ“Š Data Flow

```
Space-Track.org â†’ TLE Cache â†’ Database â†’ API â†’ Frontend â†’ User
     â†‘              â†“           â†“        â†“      â†“
   Real-time    Orbit Prop.  Analysis  REST   React
   Updates      (SGP4)       Engine    API    UI
```

## ðŸ”§ Development Workflow

1. **Backend Changes** - Modify Python modules in respective directories
2. **Frontend Changes** - Update React components in `frontend/src/`
3. **Database Changes** - Update models in `database/models.py`
4. **API Changes** - Add endpoints to `api.py`
5. **Testing** - Use health check and API endpoints
6. **Building** - Frontend build with `npm run build`
7. **Deployment** - Use startup scripts for production

---

This structure provides a clean, maintainable, and scalable architecture for space debris collision avoidance operations.