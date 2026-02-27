"""
Space debris analysis helpers.
Provides a function `analyze_debris_vs_satellite` that attempts to fetch space debris
ephemerides and compute closest approach against an Earth satellite trajectory.

This module requires `astroquery`, `astropy`, and `poliastro` for full operation.
If those packages are not installed the functions will raise ImportError with
installation guidance.
"""
from datetime import datetime, timezone
import numpy as np


def _require_packages():
    try:
        from astroquery.jplhorizons import Horizons
        from astropy.time import Time
        import astropy.units as u
        return Horizons, Time, u
    except Exception as e:
        raise ImportError(
            "Missing dependencies for space debris analysis.\n"
            "Install with: pip install astroquery astropy poliastro"
        )


def analyze_debris_vs_satellite(debris_designation: str,
                                  satellite_propagator,
                                  duration_minutes: int = 180,
                                  step_seconds: int = 60,
                                  monte_carlo_samples: int = 1000):
    """
    Analyze closest approach between space debris (by designation) and a satellite.

    Parameters
    - debris_designation: string understood by JPL Horizons (e.g. '433' or 'Ceres')
    - satellite_propagator: an instance of `OrbitPropagator` (from `propagation.propagate`)
    - duration_minutes, step_seconds: propagation window for the satellite
    - monte_carlo_samples: number of Monte Carlo draws around debris nominal state

    Returns a dictionary with summary values or raises ImportError when dependencies
    are missing.
    """
    Horizons, Time, u = _require_packages()

    # Build epochs array (UTC) for the requested window
    start_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    num_steps = int((duration_minutes * 60) / step_seconds)

    # Use astropy Time arithmetic to create an array of epochs (UTC)
    t0 = Time(start_dt, scale='utc')
    astropy_epochs = t0 + (np.arange(num_steps) * step_seconds) * u.s

    # Query JPL Horizons for debris state vectors (heliocentric) at requested epochs
    try:
        obj = Horizons(id=debris_designation, location='@sun', epochs=astropy_epochs.jd)
        vec = obj.vectors()
    except Exception as e:
        raise RuntimeError(f"Failed to query JPL Horizons: {e}")

    # Extract debris heliocentric positions (AU) and convert to km
    # Horizons.vectors() returns columns: x,y,z (AU), vx,vy,vz (AU/day)
    # Convert masked columns to regular numpy arrays (float)
    debris_pos_au = np.vstack([
        np.array(vec['x'], dtype=float),
        np.array(vec['y'], dtype=float),
        np.array(vec['z'], dtype=float)
    ]).T  # shape (N,3)
    AU_KM = 149597870.7
    debris_pos_km = debris_pos_au * AU_KM

    # Get Earth's heliocentric vectors to convert debris->geocentric
    earth = Horizons(id='399', location='@sun', epochs=astropy_epochs.jd)
    earth_vec = earth.vectors()
    earth_pos_au = np.vstack([
        np.array(earth_vec['x'], dtype=float),
        np.array(earth_vec['y'], dtype=float),
        np.array(earth_vec['z'], dtype=float)
    ]).T
    earth_pos_km = earth_pos_au * AU_KM

    # Compute debris geocentric positions (km)
    debris_geo_km = debris_pos_km - earth_pos_km

    # Propagate satellite trajectory using provided propagator
    traj = satellite_propagator.propagate_trajectory(start_dt, duration_minutes, step_seconds)
    if not traj:
        raise RuntimeError("Satellite propagation returned no states")

    sat_positions = np.vstack([s['position'] for s in traj])  # shape (N,3)

    # Compute distances at matching epochs
    if sat_positions.shape[0] != debris_geo_km.shape[0]:
        # If mismatch, resample to the shorter length
        n = min(sat_positions.shape[0], debris_geo_km.shape[0])
        sat_positions = sat_positions[:n]
        debris_geo_km = debris_geo_km[:n]

    dists = np.linalg.norm(sat_positions - debris_geo_km, axis=1)
    min_idx = int(np.argmin(dists))
    result = {
        'min_distance_km': float(dists[min_idx]),
        'min_time': str(traj[min_idx]['time']),
        'num_steps': len(dists)
    }

    return result
