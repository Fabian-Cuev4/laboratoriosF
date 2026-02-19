import axios from 'axios';

// Determinar el puerto correcto: 8001 es el NGINX que actúa como load balancer
// Si estamos en desarrollo local, el NGINX probablemente escucha en http://localhost:8001
// Si es en producción con Docker, es http://localhost:{PORT_NGINX}
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8001' 
  : `http://${window.location.hostname}:${window.location.port || 8001}`;

const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    timeout: 10000 // Timeout de 10 segundos
});

// Contador de reintentos
let retryCount = 0;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 segundo

/**
 * Interceptor de respuesta para manejar errores y reintentos
 */
api.interceptors.response.use(
    (response) => {
        // Reset del contador en caso de éxito
        retryCount = 0;
        return response;
    },
    async (error) => {
        const config = error.config;
        
        // Si no hay config, devolver el error
        if (!config) return Promise.reject(error);
        
        // No reintentar si ya lo hemos hecho MAX_RETRIES veces
        if (!config.retryCount) {
            config.retryCount = 0;
        }
        
        config.retryCount += 1;
        
        // Solo reintentar en caso de:
        // 1. Errores de red (sin respuesta)
        // 2. Errores 503 (Service Unavailable)
        // 3. Errores 504 (Gateway Timeout)
        // 4. Errors de conexión
        const shouldRetry = !error.response || 
                           error.response.status === 503 || 
                           error.response.status === 504 ||
                           error.code === 'ECONNABORTED' ||
                           error.message === 'Network Error';
        
        if (shouldRetry && config.retryCount < MAX_RETRIES) {
            const delay = RETRY_DELAY * Math.pow(2, config.retryCount - 1); // Exponential backoff
            console.warn(`🔄 Reintentando petición (intento ${config.retryCount}/${MAX_RETRIES}) en ${delay}ms...`);
            
            await new Promise(resolve => setTimeout(resolve, delay));
            return api.request(config);
        }
        
        // Si llegamos aquí, error permanente
        console.error(`❌ Error después de ${config.retryCount} reintentos:`, error.message);
        return Promise.reject(error);
    }
);

/**
 * Interceptor de solicitud para agregar headers útiles
 */
api.interceptors.request.use(
    (config) => {
        // Agregar token si existe
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export { API_BASE_URL };
export default api;
