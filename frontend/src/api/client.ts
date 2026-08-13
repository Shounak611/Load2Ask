import axios from 'axios';

const baseEnv = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, '')
  : '';

export const API_BASE_URL = baseEnv ? `${baseEnv}/api` : '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
