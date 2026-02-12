from sqlalchemy import Column, Integer, String, Boolean
from backend.database import Base


class User(Base):
    __tablename__ = "users"  # Nombre de la tabla en MySQL

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True) # Ej: "kenny"
    email = Column(String(100), unique=True, index=True)   # Ej: "kenny@uce.edu.ec"
    password = Column(String(255))  # Aquí guardaremos la contraseña encriptada (Hash)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="student") # "admin" o "student"