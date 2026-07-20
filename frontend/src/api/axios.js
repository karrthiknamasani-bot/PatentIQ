import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if (user && user.token) {
    config.headers.Authorization = `Bearer ${user.token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Optionally handle global 401s here to trigger logout
    if (error.response && error.response.status === 401) {
      // localStorage.removeItem('user');
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
