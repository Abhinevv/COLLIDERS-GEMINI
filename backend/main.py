"""
FastAPI backend for Space Debris Collision Probability Prediction System.
Endpoints: /calculate, /collision-vs-year, /monte-carlo
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List

from debris_flux import compute_flux
from orbit_length import compute_orbit_length
from petri_net import run_petri_net
from poisson import collision_probability, poisson_probability_zero, compute_poisson_results
from monte_carlo import run_monte_carlo

app = FastAPI(title="Space Debris Collision Probability API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Input Models ---

class OrbitParams(BaseModel):
    orbit_type: Literal["circular", "elliptical"] = "circular"
    altitude_km: Optional[float] = None
    semi_major_axis_km: Optional[float] = None
    semi_minor_axis_km: Optional[float] = None
    perigee_km: Optional[float] = None
    apogee_km: Optional[float] = None

    @field_validator("altitude_km")
    @classmethod
    def alt_max(cls, v):
        if v is not None and (v < 0 or v > 2000):
            raise ValueError("Altitude must be 0–2000 km")
        return v


class CalculateInput(BaseModel):
    debris_diameter: float = Field(..., gt=0, description="Debris diameter (mm)")
    altitude: float = Field(..., ge=0, le=2000, description="Altitude (km)")
    inclination: float = Field(..., ge=0, le=180, description="Inclination (deg)")
    year: float = Field(..., ge=1988, le=2100, description="Year")
    solar_flux: float = Field(..., ge=0, description="Solar flux S")
    exposure_area: float = Field(..., gt=0, description="Exposure area (m²)")
    exposure_time: float = Field(..., gt=0, description="Exposure time (years)")
    orbit_params: OrbitParams = Field(default_factory=lambda: OrbitParams())


class CollisionVsYearInput(BaseModel):
    debris_diameter: float = Field(..., gt=0)
    altitude: float = Field(..., ge=0, le=2000)
    inclination: float = Field(..., ge=0, le=180)
    solar_flux: float = Field(..., ge=0)
    exposure_area: float = Field(..., gt=0)
    exposure_time: float = Field(..., gt=0)
    orbit_params: OrbitParams = Field(default_factory=lambda: OrbitParams())


class MonteCarloInput(BaseModel):
    debris_diameter: float = Field(..., gt=0)
    altitude: float = Field(..., ge=0, le=2000)
    inclination: float = Field(..., ge=0, le=180)
    year: float = Field(..., ge=1988, le=2100)
    solar_flux: float = Field(..., ge=0)
    exposure_area: float = Field(..., gt=0)
    exposure_time: float = Field(..., gt=0)
    orbit_params: OrbitParams = Field(default_factory=lambda: OrbitParams())
    trials: int = Field(default=10000, ge=100, le=100000)


def _get_orbit_length(op: OrbitParams, altitude: float) -> float:
    if op.orbit_type == "circular":
        return compute_orbit_length("circular", altitude_km=altitude)
    return compute_orbit_length(
        "elliptical",
        altitude_km=op.altitude_km or altitude,
        semi_major_axis_km=op.semi_major_axis_km,
        semi_minor_axis_km=op.semi_minor_axis_km,
        perigee_km=op.perigee_km,
        apogee_km=op.apogee_km,
    )


def _compute_N_total(FC: float, L_orbit: float, A: float, T: float) -> float:
    return L_orbit * FC * A * T


@app.post("/calculate")
def calculate(data: CalculateInput):
    """
    Compute debris flux, orbit length, N_total, P0, Q.
    """
    try:
        _, FC, _ = compute_flux(
            data.debris_diameter,
            data.altitude,
            data.inclination,
            data.year,
            data.solar_flux,
        )
        L_orbit = _get_orbit_length(data.orbit_params, data.altitude)
        N_total = _compute_N_total(FC, L_orbit, data.exposure_area, data.exposure_time)
        results = compute_poisson_results(N_total)
        Q = results["Q"]
        P0 = results["P0"]

        return {
            "DebrisFlux": FC,
            "OrbitLength": L_orbit,
            "NTotal": N_total,
            "P0": P0,
            "Q": Q,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/collision-vs-year")
def collision_vs_year(data: CollisionVsYearInput):
    """
    Return collision probability Q for each year from 2019 to 2030.
    """
    try:
        L_orbit = _get_orbit_length(data.orbit_params, data.altitude)
        out = []
        for y in range(2019, 2031):
            _, FC, _ = compute_flux(
                data.debris_diameter,
                data.altitude,
                data.inclination,
                y,
                data.solar_flux,
            )
            N_total = _compute_N_total(
                FC, L_orbit, data.exposure_area, data.exposure_time
            )
            Q = collision_probability(N_total)
            out.append({"year": y, "probability": round(Q, 8)})
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/monte-carlo")
def monte_carlo(data: MonteCarloInput):
    """
    Run Monte Carlo simulation and return Poisson vs Monte Carlo probability.
    """
    try:
        _, FC, _ = compute_flux(
            data.debris_diameter,
            data.altitude,
            data.inclination,
            data.year,
            data.solar_flux,
        )
        L_orbit = _get_orbit_length(data.orbit_params, data.altitude)
        N_total = _compute_N_total(
            FC, L_orbit, data.exposure_area, data.exposure_time
        )
        Q = collision_probability(N_total)
        P_MC, Q_poisson, trials = run_monte_carlo(Q, trials=data.trials)
        return {
            "MonteCarloProbability": round(P_MC, 8),
            "PoissonProbability": round(Q_poisson, 8),
            "Trials": trials,
            "Difference": round(abs(P_MC - Q_poisson), 8),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/petri-net")
def petri_net_run(data: CalculateInput):
    """
    Run Petri Net model and return transition outputs for animation.
    """
    try:
        result = run_petri_net(
            data.debris_diameter,
            data.altitude,
            data.inclination,
            data.year,
            data.solar_flux,
        )
        # Format for frontend
        return {
            "t1": result["t1"],
            "t2": result["t2"],
            "t3": result["t3"],
            "t4": result["t4"],
            "t5": result["t5"],
            "FC": result["FC"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
