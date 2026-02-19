# 🎨 Frontend Features - Complete Integration

## New UI Components Added

### 1. **Enhanced Calculation Component**
- **Location**: `frontend/src/components/EnhancedCalculation.jsx`
- **Features**:
  - Velocity-adjusted collision probability
  - Geometry-adjusted collision probability (impact angle)
  - Toggle switches for velocity/geometry inclusion
  - Real-time results display
- **Inputs**: Debris diameter, altitude, impact angle, exposure area/time
- **Outputs**: Q_base, Q_enhanced, relative velocity, effective area

### 2. **Breakup Simulation Component**
- **Location**: `frontend/src/components/BreakupSimulation.jsx`
- **Features**:
  - NASA SBM-inspired breakup simulation
  - Fragment generation visualization
  - Collision energy calculation
  - Fragment list display (first 20 + count)
- **Inputs**: Satellite area, debris diameter, relative velocity
- **Outputs**: Collision energy, number of fragments, fragment sizes/masses

### 3. **Orbital Decay Component**
- **Location**: `frontend/src/components/OrbitalDecay.jsx`
- **Features**:
  - Atmospheric drag decay prediction
  - Orbital lifetime calculation
  - Decay rate visualization
- **Inputs**: Initial altitude, cross-sectional area, mass, decay altitude
- **Outputs**: Lifetime (days/years), decay rate (km/day), final altitude

### 4. **SGP4 Propagation Component**
- **Location**: `frontend/src/components/SGP4Propagation.jsx`
- **Features**:
  - TLE input (two-line element sets)
  - Orbit propagation over time
  - State vector display (position, velocity, altitude, inclination)
  - Time range selection
- **Inputs**: TLE line 1 & 2, start/end time, step size
- **Outputs**: Time series of orbital states

---

## UI Layout

### Tab System
The app now has **two tabs**:

1. **Basic Calculation** (original features)
   - Input form with Celestrak integration
   - Results display
   - Collision probability graph (2019-2030)
   - Petri Net animation
   - Monte Carlo validation

2. **Enhanced Features** (new advanced features)
   - Enhanced calculation (velocity + geometry)
   - Breakup simulation
   - Orbital decay prediction
   - SGP4 propagation

---

## How to Use

### Enhanced Calculation
1. Switch to **"Enhanced Features"** tab
2. Enter debris diameter, altitude, impact angle
3. Toggle velocity/geometry options
4. Click **"Calculate Enhanced"**
5. View Q_base vs Q_enhanced comparison

### Breakup Simulation
1. Enter satellite area, debris diameter, relative velocity
2. Click **"Simulate Breakup"**
3. View collision energy, fragment count, and fragment list

### Orbital Decay
1. Enter initial altitude, cross-sectional area, mass
2. Set decay altitude threshold
3. Click **"Predict Lifetime"**
4. View predicted lifetime and decay rate

### SGP4 Propagation
1. Enter TLE lines (or use default ISS example)
2. Set start/end time and step size
3. Click **"Propagate Orbit"**
4. View time series of orbital states

---

## API Endpoints Used

- `POST /calculate-enhanced` - Enhanced collision calculation
- `POST /simulate-breakup` - Breakup simulation
- `POST /predict-decay` - Orbital decay prediction
- `POST /propagate-orbit` - SGP4 orbit propagation

All endpoints are proxied through Vite dev server (configured in `vite.config.js`).

---

## Styling

All components use the same dark theme:
- Background: `var(--bg-card)` (#111827)
- Accent color: `var(--accent)` (#00d4aa)
- Text: `var(--text)` (#e2e8f0)
- Muted text: `var(--text-muted)` (#94a3b8)
- Font: Space Grotesk (body), JetBrains Mono (numbers)

---

## Next Steps (Optional)

- [ ] Add 3D orbit visualization for SGP4 propagation
- [ ] Add charts for decay rate over time
- [ ] Add fragment size distribution histogram
- [ ] Add export functionality (CSV/JSON)
- [ ] Add comparison mode (before/after enhancements)
