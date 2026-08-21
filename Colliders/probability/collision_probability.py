"""
Collision Probability Calculation
Statistical analysis of collision risk using probability theory
"""

import numpy as np
from scipy.stats import chi2, ncx2
from scipy.linalg import inv

class CollisionProbability:
    """Calculate probability of collision between two objects"""
    
    def __init__(self, position_uncertainty=0.1, velocity_uncertainty=0.01):
        """
        Initialize with uncertainty parameters
        
        Args:
            position_uncertainty: Position error standard deviation (km)
            velocity_uncertainty: Velocity error standard deviation (km/s)
        """
        self.pos_sigma = position_uncertainty
        self.vel_sigma = velocity_uncertainty
    
    def create_covariance_matrix(self, sigma_pos=None, sigma_vel=None):
        """
        Create 6x6 covariance matrix for position and velocity uncertainties
        
        Args:
            sigma_pos: Position uncertainty (km), uses default if None
            sigma_vel: Velocity uncertainty (km/s), uses default if None
        
        Returns:
            6x6 covariance matrix
        """
        sigma_pos = sigma_pos or self.pos_sigma
        sigma_vel = sigma_vel or self.vel_sigma
        
        # Diagonal covariance matrix (assumes independent errors)
        covariance = np.diag([
            sigma_pos**2, sigma_pos**2, sigma_pos**2,  # x, y, z position
            sigma_vel**2, sigma_vel**2, sigma_vel**2   # vx, vy, vz velocity
        ])
        
        return covariance
    
    def calculate_probability_2d(self, distance, combined_radius, position_covariance):
        """
        Calculate collision probability using 2D Gaussian model
        (Simplified Chan method)
        
        Args:
            distance: Relative distance at closest approach (km)
            combined_radius: Sum of object radii (km)
            position_covariance: 3x3 position covariance matrix
        
        Returns:
            float: Collision probability (0 to 1)
        """
        # Extract 2D covariance (projection onto B-plane)
        # For simplicity, use x-y plane
        cov_2d = position_covariance[:2, :2]

        # Approximate using non-central chi-square (2 DOF) for radial distance
        try:
            # Effective isotropic variance estimate from covariance trace
            sigma2 = np.trace(cov_2d) / 2.0
            if sigma2 <= 0 or not np.isfinite(sigma2):
                return self._distance_based_probability(distance, combined_radius)

            # Non-centrality parameter lambda = d^2 / sigma2
            nc = (distance**2) / sigma2

            # Evaluate CDF of non-central chi-square at (R^2 / sigma2)
            x = (combined_radius**2) / sigma2
            # CDF gives probability that squared radial distance <= R^2
            probability = float(ncx2.cdf(x, df=2, nc=nc))

            # Clamp between 0 and 1
            return max(0.0, min(1.0, probability))

        except Exception:
            # Fallback to distance-based heuristic
            return self._distance_based_probability(distance, combined_radius)
    
    def _distance_based_probability(self, distance, combined_radius):
        """
        Fallback: Simple distance-based probability
        
        Args:
            distance: Separation distance (km)
            combined_radius: Sum of radii (km)
        
        Returns:
            float: Probability estimate
        """
        if distance <= combined_radius:
            return 1.0
        elif distance >= combined_radius * 3:
            return 0.0
        else:
            # Linear decay
            return 1.0 - (distance - combined_radius) / (2 * combined_radius)
    
    def calculate_poisson_probability(self, expected_encounters, collision_cross_section, relative_velocity, time_window):
        """
        Calculate collision probability using Poisson distribution
        
        Args:
            expected_encounters: Expected number of close approaches
            collision_cross_section: Combined object cross-section (km²)
            relative_velocity: Relative velocity (km/s)
            time_window: Time window (seconds)
        
        Returns:
            float: Collision probability
        """
        # Flux calculation
        flux = relative_velocity * time_window
        
        # Expected number of collisions
        lambda_param = expected_encounters * (collision_cross_section / flux) if flux > 0 else 0
        
        # Poisson: P(at least one collision) = 1 - P(zero collisions)
        probability = 1 - np.exp(-lambda_param)
        
        return max(0.0, min(1.0, probability))
    
    def monte_carlo_simulation(self, pos1, pos2, vel1, vel2, num_samples=100000, combined_radius=0.02,
                               use_pinn=True, enable_importance_sampling=False):
        """
        PINN-Accelerated Batched Monte Carlo simulation for collision probability.
        Samples from 6x6 initial covariance matrix using Cholesky decomposition.
        
        Args:
            pos1, pos2: Position vectors (km)
            vel1, vel2: Velocity vectors (km/s)
            num_samples: Number of Monte Carlo samples (default 100,000)
            combined_radius: Combined object radius (km)
            use_pinn: Whether to use PINN surrogate propagation (default True)
            enable_importance_sampling: Toggle rare event importance sampling
        
        Returns:
            dict: Comprehensive results including probability, log10_probability, and miss distances
        """
        try:
            from .pinn_monte_carlo import PINNMonteCarloAssessment
            pinn_assessor = PINNMonteCarloAssessment()

            cov1 = self.create_covariance_matrix()
            cov2 = self.create_covariance_matrix(sigma_pos=self.pos_sigma * 1.5, sigma_vel=self.vel_sigma * 1.5)

            result = pinn_assessor.assess_collision_pinn(
                sat_pos_tca=np.asarray(pos1, dtype=np.float64),
                sat_vel_tca=np.asarray(vel1, dtype=np.float64),
                deb_pos_tca=np.asarray(pos2, dtype=np.float64),
                deb_vel_tca=np.asarray(vel2, dtype=np.float64),
                combined_radius_km=combined_radius,
                cov_sat_6x6=cov1,
                cov_deb_6x6=cov2,
                num_samples=num_samples,
                conjunction_window_sec=60.0,
                enable_importance_sampling=enable_importance_sampling
            )
            return {
                'probability': result['probability'],
                'probability_monte_carlo': result['probability'],
                'probability_formatted': result['probability_formatted'],
                'probability_display': result['probability_display'],
                'log10_probability': result['log10_probability'],
                'collisions': result['collision_count'],
                'collision_count': result['collision_count'],
                'samples': num_samples,
                'total_samples': num_samples,
                'combined_radius': combined_radius,
                'combined_radius_km': combined_radius,
                'confidence_interval_95': result['confidence_interval_95'],
                'min_distance_km': result['min_distance_km'],
                'mean_miss_distance_km': result['mean_miss_distance_km'],
                'pinn_accelerated': result['pinn_accelerated'],
                'method': result['method'],
                'execution_time_ms': result['execution_time_ms'],
                'risk_level': result['risk_level']
            }
        except Exception as e:
            # Fallback to vectorized Cholesky Monte Carlo in NumPy
            cov = np.eye(3) * (self.pos_sigma ** 2)
            pos1_samples = np.random.multivariate_normal(pos1, cov, num_samples)
            pos2_samples = np.random.multivariate_normal(pos2, cov, num_samples)

            diffs = pos1_samples - pos2_samples
            dists = np.linalg.norm(diffs, axis=1)
            collision_mask = dists <= combined_radius
            collision_count = int(np.count_nonzero(collision_mask))
            probability = collision_count / float(num_samples)
            
            return {
                'probability': probability,
                'probability_monte_carlo': probability,
                'probability_formatted': f"{probability:.2e}" if probability > 0 else f"<{2.99/num_samples:.2e}",
                'log10_probability': float(np.log10(max(1e-15, probability))) if probability > 0 else float(np.log10(3.0 / num_samples)),
                'collisions': collision_count,
                'collision_count': collision_count,
                'samples': num_samples,
                'total_samples': num_samples,
                'combined_radius': combined_radius,
                'min_distance_km': float(np.min(dists)),
                'pinn_accelerated': False,
                'method': 'Vectorized_NumPy_Monte_Carlo'
            }
    
    def assess_risk(self, event, object_radius_1=0.01, object_radius_2=0.01, num_samples=100000, enable_importance_sampling=False):
        """
        Comprehensive risk assessment for a close approach event using PINN-accelerated Monte Carlo.
        
        Args:
            event: Event dict from CloseApproachDetector
            object_radius_1: Radius of first object (km)
            object_radius_2: Radius of second object (km)
            num_samples: Number of Monte Carlo samples (default 100,000)
            enable_importance_sampling: Toggle importance sampling
        
        Returns:
            dict: Risk assessment results
        """
        distance = event['distance']
        rel_velocity = event['relative_velocity']
        combined_radius = object_radius_1 + object_radius_2
        
        # Position covariance
        pos_cov = self.create_covariance_matrix()[:3, :3]
        
        # Calculate analytical 2D probability
        prob_2d = self.calculate_probability_2d(distance, combined_radius, pos_cov)
        
        # PINN-Accelerated Monte Carlo assessment (N >= 10^5 in parallel)
        mc_result = self.monte_carlo_simulation(
            event['position1'], event['position2'],
            event['velocity1'], event['velocity2'],
            num_samples=num_samples,
            combined_radius=combined_radius,
            use_pinn=True,
            enable_importance_sampling=enable_importance_sampling
        )
        
        # Risk classification
        mc_prob = mc_result['probability']
        prob_avg = (prob_2d + mc_prob) / 2.0
        
        eval_prob = max(prob_avg, prob_2d if distance < 5.0 and mc_prob == 0 else mc_prob)
        if eval_prob >= 0.01:
            risk_category = "CRITICAL"
        elif eval_prob >= 0.001:
            risk_category = "HIGH"
        elif eval_prob >= 0.00001:
            risk_category = "MEDIUM"
        else:
            risk_category = "LOW"
        
        return {
            'distance': distance,
            'combined_radius': combined_radius,
            'probability_2d': prob_2d,
            'probability_monte_carlo': mc_result['probability'],
            'probability_formatted': mc_result.get('probability_formatted', f"{mc_result['probability']:.2e}"),
            'probability_display': mc_result.get('probability_display', f"{mc_result['probability']*100:.6f}%"),
            'log10_probability': mc_result.get('log10_probability', -15.0),
            'probability_average': prob_avg,
            'risk_category': risk_category,
            'relative_velocity': rel_velocity,
            'time': event['time'],
            'pinn_accelerated': mc_result.get('pinn_accelerated', True),
            'execution_time_ms': mc_result.get('execution_time_ms'),
            'total_samples': mc_result.get('samples', num_samples),
            'min_distance_km': mc_result.get('min_distance_km', distance)
        }


def main():
    """Test collision probability calculation"""
    from propagation.propagate import OrbitPropagator
    from propagation.distance_check import CloseApproachDetector
    from datetime import datetime
    
    print("=" * 70)
    print("COLLISION PROBABILITY ANALYSIS")
    print("=" * 70)
    
    # Load objects
    prop1 = OrbitPropagator('data/iss.txt')
    prop2 = OrbitPropagator('data/debris1.txt')
    
    # Generate trajectories
    start_time = datetime.utcnow()
    traj1 = prop1.propagate_trajectory(start_time, 90, 60)
    traj2 = prop2.propagate_trajectory(start_time, 90, 60)
    
    # Detect close approaches
    detector = CloseApproachDetector(threshold_km=1000.0)
    events = detector.check_trajectories(traj1, traj2)
    
    if events:
        # Analyze closest approach
        closest_event = detector.find_closest_approach()
        
        print(f"\nAnalyzing Closest Approach:")
        print(f"  Time: {closest_event['time']}")
        print(f"  Distance: {closest_event['distance']:.2f} km")
        print(f"  Relative Velocity: {closest_event['relative_velocity']:.3f} km/s")
        print()
        
        # Calculate probability
        calc = CollisionProbability(position_uncertainty=1.0, velocity_uncertainty=0.001)
        risk = calc.assess_risk(closest_event, object_radius_1=0.01, object_radius_2=0.01)
        
        print("Risk Assessment:")
        print("-" * 70)
        print(f"  Combined Radius: {risk['combined_radius']*1000:.1f} m")
        print(f"  Probability (2D Model): {risk['probability_2d']:.6f} ({risk['probability_2d']*100:.4f}%)")
        print(f"  Probability (Monte Carlo): {risk['probability_monte_carlo']:.6f} ({risk['probability_monte_carlo']*100:.4f}%)")
        print(f"  Average Probability: {risk['probability_average']:.6f} ({risk['probability_average']*100:.4f}%)")
        print(f"  Risk Category: {risk['risk_category']}")
        print("=" * 70)
    else:
        print("No close approaches detected for probability analysis.")

if __name__ == "__main__":
    main()
