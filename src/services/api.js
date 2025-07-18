import axios from 'axios';

// Configure base API URL - points to your Flask backend
const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  }
});

// Truck Route API Service
export default {
  /**
   * Get optimized truck route
   * @param {string} origin - Starting location
   * @param {string} destination - Target location
   * @param {object} truckParams - Truck specifications
   * @returns {Promise} Axios response
   */
  getOptimizedRoute(origin, destination, truckParams) {
    return api.post('/optimize', {
      origin,
      destination,
      truck_params: truckParams
    });
  },

  /**
   * Get list of saved routes
   * @returns {Promise} Axios response
   */
  getSavedRoutes() {
    return api.get('/list');
  },

  /**
   * Save a route
   * @param {string} routeName - Name for the route
   * @param {object} routeData - Route data to save
   * @returns {Promise} Axios response
   */
  saveRoute(routeName, routeData) {
    return api.post(`/save_route/${routeName}`, routeData);
  },

  /**
   * Delete a saved route
   * @param {string} routeName - Name of route to delete
   * @returns {Promise} Axios response
   */
  deleteRoute(routeName) {
    return api.delete(`/delete/${routeName}`);
  }
};
