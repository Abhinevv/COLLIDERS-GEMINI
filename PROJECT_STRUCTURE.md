# 📁 AstroCleanAI Project Structure

## 🏗️ Directory Layout

```
AstroCleanAI/
├── 📄 Core Files
│   ├── api.py                    # Main Flask API server (30+ endpoints)
│   ├── main.py                   # CLI interface for direct usage
│   ├── fetch_tle.py              # TLE data fetching utilities
│   ├── requirements.txt          # Python dependencies
│   └── README.md                 # Project documentation
│
├── 🚀 Startup Scripts
│   ├── start_with_spacetrack.bat # Production startup (with Space-Track)
│   ├── start_api.bat             # Basic API startup
│   └── activate_env.bat          # Virtual environment activation
│
├── 🗄️ Backend Modules
│   ├── alerts/                   # Real-time collision alert system
│   │   ├── alert_service.py      # Alert management and notifications
│   │   └── __init__.py
│   │
│   ├── database/                 # Data persistence layer
│   │   ├── models.py             # SQLAlchemy database models (5 tables)
│   │   ├── db_manager.py         # Database connection and operations
│   │   └── __init__.py
│   │
│   ├── debris/                   # Space debris analysis
│   │   ├── analyze.py            # Debris collision analysis algorithms
│   │   ├── space_track.py        # Space-Track.org API integration
│   │   └── __init__.py
│   │
│   ├── history/                  # Historical data tracking
│   │   ├── history_service.py    # Analysis history and statistics
│   │   └── __init__.py
│   │
│   ├── probability/              # Collision probability calculations
│   │   ├── collision_probability.py # Monte Carlo simulation
│   │   └── __init__.py
│   │
│   ├── propagation/              # Orbital mechanics
│   │   ├── propagate.py          # SGP4 orbit propagation
│   │   ├── distance_check.py     # Close approach detection
│   │   └── __init__.py
│   │
│   ├── satellites/               # Satellite fleet management
│   │   ├── satellite_manager.py  # Satellite CRUD operations
│   │   └── __init__.py
│   │
│   └── visualization/            # Orbit plotting and visualization
│       ├── plot_orbits.py        # 3D orbit visualization
│       └── __init__.py
│
├── 🌐 Frontend Application
│   ├── src/                      # React source code
│   │   ├── components/           # UI components (7 main tabs)
│   │   │   ├── Dashboard.jsx     # System overview
│   │   │   ├── DebrisTracker.jsx # Space debris tracking
│   │   │   ├── CollisionAnalysis.jsx # Monte Carlo analysis
│   │   │   ├── RiskRanking.jsx   # Risk assessment
│   │   │   ├── SatelliteRiskProfile.jsx # Individual satellite analysis
│   │   │   ├── EnhancedFeatures.jsx # NASA-grade analysis tools
│   │   │   ├── Alerts.jsx        # Alert management
│   │   │   └── Toast.jsx         # Notification system
│   │   │
│   │   ├── api.js                # API client functions
│   │   ├── styles.css            # Modern CSS styling
│   │   └── App.jsx               # Main application component
│   │
│   ├── dist/                     # Built production files
│   ├── package.json              # Node.js dependencies
│   ├── vite.config.js            # Vite build configuration
│   └── index.html                # HTML entry point
│
├── 💾 Data Storage
│   ├── data/                     # Application data
│   │   ├── astrocleanai.db       # SQLite database
│   │   └── tle_cache/            # TLE data cache
│   │       └── tle_cache.json    # Cached orbital elements
│   │
│   └── spaceenv/                 # Python virtual environment
│
├── 📚 Documentation
│   ├── API_DOCUMENTATION.md      # Complete API reference
│   ├── API_ENDPOINTS.md          # Endpoint listing
│   ├── ARCHITECTURE.md           # System architecture
│   ├── BUILD.md                  # Build instructions
│   ├── DEPLOYMENT_INSTRUCTIONS.md # Production deployment
│   └── IMPLEMENTATION_PLAN.md    # Feature roadmap
│
└── 🔧 Configuration
    ├── .gitignore                # Git ignore patterns
    ├── .vscode/                  # VS Code settings
    ├── .git/                     # Git repository
    └── LICENSE                   # MIT license
```

## 🎯 Key Components

### 🖥️ Backend (Python/Flask)
- **30+ REST API endpoints** for complete functionality
- **SQLite database** with 5 tables for data persistence
- **Space-Track.org integration** for real orbital debris data
- **Monte Carlo simulation** for collision probability
- **SGP4 orbit propagation** for accurate position calculation
- **Alert system** with real-time notifications

### 🌐 Frontend (React/Vite)
- **7 comprehensive tabs** for mission control
- **Modern React 18** with hooks and functional components
- **Real-time updates** and progress tracking
- **Responsive design** optimized for space operations
- **Dark theme** with professional aesthetics
- **Interactive visualizations** and data tables

### 🗄️ Database Schema
1. **analysis_history** - All collision analyses with results
2. **satellites** - Managed satellite fleet (74 satellites)
3. **debris_objects** - Tracked debris catalog (725+ objects)
4. **alerts** - Collision alerts and notifications
5. **alert_subscriptions** - User alert preferences

### 🔌 External Integrations
- **Space-Track.org API** - Official orbital debris data
- **NASA algorithms** - Standard collision models
- **TLE data feeds** - Two-Line Element orbital parameters
- **NORAD catalog** - Satellite identification system

## 🚀 Startup Flow

1. **Environment Setup** - Virtual environment activation
2. **Dependency Loading** - Python packages and modules
3. **Database Initialization** - SQLite connection and tables
4. **Space-Track Authentication** - API credentials validation
5. **Flask Server Start** - API endpoints activation
6. **Frontend Serving** - React application delivery
7. **Health Check** - System status verification

## 📊 Data Flow

```
Space-Track.org → TLE Cache → Database → API → Frontend → User
     ↑              ↓           ↓        ↓      ↓
   Real-time    Orbit Prop.  Analysis  REST   React
   Updates      (SGP4)       Engine    API    UI
```

## 🔧 Development Workflow

1. **Backend Changes** - Modify Python modules in respective directories
2. **Frontend Changes** - Update React components in `frontend/src/`
3. **Database Changes** - Update models in `database/models.py`
4. **API Changes** - Add endpoints to `api.py`
5. **Testing** - Use health check and API endpoints
6. **Building** - Frontend build with `npm run build`
7. **Deployment** - Use startup scripts for production

---

This structure provides a clean, maintainable, and scalable architecture for space debris collision avoidance operations.