"""
Close Approach Detection
Identifies when two objects come dangerously close
"""

import numpy as np
from datetime import datetime, timedelta

class CloseApproachDetector:
    """Detect potential collisions between space objects"""
    
    # Threshold distances (km)
    ALERT_ZONE = 5.0      # Start monitoring
    DANGER_ZONE = 1.0     # High risk
    CRITICAL_ZONE = 0.5   # Imminent collision
    
    def __init__(self, threshold_km=5.0):
        """
        Initialize detector
        
        Args:
            threshold_km: Distance threshold for close approach (km)
        """
        self.threshold = threshold_km
        self.close_approaches = []
    
    @staticmethod
    def calculate_distance(pos1, pos2):
        """
        Calculate Euclidean distance between two positions
        
        Args:
            pos1: Position vector [x, y, z] in km
            pos2: Position vector [x, y, z] in km
        
        Returns:
            float: Distance in km
        """
        return np.linalg.norm(pos1 - pos2)
    
    @staticmethod
    def calculate_relative_velocity(vel1, vel2):
        """
        Calculate relative velocity between two objects
        
        Args:
            vel1: Velocity vector [vx, vy, vz] in km/s
            vel2: Velocity vector [vx, vy, vz] in km/s
        
        Returns:
            float: Relative velocity magnitude in km/s
        """
        return np.linalg.norm(vel1 - vel2)
    
    def check_trajectories(self, traj1, traj2):
        """
        Check two trajectories for close approaches
        
        Args:
            traj1: List of states for object 1
            traj2: List of states for object 2
        
        Returns:
            list: Close approach events with details
        """
        self.close_approaches = []
        
        # Ensure trajectories have same length
        min_length = min(len(traj1), len(traj2))
        
        print(f"Analyzing {min_length} time steps...")
        print(f"Threshold: {self.threshold} km\n")
        
        for i in range(min_length):
            state1 = traj1[i]
            state2 = traj2[i]
            
            pos1 = state1['position']
            pos2 = state2['position']
            vel1 = state1['velocity']
            vel2 = state2['velocity']
            
            # Calculate distance
            # Ensure numeric arrays and compute distance as Python float
            pos1 = np.asarray(pos1, dtype=float)
            pos2 = np.asarray(pos2, dtype=float)
            distance = float(self.calculate_distance(pos1, pos2))
            
            # Check if within threshold
            if distance <= self.threshold:
                rel_velocity = float(self.calculate_relative_velocity(np.asarray(vel1, dtype=float), np.asarray(vel2, dtype=float)))
                
                # Classify risk level
                if distance <= self.CRITICAL_ZONE:
                    risk_level = "CRITICAL"
                elif distance <= self.DANGER_ZONE:
                    risk_level = "DANGER"
                elif distance <= self.ALERT_ZONE:
                    risk_level = "ALERT"
                else:
                    risk_level = "MONITOR"
                
                event = {
                    'time': state1['time'],
                    'distance': distance,
                    'relative_velocity': rel_velocity,
                    'position1': pos1,
                    'position2': pos2,
                    'velocity1': vel1,
                    'velocity2': vel2,
                    'risk_level': risk_level
                }
                
                self.close_approaches.append(event)
        
        return self.close_approaches
    
    def find_closest_approach(self):
        """
        Find the point of closest approach
        
        Returns:
            dict: Event with minimum distance, or None
        """
        if not self.close_approaches:
            return None
        
        return min(self.close_approaches, key=lambda x: x['distance'])
    
    def get_risk_summary(self):
        """
        Generate summary of detected close approaches
        
        Returns:
            dict: Summary statistics
        """
        if not self.close_approaches:
            return {
                'total_events': 0,
                'closest_distance': None,
                'risk_levels': {}
            }
        
        # Count by risk level
        risk_counts = {}
        for event in self.close_approaches:
            level = event['risk_level']
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        closest = self.find_closest_approach()
        
        return {
            'total_events': len(self.close_approaches),
            'closest_distance': closest['distance'],
            'closest_time': closest['time'],
            'risk_levels': risk_counts,
            'max_relative_velocity': max(e['relative_velocity'] for e in self.close_approaches)
        }
    
    def print_summary(self):
        """Print human-readable summary"""
        summary = self.get_risk_summary()
        
        print("=" * 60)
        print("CLOSE APPROACH DETECTION SUMMARY")
        print("=" * 60)
        
        if summary['total_events'] == 0:
            print("✓ No close approaches detected")
            print(f"  All distances > {self.threshold} km")
        else:
            print(f"⚠ Total Events: {summary['total_events']}")
            print(f"  Closest Distance: {summary['closest_distance']:.3f} km")
            print(f"  Time of Closest Approach: {summary['closest_time']}")
            print(f"  Max Relative Velocity: {summary['max_relative_velocity']:.3f} km/s")
            print()
            print("Risk Level Breakdown:")
            for level, count in summary['risk_levels'].items():
                print(f"  {level}: {count} events")
        
        print("=" * 60)


def main():
    """Test close approach detection"""
    from propagation.propagate import OrbitPropagator
    
    print("Testing Close Approach Detection")
    print("=" * 60)
    
    # Load two objects
    prop1 = OrbitPropagator('data/iss.txt')
    prop2 = OrbitPropagator('data/debris1.txt')
    
    # Generate trajectories
    start_time = datetime.utcnow()
    traj1 = prop1.propagate_trajectory(start_time, duration_minutes=90, step_seconds=60)
    traj2 = prop2.propagate_trajectory(start_time, duration_minutes=90, step_seconds=60)
    
    # Detect close approaches
    detector = CloseApproachDetector(threshold_km=1000.0)  # 1000 km for testing
    events = detector.check_trajectories(traj1, traj2)
    
    # Print results
    detector.print_summary()
    
    if events:
        print("\nFirst 3 Close Approach Events:")
        print("-" * 60)
        for event in events[:3]:
            print(f"Time: {event['time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Distance: {event['distance']:.2f} km")
            print(f"  Relative Velocity: {event['relative_velocity']:.3f} km/s")
            print(f"  Risk Level: {event['risk_level']}")
            print()

if __name__ == "__main__":
    main()
