from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import List, Optional
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

# Esquema para recibir mantenimiento (JSON Body)
class MaintenanceCreate(BaseModel):
    technician: str
    type: str
    description: str

# Esquema para crear/actualizar Item
class ItemCreate(BaseModel):
    code: str
    type: str
    status: str
    area: str
    acquisition_date: str = "2024-01-01"

class MaintenanceLog(BaseModel):
    date: str
    type: str
    technician: str
    description: str

class Item(BaseModel):
    id: str = Field(default_factory=lambda: "item_" + str(id(object())))
    name: str 
    code: str = "S/N"
    type: str = "Equipo"
    status: str
    area: str = "General"
    acquisition_date: str = ""
    maintenance_history: List[MaintenanceLog] = []

class Laboratory(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: str
    description: str
    items: List[Item] = []

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)