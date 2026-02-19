"""
Atmospheric drag decay model for LEO satellites.
Lower altitude orbits decay due to atmospheric drag, affecting debris environment.
"""

import numpy as np
from typing import Dict

# Earth radius (km)
R_EARTH = 6371.0
# Standard atmospheric density at sea level (kg/m³)
RHO_0 = 1.225
# Scale height (km)
H_SCALE = 8.5


def atmospheric_density(altitude_km: float) -> float:
    """
    Compute atmospheric density at given altitude using exponential model.
    ρ(h) = ρ₀ × exp(-h / H_scale)
    
    Args:
        altitude_km: Altitude above Earth surface (km)
    
    Returns:
        Atmospheric density (kg/m³)
    """
    if altitude_km < 0:
        return RHO_0
    if altitude_km > 1000:
        return 0.0  # Negligible above 1000 km
    
    rho = RHO_0 * np.exp(-altitude_km / H_SCALE)
    return float(max(rho, 0))


def drag_acceleration(
    altitude_km: float,
    cross_sectional_area_m2: float,
    mass_kg: float,
    drag_coefficient: float = 2.2,
    velocity_km_s: float = None,
) -> float:
    """
    Compute drag acceleration due to atmospheric drag.
    a_drag = 0.5 × ρ × C_d × A × v² / m
    
    Args:
        altitude_km: Altitude (km)
        cross_sectional_area_m2: Cross-sectional area (m²)
        mass_kg: Object mass (kg)
        drag_coefficient: Drag coefficient (default 2.2 for typical satellite)
        velocity_km_s: Orbital velocity (km/s). If None, computes from altitude.
    
    Returns:
        Drag acceleration (m/s²)
    """
    rho = atmospheric_density(altitude_km)
    
    if velocity_km_s is None:
        # Compute circular orbital velocity
        MU_EARTH = 398600.4418  # km³/s²
        r = R_EARTH + altitude_km
        velocity_km_s = np.sqrt(MU_EARTH / r)
    
    velocity_ms = velocity_km_s * 1000  # Convert to m/s
    
    # Drag force per unit mass (acceleration)
    a_drag = 0.5 * rho * drag_coefficient * cross_sectional_area_m2 * (velocity_ms ** 2) / mass_kg
    
    return float(a_drag)


def orbital_decay_rate(
    altitude_km: float,
    cross_sectional_area_m2: float,
    mass_kg: float,
    drag_coefficient: float = 2.2,
) -> float:
    """
    Compute orbital decay rate (altitude change per unit time).
    dh/dt ≈ -2π × a_drag × (h / v)
    
    Args:
        altitude_km: Current altitude (km)
        cross_sectional_area_m2: Cross-sectional area (m²)
        mass_kg: Object mass (kg)
        drag_coefficient: Drag coefficient
    
    Returns:
        Decay rate (km/day, negative = decreasing altitude)
    """
    a_drag = drag_acceleration(altitude_km, cross_sectional_area_m2, mass_kg, drag_coefficient)
    
    # Compute orbital velocity
    MU_EARTH = 398600.4418
    r = R_EARTH + altitude_km
    v_km_s = np.sqrt(MU_EARTH / r)
    
    # Approximate decay rate (simplified)
    # More accurate: integrate over orbit, but this gives order of magnitude
    decay_rate_km_s = -2 * np.pi * (a_drag / 1000) * (altitude_km / v_km_s)
    decay_rate_km_day = decay_rate_km_s * 86400
    
    return float(decay_rate_km_day)


def predict_orbital_lifetime(
    initial_altitude_km: float,
    cross_sectional_area_m2: float,
    mass_kg: float,
    decay_altitude_km: float = 200.0,
) -> Dict:
    """
    Predict orbital lifetime until decay to specified altitude.
    
    Args:
        initial_altitude_km: Starting altitude (km)
        cross_sectional_area_m2: Cross-sectional area (m²)
        mass_kg: Object mass (kg)
        decay_altitude_km: Altitude at which object decays (km)
    
    Returns:
        Dict with lifetime_days, final_altitude_km, decay_rate_km_day
    """
    current_alt = initial_altitude_km
    days = 0
    max_days = 365 * 100  # Max 100 years
    
    while current_alt > decay_altitude_km and days < max_days:
        decay_rate = orbital_decay_rate(current_alt, cross_sectional_area_m2, mass_kg)
        if decay_rate >= 0:
            # No decay (too high altitude)
            break
        
        # Step forward by 1 day
        current_alt += decay_rate
        days += 1
        
        if current_alt < decay_altitude_km:
            break
    
    return {
        "lifetime_days": days,
        "final_altitude_km": float(current_alt),
        "decay_rate_km_day": float(decay_rate) if current_alt > decay_altitude_km else 0.0,
    }
