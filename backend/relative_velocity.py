"""
Relative velocity calculation for collision probability.
Accounts for impact velocity between satellite and debris.
Higher relative velocity increases collision energy and affects probability.
"""

import numpy as np
from typing import Tuple

# Typical LEO orbital velocity (km/s)
TYPICAL_LEO_VELOCITY = 7.5


def compute_orbital_velocity(altitude_km: float) -> float:
    """
    Compute circular orbital velocity at given altitude.
    v = sqrt(GM / r), r = R_Earth + altitude
    """
    MU_EARTH = 398600.4418  # km³/s²
    R_EARTH = 6371.0  # km
    r = R_EARTH + altitude_km
    v = np.sqrt(MU_EARTH / r)
    return float(v)


def compute_relative_velocity(
    v_sat: float,
    v_debris: float = None,
    impact_angle_deg: float = 90.0,
) -> float:
    """
    Compute relative impact velocity between satellite and debris.
    
    Args:
        v_sat: Satellite velocity (km/s)
        v_debris: Debris velocity (km/s). If None, assumes same as satellite.
        impact_angle_deg: Impact angle (0° = head-on, 90° = perpendicular, 180° = tail-on)
    
    Returns:
        Relative velocity magnitude (km/s)
    """
    if v_debris is None:
        v_debris = v_sat
    
    # Convert angle to radians
    theta_rad = np.radians(impact_angle_deg)
    
    # Relative velocity vector magnitude
    # v_rel = sqrt(v_sat² + v_debris² - 2*v_sat*v_debris*cos(theta))
    v_rel = np.sqrt(
        v_sat ** 2 + v_debris ** 2 - 2 * v_sat * v_debris * np.cos(theta_rad)
    )
    
    return float(v_rel)


def collision_probability_with_velocity(
    base_probability: float,
    relative_velocity_km_s: float,
    reference_velocity_km_s: float = TYPICAL_LEO_VELOCITY,
) -> float:
    """
    Adjust collision probability based on relative velocity.
    Higher velocity = higher collision rate (proportional to velocity).
    
    P_adjusted = P_base × (v_rel / v_ref)
    
    Args:
        base_probability: Base collision probability (from flux model)
        relative_velocity_km_s: Relative impact velocity (km/s)
        reference_velocity_km_s: Reference velocity for normalization (km/s)
    
    Returns:
        Velocity-adjusted collision probability
    """
    velocity_factor = relative_velocity_km_s / reference_velocity_km_s
    adjusted_prob = base_probability * velocity_factor
    return float(np.clip(adjusted_prob, 0, 1))


def compute_collision_energy(
    relative_velocity_km_s: float,
    debris_mass_kg: float,
) -> float:
    """
    Compute collision kinetic energy.
    E = 0.5 × m × v²
    
    Returns energy in Joules.
    """
    v_ms = relative_velocity_km_s * 1000  # Convert to m/s
    energy_joules = 0.5 * debris_mass_kg * (v_ms ** 2)
    return float(energy_joules)
