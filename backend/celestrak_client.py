"""
Celestrak API client for fetching satellite orbital data (TLE/GP).
Converts NORAD GP elements to altitude, inclination, perigee, apogee for our model.
"""

import math
from typing import Optional
import httpx

# Earth gravitational parameter (km³/s²)
MU_EARTH = 398600.4418
# Earth radius (km)
R_EARTH = 6371.0

CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"
CELESTRAK_INDEX_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=json"


def _mean_motion_to_semi_major_axis(mean_motion_rev_per_day: float) -> float:
    """Convert mean motion (revolutions per day) to semi-major axis (km)."""
    if mean_motion_rev_per_day <= 0:
        raise ValueError("Mean motion must be positive")
    # n in rad/s: rev/day -> rad/s
    rev_per_sec = mean_motion_rev_per_day / 86400.0
    n_rad_s = 2 * math.pi * rev_per_sec
    # a³ = μ / n²  =>  a = (μ / n²)^(1/3)
    a_km = (MU_EARTH / (n_rad_s ** 2)) ** (1 / 3)
    return a_km


def fetch_gp_by_norad(norad_id: int) -> list:
    """Fetch GP (TLE) data from Celestrak by NORAD catalog number. Returns list of dicts."""
    url = f"{CELESTRAK_GP_URL}?CATNR={norad_id}&FORMAT=json"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    if not data:
        raise ValueError(f"No data returned for NORAD ID {norad_id}")
    return data if isinstance(data, list) else [data]


def gp_to_orbital_params(gp: dict) -> dict:
    """
    Convert one Celestrak GP record to our orbital parameters.
    Returns dict with: name, norad_id, inclination, altitude_km, orbit_type,
    perigee_km, apogee_km, eccentricity, epoch (for display).
    """
    name = gp.get("OBJECT_NAME", "Unknown")
    norad_id = gp.get("NORAD_CAT_ID")
    inc = float(gp.get("INCLINATION", 0))
    ecc = float(gp.get("ECCENTRICITY", 0))
    mm = float(gp.get("MEAN_MOTION", 0))
    epoch = gp.get("EPOCH", "")

    if mm <= 0:
        raise ValueError("Invalid mean motion from Celestrak")

    a_km = _mean_motion_to_semi_major_axis(mm)
    # Perigee and apogee radii (from center of Earth), then altitude
    r_peri = a_km * (1 - ecc)
    r_apo = a_km * (1 + ecc)
    perigee_km = r_peri - R_EARTH
    apogee_km = r_apo - R_EARTH

    # Mean altitude for circular approximation (for flux model)
    mean_alt_km = (perigee_km + apogee_km) / 2

    orbit_type = "elliptical" if ecc > 0.001 else "circular"

    return {
        "name": name,
        "norad_id": norad_id,
        "inclination": round(inc, 4),
        "altitude_km": round(mean_alt_km, 2),
        "orbit_type": orbit_type,
        "perigee_km": round(perigee_km, 2),
        "apogee_km": round(apogee_km, 2),
        "eccentricity": ecc,
        "epoch": epoch,
    }


def get_satellite_orbital_params(norad_id: int) -> dict:
    """
    Fetch Celestrak data for the given NORAD ID and return orbital params
    suitable for our collision model (altitude, inclination, orbit_type, perigee, apogee).
    """
    gp_list = fetch_gp_by_norad(norad_id)
    return gp_to_orbital_params(gp_list[0])
