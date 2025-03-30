import json
import os
import math
from typing import Dict, List, Tuple, Optional, Any

class NavGraph:
    """
    Class representing the navigation graph with vertices and lanes.
    Handles loading, parsing, and providing access to the graph data.
    """
    def __init__(self, graph_file_path: str):
        """
        Initialize the navigation graph from a JSON file.
        
        Args:
            graph_file_path: Path to the JSON file containing the graph data
        """
        self.graph_file_path = graph_file_path
        self.vertices = []  # List of vertices
        self.lanes = []  # List of lanes
        self.adjacency_list = {}  # Adjacency list for path finding
        self.load_graph()
        
    def load_graph(self) -> None:
        """Load and parse the navigation graph from the JSON file."""
        try:
            with open(self.graph_file_path, 'r') as file:
                data = json.load(file)
            
            # Get the first level in the data
            level_key = list(data['levels'].keys())[0]
            level_data = data['levels'][level_key]
            
            # Process vertices
            self.vertices = []
            for i, vertex_data in enumerate(level_data['vertices']):
                x, y = vertex_data[0], vertex_data[1]
                attrs = vertex_data[2] if len(vertex_data) > 2 else {}
                
                # If no name is provided, use the index as the name
                if 'name' in attrs and not attrs['name']:
                    attrs['name'] = f"v{i}"
                    
                self.vertices.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'attrs': attrs
                })
            
            # Process lanes
            self.lanes = []
            for lane_data in level_data['lanes']:
                start_idx, end_idx = lane_data[0], lane_data[1]
                attrs = lane_data[2] if len(lane_data) > 2 else {}
                
                self.lanes.append({
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'attrs': attrs,
                    # Calculate the lane length for path finding
                    'length': self.calculate_distance(start_idx, end_idx)
                })
                
            # Build adjacency list for pathfinding
            self.build_adjacency_list()
            
        except Exception as e:
            print(f"Error loading navigation graph: {e}")
            raise
    
    def build_adjacency_list(self) -> None:
        """Build an adjacency list representation of the graph for pathfinding."""
        self.adjacency_list = {i: [] for i in range(len(self.vertices))}
        
        for lane in self.lanes:
            start_idx = lane['start_idx']
            end_idx = lane['end_idx']
            length = lane['length']
            
            # Add the destination and distance to the adjacency list
            self.adjacency_list[start_idx].append((end_idx, length))
    
    def calculate_distance(self, start_idx: int, end_idx: int) -> float:
        """
        Calculate the Euclidean distance between two vertices.
        
        Args:
            start_idx: Index of the start vertex
            end_idx: Index of the end vertex
            
        Returns:
            The distance between the vertices
        """
        start_vertex = self.vertices[start_idx]
        end_vertex = self.vertices[end_idx]
        
        return math.sqrt(
            (start_vertex['x'] - end_vertex['x']) ** 2 + 
            (start_vertex['y'] - end_vertex['y']) ** 2
        )
    
    def get_vertex_by_index(self, index: int) -> dict:
        """
        Get a vertex by its index.
        
        Args:
            index: The index of the vertex
            
        Returns:
            The vertex data
        """
        return self.vertices[index]
    
    def get_lane(self, start_idx: int, end_idx: int) -> Optional[dict]:
        """
        Get a lane connecting two vertices.
        
        Args:
            start_idx: Index of the start vertex
            end_idx: Index of the end vertex
            
        Returns:
            The lane data if it exists, None otherwise
        """
        for lane in self.lanes:
            if lane['start_idx'] == start_idx and lane['end_idx'] == end_idx:
                return lane
        return None
    
    def get_chargers(self) -> List[dict]:
        """
        Get all charging stations in the graph.
        
        Returns:
            List of vertices that are chargers
        """
        return [
            vertex for vertex in self.vertices 
            if 'is_charger' in vertex['attrs'] and vertex['attrs']['is_charger']
        ]
    
    def get_vertex_coords(self, index: int) -> Tuple[float, float]:
        """
        Get the coordinates of a vertex by its index.
        
        Args:
            index: The index of the vertex
            
        Returns:
            Tuple containing the x and y coordinates
        """
        vertex = self.vertices[index]
        return (vertex['x'], vertex['y'])
    
    def get_vertex_name(self, index: int) -> str:
        """
        Get the name of a vertex by its index.
        
        Args:
            index: The index of the vertex
            
        Returns:
            The name of the vertex
        """
        vertex = self.vertices[index]
        return vertex['attrs'].get('name', f"v{index}")
    
    def find_shortest_path(self, start_idx: int, end_idx: int) -> List[int]:
        """
        Find the shortest path between two vertices using Dijkstra's algorithm.
        
        Args:
            start_idx: Index of the start vertex
            end_idx: Index of the end vertex
            
        Returns:
            List of vertex indices forming the shortest path
        """
        if start_idx == end_idx:
            return [start_idx]
            
        # Initialize distances with infinity for all vertices except the start
        distances = {i: float('infinity') for i in range(len(self.vertices))}
        distances[start_idx] = 0
        
        # Previous vertex in optimal path
        previous = {i: None for i in range(len(self.vertices))}
        
        # Vertices that still need to be processed
        unvisited = set(range(len(self.vertices)))
        
        while unvisited:
            # Find the unvisited vertex with minimum distance
            current = min(unvisited, key=lambda x: distances[x])
            
            # If we've reached the end or there's no path
            if current == end_idx or distances[current] == float('infinity'):
                break
                
            # Remove the current vertex from unvisited
            unvisited.remove(current)
            
            # Check all neighbors of the current vertex
            for neighbor, length in self.adjacency_list[current]:
                # Calculate the distance through the current vertex
                alternative_route = distances[current] + length
                
                # If this path is shorter than the current shortest path
                if alternative_route < distances[neighbor]:
                    distances[neighbor] = alternative_route
                    previous[neighbor] = current
        
        # Build the path from end to start
        path = []
        current = end_idx
        
        # If there's no path to the destination
        if previous[current] is None and current != start_idx:
            return []
            
        # Reconstruct the path
        while current is not None:
            path.append(current)
            current = previous[current]
            
        # Reverse the path to get it from start to end
        return path[::-1]
