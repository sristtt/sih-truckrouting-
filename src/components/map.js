import api from '../services/api';

// Example usage in your component
async function calculateRoute() {
  try {
    const response = await api.getOptimizedRoute(
      'Berlin, Germany',      // Replace with your start point
      'Hamburg, Germany',     // Replace with your end point
      {
        weight: 16,          // Truck weight in tons
        height: 4,           // Truck height in meters
        hazmat: false        // Hazardous materials flag
      }
    );
    
    // Process the response
    const routeData = response.data;
    console.log('Optimized route:', routeData);
    
    // Update your map with the new route
    updateMapWithRoute(routeData.waypoints);
    
  } catch (error) {
    console.error('Failed to calculate route:', error);
    // Show error to user
  }
}
