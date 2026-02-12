from fastapi import APIRouter, HTTPException, status
from backend.database import mongo_db 
from backend.schemas.inventory import Laboratory
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/laboratories", tags=["Inventario (MongoDB)"])

# --- 1. CREAR LABORATORIO (POST) ---
@router.post("/", response_description="Crear nuevo laboratorio", status_code=status.HTTP_201_CREATED, response_model=Laboratory)
async def create_laboratory(lab: Laboratory):
    # Usamos model_dump (La forma nueva de Pydantic V2)
    lab_dict = lab.model_dump(by_alias=True, exclude=["id"])
    
    # Insertamos en Mongo
    new_lab = await mongo_db["laboratories"].insert_one(lab_dict)
    
    # Recuperamos y devolvemos
    created_lab = await mongo_db["laboratories"].find_one({"_id": new_lab.inserted_id})
    return created_lab

# --- 2. LISTAR TODOS LOS LABORATORIOS (GET) ---
@router.get("/", response_description="Listar laboratorios", response_model=List[Laboratory])
async def list_laboratories():
    laboratories = []
    cursor = mongo_db["laboratories"].find()
    async for document in cursor:
        laboratories.append(document)
    return laboratories

# --- 3. AGREGAR COMPUTADORA A UN LAB (PUT) ---
@router.put("/{id}/add-item", response_description="Agregar item a laboratorio")
async def add_item_to_lab(id: str, item_name: str, item_status: str):
    lab = await mongo_db["laboratories"].find_one({"_id": ObjectId(id)})
    if not lab:
        raise HTTPException(status_code=404, detail=f"Laboratorio {id} no encontrado")

    new_item = {
        "id": str(ObjectId()), # ID único para el item
        "name": item_name,
        "status": item_status, 
    }

    await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(id)},
        {"$push": {"items": new_item}}
    )

    return {"mensaje": "Item agregado correctamente", "item": new_item}

# --- 4. OBTENER UN SOLO LAB POR ID (GET) ---
@router.get("/{id}", response_model=Laboratory)
async def get_laboratory(id: str):
    lab = await mongo_db["laboratories"].find_one({"_id": ObjectId(id)})
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    return lab