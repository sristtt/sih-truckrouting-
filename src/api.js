const API_BASE = 'http://localhost:5000/api';

export default {
  async getRoute(start, end, truckParams) {
    const response = await axios.post(`${API_BASE}/optimize`, {
      origin: start,
      destination: end,
      truck_params: truckParams
    });
    return response.data;
  },
  
  async saveRoute(name, data) {
    await axios.post(`${API_BASE}/save_route/${name}`, data);
  }
};
