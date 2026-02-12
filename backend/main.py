import asyncio
import os
import socket # <--- IMPORTANTE: Para obtener el ID del contenedor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importamos las conexiones y routers
from backend.database import mysql_engine, Base, mongo_client, redis_client
from backend.routers import auth, inventory

# Detectamos el puerto (Por defecto 8001 si no está definido)
PORT = os.getenv("PORT", "8000") 

# Obtenemos el ID único del contenedor (Ej: a123b456...)
# Esto es lo que diferencia a S1, S2 y S3 en el clúster
HOSTNAME = socket.gethostname()

# --- TAREA DE FONDO: HEARTBEAT (LATIDO) ---
async def send_heartbeat():
    """Envía una señal a Redis cada 3 segundos diciendo 'Estoy vivo'"""
    while True:
        try:
            # Clave: instance:ID_CONTENEDOR, Valor: "Online", Expira en: 5s
            # Usamos HOSTNAME para que cada réplica sea única
            await redis_client.setex(f"instance:{HOSTNAME}", 5, "Online")
        except Exception as e:
            print(f"❌ Error Heartbeat Redis: {e}")
        await asyncio.sleep(3)

# --- CICLO DE VIDA DE LA APP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 --- INICIANDO SISLAB (Host: {HOSTNAME} - Puerto {PORT}) ---")
    
    # 1. Verificar MySQL (Solo logs, para no saturar si hay muchas réplicas)
    try:
        # En producción, las migraciones se hacen aparte, pero aquí está bien
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
    print(f"💓 Heartbeat iniciado para el contenedor {HOSTNAME}")

    yield # Aquí corre la aplicación...

    print("🛑 --- APAGANDO SISTEMA ---")

app = FastAPI(lifespan=lifespan)

# --- CONFIGURACIÓN CORS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*", # Permitimos todo para facilitar la demo con Nginx
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRAR RUTAS ---
app.include_router(auth.router)
app.include_router(inventory.router)

# --- EL ENDPOINT QUE TE FALTABA (DASHBOARD) ---
@app.get("/system/status", tags=["Sistema"])
async def get_system_status():
    """Lee Redis para ver qué servidores están vivos y alimenta el Dashboard"""
    instances = []
    # Buscamos todas las claves que empiecen por "instance:*"
    keys = await redis_client.keys("instance:*")
    
    for key in keys:
        # key viene como "instance:a1b2c3d4..."
        # El frontend espera un campo "port", le mandamos el hostname ahí para que lo muestre
        hostname_id = key.split(":")[1]
        status = await redis_client.get(key)
        instances.append({"port": hostname_id, "status": status})
    
    # Ordenamos para que no bailen en la pantalla
    instances.sort(key=lambda x: x["port"])
    return instances

@app.get("/")
def read_root():
    # Retornamos el HOSTNAME para saber quién respondió la petición (S1, S2 o S3)
    return {
        "sistema": "SISLAB", 
        "estado": "Operativo", 
        "servidor_atendiendo": HOSTNAME
    }