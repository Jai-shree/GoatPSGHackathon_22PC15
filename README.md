# Fleet Management System with Traffic Negotiation for Multi-Robots

A visually intuitive and interactive Fleet Management System developed in Python, capable of managing multiple robots simultaneously navigating through an environment. The system implements traffic negotiation based on a provided navigation graph, ensuring collision avoidance, dynamic task assignment, and clear visualization of robot movements and statuses.

## Features

- **Environment Visualization**: Clear display of all vertices (locations) and lanes (connections) in the navigation graph.
- **Robot Spawning**: Create robots by clicking on any vertex in the graph.
- **Task Assignment**: Assign navigation tasks by selecting a robot and then clicking on a destination vertex.
- **Traffic Negotiation**: Robots automatically avoid collisions by negotiating traffic and managing lane occupancy.
- **Status Visualization**: Clear indication of robot statuses (moving, waiting, task complete).
- **Real-time Updates**: Continuous visualization of robot movements and state changes.
- **Logging**: All robot actions, paths, and status changes are logged for reference.

## Installation and Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd fleet-management-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

- **Spawn a Robot**: Click on any vertex in the graph to create a new robot.
- **Select a Robot**: Click on a robot to select it.
- **Assign a Task**: With a robot selected, click on a destination vertex to assign a navigation task.
- **View Status**: The side panel displays the status of all robots and detailed information about the selected robot.
- **Navigation**: 
  - Drag the canvas to pan the view
  - Use mouse wheel to zoom in/out
  - Use the "Reset View" button to return to the default view
  - Use "Clear Selection" to deselect any selected robot or vertex

## System Architecture

The system is organized into the following components:

- **Models**: 
  - `NavGraph`: Represents and provides access to the navigation graph.
  - `Robot`: Handles individual robot state, movement, and task execution.

- **Controllers**:
  - `FleetManager`: Manages robot creation, task assignment, and status tracking.
  - `TrafficManager`: Implements traffic negotiation and collision avoidance.

- **GUI**:
  - `FleetGUI`: Provides the graphical interface for visualizing and interacting with the system.
 
OUTPUT SCREEN:
![Screenshot 2025-03-30 193132](https://github.com/user-attachments/assets/d6da96cf-3db9-4009-bf96-cbd65a4d9505)
