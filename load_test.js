import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  // Simular tráfico creciente
  stages: [
    { duration: '10s', target: 20 }, // Subir a 20 usuarios en 10s
    { duration: '20s', target: 20 }, // Mantener 20 usuarios por 20s
    { duration: '5s', target: 0 },   // Bajar a 0
  ],
};

export default function () {
  // Petición al Balanceador de Carga (Puerto 8001)
  const res = http.get('http://host.docker.internal:8001/');
  
  // Verificar que responda OK (200)
  check(res, { 'status was 200': (r) => r.status == 200 });
  
  sleep(1);
}