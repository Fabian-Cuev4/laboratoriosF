import asyncio
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importamos las conexiones
from backend.database import mysql_engine, Base, mongo_client, redis_client
from backend.routers import auth, inventory

# --- TRUCO: Detectar en qué puerto estamos corriendo ---
# Si no lo encuentra, asume el 8001 (por defecto)
PORT = os.getenv("PORT", "8001") 

# --- TAREA DE FONDO: HEARTBEAT (Latido) ---
async def send_heartbeat():
    """Envía una señal a Redis cada 3 segundos diciendo 'Estoy vivo'"""
    while True:
        try:
            # Clave: instance:8001, Valor: "Online" (con expiración de 5s)
            # Si el servidor muere, la clave desaparece sola en 5s (TTL)
            await redis_client.setex(f"instance:{PORT}", 5, "Online")
        except Exception as e:
            print(f"Error enviando heartbeat: {e}")
        await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- AL INICIAR ---
    print(f"--- INICIANDO SISTEMA SISLAB (Puerto {PORT}) ---")
    
    # 1. Verificar MySQL
    try:
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL: Sincronizado.")
    except Exception as e: print(f"❌ MySQL Error: {e}")

    # 2. Verificar Mongo
    try:
        await mongo_client.admin.command('ping')
        print("✅ MongoDB: Conectado.")
    except Exception as e: print(f"❌ MongoDB Error: {e}")

    # 3. Iniciar el Heartbeat en segundo plano
    asyncio.create_task(send_heartbeat())
    print(f"💓 Heartbeat iniciado para el puerto {PORT}")

    yield # Aquí corre la aplicación...

    # --- AL APAGAR ---
    print("--- APAGANDO SISTEMA ---")

app = FastAPI(lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS ---
app.include_router(auth.router)
app.include_router(inventory.router)

# --- NUEVO ENDPOINT PARA EL DASHBOARD (SYSTEM STATUS) ---
@app.get("/system/status", tags=["Sistema"])
async def get_system_status():
    """Lee Redis para ver qué servidores están vivos"""
    instances = []
    # Buscamos todas las claves que empiecen por "instance:*"
    keys = await redis_client.keys("instance:*")
    
    for key in keys:
        port = key.split(":")[1]
        status = await redis_client.get(key)
        instances.append({"port": port, "status": status})
    
    # Ordenamos por puerto para que se vea bonito
    instances.sort(key=lambda x: x["port"])
    return instances

@app.get("/")
def read_root():
    return {"sistema": "SISLAB", "instancia": PORT}