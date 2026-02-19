"""
Petri Net model for debris flux computation.
Transitions t1–t5 map to:
t1 → H(d), F1(d), F2(d)
t2 → φ(h,S)
t3 → g1(t), g2(t)
t4 → θ(i)
t5 → FC
"""

from typing import Dict, Any
from debris_flux import (
    H,
    phi,
    F1,
    F2,
    g1,
    g2,
    theta,
    compute_flux,
)


def run_petri_net(d: float, h: float, i: float, t: float, S: float) -> Dict[str, Any]:
    """
    Execute Petri Net transitions t1–t5 in sequence.
    Returns dict with transition outputs for animation display.
    """
    # t1: Compute H(d), F1(d), F2(d)
    t1_result = {
        "H": H(d),
        "F1": F1(d),
        "F2": F2(d),
    }

    # t2: Compute φ(h,S)
    t2_result = {
        "phi": phi(h, S),
    }

    # t3: Compute g1(t), g2(t)
    t3_result = {
        "g1": g1(t),
        "g2": g2(t),
    }

    # t4: Compute θ(i)
    t4_result = {
        "theta": theta(i),
    }

    # t5: Compute FC (requires all previous)
    _, FC, components = compute_flux(d, h, i, t, S)
    t5_result = {
        "FC": FC,
        "Fr": components["lambda"] * components["mu"],
    }

    return {
        "t1": t1_result,
        "t2": t2_result,
        "t3": t3_result,
        "t4": t4_result,
        "t5": t5_result,
        "FC": FC,
        "components": components,
    }
