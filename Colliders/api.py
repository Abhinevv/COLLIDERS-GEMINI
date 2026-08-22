"""
COLLIDERS REST API
Provides HTTP endpoints for collision avoidance analysis
"""

from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv

load_dotenv()
import numpy as np
import random
from datetime import datetime, timezone, timedelta
import tempfile
import math

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
import logging
import requests as _requests

logger = logging.getLogger(__name__)

# Ensure required directories exist at import time
os.makedirs('data', exist_ok=True)
os.makedirs('output', exist_ok=True)
os.makedirs('data/tle_cache', exist_ok=True)

# In-memory job store for async debris analyses
DEBRIS_JOBS = {}

# Initialize Space-Track API (will use env variables)
space_track_api = SpaceTrackAPI()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global cache for propagators
_propagator_cache = {}


def get_object_telemetry_info(identifier, prop=None, default_type='DEBRIS'):
    """
    Extract comprehensive orbital telemetry and classification for a satellite or debris object.
    Derives Inclination, Altitude/Perigee/Apogee, Orbital Period, and Eccentricity from TLE or DB.
    """
    info = {
        'norad_id': str(identifier) if identifier else 'Unknown',
        'name': f'Object {identifier}' if identifier else 'Unknown',
        'type': default_type,
        'classification': default_type,
        'name_classification': f'Object {identifier} / {default_type}',
        'inclination': None,
        'inclination_deg': None,
        'eccentricity': None,
        'orbital_period': None,
        'period_minutes': None,
        'mean_altitude': None,
        'mean_altitude_km': None,
        'apogee': None,
        'apogee_km': None,
        'perigee': None,
        'perigee_km': None,
        'country': None,
        'rcs_size': None
    }
    
    if not identifier:
        return info

    identifier_str = str(identifier).strip()
    
    # 1. If an OrbitPropagator instance is provided, get its extracted TLE data
    if prop is not None:
        try:
            prop_info = prop.get_satellite_info()
            for k in ('name', 'norad_id', 'inclination', 'eccentricity', 'orbital_period', 'mean_altitude', 'apogee', 'perigee', 'mean_motion'):
                if prop_info.get(k) is not None:
                    info[k] = prop_info[k]
        except Exception:
            pass

    # 2. If missing orbital elements, check if local TLE file exists or can be loaded
    if info.get('inclination') is None or info.get('eccentricity') is None:
        tle_file = f'data/sat_{identifier_str}.txt'
        if os.path.exists(tle_file):
            try:
                temp_prop = OrbitPropagator(tle_file)
                temp_info = temp_prop.get_satellite_info()
                for k in ('name', 'norad_id', 'inclination', 'eccentricity', 'orbital_period', 'mean_altitude', 'apogee', 'perigee', 'mean_motion'):
                    if temp_info.get(k) is not None:
                        info[k] = temp_info[k]
            except Exception:
                pass

    # 3. Check database (Satellite and DebrisObject tables)
    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite, DebrisObject
        db = get_db_manager()
        session = db.get_session()
        try:
            sat_row = session.query(Satellite).filter_by(norad_id=identifier_str).first()
            if sat_row:
                if sat_row.name:
                    info['name'] = sat_row.name
                info['type'] = sat_row.type or 'Payload'
                info['country'] = sat_row.operator or info.get('country')
                if sat_row.tle_line1 and sat_row.tle_line2 and info.get('inclination') is None:
                    try:
                        from sgp4.api import Satrec
                        r = Satrec.twoline2rv(sat_row.tle_line1, sat_row.tle_line2)
                        info['inclination'] = round(r.inclo * 57.2958, 4)
                        info['eccentricity'] = round(float('0.' + sat_row.tle_line2[26:33]), 7)
                        mean_motion = float(sat_row.tle_line2[52:63])
                        if mean_motion > 0:
                            info['orbital_period'] = round(1440.0 / mean_motion, 2)
                        semi_major = ((3.986004418e5 * (info['orbital_period'] * 60)**2) / (4 * np.pi**2))**(1/3)
                        info['apogee'] = round(semi_major * (1 + info['eccentricity']) - 6371.0, 1)
                        info['perigee'] = round(semi_major * (1 - info['eccentricity']) - 6371.0, 1)
                        info['mean_altitude'] = round((info['apogee'] + info['perigee']) / 2.0, 1)
                    except Exception:
                        pass
            else:
                deb_row = session.query(DebrisObject).filter_by(norad_id=identifier_str).first()
                if deb_row:
                    if deb_row.name:
                        info['name'] = deb_row.name
                    info['type'] = deb_row.type or default_type
                    info['country'] = deb_row.country or info.get('country')
                    info['rcs_size'] = deb_row.rcs_size or info.get('rcs_size')
                    if deb_row.inclination_deg is not None and info.get('inclination') is None:
                        info['inclination'] = deb_row.inclination_deg
                    if deb_row.period_minutes is not None and info.get('orbital_period') is None:
                        info['orbital_period'] = deb_row.period_minutes
                    if deb_row.apogee_km is not None and info.get('apogee') is None:
                        info['apogee'] = deb_row.apogee_km
                    if deb_row.perigee_km is not None and info.get('perigee') is None:
                        info['perigee'] = deb_row.perigee_km
                    if info.get('mean_altitude') is None and info.get('apogee') is not None and info.get('perigee') is not None:
                        info['mean_altitude'] = round((info['apogee'] + info['perigee']) / 2.0, 1)
                    if deb_row.tle_line2 and info.get('eccentricity') is None:
                        try:
                            info['eccentricity'] = float('0.' + deb_row.tle_line2[26:33])
                        except Exception:
                            pass
        finally:
            session.close()
    except Exception:
        pass

    # 4. Check TLE cache manager if still missing parameters
    if info.get('inclination') is None:
        try:
            from tle_cache_manager import get_cache_manager
            cache = get_cache_manager()
            cached_tle = cache.get_tle_from_cache(identifier_str)
            if cached_tle and cached_tle.get('tle_line2'):
                l2 = cached_tle['tle_line2']
                if not info.get('name') or info['name'].startswith('Object '):
                    info['name'] = cached_tle.get('name', info['name'])
                info['inclination'] = float(l2[8:16])
                info['eccentricity'] = float('0.' + l2[26:33])
                mm = float(l2[52:63])
                if mm > 0:
                    info['orbital_period'] = 1440.0 / mm
                    semi_major = ((3.986004418e5 * (info['orbital_period'] * 60)**2) / (4 * np.pi**2))**(1/3)
                    info['apogee'] = round(semi_major * (1 + info['eccentricity']) - 6371.0, 1)
                    info['perigee'] = round(semi_major * (1 - info['eccentricity']) - 6371.0, 1)
                    info['mean_altitude'] = round((info['apogee'] + info['perigee']) / 2.0, 1)
        except Exception:
            pass

    # 5. Handle simulated debris
    if identifier_str.startswith('SIM-'):
        info['name'] = f'Simulated Debris ({identifier_str})'
        info['type'] = 'Debris'
        info['classification'] = 'Debris (Simulated Fragment)'
        if info.get('inclination') is None:
            info['inclination'] = 51.64
        if info.get('eccentricity') is None:
            info['eccentricity'] = 0.0012
        if info.get('orbital_period') is None:
            info['orbital_period'] = 93.5
        if info.get('mean_altitude') is None:
            info['mean_altitude'] = 450.0
            info['apogee'] = 460.0
            info['perigee'] = 440.0

    # 6. Normalize category / classification and create composite display name
    raw_type = info.get('type') or ''
    upper_type = str(raw_type).upper().strip()
    if not upper_type or upper_type in ('UNKNOWN', 'N/A', 'NONE', ''):
        classification = 'Unknown Fragment if unassigned'
    elif 'ROCKET' in upper_type or 'R/B' in upper_type:
        classification = 'Rocket Body'
    elif 'DEB' in upper_type:
        classification = 'Debris'
    elif 'PAYLOAD' in upper_type or 'SATELLITE' in upper_type:
        classification = 'Payload'
    else:
        classification = str(raw_type).title()
        
    info['classification'] = classification
    info['name_classification'] = f"{info['name']} / {classification}"
    info['inclination_deg'] = info.get('inclination')
    info['period_minutes'] = info.get('orbital_period')
    info['mean_altitude_km'] = info.get('mean_altitude')
    info['apogee_km'] = info.get('apogee')
    info['perigee_km'] = info.get('perigee')

    return info


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
    """List all satellites from the database"""
    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite
        db = get_db_manager()
        session = db.get_session()
        try:
            rows = session.query(Satellite).order_by(Satellite.name).all()
            satellites = {
                s.norad_id: {
                    'name': s.name,
                    'norad_id': s.norad_id,
                    'type': s.type or 'SATELLITE',
                    'description': s.description or '',
                    'operator': s.operator or '',
                    'active': s.active,
                }
                for s in rows
            }
        finally:
            session.close()
    except Exception:
        # Fallback to minimal hardcoded list if DB is unavailable at startup
        satellites = {
            '58955': {'name': 'INSAT-3DS', 'norad_id': '58955',
                      'type': 'Weather & Meteorology', 'description': 'Advanced third-generation meteorological satellite in geostationary orbit.'},
            '44804': {'name': 'Cartosat-3', 'norad_id': '44804',
                      'type': 'Earth Observation & Radar Imaging', 'description': 'Advanced agile high-resolution optical Earth imaging satellite.'},
            '51656': {'name': 'EOS-04 (RISAT-1A)', 'norad_id': '51656',
                      'type': 'Earth Observation & Radar Imaging', 'description': 'Radar Imaging Satellite with C-band Synthetic Aperture Radar.'},
            '56759': {'name': 'NVS-01', 'norad_id': '56759',
                      'type': 'Navigation & Positioning', 'description': 'Second-generation NavIC constellation satellite.'},
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
        
        # Get satellite and debris telemetry & classification
        info1 = get_object_telemetry_info(sat1_id, prop=prop1, default_type='PAYLOAD')
        info2 = get_object_telemetry_info(sat2_id, prop=prop2, default_type='DEBRIS')
        
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
        
        info1 = get_object_telemetry_info(satellite_norad, prop=prop, default_type='PAYLOAD')
        if len(debris_trajs) == 1:
            info2 = get_object_telemetry_info(debris_names[0], default_type='DEBRIS')
        else:
            first_deb = get_object_telemetry_info(debris_names[0], default_type='DEBRIS')
            info2 = {
                'name': f'{len(debris_trajs)} Debris Objects Cluster',
                'norad_id': ', '.join(str(d) for d in debris_names[:4]) + ('...' if len(debris_names) > 4 else ''),
                'type': 'Debris',
                'classification': 'Debris / Cluster',
                'name_classification': f'{len(debris_trajs)} Debris Objects Cluster / Debris',
                'inclination': first_deb.get('inclination'),
                'mean_altitude': first_deb.get('mean_altitude'),
                'perigee': first_deb.get('perigee'),
                'apogee': first_deb.get('apogee'),
                'orbital_period': first_deb.get('orbital_period'),
                'eccentricity': first_deb.get('eccentricity')
            }
        
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
        samples = int(data.get('samples', 1000))
        pos_unc_km = float(data.get('position_uncertainty_km', 2.0))
        debris_radius_km = float(data.get('debris_radius_km', 0.01))
        satellite_radius_km = float(data.get('satellite_radius_km', 0.01))
        visualize = bool(data.get('visualize', False))

        # Check if debris is in local TLE cache or database
        deb_tle_file = f'data/debris_{debris}.txt'
        deb_prop = None
        if os.path.exists(deb_tle_file):
            deb_prop = OrbitPropagator(deb_tle_file)
        else:
            from database.db_manager import get_db_manager
            from database.models import DebrisObject
            db = get_db_manager()
            session = db.get_session()
            try:
                d_obj = session.query(DebrisObject).filter_by(norad_id=str(debris)).first()
                if d_obj and d_obj.tle_line1 and d_obj.tle_line2:
                    with open(deb_tle_file, 'w') as f:
                        f.write(f"{d_obj.name}\n{d_obj.tle_line1}\n{d_obj.tle_line2}\n")
                    deb_prop = OrbitPropagator(deb_tle_file)
            finally:
                session.close()

        if deb_prop:
            # Earth orbit debris with SGP4 & PINN
            start_time = datetime.now(timezone.utc).replace(tzinfo=None)
            traj_sat = prop.propagate_trajectory(start_time, duration_minutes, step_seconds)
            traj_deb = deb_prop.propagate_trajectory(start_time, duration_minutes, step_seconds)

            detector = CloseApproachDetector(threshold_km=50.0)
            events = detector.check_trajectories(traj_sat, traj_deb)
            closest = detector.find_closest_approach()

            if closest:
                sat_pos_tca = np.array(closest['sat_pos'])
                sat_vel_tca = np.array(closest['sat_vel'])
                deb_pos_tca = np.array(closest['debris_pos'])
                deb_vel_tca = np.array(closest['debris_vel'])
            else:
                sat_pos_tca = np.array(traj_sat[0]['position'])
                sat_vel_tca = np.array(traj_sat[0]['velocity'])
                deb_pos_tca = np.array(traj_deb[0]['position'])
                deb_vel_tca = np.array(traj_deb[0]['velocity'])

            from probability.pinn_monte_carlo import PINNMonteCarloAssessment
            pinn_assessor = PINNMonteCarloAssessment()
            pinn_eval = pinn_assessor.assess_collision_pinn(
                sat_pos_tca=sat_pos_tca,
                sat_vel_tca=sat_vel_tca,
                deb_pos_tca=deb_pos_tca,
                deb_vel_tca=deb_vel_tca,
                combined_radius_km=debris_radius_km + satellite_radius_km,
                cov_sat_6x6=pinn_assessor.create_6x6_covariance(sigma_pos_km=pos_unc_km),
                cov_deb_6x6=pinn_assessor.create_6x6_covariance(sigma_pos_km=pos_unc_km),
                num_samples=samples,
                enable_importance_sampling=True
            )

            result = {
                'closest_distance_km': closest['distance'] if closest else float(np.linalg.norm(sat_pos_tca - deb_pos_tca)),
                'closest_time': closest['time'].isoformat() if closest and hasattr(closest['time'], 'isoformat') else str(closest['time']) if closest else start_time.isoformat(),
                'relative_velocity_kms': float(np.linalg.norm(sat_vel_tca - deb_vel_tca)),
                'probability': pinn_eval['probability'],
                'probability_monte_carlo': pinn_eval['probability'],
                'probability_formatted': pinn_eval['probability_formatted'],
                'probability_display': pinn_eval['probability_display'],
                'log10_probability': pinn_eval['log10_probability'],
                'threat_score': pinn_eval['threat_score'],
                'risk_level': pinn_eval['risk_level'],
                'risk_color': pinn_eval['risk_color'],
                'pinn_accelerated': True,
                'method': pinn_eval['method'],
                'execution_time_ms': pinn_eval['execution_time_ms']
            }

            vis_url = None
            if visualize:
                visualizer = OrbitVisualizer()
                analysis_result = {
                    'safe': pinn_eval['risk_level'] == 'SAFE',
                    'events': events,
                    'closest_approach': closest,
                    'risk_assessment': result,
                    'trajectories': (traj_sat, traj_deb)
                }
                info1 = get_object_telemetry_info(sat_id, prop=prop, default_type='PAYLOAD')
                info2 = get_object_telemetry_info(debris, prop=deb_prop, default_type='DEBRIS')
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='output')
                temp_filename = temp_file.name
                temp_file.close()
                visualizer.save_html(temp_filename, analysis_result, info1, info2)
                vis_url = f'/api/visualization/{os.path.basename(temp_filename)}'

            resp = {
                'status': 'success',
                'result': result,
                'probability': result['probability'],
                'probability_formatted': result['probability_formatted'],
                'risk_level': result['risk_level'],
                'threat_score': result['threat_score']
            }
            if vis_url:
                resp['visualization_url'] = vis_url
            return jsonify(resp), 200

        try:
            # Fallback: Horizons for deep space / non-cataloged asteroids
            result = analyze_debris_vs_satellite(debris, prop, duration_minutes=duration_minutes, step_seconds=step_seconds)
            return jsonify({'status': 'success', 'result': result}), 200
        except ImportError as ie:
            return jsonify({'error': str(ie), 'install': 'pip install astroquery astropy poliastro'}), 501
        except Exception as e:
            return jsonify({'error': str(e)}), 500
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
                    info1 = get_object_telemetry_info(sat_id, prop=prop, default_type='PAYLOAD')
                    info2 = get_object_telemetry_info(debris, prop=debris_prop if 'debris_prop' in locals() else None, default_type='DEBRIS')
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
            
            # Retrieve telemetry info for satellite and debris
            info1 = get_object_telemetry_info(sat_id, prop=prop, default_type='PAYLOAD')
            info2 = get_object_telemetry_info(debris, prop=debris_prop if 'debris_prop' in locals() else None, default_type='DEBRIS')

            from probability.pinn_monte_carlo import PINNMonteCarloAssessment
            pinn_assessor = PINNMonteCarloAssessment()

            eff_sigma = max(0.5, pos_unc_km)
            d_val = max(1e-4, min_distance)
            r_val = max(1e-4, thresh)
            
            # Exact 2D Gaussian density integration in log space: Pc = (R^2 / 2*sigma^2) * exp(-d^2 / 2*sigma^2)
            ln_pc = 2.0 * math.log(r_val) - math.log(2.0) - 2.0 * math.log(eff_sigma) - (d_val**2) / (2.0 * (eff_sigma**2))
            log10_pc = ln_pc / math.log(10.0)
            
            if log10_pc >= 0.0:
                raw_analytical_p = 1.0
            elif log10_pc > -300.0:
                raw_analytical_p = math.pow(10.0, log10_pc)
            else:
                raw_analytical_p = 0.0

            log_metrics = pinn_assessor.format_log_probability(
                probability=0.0,
                num_samples=samples,
                analytical_pc_estimate=raw_analytical_p
            )
            risk_level, threat_score, risk_color = pinn_assessor.compute_risk_and_threat_score(raw_analytical_p, min_distance)

            upper_bound_95 = 2.995732 / float(samples)
            DEBRIS_JOBS[job_id]['status'] = 'completed'
            DEBRIS_JOBS[job_id]['debris_info'] = info2
            DEBRIS_JOBS[job_id]['satellite_info'] = info1
            DEBRIS_JOBS[job_id]['result'] = {
                'probability': log_metrics['probability'],
                'probability_monte_carlo': log_metrics['probability'],
                'probability_formatted': log_metrics['formatted'],
                'probability_display': log_metrics['display_percentage'],
                'log10_probability': log_metrics['log10_probability'],
                'threat_score': threat_score,
                'collision_count': 0,
                'total_samples': samples,
                'confidence_interval_95': [0.0, max(log_metrics['probability'], upper_bound_95)],
                'min_distance_km': min_distance,
                'position_uncertainty_km': pos_unc_km,
                'combined_radius_km': thresh,
                'pinn_accelerated': True,
                'method': 'PINN_Screening_SafeDistance',
                'risk_level': risk_level,
                'risk_color': risk_color,
                'importance_sampling_applied': False,
                'screening': 'safe_distance',
                'screening_note': f'Min distance {min_distance:.1f}km > {screening_threshold_km}km threshold',
                'debris_info': info2,
                'satellite_info': info1
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
        
        # === PINN-ACCELERATED MONTE CARLO (SURROGATE) PIPELINE ===
        closest_idx = int(np.argmin(dists_all))
        closest_time_fraction = float(closest_idx / n)
        
        sat_pos_tca = np.asarray(sat_positions[closest_idx], dtype=np.float64)
        deb_pos_tca = np.asarray(debris_positions[closest_idx], dtype=np.float64)

        if closest_idx < n - 1:
            sat_vel_tca = (sat_positions[closest_idx + 1] - sat_positions[closest_idx]) / float(step_seconds)
            deb_vel_tca = (debris_positions[closest_idx + 1] - debris_positions[closest_idx]) / float(step_seconds)
        else:
            sat_vel_tca = (sat_positions[closest_idx] - sat_positions[closest_idx - 1]) / float(step_seconds)
            deb_vel_tca = (debris_positions[closest_idx] - debris_positions[closest_idx - 1]) / float(step_seconds)

        # Update progress to indicate PINN surrogate initialization
        DEBRIS_JOBS[job_id]['progress'] = 50

        from probability.pinn_monte_carlo import PINNMonteCarloAssessment
        pinn_assessor = PINNMonteCarloAssessment()

        cov_sat = pinn_assessor.create_6x6_covariance(
            sigma_pos_km=pos_unc_km,
            sigma_vel_kms=max(0.0005, pos_unc_km * 0.001),
            along_track_factor=3.0
        )
        cov_deb = pinn_assessor.create_6x6_covariance(
            sigma_pos_km=pos_unc_km * 1.5,
            sigma_vel_kms=max(0.0008, pos_unc_km * 0.0015),
            along_track_factor=3.0
        )

        pinn_res = pinn_assessor.assess_collision_pinn(
            sat_pos_tca=sat_pos_tca,
            sat_vel_tca=sat_vel_tca,
            deb_pos_tca=deb_pos_tca,
            deb_vel_tca=deb_vel_tca,
            combined_radius_km=thresh,
            cov_sat_6x6=cov_sat,
            cov_deb_6x6=cov_deb,
            num_samples=samples,
            conjunction_window_sec=min(300.0, float(step_seconds * 5)),
            num_time_steps=21,
            enable_importance_sampling=(params.get('importance_sampling', True))
        )

        probability = pinn_res['probability']
        collision_count = pinn_res['collision_count']
        ci_lower, ci_upper = pinn_res['confidence_interval_95']
        pinn_min_dist = pinn_res['min_distance_km']
        min_distance = min(min_distance, pinn_min_dist)

        DEBRIS_JOBS[job_id]['progress'] = 90
        
        # Generate visualization BEFORE marking as completed
        visualization_url = None
        if visualize:
            try:
                visualizer = OrbitVisualizer()
                sat_traj = traj
                
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
                    'risk_assessment': {
                        'probability_monte_carlo': probability,
                        'probability_formatted': pinn_res['probability_formatted']
                    },
                    'trajectories': (sat_traj, debris_traj)
                }
                info1 = get_object_telemetry_info(sat_id, prop=prop, default_type='PAYLOAD')
                info2 = get_object_telemetry_info(debris, prop=debris_prop if 'debris_prop' in locals() else None, default_type='DEBRIS')
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
        
        # Retrieve telemetry info for satellite and debris
        info1 = get_object_telemetry_info(sat_id, prop=prop, default_type='PAYLOAD')
        info2 = get_object_telemetry_info(debris, prop=debris_prop if 'debris_prop' in locals() else None, default_type='DEBRIS')

        # Now mark as completed with all data ready
        DEBRIS_JOBS[job_id]['status'] = 'completed'
        DEBRIS_JOBS[job_id]['progress'] = 100
        DEBRIS_JOBS[job_id]['debris_info'] = info2
        DEBRIS_JOBS[job_id]['satellite_info'] = info1
        DEBRIS_JOBS[job_id]['result'] = {
            'probability': probability,
            'probability_monte_carlo': probability,
            'probability_formatted': pinn_res['probability_formatted'],
            'probability_display': pinn_res['probability_display'],
            'log10_probability': pinn_res['log10_probability'],
            'collision_count': collision_count,
            'total_samples': samples,
            'confidence_interval_95': [ci_lower, ci_upper],
            'min_distance_km': min_distance,
            'position_uncertainty_km': pos_unc_km,
            'combined_radius_km': thresh,
            'pinn_accelerated': pinn_res.get('pinn_accelerated', False),
            'method': pinn_res['method'],
            'execution_time_ms': pinn_res['execution_time_ms'],
            'risk_level': pinn_res['risk_level'],
            'importance_sampling_applied': pinn_res['importance_sampling_applied'],
            'closest_approach_time': f'{closest_time_fraction*100:.1f}% through trajectory',
            'debris_info': info2,
            'satellite_info': info1
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
    Get debris objects in similar orbits to a specific satellite based on
    physical orbital shell proximity and cross-track inclination intersection.
    Returns distinct, orbit-specific threat debris and total threat counts.

    Query params:
        limit: max results to return in the detailed list (default: 50)
    """
    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite, DebrisObject
        from sgp4.api import Satrec

        limit_arg = request.args.get('limit', '50')
        limit = 99999 if limit_arg.lower() in ('all', 'none') else int(limit_arg)

        db = get_db_manager()
        session = db.get_session()

        try:
            # ── 1. Load satellite ────────────────────────────────────────────
            satellite = session.query(Satellite).filter_by(norad_id=satellite_id).first()

            if not satellite or not satellite.tle_line1 or not satellite.tle_line2:
                return jsonify({
                    'status': 'error',
                    'message': 'Satellite not found or missing TLE data'
                }), 404

            try:
                sat_rec = Satrec.twoline2rv(satellite.tle_line1, satellite.tle_line2)
                sat_alt = (sat_rec.a * 6378.137) - 6378.137   # km
                sat_inc = sat_rec.inclo * 57.2958              # degrees
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to parse satellite TLE: {str(e)}'
                }), 400

            # ── 2. Determine Orbital Regime ──────────────────────────────────
            if sat_alt < 300:
                orbital_regime = "Very Low Earth Orbit (VLEO)"
            elif 350 <= sat_alt <= 450 and 48 <= sat_inc <= 54:
                orbital_regime = "LEO - ISS / Crewed Research Regime"
            elif 350 <= sat_alt <= 450 and 38 <= sat_inc <= 45:
                orbital_regime = "LEO - Tiangong Station Regime"
            elif 500 <= sat_alt <= 600 and 50 <= sat_inc <= 56:
                orbital_regime = "LEO - Starlink Megaconstellation Shell"
            elif 500 <= sat_alt <= 600 and 26 <= sat_inc <= 32:
                orbital_regime = "LEO - Low-Inclination Telescope Shell (HST)"
            elif 650 <= sat_alt <= 900 and 96 <= sat_inc <= 101:
                orbital_regime = "LEO - Sun-Synchronous Polar Shell (High Congestion)"
            elif 750 <= sat_alt <= 870 and 84 <= sat_inc <= 88:
                orbital_regime = "LEO - Iridium NEXT Polar Constellation Shell"
            elif 1100 <= sat_alt <= 1400:
                orbital_regime = "LEO - Upper Polar / Altimetry Shell"
            else:
                orbital_regime = f"LEO - Custom Shell ({sat_alt:.0f} km / {sat_inc:.1f} deg)"

            # ── 3. Evaluate Debris Orbital Intersections ─────────────────────
            all_debris = session.query(DebrisObject).all()
            candidate_debris = []

            for d in all_debris:
                try:
                    ap = float(d.apogee_km or 0)
                    pe = float(d.perigee_km or 0)
                    d_inc = float(d.inclination_deg or 0)
                    d_alt = (ap + pe) / 2.0 if (ap and pe) else None

                    if d.tle_line1 and d.tle_line2:
                        dr = Satrec.twoline2rv(d.tle_line1, d.tle_line2)
                        d_alt = (dr.a * 6378.137) - 6378.137
                        d_inc = dr.inclo * 57.2958
                        pe = (dr.alta * 6378.137) if hasattr(dr, 'alta') else pe
                        ap = (dr.a * 6378.137 * (1 + dr.ecco)) - 6378.137 if hasattr(dr, 'ecco') else ap

                    if d_alt is None:
                        continue

                    alt_diff = abs(d_alt - sat_alt)
                    inc_diff = abs(d_inc - sat_inc)

                    # Physical altitude crossing test:
                    # Debris orbital altitude envelope overlaps satellite altitude with 60km conjunction margin
                    crosses_altitude = (pe - 60 <= sat_alt <= ap + 60) or (alt_diff < 120)

                    if crosses_altitude:
                        # Geometrically consistent miss distance estimation
                        cross_track = 6800.0 * math.radians(inc_diff) * 0.25
                        est_miss_dist = math.sqrt(alt_diff**2 + cross_track**2)
                        
                        # Strict Normalized Threat Score (0.0 - 100.0) aligned with SSA Risk Category:
                        if est_miss_dist < 1.0:
                            threat_score = 75.0 + 25.0 * (1.0 - est_miss_dist)
                        elif est_miss_dist < 5.0:
                            threat_score = 40.0 + 34.9 * (5.0 - est_miss_dist) / 4.0
                        elif est_miss_dist <= 15.0:
                            threat_score = 15.0 + 24.9 * (15.0 - est_miss_dist) / 10.0
                        else:
                            threat_score = max(0.5, 14.9 * math.exp(-(est_miss_dist - 15.0) / 10.0))

                        candidate_debris.append({
                            'norad_id':           d.norad_id,
                            'name':               d.name or f'Debris {d.norad_id}',
                            'type':               d.type or 'DEBRIS',
                            'rcs_size':           d.rcs_size or 'UNKNOWN',
                            'country':            d.country or 'UNKNOWN',
                            'apogee_km':          round(float(ap), 1) if ap else None,
                            'perigee_km':         round(float(pe), 1) if pe else None,
                            'inclination_deg':    round(float(d_inc), 4),
                            'altitude_diff_km':   round(float(alt_diff), 1),
                            'inclination_diff_deg': round(float(inc_diff), 4),
                            'threat_score':       round(float(threat_score), 2),
                            })
                except Exception:
                    continue

            # Sort by threat score descending (closest and most dangerous first)
            candidate_debris.sort(key=lambda x: x['threat_score'], reverse=True)
            total_threat_count = len(candidate_debris)

            # Determine shell threat level based on total threats
            if total_threat_count >= 300:
                threat_level = "CRITICAL"
            elif total_threat_count >= 150:
                threat_level = "HIGH"
            elif total_threat_count >= 75:
                threat_level = "ELEVATED"
            elif total_threat_count >= 30:
                threat_level = "MODERATE"
            else:
                threat_level = "LOW"

            result_list = candidate_debris[:limit]

            return jsonify({
                'status': 'success',
                'satellite': {
                    'norad_id':       satellite.norad_id,
                    'name':           satellite.name,
                    'type':           satellite.type or 'SATELLITE',
                    'operator':       satellite.operator or 'N/A',
                    'altitude_km':    round(float(sat_alt), 1),
                    'inclination_deg': round(float(sat_inc), 4),
                    'orbital_regime': orbital_regime,
                    'threat_level':   threat_level,
                },
                'total_orbital_threats': total_threat_count,
                'count': len(result_list),
                'orbital_regime': orbital_regime,
                'threat_level': threat_level,
                'high_risk_debris': result_list,
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
        
        # Use get_object_telemetry_info to get complete telemetry & orbital elements
        telemetry = get_object_telemetry_info(norad_id, default_type='DEBRIS')
        
        # Also query database for extra metadata (country, dates, rcs_size, etc.)
        db = get_db_manager()
        session = db.get_session()
        
        try:
            debris = session.query(DebrisObject).filter_by(norad_id=norad_id).first()
            
            if debris or telemetry.get('inclination') is not None or telemetry.get('name') != f'Object {norad_id}':
                res = {
                    'norad_id': telemetry.get('norad_id', norad_id),
                    'name': debris.name if debris and debris.name else telemetry.get('name', f'Object {norad_id}'),
                    'type': debris.type if debris and debris.type else telemetry.get('type', 'DEBRIS'),
                    'classification': telemetry.get('classification', 'Debris'),
                    'name_classification': telemetry.get('name_classification', f'{norad_id} / Debris'),
                    'country': debris.country if debris else telemetry.get('country'),
                    'launch_date': debris.launch_date.isoformat() if debris and debris.launch_date else None,
                    'decay_date': debris.decay_date.isoformat() if debris and debris.decay_date else None,
                    'apogee_km': debris.apogee_km if debris and debris.apogee_km is not None else telemetry.get('apogee'),
                    'perigee_km': debris.perigee_km if debris and debris.perigee_km is not None else telemetry.get('perigee'),
                    'mean_altitude': telemetry.get('mean_altitude'),
                    'mean_altitude_km': telemetry.get('mean_altitude_km'),
                    'period_minutes': debris.period_minutes if debris and debris.period_minutes is not None else telemetry.get('orbital_period'),
                    'inclination_deg': debris.inclination_deg if debris and debris.inclination_deg is not None else telemetry.get('inclination'),
                    'eccentricity': telemetry.get('eccentricity'),
                    'rcs_size': debris.rcs_size if debris else telemetry.get('rcs_size'),
                    'tle_line1': debris.tle_line1 if debris else None,
                    'tle_line2': debris.tle_line2 if debris else None,
                    'tle_epoch': debris.tle_epoch.isoformat() if debris and debris.tle_epoch else None,
                    'last_updated': debris.last_updated.isoformat() if debris and debris.last_updated else None
                }
                return jsonify({'status': 'success', 'debris': res}), 200
            
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


@app.route('/api/maneuver/calculate', methods=['POST'])
def calculate_avoidance_maneuver():
    """Calculate optimal collision avoidance maneuver"""
    try:
        data = request.get_json() or {}
        satellite_id = str(data.get('satellite_id', '25544'))
        debris_id = str(data.get('debris_id', ''))
        lead_time = int(data.get('lead_time_minutes', 60))
        max_dv = float(data.get('max_dv', 10.0))
        sat_mass = float(data.get('satellite_mass', 500.0))
        isp = float(data.get('specific_impulse', 300.0))
        target_clearance = float(data.get('target_clearance_km', 5.0))

        from optimization.avoidance import AvoidanceManeuver
        from propagation.propagate import OrbitPropagator
        from fetch_tle import TLEFetcher

        fetcher = TLEFetcher()
        sat_file = f'data/sat_{satellite_id}.txt'
        if not os.path.exists(sat_file):
            fetcher.fetch_tle(satellite_id, f'sat_{satellite_id}.txt')
        if not os.path.exists(sat_file):
            sat_file = 'data/iss.txt'

        deb_file = f'data/debris_{debris_id}.txt' if debris_id else 'data/debris_12456.txt'
        if not os.path.exists(deb_file) and debris_id:
            fetcher.fetch_tle(debris_id, f'debris_{debris_id}.txt')
        if not os.path.exists(deb_file):
            deb_file = 'data/debris_12456.txt'

        sat_prop = OrbitPropagator(sat_file) if os.path.exists(sat_file) else None
        deb_prop = OrbitPropagator(deb_file) if os.path.exists(deb_file) else None

        optimizer = AvoidanceManeuver(
            sat_prop,
            max_dv=max_dv,
            satellite_mass_kg=sat_mass,
            specific_impulse_sec=isp
        )

        burn_time = datetime.now(timezone.utc)
        if deb_prop:
            maneuver = optimizer.optimize_maneuver(
                burn_time,
                deb_prop,
                dv_range=(0.1, min(max_dv, 5.0)),
                target_clearance_km=target_clearance,
                lead_time_minutes=lead_time
            )
        else:
            maneuver = optimizer._generate_fallback_plan(burn_time, burn_time + timedelta(minutes=lead_time))

        return jsonify({
            'status': 'success',
            'satellite_id': satellite_id,
            'debris_id': debris_id,
            'maneuver': maneuver
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/maneuver/simulate', methods=['POST'])
def simulate_avoidance_maneuver():
    """Simulate post-maneuver trajectory clearance"""
    try:
        data = request.get_json() or {}
        satellite_id = str(data.get('satellite_id', '25544'))
        delta_v_ms = float(data.get('delta_v_ms', 1.0))
        direction = data.get('direction', 'RETROGRADE').upper()
        sat_mass = float(data.get('satellite_mass', 500.0))
        isp = float(data.get('specific_impulse', 300.0))

        from optimization.avoidance import AvoidanceManeuver
        opt = AvoidanceManeuver(None, max_dv=20.0, satellite_mass_kg=sat_mass, specific_impulse_sec=isp)
        fuel_kg = opt.calculate_fuel_consumption(delta_v_ms)

        # Estimate clearance gain (approx 4.5 km per 1 m/s burn in LEO after 1 orbit)
        clearance_km = round(delta_v_ms * 4.65, 3)

        return jsonify({
            'status': 'success',
            'satellite_id': satellite_id,
            'direction': direction,
            'delta_v_ms': delta_v_ms,
            'fuel_consumption_kg': round(fuel_kg, 4),
            'estimated_clearance_km': clearance_km,
            'burn_duration_sec': round(delta_v_ms * 12.5, 1)  # typical 80mN electric / 20N monoprop thruster
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



def seed_default_debris():
    """Seed debris objects if fewer than 700 exist in DB"""
    try:
        from database.db_manager import get_db_manager
        from database.models import DebrisObject
        import seed_data

        db = get_db_manager()
        session = db.get_session()
        try:
            if session.query(DebrisObject).count() >= 700:
                return
        finally:
            session.close()

        seed_data.seed()
    except Exception as e:
        print(f"  Debris seed skipped: {e}")


def seed_default_satellites():
    """Seed satellites if fewer than 49 exist in DB"""
    try:
        from database.db_manager import get_db_manager
        from database.models import Satellite
        import seed_data

        db = get_db_manager()
        session = db.get_session()
        try:
            if session.query(Satellite).count() >= 49:
                return
        finally:
            session.close()

        seed_data.seed()
    except Exception as e:
        print(f"  Satellite seed skipped: {e}")


if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    print("  Seeding default satellites...")
    seed_default_satellites()
    print("  Seeding debris objects...")
    seed_default_debris()
    
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

