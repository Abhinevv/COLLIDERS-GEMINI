# CollidersAI - System Architecture

## High-Level Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        CollidersAI System                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Data Layer    â”‚
â”‚  (fetch_tle.py) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ TLE Data (NORAD Catalog)
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Physics Engine â”‚
â”‚  (propagation/) â”‚
â”‚   - propagate   â”‚
â”‚   - distance    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ Position & Velocity Vectors
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Analysis Layer  â”‚
â”‚ (probability/)  â”‚
â”‚  - Monte Carlo  â”‚
â”‚  - Poisson      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ Collision Probability
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Decision Engine â”‚
â”‚(optimization/)  â”‚
â”‚  - Grid Search  â”‚
â”‚  - Genetic Algo â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ Optimal Maneuver
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Visualization   â”‚
â”‚(visualization/) â”‚
â”‚  - Plotly 3D    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ Interactive HTML
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  User Output    â”‚
â”‚ (output/*.html) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Component Details

### 1. Data Layer
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         fetch_tle.py                  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ Celestrak API Integration          â”‚
â”‚ â€¢ TLE Download & Parsing             â”‚
â”‚ â€¢ Data Validation                    â”‚
â”‚ â€¢ File Management                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â†“
    TLE Files
    (data/*.txt)
```

### 2. Propagation Module
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      propagation/propagate.py        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ SGP4 Orbit Propagator              â”‚
â”‚ â€¢ TLE â†’ State Vector Conversion      â”‚
â”‚ â€¢ Trajectory Generation              â”‚
â”‚ â€¢ Error Handling                     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   propagation/distance_check.py      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ Euclidean Distance Calculation     â”‚
â”‚ â€¢ Close Approach Detection           â”‚
â”‚ â€¢ Risk Zone Classification           â”‚
â”‚ â€¢ Event Logging                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 3. Probability Module
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ probability/collision_probability.py â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ Covariance Matrix Creation         â”‚
â”‚ â€¢ 2D Gaussian Model (Chan Method)    â”‚
â”‚ â€¢ Monte Carlo Simulation             â”‚
â”‚ â€¢ Poisson Distribution Model         â”‚
â”‚ â€¢ Risk Category Assignment           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 4. Optimization Module
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚     optimization/avoidance.py        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ Burn Vector Computation            â”‚
â”‚ â€¢ Grid Search Optimizer              â”‚
â”‚ â€¢ Genetic Algorithm                  â”‚
â”‚ â€¢ Cost Function Evaluation           â”‚
â”‚ â€¢ Maneuver Planning                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 5. Visualization Module
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   visualization/plot_orbits.py       â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ 3D Earth Sphere Rendering          â”‚
â”‚ â€¢ Trajectory Plotting                â”‚
â”‚ â€¢ Collision Point Marking            â”‚
â”‚ â€¢ Before/After Comparison            â”‚
â”‚ â€¢ HTML Export                        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 6. Main Controller
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚            main.py                    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ â€¢ System Initialization              â”‚
â”‚ â€¢ Pipeline Orchestration             â”‚
â”‚ â€¢ Component Integration              â”‚
â”‚ â€¢ Results Reporting                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Data Flow Diagram

```
START
  â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Download TLEâ”‚
â”‚   (Celestrak)â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Parse TLE  â”‚
â”‚   (SGP4)    â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Propagate   â”‚ â”€â”€â†’  â”‚ Propagate   â”‚
â”‚ Satellite   â”‚      â”‚   Debris    â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚                    â”‚
       â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚  Calculate  â”‚
       â”‚  Distance   â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚ Close       â”‚  No
       â”‚ Approach?   â”œâ”€â”€â”€â”€â†’ [Safe - End]
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â”‚ Yes
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚ Calculate   â”‚
       â”‚ Probability â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚   High      â”‚  No
       â”‚   Risk?     â”œâ”€â”€â”€â”€â†’ [Monitor - End]
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â”‚ Yes
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚  Optimize   â”‚
       â”‚  Maneuver   â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚  Visualize  â”‚
       â”‚   Results   â”‚
       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
              â†“
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚   Output    â”‚
       â”‚    HTML     â”‚
       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â†“
             END
```

## Module Dependencies

```
main.py
â”œâ”€â”€ fetch_tle.py
â”œâ”€â”€ propagation/
â”‚   â”œâ”€â”€ propagate.py
â”‚   â”‚   â””â”€â”€ sgp4 (external)
â”‚   â””â”€â”€ distance_check.py
â”‚       â””â”€â”€ propagate.py
â”œâ”€â”€ probability/
â”‚   â””â”€â”€ collision_probability.py
â”‚       â”œâ”€â”€ numpy (external)
â”‚       â””â”€â”€ scipy (external)
â”œâ”€â”€ optimization/
â”‚   â””â”€â”€ avoidance.py
â”‚       â””â”€â”€ propagate.py
â””â”€â”€ visualization/
    â””â”€â”€ plot_orbits.py
        â””â”€â”€ plotly (external)
```

## External Dependencies

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      Python Standard Library        â”‚
â”‚  â€¢ datetime, os, copy               â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      Scientific Computing           â”‚
â”‚  â€¢ NumPy - Arrays & Math            â”‚
â”‚  â€¢ SciPy - Statistical Functions    â”‚
â”‚  â€¢ Pandas - Data Structures         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      Orbital Mechanics              â”‚
â”‚  â€¢ sgp4 - Satellite Propagation     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      Visualization                  â”‚
â”‚  â€¢ Plotly - 3D Interactive Plots    â”‚
â”‚  â€¢ Matplotlib - Static Plots        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚      Web & Network                  â”‚
â”‚  â€¢ requests - HTTP API Calls        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## File Organization

```
CollidersAI/
â”‚
â”œâ”€â”€ README.md              # Project overview
â”œâ”€â”€ QUICKSTART.md          # Quick start guide
â”œâ”€â”€ TECHNICAL_DOCS.md      # Technical documentation
â”œâ”€â”€ ARCHITECTURE.md        # This file
â”œâ”€â”€ LICENSE                # MIT License
â”œâ”€â”€ requirements.txt       # Python dependencies
â”œâ”€â”€ .gitignore            # Git ignore rules
â”‚
â”œâ”€â”€ fetch_tle.py          # TLE data fetcher
â”œâ”€â”€ main.py               # Main system controller
â”‚
â”œâ”€â”€ data/                 # TLE data files
â”‚   â”œâ”€â”€ iss.txt
â”‚   â”œâ”€â”€ debris1.txt
â”‚   â””â”€â”€ debris2.txt
â”‚
â”œâ”€â”€ propagation/          # Orbit prediction
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ propagate.py
â”‚   â””â”€â”€ distance_check.py
â”‚
â”œâ”€â”€ probability/          # Risk assessment
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ collision_probability.py
â”‚
â”œâ”€â”€ optimization/         # Maneuver planning
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ avoidance.py
â”‚
â”œâ”€â”€ visualization/        # Graphics & plots
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ plot_orbits.py
â”‚
â””â”€â”€ output/              # Generated visualizations
    â””â”€â”€ collision_scenario.html
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
