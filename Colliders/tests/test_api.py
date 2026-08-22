"""
Integration tests for Flask API endpoints in api.py
"""
import pytest
import json


def test_health_endpoint(client):
    """Test /health endpoint returns 200 OK and expected JSON structure."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert 'status' in data
    assert data['status'] in ('healthy', 'degraded')
    assert data.get('service') == 'COLLIDERS API'
    assert 'services' in data
    assert 'features' in data


def test_list_satellites_endpoint(client):
    """Test /api/satellites returns 200 OK and valid satellite list/dict."""
    response = client.get('/api/satellites')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert 'satellites' in data
    assert 'count' in data
    assert isinstance(data['satellites'], dict)
    assert isinstance(data['count'], int)
    for norad_id, sat in data['satellites'].items():
        assert 'name' in sat
        assert 'norad_id' in sat


def test_simulate_maneuver_endpoint(client):
    """Test /api/maneuver/simulate computes delta-v and fuel consumption."""
    payload = {
        'satellite_id': '25544',
        'delta_v_ms': 1.5,
        'direction': 'RETROGRADE',
        'satellite_mass': 500.0,
        'specific_impulse': 300.0
    }
    response = client.post('/api/maneuver/simulate', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('status') == 'success'
    assert data.get('delta_v_ms') == 1.5
    assert data.get('direction') == 'RETROGRADE'
    assert 'fuel_consumption_kg' in data
    assert data['fuel_consumption_kg'] > 0
    assert 'estimated_clearance_km' in data


def test_calculate_avoidance_maneuver_endpoint(client):
    """Test /api/maneuver/calculate handles requests with fallback."""
    payload = {
        'satellite_id': '25544',
        'debris_id': '43013',
        'max_dv': 5.0,
        'lead_time_minutes': 60,
        'target_clearance_km': 5.0
    }
    response = client.post('/api/maneuver/calculate', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('status') == 'success'
    assert 'maneuver' in data
    maneuver = data['maneuver']
    assert 'direction' in maneuver
    assert 'delta_v_ms' in maneuver
    assert 'fuel_consumption_kg' in maneuver
