import math
import random
import time
from typing import Dict, List, Tuple, Optional, Any

def euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate the Euclidean distance between two points.
    
    Args:
        point1: First point as (x, y)
        point2: Second point as (x, y)
        
    Returns:
        The Euclidean distance between the points
    """
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

def lerp(start: float, end: float, t: float) -> float:
    """
    Linear interpolation between start and end by factor t.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return start + (end - start) * t

def lerp_points(start: Tuple[float, float], end: Tuple[float, float], t: float) -> Tuple[float, float]:
    """
    Linear interpolation between two points by factor t.
    
    Args:
        start: Starting point as (x, y)
        end: Ending point as (x, y)
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated point as (x, y)
    """
    return (lerp(start[0], end[0], t), lerp(start[1], end[1], t))

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))

def is_point_near_line(point: Tuple[float, float], 
                      line_start: Tuple[float, float], 
                      line_end: Tuple[float, float], 
                      threshold: float = 0.1) -> bool:
    """
    Check if a point is near a line segment.
    
    Args:
        point: Point to check as (x, y)
        line_start: Start point of the line as (x, y)
        line_end: End point of the line as (x, y)
        threshold: Maximum distance to consider the point near the line
        
    Returns:
        True if the point is near the line segment, False otherwise
    """
    # Vector from line_start to line_end
    line_vector = (line_end[0] - line_start[0], line_end[1] - line_start[1])
    
    # Length of the line segment squared
    line_length_sq = line_vector[0] ** 2 + line_vector[1] ** 2
    
    if line_length_sq == 0:
        # Line segment is a point
        return euclidean_distance(point, line_start) <= threshold
    
    # Calculate the projection of the point onto the line
    t = max(0, min(1, ((point[0] - line_start[0]) * line_vector[0] + 
                      (point[1] - line_start[1]) * line_vector[1]) / 
                      line_length_sq))
    
    # Calculate the closest point on the line segment
    closest_point = (
        line_start[0] + t * line_vector[0],
        line_start[1] + t * line_vector[1]
    )
    
    # Check if the distance to the closest point is within the threshold
    return euclidean_distance(point, closest_point) <= threshold

def generate_random_color() -> str:
    """
    Generate a random color in hexadecimal format.
    
    Returns:
        Random color as a hex string (e.g., '#FF0000')
    """
    # Generate random RGB values
    r = random.randint(100, 255)  # Avoid very dark colors
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    
    # Convert to hex format
    return f"#{r:02X}{g:02X}{b:02X}"
