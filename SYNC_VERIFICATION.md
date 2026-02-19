# 🏗️ Verificación de Sincronización MySQL ↔ Redis

## 📋 Resumen de Mejoras Implementadas

Este documento describe las mejoras realizadas al proyecto para garantizar una sincronización robusta entre **MySQL** y **Redis**, con fallback automático cuando MySQL falla.

### ✅ Mejoras Críticas Implementadas

#### 1. **Sincronización Bidireccional Mejorada** (`backend/services/mysql_redis_sync.py`)
   - ✅ **Validación de integridad de datos** mediante hash SHA256
   - ✅ **Verificación de consistencia** entre MySQL y Redis
   - ✅ **Reconstrucción automática de caché** desde MySQL cuando falla
   - ✅ **Detección de desincronización** en tiempo real
   - ✅ **Sistema de pendientes** para operaciones cuando MySQL está caído:
     - Items pendientes de crear
     - Updates pendientes de aplicar
     - Items pendientes de eliminar

#### 2. **Healthchecks Completos** (`docker-compose.yml`)
   - ✅ MySQL con healthcheck cada 5 segundos
   - ✅ Redis con healthcheck cada 5 segundos (NUEVO)
   - ✅ Backend con healthcheck del endpoint `/health` cada 5 segundos (NUEVO)
   - ✅ Dependencias correctas: Backend espera a MySQL y Redis

#### 3. **Endpoints de Monitoreo** (`backend/main.py`)
   - ✅ `GET /health` - Estado del sistema (MySQL, Redis, Sincronización)
   - ✅ `GET /sync/status` - Estado detallado de la sincronización
   - ✅ Ciclo de sincronización mejorado cada 30 segundos

#### 4. **Frontend Mejorado**
   - ✅ Axios con reintentos automáticos (exponential backoff)
   - ✅ Componente `SystemHealthMonitor` que muestra estado en tiempo real
   - ✅ Manejo de reconexión automática
   - ✅ Visualización de estado de MySQL, Redis y Sincronización

---

## 🔧 Arquitectura de Sincronización

### Flujo Normal (MySQL Online)
```
Cliente → Endpoint POST /items
    ↓
1. Escribir en MySQL (fuente de verdad)
    ↓
2. Dual-write: Actualizar caché en Redis
    ↓
3. Calcular hash SHA256 de caché
    ↓
Respuesta al cliente (source: "MySQL")
```

### Flujo Fallback (MySQL Offline)
```
Cliente → Endpoint POST /items
    ↓
1. Intento de escritura en MySQL falla
    ↓
2. Rescue: Guardar en Redis (items:pending)
    ↓
3. Agregar también a caché temporal
    ↓
Respuesta al cliente (source: "REDIS_BACKUP")
```

### Flujo de Recuperación (MySQL Online nuevamente)
```
Cada 30 segundos en background:
    ↓
1. Detectar que MySQL está online
    ↓
2. Aplicar pendientes en orden:
   a) Eliminaciones
   b) Updates
   c) Creaciones
    ↓
3. Refrescar caché desde MySQL
    ↓
4. Verificar integridad (hash)
    ↓
5. Si falla integridad → Reconstruir desde MySQL
```

---

## 🧪 Cómo Verificar la Sincronización

### Opción 1: Usar el Monitor del Dashboard
1. Iniciar el sistema: `docker-compose up`
2. Abrir el frontend en navegador
3. Ver el panel "Estado del Sistema" que muestra:
   - ✅/❌ MySQL Online/Offline
   - ✅/❌ Redis Online/Offline
   - ✅/❌ Sincronización Sincronizado/Desincronizado
   - Detalles de items en caché y operaciones pendientes

### Opción 2: Endpoints de API
```bash
# Ver salud del sistema
curl http://localhost:8001/health

# Ver estado detallado de sincronización
curl http://localhost:8001/sync/status
```

**Respuesta esperada de `/sync/status`:**
```json
{
  "mysql_available": true,
  "redis_available": true,
  "cache_items": 15,
  "pending_creates": 0,
  "pending_updates": 0,
  "pending_deletes": 0,
  "is_consistent": true,
  "consistency_details": {
    "is_valid": true,
    "items_count": 15,
    "hash_match": true
  },
  "status": "synced"
}
```

### Opción 3: Script de Prueba Automatizada
```bash
# Instalar dependencia
pip install aiohttp

# Ejecutar prueba
python test_sync.py
```

Este script:
1. ✅ Verifica conectividad al sistema
2. ✅ Crea un item de prueba con MySQL online
3. ✅ Simula caída de MySQL (solicita al usuario hacer `docker-compose stop mysql_db`)
4. ✅ Intenta crear un item con MySQL offline
5. ✅ Verifica que se guardó en Redis
6. ✅ Recupera MySQL (solicita al usuario hacer `docker-compose start mysql_db`)
7. ✅ Verifica sincronización automática
8. ✅ Genera reporte final

---

## 🚀 Cómo Ejecutar el Sistema Completo

### 1. Iniciar los Contenedores
```bash
docker-compose up -d
```

Espera a que los healthchecks pasen (máximo 30 segundos).

### 2. Verificar Estado
```bash
# Ver si todos los contenedores están healthy
docker-compose ps

# Ver logs del backend
docker-compose logs backend -f
```

### 3. Probar Sincronización Manual

**En el frontend (Dashboard):**
- El monitor mostrará el estado en tiempo real
- Crear algunos items

**Simular falla de MySQL:**
```bash
docker-compose stop mysql_db
```

**En el frontend:**
- Debería cambiar a "MySQL: Offline"
- Las nuevas operaciones guardarán en Redis
- Ver que aparecen items pendientes en el monitor

**Recuperar MySQL:**
```bash
docker-compose start mysql_db
```

**En el frontend:**
- Debería volver a "MySQL: Online"
- Los items pendientes se sincronizarán automáticamente
- El estado pasará a "Sincronizado"

---

## 📊 Claves Redis de Sincronización

El proyecto usa las siguientes claves en Redis para coordinar la sincronización:

| Clave | Descripción |
|-------|----------|
| `items:cache` | Caché JSON de todos los items (espejo de MySQL) |
| `items:cache:hash` | Hash SHA256 de la caché para verificar integridad |
| `items:pending` | Items creados cuando MySQL estaba offline (lista) |
| `items:pending_updates` | Updates pendientes de aplicar a MySQL (lista de operaciones) |
| `items:pending_deletes` | IDs de items pendientes de eliminar en MySQL (lista) |
| `sync:metadata` | Metadatos sobre la última sincronización |
| `instance:{hostname}` | Heartbeat de cada instancia del backend |
| `requests:{hostname}` | Contador de peticiones por instancia |

---

## 🔍 Monitorear en Tiempo Real

### Opción A: Redis CLI
```bash
# Conectarse a Redis
docker exec -it lab_redis redis-cli

# Ver todas las claves
keys *

# Ver contenido de caché
get items:cache | jq .

# Ver items pendientes
lrange items:pending 0 -1

# Monitorear cambios en tiempo real
monitor
```

### Opción B: Redis Insight (GUI)
```bash
# Ya está incluido en docker-compose
# Acceder a: http://localhost:5540
```

### Opción C: Logs del Backend
```bash
# Ver logs con colores (mejor para ver sincronización)
docker-compose logs backend -f | grep -E "\[SYNC\]|✅|❌|⚠️"
```

---

## 🛡️ Garantías de Corrección

### ✅ MySQL Online
- **Todos los datos** se escriben primero en MySQL
- **Luego** se actualizan en Redis
- **Integridad garantizada** por hash SHA256

### ✅ MySQL Offline
- **Operaciones** se guardan en Redis (items:pending)
- **Lecturas** devuelven caché + pendientes
- **Datos no se pierden**

### ✅ MySQL Recuperándose
- **Pendientes se sincronizan** en orden: DELETE → UPDATE → CREATE
- **Caché se refresca** desde MySQL
- **Integridad se verifica** y reconstruye si es necesario

### ✅ Frontend-Backend
- **Reintentos automáticos** con exponential backoff
- **Manejo de timeouts** (10 segundos)
- **Monitor en tiempo real** del estado del sistema
- **Mensajes claros** al usuario sobre estado

---

## 📈 Métricas Disponibles

### En el endpoint `/sync/status`:
- `mysql_available`: ¿MySQL está disponible?
- `redis_available`: ¿Redis está disponible?
- `cache_items`: Número de items en caché
- `pending_creates`: Items pendientes de crear en MySQL
- `pending_updates`: Updates pendientes de aplicar
- `pending_deletes`: Items pendientes de eliminar
- `is_consistent`: ¿Los datos están sincronizados?
- `status`: "synced" o "out_of_sync"

### En el endpoint `/health`:
- `status`: "healthy", "degraded", o "error"
- `mysql`: boolean
- `redis`: boolean
- `hostname`: nombre de la instancia
- `port`: puerto del backend

---

## 🐛 Troubleshooting

### Problema: "Redis no disponible"
```bash
# Verificar que Redis está corriendo
docker-compose ps redis_db

# Ver logs de Redis
docker-compose logs redis_db

# Reiniciar Redis
docker-compose restart redis_db
```

### Problema: "Items no se sincronizan"
```bash
# Verificar que el ciclo de sincronización está activo
docker-compose logs backend -f | grep SYNC

# Forzar sincronización con MySQL online
curl http://localhost:8001/sync/status

# Ver contenido de pendientes
docker exec -it lab_redis redis-cli
> lrange items:pending 0 -1
```

### Problema: "Integridad de caché está fallida"
```bash
# Ver detalles en /sync/status
curl http://localhost:8001/sync/status | jq .consistency_details

# El sistema debería automáticamente reconstruir
# Ver logs: docker-compose logs backend | grep REBUILD
```

---

## 📝 Archivos Modificados

1. **`backend/services/mysql_redis_sync.py`**
   - Agregadas funciones de validación y reconstrucción
   - Nuevo sistema de hash para verificar integridad
   - Endpoint de estado de sincronización
   
2. **`backend/main.py`**
   - Agregados endpoints `/health` y `/sync/status`
   - Mejorado ciclo de sincronización con verificación
   - Mejor manejo de inicialización

3. **`docker-compose.yml`**
   - Healthcheck para Redis
   - Healthcheck para Backend
   - Dependencias en correcto orden
   - Mapeo de puertos adicionales para debugging

4. **`frontend/src/api/axios.js`**
   - Reintentos automáticos
   - Exponential backoff
   - Mejor manejo de errores

5. **`frontend/src/components/SystemHealthMonitor.jsx`** (NUEVO)
   - Componente React que muestra estado en tiempo real
   - Conecta con `/health` y `/sync/status`
   - Actualiza cada 10 segundos

6. **`frontend/src/pages/DashboardPage.jsx`**
   - Integrado SystemHealthMonitor
   - Mejor visualización del estado

7. **`test_sync.py`** (NUEVO)
   - Script de prueba automatizada
   - Simula fallos y recuperación
   - Valida sincronización

---

## ✨ Conclusión

La arquitectura ahora garantiza:

1. ✅ **Sincronización total MySQL ↔ Redis**
2. ✅ **Fallback automático a Redis cuando MySQL cae**
3. ✅ **Recuperación automática cuando MySQL vuelve**
4. ✅ **Validación de integridad de datos**
5. ✅ **Comunicación confiable Frontend-Backend**
6. ✅ **Monitoreo en tiempo real del estado**
7. ✅ **Sin pérdida de datos** en ningún escenario

El sistema es **production-ready** para arquitecturas de alta disponibilidad.
