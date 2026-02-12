import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importaciones usando la ruta absoluta del módulo
from backend.database import mysql_engine, Base, mongo_client, redis_client
from backend.routers import auth, inventory

PORT = os.getenv("PORT", "8001") 

async def send_heartbeat():
    while True:
        try:
            await redis_client.setex(f"instance:{PORT}", 5, "Online")
        except Exception as e:
            print(f"❌ Redis Heartbeat Error: {e}")
        await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 --- INICIANDO SISLAB EN PUERTO {PORT} ---")
    
    # Sincronización de Base de Datos
    try:
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL: Tablas verificadas.")
        await mongo_client.admin.command('ping')
        print("✅ MongoDB: Conectado.")
    except Exception as e:
        print(f"⚠️ Error en inicio de BD: {e}")

    asyncio.create_task(send_heartbeat())
    yield
    print("🛑 --- APAGANDO SISTEMA ---")

app = FastAPI(lifespan=lifespan)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE RUTAS ---
# Importante: Asegurarse de que el router se incluya correctamente
app.include_router(auth.router)
app.include_router(inventory.router)

@app.get("/")
def read_root():
    return {"status": "online", "port": PORT, "msg": "API SISLAB Funcionando"}