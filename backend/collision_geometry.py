"""
Cross-sectional collision geometry.
Accounts for impact angle, effective collision area, and collision probability.
"""

import numpy as np
from typing import Tuple

def effective_collision_area(
    cross_sectional_area_m2: float,
    impact_angle_deg: float,
) -> float:
    """
    Compute effective collision area based on impact angle.
    
    For perpendicular impact (90°): A_eff = A (full area)
    For oblique impact: A_eff = A × sin(angle)
    
    Args:
        cross_sectional_area_m2: Projected cross-sectional area (m²)
        impact_angle_deg: Impact angle (0° = head-on, 90° = perpendicular)
    
    Returns:
        Effective collision area (m²)
    """
    angle_rad = np.radians(impact_angle_deg)
    # For perpendicular: sin(90°) = 1, full area
    # For head-on/tail-on: sin(0°) = 0, minimal area
    # For oblique: sin(angle) gives projected area
    effective = cross_sectional_area_m2 * np.sin(angle_rad)
    return float(max(effective, cross_sectional_area_m2 * 0.1))  # Minimum 10%


def collision_probability_with_geometry(
    base_probability: float,
    cross_sectional_area_m2: float,
    impact_angle_deg: float = 90.0,
) -> float:
    """
    Adjust collision probability based on collision geometry.
    
    P_geom = P_base × (A_eff / A_ref)
    
    Args:
        base_probability: Base collision probability
        cross_sectional_area_m2: Cross-sectional area (m²)
        impact_angle_deg: Impact angle (degrees)
    
    Returns:
        Geometry-adjusted collision probability
    """
    A_eff = effective_collision_area(cross_sectional_area_m2, impact_angle_deg)
    # Normalize by reference area (1 m²) or use relative scaling
    geometry_factor = A_eff / max(cross_sectional_area_m2, 0.01)
    adjusted_prob = base_probability * geometry_factor
    return float(np.clip(adjusted_prob, 0, 1))


def compute_impact_angle_distribution() -> dict:
    """
    Return typical impact angle distribution for LEO debris.
    Most impacts are near-perpendicular (90°), with some oblique angles.
    
    Returns:
        Dict mapping angle ranges to probability weights
    """
    return {
        "head_on": {"range": (0, 30), "weight": 0.1},  # 0-30°
        "oblique": {"range": (30, 60), "weight": 0.2},  # 30-60°
        "perpendicular": {"range": (60, 120), "weight": 0.6},  # 60-120°
        "tail_on": {"range": (120, 180), "weight": 0.1},  # 120-180°
    }
