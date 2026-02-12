import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8001', // Ojo: Puerto 8001
    withCredentials: true 
});

export default api;
