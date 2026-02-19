"""
SGP4 orbit propagation for time-dependent collision analysis.
Propagates satellite orbits forward in time to compute evolving collision probabilities.
"""

from sgp4.api import Satrec, WGS72
from sgp4.conveniences import jday_datetime
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Tuple

# Earth gravitational parameter (km³/s²)
MU_EARTH = 398600.4418
R_EARTH = 6371.0


def tle_to_satrec(line1: str, line2: str) -> Satrec:
    """Convert TLE lines to SGP4 satellite record."""
    satellite = Satrec.twoline2rv(line1, line2, WGS72)
    return satellite


def propagate_satellite(
    satellite: Satrec,
    start_time: datetime,
    end_time: datetime,
    step_seconds: float = 3600.0,
) -> List[Dict]:
    """
    Propagate satellite orbit from start_time to end_time.
    Returns list of state vectors: {time, position_km, velocity_km_s, altitude_km, inclination_deg}
    """
    results = []
    current = start_time
    jd_start, fr_start = jday_datetime(start_time)
    
    while current <= end_time:
        jd, fr = jday_datetime(current)
        error_code, r, v = satellite.sgp4(jd, fr)
        
        if error_code == 0:
            r_km = np.array(r)  # position in km
            v_km_s = np.array(v)  # velocity in km/s
            
            # Compute altitude
            altitude_km = np.linalg.norm(r_km) - R_EARTH
            
            # Compute inclination from velocity vector (approximate)
            # More accurate: use orbital elements from SGP4
            h_vec = np.cross(r_km, v_km_s)
            h_mag = np.linalg.norm(h_vec)
            if h_mag > 0:
                h_unit = h_vec / h_mag
                # Inclination = angle between h and z-axis
                inc_rad = np.arccos(np.clip(h_unit[2], -1, 1))
                inclination_deg = np.degrees(inc_rad)
            else:
                inclination_deg = 0.0
            
            results.append({
                "time": current.isoformat(),
                "position_km": r_km.tolist(),
                "velocity_km_s": v_km_s.tolist(),
                "altitude_km": float(altitude_km),
                "inclination_deg": float(inclination_deg),
            })
        
        current += timedelta(seconds=step_seconds)
    
    return results


def compute_orbital_elements_from_state(r: np.ndarray, v: np.ndarray) -> Dict:
    """
    Compute orbital elements from position and velocity vectors.
    Returns: semi_major_axis_km, eccentricity, inclination_deg, perigee_km, apogee_km
    """
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)
    
    # Specific angular momentum
    h_vec = np.cross(r, v)
    h_mag = np.linalg.norm(h_vec)
    
    # Specific energy
    energy = (v_mag ** 2) / 2 - MU_EARTH / r_mag
    
    # Semi-major axis
    a_km = -MU_EARTH / (2 * energy) if energy < 0 else np.inf
    
    # Eccentricity vector
    e_vec = (1 / MU_EARTH) * ((v_mag ** 2 - MU_EARTH / r_mag) * r - np.dot(r, v) * v)
    e = np.linalg.norm(e_vec)
    
    # Inclination
    if h_mag > 0:
        inc_rad = np.arccos(np.clip(h_vec[2] / h_mag, -1, 1))
        inclination_deg = np.degrees(inc_rad)
    else:
        inclination_deg = 0.0
    
    # Perigee and apogee
    r_peri = a_km * (1 - e) if a_km < np.inf else r_mag
    r_apo = a_km * (1 + e) if a_km < np.inf else r_mag
    perigee_km = r_peri - R_EARTH
    apogee_km = r_apo - R_EARTH
    
    return {
        "semi_major_axis_km": float(a_km) if a_km < np.inf else None,
        "eccentricity": float(e),
        "inclination_deg": float(inclination_deg),
        "perigee_km": float(perigee_km),
        "apogee_km": float(apogee_km),
    }
