import os
import sys
import time
from pathlib import Path
import argparse

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.models.nav_graph import NavGraph
from src.controllers.fleet_manager import FleetManager
from src.controllers.traffic_manager import TrafficManager
from src.gui.fleet_gui import FleetGUI

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fleet Management System for Multi-Robots')
    parser.add_argument('--graph', type=str, default='data/nav_graph.json',
                        help='Path to the navigation graph JSON file')
    parser.add_argument('--log', type=str, default='src/logs/fleet_logs.txt',
                        help='Path to the log file')
    return parser.parse_args()

def main():
    """Main entry point of the application."""
    args = parse_arguments()
    
    # Convert relative paths to absolute paths based on project root
    graph_path = os.path.join(project_root, args.graph)
    log_path = os.path.join(project_root, args.log)
    
    print(f"Loading navigation graph from: {graph_path}")
    print(f"Logging to: {log_path}")
    
    try:
        # Initialize the navigation graph
        nav_graph = NavGraph(graph_path)
        
        # Initialize the fleet manager
        fleet_manager = FleetManager(nav_graph, log_path)
        
        # Initialize the traffic manager
        traffic_manager = TrafficManager(nav_graph, fleet_manager)
        
        # Initialize and run the GUI
        gui = FleetGUI(nav_graph, fleet_manager, traffic_manager)
        gui.run()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
