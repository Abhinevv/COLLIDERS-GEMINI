"""
AstroCleanAI - Main Controller
Complete collision avoidance pipeline
"""

from datetime import datetime, timedelta, timezone
import os
import warnings

# Import modules
from fetch_tle import TLEFetcher
from propagation.propagate import OrbitPropagator
from propagation.distance_check import CloseApproachDetector
from probability.collision_probability import CollisionProbability
from optimization.avoidance import AvoidanceManeuver
from visualization.plot_orbits import OrbitVisualizer


class AstroCleanAI:
    """Main collision avoidance system controller"""
    
    def __init__(self):
        self.satellite_prop = None
        self.debris_prop = None
        self.detector = None
        self.probability_calc = None
        self.optimizer = None
        self.visualizer = None
    
    def setup(self, satellite_tle, debris_tle):
        """
        Initialize system with TLE files
        
        Args:
            satellite_tle: Path to satellite TLE file
            debris_tle: Path to debris TLE file
        """
        print("=" * 80)
        print("ASTROCLEANAI - COLLISION AVOIDANCE SYSTEM")
        print("=" * 80)
        print("\n[1/5] Loading Orbital Data...")
        
        self.satellite_prop = OrbitPropagator(satellite_tle)
        self.debris_prop = OrbitPropagator(debris_tle)
        
        print(f"  Primary Object: {self.satellite_prop.name}")
        print(f"  Threat Object: {self.debris_prop.name}")
        
        # Initialize components
        self.detector = CloseApproachDetector(threshold_km=10.0)
        self.probability_calc = CollisionProbability(
            position_uncertainty=1.0,  # 1 km
            velocity_uncertainty=0.001  # 1 m/s
        )
        self.optimizer = AvoidanceManeuver(self.satellite_prop, max_dv=10.0)
        self.visualizer = OrbitVisualizer()
        
        print("✓ System initialized\n")
    
    def analyze_conjunction(self, start_time, duration_minutes=180, step_seconds=60):
        """
        Analyze conjunction scenario
        
        Args:
            start_time: Analysis start time
            duration_minutes: Duration to analyze
            step_seconds: Time step
        
        Returns:
            dict: Analysis results
        """
        print("[2/5] Propagating Orbits...")
        print(f"  Start Time: {start_time}")
        print(f"  Duration: {duration_minutes} minutes")
        print(f"  Time Step: {step_seconds} seconds")
        
        # Propagate trajectories
        traj_sat = self.satellite_prop.propagate_trajectory(
            start_time, duration_minutes, step_seconds
        )
        traj_debris = self.debris_prop.propagate_trajectory(
            start_time, duration_minutes, step_seconds
        )
        
        print(f"✓ Generated {len(traj_sat)} trajectory points\n")
        
        # Detect close approaches
        print("[3/5] Detecting Close Approaches...")
        events = self.detector.check_trajectories(traj_sat, traj_debris)
        
        if not events:
            print("✓ No close approaches detected - Safe trajectory")
            return {
                'safe': True,
                'events': [],
                'trajectories': (traj_sat, traj_debris)
            }
        
        self.detector.print_summary()
        
        # Analyze closest approach
        closest = self.detector.find_closest_approach()
        
        print("\n[4/5] Calculating Collision Probability...")
        risk_assessment = self.probability_calc.assess_risk(
            closest,
            object_radius_1=0.01,  # 10m satellite
            object_radius_2=0.01   # 10m debris
        )
        
        print(f"  Distance: {risk_assessment['distance']:.3f} km")
        print(f"  Collision Probability: {risk_assessment['probability_average']:.6f}")
        print(f"  Risk Category: {risk_assessment['risk_category']}")
        
        return {
            'safe': False,
            'events': events,
            'closest_approach': closest,
            'risk_assessment': risk_assessment,
            'trajectories': (traj_sat, traj_debris)
        }
    
    def plan_avoidance(self, closest_approach, lead_time_minutes=60):
        """
        Plan collision avoidance maneuver
        
        Args:
            closest_approach: Closest approach event
            lead_time_minutes: How long before CA to execute burn
        
        Returns:
            dict: Maneuver plan
        """
        print("\n[5/5] Optimizing Avoidance Maneuver...")
        
        # Schedule burn before closest approach
        ca_time = closest_approach['time']
        burn_time = ca_time - timedelta(minutes=lead_time_minutes)
        
        print(f"  Closest Approach: {ca_time}")
        print(f"  Burn Scheduled: {burn_time}")
        print(f"  Lead Time: {lead_time_minutes} minutes\n")
        
        # Optimize using grid search
    
        print("  Running optimization algorithm...")
        maneuver = self.optimizer.optimize_maneuver(
            burn_time,
            self.debris_prop,
            dv_range=(0.1, 3.0),
            dv_step=0.2
        )
        
        print()
        self.optimizer.print_maneuver_plan(maneuver)
        
        return maneuver
    
    def visualize_scenario(self, analysis_result, output_file='output/collision_scenario.html'):
        """
        Create visualization
        
        Args:
            analysis_result: Results from analyze_conjunction
            output_file: Output HTML file path
        """
        print("\nGenerating Visualization...")
        
        traj_sat, traj_debris = analysis_result['trajectories']
        
        if analysis_result['safe']:
            # Just show orbits
            self.visualizer.plot_collision_scenario(
                traj_sat, traj_debris,
                name1=self.satellite_prop.name,
                name2=self.debris_prop.name
            )
        else:
            # Show collision scenario
            closest = analysis_result['closest_approach']
            self.visualizer.plot_collision_scenario(
                traj_sat, traj_debris, closest,
                name1=self.satellite_prop.name,
                name2=self.debris_prop.name
            )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Get satellite information
        satellite_info1 = self.satellite_prop.get_satellite_info()
        satellite_info2 = self.debris_prop.get_satellite_info()
        
        # Save visualization with analysis results for enhanced dashboard
        self.visualizer.save_html(output_file, analysis_result=analysis_result, 
                                  satellite_info1=satellite_info1, satellite_info2=satellite_info2)
        print(f"✓ Open {output_file} in your browser to view")
    
    def run_complete_analysis(self):
        """Run full collision avoidance analysis pipeline"""
        
        # Step 1: Analyze conjunction
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC timezone-aware
        analysis = self.analyze_conjunction(
            start_time,
            duration_minutes=180,
            step_seconds=60
        )
        
        # Step 2: If unsafe, plan maneuver
        if not analysis['safe']:
            maneuver = self.plan_avoidance(
                analysis['closest_approach'],
                lead_time_minutes=60
            )
        
        # Step 3: Visualize
        self.visualize_scenario(analysis)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
        if analysis['safe']:
            print("✓ STATUS: SAFE - No collision avoidance required")
        else:
            print("⚠ STATUS: COLLISION RISK DETECTED")
            print(f"  Probability: {analysis['risk_assessment']['probability_average']*100:.4f}%")
            print(f"  Recommended Action: Execute avoidance maneuver")
        
        print("=" * 80 + "\n")


def download_tle_data():
    """Download fresh TLE data from Celestrak"""
    print("Downloading latest TLE data...\n")
    
    fetcher = TLEFetcher()
    satellites = {
        '25544': 'iss.txt',        # ISS (International Space Station)
        '43013': 'debris1.txt',     # HST (Hubble Space Telescope) - active, well-tracked
    }
    
    fetcher.fetch_multiple(satellites)
    print()


def main():
    """Main entry point"""
    
    # Check if TLE data exists, download if not
    if not os.path.exists('data/iss.txt'):
        download_tle_data()
    
    # Initialize system
    system = AstroCleanAI()
    system.setup(
        satellite_tle='data/iss.txt',
        debris_tle='data/debris1.txt'
    )
    
    # Run complete analysis
    system.run_complete_analysis()


if __name__ == "__main__":
    main()
