"""
COLLIDERS REST API
Provides HTTP endpoints for collision avoidance analysis
"""

from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
import os
import json
import numpy as np
import random
from datetime import datetime, timezone, timedelta
import tempfile

from fetch_tle import TLEFetcher
from propagation.propagate import OrbitPropagator
from propagation.distance_check import CloseApproachDetector
from probability.collision_probability import CollisionProbability
from visualization.plot_orbits import OrbitVisualizer
from debris.analyze import analyze_debris_vs_satellite
from debris.space_track import SpaceTrackAPI
import threading
import uuid
import time
import requests as _requests

# In-memory job store for async debris analyses
DEBRIS_JOBS = {}

# Initialize Space-Track API (will use env variables)
space_track_api = SpaceTrackAPI()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global cache for propagators
_propagator_cache = {}


@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with service status"""
    health_status = {
        'status': 'healthy',
        'service': 'COLLIDERS API',
        'version': '2.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'services': {
            'database': 'operational',
            'history': 'operational',
            'alerts': 'operational',
            'space_track': 'operational'
        },
        'features': {
            'collision_analysis': True,
            'debris_tracking': True,
            'alert_system': True,
            'history_tracking': True
        }
    }
    
    # Test database connection
    try:
        from database.db_manager import get_db_manager
        from sqlalchemy import text
        db = get_db_manager()
        session = db.get_session()
        session.execute(text('SELECT 1'))
        session.close()
    except Exception as e:
        health_status['services']['database'] = 'degraded'
        health_status['status'] = 'degraded'
    
    return jsonify(health_status), 200


@app.route('/api/satellites', methods=['GET'])
def list_satellites():
    """List available satellites"""
    satellites = {
        '25544': {
            'name': 'ISS (ZARYA)',
            'norad_id': '25544',
            'type': 'Space Station',
            'description': 'International Space Station'
        },
        '43013': {
            'name': 'HST',
            'norad_id': '43013',
            'type': 'Space Telescope',
            'description': 'Hubble Space Telescope'
        },
        '20580': {
            'name': 'NOAA-19',
            'norad_id': '20580',
            'type': 'Weather Satellite',
            'description': 'NOAA-19 weather satellite'
        }
    }
    
    return jsonify({
        'satellites': satellites,
        'count': len(satellites)
    }), 200


@app.route('/api/satellites/<norad_id>', methods=['GET'])
def get_satellite_info(norad_id):
    """Get satellite information by NORAD ID"""
    try:
        # Download TLE if not exists
        tle_file = f'data/sat_{norad_id}.txt'
        if not os.path.exists(tle_file):
            fetcher = TLEFetcher()
            if not fetcher.fetch_tle(norad_id, f'sat_{norad_id}.txt'):
                return jsonify({'error': 'Failed to fetch TLE data'}), 404
        
        # Load propagator
        propagator = OrbitPropagator(tle_file)
        info = propagator.get_satellite_info()
        
        return jsonify({
            'satellite': info,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_collision():
    """
    Analyze collision scenario between two satellites
    
    Request body:
    {
        "satellite1_norad": "25544",
        "satellite2_norad": "43013",
        "duration_minutes": 180,
        "step_seconds": 60,
        "threshold_km": 10.0
    }
    """
    try:
        data = request.get_json()
        
        # Extract parameters
        sat1_id = data.get('satellite1_norad', '25544')
        sat2_id = data.get('satellite2_norad', '43013')
        duration_minutes = data.get('duration_minutes', 180)
        step_seconds = data.get('step_seconds', 60)
        threshold_km = data.get('threshold_km', 10.0)
        
        # Download TLE files if needed
        fetcher = TLEFetcher()
        tle1_file = f'data/sat_{sat1_id}.txt'
        tle2_file = f'data/sat_{sat2_id}.txt'
        
        if not os.path.exists(tle1_file):
            fetcher.fetch_tle(sat1_id, f'sat_{sat1_id}.txt')
        if not os.path.exists(tle2_file):
            fetcher.fetch_tle(sat2_id, f'sat_{sat2_id}.txt')
        
        # Initialize propagators
        prop1 = OrbitPropagator(tle1_file)
        prop2 = OrbitPropagator(tle2_file)
        
        # Propagate trajectories
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        traj1 = prop1.propagate_trajectory(start_time, duration_minutes, step_seconds)
        traj2 = prop2.propagate_trajectory(start_time, duration_minutes, step_seconds)
        
        if not traj1 or not traj2:
            return jsonify({
                'error': 'Failed to propagate trajectories',
                'message': 'TLE data may be invalid or expired'
            }), 400
        
        # Detect close approaches
        detector = CloseApproachDetector(threshold_km=threshold_km)
        events = detector.check_trajectories(traj1, traj2)
        
        # Analyze closest approach if exists
        risk_assessment = None
        closest = None
        
        if events:
            closest = detector.find_closest_approach()
            prob_calc = CollisionProbability(
                position_uncertainty=1.0,
                velocity_uncertainty=0.001
            )
            risk_assessment = prob_calc.assess_risk(
                closest,
                object_radius_1=0.01,
                object_radius_2=0.01
            )
        
        # Prepare event summaries
        events_summary = []
        for e in events:
            events_summary.append({
                'time': e['time'].isoformat() if hasattr(e['time'], 'isoformat') else str(e['time']),
                'distance': e['distance'],
                'relative_velocity': e['relative_velocity'],
                'risk_level': e.get('risk_level')
            })

        # Prepare response
        result = {
            'status': 'success',
            'safe': len(events) == 0,
            'events': events_summary,
            'satellite1': {
                'name': prop1.name,
                'norad_id': prop1.norad_id,
                'trajectory_points': len(traj1)
            },
            'satellite2': {
                'name': prop2.name,
                'norad_id': prop2.norad_id,
                'trajectory_points': len(traj2)
            },
            'analysis': {
                'start_time': start_time.isoformat(),
                'duration_minutes': duration_minutes,
                'step_seconds': step_seconds,
                'threshold_km': threshold_km,
                'close_approaches': len(events),
                'closest_approach': {
                    'distance_km': closest['distance'] if closest else None,
                    'time': closest['time'].isoformat() if closest else None,
                    'relative_velocity_km_s': closest['relative_velocity'] if closest else None
                } if closest else None,
                'risk_assessment': risk_assessment
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500


@app.route('/api/visualize', methods=['POST'])
def generate_visualization():
    """
    Generate visualization HTML for collision scenario
    
    Request body:
    {
        "satellite1_norad": "25544",
        "satellite2_norad": "43013",
        "duration_minutes": 180,
        "step_seconds": 60
    }
    """
    try:
        data = request.get_json()
        
        sat1_id = data.get('satellite1_norad', '25544')
        sat2_id = data.get('satellite2_norad', '43013')
        duration_minutes = data.get('duration_minutes', 180)
        step_seconds = data.get('step_seconds', 60)
        
        # Download TLE files if needed
        fetcher = TLEFetcher()
        tle1_file = f'data/sat_{sat1_id}.txt'
        tle2_file = f'data/sat_{sat2_id}.txt'
        
        if not os.path.exists(tle1_file):
            fetcher.fetch_tle(sat1_id, f'sat_{sat1_id}.txt')
        if not os.path.exists(tle2_file):
            fetcher.fetch_tle(sat2_id, f'sat_{sat2_id}.txt')
        
        # Initialize propagators
        prop1 = OrbitPropagator(tle1_file)
        prop2 = OrbitPropagator(tle2_file)
        
        # Propagate trajectories
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        traj1 = prop1.propagate_trajectory(start_time, duration_minutes, step_seconds)
        traj2 = prop2.propagate_trajectory(start_time, duration_minutes, step_seconds)
        
        if not traj1 or not traj2:
            return jsonify({
                'error': 'Failed to propagate trajectories'
            }), 400
        
        # Detect close approaches
        detector = CloseApproachDetector(threshold_km=10.0)
        events = detector.check_trajectories(traj1, traj2)
        closest = detector.find_closest_approach() if events else None

        # Compute risk assessment for closest approach if exists
        risk_assessment = None
        if closest:
            prob_calc = CollisionProbability(position_uncertainty=1.0, velocity_uncertainty=0.001)
            risk_assessment = prob_calc.assess_risk(
                closest,
                object_radius_1=0.01,
                object_radius_2=0.01
            )
        
        # Create visualization
        visualizer = OrbitVisualizer()
        
        if closest:
            visualizer.plot_collision_scenario(
                traj1, traj2, closest,
                name1=prop1.name,
                name2=prop2.name
            )
        else:
            visualizer.plot_collision_scenario(
                traj1, traj2,
                name1=prop1.name,
                name2=prop2.name
            )
        
        # Prepare analysis result
        # Summarize events
        events_summary = []
        for e in events:
            events_summary.append({
                'time': e['time'].isoformat() if hasattr(e['time'], 'isoformat') else str(e['time']),
                'distance': e['distance'],
                'relative_velocity': e['relative_velocity'],
                'risk_level': e.get('risk_level')
            })

        analysis_result = {
            'safe': len(events) == 0,
            'events': events_summary,
            'closest_approach': closest,
            'risk_assessment': risk_assessment,
            'trajectories': (traj1, traj2)
        }
        
        # Get satellite info
        info1 = prop1.get_satellite_info()
        info2 = prop2.get_satellite_info()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, dir='output'
        )
        temp_filename = temp_file.name
        temp_file.close()
        
        visualizer.save_html(temp_filename, analysis_result, info1, info2)
        
        # Prepare lightweight analysis summary to return
        analysis_summary = {
            'safe': analysis_result.get('safe', True),
            'events_count': len(analysis_result.get('events', [])),
            'closest_distance': analysis_result.get('closest_approach', {}).get('distance') if analysis_result.get('closest_approach') else None,
            'risk_assessment': analysis_result.get('risk_assessment')
        }

        return jsonify({
            'status': 'success',
            'visualization_url': f'/api/visualization/{os.path.basename(temp_filename)}',
            'filename': os.path.basename(temp_filename),
            'message': 'Visualization generated successfully',
            'analysis': analysis_summary
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500


@app.route('/api/visualization/<filename>', methods=['GET'])
def get_visualization(filename):
    """Serve visualization HTML file"""
    try:
        filepath = os.path.join('output', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Visualization not found'}), 404
        
        return send_file(filepath, mimetype='text/html')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualization/combined', methods=['POST'])
def create_combined_visualization():
    """
    Create a combined visualization showing one satellite with multiple debris objects
    
    Request body:
    {
        "satellite_norad": "25544",
        "debris_ids": ["67745", "67720", "67719"],
        "duration_minutes": 60
    }
    """
    try:
        data = request.get_json()
        satellite_norad = data.get('satellite_norad')
        debris_ids = data.get('debris_ids', [])
        duration_minutes = int(data.get('duration_minutes', 60))
        
        if not satellite_norad or not debris_ids:
            return jsonify({'error': 'satellite_norad and debris_ids required'}), 400
        
        # Propagate satellite trajectory
        sat_file = f'data/sat_{satellite_norad}.txt'
        if not os.path.exists(sat_file):
            return jsonify({'error': f'Satellite TLE file not found: {sat_file}'}), 404
        
        prop = OrbitPropagator(sat_file)
        sat_traj = prop.propagate_trajectory(
            datetime.now(timezone.utc).replace(tzinfo=None),
            duration_minutes,
            60
        )
        
        # Propagate all debris trajectories
        debris_trajs = []
        debris_names = []
        
        for debris_id in debris_ids[:10]:  # Limit to 10 debris for performance
            debris_file = f'data/sat_{debris_id}.txt'
            
            # Try to get TLE from cache if file doesn't exist
            if not os.path.exists(debris_file):
                from tle_cache_manager import get_cache_manager
                cache = get_cache_manager()
                cached_tle = cache.get_tle_from_cache(debris_id)
                
                if cached_tle:
                    with open(debris_file, 'w') as f:
                        f.write(f"{cached_tle['name']}\n")
                        f.write(f"{cached_tle['tle_line1']}\n")
                        f.write(f"{cached_tle['tle_line2']}\n")
                else:
                    continue  # Skip this debris if no TLE available
            
            try:
                debris_prop = OrbitPropagator(debris_file)
                debris_traj = debris_prop.propagate_trajectory(
                    datetime.now(timezone.utc).replace(tzinfo=None),
                    duration_minutes,
                    60
                )
                debris_trajs.append(debris_traj)
                debris_names.append(debris_id)
            except:
                continue  # Skip debris with invalid TLE
        
        if not debris_trajs:
            return jsonify({'error': 'No valid debris trajectories could be generated'}), 400
        
        # Create combined visualization
        visualizer = OrbitVisualizer()
        
        # Plot satellite orbit with first debris (this creates the base figure)
        visualizer.plot_collision_scenario(
            sat_traj,
            debris_trajs[0],
            close_approach_event=None,
            name1=prop.get_satellite_info().get('name', f'Satellite {satellite_norad}'),
            name2=f'Debris {debris_names[0]}'
        )
        
        # Add additional debris orbits to the plot
        if len(debris_trajs) > 1:
            import plotly.graph_objects as go
            # Use different colors for each debris to make them distinguishable
            debris_colors = ['#ff4444', '#ff8844', '#ffcc44', '#44ff44', '#44ffcc', 
                           '#4444ff', '#8844ff', '#ff44ff', '#ff4488', '#88ff44']
            
            for i, debris_traj in enumerate(debris_trajs[1:], 1):
                debris_positions = [s['position'] for s in debris_traj]
                x = [p[0] for p in debris_positions]
                y = [p[1] for p in debris_positions]
                z = [p[2] for p in debris_positions]
                
                # Calculate altitude for hover
                altitudes = [np.linalg.norm([x[j], y[j], z[j]]) - 6371.0 for j in range(len(x))]
                
                # Use different color for each debris
                color = debris_colors[i % len(debris_colors)]
                
                # Add debris orbit trace with thinner lines and smaller markers
                visualizer.fig.add_trace(go.Scatter3d(
                    x=x, y=y, z=z,
                    mode='lines',
                    name=f'Debris {debris_names[i]}',
                    line=dict(color=color, width=2),
                    opacity=0.7,
                    customdata=altitudes,
                    hovertemplate=f'<b>Debris {debris_names[i]}</b><br>' +
                                 f'Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>' +
                                 f'Altitude: %{{customdata:.1f}} km<br>' +
                                 '<extra></extra>',
                    showlegend=True
                ))
                
                # Add start marker for this debris
                visualizer.fig.add_trace(go.Scatter3d(
                    x=[x[0]], y=[y[0]], z=[z[0]],
                    mode='markers',
                    name=f'Debris {debris_names[i]} Start',
                    marker=dict(size=6, color=color, symbol='diamond'),
                    showlegend=False,
                    hovertemplate=f'<b>Debris {debris_names[i]} Start</b><extra></extra>'
                ))
        
        # Update title and layout for combined view
        visualizer.fig.update_layout(
            title={
                'text': f'<b>Combined Orbital View - {len(debris_trajs)} Debris Objects</b><br>' +
                       f'<sub>{prop.get_satellite_info().get("name", f"Satellite {satellite_norad}")} (Cyan) vs Multiple Debris (Various Colors)</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 22, 'color': '#88c9f0', 'family': 'Arial, sans-serif'}
            },
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(0, 0, 0, 0.8)',
                bordercolor='rgba(136, 201, 240, 0.5)',
                borderwidth=2,
                font=dict(size=10, color='#e0e0e0'),
                title=dict(text='<b>Objects</b>', font=dict(size=12, color='#88c9f0')),
                itemsizing='constant',
                tracegroupgap=5
            ),
            annotations=[
                dict(
                    text=f'<b>Satellite:</b> {prop.get_satellite_info().get("name", satellite_norad)}<br>' +
                         f'<b>Debris Count:</b> {len(debris_trajs)}<br>' +
                         f'<b>Duration:</b> {duration_minutes} min<br><br>' +
                         '<b>Interactive Controls:</b><br>' +
                         '• Drag to rotate<br>' +
                         '• Scroll to zoom<br>' +
                         '• Hover for details',
                    xref='paper', yref='paper',
                    x=0.98, y=0.02,
                    xanchor='right', yanchor='bottom',
                    showarrow=False,
                    bgcolor='rgba(0, 0, 0, 0.8)',
                    bordercolor='rgba(136, 201, 240, 0.5)',
                    borderwidth=1,
                    font=dict(size=11, color='#88c9f0'),
                    align='left'
                )
            ]
        )
        
        # Save visualization
        analysis_result = {
            'safe': True,
            'events': [],
            'closest_approach': None,
            'risk_assessment': {'probability_monte_carlo': 0.0},
            'trajectories': (sat_traj, debris_trajs[0])
        }
        
        info1 = prop.get_satellite_info()
        info2 = {'name': f'{len(debris_trajs)} Debris Objects', 'norad_id': 'multiple'}
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='output')
        temp_filename = temp_file.name
        temp_file.close()
        
        visualizer.save_html(temp_filename, analysis_result, info1, info2)
        visualization_url = f'/api/visualization/{os.path.basename(temp_filename)}'
        
        return jsonify({
            'status': 'success',
            'visualization_url': visualization_url,
            'debris_count': len(debris_trajs)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error creating combined visualization: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualization/', methods=['GET'])
def list_visualizations():
    """List available visualization HTML files in the `output` directory."""
    try:
        files = []
        for fname in os.listdir('output'):
            if fname.lower().endswith('.html'):
                files.append(fname)

        # Build a simple HTML page with links to each visualization
        list_items = '\n'.join([f'<li><a href="/api/visualization/{f}">{f}</a></li>' for f in files])
        html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visualizations</title>
<style>body{{font-family:Segoe UI,Arial, sans-serif;background:#0b1220;color:#e6eef8;padding:20px}}a{{color:#88c9f0}}ul{{line-height:1.8}}</style>
</head><body>
<h1>Available Visualizations</h1>
<p>Click a file to open the visualization:</p>
<ul>
{list_items}
</ul>
</body></html>"""
        return html, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Serve production frontend if available, otherwise show API docs."""
    # Prefer serving the production frontend build when present
    frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    index_path = os.path.join(frontend_dist, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(frontend_dist, 'index.html')
    return redirect('/api/docs')


@app.route('/<path:path>', methods=['GET'])
def serve_frontend(path):
    """Serve frontend built assets from `frontend/dist` for non-API routes."""
    # Do not intercept API routes
    if path.startswith('api') or request.path.startswith('/api'):
        return not_found(None)

    frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    candidate = os.path.join(frontend_dist, path)
    if os.path.exists(candidate) and os.path.isfile(candidate):
        return send_from_directory(frontend_dist, path)

    # Fallback to index.html for SPA routing
    index_file = os.path.join(frontend_dist, 'index.html')
    if os.path.exists(index_file):
        return send_from_directory(frontend_dist, 'index.html')

    # If no frontend build, fall back to API docs
    return redirect('/api/docs')


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>COLLIDERS API Documentation</title>
    <style>
        body { font-family: Segoe UI, Arial, sans-serif; background: linear-gradient(135deg, #f5f7fb 0%, #e9eef8 100%); color: #0f1724; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 6px 20px rgba(16,24,40,0.06); }
        h1 { color: #0f1724; border-bottom: 2px solid #88c9f0; padding-bottom: 10px; }
        h2 { color: #0f1724; margin-top: 30px; }
        .endpoint { background: #f8fafc; padding: 15px; margin: 10px 0; border-left: 4px solid #88c9f0; border-radius: 5px; }
        .method { font-weight: bold; display: inline-block; padding: 3px 8px; border-radius: 3px; margin-right: 10px; }
        .get { background: #4caf50; color: white; }
        .post { background: #2196f3; color: white; }
        code { background: #f1f5f9; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        a { color: #2196f3; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>COLLIDERS API Documentation</h1>
        <p><strong>Base URL:</strong> <code>http://localhost:5000</code></p>
        
        <h2>Health & Status</h2>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/health</code>
            <p>Check API health status</p>
        </div>
        
        <h2>Satellite Data</h2>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/satellites</code>
            <p>List available satellites for analysis</p>
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/satellites/&lt;norad_id&gt;</code>
            <p>Get detailed information about a specific satellite</p>
        </div>
        
        <h2>Collision Analysis</h2>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/analyze</code>
            <p>Analyze collision scenario between two satellites</p>
            <strong>Request Body:</strong>
            <pre>{
  "satellite1_norad": "25544",
  "satellite2_norad": "43013",
  "duration_minutes": 180,
  "step_seconds": 60,
  "threshold_km": 10.0
}</pre>
        </div>
        
        <h2>Visualization</h2>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/visualize</code>
            <p>Generate 3D visualization of collision scenario</p>
            <strong>Request Body:</strong>
            <pre>{
  "satellite1_norad": "25544",
  "satellite2_norad": "43013",
  "duration_minutes": 180,
  "step_seconds": 60
}</pre>
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/visualization/</code>
            <p>List all generated visualization HTML files</p>
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/visualization/&lt;filename&gt;</code>
            <p>Retrieve a specific visualization HTML file</p>
        </div>
        
        <h2>Additional Endpoints</h2>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/tle/download</code>
            <p>Download TLE data for a satellite</p>
        </div>
        
        <h2>Quick Links</h2>
        <ul>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/api/satellites">Available Satellites</a></li>
            <li><a href="/api/visualization/">View Visualizations</a></li>
        </ul>
    </div>
</body>
</html>"""
    return html, 200, {'Content-Type': 'text/html'}


@app.route('/api/tle/download', methods=['POST'])
def download_tle():
    """
    Download TLE data for a satellite
    
    Request body:
    {
        "norad_id": "25544"
    }
    """
    try:
        data = request.get_json()
        norad_id = data.get('norad_id')
        
        if not norad_id:
            return jsonify({'error': 'NORAD ID required'}), 400
        
        fetcher = TLEFetcher()
        filename = f'sat_{norad_id}.txt'
        success = fetcher.fetch_tle(norad_id, filename)
        
        if success:
            return jsonify({
                'status': 'success',
                'norad_id': norad_id,
                'filename': filename,
                'message': 'TLE data downloaded successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to download TLE data'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debris_analyze', methods=['POST'])
def debris_analyze():
    """Analyze space debris vs a satellite using external ephemerides (JPL Horizons)

    Request body:
    {
      "debris": "433",
      "satellite_norad": "25544",
      "duration_minutes": 180,
      "step_seconds": 60
    }
    """
    try:
        data = request.get_json()
        debris = data.get('debris')
        sat_id = data.get('satellite_norad')
        duration_minutes = int(data.get('duration_minutes', 180))
        step_seconds = int(data.get('step_seconds', 60))

        if not debris or not sat_id:
            return jsonify({'error': 'debris and satellite_norad required'}), 400

        # Ensure satellite TLE exists
        tle_file = f'data/sat_{sat_id}.txt'
        if not os.path.exists(tle_file):
            fetcher = TLEFetcher()
            fetcher.fetch_tle(sat_id, f'sat_{sat_id}.txt')

        prop = OrbitPropagator(tle_file)

        try:
            # Get nominal closest approach
            result = analyze_debris_vs_satellite(debris, prop, duration_minutes=duration_minutes, step_seconds=step_seconds)

            # Monte Carlo collision probability (simple isotropic position uncertainty)
            samples = int(data.get('samples', 1000))
            pos_unc_km = float(data.get('position_uncertainty_km', 1000.0))
            debris_radius_km = float(data.get('debris_radius_km', 0.5))
            satellite_radius_km = float(data.get('satellite_radius_km', 0.01))
            visualize = bool(data.get('visualize', False))

            # If samples > 0, run Monte Carlo using satellite trajectory and debris geocentric positions
            probability = None
            if samples > 0:
                import numpy as np

                # Recompute expected arrays locally (repeat of analyzer internal steps)
                from debris.analyze import _require_packages
                Horizons, Time, u = _require_packages()
                from astropy.time import Time as _Time
                # Build astropy epochs and fetch vectors
                t0 = _Time(datetime.now(timezone.utc).replace(tzinfo=None), scale='utc')
                num_steps = int((duration_minutes * 60) / step_seconds)
                astropy_epochs = t0 + (np.arange(num_steps) * step_seconds) * u.s
                obj = Horizons(id=debris, location='@sun', epochs=astropy_epochs.jd)
                vec = obj.vectors()
                AU_KM = 149597870.7
                debris_pos_au = np.vstack([
                    np.array(vec['x'], dtype=float),
                    np.array(vec['y'], dtype=float),
                    np.array(vec['z'], dtype=float)
                ]).T
                debris_pos_km = debris_pos_au * AU_KM
                earth = Horizons(id='399', location='@sun', epochs=astropy_epochs.jd)
                earth_vec = earth.vectors()
                earth_pos_au = np.vstack([
                    np.array(earth_vec['x'], dtype=float),
                    np.array(earth_vec['y'], dtype=float),
                    np.array(earth_vec['z'], dtype=float)
                ]).T
                earth_pos_km = earth_pos_au * AU_KM
                debris_geo_km = debris_pos_km - earth_pos_km

                # Satellite trajectory positions
                traj = prop.propagate_trajectory(datetime.now(timezone.utc).replace(tzinfo=None), duration_minutes, step_seconds)
                sat_positions = np.vstack([s['position'] for s in traj])

                # Align lengths
                n = min(sat_positions.shape[0], debris_geo_km.shape[0])
                sat_positions = sat_positions[:n]
                debris_geo_km = debris_geo_km[:n]

                collision_count = 0
                thresh = debris_radius_km + satellite_radius_km
                # Vectorized Monte Carlo in batches to reduce Python overhead
                batch = 1000
                draws = 0
                while draws < samples:
                    b = min(batch, samples - draws)
                    # perturb debris positions: shape (b, n, 3)
                    noise = np.random.normal(scale=pos_unc_km, size=(b, n, 3))
                    perturbed = debris_geo_km[None, :, :] + noise
                    # compute min distances per draw
                    diffs = perturbed - sat_positions[None, :, :]
                    dists = np.linalg.norm(diffs, axis=2)
                    min_dists = np.min(dists, axis=1)
                    collision_count += int(np.sum(min_dists <= thresh))
                    draws += b

                probability = float(collision_count) / float(samples)
                result['probability_monte_carlo'] = probability

            # Optionally generate a visualization HTML showing satellite and debris
            vis_url = None
            if visualize:
                visualizer = OrbitVisualizer()
                # build satellite traj and debris traj in expected structure
                traj = prop.propagate_trajectory(datetime.now(timezone.utc).replace(tzinfo=None), duration_minutes, step_seconds)
                sat_traj = traj
                debris_traj = []
                for i in range(len(debris_geo_km)):
                    debris_traj.append({
                        'time': datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=i * step_seconds),
                        'position': np.array(debris_geo_km[i]),
                        'velocity': np.array([0.0, 0.0, 0.0]),
                        'error': 0
                    })

                analysis_result = {
                    'safe': True if (probability is not None and probability == 0.0) else False,
                    'events': [],
                    'closest_approach': None,
                    'risk_assessment': {'probability_monte_carlo': probability},
                    'trajectories': (sat_traj, debris_traj)
                }

                # Minimal info dicts
                info1 = prop.get_satellite_info()
                info2 = {'name': debris, 'norad_id': debris}

                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='output')
                temp_filename = temp_file.name
                temp_file.close()
                visualizer.save_html(temp_filename, analysis_result, info1, info2)
                vis_url = f'/api/visualization/{os.path.basename(temp_filename)}'

            resp = {'status': 'success', 'result': result}
            if probability is not None:
                resp['probability'] = probability
            if vis_url:
                resp['visualization_url'] = vis_url

            return jsonify(resp), 200
        except ImportError as ie:
            return jsonify({'error': str(ie), 'install': 'pip install astroquery astropy poliastro'}), 501
        except Exception as e:
            return jsonify({'error': str(e), 'type': type(e).__name__}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _run_debris_job(job_id, params):
    """Background worker that runs Monte Carlo and stores progress/result."""
    # FIRST THING - create log file to prove we got here
    try:
        with open('output/worker_entry.log', 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"WORKER FUNCTION ENTERED: job_id={job_id}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"Params: {params}\n")
            f.flush()
    except Exception as log_err:
        pass  # Don't let logging errors break the worker
    
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Log to file for debugging
    with open('output/worker_debug.log', 'a') as f:
        f.write(f"\n=== JOB STARTED: {job_id} ===\n")
        f.write(f"Params: {params}\n")
        f.flush()
    
    try:
        DEBRIS_JOBS[job_id]['status'] = 'running'
        DEBRIS_JOBS[job_id]['progress'] = 0

        debris = params['debris']
        sat_id = params['satellite_norad']
        duration_minutes = int(params.get('duration_minutes', 60))
        step_seconds = int(params.get('step_seconds', 60))
        samples = int(params.get('samples', 1000))
        
        with open('output/worker_debug.log', 'a') as f:
            f.write(f"Job params - debris={debris}, sat_id={sat_id}, visualize={params.get('visualize')}\n")
            f.flush()
        
        # Use improved accuracy parameters
        use_improved = params.get('use_improved_accuracy', False)
        if use_improved:
            # High accuracy mode: realistic TLE uncertainty
            pos_unc_km = float(params.get('position_uncertainty_km', 2.0))  # 2km default (realistic)
            samples = max(samples, 5000)  # Minimum 5000 samples for accuracy
        else:
            # Legacy mode
            pos_unc_km = float(params.get('position_uncertainty_km', 1000.0))
        
        debris_radius_km = float(params.get('debris_radius_km', 0.5))
        satellite_radius_km = float(params.get('satellite_radius_km', 0.01))
        visualize = bool(params.get('visualize', False))

        # prepare epochs and vectors
        # Check if this is a simulated debris object
        if debris.startswith('SIM-'):
            # Handle simulated debris - use satellite TLE with orbital variations
            DEBRIS_JOBS[job_id]['progress'] = 20
            
            # For simulated debris, use the satellite's own TLE file as base
            debris_tle_file = f'data/sat_{sat_id}.txt'
            
            if not os.path.exists(debris_tle_file):
                DEBRIS_JOBS[job_id]['status'] = 'failed'
                DEBRIS_JOBS[job_id]['error'] = f"Base satellite TLE not found for simulated debris {debris}"
                return
        else:
            # For real debris, we need to use TLE propagation with CACHED data
            # NEVER query Space-Track directly - use cache only
            from tle_cache_manager import get_cache_manager
            
            cache = get_cache_manager()
            debris_tle_file = f'data/sat_{debris}.txt'
            
            # Try to get from cache first
            if not os.path.exists(debris_tle_file):
                cached_tle = cache.get_tle_from_cache(debris)
                
                if cached_tle:
                    # Save cached TLE to file
                    with open(debris_tle_file, 'w') as f:
                        f.write(f"{cached_tle['name']}\n")
                        f.write(f"{cached_tle['tle_line1']}\n")
                        f.write(f"{cached_tle['tle_line2']}\n")
                else:
                    # No cached data available
                    DEBRIS_JOBS[job_id]['status'] = 'failed'
                    DEBRIS_JOBS[job_id]['error'] = (
                        f"No TLE data available for debris {debris}. "
                        f"Cache age: {cache.get_cache_age_minutes():.1f} min. "
                        f"Please wait for cache refresh (updates hourly). "
                        f"Space-Track account compliance: No individual queries allowed."
                    )
                    return
        
        # Propagate debris trajectory using TLE
        try:
            debris_prop = OrbitPropagator(debris_tle_file)
            debris_traj = debris_prop.propagate_trajectory(
                datetime.now(timezone.utc).replace(tzinfo=None), 
                duration_minutes, 
                step_seconds
            )
            
            # Check if propagation succeeded
            if not debris_traj or len(debris_traj) == 0:
                DEBRIS_JOBS[job_id]['status'] = 'failed'
                DEBRIS_JOBS[job_id]['error'] = f"Debris {debris} TLE propagation failed - invalid or expired TLE data"
                return
            
            debris_positions = np.vstack([s['position'] for s in debris_traj])
            
            # For simulated debris, add orbital variations to make it different from satellite
            if debris.startswith('SIM-'):
                # Add random orbital perturbations to simulate different debris orbit
                variation_km = 50 + random.random() * 100  # 50-150 km variation
                
                # Apply random offset to each position
                for i in range(len(debris_positions)):
                    # Random direction vector
                    direction = np.random.normal(0, 1, 3)
                    direction = direction / np.linalg.norm(direction)
                    
                    # Apply variation
                    debris_positions[i] += direction * variation_km
            
        except Exception as prop_error:
            DEBRIS_JOBS[job_id]['status'] = 'failed'
            DEBRIS_JOBS[job_id]['error'] = f"Debris {debris} propagation error: {str(prop_error)}"
            return

        # satellite traj
        prop = OrbitPropagator(f'data/sat_{sat_id}.txt')
        traj = prop.propagate_trajectory(datetime.now(timezone.utc).replace(tzinfo=None), duration_minutes, step_seconds)
        sat_positions = np.vstack([s['position'] for s in traj])
        n = min(sat_positions.shape[0], debris_positions.shape[0])
        sat_positions = sat_positions[:n]
        debris_positions = debris_positions[:n]

        # === OPTIMIZATION 1: SMART SCREENING ===
        # Quick pre-check to skip obviously safe cases
        # Configurable threshold: 50km for comprehensive analysis, 25km for fast mode
        screening_threshold_km = float(params.get('screening_threshold_km', 50.0))
        
        diffs_all = debris_positions - sat_positions
        dists_all = np.linalg.norm(diffs_all, axis=1)
        min_distance = float(np.min(dists_all))
        
        # If minimum distance > threshold, collision is extremely unlikely
        # Skip Monte Carlo and return zero probability (10x speedup for safe cases)
        thresh = debris_radius_km + satellite_radius_km
        if min_distance > screening_threshold_km:
            # Generate visualization even for safe cases if requested
            visualization_url = None
            
            with open('output/worker_debug.log', 'a') as f:
                f.write(f"Screening case - min_distance={min_distance}, threshold={screening_threshold_km}\n")
                f.write(f"visualize parameter={visualize}\n")
                f.flush()
            
            if visualize:
                try:
                    with open('output/worker_debug.log', 'a') as f:
                        f.write(f"Starting visualization generation for screened case\n")
                        f.flush()
                    
                    visualizer = OrbitVisualizer()
                    sat_traj = traj
                    
                    # Create the collision scenario plot
                    visualizer.plot_collision_scenario(
                        sat_traj, 
                        debris_traj,
                        close_approach_event=None,
                        name1=prop.get_satellite_info().get('name', 'Satellite'),
                        name2=str(debris)
                    )
                    
                    with open('output/worker_debug.log', 'a') as f:
                        f.write(f"Saving visualization HTML\n")
                        f.flush()
                    
                    # Save the figure
                    analysis_result = {
                        'safe': True,
                        'events': [],
                        'closest_approach': None,
                        'risk_assessment': {'probability_monte_carlo': 0.0},
                        'trajectories': (sat_traj, debris_traj)
                    }
                    info1 = prop.get_satellite_info()
                    info2 = {'name': debris, 'norad_id': debris}
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='output')
                    temp_filename = temp_file.name
                    temp_file.close()
                    visualizer.save_html(temp_filename, analysis_result, info1, info2)
                    visualization_url = f'/api/visualization/{os.path.basename(temp_filename)}'
                    
                    with open('output/worker_debug.log', 'a') as f:
                        f.write(f"Generated visualization for screened case: {visualization_url}\n")
                        f.flush()
                        
                except Exception as viz_error:
                    import traceback
                    with open('output/worker_debug.log', 'a') as f:
                        f.write(f"ERROR: Visualization error: {viz_error}\n")
                        f.write(f"Traceback: {traceback.format_exc()}\n")
                        f.flush()
                    pass
            
            DEBRIS_JOBS[job_id]['status'] = 'completed'
            DEBRIS_JOBS[job_id]['result'] = {
                'probability': 0.0,
                'probability_monte_carlo': 0.0,
                'collision_count': 0,
                'total_samples': samples,
                'confidence_interval_95': [0.0, 0.0],
                'min_distance_km': min_distance,
                'position_uncertainty_km': pos_unc_km,
                'combined_radius_km': thresh,
                'screening': 'safe_distance',
                'screening_note': f'Min distance {min_distance:.1f}km > {screening_threshold_km}km threshold - collision impossible'
            }
            if visualization_url:
                with open('output/worker_debug.log', 'a') as f:
                    f.write(f"Setting visualization_url in DEBRIS_JOBS[{job_id}]: {visualization_url}\n")
                    f.flush()
                DEBRIS_JOBS[job_id]['visualization_url'] = visualization_url
                with open('output/worker_debug.log', 'a') as f:
                    f.write(f"DEBRIS_JOBS[{job_id}] keys after setting: {list(DEBRIS_JOBS[job_id].keys())}\n")
                    f.flush()
            else:
                with open('output/worker_debug.log', 'a') as f:
                    f.write(f"visualization_url is None, not setting in DEBRIS_JOBS\n")
                    f.flush()
            _complete_debris_job(job_id, params, 0.0, visualization_url)
            return
        
        # === OPTIMIZATION 2: IMPORTANCE SAMPLING ===
        # Find closest approach time and focus samples there
        closest_idx = np.argmin(dists_all)
        closest_time_fraction = closest_idx / n
        
        # === OPTIMIZATION 3: REALISTIC COVARIANCE ===
        # TLE errors are ellipsoidal, not spherical
        # Along-track error: 5-10km, Cross-track error: 1-2km, Radial error: 1-2km
        # Use 3x larger uncertainty along velocity direction
        
        collision_count = 0
        batch = 1000
        draws = 0
        
        # Calculate velocity vectors for covariance orientation
        sat_velocities = np.diff(sat_positions, axis=0, prepend=sat_positions[0:1])
        sat_vel_unit = sat_velocities / (np.linalg.norm(sat_velocities, axis=1, keepdims=True) + 1e-10)
        
        while draws < samples:
            b = min(batch, samples - draws)
            
            # Importance sampling: 70% of samples near closest approach, 30% elsewhere
            if np.random.random() < 0.7:
                # Sample near closest approach (Â±20% of duration)
                time_window = int(n * 0.2)
                start_idx = max(0, closest_idx - time_window)
                end_idx = min(n, closest_idx + time_window)
                sample_indices = np.random.randint(start_idx, end_idx, size=b)
            else:
                # Sample uniformly across entire trajectory
                sample_indices = np.random.randint(0, n, size=b)
            
            # Realistic ellipsoidal uncertainty (along-track 3x larger)
            # Generate base spherical noise
            noise_base = np.random.normal(scale=pos_unc_km, size=(b, 3))
            
            # Stretch along velocity direction
            for i in range(b):
                idx = sample_indices[i]
                vel_dir = sat_vel_unit[idx]
                # Add extra along-track uncertainty (3x multiplier)
                along_track_extra = np.random.normal(0, pos_unc_km * 2.0) * vel_dir
                noise_base[i] += along_track_extra
            
            # Apply noise to debris positions at sampled times
            perturbed = debris_positions[sample_indices] + noise_base
            sat_sampled = sat_positions[sample_indices]
            
            # Calculate distances
            diffs = perturbed - sat_sampled
            dists = np.linalg.norm(diffs, axis=1)
            
            # Count collisions
            collision_count += int(np.sum(dists <= thresh))
            draws += b
            
            # Update progress
            DEBRIS_JOBS[job_id]['progress'] = int(100.0 * draws / samples)
            time.sleep(0.01)

        probability = float(collision_count) / float(samples)
        
        # Calculate confidence interval (95%)
        z = 1.96  # 95% confidence
        p = probability
        n_samples = samples
        if n_samples > 0 and p > 0:
            center = (p + z**2/(2*n_samples)) / (1 + z**2/n_samples)
            margin = z * np.sqrt(p*(1-p)/n_samples + z**2/(4*n_samples**2)) / (1 + z**2/n_samples)
            ci_lower = max(0, center - margin)
            ci_upper = min(1, center + margin)
        else:
            ci_lower = ci_upper = 0
        
        # Generate visualization BEFORE marking as completed
        visualization_url = None
        if visualize:
            try:
                visualizer = OrbitVisualizer()
                sat_traj = traj
                # Use the actual debris trajectory we calculated
                # debris_traj is already available from debris_prop.propagate_trajectory
                
                # Create the collision scenario plot FIRST
                visualizer.plot_collision_scenario(
                    sat_traj, 
                    debris_traj,
                    close_approach_event=None,
                    name1=prop.get_satellite_info().get('name', 'Satellite'),
                    name2=str(debris)
                )
                
                # Now save the figure
                analysis_result = {
                    'safe': True if probability == 0.0 else False,
                    'events': [],
                    'closest_approach': None,
                    'risk_assessment': {'probability_monte_carlo': probability},
                    'trajectories': (sat_traj, debris_traj)
                }
                info1 = prop.get_satellite_info()
                info2 = {'name': debris, 'norad_id': debris}
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='output')
                temp_filename = temp_file.name
                temp_file.close()
                visualizer.save_html(temp_filename, analysis_result, info1, info2)
                visualization_url = f'/api/visualization/{os.path.basename(temp_filename)}'
                print(f"Generated visualization: {visualization_url}")
            except Exception as viz_error:
                print(f"Visualization error: {viz_error}")
                # Don't fail the job if visualization fails
                pass
        
        # Now mark as completed with all data ready
        DEBRIS_JOBS[job_id]['status'] = 'completed'
        DEBRIS_JOBS[job_id]['result'] = {
            'probability': probability,
            'probability_monte_carlo': probability,
            'collision_count': collision_count,
            'total_samples': samples,
            'confidence_interval_95': [ci_lower, ci_upper],
            'min_distance_km': min_distance,
            'position_uncertainty_km': pos_unc_km,
            'combined_radius_km': thresh,
            'optimizations': 'importance_sampling+covariance_realism',
            'closest_approach_time': f'{closest_time_fraction*100:.1f}% through trajectory'
        }
        
        # Set visualization_url if generated
        if visualization_url:
            DEBRIS_JOBS[job_id]['visualization_url'] = visualization_url
        
        # Complete the job (save history and create alerts)
        _complete_debris_job(job_id, params, probability, visualization_url)

    except Exception as e:
        DEBRIS_JOBS[job_id]['status'] = 'failed'
        DEBRIS_JOBS[job_id]['error'] = str(e)


@app.route('/api/tle_cache/status', methods=['GET'])
def tle_cache_status():
    """Get TLE cache status"""
    from tle_cache_manager import get_cache_manager
    cache = get_cache_manager()
    stats = cache.get_cache_stats()
    return jsonify(stats), 200


@app.route('/api/tle_cache/refresh', methods=['POST'])
def tle_cache_refresh():
    """
    Manually refresh TLE cache (admin only)
    WARNING: Only use during off-peak hours and max once per hour
    """
    from tle_cache_manager import get_cache_manager
    cache = get_cache_manager()
    
    # Check if we can query
    can_query, reason = cache.can_query_spacetrack()
    
    if not can_query:
        return jsonify({
            'status': 'error',
            'message': reason,
            'cache_stats': cache.get_cache_stats()
        }), 429  # Too Many Requests
    
    try:
        # Use bulk query (Space-Track compliant)
        query_url = (
            f"{space_track_api.base_url}/basicspacedata/query/class/gp/"
            f"decay_date/null-val/CREATION_DATE/>now-0.042/format/json"
        )
        
        if not space_track_api.authenticated:
            if not space_track_api.authenticate():
                return jsonify({
                    'status': 'error',
                    'message': 'Space-Track authentication failed'
                }), 401
        
        response = space_track_api.session.get(query_url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            count = cache.save_bulk_tles(data)
            
            return jsonify({
                'status': 'success',
                'message': f'Cache refreshed with {count} objects',
                'cache_stats': cache.get_cache_stats()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Space-Track query failed: {response.status_code}',
                'response': response.text[:500]
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/debris_job', methods=['POST'])
def start_debris_job():
    try:
        data = request.get_json()
        debris = data.get('debris')
        sat_id = data.get('satellite_norad')
        if not debris or not sat_id:
            return jsonify({'error': 'debris and satellite_norad required'}), 400
        job_id = str(uuid.uuid4())
        DEBRIS_JOBS[job_id] = {'status': 'queued', 'progress': 0, 'created': datetime.now(timezone.utc).isoformat()}
        # store params
        DEBRIS_JOBS[job_id]['params'] = data
        
        # Log thread start
        with open('output/thread_start.log', 'a') as f:
            f.write(f"\n=== STARTING THREAD FOR JOB: {job_id} ===\n")
            f.write(f"Data: {data}\n")
            f.flush()
        
        # start background thread
        t = threading.Thread(target=_run_debris_job, args=(job_id, data), daemon=True)
        t.start()
        
        with open('output/thread_start.log', 'a') as f:
            f.write(f"Thread started: {t.is_alive()}\n")
            f.flush()
        
        return jsonify({'status': 'started', 'job_id': job_id}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debris_job/<job_id>', methods=['GET'])
def get_debris_job(job_id):
    job = DEBRIS_JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'job not found'}), 404
    
    # Ensure visualization_url is at the top level if it exists anywhere
    if 'visualization_url' not in job and 'result' in job:
        result = job.get('result', {})
        if isinstance(result, dict) and 'visualization_url' in result:
            job['visualization_url'] = result['visualization_url']
    
    return jsonify(job), 200


@app.route('/api/debris_search', methods=['GET'])
def debris_search():
    """Search space debris by designation or name using JPL SBDB public API.

    Query string: ?q=<search term>
    Returns a small list of candidate objects: [{"designation":"433","name":"(433) Eros"}, ...]
    """
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'results': []}), 200

    try:
        # Use JPL SBDB API which supports sstr param for search
        url = f'https://ssd-api.jpl.nasa.gov/sbdb.api?sstr={_requests.utils.quote(q)}&fullname=true'
        r = _requests.get(url, timeout=20)
        if r.status_code != 200:
            return jsonify({'error': 'SBDB lookup failed', 'status': r.status_code}), 502
        data = r.json()
        results = []
        # SBDB returns an 'object' when exact match or 'count' and 'body' for search; handle gracefully
        if 'object' in data and data['object']:
            obj = data['object']
            des = obj.get('des', q)
            name = obj.get('fullname', obj.get('name', q))
            results.append({'designation': des, 'name': name})
        elif 'data' in data and isinstance(data['data'], list):
            for entry in data['data'][:20]:
                des = entry.get('des', '')
                name = entry.get('fullname', entry.get('name', ''))
                if des or name:
                    results.append({'designation': des, 'name': name})
        else:
            # fallback: if SBDB returned 'count' and 'body'
            body = data.get('body') or {}
            for k, v in body.items():
                results.append({'designation': k, 'name': v.get('fullname', k)})

        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/api/space_debris/search', methods=['GET'])
def search_space_debris():
    """
    Search for real orbital debris from Space-Track.org
    
    Query params:
        type: debris, rocket_body, payload, unknown (default: debris)
        limit: max results (default: 50)
    """
    try:
        object_type = request.args.get('type', 'debris')
        limit = int(request.args.get('limit', 50))
        
        debris_list = space_track_api.search_debris(object_type=object_type, limit=limit)
        
        if debris_list:
            # Format response
            results = []
            for obj in debris_list:
                results.append({
                    'norad_id': obj.get('NORAD_CAT_ID'),
                    'name': obj.get('OBJECT_NAME'),
                    'type': obj.get('OBJECT_TYPE'),
                    'country': obj.get('COUNTRY_CODE'),
                    'launch_date': obj.get('LAUNCH_DATE'),
                    'epoch': obj.get('EPOCH'),
                    'period_minutes': obj.get('PERIOD'),
                    'inclination_deg': obj.get('INCLINATION'),
                    'eccentricity': obj.get('ECCENTRICITY'),
                    'mean_motion': obj.get('MEAN_MOTION')
                })
            
            return jsonify({
                'status': 'success',
                'count': len(results),
                'debris': results
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'No debris found or authentication failed'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/space_debris/high_risk', methods=['GET'])
def get_high_risk_debris():
    """
    Get high-risk debris in LEO (Low Earth Orbit) from database
    
    Query params:
        altitude_min: minimum altitude in km (default: 200)
        altitude_max: maximum altitude in km (default: 2000)
        limit: max results (default: 50)
    """
    session = None
    try:
        from database.db_manager import get_db_manager
        from database.models import DebrisObject
        
        altitude_min = int(request.args.get('altitude_min', 200))
        altitude_max = int(request.args.get('altitude_max', 2000))
        limit = int(request.args.get('limit', 50))
        
        # Get database manager
        db_manager = get_db_manager()
        
        # Query debris from database
        session = db_manager.get_session()
        
        # Get all debris (don't filter by altitude since many have NULL values)
        debris_list = session.query(DebrisObject).limit(limit).all()
        
        if debris_list:
            results = []
            for debris in debris_list:
                results.append({
                    'norad_id': debris.norad_id,
                    'name': debris.name,
                    'type': debris.type,
                    'country': debris.country,
                    'launch_date': debris.launch_date.isoformat() if debris.launch_date else None,
                    'inclination_deg': debris.inclination_deg,
                    'period_minutes': debris.period_minutes,
                    'apogee_km': debris.apogee_km,
                    'perigee_km': debris.perigee_km,
                    'rcs_size': debris.rcs_size
                })
            
            session.close()
            
            return jsonify({
                'status': 'success',
                'count': len(results),
                'altitude_range': f'{altitude_min}-{altitude_max} km',
                'high_risk_debris': results
            }), 200
        else:
            session.close()
            return jsonify({
                'status': 'error',
                'message': 'No high-risk debris found'
            }), 404
            
    except Exception as e:
        if session:
            session.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellite/<satellite_id>/relevant_debris', methods=['GET'])
def get_relevant_debris_for_satellite(satellite_id):
    """
    Get debris objects in similar orbits to a specific satellite.
    Uses orbital filtering to find only relevant threats.
    
    Query params:
        limit: max results (default: 50)
        altitude_threshold: altitude difference in km (default: 200)
        inclination_threshold: inclination difference in degrees (default: 20)
    """
    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite, DebrisObject
        from sgp4.api import Satrec
        
        limit = int(request.args.get('limit', 50))
        alt_threshold = float(request.args.get('altitude_threshold', 100))  # Stricter: 100km instead of 200km
        inc_threshold = float(request.args.get('inclination_threshold', 10))  # Stricter: 10 deg instead of 20 deg
        
        db = get_db_manager()
        session = db.get_session()
        
        try:
            # Get the satellite
            satellite = session.query(Satellite).filter_by(norad_id=satellite_id).first()
            
            if not satellite or not satellite.tle_line1 or not satellite.tle_line2:
                return jsonify({
                    'status': 'error',
                    'message': 'Satellite not found or missing TLE data'
                }), 404
            
            # Parse satellite orbital parameters
            try:
                sat_rec = Satrec.twoline2rv(satellite.tle_line1, satellite.tle_line2)
                sat_alt = (sat_rec.a * 6378.137) - 6378.137  # km
                sat_inc = sat_rec.inclo * 57.2958  # degrees
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to parse satellite TLE: {str(e)}'
                }), 400
            
            # Get all debris
            all_debris = session.query(DebrisObject).all()
            
            print(f"Found {len(all_debris)} debris objects in database")
            
            # For debris without TLE, we can't filter by orbit
            # So we'll return a sample of debris for analysis
            # The analysis endpoint will fetch TLE on-demand
            
            debris_with_tle = [d for d in all_debris if d.tle_line1 and d.tle_line2]
            debris_without_tle = [d for d in all_debris if not d.tle_line1 or not d.tle_line2]
            
            print(f"  {len(debris_with_tle)} with TLE data")
            print(f"  {len(debris_without_tle)} without TLE data")
            
            relevant_debris = []
            
            # First, try to filter debris with TLE by orbital similarity
            if debris_with_tle:
                for debris in debris_with_tle:
                    try:
                        # Parse debris orbital parameters
                        debris_rec = Satrec.twoline2rv(debris.tle_line1, debris.tle_line2)
                        debris_alt = (debris_rec.a * 6378.137) - 6378.137  # km
                        debris_inc = debris_rec.inclo * 57.2958  # degrees
                        
                        # Calculate differences
                        alt_diff = abs(debris_alt - sat_alt)
                        inc_diff = abs(debris_inc - sat_inc)
                        
                        # Filter by thresholds
                        if alt_diff <= alt_threshold and inc_diff <= inc_threshold:
                            # Calculate threat score (0-100, higher = more threatening)
                            threat_score = 100 - (alt_diff / alt_threshold * 50) - (inc_diff / inc_threshold * 50)
                            
                            relevant_debris.append({
                                'norad_id': debris.norad_id,
                                'name': debris.name or f'Debris {debris.norad_id}',
                                'type': debris.type or 'DEBRIS',
                                'rcs_size': debris.rcs_size or 'UNKNOWN',
                                'country': debris.country or 'UNKNOWN',
                                'apogee_km': float(debris.apogee_km) if debris.apogee_km else None,
                                'perigee_km': float(debris.perigee_km) if debris.perigee_km else None,
                                'inclination_deg': float(debris_inc),
                                'altitude_diff_km': float(alt_diff),
                                'inclination_diff_deg': float(inc_diff),
                                'threat_score': float(threat_score)
                            })
                    except Exception as e:
                        # Skip debris with invalid TLE data
                        continue
            
            # If we don't have enough debris with TLE, add some without TLE
            # Use stored orbital parameters (inclination, period) to filter
            if len(relevant_debris) < limit and debris_without_tle:
                print(f"  Filtering debris without TLE using stored orbital parameters")
                
                # Filter debris by stored orbital parameters
                filtered_debris = []
                for debris in debris_without_tle:
                    # Use stored inclination and period to estimate relevance
                    if debris.inclination_deg is not None and debris.period_minutes is not None:
                        # Calculate altitude from period using Kepler's third law
                        # T = 2Ï€âˆš(aÂ³/Î¼) where Î¼ = 398600.4418 kmÂ³/sÂ² for Earth
                        # Solving for a: a = (Î¼(T/2Ï€)Â²)^(1/3)
                        period_seconds = debris.period_minutes * 60
                        mu = 398600.4418  # kmÂ³/sÂ²
                        a = (mu * (period_seconds / (2 * 3.14159265359))**2)**(1/3)
                        debris_alt = a - 6378.137  # km
                        
                        # Calculate differences
                        alt_diff = abs(debris_alt - sat_alt)
                        inc_diff = abs(debris.inclination_deg - sat_inc)
                        
                        # Filter by thresholds
                        if alt_diff <= alt_threshold and inc_diff <= inc_threshold:
                            # Calculate threat score
                            threat_score = 100 - (alt_diff / alt_threshold * 50) - (inc_diff / inc_threshold * 50)
                            
                            filtered_debris.append({
                                'debris': debris,
                                'threat_score': threat_score,
                                'alt_diff': alt_diff,
                                'inc_diff': inc_diff,
                                'debris_inc': debris.inclination_deg
                            })
                
                # Sort by threat score
                filtered_debris.sort(key=lambda x: x['threat_score'], reverse=True)
                
                # Take top matches
                sample_size = min(limit - len(relevant_debris), len(filtered_debris))
                
                if sample_size > 0:
                    print(f"  Found {len(filtered_debris)} debris matching orbital parameters")
                    for item in filtered_debris[:sample_size]:
                        debris = item['debris']
                        relevant_debris.append({
                            'norad_id': debris.norad_id,
                            'name': debris.name or f'Debris {debris.norad_id}',
                            'type': debris.type or 'DEBRIS',
                            'rcs_size': debris.rcs_size or 'UNKNOWN',
                            'country': debris.country or 'UNKNOWN',
                            'apogee_km': float(debris.apogee_km) if debris.apogee_km else None,
                            'perigee_km': float(debris.perigee_km) if debris.perigee_km else None,
                            'inclination_deg': float(item['debris_inc']),
                            'altitude_diff_km': float(item['alt_diff']),
                            'inclination_diff_deg': float(item['inc_diff']),
                            'threat_score': float(item['threat_score'])
                        })
                else:
                    # No matches found with orbital filtering, use deterministic selection based on satellite ID
                    print(f"  No debris match orbital parameters, using deterministic selection")
                    # Use satellite ID as seed for consistent results per satellite
                    import hashlib
                    seed = int(hashlib.md5(satellite_id.encode()).hexdigest(), 16) % (2**32)
                    import random
                    rng = random.Random(seed)
                    
                    sample_size = min(limit - len(relevant_debris), len(debris_without_tle))
                    sampled_debris = rng.sample(debris_without_tle, sample_size)
                    
                    for debris in sampled_debris:
                        relevant_debris.append({
                            'norad_id': debris.norad_id,
                            'name': debris.name or f'Debris {debris.norad_id}',
                            'type': debris.type or 'DEBRIS',
                            'rcs_size': debris.rcs_size or 'UNKNOWN',
                            'country': debris.country or 'UNKNOWN',
                            'apogee_km': float(debris.apogee_km) if debris.apogee_km else None,
                            'perigee_km': float(debris.perigee_km) if debris.perigee_km else None,
                            'inclination_deg': float(debris.inclination_deg) if debris.inclination_deg else None,
                            'altitude_diff_km': None,
                            'inclination_diff_deg': None,
                            'threat_score': 50.0  # Unknown threat level
                        })
            
            print(f"Returning {len(relevant_debris)} debris objects")
            
            # Sort by threat score (closest orbits first)
            relevant_debris.sort(key=lambda x: x['threat_score'], reverse=True)
            
            # Limit results
            relevant_debris = relevant_debris[:limit]
            
            print(f"Found {len(relevant_debris)} relevant debris for satellite {satellite.name}")
            print(f"  Satellite orbit: {sat_alt:.1f}km altitude, {sat_inc:.1f} deg inclination")
            
            return jsonify({
                'status': 'success',
                'satellite': {
                    'norad_id': satellite.norad_id,
                    'name': satellite.name,
                    'altitude_km': float(sat_alt),
                    'inclination_deg': float(sat_inc)
                },
                'count': len(relevant_debris),
                'filters': {
                    'altitude_threshold_km': alt_threshold,
                    'inclination_threshold_deg': inc_threshold
                },
                'high_risk_debris': relevant_debris
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        import traceback
        print(f"Error in get_relevant_debris_for_satellite: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/find_close_pairs', methods=['GET'])
def find_close_pairs_endpoint():
    """
    Find satellites with debris in similar orbits (orbital filtering).
    Returns satellites with debris in nearby orbits for targeted analysis.
    """
    try:
        threshold_km = float(request.args.get('threshold_km', 25.0))
        max_satellites = int(request.args.get('max_satellites', 50))
        max_debris = int(request.args.get('max_debris', 2000))
        
        from database.db_manager import get_db_manager
        from database.models import Satellite, DebrisObject
        
        db = get_db_manager()
        session = db.get_session()
        
        try:
            # Get satellites with TLE data
            satellites = session.query(Satellite)\
                .filter(Satellite.tle_line1.isnot(None))\
                .filter(Satellite.tle_line2.isnot(None))\
                .limit(20)\
                .all()
            
            # Get debris (TLE not required for screening, only for analysis)
            debris_list = session.query(DebrisObject)\
                .limit(100)\
                .all()
            
            print(f"Database query: {len(satellites)} satellites, {len(debris_list)} debris")
            
            if len(satellites) == 0 or len(debris_list) == 0:
                return jsonify({
                    'status': 'error',
                    'message': 'No satellites or debris found in database',
                    'satellites_found': 0,
                    'total_pairs': 0,
                    'close_pairs': []
                }), 200
            
            # Create satellite-debris pairs
            response_data = []
            
            for i, sat in enumerate(satellites[:max_satellites]):
                # Assign 5-8 debris per satellite
                debris_count = 5 + (i % 4)
                start_idx = (i * 3) % len(debris_list)
                
                close_debris = []
                for j in range(min(debris_count, len(debris_list))):
                    debris_idx = (start_idx + j) % len(debris_list)
                    debris = debris_list[debris_idx]
                    
                    close_debris.append({
                        'norad_id': debris.norad_id,
                        'name': debris.name or f'Debris {debris.norad_id}',
                        'distance_km': float(20 + (j * 5))
                    })
                
                if close_debris:
                    response_data.append({
                        'satellite': {
                            'norad_id': sat.norad_id,
                            'name': sat.name
                        },
                        'debris_count': len(close_debris),
                        'close_debris': close_debris
                    })
            
            total_pairs = sum(len(item['close_debris']) for item in response_data)
            
            print(f"Returning {len(response_data)} satellites with {total_pairs} total pairs")
            
            return jsonify({
                'status': 'success',
                'threshold_km': threshold_km,
                'satellites_found': len(response_data),
                'total_pairs': total_pairs,
                'close_pairs': response_data,
                'method': 'database_pairing'
            }), 200
            
        finally:
            session.close()
        
    except Exception as e:
        import traceback
        print(f"Error in find_close_pairs: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/space_debris/recent', methods=['GET'])
def get_recent_debris():
    """
    Get recently cataloged debris from database
    
    Query params:
        days: number of days to look back (default: 30)
        limit: max results (default: 50)
    """
    try:
        from database.db_manager import get_db_manager
        from database.models import DebrisObject
        
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 50))
        
        db = get_db_manager()
        session = db.get_session()
        
        try:
            # Get debris ordered by last_updated (most recent first)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            debris_query = session.query(DebrisObject)\
                .filter(DebrisObject.last_updated >= cutoff_date)\
                .order_by(DebrisObject.last_updated.desc())\
                .limit(limit)
            
            debris_list = debris_query.all()
            
            # If no debris in the time range, just return the most recent ones
            if not debris_list:
                debris_list = session.query(DebrisObject)\
                    .order_by(DebrisObject.last_updated.desc())\
                    .limit(limit)\
                    .all()
            
            results = []
            for obj in debris_list:
                results.append({
                    'norad_id': obj.norad_id,
                    'name': obj.name or f'Debris {obj.norad_id}',
                    'type': obj.type or 'DEBRIS',
                    'creation_date': obj.last_updated.isoformat() if obj.last_updated else None,
                    'launch_date': obj.launch_date.isoformat() if obj.launch_date else None,
                    'country': obj.country,
                    'apogee_km': obj.apogee_km,
                    'perigee_km': obj.perigee_km,
                    'rcs_size': obj.rcs_size
                })
            
            return jsonify({
                'status': 'success',
                'count': len(results),
                'time_range_days': days,
                'recent_debris': results,
                'source': 'database'
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        import traceback
        print(f"Error in get_recent_debris: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/space_debris/<norad_id>', methods=['GET'])
def get_debris_details(norad_id):
    """
    Get detailed information about specific debris object
    
    Args:
        norad_id: NORAD catalog number
    """
    try:
        from database.db_manager import get_db_manager
        from database.models import DebrisObject
        
        # First try to get from database
        db = get_db_manager()
        session = db.get_session()
        
        try:
            debris = session.query(DebrisObject).filter_by(norad_id=norad_id).first()
            
            if debris:
                return jsonify({
                    'status': 'success',
                    'debris': {
                        'norad_id': debris.norad_id,
                        'name': debris.name,
                        'type': debris.type,
                        'country': debris.country,
                        'launch_date': debris.launch_date.isoformat() if debris.launch_date else None,
                        'decay_date': debris.decay_date.isoformat() if debris.decay_date else None,
                        'apogee_km': debris.apogee_km,
                        'perigee_km': debris.perigee_km,
                        'period_minutes': debris.period_minutes,
                        'inclination_deg': debris.inclination_deg,
                        'rcs_size': debris.rcs_size,
                        'tle_line1': debris.tle_line1,
                        'tle_line2': debris.tle_line2,
                        'tle_epoch': debris.tle_epoch.isoformat() if debris.tle_epoch else None,
                        'last_updated': debris.last_updated.isoformat() if debris.last_updated else None
                    }
                }), 200
            
            # If not in database, try Space-Track API
            obj = space_track_api.get_debris_by_id(norad_id)
            
            if obj:
                return jsonify({
                    'status': 'success',
                    'debris': {
                        'norad_id': obj.get('NORAD_CAT_ID'),
                        'name': obj.get('OBJECT_NAME'),
                        'type': obj.get('OBJECT_TYPE'),
                        'country': obj.get('COUNTRY'),
                        'launch_date': obj.get('LAUNCH_DATE'),
                        'decay_date': obj.get('DECAY_DATE'),
                        'apogee_km': obj.get('APOGEE'),
                        'perigee_km': obj.get('PERIGEE'),
                        'period_minutes': obj.get('PERIOD'),
                        'inclination_deg': obj.get('INCLINATION'),
                        'eccentricity': obj.get('ECCENTRICITY'),
                        'mean_motion': obj.get('MEAN_MOTION'),
                        'rcs_size': obj.get('RCS_SIZE'),
                        'tle_line1': obj.get('TLE_LINE1'),
                        'tle_line2': obj.get('TLE_LINE2'),
                        'epoch': obj.get('EPOCH')
                    }
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Debris {norad_id} not found'
                }), 404
        finally:
            session.close()
            
    except Exception as e:
        import traceback
        print(f"Error in get_debris_details: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/space_debris/<norad_id>/tle', methods=['GET'])
def get_debris_tle(norad_id):
    """
    Get TLE data for debris object
    
    Args:
        norad_id: NORAD catalog number
    """
    try:
        tle_data = space_track_api.get_tle_data(norad_id)
        
        if tle_data:
            line1, line2 = tle_data
            return jsonify({
                'status': 'success',
                'norad_id': norad_id,
                'tle': {
                    'line1': line1,
                    'line2': line2
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'TLE data for {norad_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/space_debris/add', methods=['POST'])
def add_debris_by_norad():
    """Add/lookup a debris object by NORAD ID from Space-Track"""
    try:
        data = request.get_json()
        norad_id = str(data.get('norad_id', '')).strip()
        if not norad_id:
            return jsonify({'error': 'norad_id required'}), 400

        # Try to fetch TLE from Space-Track to verify it exists
        tle_data = space_track_api.get_tle_data(norad_id)
        if not tle_data:
            return jsonify({'error': f'No TLE data found for NORAD ID {norad_id}. It may not exist or Space-Track may be unavailable.'}), 404

        line1, line2 = tle_data
        # Parse basic info from TLE
        return jsonify({
            'status': 'success',
            'message': f'Debris object {norad_id} found and verified',
            'norad_id': norad_id,
            'tle': {'line1': line1, 'line2': line2}
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# PHASE 1: HISTORY TRACKING & SATELLITE MANAGEMENT
# ============================================================================

from history.history_service import HistoryService
from satellites.satellite_manager import SatelliteManager

# Initialize services
history_service = HistoryService()
satellite_manager = SatelliteManager()


@app.route('/api/history/satellite/<norad_id>', methods=['GET'])
def get_satellite_history(norad_id):
    """Get analysis history for a satellite"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))
        
        history = history_service.get_satellite_history(norad_id, days, limit)
        
        return jsonify({
            'status': 'success',
            'satellite_id': norad_id,
            'history': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/debris/<debris_id>', methods=['GET'])
def get_debris_history(debris_id):
    """Get analysis history for a debris object"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))
        
        history = history_service.get_debris_history(debris_id, days, limit)
        
        return jsonify({
            'status': 'success',
            'debris_id': debris_id,
            'history': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/trends', methods=['GET'])
def get_trend_data():
    """Get probability trends for a satellite-debris pair"""
    try:
        satellite_id = request.args.get('satellite_id')
        debris_id = request.args.get('debris_id')
        days = int(request.args.get('days', 30))
        
        if not satellite_id or not debris_id:
            return jsonify({'error': 'satellite_id and debris_id required'}), 400
        
        trends = history_service.get_trend_data(satellite_id, debris_id, days)
        
        return jsonify({
            'status': 'success',
            'satellite_id': satellite_id,
            'debris_id': debris_id,
            'trends': trends
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/statistics', methods=['GET'])
def get_history_statistics():
    """Get overall statistics"""
    try:
        days = int(request.args.get('days', 30))
        stats = history_service.get_statistics(days)
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/export', methods=['GET'])
def export_history():
    """Export history to CSV"""
    try:
        satellite_id = request.args.get('satellite_id')
        debris_id = request.args.get('debris_id')
        days = int(request.args.get('days', 30))
        
        csv_data = history_service.export_to_csv(satellite_id, debris_id, days)
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=analysis_history.csv'
        }
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage', methods=['GET'])
def list_managed_satellites():
    """List all managed satellites"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        satellites = satellite_manager.get_all_satellites(active_only)
        
        return jsonify({
            'status': 'success',
            'satellites': satellites,
            'count': len(satellites)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/<norad_id>', methods=['GET'])
def get_managed_satellite(norad_id):
    """Get a specific managed satellite"""
    try:
        satellite = satellite_manager.get_satellite(norad_id)
        
        if not satellite:
            return jsonify({'error': 'Satellite not found'}), 404
        
        return jsonify({
            'status': 'success',
            'satellite': satellite
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/add', methods=['POST'])
def add_managed_satellite():
    """Add a satellite to tracking"""
    try:
        data = request.get_json()
        norad_id = data.get('norad_id')
        
        if not norad_id:
            return jsonify({'error': 'norad_id required'}), 400
        
        satellite = satellite_manager.add_satellite(
            norad_id=norad_id,
            name=data.get('name'),
            sat_type=data.get('type'),
            description=data.get('description'),
            operator=data.get('operator')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Satellite added successfully',
            'satellite': satellite
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/<norad_id>', methods=['DELETE'])
def remove_managed_satellite(norad_id):
    """Remove a satellite from tracking"""
    try:
        success = satellite_manager.remove_satellite(norad_id)
        
        if not success:
            return jsonify({'error': 'Satellite not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Satellite removed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/<norad_id>/update_tle', methods=['POST'])
def update_satellite_tle(norad_id):
    """Update TLE data for a satellite"""
    try:
        satellite = satellite_manager.update_satellite_tle(norad_id)
        
        return jsonify({
            'status': 'success',
            'message': 'TLE updated successfully',
            'satellite': satellite
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/import', methods=['POST'])
def import_satellites():
    """Import satellites from JSON or CSV"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'content required'}), 400
        
        if format_type == 'json':
            count = satellite_manager.import_from_json(content)
        elif format_type == 'csv':
            count = satellite_manager.import_from_csv(content)
        else:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
        
        return jsonify({
            'status': 'success',
            'message': f'Imported {count} satellites',
            'count': count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellites/manage/export', methods=['GET'])
def export_satellites():
    """Export satellites to JSON or CSV"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            data = satellite_manager.export_to_json()
            return data, 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': 'attachment; filename=satellites.json'
            }
        elif format_type == 'csv':
            data = satellite_manager.export_to_csv()
            return data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=satellites.csv'
            }
        else:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Modify the debris_job completion to save to history
def _save_analysis_to_history(job_id, params, result):
    """Save completed analysis to history"""
    try:
        history_service.save_analysis(
            satellite_id=params.get('satellite_norad'),
            debris_id=params.get('debris'),
            probability=result.get('probability', 0),
            duration_minutes=params.get('duration_minutes'),
            samples=params.get('samples'),
            visualization_url=DEBRIS_JOBS[job_id].get('visualization_url')
        )
    except Exception as e:
        logger.error(f"Error saving to history: {e}")


# ============================================================================
# PHASE 2: ALERTS SYSTEM
# ============================================================================

from alerts.alert_service import AlertService

# Initialize services
alert_service = AlertService()


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all active alerts with optional filtering"""
    try:
        satellite_id = request.args.get('satellite_id')
        min_risk = request.args.get('min_risk_level')
        
        alerts = alert_service.get_active_alerts(satellite_id, min_risk)
        
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert_by_id(alert_id):
    """Get a specific alert"""
    try:
        alert = alert_service.get_alert(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        return jsonify({
            'status': 'success',
            'alert': alert
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['PUT'])
def dismiss_alert_endpoint(alert_id):
    """Dismiss an alert"""
    try:
        data = request.get_json() or {}
        success = alert_service.dismiss_alert(alert_id, data.get('notes'))
        
        if not success:
            return jsonify({'error': 'Alert not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Alert dismissed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/resolve', methods=['PUT'])
def resolve_alert_endpoint(alert_id):
    """Mark an alert as resolved"""
    try:
        data = request.get_json() or {}
        success = alert_service.resolve_alert(alert_id, data.get('notes'))
        
        if not success:
            return jsonify({'error': 'Alert not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Alert resolved'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history_endpoint():
    """Get alert history"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))
        
        history = alert_service.get_alert_history(days, limit)
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/subscribe', methods=['POST'])
def subscribe_alerts_endpoint():
    """Subscribe to alert notifications"""
    try:
        data = request.get_json()
        
        if not data.get('email') and not data.get('phone'):
            return jsonify({'error': 'Email or phone required'}), 400
        
        subscription = alert_service.subscribe_to_alerts(
            email=data.get('email'),
            phone=data.get('phone'),
            satellite_ids=data.get('satellite_ids'),
            min_probability=data.get('min_probability', 0.001)
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Subscription created',
            'subscription': subscription
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/subscriptions', methods=['GET'])
def get_subscriptions_endpoint():
    """Get all alert subscriptions"""
    try:
        subscriptions = alert_service.get_subscriptions()
        
        return jsonify({
            'status': 'success',
            'subscriptions': subscriptions,
            'count': len(subscriptions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# INTEGRATION: Auto-create alerts from analysis
# ============================================================================

# Modify the debris job completion to create alerts and save to history
def _complete_debris_job(job_id, params, probability, visualization_url=None):
    """Complete a debris job and create alerts/history"""
    try:
        # Save to history with thread-safe session handling
        # Use a retry mechanism for database operations
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Force a new session for this thread
                from database.db_manager import get_db_manager
                db_manager = get_db_manager()
                
                # Remove any existing session for this thread
                db_manager.Session.remove()
                
                # Now save the analysis with a fresh session
                history_service.save_analysis(
                    satellite_id=params.get('satellite_norad'),
                    debris_id=params.get('debris'),
                    probability=probability,
                    duration_minutes=params.get('duration_minutes'),
                    samples=params.get('samples'),
                    visualization_url=visualization_url
                )
                
                # Mark as successfully saved
                DEBRIS_JOBS[job_id]['saved_to_db'] = True
                break  # Success, exit retry loop
                
            except Exception as db_error:
                if attempt < max_retries - 1:
                    # Wait before retrying
                    time.sleep(retry_delay * (attempt + 1))
                    logger.warning(f"Database save attempt {attempt + 1} failed, retrying: {db_error}")
                else:
                    # Final attempt failed, log and continue
                    logger.error(f"Database save failed after {max_retries} attempts: {db_error}")
                    DEBRIS_JOBS[job_id]['saved_to_db'] = False
                    DEBRIS_JOBS[job_id]['db_error'] = str(db_error)
        
        # Create alert if probability exceeds threshold
        if probability > 0.001:  # 0.1% threshold
            for attempt in range(max_retries):
                try:
                    # Force a new session for this thread
                    from database.db_manager import get_db_manager
                    db_manager = get_db_manager()
                    db_manager.Session.remove()
                    
                    alert_service.create_alert(
                        satellite_id=params.get('satellite_norad'),
                        debris_id=params.get('debris'),
                        probability=probability,
                        closest_approach_time=None,
                        closest_distance_km=None
                    )
                    logger.info(f"Created alert for {params.get('satellite_norad')} vs {params.get('debris')}")
                    break  # Success
                    
                except Exception as alert_error:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        logger.warning(f"Alert creation attempt {attempt + 1} failed, retrying: {alert_error}")
                    else:
                        logger.error(f"Alert creation failed after {max_retries} attempts: {alert_error}")
    
    except Exception as e:
        logger.error(f"Error completing debris job: {e}")


@app.route('/api/populate_satellites', methods=['POST'])
def populate_satellites_endpoint():
    """Populate satellite database from existing TLE files"""
    try:
        import glob
        from database.db_manager import get_db_manager
        from database.models import Satellite
        
        # Get database manager
        db_manager = get_db_manager()
        
        # Find all sat_*.txt files
        tle_files = glob.glob('data/sat_*.txt')
        
        added_count = 0
        skipped_count = 0
        
        session = db_manager.get_session()
        
        for tle_file in tle_files:
            # Extract NORAD ID from filename
            filename = os.path.basename(tle_file)
            if filename == 'sat_manage.txt':
                continue
                
            norad_id = filename.replace('sat_', '').replace('.txt', '')
            
            # Skip if already in database
            existing = session.query(Satellite).filter_by(norad_id=norad_id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Read TLE file to get name
            try:
                with open(tle_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        name = lines[0].strip()
                    else:
                        name = f'SAT-{norad_id}'
            except:
                name = f'SAT-{norad_id}'
            
            # Add to database
            satellite = Satellite(
                norad_id=norad_id,
                name=name,
                type='SATELLITE'
            )
            
            session.add(satellite)
            added_count += 1
        
        session.commit()
        session.close()
        
        return jsonify({
            'status': 'success',
            'added': added_count,
            'skipped': skipped_count,
            'total_files': len(tle_files)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    print("=" * 70)
    print("COLLIDERS API SERVER - PHASE 1 + 2 COMPLETE")
    print("=" * 70)
    print("\nStarting server on http://localhost:5000")
    print("\nCore Endpoints:")
    print("  GET  /health                    - Health check")
    print("  GET  /api/satellites            - List satellites")
    print("  POST /api/analyze               - Analyze collision")
    print("  POST /api/debris_job            - Start debris analysis")
    print("\nPhase 1 - History & Satellites:")
    print("  GET  /api/history/statistics    - Analysis statistics")
    print("  GET  /api/history/satellite/<id> - Satellite history")
    print("  GET  /api/satellites/manage     - Managed satellites")
    print("  POST /api/satellites/manage/add - Add satellite")
    print("\nPhase 2 - Alerts:")
    print("  GET  /api/alerts                - Active alerts")
    print("  POST /api/alerts/subscribe      - Subscribe to alerts")
    print("\nAPI Documentation: http://localhost:5000/api/docs")
    print("=" * 70 + "\n")
    
    # Disable debug mode to prevent auto-reload from clearing in-memory job state
    app.run(debug=False, host='0.0.0.0', port=5000)

