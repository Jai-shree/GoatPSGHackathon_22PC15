import time
import uuid
import math
from typing import Dict, List, Tuple, Optional, Any, Callable

class Robot:
    """
    Class representing a robot in the fleet management system.
    Handles robot state, movement, and task execution.
    """
    # Possible robot states
    IDLE = "idle"
    MOVING = "moving"
    WAITING = "waiting"
    CHARGING = "charging"
    TASK_COMPLETE = "task_complete"
    
    # Robot speed in units per second
    DEFAULT_SPEED = 1.0
    
    def __init__(self, robot_id: str, position_idx: int, 
                 position: Tuple[float, float], color: str):
        """
        Initialize a new robot.
        
        Args:
            robot_id: Unique identifier for the robot
            position_idx: Index of the vertex where the robot is located
            position: (x, y) coordinates of the robot
            color: Color used to display the robot
        """
        self.id = robot_id
        self.position_idx = position_idx  # Current vertex index
        self.position = position  # Current (x, y) coordinates
        self.color = color
        self.state = Robot.IDLE
        self.path = []  # List of vertex indices forming the path
        self.current_path_index = 0
        self.destination_idx = None
        self.task_id = None
        self.last_update_time = time.time()
        self.target_position = position  # Target position for movement
        self.progress = 0.0  # Progress along the current lane (0.0 to 1.0)
        self.path_blocked = False
        self.battery_level = 100.0  # Battery level (0-100)
        self.speed = Robot.DEFAULT_SPEED
        self.blocked_time = 0  # Time spent blocked
        
    def assign_task(self, destination_idx: int, path: List[int]) -> None:
        """
        Assign a navigation task to the robot.
        
        Args:
            destination_idx: Index of the destination vertex
            path: List of vertex indices forming the path
        """
        self.destination_idx = destination_idx
        self.path = path
        self.current_path_index = 0
        self.task_id = str(uuid.uuid4())[:8]  # Generate a unique task ID
        
        if self.position_idx != path[0]:
            # If the robot is not already at the start of the path
            raise ValueError(f"Robot {self.id} is not at the start of the assigned path")
            
        if len(path) == 1:
            # If the path consists of only one vertex, the robot is already at the destination
            self.state = Robot.TASK_COMPLETE
        else:
            # Set the next target in the path
            self.state = Robot.MOVING
            self.progress = 0.0
            
        # Reset blocked status
        self.path_blocked = False
        self.blocked_time = 0
    
    def get_next_vertex(self) -> Optional[int]:
        """
        Get the next vertex in the path.
        
        Returns:
            The index of the next vertex or None if at the end of the path
        """
        if not self.path or self.current_path_index >= len(self.path) - 1:
            return None
        return self.path[self.current_path_index + 1]
    
    def get_current_lane(self) -> Optional[Tuple[int, int]]:
        """
        Get the current lane the robot is on.
        
        Returns:
            Tuple (start_idx, end_idx) representing the lane, or None if not moving
        """
        if self.state != Robot.MOVING or not self.path or self.current_path_index >= len(self.path) - 1:
            return None
            
        return (self.path[self.current_path_index], self.path[self.current_path_index + 1])
    
    def set_waiting(self) -> None:
        """Set the robot state to waiting (blocked by traffic)."""
        if self.state != Robot.WAITING:
            self.state = Robot.WAITING
            self.blocked_time = time.time()
    
    def resume_movement(self) -> None:
        """Resume movement after waiting."""
        if self.state == Robot.WAITING:
            self.state = Robot.MOVING
            self.blocked_time = 0
    
    def update(self, delta_time: float, 
               get_vertex_coords: Callable[[int], Tuple[float, float]],
               calculate_distance: Callable[[int, int], float],
               is_lane_blocked: Callable[[int, int, str], bool]) -> bool:
        """
        Update the robot's state and position.
        
        Args:
            delta_time: Time elapsed since the last update (in seconds)
            get_vertex_coords: Function to get coordinates of a vertex by index
            calculate_distance: Function to calculate distance between two vertices
            is_lane_blocked: Function to check if a lane is blocked by another robot
            
        Returns:
            True if the robot's state or position has changed, False otherwise
        """
        if self.state not in [Robot.MOVING, Robot.WAITING]:
            return False
            
        # If robot is waiting, check if path is still blocked
        if self.state == Robot.WAITING:
            current_vertex = self.path[self.current_path_index]
            next_vertex = self.get_next_vertex()
            
            if next_vertex is not None and not is_lane_blocked(current_vertex, next_vertex, self.id):
                # Path is clear, resume movement
                self.resume_movement()
            else:
                # Still blocked
                return False
        
        # Robot is moving
        if self.current_path_index < len(self.path) - 1:
            current_vertex_idx = self.path[self.current_path_index]
            next_vertex_idx = self.path[self.current_path_index + 1]
            
            # Check if the lane to the next vertex is blocked
            if is_lane_blocked(current_vertex_idx, next_vertex_idx, self.id):
                self.set_waiting()
                return True
            
            start_pos = get_vertex_coords(current_vertex_idx)
            end_pos = get_vertex_coords(next_vertex_idx)
            
            # Calculate distance between vertices
            total_distance = calculate_distance(current_vertex_idx, next_vertex_idx)
            
            # Update progress along the current lane
            distance_to_move = self.speed * delta_time
            progress_increment = distance_to_move / total_distance if total_distance > 0 else 1.0
            
            self.progress += progress_increment
            
            # Clamp progress to [0, 1]
            self.progress = min(1.0, max(0.0, self.progress))
            
            # Calculate new position by linear interpolation
            self.position = (
                start_pos[0] + (end_pos[0] - start_pos[0]) * self.progress,
                start_pos[1] + (end_pos[1] - start_pos[1]) * self.progress
            )
            
            # If we've reached the next vertex
            if self.progress >= 1.0:
                self.position = end_pos
                self.position_idx = next_vertex_idx
                self.current_path_index += 1
                self.progress = 0.0
                
                # Check if we've reached the destination
                if self.current_path_index >= len(self.path) - 1:
                    self.state = Robot.TASK_COMPLETE
                    return True
            
            # Reduce battery level as the robot moves
            self.battery_level = max(0.0, self.battery_level - 0.01 * distance_to_move)
            
            return True
        
        return False
        
    def get_position(self) -> Tuple[float, float]:
        """
        Get the current position of the robot.
        
        Returns:
            Tuple (x, y) representing the coordinates
        """
        return self.position
        
    def get_status_text(self) -> str:
        """
        Get a text representation of the robot's status.
        
        Returns:
            String describing the robot's state
        """
        if self.state == Robot.IDLE:
            return f"Robot {self.id}: Idle"
        elif self.state == Robot.MOVING:
            return f"Robot {self.id}: Moving to {self.destination_idx}"
        elif self.state == Robot.WAITING:
            return f"Robot {self.id}: Waiting (blocked)"
        elif self.state == Robot.CHARGING:
            return f"Robot {self.id}: Charging ({self.battery_level:.0f}%)"
        elif self.state == Robot.TASK_COMPLETE:
            return f"Robot {self.id}: Task Complete"
        else:
            return f"Robot {self.id}: Unknown state"
