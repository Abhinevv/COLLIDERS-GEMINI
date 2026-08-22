"""
Unit tests for 3D Orbit Visualization and Animation Engine
"""

import pytest
import os
import tempfile
import numpy as np
from visualization.plot_orbits import OrbitVisualizer


def generate_mock_trajectory(r_km=7000.0, num_steps=60, inclination_deg=51.6, offset_phase=0.0):
    """Generate circular test trajectory"""
    traj = []
    inc_rad = np.radians(inclination_deg)
    for i in range(num_steps):
        theta = (2.0 * np.pi * i / num_steps) + offset_phase
        x = r_km * np.cos(theta)
        y = r_km * np.sin(theta) * np.cos(inc_rad)
        z = r_km * np.sin(theta) * np.sin(inc_rad)
        traj.append({
            'time': f'2026-08-22T12:{i:02d}:00Z',
            'position': np.array([x, y, z]),
            'velocity': np.array([-7.5 * np.sin(theta), 7.5 * np.cos(theta), 0.0])
        })
    return traj


def test_earth_sphere_generation():
    """Verify high-resolution Earth sphere surface and procedural continent map."""
    visualizer = OrbitVisualizer()
    earth = visualizer.create_earth_sphere(resolution=36)

    assert earth is not None
    assert earth.x.shape == (72, 36)
    assert earth.y.shape == (72, 36)
    assert earth.z.shape == (72, 36)
    assert earth.surfacecolor.shape == (72, 36)
    # Check bounds match earth radius
    assert np.isclose(np.max(np.abs(earth.x)), 6371.0, rtol=1e-2)


def test_starfield_generation():
    """Verify starfield layer."""
    visualizer = OrbitVisualizer()
    stars = visualizer.create_starfield(count=100)

    assert stars is not None
    assert len(stars.x) == 100
    assert np.all(np.linalg.norm(np.column_stack((stars.x, stars.y, stars.z)), axis=1) > 20000.0)


def test_animated_collision_scenario():
    """Verify animated figure contains Plotly frames, comet trails, play/pause buttons, and sliders."""
    traj1 = generate_mock_trajectory(r_km=6800.0, num_steps=60, inclination_deg=51.6, offset_phase=0.0)
    traj2 = generate_mock_trajectory(r_km=6800.0, num_steps=60, inclination_deg=97.5, offset_phase=0.1)

    visualizer = OrbitVisualizer()
    fig = visualizer.plot_collision_scenario(
        traj1, traj2,
        name1="ISS (ZARYA)",
        name2="COSMOS DEB",
        max_animation_frames=50
    )

    assert fig is not None
    # Check that frames were generated
    assert hasattr(fig, 'frames')
    assert len(fig.frames) == 50

    # Verify frame 0 has traces for trails and markers
    f0 = fig.frames[0]
    assert len(f0.data) == 5  # trail1, marker1, trail2, marker2, dist_line
    assert list(f0.traces) == [10, 11, 12, 13, 14]

    # Verify updatemenus has Play & Pause
    layout = fig.layout
    assert len(layout.updatemenus) > 0
    buttons = layout.updatemenus[0].buttons
    assert any(b.label == '▶ Play' for b in buttons)
    assert any(b.label == '⏸ Pause' for b in buttons)

    # Verify sliders are present
    assert len(layout.sliders) > 0
    assert len(layout.sliders[0].steps) == 50


def test_dashboard_html_export():
    """Verify export to HTML creates interactive dashboard file with addFrames."""
    traj1 = generate_mock_trajectory(r_km=6800.0, num_steps=30)
    traj2 = generate_mock_trajectory(r_km=6800.0, num_steps=30, offset_phase=0.05)

    visualizer = OrbitVisualizer()
    visualizer.plot_collision_scenario(traj1, traj2, name1="SatA", name2="SatB", max_animation_frames=20)

    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tf:
        tmp_path = tf.name

    try:
        analysis_result = {
            'safe': False,
            'closest_approach': {'distance': 3.25, 'relative_velocity': 14.2, 'time': '2026-08-22T12:15:00Z'},
            'risk_assessment': {'risk_level': 'HIGH', 'collision_probability': 0.045}
        }
        sat_info1 = {'name': 'ISS'}
        sat_info2 = {'name': 'DEBRIS #123'}

        visualizer.save_html(tmp_path, analysis_result, sat_info1, sat_info2)

        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 10000

        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'COLLIDERS' in content
        assert 'Plotly.addFrames' in content
        assert 'HIGH' in content
        assert '3.25 km' in content

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_api_visualize_route(client):
    """Test /api/visualize endpoint generates an animated HTML file."""
    response = client.post(
        '/api/visualize',
        json={
            'satellite1': '25544',
            'satellite2': '44120',
            'duration_minutes': 30,
            'step_seconds': 60
        }
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'visualization_url' in data
    filename = data['filename']
    assert filename.endswith('.html')
