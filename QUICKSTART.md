# AstroCleanAI - Quick Start Guide 🚀

## Get Running in 3 Steps

### Step 1: Setup Environment
```bash
# Clone the repository (or navigate to project folder)
cd AstroCleanAI

# Create virtual environment
python -m venv spaceenv

# Activate it
# On Linux/Mac:
source spaceenv/bin/activate
# On Windows:
spaceenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Run the System
```bash
python main.py
```

That's it! The system will:
1. ✓ Download live satellite data from Celestrak
2. ✓ Propagate orbits using SGP4
3. ✓ Detect close approaches
4. ✓ Calculate collision probability
5. ✓ Optimize avoidance maneuvers
6. ✓ Generate 3D visualization

### Step 3: View Results
Open the generated file in your browser:
```
output/collision_scenario.html
```

## Project Structure
```
AstroCleanAI/
│
├── fetch_tle.py           # Download satellite data
├── main.py                # Main system controller
│
├── propagation/           # Orbit prediction
│   ├── propagate.py       # SGP4 propagator
│   └── distance_check.py  # Close approach detection
│
├── probability/           # Risk assessment
│   └── collision_probability.py  # Monte Carlo & statistics
│
├── optimization/          # Maneuver planning
│   └── avoidance.py      # Genetic algorithm optimizer
│
└── visualization/         # 3D graphics
    └── plot_orbits.py    # Plotly visualizations
```

## Test Individual Components

### Test TLE Download
```bash
python fetch_tle.py
```

### Test Orbit Propagation
```bash
python -m propagation.propagate
```

### Test Close Approach Detection
```bash
python -m propagation.distance_check
```

### Test Probability Calculation
```bash
python -m probability.collision_probability
```

### Test Maneuver Optimization
```bash
python -m optimization.avoidance
```

### Test Visualization
```bash
python -m visualization.plot_orbits
```

## Customization

### Track Different Satellites
Edit `fetch_tle.py` or `main.py`:
```python
satellites = {
    '25544': 'iss.txt',      # ISS
    '12345': 'mysat.txt',    # Your satellite NORAD ID
}
```

### Adjust Detection Threshold
In `main.py`:
```python
self.detector = CloseApproachDetector(threshold_km=5.0)  # 5 km threshold
```

### Change Maneuver Parameters
In `main.py`:
```python
maneuver = self.optimizer.optimize_maneuver(
    burn_time,
    self.debris_prop,
    dv_range=(0.1, 5.0),  # Min and max delta-V (m/s)
    dv_step=0.1           # Search step size
)
```

## Troubleshooting

**Problem: "No module named 'sgp4'"**
→ Solution: `pip install sgp4`

**Problem: "TLE file not found"**
→ Solution: Run `python fetch_tle.py` first

**Problem: "Network error downloading TLE"**
→ Solution: Check internet connection, Celestrak may be down

**Problem: Visualization not showing**
→ Solution: Open the HTML file manually in browser from `output/` folder

## Next Steps

1. **Live Dashboard**: Add Streamlit UI for real-time monitoring
2. **Multiple Objects**: Track entire constellations
3. **API Integration**: Connect to Space-Track.org for more data
4. **ML Predictions**: Train models on historical conjunction data
5. **Alert System**: Email/SMS notifications for high-risk events

## Resources
- TLE Data: https://celestrak.org
- SGP4 Documentation: https://pypi.org/project/sgp4/
- Orbital Mechanics: https://orbital-mechanics.space

---

**Need Help?** Open an issue on GitHub or check the main README.md
