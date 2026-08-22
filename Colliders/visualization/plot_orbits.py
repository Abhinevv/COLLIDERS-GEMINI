"""
3D Orbit Visualization
Display satellite trajectories and collision scenarios
Enhanced with dynamic 3D animation, comet trails, time scrubbing, and cinematic Earth rendering
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils
import numpy as np
from datetime import datetime, timezone
import json
import os


class OrbitVisualizer:
    """Create interactive 3D visualizations of orbits and collision scenarios with Plotly animations"""

    def __init__(self, earth_radius=6371.0):
        """
        Initialize visualizer
        
        Args:
            earth_radius: Earth radius in km
        """
        self.earth_radius = float(earth_radius)
        self.fig = None

    def create_earth_sphere(self, resolution=72):
        """
        Create cinematic 3D Earth sphere with realistic continental landmasses,
        oceanic trenches, shallow coastal shelves, polar ice caps, and atmospheric glow.
        
        Returns:
            go.Surface: Plotly surface object for Earth
        """
        # Spherical coordinate grid
        u = np.linspace(0, 2 * np.pi, resolution * 2)  # longitude (144)
        v = np.linspace(0, np.pi, resolution)          # colatitude (72)
        
        # Cartesian coordinates (shape 144, 72)
        x = self.earth_radius * np.outer(np.cos(u), np.sin(v))
        y = self.earth_radius * np.outer(np.sin(u), np.sin(v))
        z = self.earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))

        # 2D Grid for latitude and longitude
        lat_grid = np.pi / 2.0 - np.outer(np.ones_like(u), v)
        lon_grid = np.outer(u - np.pi, np.ones_like(v))
        
        # Multi-frequency harmonic representation of continents
        elevation = (
            0.42 * np.sin(lon_grid) * np.cos(lat_grid) +
            0.32 * np.cos(2.0 * lon_grid - 0.4) * (np.cos(lat_grid) ** 2) +
            0.28 * np.sin(3.0 * lon_grid + 1.1) * np.sin(lat_grid) +
            0.22 * np.cos(lat_grid) * np.cos(lon_grid - 0.9) +
            0.16 * np.sin(4.0 * lon_grid) * np.cos(2.0 * lat_grid)
        )
        # Polar ice cap intensification
        polar_mask = np.abs(lat_grid) > (np.pi * 0.38)
        elevation[polar_mask] = 1.25

        # Earth multi-layer color scale
        earth_colorscale = [
            [0.00, 'rgb(3, 14, 38)'],       # Deep Ocean Abyss
            [0.25, 'rgb(8, 48, 110)'],      # Ocean Blue
            [0.45, 'rgb(20, 105, 175)'],    # Continental Shelf / Azure
            [0.49, 'rgb(42, 165, 190)'],    # Shallow Coastal Turquoise
            [0.51, 'rgb(225, 200, 135)'],   # Coastline Sand
            [0.55, 'rgb(32, 108, 55)'],     # Lowland Forest Green
            [0.68, 'rgb(72, 148, 78)'],     # Highland Green Hills
            [0.80, 'rgb(135, 105, 75)'],    # Mountain Terrain Brown
            [0.90, 'rgb(185, 175, 165)'],   # Rocky Peaks
            [1.00, 'rgb(255, 255, 255)']    # Polar Snow & Ice
        ]

        earth = go.Surface(
            x=x, y=y, z=z,
            surfacecolor=elevation,
            colorscale=earth_colorscale,
            cmin=-1.0,
            cmax=1.3,
            showscale=False,
            name='Earth',
            opacity=0.96,
            hoverinfo='skip',
            lighting=dict(
                ambient=0.55,
                diffuse=0.85,
                specular=0.45,
                roughness=0.35,
                fresnel=0.3
            ),
            lightposition=dict(x=18000, y=24000, z=14000)
        )

        return earth

    def create_starfield(self, count=350, distance=24000.0):
        """
        Create background 3D starfield layer for deep space ambiance
        """
        rng = np.random.RandomState(42)
        phi = rng.uniform(0, np.pi, count)
        theta = rng.uniform(0, 2 * np.pi, count)
        r = distance + rng.uniform(-2500, 3500, count)
        
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        sizes = rng.uniform(1.2, 2.6, count)

        return go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            name='Starfield',
            marker=dict(
                size=sizes,
                color='rgba(235, 245, 255, 0.75)',
                opacity=0.75,
            ),
            hoverinfo='skip',
            showlegend=False
        )

    def extract_trajectory_coords(self, trajectory):
        """
        Extract x, y, z coordinates from trajectory
        
        Args:
            trajectory: List of state dicts
        
        Returns:
            tuple: (x, y, z) numpy arrays
        """
        x = [state['position'][0] for state in trajectory]
        y = [state['position'][1] for state in trajectory]
        z = [state['position'][2] for state in trajectory]
        return np.array(x, dtype=float), np.array(y, dtype=float), np.array(z, dtype=float)

    def plot_single_orbit_with_risk(self, trajectory, name="Satellite", base_color='#00f0ff', distances=None, min_idx=-1):
        """
        Plot static orbit path with subtle risk markers
        """
        x, y, z = self.extract_trajectory_coords(trajectory)
        altitudes = np.linalg.norm(np.column_stack((x, y, z)), axis=1) - self.earth_radius

        orbit_trace = go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            name=f'{name} (Full Orbit)',
            line=dict(
                color=base_color,
                width=2.5
            ),
            opacity=0.35,
            customdata=altitudes,
            hovertemplate=f'<b>{name} Orbit Path</b><br>' +
                         f'Pos: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>' +
                         f'Alt: %{{customdata:.1f}} km<br>' +
                         '<extra></extra>',
            showlegend=True
        )
        return orbit_trace

    def plot_single_orbit(self, trajectory, name="Satellite", color='#00f0ff'):
        """
        Plot a single orbit trajectory path
        """
        x, y, z = self.extract_trajectory_coords(trajectory)
        altitudes = np.linalg.norm(np.column_stack((x, y, z)), axis=1) - self.earth_radius

        orbit_trace = go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            name=name,
            line=dict(
                color=color,
                width=2.5
            ),
            opacity=0.45,
            customdata=altitudes,
            hovertemplate=f'<b>{name}</b><br>' +
                         f'Pos: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>' +
                         f'Alt: %{{customdata:.1f}} km<br>' +
                         '<extra></extra>',
            showlegend=True
        )
        return orbit_trace

    def _add_collision_zones(self, close_approach_event):
        """Add visual collision risk zones at close approach point"""
        pos1 = close_approach_event['position1']
        distance = close_approach_event.get('distance', 10.0)

        # Danger zone sphere (< 5 km)
        if distance < 5.0:
            self._add_warning_sphere(pos1, 5.0, 'rgba(255, 0, 85, 0.15)', 'Danger Zone (5 km)')
        # Alert zone sphere (< 20 km)
        if distance < 20.0:
            self._add_warning_sphere(pos1, 20.0, 'rgba(255, 170, 0, 0.08)', 'Alert Zone (20 km)')

    def _add_warning_sphere(self, center, radius, color='rgba(255, 23, 68, 0.2)', name='Warning Zone'):
        """Add a semi-transparent danger sphere"""
        u = np.linspace(0, 2 * np.pi, 24)
        v = np.linspace(0, np.pi, 24)
        x = center[0] + radius * np.outer(np.cos(u), np.sin(v))
        y = center[1] + radius * np.outer(np.sin(u), np.sin(v))
        z = center[2] + radius * np.outer(np.ones(np.size(u)), np.cos(v))

        self.fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            name=name,
            opacity=0.35,
            hoverinfo='skip',
            showlegend=False
        ))

    def _add_distance_visualization(self, traj1, traj2, distances, min_idx):
        """Add distance lines at key orbital intersections"""
        if min_idx < 0 or not distances:
            return

        if 0 <= min_idx < len(traj1) and 0 <= min_idx < len(traj2):
            pos1 = traj1[min_idx]['position']
            pos2 = traj2[min_idx]['position']
            dist = distances[min_idx]

            self.fig.add_trace(go.Scatter3d(
                x=[pos1[0], pos2[0]],
                y=[pos1[1], pos2[1]],
                z=[pos1[2], pos2[2]],
                mode='lines',
                name=f'Min Separation: {dist:.2f} km',
                line=dict(
                    color='rgba(255, 214, 0, 0.85)',
                    width=3.5,
                    dash='solid'
                ),
                showlegend=True,
                hovertemplate=f'<b>Closest Approach Distance: {dist:.2f} km</b><extra></extra>'
            ))

    def plot_collision_scenario(
        self,
        traj1,
        traj2,
        close_approach_event=None,
        name1="Satellite",
        name2="Debris",
        max_animation_frames=120
    ):
        """
        Visualize 3D collision scenario with smooth live animation, comet trails,
        scrubbable time slider, and play/pause controls.
        
        Args:
            traj1: Trajectory of first object (list of state dicts)
            traj2: Trajectory of second object (list of state dicts)
            close_approach_event: Optional event dict with collision point
            name1: Name of first object
            name2: Name of second object
            max_animation_frames: Target downsampled animation frames (default: 120)
        
        Returns:
            go.Figure: Animated plotly figure
        """
        self.fig = go.Figure()

        # 1. Starfield Background
        starfield = self.create_starfield()
        self.fig.add_trace(starfield)

        # 2. Cinematic Earth Sphere
        earth = self.create_earth_sphere()
        self.fig.add_trace(earth)

        # 3. Reference Equatorial Plane
        theta = np.linspace(0, 2 * np.pi, 80)
        eq_radius = self.earth_radius * 1.45
        self.fig.add_trace(go.Scatter3d(
            x=eq_radius * np.cos(theta),
            y=eq_radius * np.sin(theta),
            z=np.zeros_like(theta),
            mode='lines',
            name='Equatorial Plane',
            line=dict(color='rgba(77, 163, 255, 0.18)', width=1.2, dash='dot'),
            showlegend=True,
            hoverinfo='skip'
        ))

        # 4. Reference Coordinate Axes (Subtle RGB)
        axis_len = self.earth_radius * 1.8
        self.fig.add_trace(go.Scatter3d(
            x=[0, axis_len], y=[0, 0], z=[0, 0],
            mode='lines',
            name='X-axis (0° Lon)',
            line=dict(color='rgba(255, 82, 82, 0.3)', width=1.5),
            showlegend=False,
            hoverinfo='skip'
        ))
        self.fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, axis_len], z=[0, 0],
            mode='lines',
            name='Y-axis (90° E)',
            line=dict(color='rgba(0, 230, 118, 0.3)', width=1.5),
            showlegend=False,
            hoverinfo='skip'
        ))
        self.fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, axis_len],
            mode='lines',
            name='Z-axis (North Pole)',
            line=dict(color='rgba(41, 121, 255, 0.3)', width=1.5),
            showlegend=False,
            hoverinfo='skip'
        ))

        # 5. Extract trajectory data & calculate separation distances
        x1, y1, z1 = self.extract_trajectory_coords(traj1)
        x2, y2, z2 = self.extract_trajectory_coords(traj2)

        min_len = min(len(traj1), len(traj2))
        distances = []
        min_distance = float('inf')
        min_distance_idx = -1

        for i in range(min_len):
            p1 = np.array(traj1[i]['position'])
            p2 = np.array(traj2[i]['position'])
            d = float(np.linalg.norm(p1 - p2))
            distances.append(d)
            if d < min_distance:
                min_distance = d
                min_distance_idx = i

        # Color schemes: High-contrast Neon Cyan (#00f0ff) vs Neon Magenta/Coral (#ff0055)
        color1 = '#00f0ff'
        color2 = '#ff0055'

        # 6. Static Full Orbit Path Lines (semi-transparent)
        orbit1_path = self.plot_single_orbit_with_risk(traj1, name1, color1, distances, min_distance_idx)
        orbit2_path = self.plot_single_orbit_with_risk(traj2, name2, color2, distances, min_distance_idx)
        self.fig.add_trace(orbit1_path)
        self.fig.add_trace(orbit2_path)

        # 7. Static Closest Approach & Warning Indicators
        if close_approach_event:
            self._add_collision_zones(close_approach_event)

        if min_len > 0 and min_distance_idx >= 0:
            self._add_distance_visualization(traj1, traj2, distances, min_distance_idx)

            pos1_min = traj1[min_distance_idx]['position']
            pos2_min = traj2[min_distance_idx]['position']

            self.fig.add_trace(go.Scatter3d(
                x=[pos1_min[0], pos2_min[0]],
                y=[pos1_min[1], pos2_min[1]],
                z=[pos1_min[2], pos2_min[2]],
                mode='markers',
                name=f'Closest Approach ({min_distance:.2f} km)',
                marker=dict(size=9, color='#ffd600', symbol='diamond', line=dict(color='#ffffff', width=1.5)),
                showlegend=True,
                hovertemplate=f'<b>Closest Encounter</b><br>Separation: {min_distance:.2f} km<br>Time: {traj1[min_distance_idx].get("time", "")}<extra></extra>'
            ))

        # 8. Animated Dynamic Traces (Traces 10, 11, 12, 13, 14 in figure trace list)
        # Trace idx_t1: Satellite 1 Comet Trail
        # Trace idx_m1: Satellite 1 Active Moving Head
        # Trace idx_t2: Satellite 2 Comet Trail
        # Trace idx_m2: Satellite 2 Active Moving Head
        # Trace idx_dist: Live Instantaneous Separation Vector

        idx_t1 = len(self.fig.data)
        self.fig.add_trace(go.Scatter3d(
            x=[x1[0]], y=[y1[0]], z=[z1[0]],
            mode='lines',
            name=f'{name1} Trail',
            line=dict(color=color1, width=5.0),
            opacity=0.9,
            showlegend=False,
            hoverinfo='skip'
        ))

        idx_m1 = len(self.fig.data)
        self.fig.add_trace(go.Scatter3d(
            x=[x1[0]], y=[y1[0]], z=[z1[0]],
            mode='markers',
            name=f'🛰️ {name1}',
            marker=dict(
                size=11,
                color=color1,
                symbol='circle',
                line=dict(color='#ffffff', width=2.5)
            ),
            showlegend=True,
            hovertemplate=f'<b>🛰️ {name1} (Live Position)</b><br>Pos: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<extra></extra>'
        ))

        idx_t2 = len(self.fig.data)
        self.fig.add_trace(go.Scatter3d(
            x=[x2[0]], y=[y2[0]], z=[z2[0]],
            mode='lines',
            name=f'{name2} Trail',
            line=dict(color=color2, width=5.0),
            opacity=0.9,
            showlegend=False,
            hoverinfo='skip'
        ))

        idx_m2 = len(self.fig.data)
        self.fig.add_trace(go.Scatter3d(
            x=[x2[0]], y=[y2[0]], z=[z2[0]],
            mode='markers',
            name=f'⚠️ {name2}',
            marker=dict(
                size=11,
                color=color2,
                symbol='circle',
                line=dict(color='#ffffff', width=2.5)
            ),
            showlegend=True,
            hovertemplate=f'<b>⚠️ {name2} (Live Position)</b><br>Pos: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<extra></extra>'
        ))

        idx_dist = len(self.fig.data)
        d0 = distances[0] if distances else 0.0
        self.fig.add_trace(go.Scatter3d(
            x=[x1[0], x2[0]],
            y=[y1[0], y2[0]],
            z=[z1[0], z2[0]],
            mode='lines',
            name='Live Distance Vector',
            line=dict(color='rgba(255, 214, 0, 0.75)', width=2.2, dash='dot'),
            showlegend=False,
            hovertemplate=f'<b>Live Separation: {d0:.2f} km</b><extra></extra>'
        ))

        # 9. Downsample trajectory to create smooth Plotly Frames
        n_pts = min_len
        n_frames = min(max_animation_frames, n_pts)
        if n_frames < 2:
            frame_indices = [0]
        else:
            frame_indices = [int(i * (n_pts - 1) / (n_frames - 1)) for i in range(n_frames)]

        comet_tail_len = max(6, int(n_pts * 0.08))

        frames = []
        slider_steps = []

        for frame_idx, raw_idx in enumerate(frame_indices):
            # Tail slice
            start_tail = max(0, raw_idx - comet_tail_len)
            
            tail_x1 = x1[start_tail : raw_idx + 1]
            tail_y1 = y1[start_tail : raw_idx + 1]
            tail_z1 = z1[start_tail : raw_idx + 1]

            tail_x2 = x2[start_tail : raw_idx + 1]
            tail_y2 = y2[start_tail : raw_idx + 1]
            tail_z2 = z2[start_tail : raw_idx + 1]

            cur_p1 = [x1[raw_idx], y1[raw_idx], z1[raw_idx]]
            cur_p2 = [x2[raw_idx], y2[raw_idx], z2[raw_idx]]
            cur_dist = distances[raw_idx] if raw_idx < len(distances) else 0.0
            cur_time = traj1[raw_idx].get('time', f'Step {frame_idx}')

            frame_data = [
                # 0: Trail 1
                go.Scatter3d(x=tail_x1, y=tail_y1, z=tail_z1),
                # 1: Marker 1
                go.Scatter3d(
                    x=[cur_p1[0]], y=[cur_p1[1]], z=[cur_p1[2]],
                    hovertemplate=f'<b>🛰️ {name1}</b><br>Time: {cur_time}<br>Pos: ({cur_p1[0]:.1f}, {cur_p1[1]:.1f}, {cur_p1[2]:.1f}) km<extra></extra>'
                ),
                # 2: Trail 2
                go.Scatter3d(x=tail_x2, y=tail_y2, z=tail_z2),
                # 3: Marker 2
                go.Scatter3d(
                    x=[cur_p2[0]], y=[cur_p2[1]], z=[cur_p2[2]],
                    hovertemplate=f'<b>⚠️ {name2}</b><br>Time: {cur_time}<br>Pos: ({cur_p2[0]:.1f}, {cur_p2[1]:.1f}, {cur_p2[2]:.1f}) km<extra></extra>'
                ),
                # 4: Distance Vector
                go.Scatter3d(
                    x=[cur_p1[0], cur_p2[0]],
                    y=[cur_p1[1], cur_p2[1]],
                    z=[cur_p1[2], cur_p2[2]],
                    hovertemplate=f'<b>Live Separation: {cur_dist:.2f} km</b><br>Time: {cur_time}<extra></extra>'
                )
            ]

            frame_name = f'frame_{frame_idx}'
            frames.append(go.Frame(
                name=frame_name,
                data=frame_data,
                traces=[idx_t1, idx_m1, idx_t2, idx_m2, idx_dist]
            ))

            # Format slider label
            time_display = str(cur_time).split('T')[-1][:8] if 'T' in str(cur_time) else f'T+{frame_idx}'
            slider_steps.append({
                'args': [
                    [frame_name],
                    {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }
                ],
                'label': time_display,
                'method': 'animate'
            })

        self.fig.frames = frames

        # 10. Max bounding sphere for camera framing
        max_r1 = np.max(np.linalg.norm(np.column_stack((x1, y1, z1)), axis=1)) if len(x1) > 0 else 7000.0
        max_r2 = np.max(np.linalg.norm(np.column_stack((x2, y2, z2)), axis=1)) if len(x2) > 0 else 7000.0
        max_orbit_r = max(max_r1, max_r2, self.earth_radius + 500.0)
        axis_limit = max_orbit_r * 1.35

        # 11. Plotly Layout with Play/Pause & Slider
        self.fig.update_layout(
            title={
                'text': f'<b>Orbital Encounter Live Simulation</b><br>' +
                       f'<sub>Min Separation: <b style="color: #ffd600;">{min_distance:.2f} km</b> | ' +
                       f'<span style="color: {color1};">🛰️ {name1}</span> vs <span style="color: {color2};">⚠️ {name2}</span></sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#ffffff', 'family': 'Rajdhani, Segoe UI, sans-serif'}
            },
            scene=dict(
                xaxis=dict(
                    title=dict(text='X (km) → 0° Lon', font=dict(size=11, color='#88c9f0')),
                    backgroundcolor='rgba(2, 6, 16, 0.95)',
                    gridcolor='rgba(77, 163, 255, 0.15)',
                    showbackground=True,
                    zerolinecolor='rgba(77, 163, 255, 0.25)',
                    range=[-axis_limit, axis_limit]
                ),
                yaxis=dict(
                    title=dict(text='Y (km) → 90° E', font=dict(size=11, color='#88c9f0')),
                    backgroundcolor='rgba(2, 6, 16, 0.95)',
                    gridcolor='rgba(77, 163, 255, 0.15)',
                    showbackground=True,
                    zerolinecolor='rgba(77, 163, 255, 0.25)',
                    range=[-axis_limit, axis_limit]
                ),
                zaxis=dict(
                    title=dict(text='Z (km) → North Pole', font=dict(size=11, color='#88c9f0')),
                    backgroundcolor='rgba(2, 6, 16, 0.95)',
                    gridcolor='rgba(77, 163, 255, 0.15)',
                    showbackground=True,
                    zerolinecolor='rgba(77, 163, 255, 0.25)',
                    range=[-axis_limit, axis_limit]
                ),
                bgcolor='rgb(2, 6, 14)',
                aspectmode='cube',
                camera=dict(
                    eye=dict(x=1.65, y=1.65, z=1.2),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)
                )
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0', family='Segoe UI, Arial, sans-serif'),
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.98,
                bgcolor='rgba(4, 10, 22, 0.85)',
                bordercolor='rgba(77, 163, 255, 0.4)',
                borderwidth=1,
                font=dict(size=11, color='#ffffff')
            ),
            updatemenus=[
                dict(
                    type='buttons',
                    direction='left',
                    showactive=True,
                    x=0.08,
                    y=0.03,
                    xanchor='right',
                    yanchor='top',
                    bgcolor='rgba(4, 10, 22, 0.9)',
                    bordercolor='rgba(77, 163, 255, 0.4)',
                    borderwidth=1,
                    font=dict(size=12, color='#00f0ff'),
                    pad=dict(r=10, t=5),
                    buttons=[
                        dict(
                            label='▶ Play',
                            method='animate',
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=65, redraw=True),
                                    fromcurrent=True,
                                    mode='immediate',
                                    transition=dict(duration=0)
                                )
                            ]
                        ),
                        dict(
                            label='⏸ Pause',
                            method='animate',
                            args=[
                                [None],
                                dict(
                                    frame=dict(duration=0, redraw=False),
                                    mode='immediate',
                                    transition=dict(duration=0)
                                )
                            ]
                        )
                    ]
                )
            ],
            sliders=[
                dict(
                    active=0,
                    x=0.10,
                    y=0.02,
                    len=0.86,
                    xanchor='left',
                    yanchor='top',
                    pad=dict(t=10, b=10),
                    bgcolor='rgba(4, 10, 22, 0.85)',
                    bordercolor='rgba(77, 163, 255, 0.3)',
                    borderwidth=1,
                    font=dict(size=10, color='#88c9f0'),
                    currentvalue=dict(
                        visible=True,
                        prefix='Orbit Timeline: ',
                        xanchor='center',
                        font=dict(size=12, color='#00f0ff')
                    ),
                    steps=slider_steps
                )
            ],
            margin=dict(l=0, r=0, t=50, b=50)
        )

        return self.fig

    def plot_maneuver_comparison(
        self,
        traj_original,
        traj_after_maneuver,
        debris_traj,
        maneuver_point=None
    ):
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

        # Add starfield & Earth
        self.fig.add_trace(self.create_starfield())
        self.fig.add_trace(self.create_earth_sphere())

        # Original trajectory (dashed red/cyan)
        orbit_original = self.plot_single_orbit(
            traj_original, "Original Path (Colliding)", 'rgba(255, 82, 82, 0.6)'
        )
        orbit_original.line.dash = 'dash'
        self.fig.add_trace(orbit_original)

        # New trajectory after maneuver (safe bright green)
        orbit_new = self.plot_single_orbit(
            traj_after_maneuver, "Safe Maneuver Path", '#00e676'
        )
        orbit_new.line.width = 3.5
        self.fig.add_trace(orbit_new)

        # Debris trajectory
        debris = self.plot_single_orbit(debris_traj, "Debris Path", '#ff0055')
        self.fig.add_trace(debris)

        # Mark maneuver execution point
        if maneuver_point is not None:
            self.fig.add_trace(go.Scatter3d(
                x=[maneuver_point[0]],
                y=[maneuver_point[1]],
                z=[maneuver_point[2]],
                mode='markers',
                name='⚡ Maneuver Execution Point',
                marker=dict(size=12, color='#ffd600', symbol='diamond', line=dict(color='#ffffff', width=2)),
                hovertemplate='<b>⚡ Maneuver Burn Executed Here</b><extra></extra>'
            ))

        self.fig.update_layout(
            title={
                'text': '<b>Collision Avoidance Maneuver - Before & After</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#ffffff', 'family': 'Rajdhani, Segoe UI, sans-serif'}
            },
            scene=dict(
                xaxis=dict(title='X (km)', backgroundcolor='rgb(4, 10, 22)', gridcolor='rgba(77, 163, 255, 0.2)'),
                yaxis=dict(title='Y (km)', backgroundcolor='rgb(4, 10, 22)', gridcolor='rgba(77, 163, 255, 0.2)'),
                zaxis=dict(title='Z (km)', backgroundcolor='rgb(4, 10, 22)', gridcolor='rgba(77, 163, 255, 0.2)'),
                bgcolor='rgb(2, 6, 14)',
                aspectmode='cube',
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0', family='Segoe UI, Arial, sans-serif'),
            showlegend=True,
            legend=dict(x=0.02, y=0.98, bgcolor='rgba(4, 10, 22, 0.85)', bordercolor='rgba(77, 163, 255, 0.3)'),
            margin=dict(l=0, r=0, t=50, b=20)
        )

        return self.fig

    def create_dashboard_html(
        self,
        analysis_result=None,
        filename='output/collision_scenario.html',
        satellite_info1=None,
        satellite_info2=None
    ):
        """
        Create enhanced HTML dashboard with interactive 3D animated simulation and telemetry
        
        Args:
            analysis_result: Analysis results dict (optional)
            filename: Output HTML file path
            satellite_info1: Satellite information dict for first object
            satellite_info2: Satellite information dict for second object
        """
        if not self.fig:
            print("Warning: no figure to save")
            return

        # Ensure output directory exists
        out_dir = os.path.dirname(filename)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Extract data for statistics
        stats_html = self._generate_stats_html(analysis_result, satellite_info1, satellite_info2)

        # Generate collision indicator
        safe = analysis_result.get('safe', True) if analysis_result else True
        collision_indicator = f"""
        <div class="collision-indicator {'safe' if safe else 'danger'}">
            {'✅ SAFE: No immediate collision risk detected. Objects will pass each other safely.' if safe else '⚠️ WARNING: High-risk close approach detected. Conjunction avoidance recommended.'}
        </div>
        """

        # Convert figure to JSON for embedding
        fig_json = json.dumps(self.fig.to_dict(), cls=plotly.utils.PlotlyJSONEncoder)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COLLIDERS - 3D Orbital Encounter Simulation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #02060e 0%, #061124 50%, #040a17 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 16px;
        }}
        
        .dashboard-container {{
            max-width: 1640px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, rgba(6, 26, 56, 0.9) 0%, rgba(10, 42, 90, 0.9) 100%);
            border: 1px solid rgba(77, 163, 255, 0.35);
            padding: 22px 30px;
            border-radius: 12px;
            margin-bottom: 18px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            margin-bottom: 6px;
            color: #ffffff;
            letter-spacing: 3px;
            text-shadow: 0 0 20px rgba(77, 163, 255, 0.6);
        }}
        
        .header p {{
            font-size: 1.0rem;
            color: #4da3ff;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }}
        
        .stat-card {{
            background: rgba(4, 14, 30, 0.85);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(77, 163, 255, 0.25);
            border-radius: 10px;
            padding: 16px 20px;
            transition: transform 0.25s, box-shadow 0.25s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 240, 255, 0.25);
            border-color: rgba(0, 240, 255, 0.5);
        }}
        
        .stat-card h3 {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
            color: #4da3ff;
        }}
        
        .stat-card .value {{
            font-size: 1.65rem;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 4px;
            font-family: 'Courier New', monospace;
        }}
        
        .stat-card .unit {{
            font-size: 0.8rem;
            color: #888;
        }}
        
        .collision-indicator {{
            padding: 14px 20px;
            border-radius: 8px;
            margin-bottom: 18px;
            font-weight: 600;
            font-size: 0.95rem;
            letter-spacing: 0.5px;
            text-align: center;
        }}
        
        .collision-indicator.safe {{
            background: rgba(0, 230, 118, 0.12);
            border: 1px solid #00e676;
            color: #00e676;
        }}
        
        .collision-indicator.danger {{
            background: rgba(255, 23, 68, 0.15);
            border: 1px solid #ff1744;
            color: #ff5252;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.75; }}
        }}
        
        .visualization-container {{
            background: rgba(2, 6, 14, 0.95);
            border: 1px solid rgba(77, 163, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 18px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.7);
        }}
        
        .visualization-container h2 {{
            font-size: 1.15rem;
            color: #4da3ff;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .plot-container {{
            width: 100%;
            height: 720px;
            border-radius: 8px;
            overflow: hidden;
        }}

        .timestamp {{
            font-size: 0.75rem;
            color: #666;
            text-align: right;
            margin-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            font-size: 0.8rem;
            color: #666;
            padding: 14px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        @media (max-width: 900px) {{
            .plot-container {{
                height: 520px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>COLLIDERS</h1>
            <p>3D Orbital Conjunction Simulation & Collision Avoidance</p>
        </div>
        
        {stats_html}
        
        {collision_indicator}
        
        <div class="visualization-container">
            <h2>
                <span>🌐 Interactive 3D Orbit Simulation</span>
                <span style="font-size: 0.8rem; color: #00f0ff; font-weight: normal;">▶ Use Play/Pause & Slider below to animate orbital positions</span>
            </h2>
            <div class="plot-container" id="plotly-div"></div>
        </div>
        
        <div class="timestamp">
            Simulation Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
        
        <div class="footer">
            <p>COLLIDERS - Real-Time Autonomous Space Debris Monitoring & Collision Avoidance System</p>
        </div>
    </div>
    
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        var figureData = {fig_json};
        
        Plotly.newPlot('plotly-div', figureData.data, figureData.layout, {{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d'],
            displaylogo: false,
            toImageButtonOptions: {{
                format: 'png',
                filename: 'colliders_3d_encounter_simulation',
                height: 1080,
                width: 1920,
                scale: 2
            }}
        }}).then(function() {{
            if (figureData.frames && figureData.frames.length > 0) {{
                Plotly.addFrames('plotly-div', figureData.frames);
            }}
        }});
    </script>
</body>
</html>
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Enhanced 3D animation dashboard saved to: {filename}")

    def _generate_stats_html(self, analysis_result, satellite_info1=None, satellite_info2=None):
        """Generate statistics HTML cards from analysis results"""
        if not analysis_result:
            return """
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Status</h3>
                <div class="value" style="color: #00e676;">Nominal</div>
                <div class="unit">No active collision alerts</div>
            </div>
        </div>
        """

        closest = analysis_result.get('closest_approach', {})
        events = analysis_result.get('events', [])
        risk = analysis_result.get('risk_assessment', {})

        closest_dist = closest.get('distance') if closest else None
        closest_time = closest.get('time') if closest else None
        rel_vel = closest.get('relative_velocity') if closest else None
        risk_level = risk.get('risk_level', 'SAFE') if isinstance(risk, dict) else 'SAFE'
        probability = risk.get('collision_probability', 0.0) if isinstance(risk, dict) else 0.0

        if probability < 1e-6:
            prob_str = f"{probability:.2e}"
        else:
            prob_str = f"{probability * 100:.3f}%"

        risk_colors = {
            'SAFE': '#00e676',
            'LOW': '#00e5ff',
            'MODERATE': '#ffb74d',
            'HIGH': '#ff7043',
            'CRITICAL': '#ff1744'
        }
        risk_color = risk_colors.get(risk_level, '#00e676')

        sat1_name = satellite_info1.get('name', 'Object 1') if satellite_info1 else 'Satellite 1'
        sat2_name = satellite_info2.get('name', 'Object 2') if satellite_info2 else 'Debris Object'

        return f"""
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Conjunction Target</h3>
                <div class="value" style="font-size: 1.15rem; color: #00f0ff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{sat1_name}">
                    {sat1_name}
                </div>
                <div class="unit">vs <strong style="color: #ff0055;">{sat2_name}</strong></div>
            </div>
            
            <div class="stat-card">
                <h3>Minimum Separation</h3>
                <div class="value" style="color: {'#ff1744' if closest_dist and closest_dist < 5 else '#ffd600'};">
                    {f"{closest_dist:.2f} km" if closest_dist is not None else "N/A"}
                </div>
                <div class="unit">Closest Approach Distance</div>
            </div>
            
            <div class="stat-card">
                <h3>Relative Speed</h3>
                <div class="value" style="color: #00f0ff;">
                    {f"{rel_vel:.2f} km/s" if rel_vel is not None else "N/A"}
                </div>
                <div class="unit">Encounter Relative Velocity</div>
            </div>
            
            <div class="stat-card">
                <h3>Collision Risk Level</h3>
                <div class="value" style="color: {risk_color};">
                    {risk_level}
                </div>
                <div class="unit">P(Collision): <strong style="color: #ffffff;">{prob_str}</strong></div>
            </div>
        </div>
        """

    def save_html(self, filename, analysis_result=None, satellite_info1=None, satellite_info2=None):
        """
        Save visualization to HTML file with full dashboard
        """
        if self.fig:
            try:
                self.create_dashboard_html(analysis_result, filename, satellite_info1, satellite_info2)
            except Exception as e:
                print(f"Error saving enhanced dashboard: {e}")
                try:
                    self.fig.write_html(filename, include_plotlyjs='cdn')
                    print(f"Fallback visualization saved to: {filename}")
                except Exception as e2:
                    print(f"Fallback also failed: {e2}")

    def show(self):
        """Display visualization in browser"""
        if self.fig:
            self.fig.show()


def main():
    """Test orbit visualization"""
    from propagation.propagate import OrbitPropagator
    from propagation.distance_check import CloseApproachDetector
    from datetime import datetime, timezone

    print("=" * 70)
    print("ORBIT VISUALIZATION ANIMATION TEST")
    print("=" * 70)

    prop1 = OrbitPropagator('data/iss.txt')
    prop2 = OrbitPropagator('data/debris1.txt')

    start_time = datetime.now(timezone.utc)
    print(f"\nGenerating trajectories from: {start_time}")

    traj1 = prop1.propagate_trajectory(start_time, 90, 60)
    traj2 = prop2.propagate_trajectory(start_time, 90, 60)

    print(f"Generated {len(traj1)} points for object 1")
    print(f"Generated {len(traj2)} points for object 2")

    detector = CloseApproachDetector(threshold_km=1000.0)
    events = detector.check_trajectories(traj1, traj2)

    visualizer = OrbitVisualizer()

    if events:
        closest = detector.find_closest_approach()
        print(f"\nClosest approach: {closest['distance']:.2f} km")
        visualizer.plot_collision_scenario(
            traj1, traj2, closest,
            name1=prop1.name, name2=prop2.name
        )
    else:
        print("\nNo close approaches detected, plotting orbits only")
        visualizer.plot_collision_scenario(
            traj1, traj2,
            name1=prop1.name, name2=prop2.name
        )

    out_file = 'output/orbit_visualization.html'
    visualizer.save_html(out_file)
    print(f"\nAnimation dashboard saved to: {out_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
