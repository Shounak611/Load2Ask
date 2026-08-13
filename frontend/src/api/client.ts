import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const customError = error.response?.data?.detail || error.message || 'An unexpected backend error occurred.';
    return Promise.reject(new Error(customError));
  }
);
