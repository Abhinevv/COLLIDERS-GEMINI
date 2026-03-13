"""
3D Orbit Visualization
Display satellite trajectories and collision scenarios
Enhanced with modern dashboard UI
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils
import numpy as np
from datetime import datetime
import json

class OrbitVisualizer:
    """Create 3D visualizations of orbits and collision scenarios"""
    
    def __init__(self, earth_radius=6371.0):
        """
        Initialize visualizer
        
        Args:
            earth_radius: Earth radius in km
        """
        self.earth_radius = earth_radius
        self.fig = None
    
    def create_earth_sphere(self):
        """
        Create enhanced 3D Earth sphere for visualization
        
        Returns:
            go.Surface: Plotly surface object for Earth
        """
        # Create sphere coordinates with higher resolution
        u = np.linspace(0, 2 * np.pi, 60)
        v = np.linspace(0, np.pi, 60)
        x = self.earth_radius * np.outer(np.cos(u), np.sin(v))
        y = self.earth_radius * np.outer(np.sin(u), np.sin(v))
        z = self.earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
        
        # Create custom colorscale for Earth (blue-green gradient)
        earth_colorscale = [
            [0, 'rgb(20, 50, 100)'],      # Deep ocean blue
            [0.3, 'rgb(30, 80, 150)'],    # Ocean blue
            [0.6, 'rgb(50, 120, 180)'],   # Light blue
            [0.8, 'rgb(70, 150, 200)'],   # Sky blue
            [1, 'rgb(100, 180, 220)']     # Bright blue
        ]
        
        earth = go.Surface(
            x=x, y=y, z=z,
            colorscale=earth_colorscale,
            showscale=False,
            name='Earth',
            opacity=0.85,
            hoverinfo='skip',
            lighting=dict(
                ambient=0.4,
                diffuse=0.8,
                specular=0.2,
                roughness=0.5
            ),
            lightposition=dict(x=100, y=100, z=100)
        )
        
        return earth
    
    def extract_trajectory_coords(self, trajectory):
        """
        Extract x, y, z coordinates from trajectory
        
        Args:
            trajectory: List of state dicts
        
        Returns:
            tuple: (x, y, z) arrays
        """
        x = [state['position'][0] for state in trajectory]
        y = [state['position'][1] for state in trajectory]
        z = [state['position'][2] for state in trajectory]
        
        return np.array(x), np.array(y), np.array(z)
    
    def plot_single_orbit_with_risk(self, trajectory, name="Satellite", base_color='cyan', distances=None, min_idx=-1):
        """
        Plot orbit with color coding based on collision risk
        
        Args:
            trajectory: List of states
            name: Trajectory name
            base_color: Base color for orbit
            distances: List of distances at each point
            min_idx: Index of minimum distance
        
        Returns:
            go.Scatter3d: Plotly scatter object
        """
        x, y, z = self.extract_trajectory_coords(trajectory)
        
        # Calculate altitudes
        altitudes = np.array([np.linalg.norm([x[i], y[i], z[i]]) - self.earth_radius for i in range(len(x))])
        
        # Color code markers based on distance if provided
        if distances and len(distances) == len(x):
            marker_colors = []
            for i, dist in enumerate(distances):
                if i == min_idx:
                    marker_colors.append('yellow')  # Closest point
                elif dist < 5.0:
                    marker_colors.append('red')  # Danger zone
                elif dist < 20.0:
                    marker_colors.append('orange')  # Warning zone
                else:
                    marker_colors.append(base_color)  # Safe
            # Use base color for line, markers will show risk
            line_color = base_color
        else:
            marker_colors = base_color
            line_color = base_color
        
        orbit_trace = go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines+markers',
            name=name,
            line=dict(
                color=line_color,
                width=4
            ),
            marker=dict(
                size=4 if isinstance(marker_colors, list) else 3,
                color=marker_colors,
                opacity=0.8 if isinstance(marker_colors, list) else 0.6,
                line=dict(width=0.5, color='white')
            ),
            customdata=altitudes,
            hovertemplate=f'<b>{name}</b><br>' +
                         f'Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>' +
                         f'Altitude: %{{customdata:.1f}} km<br>' +
                         '<extra></extra>',
            showlegend=True
        )
        
        return orbit_trace
    
    def plot_single_orbit(self, trajectory, name="Satellite", color='cyan'):
        """
        Plot a single orbit trajectory with enhanced styling
        
        Args:
            trajectory: List of states
            name: Trajectory name
            color: Line color
        
        Returns:
            go.Scatter3d: Plotly scatter object
        """
        x, y, z = self.extract_trajectory_coords(trajectory)
        
        # Calculate altitudes for hover info
        altitudes = np.array([np.linalg.norm([x[i], y[i], z[i]]) - self.earth_radius for i in range(len(x))])
        
        orbit_trace = go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines+markers',
            name=name,
            line=dict(
                color=color,
                width=4
            ),
            marker=dict(
                size=3,
                color=color,
                opacity=0.6,
                line=dict(width=0.5, color='white')
            ),
            customdata=altitudes,
            hovertemplate=f'<b>{name}</b><br>' +
                         f'Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>' +
                         f'Altitude: %{{customdata:.1f}} km<br>' +
                         '<extra></extra>',
            showlegend=True
        )
        
        return orbit_trace
    
    def _add_collision_zones(self, close_approach_event):
        """Add visual collision risk zones"""
        pos1 = close_approach_event['position1']
        distance = close_approach_event.get('distance', 10.0)
        
        # Add warning sphere for danger zone (5 km radius)
        if distance < 5.0:
            self._add_warning_sphere(pos1, 5.0, 'rgba(255, 0, 0, 0.1)', 'Danger Zone (5 km)')
        
        # Add warning sphere for alert zone (20 km radius)
        if distance < 20.0:
            self._add_warning_sphere(pos1, 20.0, 'rgba(255, 165, 0, 0.05)', 'Alert Zone (20 km)')
    
    def _add_warning_sphere(self, center, radius, color='rgba(255, 255, 0, 0.2)', name='Warning Zone'):
        """Add a semi-transparent sphere showing danger zone"""
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        x = center[0] + radius * np.outer(np.cos(u), np.sin(v))
        y = center[1] + radius * np.outer(np.sin(u), np.sin(v))
        z = center[2] + radius * np.outer(np.ones(np.size(u)), np.cos(v))
        
        self.fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            name=name,
            opacity=0.3,
            hoverinfo='skip'
        ))
    
    def _add_distance_visualization(self, traj1, traj2, distances, min_idx):
        """Add visualization showing distance between objects over time"""
        if min_idx < 0 or not distances:
            return
        
        # Add markers at key points
        key_indices = [0, min_idx, len(distances)-1]
        for idx in key_indices:
            if 0 <= idx < len(traj1) and 0 <= idx < len(traj2):
                pos1 = traj1[idx]['position']
                pos2 = traj2[idx]['position']
                dist = distances[idx]
                
                # Draw line between objects
                self.fig.add_trace(go.Scatter3d(
                    x=[pos1[0], pos2[0]],
                    y=[pos1[1], pos2[1]],
                    z=[pos1[2], pos2[2]],
                    mode='lines',
                    name=f'Distance: {dist:.1f} km' if idx == min_idx else None,
                    line=dict(
                        color='rgba(255, 255, 255, 0.3)' if idx != min_idx else 'yellow',
                        width=2 if idx != min_idx else 3,
                        dash='dot' if idx != min_idx else 'solid'
                    ),
                    showlegend=(idx == min_idx),
                    hovertemplate=f'Distance: {dist:.2f} km<br>Time: {traj1[idx]["time"]}<extra></extra>'
                ))
    
    def plot_collision_scenario(self, traj1, traj2, close_approach_event=None,
                                name1="Satellite", name2="Debris"):
        """
        Visualize collision scenario with two orbits and collision indicators
        Enhanced with better visual context and understanding
        
        Args:
            traj1: Trajectory of first object
            traj2: Trajectory of second object
            close_approach_event: Optional event dict with collision point
            name1: Name of first object
            name2: Name of second object
        
        Returns:
            go.Figure: Complete plotly figure
        """
        # Create figure
        self.fig = go.Figure()
        
        # Add Earth with enhanced appearance
        earth = self.create_earth_sphere()
        self.fig.add_trace(earth)
        
        # Add equatorial plane for reference
        theta = np.linspace(0, 2*np.pi, 100)
        equator_radius = self.earth_radius * 1.5
        self.fig.add_trace(go.Scatter3d(
            x=equator_radius * np.cos(theta),
            y=equator_radius * np.sin(theta),
            z=np.zeros_like(theta),
            mode='lines',
            name='Equatorial Plane',
            line=dict(color='rgba(255, 255, 255, 0.2)', width=1, dash='dot'),
            showlegend=True,
            hoverinfo='skip'
        ))
        
        # Add coordinate axes for reference
        axis_length = self.earth_radius * 2
        # X-axis (red)
        self.fig.add_trace(go.Scatter3d(
            x=[0, axis_length], y=[0, 0], z=[0, 0],
            mode='lines',
            name='X-axis (0° Longitude)',
            line=dict(color='rgba(255, 100, 100, 0.3)', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
        # Y-axis (green)
        self.fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, axis_length], z=[0, 0],
            mode='lines',
            name='Y-axis (90° E)',
            line=dict(color='rgba(100, 255, 100, 0.3)', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
        # Z-axis (blue) - North Pole
        self.fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, axis_length],
            mode='lines',
            name='Z-axis (North Pole)',
            line=dict(color='rgba(100, 100, 255, 0.3)', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
        
        # Calculate distances between trajectories at each time step
        distances = []
        min_distance = float('inf')
        min_distance_idx = -1
        
        min_len = min(len(traj1), len(traj2))
        for i in range(min_len):
            pos1 = traj1[i]['position']
            pos2 = traj2[i]['position']
            dist = np.linalg.norm(pos1 - pos2)
            distances.append(dist)
            if dist < min_distance:
                min_distance = dist
                min_distance_idx = i
        
        # Add orbits with color coding based on collision risk
        orbit1 = self.plot_single_orbit_with_risk(traj1, name1, 'cyan', distances, min_distance_idx)
        orbit2 = self.plot_single_orbit_with_risk(traj2, name2, 'red', distances, min_distance_idx)
        
        self.fig.add_trace(orbit1)
        self.fig.add_trace(orbit2)
        
        # Add start/end markers for better orientation
        # Start point (green sphere)
        start1 = traj1[0]['position']
        self.fig.add_trace(go.Scatter3d(
            x=[start1[0]], y=[start1[1]], z=[start1[2]],
            mode='markers',
            name=f'{name1} Start',
            marker=dict(size=8, color='lime', symbol='diamond'),
            showlegend=True,
            hovertemplate=f'<b>{name1} Start Position</b><br>Time: {traj1[0]["time"]}<extra></extra>'
        ))
        
        start2 = traj2[0]['position']
        self.fig.add_trace(go.Scatter3d(
            x=[start2[0]], y=[start2[1]], z=[start2[2]],
            mode='markers',
            name=f'{name2} Start',
            marker=dict(size=8, color='orange', symbol='diamond'),
            showlegend=True,
            hovertemplate=f'<b>{name2} Start Position</b><br>Time: {traj2[0]["time"]}<extra></extra>'
        ))
        
        # Add collision risk zones (spheres showing danger areas)
        if close_approach_event:
            self._add_collision_zones(close_approach_event)
        
        # Add distance visualization between trajectories
        if min_len > 0:
            self._add_distance_visualization(traj1, traj2, distances, min_distance_idx)
            
            # Add closest approach marker
            if min_distance_idx >= 0:
                pos1_closest = traj1[min_distance_idx]['position']
                pos2_closest = traj2[min_distance_idx]['position']
                
                # Add large marker at closest approach (use 'diamond' instead of 'star' for 3D)
                self.fig.add_trace(go.Scatter3d(
                    x=[pos1_closest[0]], y=[pos1_closest[1]], z=[pos1_closest[2]],
                    mode='markers',
                    name=f'Closest Approach: {min_distance:.2f} km',
                    marker=dict(size=12, color='yellow', symbol='diamond', 
                               line=dict(color='white', width=2)),
                    showlegend=True,
                    hovertemplate=f'<b>Closest Approach Point</b><br>' +
                                 f'Distance: {min_distance:.2f} km<br>' +
                                 f'Time: {traj1[min_distance_idx]["time"]}<extra></extra>'
                ))
        
        # Add close approach point if provided
        if close_approach_event:
            pos1 = close_approach_event['position1']
            pos2 = close_approach_event['position2']
            distance = close_approach_event.get('distance', min_distance)
            
            # Mark positions at closest approach with larger markers
            self.fig.add_trace(go.Scatter3d(
                x=[pos1[0]], y=[pos1[1]], z=[pos1[2]],
                mode='markers',
                name=f'{name1} at Closest Approach',
                marker=dict(size=15, color='yellow', symbol='diamond', line=dict(width=2, color='orange')),
                hovertemplate=f'<b>{name1} at Closest Approach</b><br>' +
                             f'Position: ({pos1[0]:.1f}, {pos1[1]:.1f}, {pos1[2]:.1f}) km<br>' +
                             f'Distance: {distance:.3f} km<br>' +
                             '<extra></extra>'
            ))
            
            self.fig.add_trace(go.Scatter3d(
                x=[pos2[0]], y=[pos2[1]], z=[pos2[2]],
                mode='markers',
                name=f'{name2} at Closest Approach',
                marker=dict(size=15, color='orange', symbol='diamond', line=dict(width=2, color='red')),
                hovertemplate=f'<b>{name2} at Closest Approach</b><br>' +
                             f'Position: ({pos2[0]:.1f}, {pos2[1]:.1f}, {pos2[2]:.1f}) km<br>' +
                             f'Distance: {distance:.3f} km<br>' +
                             '<extra></extra>'
            ))
            
            # Draw line between objects at close approach
            self.fig.add_trace(go.Scatter3d(
                x=[pos1[0], pos2[0]],
                y=[pos1[1], pos2[1]],
                z=[pos1[2], pos2[2]],
                mode='lines',
                name='Separation Distance',
                line=dict(color='yellow', width=4, dash='dash'),
                hovertemplate=f'<b>Separation: {distance:.3f} km</b><extra></extra>'
            ))
            
            # Add collision warning sphere if too close
            if distance < 10.0:  # Less than 10 km
                self._add_warning_sphere(pos1, distance)
        
        # Add current positions (start of trajectory)
        if len(traj1) > 0 and len(traj2) > 0:
            self.fig.add_trace(go.Scatter3d(
                x=[traj1[0]['position'][0]], 
                y=[traj1[0]['position'][1]], 
                z=[traj1[0]['position'][2]],
                mode='markers',
                name=f'{name1} Start',
                marker=dict(size=8, color='lime', symbol='circle', line=dict(width=1, color='white')),
                hovertemplate=f'<b>{name1} Start Position</b><br>Time: {traj1[0]["time"]}<extra></extra>'
            ))
            
            self.fig.add_trace(go.Scatter3d(
                x=[traj2[0]['position'][0]], 
                y=[traj2[0]['position'][1]], 
                z=[traj2[0]['position'][2]],
                mode='markers',
                name=f'{name2} Start',
                marker=dict(size=8, color='magenta', symbol='circle', line=dict(width=1, color='white')),
                hovertemplate=f'<b>{name2} Start Position</b><br>Time: {traj2[0]["time"]}<extra></extra>'
            ))
        
        # Enhanced layout settings with better styling and annotations
        self.fig.update_layout(
            title={
                'text': f'<b>Orbital Collision Scenario - 3D View</b><br>' +
                       f'<sub>Minimum Distance: {min_distance:.2f} km | ' +
                       f'{name1} (Cyan) vs {name2} (Red)</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 22, 'color': '#88c9f0', 'family': 'Arial, sans-serif'}
            },
            scene=dict(
                xaxis=dict(
                    title=dict(text='X (km) → 0° Longitude', font=dict(size=12, color='#88c9f0')),
                    backgroundcolor='rgb(15, 15, 35)',
                    gridcolor='rgba(136, 201, 240, 0.2)',
                    showbackground=True,
                    zerolinecolor='rgba(136, 201, 240, 0.3)',
                    range=[-axis_length, axis_length]
                ),
                yaxis=dict(
                    title=dict(text='Y (km) → 90° E Longitude', font=dict(size=12, color='#88c9f0')),
                    backgroundcolor='rgb(15, 15, 35)',
                    gridcolor='rgba(136, 201, 240, 0.2)',
                    showbackground=True,
                    zerolinecolor='rgba(136, 201, 240, 0.3)',
                    range=[-axis_length, axis_length]
                ),
                zaxis=dict(
                    title=dict(text='Z (km) → North Pole', font=dict(size=12, color='#88c9f0')),
                    backgroundcolor='rgb(15, 15, 35)',
                    gridcolor='rgba(136, 201, 240, 0.2)',
                    showbackground=True,
                    zerolinecolor='rgba(136, 201, 240, 0.3)',
                    range=[-axis_length, axis_length]
                ),
                bgcolor='rgb(10, 10, 25)',
                aspectmode='cube',  # Changed to cube for better perspective
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.5),  # Better viewing angle
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)  # Z-axis points up
                )
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0', family='Arial, sans-serif'),
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(0, 0, 0, 0.7)',
                bordercolor='rgba(136, 201, 240, 0.5)',
                borderwidth=2,
                font=dict(size=11, color='#e0e0e0'),
                title=dict(text='<b>Legend</b>', font=dict(size=13, color='#88c9f0'))
            ),
            height=900,
            margin=dict(l=0, r=0, t=80, b=0),
            annotations=[
                dict(
                    text='<b>Interactive Controls:</b><br>' +
                         '• Drag to rotate<br>' +
                         '• Scroll to zoom<br>' +
                         '• Hover for details',
                    xref='paper', yref='paper',
                    x=0.98, y=0.02,
                    xanchor='right', yanchor='bottom',
                    showarrow=False,
                    bgcolor='rgba(0, 0, 0, 0.7)',
                    bordercolor='rgba(136, 201, 240, 0.5)',
                    borderwidth=1,
                    font=dict(size=10, color='#88c9f0')
                )
            ]
        )
        
        return self.fig
    
    def plot_maneuver_comparison(self, traj_original, traj_after_maneuver, 
                                 debris_traj, maneuver_point=None):
        """
        Visualize orbit before and after avoidance maneuver
        
        Args:
            traj_original: Original trajectory
            traj_after_maneuver: Trajectory after maneuver
            debris_traj: Debris trajectory
            maneuver_point: Position where maneuver executed
        
        Returns:
            go.Figure: Plotly figure
        """
        self.fig = go.Figure()
        
        # Add Earth
        earth = self.create_earth_sphere()
        self.fig.add_trace(earth)
        
        # Original trajectory (dashed)
        orbit_original = self.plot_single_orbit(
            traj_original, "Original Path", 'rgba(0, 255, 255, 0.5)'
        )
        orbit_original.line.dash = 'dash'
        self.fig.add_trace(orbit_original)
        
        # New trajectory after maneuver
        orbit_new = self.plot_single_orbit(
            traj_after_maneuver, "Safe Path", 'lime'
        )
        self.fig.add_trace(orbit_new)
        
        # Debris trajectory
        debris = self.plot_single_orbit(debris_traj, "Debris", 'red')
        self.fig.add_trace(debris)
        
        # Mark maneuver point
        if maneuver_point is not None:
            self.fig.add_trace(go.Scatter3d(
                x=[maneuver_point[0]], 
                y=[maneuver_point[1]], 
                z=[maneuver_point[2]],
                mode='markers',
                name='Maneuver Point',
                marker=dict(size=10, color='yellow', symbol='diamond'),
                hovertemplate='Burn executed here<extra></extra>'
            ))
        
        # Layout
        self.fig.update_layout(
            title={
                'text': 'Collision Avoidance Maneuver - Before & After',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            scene=dict(
                xaxis=dict(title='X (km)', backgroundcolor='rgb(20, 20, 40)', gridcolor='gray'),
                yaxis=dict(title='Y (km)', backgroundcolor='rgb(20, 20, 40)', gridcolor='gray'),
                zaxis=dict(title='Z (km)', backgroundcolor='rgb(20, 20, 40)', gridcolor='gray'),
                bgcolor='rgb(10, 10, 30)',
                aspectmode='data'
            ),
            paper_bgcolor='rgb(10, 10, 30)',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(x=0.7, y=0.9),
            height=800
        )
        
        return self.fig
    
    def create_dashboard_html(self, analysis_result=None, filename='output/collision_scenario.html', 
                              satellite_info1=None, satellite_info2=None):
        """
        Create enhanced HTML dashboard with multiple visualizations and statistics
        
        Args:
            analysis_result: Analysis results dict (optional)
            filename: Output HTML file path
            satellite_info1: Satellite information dict for first object
            satellite_info2: Satellite information dict for second object
        """
        if not self.fig:
            print("⚠ No figure to save")
            return
        
        # Extract data for statistics
        stats_html = self._generate_stats_html(analysis_result, satellite_info1, satellite_info2)
        
        # Generate collision indicator
        safe = analysis_result.get('safe', True) if analysis_result else True
        collision_indicator = f"""
        <div class="collision-indicator {'safe' if safe else 'danger'}">
            {'✓ NO COLLISION RISK - Objects will safely pass each other' if safe else '⚠ COLLISION RISK DETECTED - Immediate action required'}
        </div>
        """
        
        # Convert figure to JSON for embedding
        fig_json = json.dumps(self.fig.to_dict(), cls=plotly.utils.PlotlyJSONEncoder)
        
        # Create enhanced HTML with dashboard layout
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AstroCleanAI - Collision Avoidance Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .dashboard-container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 25px;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 150, 255, 0.3);
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #88c9f0;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #fff;
            margin-bottom: 5px;
        }}
        
        .stat-card .unit {{
            font-size: 0.9em;
            color: #aaa;
        }}
        
        .stat-card.safe {{
            border-left: 4px solid #4caf50;
        }}
        
        .stat-card.warning {{
            border-left: 4px solid #ff9800;
        }}
        
        .stat-card.danger {{
            border-left: 4px solid #f44336;
        }}
        
        .visualization-container {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .visualization-container h2 {{
            margin-bottom: 20px;
            color: #88c9f0;
            font-size: 1.5em;
        }}
        
        .plot-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 0.9em;
        }}
        
        .timestamp {{
            text-align: center;
            color: #888;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .info-section {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .info-section h2 {{
            color: #88c9f0;
            margin-bottom: 25px;
            font-size: 1.8em;
            text-align: center;
        }}
        
        .satellite-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
        }}
        
        .satellite-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(136, 201, 240, 0.3);
            border-radius: 12px;
            padding: 25px;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .satellite-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(136, 201, 240, 0.3);
        }}
        
        .satellite-card h3 {{
            color: #88c9f0;
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
            border-bottom: 2px solid rgba(136, 201, 240, 0.3);
            padding-bottom: 10px;
        }}
        
        .info-grid {{
            display: grid;
            gap: 15px;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }}
        
        .info-label {{
            color: #aaa;
            font-weight: 500;
        }}
        
        .info-value {{
            color: #fff;
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .collision-indicator {{
            text-align: center;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .collision-indicator.safe {{
            background: rgba(76, 175, 80, 0.2);
            border: 2px solid #4caf50;
            color: #4caf50;
        }}
        
        .collision-indicator.danger {{
            background: rgba(244, 67, 54, 0.2);
            border: 2px solid #f44336;
            color: #f44336;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🛰️ AstroCleanAI</h1>
            <p>Satellite Collision Avoidance System Dashboard</p>
        </div>
        
        {stats_html}
        
        {collision_indicator}
        
        <div class="visualization-container">
            <h2>📊 3D Orbit Visualization</h2>
            <div class="plot-container" id="plotly-div"></div>
        </div>
        
        <div class="timestamp">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
        
        <div class="footer">
            <p>AstroCleanAI - Making space safer through intelligent collision avoidance</p>
        </div>
    </div>
    
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        // Embed Plotly figure
        var figureData = {fig_json};
        Plotly.newPlot('plotly-div', figureData.data, figureData.layout, {{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
            displaylogo: false,
            toImageButtonOptions: {{
                format: 'png',
                filename: 'orbit_visualization',
                height: 900,
                width: 1600,
                scale: 2
            }}
        }});
    </script>
</body>
</html>
"""
        
        # Save HTML file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Enhanced dashboard saved to: {filename}")
    
    def _generate_stats_html(self, analysis_result, satellite_info1=None, satellite_info2=None):
        """Generate statistics HTML from analysis results"""
        if not analysis_result:
            return """
        <div class="stats-grid">
            <div class="stat-card safe">
                <h3>Status</h3>
                <div class="value">✓ Safe</div>
                <div class="unit">No collision risk detected</div>
            </div>
            <div class="stat-card">
                <h3>Trajectory Points</h3>
                <div class="value">-</div>
                <div class="unit">Analysis in progress</div>
            </div>
        </div>
            """
        
        safe = analysis_result.get('safe', True)
        events = analysis_result.get('events', [])
        risk_assessment = analysis_result.get('risk_assessment', {})
        traj_sat, traj_debris = analysis_result.get('trajectories', ([], []))
        
        # Calculate statistics
        num_points = len(traj_sat) if traj_sat else 0
        num_events = len(events)
        
        if risk_assessment:
            distance = risk_assessment.get('distance', 0)
            probability = risk_assessment.get('probability_average', 0) * 100
            risk_category = risk_assessment.get('risk_category', 'UNKNOWN')
        else:
            distance = 0
            probability = 0
            risk_category = 'UNKNOWN'
        
        # Determine card classes
        status_class = 'safe' if safe else ('danger' if probability > 1 else 'warning')
        
        # Generate satellite information section
        satellite_info_html = self._generate_satellite_info_html(satellite_info1, satellite_info2)
        
        return f"""
        <div class="stats-grid">
            <div class="stat-card {status_class}">
                <h3>Collision Status</h3>
                <div class="value">{'✓ SAFE' if safe else '⚠ COLLISION RISK'}</div>
                <div class="unit">{risk_category if not safe else 'No collision detected'}</div>
            </div>
            <div class="stat-card">
                <h3>Trajectory Points</h3>
                <div class="value">{num_points}</div>
                <div class="unit">Points analyzed</div>
            </div>
            <div class="stat-card">
                <h3>Close Approaches</h3>
                <div class="value">{num_events}</div>
                <div class="unit">Events detected</div>
            </div>
            <div class="stat-card">
                <h3>Closest Distance</h3>
                <div class="value">{distance:.2f}</div>
                <div class="unit">km</div>
            </div>
            <div class="stat-card">
                <h3>Collision Probability</h3>
                <div class="value">{probability:.6f}</div>
                <div class="unit">%</div>
            </div>
        </div>
        {satellite_info_html}
        """
    
    def _generate_satellite_info_html(self, info1, info2):
        """Generate HTML for satellite information section"""
        if not info1 and not info2:
            return ""
        
        info_html = '<div class="info-section"><h2>🛰️ Satellite Information</h2><div class="satellite-cards">'
        
        for i, info in enumerate([info1, info2]):
            if not info:
                continue
            
            name = info.get('name', 'Unknown')
            norad_id = info.get('norad_id', 'N/A')
            inclination = info.get('inclination', None)
            altitude = info.get('mean_altitude', None)
            period = info.get('orbital_period', None)
            eccentricity = info.get('eccentricity', None)
            
            info_html += f"""
            <div class="satellite-card">
                <h3>{name}</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">NORAD ID:</span>
                        <span class="info-value">{norad_id}</span>
                    </div>
                    {f'<div class="info-item"><span class="info-label">Inclination:</span><span class="info-value">{inclination:.2f}°</span></div>' if inclination else ''}
                    {f'<div class="info-item"><span class="info-label">Mean Altitude:</span><span class="info-value">{altitude:.1f} km</span></div>' if altitude else ''}
                    {f'<div class="info-item"><span class="info-label">Orbital Period:</span><span class="info-value">{period:.1f} min</span></div>' if period else ''}
                    {f'<div class="info-item"><span class="info-label">Eccentricity:</span><span class="info-value">{eccentricity:.6f}</span></div>' if eccentricity else ''}
                </div>
            </div>
            """
        
        info_html += '</div></div>'
        return info_html
    
    def save_html(self, filename, analysis_result=None, satellite_info1=None, satellite_info2=None):
        """
        Save visualization to HTML file with enhanced dashboard
        
        Args:
            filename: Output HTML file path
            analysis_result: Optional analysis results for statistics
            satellite_info1: Satellite information for first object
            satellite_info2: Satellite information for second object
        """
        if self.fig:
            try:
                # Use enhanced dashboard if analysis_result provided
                if analysis_result:
                    self.create_dashboard_html(analysis_result, filename, satellite_info1, satellite_info2)
                else:
                    # Use include_plotlyjs='cdn' for faster loading
                    self.fig.write_html(
                        filename,
                        include_plotlyjs='cdn',
                        config={
                            'responsive': True,
                            'displayModeBar': True,
                            'displaylogo': False
                        }
                    )
                    print(f"✓ Visualization saved to: {filename}")
            except Exception as e:
                print(f"✗ Error saving visualization: {e}")
                # Fallback: save simple HTML
                try:
                    self.fig.write_html(filename, include_plotlyjs='cdn')
                    print(f"✓ Fallback visualization saved to: {filename}")
                except Exception as e2:
                    print(f"✗ Fallback also failed: {e2}")
    
    def show(self):
        """Display visualization in browser"""
        if self.fig:
            self.fig.show()


def main():
    """Test orbit visualization"""
    from propagation.propagate import OrbitPropagator
    from propagation.distance_check import CloseApproachDetector
    from datetime import datetime
    
    print("=" * 70)
    print("ORBIT VISUALIZATION TEST")
    print("=" * 70)
    
    # Load objects
    prop1 = OrbitPropagator('data/iss.txt')
    prop2 = OrbitPropagator('data/debris1.txt')
    
    # Generate trajectories
    start_time = datetime.utcnow()
    print(f"\nGenerating trajectories from: {start_time}")
    
    traj1 = prop1.propagate_trajectory(start_time, 90, 60)
    traj2 = prop2.propagate_trajectory(start_time, 90, 60)
    
    print(f"✓ Generated {len(traj1)} points for object 1")
    print(f"✓ Generated {len(traj2)} points for object 2")
    
    # Detect close approaches
    detector = CloseApproachDetector(threshold_km=1000.0)
    events = detector.check_trajectories(traj1, traj2)
    
    # Visualize
    visualizer = OrbitVisualizer()
    
    if events:
        closest = detector.find_closest_approach()
        print(f"\n✓ Closest approach: {closest['distance']:.2f} km")
        
        fig = visualizer.plot_collision_scenario(
            traj1, traj2, closest,
            name1=prop1.name, name2=prop2.name
        )
    else:
        print("\nNo close approaches detected, plotting orbits only")
        fig = visualizer.plot_collision_scenario(
            traj1, traj2,
            name1=prop1.name, name2=prop2.name
        )
    
    # Save to file
    visualizer.save_html('visualization/orbit_visualization.html')
    print("\n✓ You can open orbit_visualization.html in your browser")
    print("=" * 70)

if __name__ == "__main__":
    main()
