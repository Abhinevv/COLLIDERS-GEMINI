"""
Unit tests for Ion Beam Shepherd (IBS) Deorbit Simulation
"""

import pytest
import math
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


def test_from_debris_factory_small_rcs():
    """Test from_debris factory with a small RCS fragment."""
    debris = {
        "norad_id": "44120",
        "name": "PSLV C-45 DEB",
        "type": "Fragment",
        "rcs_size": "SMALL",
        "apogee_km": 650.0,
        "perigee_km": 550.0,
        "inclination_deg": 97.8,
    }

    sim = IBSDeorbitSimulator.from_debris(debris)

    # Initial altitude should be midpoint of apogee and perigee: (650+550)/2 = 600 km
    assert sim.initial_altitude_km == 600.0
    # Mass for SMALL should be 15.0 kg
    assert sim.debris_mass_kg == 15.0
    assert sim.drag_area_m2 == 0.2
    assert sim.inclination_deg == 97.8
    assert sim.debris_name == "PSLV C-45 DEB"

    # Initial speed should match vis-viva at 600 km: sqrt(398600.4418 / (6371 + 600)) ≈ 7.56 km/s
    expected_speed = math.sqrt(398600.4418 / (6371.0 + 600.0))
    assert pytest.approx(sim.initial_speed_kms, rel=1e-3) == expected_speed


def test_from_debris_factory_large_rcs():
    """Test from_debris factory with a large payload object."""
    debris = {
        "norad_id": "27386",
        "name": "ENVISAT DERELICT",
        "type": "PAYLOAD",
        "rcs_size": "LARGE",
        "apogee_km": 770.0,
        "perigee_km": 765.0,
        "inclination_deg": 98.5,
    }

    sim = IBSDeorbitSimulator.from_debris(debris)
    assert pytest.approx(sim.initial_altitude_km, rel=1e-3) == 767.5
    assert sim.debris_mass_kg == 750.0
    assert sim.drag_area_m2 == 2.5
    assert sim.inclination_deg == 98.5


def test_from_debris_factory_rocket_body():
    """Test from_debris factory with a spent rocket body."""
    debris = {
        "norad_id": "44858",
        "name": "PSLV R/B Stage-4",
        "type": "ROCKET BODY",
        "rcs_size": "LARGE",
        "apogee_km": 500.0,
        "perigee_km": 480.0,
        "inclination_deg": 97.5,
    }

    sim = IBSDeorbitSimulator.from_debris(debris)
    assert sim.debris_mass_kg == 1200.0
    assert sim.drag_area_m2 == 3.5
    assert sim.initial_altitude_km == 490.0


def test_ibs_api_endpoint(client):
    """Test the /api/ibs-deorbit-simulation endpoint returns valid JSON with default parameters."""
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


def test_ibs_api_with_norad_id(client):
    """Test the /api/ibs-deorbit-simulation endpoint with a real catalog NORAD ID."""
    response = client.post(
        "/api/ibs-deorbit-simulation",
        json={
            "norad_id": "44120",
            "target_steps": 50,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    params = data["mission_parameters"]
    assert params["norad_id"] == "44120"
    assert params["debris_mass_kg"] == 15.0  # SMALL RCS
    assert params["mass_estimated"] is True
    assert "time_series" in data


def test_ibs_api_norad_not_found(client):
    """Test the /api/ibs-deorbit-simulation endpoint returns 404 for invalid NORAD ID."""
    response = client.post(
        "/api/ibs-deorbit-simulation",
        json={
            "norad_id": "99999999",
            "target_steps": 50,
        },
    )

    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
