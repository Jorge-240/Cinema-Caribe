import axios from 'axios';

// Si estamos en producción (Railway static files) no forzamos localhost, usamos el host origen + /api
const baseURL = import.meta.env.PROD || window.location.hostname !== 'localhost'
    ? '/api'
    : 'http://localhost:5000/api';

const api = axios.create({
    baseURL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Interceptor para agregar jwt
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

export default api;
