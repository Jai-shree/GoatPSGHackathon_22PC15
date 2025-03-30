import tkinter as tk
from tkinter import messagebox, Canvas, Frame, Label, Button, Scrollbar, Text
import time
import math
import threading
from typing import Dict, List, Tuple, Optional, Any, Callable
import os

from src.models.nav_graph import NavGraph
from src.models.robot import Robot
from src.controllers.fleet_manager import FleetManager
from src.controllers.traffic_manager import TrafficManager

class FleetGUI:
    """
    Graphical user interface for the Fleet Management System.
    """
    # Constants for GUI dimensions and styling
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600
    VERTEX_RADIUS = 15
    CHARGER_RADIUS = 18
    ROBOT_RADIUS = 12
    SELECTION_OUTLINE_WIDTH = 3
    LANE_WIDTH = 2
    VERTEX_COLOR = "#4CAF50"  # Green
    CHARGER_COLOR = "#FFC107"  # Amber
    LANE_COLOR = "#2196F3"  # Blue
    BACKGROUND_COLOR = "#333333"  # Dark gray
    TEXT_COLOR = "#FFFFFF"  # White
    SELECTION_COLOR = "#FF5722"  # Deep orange
    BLOCKED_COLOR = "#F44336"  # Red
    
    def __init__(self, nav_graph: NavGraph, fleet_manager: FleetManager, 
                 traffic_manager: TrafficManager):
        """
        Initialize the Fleet GUI.
        
        Args:
            nav_graph: NavGraph object containing the navigation graph
            fleet_manager: FleetManager object managing the robots
            traffic_manager: TrafficManager object managing traffic negotiation
        """
        self.nav_graph = nav_graph
        self.fleet_manager = fleet_manager
        self.traffic_manager = traffic_manager
        
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Fleet Management System")
        self.root.geometry(f"{self.CANVAS_WIDTH + 300}x{self.CANVAS_HEIGHT + 50}")
        self.root.configure(bg="#333333")
        
        # Initialize GUI components
        self.init_gui_components()
        
        # Variables for tracking state
        self.selected_robot_id = None
        self.selected_vertex_idx = None
        self.last_update_time = time.time()
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.scale_factor = 50  # Scaling factor for the graph
        
        # Calculate the bounds of the navigation graph
        self.calculate_graph_bounds()
        
        # Center the graph on the canvas
        self.center_graph()
        
        # Start the animation loop
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self.animation_loop)
        self.animation_thread.daemon = True
        self.animation_thread.start()
    
    def init_gui_components(self) -> None:
        """Initialize the GUI components."""
        # Create the main frame
        main_frame = Frame(self.root, bg="#333333")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the canvas for drawing the navigation graph and robots
        self.canvas = Canvas(
            main_frame, 
            width=self.CANVAS_WIDTH, 
            height=self.CANVAS_HEIGHT, 
            bg=self.BACKGROUND_COLOR
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse events to the canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)  # Windows/MacOS
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)  # Linux scroll down
        
        # Create the control panel
        control_panel = Frame(main_frame, bg="#333333", width=300)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # Add title label
        title_label = Label(
            control_panel, 
            text="Fleet Management System", 
            font=("Arial", 16), 
            bg="#333333", 
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        # Instructions label
        instructions_label = Label(
            control_panel, 
            text="Click on a vertex to spawn a robot.\n"
                 "Select a robot, then click a destination\n"
                 "vertex to assign a task.",
            justify=tk.LEFT, 
            bg="#333333", 
            fg="#FFFFFF"
        )
        instructions_label.pack(pady=(0, 10), anchor=tk.W)
        
        # Status label
        self.status_label = Label(
            control_panel, 
            text="Ready", 
            bg="#333333", 
            fg="#FFFFFF", 
            anchor=tk.W, 
            justify=tk.LEFT
        )
        self.status_label.pack(pady=(0, 10), fill=tk.X)
        
        # Selected robot label
        self.selected_robot_label = Label(
            control_panel, 
            text="No robot selected", 
            bg="#333333", 
            fg="#FFFFFF", 
            anchor=tk.W, 
            justify=tk.LEFT
        )
        self.selected_robot_label.pack(pady=(0, 10), fill=tk.X)
        
        # Robot list label
        robot_list_label = Label(
            control_panel, 
            text="Robots:", 
            bg="#333333", 
            fg="#FFFFFF", 
            anchor=tk.W
        )
        robot_list_label.pack(anchor=tk.W)
        
        # Robot list container
        robot_list_frame = Frame(control_panel, bg="#333333")
        robot_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Robot list box
        self.robot_list = Text(
            robot_list_frame, 
            height=10, 
            width=40, 
            bg="#222222", 
            fg="#FFFFFF", 
            wrap=tk.WORD
        )
        self.robot_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for robot list
        robot_list_scrollbar = Scrollbar(robot_list_frame)
        robot_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Connect scrollbar and text widget
        self.robot_list.config(yscrollcommand=robot_list_scrollbar.set)
        robot_list_scrollbar.config(command=self.robot_list.yview)
        
        # Button frame
        button_frame = Frame(control_panel, bg="#333333")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Reset view button
        reset_view_button = Button(
            button_frame, 
            text="Reset View", 
            command=self.reset_view,
            bg="#4CAF50", 
            fg="#FFFFFF", 
            activebackground="#45a049", 
            activeforeground="#FFFFFF", 
            bd=0, 
            padx=10, 
            pady=5
        )
        reset_view_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear selection button
        clear_selection_button = Button(
            button_frame, 
            text="Clear Selection", 
            command=self.clear_selection,
            bg="#2196F3", 
            fg="#FFFFFF", 
            activebackground="#0b7dda", 
            activeforeground="#FFFFFF", 
            bd=0, 
            padx=10, 
            pady=5
        )
        clear_selection_button.pack(side=tk.LEFT)
        
        # Status bar at the bottom
        status_frame = Frame(self.root, bg="#222222", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_bar = Label(
            status_frame, 
            text="System Ready", 
            bg="#222222", 
            fg="#FFFFFF", 
            anchor=tk.W, 
            padx=10
        )
        self.status_bar.pack(fill=tk.X)
    
    def calculate_graph_bounds(self) -> None:
        """Calculate the bounds of the navigation graph."""
        vertices = self.nav_graph.vertices
        
        if not vertices:
            self.min_x, self.min_y = 0, 0
            self.max_x, self.max_y = 10, 10
            return
            
        # Initialize with the first vertex
        self.min_x = self.max_x = vertices[0]['x']
        self.min_y = self.max_y = vertices[0]['y']
        
        # Find min and max coordinates
        for vertex in vertices:
            self.min_x = min(self.min_x, vertex['x'])
            self.max_x = max(self.max_x, vertex['x'])
            self.min_y = min(self.min_y, vertex['y'])
            self.max_y = max(self.max_y, vertex['y'])
            
        # Add some padding
        padding = 1.0
        self.min_x -= padding
        self.max_x += padding
        self.min_y -= padding
        self.max_y += padding
    
    def center_graph(self) -> None:
        """Center the graph on the canvas."""
        # Calculate the width and height of the graph
        graph_width = self.max_x - self.min_x
        graph_height = self.max_y - self.min_y
        
        # Calculate the scale factor to fit the graph on the canvas
        scale_x = self.CANVAS_WIDTH / graph_width if graph_width > 0 else 50
        scale_y = self.CANVAS_HEIGHT / graph_height if graph_height > 0 else 50
        
        # Use the smaller scale factor to ensure the entire graph fits
        self.scale_factor = min(scale_x, scale_y) * 0.9
        
        # Calculate the offset to center the graph
        self.view_offset_x = (self.CANVAS_WIDTH / 2) - (graph_width * self.scale_factor / 2) - (self.min_x * self.scale_factor)
        self.view_offset_y = (self.CANVAS_HEIGHT / 2) - (graph_height * self.scale_factor / 2) - (self.min_y * self.scale_factor)
    
    def reset_view(self) -> None:
        """Reset the view to center the graph on the canvas."""
        self.center_graph()
        self.update_gui()
        self.status_bar.config(text="View reset")
    
    def clear_selection(self) -> None:
        """Clear any selected robot or vertex."""
        self.selected_robot_id = None
        self.selected_vertex_idx = None
        self.selected_robot_label.config(text="No robot selected")
        self.update_gui()
        self.status_bar.config(text="Selection cleared")
    
    def transform_coord_to_canvas(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform graph coordinates to canvas coordinates.
        
        Args:
            x: X coordinate in the graph
            y: Y coordinate in the graph
            
        Returns:
            Tuple (canvas_x, canvas_y) representing canvas coordinates
        """
        # Invert Y coordinate since canvas Y increases downward
        canvas_x = (x * self.scale_factor) + self.view_offset_x
        canvas_y = (-y * self.scale_factor) + self.view_offset_y
        return (canvas_x, canvas_y)
    
    def transform_canvas_to_coord(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
        """
        Transform canvas coordinates to graph coordinates.
        
        Args:
            canvas_x: X coordinate on the canvas
            canvas_y: Y coordinate on the canvas
            
        Returns:
            Tuple (x, y) representing graph coordinates
        """
        x = (canvas_x - self.view_offset_x) / self.scale_factor
        y = -((canvas_y - self.view_offset_y) / self.scale_factor)
        return (x, y)
    
    def draw_lanes(self) -> None:
        """Draw the lanes of the navigation graph on the canvas."""
        for lane in self.nav_graph.lanes:
            start_idx = lane['start_idx']
            end_idx = lane['end_idx']
            
            start_vertex = self.nav_graph.get_vertex_by_index(start_idx)
            end_vertex = self.nav_graph.get_vertex_by_index(end_idx)
            
            start_x, start_y = self.transform_coord_to_canvas(start_vertex['x'], start_vertex['y'])
            end_x, end_y = self.transform_coord_to_canvas(end_vertex['x'], end_vertex['y'])
            
            # Check if lane is occupied by a robot
            lane_tuple = (start_idx, end_idx)
            lane_color = self.LANE_COLOR
            
            if lane_tuple in self.fleet_manager.occupied_lanes:
                lane_color = self.BLOCKED_COLOR
            
            # Draw the lane line
            self.canvas.create_line(
                start_x, start_y, end_x, end_y, 
                fill=lane_color, 
                width=self.LANE_WIDTH,
                arrow=tk.LAST,  # Add an arrow to indicate direction
                arrowshape=(8, 10, 5)  # Adjust arrow size
            )
    
    def draw_vertices(self) -> None:
        """Draw the vertices of the navigation graph on the canvas."""
        for i, vertex in enumerate(self.nav_graph.vertices):
            x, y = self.transform_coord_to_canvas(vertex['x'], vertex['y'])
            
            # Determine if this vertex is a charger
            is_charger = 'is_charger' in vertex['attrs'] and vertex['attrs']['is_charger']
            
            # Determine vertex color and radius
            color = self.CHARGER_COLOR if is_charger else self.VERTEX_COLOR
            radius = self.CHARGER_RADIUS if is_charger else self.VERTEX_RADIUS
            
            # Draw the vertex (circle)
            outline = self.SELECTION_COLOR if i == self.selected_vertex_idx else color
            outline_width = self.SELECTION_OUTLINE_WIDTH if i == self.selected_vertex_idx else 1
            
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=color,
                outline=outline,
                width=outline_width,
                tags=f"vertex_{i}"
            )
            
            # Draw vertex name
            name = vertex['attrs'].get('name', f"v{i}")
            if name:
                self.canvas.create_text(
                    x, y,
                    text=name,
                    fill=self.TEXT_COLOR,
                    font=("Arial", 9, "bold")
                )
    
    def draw_robots(self) -> None:
        """Draw all robots on the canvas."""
        for robot_id, robot in self.fleet_manager.get_all_robots().items():
            x, y = robot.get_position()
            canvas_x, canvas_y = self.transform_coord_to_canvas(x, y)
            
            # Determine outline color based on robot state
            outline_color = self.SELECTION_COLOR if robot_id == self.selected_robot_id else "#000000"
            outline_width = self.SELECTION_OUTLINE_WIDTH if robot_id == self.selected_robot_id else 1
            
            # Draw the robot (circle)
            self.canvas.create_oval(
                canvas_x - self.ROBOT_RADIUS, canvas_y - self.ROBOT_RADIUS,
                canvas_x + self.ROBOT_RADIUS, canvas_y + self.ROBOT_RADIUS,
                fill=robot.color,
                outline=outline_color,
                width=outline_width,
                tags=f"robot_{robot_id}"
            )
            
            # Draw robot ID
            self.canvas.create_text(
                canvas_x, canvas_y,
                text=robot_id,
                fill=self.TEXT_COLOR,
                font=("Arial", 8, "bold")
            )
            
            # Draw robot state indicator
            state_indicators = {
                Robot.IDLE: "I",
                Robot.MOVING: "M",
                Robot.WAITING: "W",
                Robot.CHARGING: "C",
                Robot.TASK_COMPLETE: "✓"
            }
            
            indicator = state_indicators.get(robot.state, "?")
            indicator_color = {
                Robot.IDLE: "#FFFFFF",
                Robot.MOVING: "#4CAF50",  # Green
                Robot.WAITING: "#F44336",  # Red
                Robot.CHARGING: "#FF9800",  # Orange
                Robot.TASK_COMPLETE: "#2196F3"  # Blue
            }.get(robot.state, "#FFFFFF")
            
            # Draw small circle with state indicator
            indicator_radius = 8
            indicator_x = canvas_x + self.ROBOT_RADIUS + 5
            indicator_y = canvas_y - self.ROBOT_RADIUS - 5
            
            self.canvas.create_oval(
                indicator_x - indicator_radius, indicator_y - indicator_radius,
                indicator_x + indicator_radius, indicator_y + indicator_radius,
                fill="#333333",
                outline=indicator_color,
                width=2
            )
            
            self.canvas.create_text(
                indicator_x, indicator_y,
                text=indicator,
                fill=indicator_color,
                font=("Arial", 8, "bold")
            )
    
    def update_status_display(self) -> None:
        """Update the status display in the UI."""
        # Update the robot list
        self.robot_list.delete(1.0, tk.END)
        
        for robot_id, robot in self.fleet_manager.get_all_robots().items():
            status_text = robot.get_status_text()
            if robot_id == self.selected_robot_id:
                status_text = f"▶ {status_text} ◀"
            self.robot_list.insert(tk.END, f"{status_text}\n")
        
        # Update the selected robot label
        if self.selected_robot_id:
            robot = self.fleet_manager.get_robot_by_id(self.selected_robot_id)
            if robot:
                self.selected_robot_label.config(
                    text=f"Selected: {self.selected_robot_id} - {robot.state}"
                )
            else:
                self.selected_robot_label.config(text="No robot selected")
        else:
            self.selected_robot_label.config(text="No robot selected")
    
    def update_gui(self) -> None:
        """Update the GUI by redrawing all elements."""
        self.canvas.delete("all")
        self.draw_lanes()
        self.draw_vertices()
        self.draw_robots()
        self.update_status_display()
    
    def animation_loop(self) -> None:
        """Main animation loop for updating robot positions and the GUI."""
        while self.animation_running:
            current_time = time.time()
            delta_time = current_time - self.last_update_time
            self.last_update_time = current_time
            
            # Update robots with the elapsed time
            self.fleet_manager.update_robots(delta_time)
            
            # Update the traffic manager
            self.traffic_manager.update(current_time)
            
            # Update the GUI
            self.root.after(0, self.update_gui)
            
            # Delay to target approximately 30 fps
            time.sleep(1 / 30)
    
    def find_vertex_at_position(self, canvas_x: float, canvas_y: float) -> Optional[int]:
        """
        Find the vertex at the given canvas position.
        
        Args:
            canvas_x: X coordinate on the canvas
            canvas_y: Y coordinate on the canvas
            
        Returns:
            Index of the vertex if found, None otherwise
        """
        x, y = self.transform_canvas_to_coord(canvas_x, canvas_y)
        
        for i, vertex in enumerate(self.nav_graph.vertices):
            vertex_x, vertex_y = vertex['x'], vertex['y']
            
            # Calculate distance to vertex
            distance = math.sqrt((x - vertex_x) ** 2 + (y - vertex_y) ** 2)
            
            # Check if click is within vertex radius (adjusted for scale)
            threshold = (self.VERTEX_RADIUS / self.scale_factor) * 1.2
            
            if distance <= threshold:
                return i
                
        return None
    
    def find_robot_at_position(self, canvas_x: float, canvas_y: float) -> Optional[str]:
        """
        Find the robot at the given canvas position.
        
        Args:
            canvas_x: X coordinate on the canvas
            canvas_y: Y coordinate on the canvas
            
        Returns:
            ID of the robot if found, None otherwise
        """
        x, y = self.transform_canvas_to_coord(canvas_x, canvas_y)
        
        for robot_id, robot in self.fleet_manager.get_all_robots().items():
            robot_x, robot_y = robot.get_position()
            
            # Calculate distance to robot
            distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
            
            # Check if click is within robot radius (adjusted for scale)
            threshold = (self.ROBOT_RADIUS / self.scale_factor) * 1.2
            
            if distance <= threshold:
                return robot_id
                
        return None
    
    def on_canvas_click(self, event) -> None:
        """
        Handle click events on the canvas.
        
        Args:
            event: The click event
        """
        # Start tracking for potential drag
        self.dragging = False
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Check if a robot was clicked
        robot_id = self.find_robot_at_position(event.x, event.y)
        if robot_id:
            # Select the robot
            self.selected_robot_id = robot_id
            self.selected_vertex_idx = None
            self.status_bar.config(text=f"Selected robot {robot_id}")
            self.update_gui()
            return
            
        # Check if a vertex was clicked
        vertex_idx = self.find_vertex_at_position(event.x, event.y)
        if vertex_idx is not None:
            if self.selected_robot_id:
                # Assign a task to the selected robot
                robot = self.fleet_manager.get_robot_by_id(self.selected_robot_id)
                if robot and robot.state in [Robot.IDLE, Robot.TASK_COMPLETE]:
                    success = self.fleet_manager.assign_task(self.selected_robot_id, vertex_idx)
                    if success:
                        vertex_name = self.nav_graph.get_vertex_name(vertex_idx)
                        self.status_bar.config(text=f"Assigned task to {self.selected_robot_id}: Go to {vertex_name}")
                    else:
                        self.status_bar.config(text=f"Failed to assign task to {self.selected_robot_id}")
                else:
                    self.status_bar.config(text=f"Robot {self.selected_robot_id} is not available for a new task")
            else:
                # Spawn a new robot at this vertex
                robot_id = self.fleet_manager.create_robot(vertex_idx)
                self.selected_robot_id = robot_id
                self.selected_vertex_idx = None
                vertex_name = self.nav_graph.get_vertex_name(vertex_idx)
                self.status_bar.config(text=f"Spawned robot {robot_id} at {vertex_name}")
            
            self.update_gui()
            return
    
    def on_canvas_drag(self, event) -> None:
        """
        Handle drag events on the canvas.
        
        Args:
            event: The drag event
        """
        # Calculate the distance from the drag start point
        drag_distance = math.sqrt(
            (event.x - self.drag_start_x) ** 2 +
            (event.y - self.drag_start_y) ** 2
        )
        
        # If the drag distance is above a threshold, consider it a drag
        if drag_distance > 5:
            self.dragging = True
            
            # Calculate the movement delta
            delta_x = event.x - self.drag_start_x
            delta_y = event.y - self.drag_start_y
            
            # Update the drag start point
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Update the view offset
            self.view_offset_x += delta_x
            self.view_offset_y += delta_y
            
            # Update the canvas
            self.update_gui()
    
    def on_canvas_release(self, event) -> None:
        """
        Handle mouse button release events on the canvas.
        
        Args:
            event: The release event
        """
        # If it was a drag, do nothing
        if self.dragging:
            self.dragging = False
            return
    
    def on_canvas_scroll(self, event) -> None:
        """
        Handle scroll events on the canvas for zooming.
        
        Args:
            event: The scroll event
        """
        # Determine the scroll direction
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            zoom_factor = 1.1  # Zoom in
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            zoom_factor = 0.9  # Zoom out
        else:
            return
            
        # Calculate the position under the cursor in graph coordinates
        cursor_x, cursor_y = self.transform_canvas_to_coord(event.x, event.y)
        
        # Apply zoom
        old_scale = self.scale_factor
        self.scale_factor *= zoom_factor
        
        # Ensure scale factor is within reasonable bounds
        self.scale_factor = max(5, min(200, self.scale_factor))
        
        # Adjust offset to keep cursor position stable
        scale_change = self.scale_factor / old_scale
        self.view_offset_x = event.x - (cursor_x * self.scale_factor)
        self.view_offset_y = event.y - (-cursor_y * self.scale_factor)
        
        # Update the canvas
        self.update_gui()
    
    def run(self) -> None:
        """Run the GUI main loop."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.status_bar.config(text="System ready")
        self.root.mainloop()
    
    def on_closing(self) -> None:
        """Handle window closing event."""
        self.animation_running = False
        if self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        self.root.destroy()
