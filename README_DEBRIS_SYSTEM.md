# Space Debris Collision Probability Prediction System

A full-stack scientific web application that models orbital debris flux using a Petri Net–based mathematical model (NASA SSP30425 / M. Torky et al.), computes collision probability via Poisson distribution, and validates with Monte Carlo simulation.

## Features

- **Debris flux model** – λ × μ with H(d), φ(h,S), θ(i), F1/F2, g1/g2
- **Orbit length** – Circular and elliptical orbits
- **Poisson collision probability** – P₀, Q, Pₙ
- **Monte Carlo validation** – 10,000 trials
- **Year trend graph** – Collision probability 2019–2030
- **Petri Net animation** – Transitions t1→t2→t3→t4→t5

## Quick Start

### Backend (Python + FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 (frontend proxies API to http://localhost:8000).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/calculate` | DebrisFlux, OrbitLength, NTotal, P0, Q |
| POST | `/collision-vs-year` | Array of {year, probability} for 2019–2030 |
| POST | `/monte-carlo` | MonteCarloProbability, PoissonProbability, Trials |
| POST | `/petri-net` | Petri Net transition outputs for animation |

## Project Structure

```
COLLIDERS/
├── backend/
│   ├── main.py           # FastAPI app & endpoints
│   ├── debris_flux.py     # Fr, FC, H, φ, F1, F2, g1, g2, θ
│   ├── orbit_length.py   # Circular & elliptical orbit length
│   ├── petri_net.py      # t1–t5 transitions
│   ├── poisson.py        # P0, Q, Pn
│   ├── monte_carlo.py    # 10k trials
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── InputForm.jsx
│   │   │   ├── CollisionGraph.jsx
│   │   │   ├── PetriNetAnimation.jsx
│   │   │   └── MonteCarloResult.jsx
│   │   └── main.jsx
│   └── package.json
└── README_DEBRIS_SYSTEM.md
```

## Input Parameters

- Debris diameter (mm)
- Altitude (km) – limited to 0–2000
- Inclination (°)
- Year
- Solar flux S
- Exposure area (m²)
- Exposure time (years)
- Orbit type (circular / elliptical)
- Elliptical: perigee, apogee (km)

## Requirements

- Python 3.9+
- Node.js 18+
- NumPy, SciPy (double precision)
- Monte Carlo 10k trials &lt; 1 s
