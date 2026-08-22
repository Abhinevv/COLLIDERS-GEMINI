"""
Unit tests for physics-based orbital propagation, PINN surrogate fallback,
and collision probability estimation.
"""
import pytest
import numpy as np
import math

from probability.pinn_surrogate import (
    PINNPropagatorEngine,
    propagate_kepler_universal_single,
    get_two_body_j2_acceleration_numpy,
    EARTH_MU,
    EARTH_RADIUS
)
from probability.pinn_monte_carlo import PINNMonteCarloAssessment
from probability.collision_probability import CollisionProbability
from probability.improved_collision_probability import ImprovedCollisionProbability


def test_pinn_engine_safe_physics_fallback():
    """
    Verify PINNPropagatorEngine defaults to the validated physics-based
    Taylor-J2 propagator (has_torch=False, model=None) when no trained
    checkpoint is provided, ensuring untrained weights are never evaluated.
    """
    engine = PINNPropagatorEngine()
    assert engine.has_torch is False
    assert engine.model is None


def test_pinn_engine_nonexistent_checkpoint_handling():
    """
    Verify passing a nonexistent checkpoint safely falls back to physics-based Taylor-J2.
    """
    engine = PINNPropagatorEngine(checkpoint_path="nonexistent_checkpoint.pth")
    assert engine.has_torch is False
    assert engine.model is None


def test_kepler_universal_variable_propagation():
    """
    Test exact Kepler universal variable propagation for circular LEO orbit.
    """
    # Circular LEO orbit at r = 7000 km
    r0 = np.array([7000.0, 0.0, 0.0])
    v_circ = math.sqrt(EARTH_MU / 7000.0)
    v0 = np.array([0.0, v_circ, 0.0])

    period = 2.0 * math.pi * math.sqrt((7000.0 ** 3) / EARTH_MU)
    r_half, v_half = propagate_kepler_universal_single(r0, v0, dt=period / 2.0)

    # After half orbit, position should be approximately [-7000, 0, 0]
    np.testing.assert_allclose(r_half[0], -7000.0, atol=1e-3)
    np.testing.assert_allclose(r_half[1], 0.0, atol=1e-3)


def test_batched_perturbation_propagation_fallback():
    """
    Verify batched perturbation propagation works via physics fallback
    and returns correct array dimensions with finite, physical values.
    """
    engine = PINNPropagatorEngine()
    nominal_r0 = np.array([7000.0, 0.0, 0.0])
    nominal_v0 = np.array([0.0, 7.546, 0.0])

    num_samples = 500
    delta_r = np.random.normal(0, 0.5, (num_samples, 3))
    delta_v = np.random.normal(0, 0.001, (num_samples, 3))
    time_offsets = np.linspace(-30.0, 30.0, 11)

    positions = engine.propagate_batched_perturbations(
        nominal_r0, nominal_v0, delta_r, delta_v, time_offsets
    )

    assert positions.shape == (num_samples, 11, 3)
    assert not np.isnan(positions).any()
    assert not np.isinf(positions).any()
    # Average radius should remain near LEO (~7000 km)
    radii = np.linalg.norm(positions, axis=-1)
    assert np.all((radii >= 6378.0) & (radii <= 8000.0))


def test_collision_probability_monte_carlo():
    """
    Test standard CollisionProbability calculation and risk assessment.
    """
    calc = CollisionProbability(position_uncertainty=1.0, velocity_uncertainty=0.001)

    # Close conjunction: separation 0.01 km (10m) with 20m combined radius
    pos1 = [7000.0, 0.0, 0.0]
    pos2 = [7000.005, 0.0, 0.0]
    vel1 = [0.0, 7.5, 0.0]
    vel2 = [0.0, -7.5, 0.0]

    result = calc.monte_carlo_simulation(
        pos1, pos2, vel1, vel2, num_samples=1000, combined_radius=0.02
    )

    assert 'probability' in result
    assert 0.0 <= result['probability'] <= 1.0
    assert result['samples'] == 1000
    assert 'risk_level' in result


def test_improved_collision_probability():
    """
    Test ImprovedCollisionProbability with 6x6 covariance sampling.
    """
    calc = ImprovedCollisionProbability()
    pos1 = [7000.0, 0.0, 0.0]
    pos2 = [7000.01, 0.0, 0.0]
    vel1 = [0.0, 7.5, 0.0]
    vel2 = [0.0, 7.5, 0.0]

    res = calc.monte_carlo_simulation(pos1, pos2, vel1, vel2, num_samples=1000, combined_radius=0.02)
    assert 0.0 <= res['probability'] <= 1.0
    assert 'confidence_interval_95' in res


def test_pinn_monte_carlo_assessment():
    """
    Test PINNMonteCarloAssessment end-to-end evaluation.
    """
    assessor = PINNMonteCarloAssessment()
    sat_pos = np.array([7000.0, 0.0, 0.0])
    sat_vel = np.array([0.0, 7.546, 0.0])
    deb_pos = np.array([7000.05, 0.0, 0.0])
    deb_vel = np.array([0.0, -7.546, 0.0])

    assessment = assessor.assess_collision_pinn(
        sat_pos_tca=sat_pos,
        sat_vel_tca=sat_vel,
        deb_pos_tca=deb_pos,
        deb_vel_tca=deb_vel,
        num_samples=1000,
        combined_radius_km=0.02
    )

    assert 'probability' in assessment
    assert 0.0 <= assessment['probability'] <= 1.0
    assert 'threat_score' in assessment
    assert 'risk_level' in assessment
    assert assessment['method'] == 'Taylor_J2_Monte_Carlo'
    assert assessment['pinn_accelerated'] is False
