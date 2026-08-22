"""
Unit tests for collision avoidance maneuver planning and Tsiolkovsky rocket equation.
"""
import pytest
import math
from datetime import datetime, timezone

from optimization.avoidance import AvoidanceManeuver


def test_tsiolkovsky_fuel_consumption():
    """
    Test propellant mass calculation: delta_m = m0 * (1 - exp(-delta_v / (Isp * g0)))
    """
    m0 = 500.0   # kg
    isp = 300.0  # s
    g0 = 9.80665 # m/s^2
    dv = 10.0    # m/s

    optimizer = AvoidanceManeuver(None, max_dv=20.0, satellite_mass_kg=m0, specific_impulse_sec=isp)
    fuel = optimizer.calculate_fuel_consumption(dv)

    expected_fuel = m0 * (1.0 - math.exp(-dv / (isp * g0)))
    assert math.isclose(fuel, expected_fuel, rel_tol=1e-5)


def test_avoidance_maneuver_fallback():
    """
    Test avoidance maneuver generation fallback when ephemeris is unavailable.
    """
    optimizer = AvoidanceManeuver(None, max_dv=10.0, satellite_mass_kg=500.0)
    burn_time = datetime.now(timezone.utc)

    plan = optimizer.optimize_maneuver(burn_time, None, dv_range=(0.1, 3.0))

    assert plan is not None
    assert 'direction' in plan
    assert 'delta_v_ms' in plan
    assert 'fuel_consumption_kg' in plan
    assert plan['fuel_consumption_kg'] > 0
    assert plan['status'] in ('OPTIMAL', 'SUBOPTIMAL_MAX_CLEARANCE')


def test_avoidance_maneuver_string_epoch():
    """
    Test avoidance maneuver handles ISO formatted string burn_time.
    """
    optimizer = AvoidanceManeuver(None, max_dv=10.0, satellite_mass_kg=500.0)
    burn_time_str = "2026-08-21T12:00:00Z"

    plan = optimizer.optimize_maneuver(burn_time_str, None, dv_range=(0.1, 3.0))
    assert plan is not None
    assert 'delta_v_ms' in plan
