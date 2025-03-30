import time
import random
from typing import Dict, List, Tuple, Optional, Any
import os
from datetime import datetime

from src.models.robot import Robot
from src.models.nav_graph import NavGraph

class FleetManager:
    """
    Manages the fleet of robots, including creation, task assignment,
    and status tracking.
    """
    # List of colors for robots
    ROBOT_COLORS = [
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", 
        "#00FFFF", "#FF8000", "#8000FF", "#0080FF", "#FF0080"
    ]
    
    def __init__(self, nav_graph: NavGraph, log_file_path: str):
        """
        Initialize the fleet manager.
        
        Args:
            nav_graph: NavGraph object containing the navigation graph
            log_file_path: Path to the log file
        """
        self.nav_graph = nav_graph
        self.robots = {}  # Dictionary mapping robot IDs to Robot objects
        self.robot_count = 0  # Counter for generating robot IDs
        self.occupied_lanes = {}  # Dictionary mapping lane tuples to robot IDs
        self.log_file_path = log_file_path
        self.ensure_log_file_exists()
        
    def ensure_log_file_exists(self) -> None:
        """Create the log file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w') as f:
                f.write(f"Fleet Management System Log - Started at {datetime.now()}\n")
                f.write("-" * 80 + "\n")
    
    def log_event(self, message: str) -> None:
        """
        Log an event to the log file.
        
        Args:
            message: The message to log
        """
        try:
            with open(self.log_file_path, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def create_robot(self, vertex_idx: int) -> str:
        """
        Create a new robot at the specified vertex.
        
        Args:
            vertex_idx: Index of the vertex where the robot should be created
            
        Returns:
            The ID of the created robot
        """
        # Generate a unique ID for the robot
        robot_id = f"R{self.robot_count + 1}"
        self.robot_count += 1
        
        # Get the vertex coordinates
        vertex_coords = self.nav_graph.get_vertex_coords(vertex_idx)
        
        # Choose a color for the robot
        color = self.ROBOT_COLORS[self.robot_count % len(self.ROBOT_COLORS)]
        
        # Create the robot
        robot = Robot(robot_id, vertex_idx, vertex_coords, color)
        
        # Add the robot to the dictionary
        self.robots[robot_id] = robot
        
        # Log the creation event
        vertex_name = self.nav_graph.get_vertex_name(vertex_idx)
        self.log_event(f"Robot {robot_id} created at vertex {vertex_name} (index: {vertex_idx})")
        
        return robot_id
    
    def assign_task(self, robot_id: str, destination_idx: int) -> bool:
        """
        Assign a navigation task to a robot.
        
        Args:
            robot_id: ID of the robot
            destination_idx: Index of the destination vertex
            
        Returns:
            True if the task was assigned successfully, False otherwise
        """
        if robot_id not in self.robots:
            self.log_event(f"Error: Cannot assign task - Robot {robot_id} does not exist")
            return False
            
        robot = self.robots[robot_id]
        
        # If robot is already moving, don't assign a new task
        if robot.state in [Robot.MOVING, Robot.WAITING]:
            self.log_event(f"Error: Cannot assign task - Robot {robot_id} is already moving or waiting")
            return False
            
        # Find the shortest path from the robot's current position to the destination
        start_idx = robot.position_idx
        path = self.nav_graph.find_shortest_path(start_idx, destination_idx)
        
        if not path:
            self.log_event(f"Error: Cannot assign task - No path found from vertex {start_idx} to {destination_idx}")
            return False
            
        # Assign the task to the robot
        try:
            robot.assign_task(destination_idx, path)
            start_name = self.nav_graph.get_vertex_name(start_idx)
            dest_name = self.nav_graph.get_vertex_name(destination_idx)
            self.log_event(f"Task assigned to Robot {robot_id}: Navigate from {start_name} to {dest_name}")
            return True
        except Exception as e:
            self.log_event(f"Error assigning task to Robot {robot_id}: {e}")
            return False
    
    def update_robots(self, delta_time: float) -> None:
        """
        Update the state and position of all robots.
        
        Args:
            delta_time: Time elapsed since the last update (in seconds)
        """
        # Clear occupied lanes
        self.occupied_lanes = {}
        
        # First, mark all occupied lanes
        for robot_id, robot in self.robots.items():
            lane = robot.get_current_lane()
            if lane is not None:
                self.occupied_lanes[lane] = robot_id
        
        # Then update each robot
        for robot_id, robot in self.robots.items():
            # Update the robot's state and position
            state_changed = robot.update(
                delta_time, 
                self.nav_graph.get_vertex_coords,
                self.nav_graph.calculate_distance,
                self.is_lane_blocked
            )
            
            # If robot's state changed, update the occupied lanes and log
            if state_changed:
                lane = robot.get_current_lane()
                if lane is not None:
                    self.occupied_lanes[lane] = robot_id
                    
                # Log state changes
                if robot.state == Robot.TASK_COMPLETE:
                    dest_name = self.nav_graph.get_vertex_name(robot.destination_idx)
                    self.log_event(f"Robot {robot_id} arrived at destination {dest_name}")
                elif robot.state == Robot.WAITING:
                    lane = robot.get_current_lane()
                    if lane:
                        blocking_robot_id = self.occupied_lanes.get(lane)
                        self.log_event(f"Robot {robot_id} waiting: Lane from {lane[0]} to {lane[1]} blocked by Robot {blocking_robot_id}")
                elif robot.state == Robot.MOVING and robot.current_path_index < len(robot.path) - 1:
                    # Log movement to a new vertex
                    prev_idx = robot.path[robot.current_path_index - 1] if robot.current_path_index > 0 else None
                    curr_idx = robot.path[robot.current_path_index]
                    next_idx = robot.path[robot.current_path_index + 1]
                    
                    if prev_idx is not None and prev_idx != curr_idx:
                        from_name = self.nav_graph.get_vertex_name(prev_idx)
                        to_name = self.nav_graph.get_vertex_name(curr_idx)
                        self.log_event(f"Robot {robot_id} moved from {from_name} to {to_name}")
    
    def is_lane_blocked(self, start_idx: int, end_idx: int, robot_id: str) -> bool:
        """
        Check if a lane is blocked by another robot.
        
        Args:
            start_idx: Index of the start vertex of the lane
            end_idx: Index of the end vertex of the lane
            robot_id: ID of the robot making the request (to avoid self-blocking)
            
        Returns:
            True if the lane is blocked, False otherwise
        """
        lane = (start_idx, end_idx)
        blocking_robot_id = self.occupied_lanes.get(lane)
        
        return blocking_robot_id is not None and blocking_robot_id != robot_id
        
    def get_robot_by_id(self, robot_id: str) -> Optional[Robot]:
        """
        Get a robot by its ID.
        
        Args:
            robot_id: ID of the robot
            
        Returns:
            The Robot object if found, None otherwise
        """
        return self.robots.get(robot_id)
        
    def get_all_robots(self) -> Dict[str, Robot]:
        """
        Get all robots.
        
        Returns:
            Dictionary mapping robot IDs to Robot objects
        """
        return self.robots
