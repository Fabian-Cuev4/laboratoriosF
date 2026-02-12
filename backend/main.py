from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# Importamos la configuración de MySQL desde el nuevo archivo
from backend.database import mysql_engine, Base
from backend.routers import auth 

app = FastAPI()

app.include_router(auth.router)

# --- CONFIGURACIÓN DE CONEXIONES ---

# 2. MongoDB
MONGO_URL = "mongodb://admin:adminpassword@localhost:27018"
mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client.lab_inventario

# 3. Redis
REDIS_URL = "redis://localhost:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup_db():
    # 1. Crear tablas en MySQL automáticamente
    try:
        # Usamos el engine importado de database.py
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL: Tablas creadas/verificadas correctamente.")
    except Exception as e:
        print(f"❌ MySQL Error al crear tablas: {e}")

    # 2. Verificar Mongo
    try:
        await mongo_client.admin.command('ping')
        print("✅ MongoDB: Conectado.")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

    # 3. Verificar Redis
    try:
        await redis_client.ping()
        print("✅ Redis: Conectado.")
    except Exception as e:
        print(f"❌ Redis Error: {e}")

@app.get("/")
def read_root():
    return {"sistema": "SISLAB", "estado": "online"}