from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import json
import logging
from pathlib import Path
import re
import osmnx as ox
import networkx as nx
from datetime import datetime
import heapq

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(filename='truck_routing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define API
api = Api(
    app=app,
    version="1.0",
    title="Truck Route Optimization API",
    description="API for optimizing truck routes with road constraints"
)

# Constants
ROUTES_DIR = Path("./saved_routes")
ROUTES_DIR.mkdir(exist_ok=True)
CACHE_DIR = Path("./map_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Models
route_request = api.model('RouteRequest', {
    'origin': fields.String(required=True, description='Origin address or coordinates'),
    'destination': fields.String(required=True, description='Destination address or coordinates'),
    'truck_params': fields.Nested(api.model('TruckParams', {
        'weight': fields.Float(required=True, description='Truck weight in tons'),
        'height': fields.Float(required=True, description='Truck height in meters'),
        'hazmat': fields.Boolean(default=False, description='Hazardous materials flag')
    })),
    'time_constraint': fields.String(description='Arrival time (HH:MM)')
})

# Namespace
route_ns = api.namespace('api', description='Truck routing operations')

class TruckRouteOptimizer:
    def __init__(self):
        self.graph = None
        self.area = "Germany"  # Default area for map data
        
    def load_map(self, location):
        """Load or create road network graph for the area"""
        cache_file = CACHE_DIR / f"{location.replace(' ', '_')}.graphml"
        
        if cache_file.exists():
            self.graph = ox.load_graphml(cache_file)
        else:
            try:
                self.graph = ox.graph_from_place(location, network_type='drive')
                ox.save_graphml(self.graph, cache_file)
            except Exception as e:
                logging.error(f"Map loading error: {str(e)}")
                raise ValueError("Could not load map data for the specified area")
        
        # Add edge speeds and travel times
        self.graph = ox.add_edge_speeds(self.graph)
        self.graph = ox.add_edge_travel_times(self.graph)
        
        # Add truck restrictions (simplified)
        for u, v, data in self.graph.edges(data=True):
            data['truck_restricted'] = False
            if 'maxweight' in data and data['maxweight'] < 7.5:  # 7.5 ton limit
                data['truck_restricted'] = True
            if 'tunnel' in data.get('name', '').lower():
                data['truck_restricted'] = True

    def optimize_route(self, origin, destination, truck_params):
        """Find optimal truck route using A* algorithm with truck constraints"""
        try:
            # Geocode if addresses are provided
            if not (origin.replace('.','').isdigit() and ',' in origin):
                origin = ox.geocode(origin)
            if not (destination.replace('.','').isdigit() and ',' in destination):
                destination = ox.geocode(destination)
                
            # Get nearest network nodes
            orig_node = ox.distance.nearest_nodes(self.graph, float(origin.split(',')[1]), float(origin.split(',')[0]))
            dest_node = ox.distance.nearest_nodes(self.graph, float(destination.split(',')[1]), float(destination.split(',')[0]))
            
            # Custom cost function for trucks
            def cost_func(u, v, edge_data):
                base_cost = edge_data.get('travel_time', 1)
                
                # Penalize truck-restricted roads
                if edge_data.get('truck_restricted', False):
                    return base_cost * 10  # High penalty
                    
                # Penalize steep grades (simplified)
                if 'grade' in edge_data and abs(edge_data['grade']) > 5:
                    return base_cost * 2
                    
                # Hazardous materials routing
                if truck_params['hazmat'] and 'residential' in edge_data.get('highway', ''):
                    return base_cost * 5
                    
                return base_cost
            
            # Find shortest path using custom cost
            route = nx.astar_path(self.graph, orig_node, dest_node, weight=cost_func)
            
            # Get route details
            travel_time = sum(self.graph[u][v][0].get('travel_time', 0) for u, v in zip(route[:-1], route[1:])) / 60  # in minutes
            distance = sum(self.graph[u][v][0].get('length', 0) for u, v in zip(route[:-1], route[1:])) / 1000  # in km
            
            return {
                'waypoints': [self.graph.nodes[node] for node in route],
                'travel_time': round(travel_time, 1),
                'distance': round(distance, 1),
                'truck_safe': True
            }
            
        except Exception as e:
            logging.error(f"Routing error: {str(e)}")
            raise ValueError("Could not calculate route")

# Initialize optimizer
optimizer = TruckRouteOptimizer()
optimizer.load_map("Germany")  # Load default map

@route_ns.route('/optimize')
class RouteOptimizer(Resource):
    @route_ns.expect(route_request)
    @route_ns.doc(responses={
        200: 'Success',
        400: 'Bad Request',
        500: 'Server Error'
    })
    def post(self):
        """Calculate optimal truck route"""
        try:
            data = request.get_json()
            
            # Validate input
            if not data or 'origin' not in data or 'destination' not in data:
                return {"status": "error", "message": "Missing origin or destination"}, 400
                
            # Get truck parameters (defaults for semi-truck)
            truck_params = data.get('truck_params', {
                'weight': 16.0,
                'height': 4.0,
                'hazmat': False
            })
            
            # Calculate route
            route = optimizer.optimize_route(
                data['origin'],
                data['destination'],
                truck_params
            )
            
            # Add metadata
            route['calculation_time'] = datetime.now().isoformat()
            route['truck_parameters'] = truck_params
            
            return {"status": "success", "data": route}, 200
            
        except ValueError as e:
            return {"status": "error", "message": str(e)}, 400
        except Exception as e:
            logging.error(f"Route optimization failed: {str(e)}")
            return {"status": "error", "message": "Internal server error"}, 500

@route_ns.route('/save_route/<string:route_name>')
class RouteSaver(Resource):
    @route_ns.doc(responses={
        200: 'Success',
        400: 'Bad Request',
        500: 'Server Error'
    })
    def post(self, route_name):
        """Save a calculated route"""
        try:
            if not re.match(r'^[a-zA-Z0-9_-]+$', route_name):
                return {"status": "error", "message": "Invalid route name"}, 400
                
            data = request.get_json()
            if not data:
                return {"status": "error", "message": "No route data provided"}, 400
                
            route_file = ROUTES_DIR / f"{route_name}.json"
            if route_file.exists():
                return {"status": "error", "message": "Route name already exists"}, 400
                
            with open(route_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            return {"status": "success", "message": "Route saved"}, 200
            
        except Exception as e:
            logging.error(f"Route save failed: {str(e)}")
            return {"status": "error", "message": "Internal server error"}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
