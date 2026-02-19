"""
Breakup simulation using NASA Standard Breakup Model (SBM) principles.
When a collision occurs, generates fragments following power-law distribution.
"""

import numpy as np
from typing import List, Dict
from scipy.stats import powerlaw

# NASA SBM constants (simplified)
SBM_EXPONENT = -1.6  # Power-law exponent for fragment size distribution
MIN_FRAGMENT_SIZE_MM = 0.1
MAX_FRAGMENT_SIZE_MM = 1000.0


def generate_breakup_fragments(
    parent_size_mm: float,
    collision_energy_joules: float,
    num_fragments: int = None,
) -> List[Dict]:
    """
    Generate debris fragments from a collision breakup.
    Uses power-law distribution: N(>L) = 0.1 × M^0.75 × L^-1.6
    
    Args:
        parent_size_mm: Size of parent object (mm)
        collision_energy_joules: Collision energy (J)
        num_fragments: Number of fragments to generate (auto if None)
    
    Returns:
        List of fragment dicts: {diameter_mm, mass_kg (estimated)}
    """
    # Estimate number of fragments from collision energy
    # Simplified: more energy = more fragments
    if num_fragments is None:
        # Rough estimate: E > 40 kJ typically causes catastrophic breakup
        if collision_energy_joules > 40000:
            num_fragments = int(100 + collision_energy_joules / 1000)
        else:
            num_fragments = int(10 + collision_energy_joules / 5000)
        num_fragments = min(max(num_fragments, 10), 10000)
    
    # Generate fragment sizes using power-law distribution
    # Power-law: P(L) ∝ L^-1.6
    fragments = []
    
    # Use inverse transform sampling for power-law
    for _ in range(num_fragments):
        # Random uniform [0,1]
        u = np.random.uniform(0, 1)
        # Inverse CDF of power-law: L = L_min * (1 - u)^(-1/(alpha-1))
        # For alpha = -1.6, we use L_max * u^(1/(1.6))
        size_mm = MIN_FRAGMENT_SIZE_MM + (
            (MAX_FRAGMENT_SIZE_MM - MIN_FRAGMENT_SIZE_MM) * (u ** (1 / 1.6))
        )
        size_mm = np.clip(size_mm, MIN_FRAGMENT_SIZE_MM, parent_size_mm)
        
        # Estimate mass (assuming spherical, density ~2700 kg/m³ for aluminum)
        density_kg_m3 = 2700
        radius_m = (size_mm / 1000) / 2
        mass_kg = (4/3) * np.pi * (radius_m ** 3) * density_kg_m3
        
        fragments.append({
            "diameter_mm": float(size_mm),
            "mass_kg": float(mass_kg),
        })
    
    return fragments


def simulate_collision_breakup(
    satellite_area_m2: float,
    debris_diameter_mm: float,
    relative_velocity_km_s: float,
) -> Dict:
    """
    Simulate a collision and generate breakup fragments.
    
    Returns:
        Dict with collision details and fragment list
    """
    # Estimate debris mass
    density_kg_m3 = 2700
    radius_m = (debris_diameter_mm / 1000) / 2
    debris_mass_kg = (4/3) * np.pi * (radius_m ** 3) * density_kg_m3
    
    # Compute collision energy
    v_ms = relative_velocity_km_s * 1000
    collision_energy_joules = 0.5 * debris_mass_kg * (v_ms ** 2)
    
    # Generate fragments
    fragments = generate_breakup_fragments(
        debris_diameter_mm,
        collision_energy_joules,
    )
    
    return {
        "collision_energy_joules": float(collision_energy_joules),
        "debris_mass_kg": float(debris_mass_kg),
        "relative_velocity_km_s": float(relative_velocity_km_s),
        "num_fragments": len(fragments),
        "fragments": fragments,
    }
