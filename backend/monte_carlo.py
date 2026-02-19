"""
Monte Carlo simulation for collision probability validation.
10,000 trials: for each trial, r in [0,1]; if r < Q count collision.
"""

import numpy as np
from typing import Tuple

TRIALS = 10_000


def run_monte_carlo(Q: float, trials: int = TRIALS) -> Tuple[float, float, int]:
    """
    Run Monte Carlo simulation.
    Returns (MonteCarloProbability, PoissonProbability, Trials).
    """
    Q = float(np.clip(Q, 0, 1))
    rng = np.random.default_rng()
    r_values = rng.uniform(0, 1, size=trials)
    collisions = int(np.sum(r_values < Q))
    P_MC = collisions / trials
    return float(P_MC), float(Q), trials
