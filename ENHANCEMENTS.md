# 🚀 Enhanced Collision Probability System

## New Features Added

### 1. **SGP4 Propagation** ✅
- **Module**: `backend/sgp4_propagator.py`
- **Endpoint**: `POST /propagate-orbit`
- **Purpose**: Propagate satellite orbits forward in time using SGP4
- **Input**: TLE lines, start/end time, step size
- **Output**: Time series of position, velocity, altitude, inclination
- **Use Case**: Analyze collision probability evolution over mission lifetime

### 2. **Relative Velocity Calculation** ✅
- **Module**: `backend/relative_velocity.py`
- **Integration**: Enhanced `/calculate-enhanced` endpoint
- **Purpose**: Account for impact velocity between satellite and debris
- **Formula**: 
  - `v_rel = sqrt(v_sat² + v_debris² - 2×v_sat×v_debris×cos(θ))`
  - Adjusted probability: `P_adj = P_base × (v_rel / v_ref)`
- **Impact**: Higher relative velocity → higher collision rate

### 3. **Collision Geometry** ✅
- **Module**: `backend/collision_geometry.py`
- **Integration**: Enhanced `/calculate-enhanced` endpoint
- **Purpose**: Account for impact angle and effective collision area
- **Formula**: 
  - `A_eff = A × sin(impact_angle)`
  - Adjusted probability based on effective area
- **Impact**: Perpendicular impacts (90°) have full area; oblique impacts have reduced effective area

### 4. **Breakup Simulation** ✅
- **Module**: `backend/breakup_simulation.py`
- **Endpoint**: `POST /simulate-breakup`
- **Purpose**: Simulate collision breakup and generate debris fragments
- **Model**: NASA SBM-inspired power-law distribution
- **Formula**: `N(>L) = 0.1 × M^0.75 × L^-1.6`
- **Output**: Fragment sizes, masses, collision energy
- **Use Case**: Assess secondary debris generation from collisions

### 5. **Atmospheric Drag Decay** ✅
- **Module**: `backend/atmospheric_drag.py`
- **Endpoint**: `POST /predict-decay`
- **Purpose**: Predict orbital lifetime due to atmospheric drag
- **Model**: Exponential atmospheric density + drag acceleration
- **Formulas**:
  - `ρ(h) = ρ₀ × exp(-h / H_scale)`
  - `a_drag = 0.5 × ρ × C_d × A × v² / m`
  - `dh/dt ≈ -2π × a_drag × (h / v)`
- **Output**: Lifetime in days, decay rate, final altitude
- **Use Case**: Predict when low-altitude satellites will decay

---

## New API Endpoints

### `POST /calculate-enhanced`
Enhanced collision calculation with velocity and geometry adjustments.

**Request Body**:
```json
{
  "debris_diameter": 10,
  "altitude": 400,
  "inclination": 51.6,
  "year": 2024,
  "solar_flux": 200,
  "exposure_area": 10,
  "exposure_time": 1,
  "impact_angle_deg": 90,
  "include_velocity": true,
  "include_geometry": true
}
```

**Response**:
```json
{
  "DebrisFlux": 3.44e-6,
  "NTotal": 0.000034,
  "Q_base": 0.000034,
  "Q_enhanced": 0.000041,
  "relative_velocity_km_s": 7.5,
  "effective_area_m2": 10.0
}
```

### `POST /simulate-breakup`
Simulate collision breakup and generate fragments.

**Request Body**:
```json
{
  "satellite_area_m2": 100,
  "debris_diameter_mm": 10,
  "relative_velocity_km_s": 10.0
}
```

**Response**:
```json
{
  "collision_energy_joules": 50000,
  "debris_mass_kg": 0.001,
  "relative_velocity_km_s": 10.0,
  "num_fragments": 150,
  "fragments": [
    {"diameter_mm": 0.5, "mass_kg": 0.0001},
    ...
  ]
}
```

### `POST /predict-decay`
Predict orbital lifetime due to atmospheric drag.

**Request Body**:
```json
{
  "initial_altitude_km": 400,
  "cross_sectional_area_m2": 10,
  "mass_kg": 1000,
  "decay_altitude_km": 200
}
```

**Response**:
```json
{
  "lifetime_days": 1825,
  "final_altitude_km": 200.0,
  "decay_rate_km_day": -0.11
}
```

### `POST /propagate-orbit`
Propagate satellite orbit using SGP4 from TLE.

**Request Body**:
```json
{
  "tle_line1": "1 25544U 98067A   24050.12345678  .00001234  00000+0  12345-4 0  9999",
  "tle_line2": "2 25544  51.6323 161.9142 0008604 112.9152 247.2745 15.48140240123456",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-02T00:00:00Z",
  "step_seconds": 3600
}
```

**Response**:
```json
{
  "num_states": 24,
  "states": [
    {
      "time": "2024-01-01T00:00:00",
      "position_km": [x, y, z],
      "velocity_km_s": [vx, vy, vz],
      "altitude_km": 408.5,
      "inclination_deg": 51.6
    },
    ...
  ]
}
```

---

## Installation

Install new dependency:
```bash
pip install sgp4
```

Or update requirements:
```bash
pip install -r backend/requirements.txt
```

---

## Usage Examples

### Enhanced Calculation
```python
import requests

response = requests.post("http://localhost:8000/calculate-enhanced", json={
    "debris_diameter": 10,
    "altitude": 400,
    "inclination": 51.6,
    "year": 2024,
    "solar_flux": 200,
    "exposure_area": 10,
    "exposure_time": 1,
    "impact_angle_deg": 90,
    "include_velocity": True,
    "include_geometry": True,
})
```

### Breakup Simulation
```python
response = requests.post("http://localhost:8000/simulate-breakup", json={
    "satellite_area_m2": 100,
    "debris_diameter_mm": 10,
    "relative_velocity_km_s": 10.0,
})
fragments = response.json()["fragments"]
```

### Orbital Decay Prediction
```python
response = requests.post("http://localhost:8000/predict-decay", json={
    "initial_altitude_km": 400,
    "cross_sectional_area_m2": 10,
    "mass_kg": 1000,
})
lifetime_days = response.json()["lifetime_days"]
```

---

## Mathematical Models

### Relative Velocity
- **Orbital velocity**: `v = sqrt(GM / r)`
- **Relative velocity**: `v_rel = sqrt(v₁² + v₂² - 2×v₁×v₂×cos(θ))`
- **Velocity factor**: `P_adj = P_base × (v_rel / v_ref)`

### Collision Geometry
- **Effective area**: `A_eff = A × sin(θ)`
- **Geometry factor**: `P_adj = P_base × (A_eff / A_ref)`

### Breakup Model
- **Power-law**: `N(>L) = 0.1 × M^0.75 × L^-1.6`
- **Collision energy**: `E = 0.5 × m × v²`

### Atmospheric Drag
- **Density**: `ρ(h) = ρ₀ × exp(-h / H_scale)`
- **Drag acceleration**: `a = 0.5 × ρ × C_d × A × v² / m`
- **Decay rate**: `dh/dt ≈ -2π × a × (h / v)`

---

## Next Steps (Optional Enhancements)

- [ ] Integrate SGP4 propagation into frontend visualization
- [ ] Add 3D orbit visualization
- [ ] Implement debris cloud evolution over time
- [ ] Add collision avoidance maneuver planning
- [ ] Integrate with Space-Track API for real-time debris tracking
- [ ] Add Monte Carlo for breakup fragment trajectories
