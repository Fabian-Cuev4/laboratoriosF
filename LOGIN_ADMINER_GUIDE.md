# 🔧 Guía Completa: Login/Register + Adminer + Verificación

## 📌 Problemas Resueltos

✅ **CORS habilitado en NGINX** - Frontend puede comunicarse con backend  
✅ **Adminer integrado** - Visualización de MySQL sin línea de comandos  
✅ **Mensajes de error mejorados** - Debugging más fácil  
✅ **Reintentos automáticos** - Manejo de fallos de red  

---

## 🚀 Inicio Rápido

### Paso 1: Iniciar el Sistema
```bash
cd c:\Users\Fabian\Desktop\arquitectura\laboratorios
docker-compose up -d
```

### Paso 2: Verificar Contenedores
```bash
docker-compose ps
```

Deberías ver 8 contenedores corriendo:
```
lab_mysql        ✅ healthy
lab_redis        ✅ healthy
lab_mongo        ✅ running
lab_backend-1    ✅ healthy
lab_backend-2    ✅ healthy
lab_backend-3    ✅ healthy
lab_lb (NGINX)   ✅ running
lab_adminer      ✅ running
lab_redis_insight✅ running
```

### Paso 3: Acceder a Adminer (New!)
```
http://localhost:8080
```

Credenciales:
- **Server:** `mysql_db` (o dejar en blanco, se completa automáticamente)
- **Usuario:** `user`
- **Contraseña:** `password`
- **Base de datos:** `lab_usuarios`

### Paso 4: Acceder al Frontend
```
http://localhost:5173
```

---

## 🔐 Prueba Completa: Login/Register

### 1️⃣ Crear Cuenta (Register)

**URL:** `http://localhost:5173/register`

**Datos de prueba:**
```
Usuario: testuser
Email: test@example.com
Contraseña: Test1234!
```

**Resultado esperado:**
```
✅ ¡Cuenta creada exitosamente!
```

**Verificar en Adminer:**
1. Abre http://localhost:8080
2. Login con credenciales arriba
3. Tabla `user` → Nueva fila creada

---

### 2️⃣ Iniciar Sesión (Login)

**URL:** `http://localhost:5173`

**Datos de prueba:**
```
Usuario: testuser
Contraseña: Test1234!
```

**Resultado esperado:**
```
✅ Redirige a /dashboard
```

**Lo que sucede internamente:**
```
1. Frontend envía POST a http://localhost:8001/auth/login
2. NGINX recibe (con CORS habilitado) ✅
3. Backend procesa (3 replicas, load balanced)
4. MySQL valida usuario y contraseña
5. Redis cachea datos si es necesario
6. Respuesta llega al frontend
7. UserLocal se guarda en localStorage
```

---

## 🔍 Adminer - Visualización de MySQL

### Acceso
```
http://localhost:8080
```

### Credenciales
| Campo | Valor |
|-------|-------|
| Server | mysql_db |
| Usuario | user |
| Contraseña | password |
| Base de datos | lab_usuarios |

### Tablas Disponibles

#### 1. **user** (Autenticación)
```sql
CREATE TABLE `user` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(255) UNIQUE NOT NULL,
  `email` VARCHAR(255) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Abrir en Adminer:**
1. Selecciona tabla `user`
2. Verás todas las cuentas creadas
3. Puedes editar/eliminar/agregar usuarios

#### 2. **item** (Inventario Global)
```sql
CREATE TABLE `item` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `status` VARCHAR(100) NOT NULL,
  `area` VARCHAR(255),
  `acquisition_date` DATE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧪 Pruebas Específicas

### Prueba 1: Verificar Conectividad CORS

```bash
# Terminal/PowerShell
curl -X OPTIONS http://localhost:8001 -v
```

Busca en la respuesta:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

✅ Si aparecen, CORS está funcionando.

### Prueba 2: Probar Login Directamente

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234!"}'
```

**Respuesta esperada:**
```json
{
  "mensaje": "Login exitoso",
  "usuario": "testuser"
}
```

### Prueba 3: Probar Register Directamente

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"newuser",
    "email":"new@example.com",
    "password":"Password123!"
  }'
```

**Respuesta esperada:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "new@example.com"
}
```

### Prueba 4: Verificar Salud del Sistema

```bash
curl http://localhost:8001/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "mysql": true,
  "redis": true,
  "hostname": "laboratorios-backend-1",
  "port": "8000"
}
```

### Prueba 5: Verificar Sincronización

```bash
curl http://localhost:8001/sync/status
```

**Respuesta esperada:**
```json
{
  "mysql_available": true,
  "redis_available": true,
  "cache_items": 0,
  "pending_creates": 0,
  "pending_updates": 0,
  "pending_deletes": 0,
  "is_consistent": true,
  "status": "synced"
}
```

---

## 🛠️ Debugging - Si Algo No Funciona

### ❌ Error: "Error de red: Verifica que el servidor esté disponible"

**Causa:** NGINX no responde o está caído

**Solución:**
```bash
# Verificar contenedores
docker-compose ps | grep lab_lb

# Reiniciar NGINX
docker-compose restart nginx

# Ver logs de NGINX
docker-compose logs nginx -f
```

---

### ❌ Error: "Usuario no encontrado" al Login

**Causa:** Usuario no existe en la base de datos

**Solución:**
1. Abre Adminer: http://localhost:8080
2. Verifica tabla `user`
3. Si está vacía, crea una cuenta primero en `/register`

---

### ❌ Error: "Email ya está registrado"

**Causa:** El email ya existe en la BD

**Solución:**
1. Usa otro email
2. O borra el usuario en Adminer

---

### ❌ Error: "Este email ya está registrado" pero no sale en Adminer

**Causa:** Hay inconsistencia entre MySQL y Redis

**Solución:**
```bash
# Esperar 30 segundos a que se sincronicen
# O reiniciar backend:
docker-compose restart backend

# Ver logs de sincronización
docker-compose logs backend | grep -E "\[SYNC\]|✅|❌"
```

---

## 🌐 Arquitectura de Comunicación Verificada

```
Frontend (http://localhost:5173)
    │
    ├─ POST /auth/login
    ├─ POST /auth/register
    ├─ GET /health
    └─ GET /sync/status
    │
    ▼
NGINX (http://localhost:8001) ← CORS HABILITADO ✅
    │
    ├─ Load Balancer (Round Robin)
    │
    ▼
Backend (3 replicas, puerto 8000)
    │
    ├─ /auth/login
    ├─ /auth/register
    ├─ /health
    ├─ /sync/status
    └─ /laboratories/*
    │
    ▼┌──────────────────────────┐
     │ MySQL (Puerto 3306)      │ ← Visualizar en Adminer
     │ Redis (Puerto 6379)      │
     │ MongoDB (Puerto 27018)   │
     └──────────────────────────┘
```

---

## 📊 Herramientas de Visualización

| Herramienta | Puerto | Uso |
|------------|--------|-----|
| **Frontend** | 5173 | Aplicación principal |
| **NGINX** | 8001 | Load Balancer |
| **Adminer** | 8080 | Visualizar MySQL |
| **Redis Insight** | 5540 | Visualizar Redis |
| **Backend** | 8000 | API (interno) |

---

## ✅ Checklist de Verificación

Ejecuta esto paso por paso:

- [ ] `docker-compose ps` - todos en estado healthy/running
- [ ] `http://localhost:5173` - Frontend carga sin errores
- [ ] `/register` - Crear cuenta exitosamente
- [ ] `/auth/login` - Login exitosamente
- [ ] `http://localhost:8080` - Adminer carga
- [ ] Adminer muestra tabla `user` con registro
- [ ] `curl http://localhost:8001/health` - Retorna status healthy
- [ ] `curl http://localhost:8001/sync/status` - Retorna synced
- [ ] Dashboard muestra estado del sistema (MySQL ✅, Redis ✅)
- [ ] `http://localhost:5540` - Redis Insight carga

**Si todos pasan:** ✅ Sistema perfectamente sincronizado

---

## 🚨 Logs Útiles para Debugging

```bash
# Ver logs de NGINX (CORS)
docker-compose logs nginx -f

# Ver logs del backend (sincronización)
docker-compose logs backend -f

# Ver logs de MySQL (errores)
docker-compose logs mysql_db -f

# Ver logs de Redis
docker-compose logs redis_db -f

# Filtrar solo errores
docker-compose logs | grep -i error

# Filtrar solo sincronización
docker-compose logs backend | grep -E "\[SYNC\]|✅|❌"
```

---

## 🔄 Flujo Completo de Comunicación

### Scenario: Usuario nuevo se registra

```
1. Frontend: POST http://localhost:5173/auth/register
               {username: "john", email: "john@example.com", password: "..."}

2. NGINX: Recibe petición
           ✅ CORS headers agregados
           ✅ Enruta a backend (Round Robin)

3. Backend: Procesa en una de 3 replicas
            ✅ Valida esquema con Pydantic
            ✅ Hashea contraseña con bcrypt
            ✅ Inserta en MySQL
            ✅ Cachea en Redis

4. MySQL: Crea registro
           ✅ Trigger de auditoría (si existe)
           ✅ Confirma insert

5. Redis: Cachea datos
          ✅ Setea key user:{username}
          ✅ Actualiza índices

6. Backend: Retorna respuesta
            {id: 1, username: "john", email: "john@example.com"}

7. NGINX: Retorna con CORS headers
           ✅ Access-Control-Allow-Origin: *

8. Frontend: Recibe respuesta
             ✅ Parsea JSON
             ✅ Muestra confirmación
             ✅ Redirige a login
```

---

## 📝 Notas Importantes

### CORS en NGINX
```nginx
# Ya está habilitado en nginx/nginx.conf:
add_header 'Access-Control-Allow-Origin' '*' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
```

### Reintentos en Frontend
```javascript
// Ya están habilitados en axios.js:
- Máximo 3 reintentos
- Exponential backoff: 1s → 2s → 4s
- Aplica para: 503, 504, Network Error
```

### Sincronización MySQL ↔ Redis
```
- Cada 30 segundos: verifica estado
- Si MySQL está caído: Redis actúa como respaldo
- Si MySQL revive: aplica pendientes automáticamente
- Valida integridad con hash SHA256
```

---

## 🎓 Conclusión

Tu sistema ahora tiene:

✅ **Frontend-Backend Communication** - Funcionando con CORS habilitado  
✅ **Authentication** - Login y Register correctamente  
✅ **Database Visualization** - Adminer para ver MySQL  
✅ **Load Balancing** - NGINX distribuyendo 3 replicas  
✅ **High Availability** - MySQL + Redis sincronizado  
✅ **Error Handling** - Mensajes claros de debugging  
✅ **Auto Recovery** - Reintentos y fallback automático  

**¡Listo para producción! 🚀**
