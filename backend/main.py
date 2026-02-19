"""
FastAPI backend for Space Debris Collision Probability Prediction System.
Endpoints: /calculate, /collision-vs-year, /monte-carlo
"""

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List

from debris_flux import compute_flux
from orbit_length import compute_orbit_length
from petri_net import run_petri_net
from poisson import collision_probability, poisson_probability_zero, compute_poisson_results
from monte_carlo import run_monte_carlo
from celestrak_client import get_satellite_orbital_params
from relative_velocity import (
    compute_orbital_velocity,
    compute_relative_velocity,
    collision_probability_with_velocity,
)
from collision_geometry import (
    effective_collision_area,
    collision_probability_with_geometry,
)
from breakup_simulation import simulate_collision_breakup
from atmospheric_drag import (
    atmospheric_density,
    orbital_decay_rate,
    predict_orbital_lifetime,
)
from sgp4_propagator import (
    tle_to_satrec,
    propagate_satellite,
    compute_orbital_elements_from_state,
)
from datetime import datetime, timedelta

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
    # Standard formulation: expected collisions = flux × area × time.
    # FC is debris flux (per m² per year); orbit length is not multiplied here.
    return FC * A * T


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


class CalculateFromCelestrakInput(BaseModel):
    norad_id: int = Field(..., gt=0, description="NORAD catalog number (e.g. 25544 for ISS)")
    debris_diameter: float = Field(..., gt=0)
    year: float = Field(..., ge=1988, le=2100)
    solar_flux: float = Field(..., ge=0)
    exposure_area: float = Field(..., gt=0)
    exposure_time: float = Field(..., gt=0)


@app.get("/celestrak/satellite/{norad_id}")
def celestrak_satellite(norad_id: int):
    """
    Fetch orbital parameters from Celestrak for the given NORAD catalog number.
    Returns name, inclination, altitude_km, orbit_type, perigee_km, apogee_km for use in the app.
    """
    try:
        params = get_satellite_orbital_params(norad_id)
        return params
    except (ValueError, httpx.HTTPError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/calculate-from-celestrak")
def calculate_from_celestrak(data: CalculateFromCelestrakInput):
    """
    Run collision calculation using orbit data from Celestrak for the given NORAD ID.
    Other inputs (debris diameter, solar flux, area, time) are provided in the body.
    """
    try:
        orbit = get_satellite_orbital_params(data.norad_id)
    except (ValueError, httpx.HTTPError) as e:
        raise HTTPException(status_code=400, detail=f"Celestrak: {e}")

    altitude = orbit["altitude_km"]
    inclination = orbit["inclination"]
    op = OrbitParams(
        orbit_type=orbit["orbit_type"],
        altitude_km=altitude,
        perigee_km=orbit.get("perigee_km"),
        apogee_km=orbit.get("apogee_km"),
    )
    try:
        _, FC, _ = compute_flux(
            data.debris_diameter,
            altitude,
            inclination,
            data.year,
            data.solar_flux,
        )
        L_orbit = _get_orbit_length(op, altitude)
        N_total = _compute_N_total(FC, L_orbit, data.exposure_area, data.exposure_time)
        results = compute_poisson_results(N_total)
        return {
            "satellite": orbit,
            "DebrisFlux": FC,
            "OrbitLength": L_orbit,
            "NTotal": N_total,
            "P0": results["P0"],
            "Q": results["Q"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class EnhancedCalculateInput(BaseModel):
    debris_diameter: float = Field(..., gt=0)
    altitude: float = Field(..., ge=0, le=2000)
    inclination: float = Field(..., ge=0, le=180)
    year: float = Field(..., ge=1988, le=2100)
    solar_flux: float = Field(..., ge=0)
    exposure_area: float = Field(..., gt=0)
    exposure_time: float = Field(..., gt=0)
    impact_angle_deg: float = Field(default=90.0, ge=0, le=180)
    include_velocity: bool = Field(default=True)
    include_geometry: bool = Field(default=True)


@app.post("/calculate-enhanced")
def calculate_enhanced(data: EnhancedCalculateInput):
    """
    Enhanced collision calculation with relative velocity and collision geometry.
    """
    try:
        _, FC, _ = compute_flux(
            data.debris_diameter,
            data.altitude,
            data.inclination,
            data.year,
            data.solar_flux,
        )
        
        # Base probability
        N_total = FC * data.exposure_area * data.exposure_time
        Q_base = collision_probability(N_total)
        v_rel = None
        
        # Velocity adjustment
        if data.include_velocity:
            v_sat = compute_orbital_velocity(data.altitude)
            v_rel = compute_relative_velocity(v_sat, impact_angle_deg=data.impact_angle_deg)
            Q_base = collision_probability_with_velocity(Q_base, v_rel)
        
        # Geometry adjustment
        if data.include_geometry:
            Q_base = collision_probability_with_geometry(
                Q_base, data.exposure_area, data.impact_angle_deg
            )
        
        return {
            "DebrisFlux": FC,
            "NTotal": N_total,
            "Q_base": collision_probability(N_total),
            "Q_enhanced": Q_base,
            "relative_velocity_km_s": v_rel,
            "effective_area_m2": effective_collision_area(
                data.exposure_area, data.impact_angle_deg
            ) if data.include_geometry else data.exposure_area,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class BreakupSimulationInput(BaseModel):
    satellite_area_m2: float = Field(..., gt=0)
    debris_diameter_mm: float = Field(..., gt=0)
    relative_velocity_km_s: float = Field(..., gt=0)


@app.post("/simulate-breakup")
def simulate_breakup(data: BreakupSimulationInput):
    """
    Simulate collision breakup and generate debris fragments.
    """
    try:
        result = simulate_collision_breakup(
            data.satellite_area_m2,
            data.debris_diameter_mm,
            data.relative_velocity_km_s,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class DragDecayInput(BaseModel):
    initial_altitude_km: float = Field(..., ge=0, le=2000)
    cross_sectional_area_m2: float = Field(..., gt=0)
    mass_kg: float = Field(..., gt=0)
    decay_altitude_km: float = Field(default=200.0, ge=0)


@app.post("/predict-decay")
def predict_decay(data: DragDecayInput):
    """
    Predict orbital lifetime due to atmospheric drag decay.
    """
    try:
        result = predict_orbital_lifetime(
            data.initial_altitude_km,
            data.cross_sectional_area_m2,
            data.mass_kg,
            data.decay_altitude_km,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SGP4PropagateInput(BaseModel):
    tle_line1: str
    tle_line2: str
    start_time: str  # ISO format datetime
    end_time: str  # ISO format datetime
    step_seconds: float = Field(default=3600.0, gt=0)


@app.post("/propagate-orbit")
def propagate_orbit(data: SGP4PropagateInput):
    """
    Propagate satellite orbit using SGP4 from TLE.
    """
    try:
        satellite = tle_to_satrec(data.tle_line1, data.tle_line2)
        
        # Parse datetime - handle various formats
        start_str = data.start_time.replace("Z", "+00:00")
        end_str = data.end_time.replace("Z", "+00:00")
        
        # If no timezone, assume UTC
        if "+" not in start_str and "Z" not in data.start_time:
            start_str += "+00:00"
        if "+" not in end_str and "Z" not in data.end_time:
            end_str += "+00:00"
        
        try:
            start = datetime.fromisoformat(start_str)
        except ValueError:
            # Try parsing without timezone
            start = datetime.fromisoformat(data.start_time)
        
        try:
            end = datetime.fromisoformat(end_str)
        except ValueError:
            # Try parsing without timezone
            end = datetime.fromisoformat(data.end_time)
        
        states = propagate_satellite(satellite, start, end, data.step_seconds)
        
        return {
            "num_states": len(states),
            "states": states,
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
