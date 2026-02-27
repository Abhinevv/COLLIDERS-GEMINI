"""
Maneuver Calculator for collision avoidance
Calculates optimal maneuvers to avoid collisions
"""

import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ManeuverCalculator:
    """Calculate collision avoidance maneuvers"""
    
    def __init__(self):
        self.earth_mu = 398600.4418  # Earth's gravitational parameter (km^3/s^2)
    
    def calculate_avoidance_options(self, satellite_position, satellite_velocity,
                                   debris_position, debris_velocity,
                                   closest_approach_time, current_time):
        """
        Calculate maneuver options to avoid collision
        
        Args:
            satellite_position: Satellite position vector [x, y, z] in km
            satellite_velocity: Satellite velocity vector [vx, vy, vz] in km/s
            debris_position: Debris position vector [x, y, z] in km
            debris_velocity: Debris velocity vector [vx, vy, vz] in km/s
            closest_approach_time: Time of closest approach
            current_time: Current time
            
        Returns:
            List of maneuver options
        """
        options = []
        
        # Calculate time until closest approach
        if isinstance(closest_approach_time, datetime) and isinstance(current_time, datetime):
            time_to_ca = (closest_approach_time - current_time).total_seconds()
        else:
            time_to_ca = 3600  # Default 1 hour
        
        # Option 1: Radial boost (increase altitude)
        radial_option = self._calculate_radial_maneuver(
            satellite_position, satellite_velocity, time_to_ca, delta_altitude=5.0
        )
        if radial_option:
            options.append(radial_option)
        
        # Option 2: In-track adjustment (speed up)
        in_track_option = self._calculate_in_track_maneuver(
            satellite_position, satellite_velocity, time_to_ca, delta_v_factor=1.01
        )
        if in_track_option:
            options.append(in_track_option)
        
        # Option 3: In-track adjustment (slow down)
        in_track_slow = self._calculate_in_track_maneuver(
            satellite_position, satellite_velocity, time_to_ca, delta_v_factor=0.99
        )
        if in_track_slow:
            options.append(in_track_slow)
        
        # Sort by fuel cost
        options.sort(key=lambda x: x['delta_v_magnitude'])
        
        return options
    
    def _calculate_radial_maneuver(self, position, velocity, time_to_ca, delta_altitude=5.0):
        """
        Calculate radial boost maneuver
        
        Args:
            position: Position vector [x, y, z] in km
            velocity: Velocity vector [vx, vy, vz] in km/s
            time_to_ca: Time to closest approach in seconds
            delta_altitude: Altitude change in km
            
        Returns:
            Maneuver dictionary
        """
        try:
            # Calculate radial direction (away from Earth)
            r = np.linalg.norm(position)
            radial_unit = position / r
            
            # Calculate required delta-v for altitude change
            # Using vis-viva equation approximation
            v_current = np.linalg.norm(velocity)
            a_current = r  # Semi-major axis approximation
            a_new = a_current + delta_altitude
            
            # Delta-v for Hohmann transfer (simplified)
            delta_v = np.sqrt(self.earth_mu / a_current) * (np.sqrt(2 * a_new / (a_current + a_new)) - 1)
            delta_v_vector = radial_unit * abs(delta_v)
            
            return {
                'type': 'radial_boost',
                'name': 'Radial Boost (Increase Altitude)',
                'description': f'Increase altitude by {delta_altitude:.1f} km',
                'delta_v_vector': delta_v_vector.tolist(),
                'delta_v_magnitude': abs(delta_v),
                'direction': 'radial',
                'altitude_change_km': delta_altitude,
                'execution_time': 'As soon as possible',
                'fuel_cost_estimate': self._estimate_fuel_cost(abs(delta_v))
            }
        except Exception as e:
            logger.error(f"Error calculating radial maneuver: {e}")
            return None
    
    def _calculate_in_track_maneuver(self, position, velocity, time_to_ca, delta_v_factor=1.01):
        """
        Calculate in-track maneuver (speed up or slow down)
        
        Args:
            position: Position vector [x, y, z] in km
            velocity: Velocity vector [vx, vy, vz] in km/s
            time_to_ca: Time to closest approach in seconds
            delta_v_factor: Factor to multiply velocity (>1 = speed up, <1 = slow down)
            
        Returns:
            Maneuver dictionary
        """
        try:
            # Calculate velocity direction
            v_mag = np.linalg.norm(velocity)
            v_unit = velocity / v_mag
            
            # Calculate delta-v
            v_new = v_mag * delta_v_factor
            delta_v = v_new - v_mag
            delta_v_vector = v_unit * delta_v
            
            maneuver_type = 'speed_up' if delta_v > 0 else 'slow_down'
            name = 'In-Track Speed Up' if delta_v > 0 else 'In-Track Slow Down'
            description = f'{"Increase" if delta_v > 0 else "Decrease"} velocity by {abs(delta_v)*1000:.1f} m/s'
            
            return {
                'type': maneuver_type,
                'name': name,
                'description': description,
                'delta_v_vector': delta_v_vector.tolist(),
                'delta_v_magnitude': abs(delta_v),
                'direction': 'in-track',
                'velocity_change_m_s': delta_v * 1000,
                'execution_time': 'As soon as possible',
                'fuel_cost_estimate': self._estimate_fuel_cost(abs(delta_v))
            }
        except Exception as e:
            logger.error(f"Error calculating in-track maneuver: {e}")
            return None
    
    def _estimate_fuel_cost(self, delta_v_km_s, satellite_mass_kg=1000):
        """
        Estimate fuel cost for a maneuver
        
        Args:
            delta_v_km_s: Delta-v in km/s
            satellite_mass_kg: Satellite mass in kg
            
        Returns:
            Dictionary with fuel estimates
        """
        # Typical specific impulse for satellite thrusters
        isp = 300  # seconds
        g0 = 9.81 / 1000  # km/s^2
        
        # Tsiolkovsky rocket equation
        mass_ratio = np.exp(delta_v_km_s / (isp * g0))
        fuel_mass = satellite_mass_kg * (mass_ratio - 1)
        
        return {
            'fuel_mass_kg': round(fuel_mass, 2),
            'delta_v_m_s': round(delta_v_km_s * 1000, 2),
            'mass_ratio': round(mass_ratio, 4)
        }
    
    def simulate_maneuver(self, original_position, original_velocity, delta_v_vector, duration_hours=24):
        """
        Simulate the effect of a maneuver
        
        Args:
            original_position: Original position vector [x, y, z] in km
            original_velocity: Original velocity vector [vx, vy, vz] in km/s
            delta_v_vector: Delta-v vector [dvx, dvy, dvz] in km/s
            duration_hours: Simulation duration in hours
            
        Returns:
            Dictionary with before/after trajectories
        """
        # Convert to numpy arrays
        original_position = np.array(original_position, dtype=float)
        original_velocity = np.array(original_velocity, dtype=float)
        delta_v_vector = np.array(delta_v_vector, dtype=float)
        
        # Apply maneuver
        new_velocity = original_velocity + delta_v_vector
        
        # Simple propagation (this is simplified - real implementation would use SGP4)
        time_steps = np.linspace(0, duration_hours * 3600, 100)
        
        original_trajectory = []
        new_trajectory = []
        
        for t in time_steps:
            # Very simplified orbital propagation (circular orbit approximation)
            r = np.linalg.norm(original_position)
            v = np.linalg.norm(original_velocity)
            period = 2 * np.pi * r / v
            
            angle = (t / period) * 2 * np.pi
            
            # Original trajectory
            orig_pos = self._rotate_vector(original_position, angle)
            original_trajectory.append(orig_pos.tolist())
            
            # New trajectory (with slightly different radius due to delta-v)
            r_new = r + np.linalg.norm(delta_v_vector) * t / 10  # Simplified
            new_pos = self._rotate_vector(original_position * (r_new / r), angle)
            new_trajectory.append(new_pos.tolist())
        
        # Calculate max separation
        separations = [np.linalg.norm(np.array(orig) - np.array(new)) 
                      for orig, new in zip(original_trajectory, new_trajectory)]
        max_separation = max(separations) if separations else 0
        
        return {
            'original_trajectory': original_trajectory,
            'new_trajectory': new_trajectory,
            'time_steps': time_steps.tolist(),
            'duration_hours': duration_hours,
            'max_separation_km': round(max_separation, 2)
        }
    
    def _rotate_vector(self, vector, angle):
        """Rotate a vector around the z-axis"""
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        rotation_matrix = np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
        return rotation_matrix @ vector
    
    def compare_maneuver_options(self, options):
        """
        Compare maneuver options and recommend the best one
        
        Args:
            options: List of maneuver dictionaries
            
        Returns:
            Dictionary with comparison and recommendation
        """
        if not options:
            return {'recommendation': None, 'reason': 'No maneuver options available'}
        
        # Find option with lowest delta-v (most fuel efficient)
        best_option = min(options, key=lambda x: x['delta_v_magnitude'])
        
        comparison = {
            'total_options': len(options),
            'recommended': best_option,
            'reason': 'Lowest fuel cost',
            'all_options': options
        }
        
        return comparison
