# Ã°Å¸â€œÂ Colliders Project Structure

## Ã°Å¸Ââ€”Ã¯Â¸Â Directory Layout

```
Colliders/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸â€œâ€ž Core Files
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ api.py                    # Main Flask API server (30+ endpoints)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.py                   # CLI interface for direct usage
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fetch_tle.py              # TLE data fetching utilities
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt          # Python dependencies
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ README.md                 # Project documentation
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸Å¡â‚¬ Startup Scripts
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ start_with_spacetrack.bat # Production startup (with Space-Track)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ start_api.bat             # Basic API startup
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ activate_env.bat          # Virtual environment activation
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸â€”â€žÃ¯Â¸Â Backend Modules
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ alerts/                   # Real-time collision alert system
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ alert_service.py      # Alert management and notifications
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ database/                 # Data persistence layer
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ models.py             # SQLAlchemy database models (5 tables)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ db_manager.py         # Database connection and operations
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ debris/                   # Space debris analysis
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ analyze.py            # Debris collision analysis algorithms
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ space_track.py        # Space-Track.org API integration
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ history/                  # Historical data tracking
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ history_service.py    # Analysis history and statistics
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ probability/              # Collision probability calculations
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ collision_probability.py # Monte Carlo simulation
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ propagation/              # Orbital mechanics
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ propagate.py          # SGP4 orbit propagation
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ distance_check.py     # Close approach detection
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ satellites/               # Satellite fleet management
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ satellite_manager.py  # Satellite CRUD operations
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ visualization/            # Orbit plotting and visualization
Ã¢â€â€š       Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ plot_orbits.py        # 3D orbit visualization
Ã¢â€â€š       Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸Å’Â Frontend Application
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ src/                      # React source code
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ components/           # UI components (7 main tabs)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Dashboard.jsx     # System overview
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ DebrisTracker.jsx # Space debris tracking
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ CollisionAnalysis.jsx # Monte Carlo analysis
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ RiskRanking.jsx   # Risk assessment
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ SatelliteRiskProfile.jsx # Individual satellite analysis
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ EnhancedFeatures.jsx # NASA-grade analysis tools
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Alerts.jsx        # Alert management
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Toast.jsx         # Notification system
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ api.js                # API client functions
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ styles.css            # Modern CSS styling
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ App.jsx               # Main application component
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ dist/                     # Built production files
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ package.json              # Node.js dependencies
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ vite.config.js            # Vite build configuration
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ index.html                # HTML entry point
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸â€™Â¾ Data Storage
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ data/                     # Application data
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ colliders.db       # SQLite database
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ tle_cache/            # TLE data cache
Ã¢â€â€š   Ã¢â€â€š       Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ tle_cache.json    # Cached orbital elements
Ã¢â€â€š   Ã¢â€â€š
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ spaceenv/                 # Python virtual environment
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸â€œÅ¡ Documentation
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ API_DOCUMENTATION.md      # Complete API reference
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ API_ENDPOINTS.md          # Endpoint listing
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ ARCHITECTURE.md           # System architecture
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ BUILD.md                  # Build instructions
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ DEPLOYMENT_INSTRUCTIONS.md # Production deployment
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ IMPLEMENTATION_PLAN.md    # Feature roadmap
Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Ã°Å¸â€Â§ Configuration
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .gitignore                # Git ignore patterns
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .vscode/                  # VS Code settings
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .git/                     # Git repository
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ LICENSE                   # MIT license
```

## Ã°Å¸Å½Â¯ Key Components

### Ã°Å¸â€“Â¥Ã¯Â¸Â Backend (Python/Flask)
- **30+ REST API endpoints** for complete functionality
- **SQLite database** with 5 tables for data persistence
- **Space-Track.org integration** for real orbital debris data
- **Monte Carlo simulation** for collision probability
- **SGP4 orbit propagation** for accurate position calculation
- **Alert system** with real-time notifications

### Ã°Å¸Å’Â Frontend (React/Vite)
- **7 comprehensive tabs** for mission control
- **Modern React 18** with hooks and functional components
- **Real-time updates** and progress tracking
- **Responsive design** optimized for space operations
- **Dark theme** with professional aesthetics
- **Interactive visualizations** and data tables

### Ã°Å¸â€”â€žÃ¯Â¸Â Database Schema
1. **analysis_history** - All collision analyses with results
2. **satellites** - Managed satellite fleet (74 satellites)
3. **debris_objects** - Tracked debris catalog (725+ objects)
4. **alerts** - Collision alerts and notifications
5. **alert_subscriptions** - User alert preferences

### Ã°Å¸â€Å’ External Integrations
- **Space-Track.org API** - Official orbital debris data
- **NASA algorithms** - Standard collision models
- **TLE data feeds** - Two-Line Element orbital parameters
- **NORAD catalog** - Satellite identification system

## Ã°Å¸Å¡â‚¬ Startup Flow

1. **Environment Setup** - Virtual environment activation
2. **Dependency Loading** - Python packages and modules
3. **Database Initialization** - SQLite connection and tables
4. **Space-Track Authentication** - API credentials validation
5. **Flask Server Start** - API endpoints activation
6. **Frontend Serving** - React application delivery
7. **Health Check** - System status verification

## Ã°Å¸â€œÅ  Data Flow

```
Space-Track.org Ã¢â€ â€™ TLE Cache Ã¢â€ â€™ Database Ã¢â€ â€™ API Ã¢â€ â€™ Frontend Ã¢â€ â€™ User
     Ã¢â€ â€˜              Ã¢â€ â€œ           Ã¢â€ â€œ        Ã¢â€ â€œ      Ã¢â€ â€œ
   Real-time    Orbit Prop.  Analysis  REST   React
   Updates      (SGP4)       Engine    API    UI
```

## Ã°Å¸â€Â§ Development Workflow

1. **Backend Changes** - Modify Python modules in respective directories
2. **Frontend Changes** - Update React components in `frontend/src/`
3. **Database Changes** - Update models in `database/models.py`
4. **API Changes** - Add endpoints to `api.py`
5. **Testing** - Use health check and API endpoints
6. **Building** - Frontend build with `npm run build`
7. **Deployment** - Use startup scripts for production

---

This structure provides a clean, maintainable, and scalable architecture for space debris collision avoidance operations.