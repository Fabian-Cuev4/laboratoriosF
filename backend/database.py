from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Configuración de MySQL
MYSQL_URL = "mysql+pymysql://user:password@localhost:3306/lab_usuarios"

mysql_engine = create_engine(MYSQL_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)

Base = declarative_base()