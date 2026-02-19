"""
Poisson distribution for collision probability.
P0 = e^(-N_total)
Q = 1 - e^(-N_total)
Pn = (N_total^n * e^(-N_total)) / n!
"""

import numpy as np
from typing import Tuple
from math import factorial


def poisson_probability_zero(N_total: float) -> float:
    """P0 = probability of zero collisions = e^(-N_total)"""
    N = float(np.clip(N_total, 0, 1e10))
    return float(np.exp(-N))


def collision_probability(N_total: float) -> float:
    """Q = 1 - P0 = 1 - e^(-N_total)"""
    P0 = poisson_probability_zero(N_total)
    return float(np.clip(1 - P0, 0, 1))


def poisson_probability_n(N_total: float, n: int) -> float:
    """Pn = (N_total^n * e^(-N_total)) / n!"""
    N = float(np.clip(N_total, 0, 1e10))
    n = int(max(0, n))
    if n > 100:
        return 0.0  # Avoid overflow
    return float((N**n) * np.exp(-N) / factorial(n))


def compute_poisson_results(N_total: float) -> dict:
    """Return P0, Q, and collision probability (Q) for API."""
    P0 = poisson_probability_zero(N_total)
    Q = collision_probability(N_total)
    return {
        "P0": float(P0),
        "Q": float(Q),
        "N_total": float(N_total),
    }
