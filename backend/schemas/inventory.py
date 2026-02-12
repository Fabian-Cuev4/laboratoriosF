from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

# Esto permite que Pydantic maneje los IDs de Mongo
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Modelo de una Computadora o Item dentro del laboratorio
class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId())) # ID único del item
    name: str   # Ej: "PC-01"
    status: str # Ej: "Operativa", "Dañada", "En Mantenimiento"
    specs: Optional[str] = None # Ej: "i7 16GB RAM"

# Modelo del Laboratorio Completo
class Laboratory(BaseModel):
    id: Optional[str] = Field(alias="_id") # El ID de Mongo
    name: str        # Ej: "Laboratorio de Redes"
    location: str    # Ej: "Edificio B, Piso 2"
    description: str
    items: List[Item] = [] # Lista de computadoras dentro

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "name": "Laboratorio de Software",
                "location": "Piso 3",
                "description": "Lab principal para desarrollo",
                "items": []
            }
        }