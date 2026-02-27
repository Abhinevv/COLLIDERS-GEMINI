"""
Improved Collision Probability Calculation
Based on NASA CARA methodology for conjunction assessment
"""

import numpy as np
from scipy.stats import chi2
from scipy.special import erf


class ImprovedCollisionProbability:
    """
    Calculate collision probability using proper conjunction assessment methods
    Based on NASA's Probability of Collision (Pc) calculations
    """
    
    def __init__(self, tle_uncertainty_km=2.0):
        """
        Initialize with realistic TLE uncertainty
        
        Args:
            tle_uncertainty_km: TLE position uncertainty (1-5 km typical)
        """
        self.tle_sigma = tle_uncertainty_km
    
    def calculate_pc_2d(self, miss_distance, combined_radius, 
                        sigma_primary=None, sigma_secondary=None):
        """
        Calculate Probability of Collision using 2D method on B-plane
        
        This is the standard method used by NASA CARA and ESA
        
        Args:
            miss_distance: Miss distance at TCA (km)
            combined_radius: Combined hard body radius (km)
            sigma_primary: Primary object position uncertainty (km)
            sigma_secondary: Secondary object position uncertainty (km)
        
        Returns:
            float: Collision probability (0 to 1)
        """
        # Use default TLE uncertainty if not provided
        sigma_primary = sigma_primary or self.tle_sigma
        sigma_secondary = sigma_secondary or self.tle_sigma
        
        # Combined covariance (RSS - Root Sum Square)
        sigma_combined = np.sqrt(sigma_primary**2 + sigma_secondary**2)
        
        # Normalized miss distance
        normalized_distance = miss_distance / sigma_combined
        
        # Hard body radius in sigma units
        normalized_radius = combined_radius / sigma_combined
        
        # 2D circular probability (Chan method)
        # Pc = 1 - exp(-R²/2σ²) for circular covariance
        # More accurate: use non-central chi-square
        
        if normalized_distance <= normalized_radius:
            # Objects overlap within uncertainty
            return 1.0
        
        # For well-separated objects, use approximation
        if normalized_distance > 5 * normalized_radius:
            # Very low probability, use exponential approximation
            pc = (normalized_radius**2) / (2 * normalized_distance**2) * \
                 np.exp(-(normalized_distance**2 - normalized_radius**2) / 2)
        else:
            # Use more accurate formula for intermediate cases
            # Foster's method (1992)
            x = normalized_distance
            r = normalized_radius
            
            # Probability density at miss distance
            pc = (r**2 / (2 * x**2)) * (1 - np.exp(-(x**2) / 2))
        
        return max(0.0, min(1.0, pc))
    
    def calculate_pc_elliptical(self, miss_vector, combined_radius, 
                                covariance_matrix):
        """
        Calculate Pc with elliptical covariance (more accurate)
        
        Args:
            miss_vector: 3D miss vector at TCA (km)
            combined_radius: Combined hard body radius (km)
            covariance_matrix: 3x3 combined covariance matrix
        
        Returns:
            float: Collision probability
        """
        try:
            # Project onto B-plane (perpendicular to relative velocity)
            # For simplicity, use 2D projection
            miss_2d = miss_vector[:2]
            cov_2d = covariance_matrix[:2, :2]
            
            # Mahalanobis distance
            cov_inv = np.linalg.inv(cov_2d)
            mahal_dist_sq = miss_2d.T @ cov_inv @ miss_2d
            
            # Effective radius in Mahalanobis space
            # This requires eigenvalue decomposition
            eigenvalues = np.linalg.eigvalsh(cov_2d)
            effective_sigma = np.sqrt(np.mean(eigenvalues))
            normalized_radius = combined_radius / effective_sigma
            
            # Chi-square CDF for 2 DOF
            pc = 1 - chi2.cdf(mahal_dist_sq, df=2) * \
                 (1 - chi2.cdf(normalized_radius**2, df=2))
            
            return max(0.0, min(1.0, pc))
            
        except:
            # Fallback to circular method
            miss_distance = np.linalg.norm(miss_vector)
            sigma = np.sqrt(np.trace(covariance_matrix) / 3)
            return self.calculate_pc_2d(miss_distance, combined_radius, 
                                       sigma, sigma)
    
    def monte_carlo_with_tle_uncertainty(self, sat_position, debris_position,
                                        combined_radius, num_samples=10000,
                                        sat_sigma=None, debris_sigma=None):
        """
        Monte Carlo with realistic TLE uncertainty
        
        Args:
            sat_position: Satellite position at TCA (km)
            debris_position: Debris position at TCA (km)
            combined_radius: Combined hard body radius (km)
            num_samples: Number of Monte Carlo samples
            sat_sigma: Satellite position uncertainty (km)
            debris_sigma: Debris position uncertainty (km)
        
        Returns:
            dict: Results with probability and statistics
        """
        sat_sigma = sat_sigma or self.tle_sigma
        debris_sigma = debris_sigma or self.tle_sigma
        
        # Generate samples
        sat_samples = np.random.normal(
            sat_position, sat_sigma, (num_samples, 3)
        )
        debris_samples = np.random.normal(
            debris_position, debris_sigma, (num_samples, 3)
        )
        
        # Calculate distances
        distances = np.linalg.norm(sat_samples - debris_samples, axis=1)
        
        # Count collisions
        collisions = np.sum(distances <= combined_radius)
        probability = collisions / num_samples
        
        # Calculate confidence interval (95%)
        # Using Wilson score interval
        z = 1.96  # 95% confidence
        p = probability
        n = num_samples
        
        if n > 0:
            center = (p + z**2/(2*n)) / (1 + z**2/n)
            margin = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / (1 + z**2/n)
            ci_lower = max(0, center - margin)
            ci_upper = min(1, center + margin)
        else:
            ci_lower = ci_upper = 0
        
        return {
            'probability': probability,
            'collisions': int(collisions),
            'samples': num_samples,
            'confidence_interval_95': (ci_lower, ci_upper),
            'mean_distance': float(np.mean(distances)),
            'min_distance': float(np.min(distances)),
            'std_distance': float(np.std(distances))
        }
    
    def assess_conjunction(self, sat_position, debris_position, 
                          sat_velocity, debris_velocity,
                          combined_radius=0.02,
                          sat_sigma=None, debris_sigma=None,
                          use_monte_carlo=True, mc_samples=10000):
        """
        Complete conjunction assessment
        
        Args:
            sat_position: Satellite position at TCA (km)
            debris_position: Debris position at TCA (km)
            sat_velocity: Satellite velocity (km/s)
            debris_velocity: Debris velocity (km/s)
            combined_radius: Combined hard body radius (km)
            sat_sigma: Satellite uncertainty (km)
            debris_sigma: Debris uncertainty (km)
            use_monte_carlo: Whether to run Monte Carlo
            mc_samples: Number of MC samples
        
        Returns:
            dict: Complete assessment results
        """
        sat_sigma = sat_sigma or self.tle_sigma
        debris_sigma = debris_sigma or self.tle_sigma
        
        # Calculate miss distance
        miss_vector = sat_position - debris_position
        miss_distance = np.linalg.norm(miss_vector)
        
        # Relative velocity
        rel_velocity = sat_velocity - debris_velocity
        rel_speed = np.linalg.norm(rel_velocity)
        
        # 2D Pc calculation
        pc_2d = self.calculate_pc_2d(miss_distance, combined_radius,
                                     sat_sigma, debris_sigma)
        
        # Monte Carlo if requested
        mc_result = None
        if use_monte_carlo:
            mc_result = self.monte_carlo_with_tle_uncertainty(
                sat_position, debris_position, combined_radius,
                mc_samples, sat_sigma, debris_sigma
            )
        
        # Determine recommended Pc
        if mc_result:
            # Use Monte Carlo if available (more accurate)
            recommended_pc = mc_result['probability']
        else:
            recommended_pc = pc_2d
        
        # Risk classification (NASA CARA thresholds)
        if recommended_pc >= 1e-4:  # 1 in 10,000
            risk_level = 'HIGH'
        elif recommended_pc >= 1e-5:  # 1 in 100,000
            risk_level = 'MEDIUM'
        elif recommended_pc >= 1e-6:  # 1 in 1,000,000
            risk_level = 'LOW'
        else:
            risk_level = 'NEGLIGIBLE'
        
        return {
            'miss_distance_km': miss_distance,
            'relative_velocity_km_s': rel_speed,
            'combined_radius_km': combined_radius,
            'pc_2d_method': pc_2d,
            'pc_monte_carlo': mc_result['probability'] if mc_result else None,
            'recommended_pc': recommended_pc,
            'risk_level': risk_level,
            'monte_carlo_details': mc_result,
            'uncertainties': {
                'satellite_sigma_km': sat_sigma,
                'debris_sigma_km': debris_sigma,
                'combined_sigma_km': np.sqrt(sat_sigma**2 + debris_sigma**2)
            }
        }


def main():
    """Test improved collision probability"""
    print("="*70)
    print("IMPROVED COLLISION PROBABILITY CALCULATOR")
    print("="*70)
    
    # Example conjunction scenario
    calc = ImprovedCollisionProbability(tle_uncertainty_km=2.0)
    
    # Scenario 1: Close approach
    print("\nScenario 1: Close Approach (100m miss distance)")
    print("-"*70)
    
    sat_pos = np.array([6778.0, 0.0, 0.0])  # km
    debris_pos = np.array([6778.1, 0.0, 0.0])  # 100m miss
    sat_vel = np.array([0.0, 7.5, 0.0])  # km/s
    debris_vel = np.array([0.0, 7.4, 0.0])
    
    result = calc.assess_conjunction(
        sat_pos, debris_pos, sat_vel, debris_vel,
        combined_radius=0.02,  # 20m combined radius
        use_monte_carlo=True,
        mc_samples=10000
    )
    
    print(f"Miss Distance: {result['miss_distance_km']*1000:.1f} m")
    print(f"Relative Velocity: {result['relative_velocity_km_s']:.3f} km/s")
    print(f"Pc (2D Method): {result['pc_2d_method']:.6e}")
    print(f"Pc (Monte Carlo): {result['pc_monte_carlo']:.6e}")
    print(f"Recommended Pc: {result['recommended_pc']:.6e}")
    print(f"Risk Level: {result['risk_level']}")
    
    if result['monte_carlo_details']:
        mc = result['monte_carlo_details']
        ci = mc['confidence_interval_95']
        print(f"95% CI: [{ci[0]:.6e}, {ci[1]:.6e}]")
        print(f"Collisions: {mc['collisions']}/{mc['samples']}")
    
    # Scenario 2: Safe separation
    print("\n\nScenario 2: Safe Separation (10km miss distance)")
    print("-"*70)
    
    debris_pos2 = np.array([6788.0, 0.0, 0.0])  # 10km miss
    
    result2 = calc.assess_conjunction(
        sat_pos, debris_pos2, sat_vel, debris_vel,
        combined_radius=0.02,
        use_monte_carlo=True,
        mc_samples=10000
    )
    
    print(f"Miss Distance: {result2['miss_distance_km']:.3f} km")
    print(f"Pc (2D Method): {result2['pc_2d_method']:.6e}")
    print(f"Pc (Monte Carlo): {result2['pc_monte_carlo']:.6e}")
    print(f"Risk Level: {result2['risk_level']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
