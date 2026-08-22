"""
Unit tests for Ion Beam Shepherd (IBS) Deorbit Simulation
"""

import pytest
from probability.ibs_deorbit import IBSDeorbitSimulator


def test_ibs_deorbit_simulator_default_decay():
    """Test that the default IBS simulator decays monotonically to the 100 km threshold."""
    simulator = IBSDeorbitSimulator(
        debris_mass_kg=500.0,
        initial_altitude_km=800.0,
        initial_speed_kms=7.35,
        ion_beam_force_mN=20.0,
        ion_mass_flow_rate_mg_s=1.00,
        ion_exhaust_velocity_kms=20.0,
        shepherd_mass_kg=1500.0,
        drag_area_m2=2.0,
        drag_coefficient_cd=2.2,
    )

    result = simulator.simulate(target_steps=100)

    assert result["status"] == "success"
    assert "time_series" in result
    assert len(result["time_series"]) > 0

    series = result["time_series"]
    assert series[0]["altitude_km"] == 800.0
    assert series[-1]["altitude_km"] <= 100.0

    # Assert monotonic altitude decrease
    for i in range(1, len(series)):
        assert series[i]["altitude_km"] <= series[i - 1]["altitude_km"]

    # Verify summary
    summary = result["ibs_summary"]
    assert summary["reentry_achieved"] is True
    assert summary["acceleration_on_debris_um_s2"] == 40.0
    assert summary["estimated_deorbit_time_days"] > 0


def test_ibs_atmospheric_density_profile():
    """Verify atmospheric density behaves exponentially with altitude."""
    sim = IBSDeorbitSimulator()
    rho_0 = sim.atmospheric_density(0.0)
    rho_8_5 = sim.atmospheric_density(8.5)
    rho_100 = sim.atmospheric_density(100.0)

    assert pytest.approx(rho_0, rel=1e-3) == 1.225
    # At 1 scale height (8.5 km), density should be rho_0 / e
    assert pytest.approx(rho_8_5, rel=1e-2) == 1.225 / 2.7182818
    assert rho_100 < 1e-4
    assert rho_100 > 0.0


def test_ibs_api_endpoint(client):
    """Test the /api/ibs-deorbit-simulation endpoint returns valid JSON."""
    response = client.post(
        "/api/ibs-deorbit-simulation",
        json={
            "debris_mass_kg": 500.0,
            "initial_altitude_km": 800.0,
            "ion_beam_force_mN": 20.0,
            "target_steps": 50,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "ibs_summary" in data
    assert "time_series" in data
    assert len(data["time_series"]) > 0
    assert data["time_series"][0]["altitude_km"] == 800.0
    assert data["time_series"][-1]["altitude_km"] <= 100.0
