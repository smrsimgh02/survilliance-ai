import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const API_KEY = import.meta.env.VITE_API_KEY || 'surveillance_secret_key_2024';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'X-API-KEY': API_KEY,
    'Content-Type': 'application/json',
  },
});

export const getWSUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = API_BASE.replace(/^https?:\/\//, '');
  return `${protocol}//${host}/ws/detections`;
};
