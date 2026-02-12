from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# --- 1. MySQL (Usuarios) ---
MYSQL_URL = "mysql+pymysql://user:password@localhost:3306/lab_usuarios"
mysql_engine = create_engine(MYSQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)
Base = declarative_base()

# --- 2. MongoDB (Inventario) ---
MONGO_URL = "mongodb://admin:adminpassword@localhost:27018"
mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client.lab_inventario

# --- 3. Redis (Cache/Estado) ---
REDIS_URL = "redis://localhost:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)