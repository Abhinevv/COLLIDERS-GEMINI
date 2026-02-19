"""
Debris Flux Model based on NASA SSP30425 / M. Torky et al. research.
Implements the cumulative debris flux Fr(d, h, i, t, S) = λ × μ
with FC = 6 × Fr
"""

import numpy as np
from typing import Tuple

# Constants from the model
Q = 0.02
Q_TILDE = 0.04
P = 0.05

# Inclination factor θ(i) - discrete lookup table (degrees -> factor)
# Based on typical LEO debris distribution; higher flux at SSO (98°) and polar
INCLINATION_TABLE = [
    (0, 0.5), (10, 0.55), (28, 0.75), (51.6, 1.0), (90, 1.25),
    (98, 1.5), (110, 1.35), (180, 1.2),
]


def _theta_interpolate(deg: float) -> float:
    """Interpolate inclination factor from discrete lookup table."""
    deg = float(np.clip(deg, 0, 180))
    incls = np.array([x[0] for x in INCLINATION_TABLE])
    factors = np.array([x[1] for x in INCLINATION_TABLE])
    idx = np.searchsorted(incls, deg, side="right")
    if idx == 0:
        return float(factors[0])
    if idx >= len(incls):
        return float(factors[-1])
    # Linear interpolation
    t = (deg - incls[idx - 1]) / (incls[idx] - incls[idx - 1])
    return float(factors[idx - 1] + t * (factors[idx] - factors[idx - 1]))


def H(d: float) -> float:
    """H(d) = [10^exp(-(log10(d) - 0.78)² / 0.6372)]^(1/2)"""
    d = float(np.clip(d, 1e-10, 1e10))
    log_d = np.log10(d)
    exp_arg = -((log_d - 0.78) ** 2) / 0.6372
    inner = 10 ** np.exp(exp_arg)
    return float(np.sqrt(inner))


def phi(h: float, S: float) -> float:
    """φ(h,S) = ψ1/(ψ1+1), ψ1 = 10^(h/200 - S/140 - 1.5)"""
    h = float(np.clip(h, 0, 2000))
    psi1 = 10 ** (h / 200 - S / 140 - 1.5)
    return float(psi1 / (psi1 + 1))


def F1(d: float) -> float:
    """F1(d) = 1.22e-5 * d^(-2.5)"""
    d = float(np.clip(d, 1e-10, 1e10))
    return float(1.22e-5 * (d ** (-2.5)))


def F2(d: float) -> float:
    """F2(d) = 8.1e10 * (d + 700)^(-6)"""
    d = float(np.clip(d, 0, 1e10))
    return float(8.1e10 * ((d + 700) ** (-6)))


def g1(t: float) -> float:
    """g1(t): if t<2011: (1+q)^(t-1988); else (1+q)^23 * (1+q̃)^(t-2011)"""
    t = int(round(t))
    if t < 2011:
        return float((1 + Q) ** (t - 1988))
    return float((1 + Q) ** 23 * (1 + Q_TILDE) ** (t - 2011))


def g2(t: float) -> float:
    """g2(t) = 1 + p * (t - 1988)"""
    t = int(round(t))
    return float(1 + P * (t - 1988))


def theta(i: float) -> float:
    """Inclination factor θ(i) from discrete lookup table."""
    return _theta_interpolate(float(i))


def compute_lambda(d: float, h: float, i: float, S: float) -> float:
    """λ = H(d) × φ(h,S) × θ(i)"""
    return H(d) * phi(h, S) * theta(i)


def compute_mu(d: float, t: float) -> float:
    """μ = F1(d)×g1(t) + F2(d)×g2(t)"""
    return F1(d) * g1(t) + F2(d) * g2(t)


def compute_flux(
    d: float, h: float, i: float, t: float, S: float
) -> Tuple[float, float, float]:
    """
    Compute debris flux. Returns (Fr, FC, components dict).
    Fr = λ × μ, FC = 6 × Fr
    """
    lam = compute_lambda(d, h, i, S)
    mu = compute_mu(d, t)
    Fr = lam * mu
    FC = 6.0 * Fr
    return float(Fr), float(FC), {
        "H": H(d),
        "phi": phi(h, S),
        "theta": theta(i),
        "F1": F1(d),
        "F2": F2(d),
        "g1": g1(t),
        "g2": g2(t),
        "lambda": lam,
        "mu": mu,
    }
