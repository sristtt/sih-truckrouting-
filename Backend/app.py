from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import osmnx as ox
import networkx as nx
import logging
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize API
api = Api(
    app,
    version='1.0',
    title='Delhi Truck Routing API',
    description='Optimize truck routes in Delhi',
    prefix='/api'
)

# Namespace
ns = api.namespace('', description='Truck routing operations')

# Constants
CACHE_DIR = Path("./map_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Configure OSMnx
ox.settings.timeout = 600
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.cache_folder = str(CACHE_DIR)

class DelhiRouteOptimizer:
    def __init__(self):
        self.graph = None
        self.area = "Delhi, India"
        self.restricted_areas = [
            "Connaught Place",
            "India Gate",
            "NDMC"
        ]

    def load_map(self):
        """Load Delhi road network safely"""
        try:
            cache_file = CACHE_DIR / "delhi_roads.graphml"
            
            if cache_file.exists():
                logging.info("Loading cached Delhi map")
                self.graph = ox.load_graphml(cache_file)
            else:
                logging.info("Downloading Delhi road network...")
                self.graph = ox.graph_from_place(
                    self.area,
                    network_type='drive',
                    custom_filter='["highway"~"motorway|trunk|primary"]'
                )
                
                # Add truck restrictions
                for _, _, data in self.graph.edges(data=True):
                    data['truck_restricted'] = False
                    name = data.get('name', '')
                    if isinstance(name, str):  # Ensure name is string before .lower()
                        if any(area.lower() in name.lower() 
                              for area in self.restricted_areas):
                            data['truck_restricted'] = True
                
                ox.save_graphml(self.graph, cache_file)
                logging.info(f"Saved map to {cache_file}")
                
            return True
            
        except Exception as e:
            logging.error(f"Map loading failed: {str(e)}")
            return False

# Initialize optimizer
optimizer = DelhiRouteOptimizer()

# API Models
route_model = api.model('RouteRequest', {
    'origin': fields.String(required=True),
    'destination': fields.String(required=True),
    'truck_params': fields.Nested(api.model('TruckParams', {
        'weight': fields.Float(required=True),
        'height': fields.Float(required=True)
    }))
})

# API Endpoints
@ns.route('/health')
class Health(Resource):
    def get(self):
        return {'status': 'OK'}

@ns.route('/restrictions')
class Restrictions(Resource):
    def get(self):
        return {
            'restricted_areas': optimizer.restricted_areas,
            'limits': {'max_weight': 7.5, 'max_height': 4.0}
        }

@ns.route('/optimize')
class OptimizeRoute(Resource):
    @ns.expect(route_model)
    def post(self):
        try:
            data = request.get_json()
            
            # Initialize map if needed
            if not optimizer.graph and not optimizer.load_map():
                return {"error": "Map initialization failed"}, 500
                
            # Your optimization logic here
            # For now return a mock response
            return {
                "status": "success",
                "route": {
                    "waypoints": [],
                    "distance": 0,
                    "time": 0
                }
            }
            
        except Exception as e:
            logging.error(f"Optimization error: {str(e)}")
            return {"error": str(e)}, 400

if __name__ == '__main__':
    print("Starting Delhi Truck Routing API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
