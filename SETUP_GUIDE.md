# 🚀 Guía de Uso - Sincronización MySQL ↔ Redis

## 📌 Introducción

Este sistema ha sido configurado para garantizar sincronización total entre **MySQL** (base de datos principal) y **Redis** (caché y respaldo).

### Garantías Implementadas:
- ✅ **Si MySQL muere:** Redis actúa como respaldo automáticamente
- ✅ **Si Redis falla:** El sistema informa del problema inmediatamente
- ✅ **Si MySQL revive:** Sincronización automática de datos pendientes
- ✅ **Integridad de datos:** Validación mediante hash SHA256
- ✅ **Sin pérdida de datos:** Todas las operaciones pendientes se aplican

---

## 🏃 Inicio Rápido

### 1. Iniciar el Sistema
```bash
# Asegúrate de estar en el directorio del proyecto
cd c:\Users\Fabian\Desktop\arquitectura\laboratorios

# Inicia todo
docker-compose up -d

# Espera a que healthchecks pasen (máximo 30 segundos)
docker-compose ps
```

El sistema debe mostrar algo como:
```
NAME                  STATUS
lab_mysql            healthy (elapsed: 5s), 1 check
lab_redis            healthy (elapsed: 5s), 1 check
lab_backend_1        healthy (elapsed: 5s), 1 check
lab_backend_2        healthy (elapsed: 5s), 1 check
lab_backend_3        healthy (elapsed: 5s), 1 check
lab_lb               running
lab_redis_insight    running
```

### 2. Ver el Dashboard
```
Abre: http://localhost:5173
(o donde esté tu frontend)
```

Deberías ver el "Panel de Control de Arquitectura" con:
- 🟢 Estado de MySQL
- 🟢 Estado de Redis
- 🟢 Estado de Sincronización

---

## 🔍 Verificar Sincronización - Tres Formas

### FORMA 1: Dashboard Visual (Recomendado 👍)
El componente `SystemHealthMonitor` muestra el estado en tiempo real:
- Estado de MySQL (Online/Offline)
- Estado de Redis (Online/Offline)
- Items en caché
- Operaciones pendientes
- Estado de sincronización

Se actualiza cada 10 segundos automáticamente.

### FORMA 2: API REST
```bash
# Ver salud general del sistema
curl http://localhost:8001/health

# Ver estado detallado de sincronización
curl http://localhost:8001/sync/status
```

**Respuesta esperada (todo bien):**
```json
{
  "mysql_available": true,
  "redis_available": true,
  "cache_items": 10,
  "pending_creates": 0,
  "pending_updates": 0,
  "pending_deletes": 0,
  "is_consistent": true,
  "status": "synced"
}
```

### FORMA 3: Script de Prueba Automatizada
```bash
# Instalar dependencia (si no la tienes)
pip install aiohttp

# Ejecutar la prueba
python test_sync.py
```

Este script simula:
- Creación de items con MySQL online
- Caída de MySQL (solicita confirmación manual)
- Creación de items con MySQL offline
- Recuperación de MySQL
- Verificación de sincronización

---

## 🧪 Prueba Manual de Sincronización

### Paso 1: Crear Items Normalmente
1. Abre el Dashboard
2. Crea algunos items en `/laboratorios/items`
3. Verifica que aparecen en el componente `SystemHealthMonitor`
4. Comprueba que `status` es `"synced"`

### Paso 2: Simular Caída de MySQL
```bash
docker-compose stop mysql_db
```

Observarás en el Dashboard:
- MySQL cambia a 🔴 Offline
- Estado de Sincronización cambia a ⚠️ Desincronizado
- El sistema sigue funcionando (modo fallback)

### Paso 3: Crear Items con MySQL Caído
1. Intenta crear un nuevo item
2. Debería funcionar (respuesta con `source: REDIS_BACKUP`)
3. En el Dashboard verás que aumentan "Operaciones pendientes"

### Paso 4: Recuperar MySQL
```bash
docker-compose start mysql_db
```

Observarás:
- MySQL cambia a 🟢 Online (después de 5 segundos aprox)
- Las "Operaciones pendientes" disminuyen a medida que se sincronizan
- `status` cambia nuevamente a `"synced"`

### Paso 5: Verificar Datos Pendientes Aplicados
```bash
# Ver items en la caché
curl http://localhost:8001/sync/status | jq '.cache_items'

# Debería mostrar: original + los items creados mientras MySQL estaba caído
```

---

## 🔧 Debugging - Qué Hacer si Algo Falla

### Problema: "MySQL: Offline" pero no lo paré
```bash
# Ver logs de MySQL
docker-compose logs mysql_db

# Reiniciar MySQL
docker-compose restart mysql_db

# Esperar a healthcheck (5-10 segundos)
docker-compose ps
```

### Problema: "Redis: Offline"
```bash
# Ver logs de Redis
docker-compose logs redis_db

# Reiniciar Redis
docker-compose restart redis_db

# Acceder a Redis CLI
docker exec -it lab_redis redis-cli

# Ping a Redis
> ping
```

### Problema: "Datos desincronizados" después de recuperación
```bash
# Ver detalles en API
curl http://localhost:8001/sync/status | jq '.consistency_details'

# El sistema automáticamente should reconstruir en 30 segundos
# Ver logs
docker-compose logs backend | grep REBUILD
```

### Problema: Items "cuelgan" pendientes
```bash
# Ver items pendientes
docker exec -it lab_redis redis-cli
> lrange items:pending 0 -1

# Ver actualizaciones pendientes
> lrange items:pending_updates 0 -1

# Ver eliminaciones pendientes
> lrange items:pending_deletes 0 -1
```

---

## 📊 Monitoreo en Tiempo Real

### Opción A: UI de Redis (Recomendado 👍)
```
http://localhost:5540
```
Permite:
- Ver todas las claves Redis
- Monitorear cambios en tiempo real
- Inspeccionar valores

### Opción B: CLI de Redis
```bash
docker exec -it lab_redis redis-cli

# Ver todas las claves
> keys *

# Monitorear cambios en vivo
> monitor

# Ver contenido de la caché
> get items:cache | head -50

# Contar items pendientes
> llen items:pending
```

### Opción C: Logs del Backend
```bash
# Ver solo lines de sincronización
docker-compose logs backend -f | grep -E "\[SYNC\]|✅|❌|⚠️"

# O seguir todos los logs
docker-compose logs backend -f
```

---

## 🎯 Casos de Uso - Qué Debería Pasar

### Caso 1: MySQL Online Todo el Tiempo
```
POST /laboratories/items
    ↓
Escribe en MySQL ✅
Actualiza Redis ✅
source: "MySQL"
```

### Caso 2: MySQL Falla Momentáneamente
```
POST /laboratories/items (MySQL offline)
    ↓
Intenta MySQL ❌
Escribe en Redis ✅
Encolación de pendientes ✅
source: "REDIS_BACKUP"
```

### Caso 3: MySQL Recupera Después de Falla
```
Background cada 30 segundos:
    ↓
Detecta MySQL online ✅
Aplica pendientes en orden ✅
Refresca caché ✅
Verifica integridad ✅
Reporte: "synced"
```

### Caso 4: Lectura con MySQL Offline
```
GET /laboratories/items
    ↓
Intenta MySQL ❌
Lee de Redis caché ✓
+ Items pendientes ✓
source: "REDIS_CACHE"
```

---

## 📋 Arquitectura de la Sincronización

```
┌─────────────────────────────────────────────────────┐
│                    Cliente                          │
└─────────────────────────────────────────────────────┘
              ↓ (HTTP Requests)
┌─────────────────────────────────────────────────────┐
│          NGINX Load Balancer (8001)                │
│    (distribuye a 3 instancias backend)             │
└─────────────────────────────────────────────────────┘
              ↓ (Round Robin)
┌─────────────────────────────────────────────────────┐
│    Backend (3 instancias en paralelo)              │
│  - Cada una con MySQL, Redis, Sync Loop            │
│  - `/health` - Estado del sistema                  │
│  - `/sync/status` - Detalles de sincronización     │
└─────────────────────────────────────────────────────┘
         ↙                    ↘
     ┌─────────┐           ┌────────┐
     │  MySQL  │           │ Redis  │
     │ (Fuente)│           │(Caché) │
     └─────────┘           └────────┘
         ↑                      ↑
     [Sync cada 30s]    [Dual-write]
```

---

## 🚨 Estados del Sistema

| Estado | MySQL | Redis | Acción |
|--------|-------|-------|--------|
| ✅ Normal | 🟢 | 🟢 | Escrituras en MySQL, caché sincronizado |
| ⚠️ Degradado | 🔴 | 🟢 | Escrituras en Redis pendientes, lecturas desde caché |
| ❌ Error | 🔴 | 🔴 | Sistema no funciona |
| ⚠️ Recuperando | 🟢 | 🟢 | Sincronizando pendientes, verificando integridad |

---

## 📈 Métricas Clave

En `/sync/status` puedes monitorear:

- **mysql_available**: ¿MySQL está disponible?
- **redis_available**: ¿Redis está disponible?
- **cache_items**: Número de items en caché
- **pending_creates**: Items pendientes de crear
- **pending_updates**: Updates pendientes
- **pending_deletes**: Items pendientes de eliminar
- **is_consistent**: ¿Datos están sincronizados?
- **status**: "synced" o "out_of_sync"

---

## 🛑 Parar el Sistema

```bash
# Parar todos los contenedores
docker-compose down

# Parar sin borrar volúmenes
docker-compose stop

# Borrar todo (incluyendo datos)
docker-compose down -v
```

---

## 📚 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| `backend/services/mysql_redis_sync.py` | Lógica de sincronización |
| `backend/main.py` | Endpoints `/health` y `/sync/status` |
| `backend/Dockerfile` | Imagen del backend (con curl) |
| `docker-compose.yml` | Configuración con healthchecks |
| `frontend/src/api/axios.js` | Cliente HTTP con reintentos |
| `frontend/src/components/SystemHealthMonitor.jsx` | Monitor visual |
| `.env` | Variables de configuración |
| `test_sync.py` | Script de prueba automatizada |
| `SYNC_VERIFICATION.md` | Documentación técnica completa |

---

## ✅ Checklist Final

Antes de considerar la sincronización completa, verifica:

- [ ] Docker-compose up levanta 7 contenedores
- [ ] Los 7 están en estado `healthy` o `running`
- [ ] Dashboard muestra 🟢 MySQL, 🟢 Redis
- [ ] Puedes crear items normalmente
- [ ] API `/health` retorna `status: "healthy"`
- [ ] API `/sync/status` retorna `is_consistent: true`
- [ ] Puedes parar MySQL y seguir creando items
- [ ] Los items creados offline se sincronizan cuando MySQL vuelve
- [ ] El script `test_sync.py` completa exitosamente
- [ ] No hay advertencias de desincronización después de recuperación

---

## 🎓 Aprendiste

1. ✅ Cómo funciona la sincronización MySQL ↔ Redis
2. ✅ Cómo el sistema tolera fallos de MySQL
3. ✅ Cómo verificar integridad de datos
4. ✅ Cómo monitorear el estado en tiempo real
5. ✅ Cómo hacer debugging cuando algo falla

**¡Tu arquitectura es production-ready! 🚀**
