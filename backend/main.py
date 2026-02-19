import asyncio
import os
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importamos DB y Routers
from backend.database import mysql_engine, Base, mongo_client, redis_client
from backend.routers import auth, inventory
# IMPORTANTE: Importar el modelo para que SQLAlchemy cree la tabla
from backend.models.inventory import ItemModel
from backend.services.mysql_redis_sync import (
    check_mysql_available,
    check_redis_available,
    full_sync_on_mysql_recovery,
    migrate_backup_items_to_pending,
    rebuild_cache_from_mysql,
    get_sync_status,
    verify_cache_integrity,
) 

PORT = os.getenv("PORT", "8000") 
HOSTNAME = socket.gethostname()

# --- HEARTBEAT (Latido) ---
async def send_heartbeat():
    while True:
        try:
            # 1. Decir "Estoy Vivo" (Status)
            await redis_client.setex(f"instance:{HOSTNAME}", 5, "Online")
            # 2. Inicializar el contador en 0 si no existe (para que salga en la gráfica)
            await redis_client.setnx(f"requests:{HOSTNAME}", 0)
        except Exception as e:
            print(f"❌ Error Redis: {e}")
        await asyncio.sleep(3)

# --- SINCRONIZACIÓN MYSQL ↔ REDIS ---
async def mysql_redis_sync_loop():
    """
    Tarea periódica: si MySQL está disponible, sincroniza pendientes de Redis → MySQL
    y refresca la caché Redis desde MySQL.
    También verifica integridad de la caché.
    """
    while True:
        try:
            await asyncio.sleep(2)  # Cada 2 segundos
            
            mysql_ok = await check_mysql_available()
            redis_ok = await check_redis_available()
            
            if not redis_ok:
                print("⚠️ [SYNC] Redis no disponible, saltando sincronización")
                continue
            
            if mysql_ok:
                # MySQL está disponible - sincronizar pendientes y verificar integridad
                result = await full_sync_on_mysql_recovery()
                if any(v > 0 for k, v in result.items() if k != "integrity_verified"):
                    print(f"✅ [SYNC] MySQL recuperado: {result}")
                
                # Verificar integridad de la caché
                is_valid, details = await verify_cache_integrity()
                if not is_valid:
                    print(f"⚠️ [SYNC] Caché inconsistente: {details}. Reconstruyendo...")
                    await rebuild_cache_from_mysql()
            else:
                # MySQL no está disponible - reportar estado
                print("⚠️ [SYNC] MySQL no disponible. Redis actúa como respaldo.")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ [SYNC] Error en tarea de sincronización: {e}")


# --- CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 INICIANDO {HOSTNAME} en Puerto {PORT}")

    # Crear tablas en MySQL (Auth e Inventario)
    try:
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL: Tablas sincronizadas.")
    except Exception as e:
        print(f"❌ MySQL Error: {e}")

    # Sincronización inicial MySQL ↔ Redis
    try:
        mysql_ok = await check_mysql_available()
        redis_ok = await check_redis_available()
        
        if not redis_ok:
            print("❌ Redis no está disponible. Sistema no puede iniciar sin Redis.")
            raise Exception("Redis no disponible")
        
        if mysql_ok:
            # Migrar datos legacy y sincronizar
            migrated = await migrate_backup_items_to_pending()
            if migrated:
                print(f"✅ [SYNC] Migrados {migrated} items de backup_items legacy")
            
            result = await full_sync_on_mysql_recovery()
            print(f"✅ [SYNC] Inicial: {result}")
        else:
            print("⚠️ [SYNC] MySQL no disponible al iniciar. Reconstruyendo caché desde backup...")
            # Intentar reconstruir desde caché existente
            cache_exists = await redis_client.get("items:cache")
            if not cache_exists:
                print("⚠️ [SYNC] No hay caché anterior. El sistema operará en modo 'vacío' hasta que MySQL se recupere.")
            else:
                print("✅ [SYNC] Caché anterior restaurado. Redis servirá como fuente de verdad.")
    except Exception as e:
        print(f"⚠️ [SYNC] Error sincronización inicial: {e}")

    # Iniciar Heartbeat y tarea de sincronización
    asyncio.create_task(send_heartbeat())
    sync_task = asyncio.create_task(mysql_redis_sync_loop())

    yield

    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass
    print("🛑 APAGANDO SISTEMA")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir todo para la demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth.router)
app.include_router(inventory.router)

# --- ENDPOINT DE SALUD (HEALTH CHECK) ---
@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica que el sistema esté funcionando correctamente"""
    try:
        mysql_ok = await check_mysql_available()
        redis_ok = await check_redis_available()
        
        if not redis_ok:
            return {
                "status": "unhealthy",
                "mysql": mysql_ok,
                "redis": redis_ok,
                "message": "Redis no disponible"
            }
        
        return {
            "status": "healthy" if mysql_ok else "degraded",
            "mysql": mysql_ok,
            "redis": redis_ok,
            "hostname": HOSTNAME,
            "port": PORT
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# --- ENDPOINT DE ESTADO DE SINCRONIZACIÓN ---
@app.get("/sync/status", tags=["Sincronización"])
async def sync_status():
    """Devuelve el estado actual de la sincronización MySQL ↔ Redis"""
    return await get_sync_status()


# --- ENDPOINT DASHBOARD (Consolidado) ---
@app.get("/system/status", tags=["Sistema"])
async def get_system_status():
    """Devuelve estado (Cajas Verdes) Y tráfico (Barras)"""
    instances = []
    # Buscamos claves de instancias
    keys = await redis_client.keys("instance:*")
    
    for key in keys:
        hostname_id = key.split(":")[1]
        status = await redis_client.get(key)
        # Buscamos cuántas peticiones ha atendido este servidor
        count = await redis_client.get(f"requests:{hostname_id}")
        
        instances.append({
            "port": hostname_id,    # ID del servidor
            "status": status,       # Online/Offline
            "requests": int(count) if count else 0 # Número para la gráfica
        })
    
    instances.sort(key=lambda x: x["port"])
    return instances

# --- ENDPOINT QUE GOLPEA K6 ---
@app.get("/")
async def read_root():
    # INCREMENTAR CONTADOR DE TRÁFICO
    # Cada vez que K6 entra aquí, sube +1 en Redis para este servidor
    try:
        await redis_client.incr(f"requests:{HOSTNAME}")
    except:
        pass

    return {
        "sistema": "SISLAB", 
        "servidor": HOSTNAME,
        "mensaje": "Petición procesada correctamente"
    }


@app.delete("/system/reset")
async def reset_counters():
    """Reinicia los contadores de las gráficas a cero"""
    # 1. Busca las claves REALES (requests:*)
    keys = await redis_client.keys("requests:*")
    
    # 2. Si encuentra alguna, las borra
    if keys:
        await redis_client.delete(*keys)
        
    # 3. Opcional: Reiniciar a 0 explícitamente para que no desaparezcan de la gráfica
    # (Si las borras totalmente, podrían desaparecer las barras hasta el próximo heartbeat)
    active_instances = await redis_client.keys("instance:*")
    for instance in active_instances:
        hostname = instance.split(":")[1]
        await redis_client.set(f"requests:{hostname}", 0)

    return {"message": "🧹 Contadores reiniciados correctamente"}

# --- RUTA COMODÍN (CATCH-ALL) PARA DEMOS ---
# Esto captura cualquier ruta no definida arriba (como /logo.png)
# y cuenta la visita para que la gráfica se mueva.
@app.get("/{full_path:path}")
async def catch_all_demo(full_path: str):
    try:
        # ¡IMPORTANTE! Sumar al contador
        await redis_client.incr(f"requests:{HOSTNAME}")
    except Exception as e:
        print(f"Error contando: {e}")

    return {
        "mensaje": "Ruta de demostración capturada", 
        "ruta_simulada": full_path,
        "servidor_atendiendo": HOSTNAME
    }