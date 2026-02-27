# AstroCleanAI - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AstroCleanAI System                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Data Layer    │
│  (fetch_tle.py) │
└────────┬────────┘
         │ TLE Data (NORAD Catalog)
         ↓
┌─────────────────┐
│  Physics Engine │
│  (propagation/) │
│   - propagate   │
│   - distance    │
└────────┬────────┘
         │ Position & Velocity Vectors
         ↓
┌─────────────────┐
│ Analysis Layer  │
│ (probability/)  │
│  - Monte Carlo  │
│  - Poisson      │
└────────┬────────┘
         │ Collision Probability
         ↓
┌─────────────────┐
│ Decision Engine │
│(optimization/)  │
│  - Grid Search  │
│  - Genetic Algo │
└────────┬────────┘
         │ Optimal Maneuver
         ↓
┌─────────────────┐
│ Visualization   │
│(visualization/) │
│  - Plotly 3D    │
└────────┬────────┘
         │ Interactive HTML
         ↓
┌─────────────────┐
│  User Output    │
│ (output/*.html) │
└─────────────────┘
```

## Component Details

### 1. Data Layer
```
┌──────────────────────────────────────┐
│         fetch_tle.py                  │
├──────────────────────────────────────┤
│ • Celestrak API Integration          │
│ • TLE Download & Parsing             │
│ • Data Validation                    │
│ • File Management                    │
└──────────────────────────────────────┘
         ↓
    TLE Files
    (data/*.txt)
```

### 2. Propagation Module
```
┌──────────────────────────────────────┐
│      propagation/propagate.py        │
├──────────────────────────────────────┤
│ • SGP4 Orbit Propagator              │
│ • TLE → State Vector Conversion      │
│ • Trajectory Generation              │
│ • Error Handling                     │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│   propagation/distance_check.py      │
├──────────────────────────────────────┤
│ • Euclidean Distance Calculation     │
│ • Close Approach Detection           │
│ • Risk Zone Classification           │
│ • Event Logging                      │
└──────────────────────────────────────┘
```

### 3. Probability Module
```
┌──────────────────────────────────────┐
│ probability/collision_probability.py │
├──────────────────────────────────────┤
│ • Covariance Matrix Creation         │
│ • 2D Gaussian Model (Chan Method)    │
│ • Monte Carlo Simulation             │
│ • Poisson Distribution Model         │
│ • Risk Category Assignment           │
└──────────────────────────────────────┘
```

### 4. Optimization Module
```
┌──────────────────────────────────────┐
│     optimization/avoidance.py        │
├──────────────────────────────────────┤
│ • Burn Vector Computation            │
│ • Grid Search Optimizer              │
│ • Genetic Algorithm                  │
│ • Cost Function Evaluation           │
│ • Maneuver Planning                  │
└──────────────────────────────────────┘
```

### 5. Visualization Module
```
┌──────────────────────────────────────┐
│   visualization/plot_orbits.py       │
├──────────────────────────────────────┤
│ • 3D Earth Sphere Rendering          │
│ • Trajectory Plotting                │
│ • Collision Point Marking            │
│ • Before/After Comparison            │
│ • HTML Export                        │
└──────────────────────────────────────┘
```

### 6. Main Controller
```
┌──────────────────────────────────────┐
│            main.py                    │
├──────────────────────────────────────┤
│ • System Initialization              │
│ • Pipeline Orchestration             │
│ • Component Integration              │
│ • Results Reporting                  │
└──────────────────────────────────────┘
```

## Data Flow Diagram

```
START
  ↓
┌─────────────┐
│ Download TLE│
│   (Celestrak)│
└──────┬──────┘
       ↓
┌─────────────┐
│  Parse TLE  │
│   (SGP4)    │
└──────┬──────┘
       ↓
┌─────────────┐      ┌─────────────┐
│ Propagate   │ ──→  │ Propagate   │
│ Satellite   │      │   Debris    │
└──────┬──────┘      └──────┬──────┘
       │                    │
       └────────┬───────────┘
                ↓
       ┌─────────────┐
       │  Calculate  │
       │  Distance   │
       └──────┬──────┘
              ↓
       ┌─────────────┐
       │ Close       │  No
       │ Approach?   ├────→ [Safe - End]
       └──────┬──────┘
              │ Yes
              ↓
       ┌─────────────┐
       │ Calculate   │
       │ Probability │
       └──────┬──────┘
              ↓
       ┌─────────────┐
       │   High      │  No
       │   Risk?     ├────→ [Monitor - End]
       └──────┬──────┘
              │ Yes
              ↓
       ┌─────────────┐
       │  Optimize   │
       │  Maneuver   │
       └──────┬──────┘
              ↓
       ┌─────────────┐
       │  Visualize  │
       │   Results   │
       └──────┬──────┘
              ↓
       ┌─────────────┐
       │   Output    │
       │    HTML     │
       └─────────────┘
              ↓
             END
```

## Module Dependencies

```
main.py
├── fetch_tle.py
├── propagation/
│   ├── propagate.py
│   │   └── sgp4 (external)
│   └── distance_check.py
│       └── propagate.py
├── probability/
│   └── collision_probability.py
│       ├── numpy (external)
│       └── scipy (external)
├── optimization/
│   └── avoidance.py
│       └── propagate.py
└── visualization/
    └── plot_orbits.py
        └── plotly (external)
```

## External Dependencies

```
┌─────────────────────────────────────┐
│      Python Standard Library        │
│  • datetime, os, copy               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Scientific Computing           │
│  • NumPy - Arrays & Math            │
│  • SciPy - Statistical Functions    │
│  • Pandas - Data Structures         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Orbital Mechanics              │
│  • sgp4 - Satellite Propagation     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Visualization                  │
│  • Plotly - 3D Interactive Plots    │
│  • Matplotlib - Static Plots        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Web & Network                  │
│  • requests - HTTP API Calls        │
└─────────────────────────────────────┘
```

## File Organization

```
AstroCleanAI/
│
├── README.md              # Project overview
├── QUICKSTART.md          # Quick start guide
├── TECHNICAL_DOCS.md      # Technical documentation
├── ARCHITECTURE.md        # This file
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
│
├── fetch_tle.py          # TLE data fetcher
├── main.py               # Main system controller
│
├── data/                 # TLE data files
│   ├── iss.txt
│   ├── debris1.txt
│   └── debris2.txt
│
├── propagation/          # Orbit prediction
│   ├── __init__.py
│   ├── propagate.py
│   └── distance_check.py
│
├── probability/          # Risk assessment
│   ├── __init__.py
│   └── collision_probability.py
│
├── optimization/         # Maneuver planning
│   ├── __init__.py
│   └── avoidance.py
│
├── visualization/        # Graphics & plots
│   ├── __init__.py
│   └── plot_orbits.py
│
└── output/              # Generated visualizations
    └── collision_scenario.html
```

## Execution Flow

### Initialization Phase
1. Load configuration
2. Initialize components
3. Validate dependencies

### Data Acquisition Phase
1. Check for existing TLE data
2. Download if missing/outdated
3. Parse and validate TLE files

### Analysis Phase
1. Propagate satellite orbit
2. Propagate debris orbit
3. Calculate distances at each timestep
4. Identify close approaches

### Risk Assessment Phase
1. Extract closest approach event
2. Calculate collision probability
3. Classify risk level

### Decision Phase
1. If high risk:
   - Plan avoidance maneuver
   - Optimize delta-V
   - Generate maneuver plan
2. If low risk:
   - Continue monitoring

### Output Phase
1. Generate 3D visualization
2. Export to HTML
3. Display results summary

## Performance Optimization Strategies

1. **Caching**: Store propagated trajectories
2. **Parallel Processing**: Evaluate multiple maneuvers simultaneously
3. **Adaptive Sampling**: Use finer time steps only near close approaches
4. **GPU Acceleration**: Offload Monte Carlo simulations (future)
5. **Database Integration**: Cache TLE data and results (future)

---

**Version**: 1.0  
**Last Updated**: February 2026
