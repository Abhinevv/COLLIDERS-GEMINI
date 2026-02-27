"""
Collision Avoidance Maneuver Optimization
Find minimum fuel solution to avoid collision
"""

import numpy as np
from datetime import timedelta
from copy import deepcopy

class AvoidanceManeuver:
    """Optimize collision avoidance maneuvers"""
    
    # Burn directions
    RADIAL = 'radial'       # Away from Earth
    TANGENTIAL = 'tangential'  # Along velocity
    NORMAL = 'normal'       # Perpendicular to orbital plane
    
    def __init__(self, propagator, max_dv=10.0):
        """
        Initialize maneuver optimizer
        
        Args:
            propagator: OrbitPropagator instance
            max_dv: Maximum delta-V budget (m/s)
        """
        self.propagator = propagator
        self.max_dv = max_dv / 1000.0  # Convert to km/s
        self.best_maneuver = None
    
    def compute_burn_vector(self, state, magnitude, direction):
        """
        Compute delta-V vector in specified direction
        
        Args:
            state: Current state dict with position and velocity
            magnitude: Delta-V magnitude (km/s)
            direction: 'radial', 'tangential', or 'normal'
        
        Returns:
            np.array: Delta-V vector [dvx, dvy, dvz] (km/s)
        """
        pos = state['position']
        vel = state['velocity']
        
        # Unit vectors
        r_hat = pos / np.linalg.norm(pos)  # Radial
        v_hat = vel / np.linalg.norm(vel)  # Tangential
        h_hat = np.cross(pos, vel)
        h_hat = h_hat / np.linalg.norm(h_hat)  # Normal to orbital plane
        
        if direction == self.RADIAL:
            return magnitude * r_hat
        elif direction == self.TANGENTIAL:
            return magnitude * v_hat
        elif direction == self.NORMAL:
            return magnitude * h_hat
        else:
            raise ValueError(f"Unknown direction: {direction}")
    
    def apply_maneuver(self, state, dv_vector):
        """
        Apply delta-V to state
        
        Args:
            state: Current state
            dv_vector: Delta-V vector (km/s)
        
        Returns:
            dict: New state after maneuver
        """
        new_state = deepcopy(state)
        new_state['velocity'] = state['velocity'] + dv_vector
        return new_state
    
    def evaluate_maneuver(self, burn_time, magnitude, direction, 
                         debris_propagator, check_duration=60):
        """
        Evaluate effectiveness of a maneuver
        
        Args:
            burn_time: Time to execute burn (datetime)
            magnitude: Delta-V magnitude (m/s)
            direction: Burn direction
            debris_propagator: Propagator for debris object
            check_duration: Duration to check after maneuver (minutes)
        
        Returns:
            dict: Evaluation results
        """
        magnitude_kms = magnitude / 1000.0  # Convert to km/s
        
        # Get state at burn time
        state_before = self.propagator.propagate(burn_time)
        
        # Compute and apply maneuver
        dv_vector = self.compute_burn_vector(state_before, magnitude_kms, direction)
        
        # NOTE: In real implementation, would need to update TLE or use numerical propagator
        # For this demo, we estimate the effect
        
        # Propagate both objects after maneuver
        min_distance = float('inf')
        min_distance_time = None
        
        for i in range(check_duration):
            check_time = burn_time + timedelta(minutes=i)
            
            # Original trajectory (approximation - would need proper propagation)
            state_sat = self.propagator.propagate(check_time)
            state_debris = debris_propagator.propagate(check_time)
            
            # Approximate new position (simplified)
            # In reality, would re-propagate with modified orbit
            dt = (check_time - burn_time).total_seconds()
            position_change = dv_vector * dt  # Simplified linear approximation
            
            new_pos = state_sat['position'] + position_change
            distance = np.linalg.norm(new_pos - state_debris['position'])
            
            if distance < min_distance:
                min_distance = distance
                min_distance_time = check_time
        
        # Cost function: balance fuel and safety
        # cost = fuel_cost + collision_risk_penalty
        fuel_cost = magnitude_kms * 1000  # Back to m/s
        
        # Penalty if still too close
        if min_distance < 1.0:  # Less than 1 km
            safety_penalty = 1000.0 / min_distance
        else:
            safety_penalty = 0.0
        
        total_cost = fuel_cost + safety_penalty
        
        return {
            'burn_time': burn_time,
            'magnitude': magnitude,  # m/s
            'direction': direction,
            'dv_vector': dv_vector * 1000,  # m/s
            'min_distance': min_distance,
            'min_distance_time': min_distance_time,
            'fuel_cost': fuel_cost,
            'safety_penalty': safety_penalty,
            'total_cost': total_cost
        }
    
    def optimize_maneuver(self, burn_time, debris_propagator, 
                         dv_range=(0.1, 5.0), dv_step=0.1):
        """
        Find optimal maneuver using grid search
        
        Args:
            burn_time: When to execute maneuver
            debris_propagator: Propagator for threat object
            dv_range: (min, max) delta-V to test (m/s)
            dv_step: Step size for search (m/s)
        
        Returns:
            dict: Best maneuver found
        """
        print("Optimizing collision avoidance maneuver...")
        print(f"  Burn time: {burn_time}")
        print(f"  Delta-V range: {dv_range[0]} - {dv_range[1]} m/s")
        print()
        
        best_solution = None
        best_cost = float('inf')
        
        directions = [self.RADIAL, self.TANGENTIAL, self.NORMAL]
        
        # Grid search over magnitudes and directions
        dv_values = np.arange(dv_range[0], dv_range[1], dv_step)
        
        for magnitude in dv_values:
            for direction in directions:
                result = self.evaluate_maneuver(
                    burn_time, magnitude, direction, debris_propagator
                )
                
                if result['total_cost'] < best_cost:
                    best_cost = result['total_cost']
                    best_solution = result
        
        self.best_maneuver = best_solution
        return best_solution
    
    def genetic_algorithm_optimize(self, burn_time, debris_propagator,
                                   population_size=20, generations=10):
        """
        Genetic algorithm for maneuver optimization
        More sophisticated than grid search
        
        Args:
            burn_time: Maneuver execution time
            debris_propagator: Threat object propagator
            population_size: GA population size
            generations: Number of GA generations
        
        Returns:
            dict: Optimized maneuver
        """
        # Initialize population
        # Genes: [magnitude (m/s), direction_index (0-2)]
        population = []
        directions = [self.RADIAL, self.TANGENTIAL, self.NORMAL]
        
        for _ in range(population_size):
            magnitude = np.random.uniform(0.1, 5.0)
            direction_idx = np.random.randint(0, 3)
            population.append([magnitude, direction_idx])
        
        for gen in range(generations):
            # Evaluate fitness
            fitness = []
            for individual in population:
                magnitude, dir_idx = individual
                direction = directions[dir_idx]
                
                result = self.evaluate_maneuver(
                    burn_time, magnitude, direction, debris_propagator
                )
                
                # Fitness = 1 / cost (lower cost = higher fitness)
                fitness.append(1.0 / (result['total_cost'] + 1e-6))
            
            # Selection, crossover, mutation
            # (Simplified implementation)
            fitness = np.array(fitness)
            fitness = fitness / fitness.sum()
            
            # Select parents
            parents_idx = np.random.choice(
                len(population), size=population_size, p=fitness
            )
            
            new_population = []
            for idx in parents_idx:
                # Mutation
                individual = population[idx].copy()
                if np.random.random() < 0.3:  # Mutation rate
                    individual[0] += np.random.normal(0, 0.5)  # Magnitude
                    individual[0] = np.clip(individual[0], 0.1, 5.0)
                if np.random.random() < 0.2:
                    individual[1] = np.random.randint(0, 3)  # Direction
                
                new_population.append(individual)
            
            population = new_population
        
        # Final evaluation - get best solution
        best_solution = None
        best_cost = float('inf')
        
        for individual in population:
            magnitude, dir_idx = individual
            direction = directions[dir_idx]
            
            result = self.evaluate_maneuver(
                burn_time, magnitude, direction, debris_propagator
            )
            
            if result['total_cost'] < best_cost:
                best_cost = result['total_cost']
                best_solution = result
        
        self.best_maneuver = best_solution
        return best_solution
    
    def print_maneuver_plan(self, maneuver):
        """Print human-readable maneuver plan"""
        print("=" * 70)
        print("OPTIMAL COLLISION AVOIDANCE MANEUVER")
        print("=" * 70)
        print(f"Burn Time: {maneuver['burn_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Direction: {maneuver['direction'].upper()}")
        print(f"Delta-V Magnitude: {maneuver['magnitude']:.3f} m/s")
        print()
        print(f"Delta-V Vector:")
        print(f"  dVx: {maneuver['dv_vector'][0]:7.3f} m/s")
        print(f"  dVy: {maneuver['dv_vector'][1]:7.3f} m/s")
        print(f"  dVz: {maneuver['dv_vector'][2]:7.3f} m/s")
        print()
        print(f"Expected Outcome:")
        print(f"  Minimum Distance: {maneuver['min_distance']:.3f} km")
        print(f"  Time of Min Distance: {maneuver['min_distance_time'].strftime('%H:%M:%S UTC')}")
        print(f"  Fuel Cost: {maneuver['fuel_cost']:.3f} m/s")
        print("=" * 70)


def main():
    """Test avoidance maneuver optimization"""
    from propagation.propagate import OrbitPropagator
    from datetime import datetime
    
    print("COLLISION AVOIDANCE MANEUVER OPTIMIZATION")
    print("=" * 70)
    
    # Load objects
    sat_prop = OrbitPropagator('data/iss.txt')
    debris_prop = OrbitPropagator('data/debris1.txt')
    
    # Set burn time (e.g., 30 minutes from now)
    burn_time = datetime.utcnow() + timedelta(minutes=30)
    
    # Optimize maneuver
    optimizer = AvoidanceManeuver(sat_prop, max_dv=10.0)
    
    print("\n1. Grid Search Optimization:")
    print("-" * 70)
    best_maneuver = optimizer.optimize_maneuver(
        burn_time, debris_prop,
        dv_range=(0.1, 2.0),
        dv_step=0.2
    )
    optimizer.print_maneuver_plan(best_maneuver)
    
    print("\n2. Genetic Algorithm Optimization:")
    print("-" * 70)
    best_maneuver_ga = optimizer.genetic_algorithm_optimize(
        burn_time, debris_prop,
        population_size=15,
        generations=8
    )
    optimizer.print_maneuver_plan(best_maneuver_ga)

if __name__ == "__main__":
    main()
