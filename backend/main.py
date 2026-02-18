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

# --- CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 INICIANDO {HOSTNAME} en Puerto {PORT}")
    
    # Crear tablas en MySQL (Auth e Inventario)
    try:
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL: Tablas sincronizadas.")
    except Exception as e: print(f"❌ MySQL Error: {e}")

    # Iniciar Heartbeat
    asyncio.create_task(send_heartbeat())
    yield
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