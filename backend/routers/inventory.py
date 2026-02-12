from fastapi import APIRouter, HTTPException, status, Body
from backend.database import mongo_db 
from backend.schemas.inventory import Laboratory, Item, MaintenanceCreate, ItemCreate
from bson import ObjectId
from typing import List
from datetime import datetime

router = APIRouter(prefix="/laboratories", tags=["Inventario (MongoDB)"])

# --- 1. CREAR LABORATORIO ---
@router.post("/", response_description="Crear nuevo laboratorio", status_code=status.HTTP_201_CREATED, response_model=Laboratory)
async def create_laboratory(lab: Laboratory):
    lab_dict = lab.model_dump(by_alias=True, exclude=["id"])
    new_lab = await mongo_db["laboratories"].insert_one(lab_dict)
    created_lab = await mongo_db["laboratories"].find_one({"_id": new_lab.inserted_id})
    return created_lab

# --- 2. LISTAR TODOS ---
@router.get("/", response_description="Listar laboratorios", response_model=List[Laboratory])
async def list_laboratories():
    laboratories = []
    cursor = mongo_db["laboratories"].find()
    async for document in cursor:
        laboratories.append(document)
    return laboratories

# --- 3. OBTENER UNO SOLO ---
@router.get("/{id}", response_description="Obtener un laboratorio", response_model=Laboratory)
async def get_laboratory(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    lab = await mongo_db["laboratories"].find_one({"_id": ObjectId(id)})
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    return lab

# --- 4. AGREGAR ITEM (CORREGIDO PARA RECIBIR JSON COMPLETO) ---
# --- 4. AGREGAR ITEM (Usando Pydantic) ---
@router.put("/{id}/add-item")
async def add_item_to_lab(id: str, item_data: ItemCreate):
    new_item = {
        "id": str(ObjectId()),
        "name": item_data.code, # Nombre visual
        **item_data.model_dump(), # Desempaquetar resto de datos
        "maintenance_history": []
    }
    await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(id)}, {"$push": {"items": new_item}}
    )
    return {"message": "Item agregado", "item": new_item}

# --- 5. ACTUALIZAR ITEM ---
@router.put("/{lab_id}/items/{item_id}")
async def update_item(lab_id: str, item_id: str, item_data: ItemCreate):
    await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(lab_id), "items.id": item_id},
        {"$set": {
            "items.$.name": item_data.code,
            "items.$.code": item_data.code,
            "items.$.type": item_data.type,
            "items.$.status": item_data.status,
            "items.$.area": item_data.area,
            "items.$.acquisition_date": item_data.acquisition_date
        }}
    )
    return {"message": "Item actualizado"}

# --- 6. AGREGAR MANTENIMIENTO (CORREGIDO ERROR 422) ---
@router.post("/{lab_id}/items/{item_id}/maintenance")
async def add_maintenance(lab_id: str, item_id: str, maintenance: MaintenanceCreate):
    new_log = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        **maintenance.model_dump()
    }
    await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(lab_id), "items.id": item_id},
        {"$push": {"items.$.maintenance_history": new_log}}
    )
    return {"message": "Mantenimiento registrado"}

# --- 7. REPORTE GENERAL (NUEVO PARA TU TABLA) ---
@router.get("/reports/all-items")
async def get_all_items_report():
    """Busca en TODOS los laboratorios y extrae TODAS las máquinas"""
    pipeline = [
        {"$unwind": "$items"}, # Desglosa el array de items
        {"$project": {         # Selecciona campos para la tabla
            "_id": 0,
            "lab_name": "$name",
            "location": "$location",
            "id": "$items.id",
            "code": "$items.code",
            "type": "$items.type",
            "status": "$items.status",
            "technician": {"$last": "$items.maintenance_history.technician"}, # Último técnico
            "last_date": {"$last": "$items.maintenance_history.date"},       # Última fecha
            "last_desc": {"$last": "$items.maintenance_history.description"} # Última descripción
        }}
    ]
    cursor = mongo_db["laboratories"].aggregate(pipeline)
    items = await cursor.to_list(length=1000)
    return items