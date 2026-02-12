from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import List, Optional
from typing_extensions import Annotated

# --- TRUCO JEDI: Convertir ObjectId a String automáticamente ---
# Esto intercepta el dato antes de validarlo y lo vuelve string
PyObjectId = Annotated[str, BeforeValidator(str)]

class Item(BaseModel):
    id: str = Field(default_factory=lambda: "item_" + str(id(object())))
    name: str
    status: str
    specs: Optional[str] = None

class Laboratory(BaseModel):
    # Mapeamos el "_id" de Mongo al "id" de Python
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: str
    description: str
    items: List[Item] = []

    # Configuración estricta para Pydantic V2
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra = {
            "example": {
                "name": "Lab de Redes",
                "location": "Bloque B",
                "description": "Laboratorio principal",
                "items": []
            }
        }
    )