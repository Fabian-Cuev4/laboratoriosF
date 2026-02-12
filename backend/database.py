import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# --- DETECTOR DE ENTORNO ---
# Si existe la variable MYSQL_URL (que pusimos en el docker-compose), úsala.
# Si no, usa la de localhost.

# 1. MySQL
DATABASE_URL = os.getenv("MYSQL_URL", "mysql+pymysql://user:password@localhost:3306/lab_usuarios")
mysql_engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)
Base = declarative_base()

# 2. MongoDB
MONGO_URI = os.getenv("MONGO_URL", "mongodb://admin:adminpassword@localhost:27018")
mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client.lab_inventario

# 3. Redis
REDIS_URI = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URI, decode_responses=True)