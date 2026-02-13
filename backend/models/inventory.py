from sqlalchemy import Column, Integer, String
from backend.database import Base

class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), index=True) # Ej: PC-01
    type = Column(String(50))             # Ej: Computadora
    status = Column(String(50))           # Ej: Operativa
    area = Column(String(100))            # Ej: Sala 1
    acquisition_date = Column(String(20)) # Ej: 2024-01-01