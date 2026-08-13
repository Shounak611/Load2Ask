import axios from 'axios';

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (!envUrl) {
    return '/api';
  }
  const cleanUrl = envUrl.trim().replace(/\/$/, '');
  if (cleanUrl.endsWith('/api')) {
    return cleanUrl;
  }
  return `${cleanUrl}/api`;
};

export const API_BASE_URL = getApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let customError = 'An unexpected backend error occurred.';
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === 'string') {
        customError = data.detail;
      } else if (Array.isArray(data.detail)) {
        customError = data.detail
          .map((d: any) => (typeof d === 'string' ? d : d.msg || JSON.stringify(d)))
          .join('; ');
      } else if (typeof data === 'string') {
        customError = data.length > 300 ? 'Server returned an HTML or unexpected error response.' : data;
      } else if (typeof data === 'object') {
        customError = JSON.stringify(data);
      }
    } else if (error.message) {
      customError = String(error.message);
    }
    return Promise.reject(new Error(customError));
  }
);
