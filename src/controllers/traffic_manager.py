import time
from typing import Dict, List, Tuple, Optional, Any

from src.models.nav_graph import NavGraph
from src.controllers.fleet_manager import FleetManager

class TrafficManager:
    """
    Manages traffic negotiation between robots to avoid collisions
    and ensure efficient navigation.
    """
    def __init__(self, nav_graph: NavGraph, fleet_manager: FleetManager):
        """
        Initialize the traffic manager.
        
        Args:
            nav_graph: NavGraph object containing the navigation graph
            fleet_manager: FleetManager object managing the robots
        """
        self.nav_graph = nav_graph
        self.fleet_manager = fleet_manager
        self.intersection_slots = {}  # Dict mapping vertex indices to timeslots
        self.lane_reservations = {}  # Dict mapping lane tuples to reservation times
        
    def update(self, current_time: float) -> None:
        """
        Update the traffic management system.
        
        Args:
            current_time: Current time in seconds
        """
        # Clear expired reservations
        self.clear_expired_reservations(current_time)
        
        # Process robots waiting at intersections
        self.process_waiting_robots()
        
    def clear_expired_reservations(self, current_time: float) -> None:
        """
        Clear expired reservations.
        
        Args:
            current_time: Current time in seconds
        """
        # Clear lane reservations
        expired_lanes = []
        for lane, (robot_id, expiry_time) in self.lane_reservations.items():
            if expiry_time < current_time:
                expired_lanes.append(lane)
                
        for lane in expired_lanes:
            del self.lane_reservations[lane]
            
        # Clear intersection reservations
        expired_slots = []
        for vertex, (robot_id, expiry_time) in self.intersection_slots.items():
            if expiry_time < current_time:
                expired_slots.append(vertex)
                
        for vertex in expired_slots:
            del self.intersection_slots[vertex]
            
    def process_waiting_robots(self) -> None:
        """Process robots that are waiting for a path to clear."""
        # Get all robots from the fleet manager
        robots = self.fleet_manager.get_all_robots()
        
        for robot_id, robot in robots.items():
            if robot.state == robot.WAITING:
                # Get the lane the robot is trying to enter
                lane = robot.get_current_lane()
                if lane is None:
                    continue
                    
                # Check if the lane is still blocked
                if not self.fleet_manager.is_lane_blocked(lane[0], lane[1], robot_id):
                    # Lane is clear, robot can resume movement
                    robot.resume_movement()
                    
    def reserve_lane(self, lane: Tuple[int, int], robot_id: str, 
                    duration: float = 5.0) -> bool:
        """
        Reserve a lane for a robot.
        
        Args:
            lane: Tuple (start_idx, end_idx) representing the lane
            robot_id: ID of the robot making the reservation
            duration: Duration of the reservation in seconds
            
        Returns:
            True if the reservation was successful, False otherwise
        """
        current_time = time.time()
        
        # Check if the lane is already reserved
        if lane in self.lane_reservations:
            reserved_robot_id, expiry_time = self.lane_reservations[lane]
            if reserved_robot_id != robot_id and expiry_time > current_time:
                # Lane is already reserved by another robot
                return False
                
        # Make the reservation
        self.lane_reservations[lane] = (robot_id, current_time + duration)
        return True
        
    def reserve_intersection(self, vertex_idx: int, robot_id: str, 
                            duration: float = 2.0) -> bool:
        """
        Reserve an intersection (vertex) for a robot.
        
        Args:
            vertex_idx: Index of the vertex (intersection)
            robot_id: ID of the robot making the reservation
            duration: Duration of the reservation in seconds
            
        Returns:
            True if the reservation was successful, False otherwise
        """
        current_time = time.time()
        
        # Check if the intersection is already reserved
        if vertex_idx in self.intersection_slots:
            reserved_robot_id, expiry_time = self.intersection_slots[vertex_idx]
            if reserved_robot_id != robot_id and expiry_time > current_time:
                # Intersection is already reserved by another robot
                return False
                
        # Make the reservation
        self.intersection_slots[vertex_idx] = (robot_id, current_time + duration)
        return True
        
    def check_path_availability(self, path: List[int], robot_id: str) -> bool:
        """
        Check if a path is available for a robot.
        
        Args:
            path: List of vertex indices forming the path
            robot_id: ID of the robot checking the path
            
        Returns:
            True if the path is available, False otherwise
        """
        if not path or len(path) < 2:
            return True
            
        current_time = time.time()
        
        # Check each lane in the path
        for i in range(len(path) - 1):
            start_idx = path[i]
            end_idx = path[i + 1]
            lane = (start_idx, end_idx)
            
            # Check if the lane is reserved
            if lane in self.lane_reservations:
                reserved_robot_id, expiry_time = self.lane_reservations[lane]
                if reserved_robot_id != robot_id and expiry_time > current_time:
                    # Lane is already reserved by another robot
                    return False
                    
            # Check intersections (vertices)
            if start_idx in self.intersection_slots:
                reserved_robot_id, expiry_time = self.intersection_slots[start_idx]
                if reserved_robot_id != robot_id and expiry_time > current_time:
                    # Intersection is already reserved by another robot
                    return False
        
        return True
