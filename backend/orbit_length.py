"""
Orbit length calculation for circular and elliptical orbits.
L_orbit = 2πr for circular
L_orbit ≈ π[3(a+b) − √((3a+b)(a+3b))] for elliptical
"""

import numpy as np
from typing import Literal

# Earth radius in km (for altitude -> radius conversion)
EARTH_RADIUS_KM = 6371.0


def orbit_length_circular(altitude_km: float) -> float:
    """Circular orbit: L = 2πr, r = R_Earth + altitude."""
    r = EARTH_RADIUS_KM + float(altitude_km)
    return float(2 * np.pi * r)


def orbit_length_elliptical(
    semi_major_axis_km: float = None,
    semi_minor_axis_km: float = None,
    perigee_km: float = None,
    apogee_km: float = None,
) -> float:
    """
    Elliptical orbit: L ≈ π[3(a+b) − √((3a+b)(a+3b))]
    Provide either (semi_major_axis_km, semi_minor_axis_km)
    or (perigee_km, apogee_km) as altitude above Earth surface.
    """
    if semi_major_axis_km is not None and semi_minor_axis_km is not None:
        a = float(semi_major_axis_km)
        b = float(semi_minor_axis_km)
    elif perigee_km is not None and apogee_km is not None:
        r_peri = EARTH_RADIUS_KM + float(perigee_km)
        r_apo = EARTH_RADIUS_KM + float(apogee_km)
        a = (r_peri + r_apo) / 2
        # b = semi-minor: for ellipse 2a = r_peri + r_apo, 2c = r_apo - r_peri
        # b² = a² - c², c = (r_apo - r_peri)/2
        c = (r_apo - r_peri) / 2
        b = np.sqrt(max(0, a**2 - c**2))
    else:
        raise ValueError("Provide semi_major_axis_km and semi_minor_axis_km, or perigee_km and apogee_km")

    term = np.sqrt((3 * a + b) * (a + 3 * b))
    L = np.pi * (3 * (a + b) - term)
    return float(max(L, 0))


def compute_orbit_length(
    orbit_type: Literal["circular", "elliptical"],
    altitude_km: float = None,
    semi_major_axis_km: float = None,
    semi_minor_axis_km: float = None,
    perigee_km: float = None,
    apogee_km: float = None,
) -> float:
    """
    Compute orbit length based on orbit type and parameters.
    For circular: altitude_km required.
    For elliptical: perigee_km & apogee_km, or semi_major_axis_km & semi_minor_axis_km.
    """
    if orbit_type == "circular":
        if altitude_km is None:
            raise ValueError("altitude_km required for circular orbit")
        return orbit_length_circular(altitude_km)
    elif orbit_type == "elliptical":
        return orbit_length_elliptical(
            semi_major_axis_km=semi_major_axis_km,
            semi_minor_axis_km=semi_minor_axis_km,
            perigee_km=perigee_km,
            apogee_km=apogee_km,
        )
    else:
        raise ValueError(f"Unknown orbit_type: {orbit_type}")
