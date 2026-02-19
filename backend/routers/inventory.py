from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from backend.database import get_db, mongo_db
from backend.models.inventory import ItemModel
from backend.schemas.inventory import ItemCreate, Laboratory
from backend.services.mysql_redis_sync import (
    check_mysql_available,
    get_items_from_redis_fallback,
    add_item_to_redis_cache,
    add_item_to_redis_pending_and_cache,
    add_pending_update,
    add_pending_delete,
    update_item_in_redis_cache,
    delete_item_from_redis_cache,
)
from bson import ObjectId
from typing import List, Dict
import uuid  # Para generar IDs unicos para los items de mongo

router = APIRouter(prefix="/laboratories", tags=["Gestión Híbrida"])

# ==========================================
# 🟠 PARTE 1: MYSQL + REDIS (Inventario Global - Sincronizado)
# ==========================================


@router.get("/items")
async def list_global_items(db: Session = Depends(get_db)):
    try:
        items = db.query(ItemModel).all()
        data = [
            {
                "id": i.id,
                "code": i.code,
                "type": i.type,
                "status": i.status,
                "area": i.area,
                "acquisition_date": getattr(i, "acquisition_date", "") or "",
            }
            for i in items
        ]
        return {"source": "MySQL", "data": data}
    except Exception as e:
        print(f"⚠️ [MySQL CAÍDO] Leyendo desde Redis: {e}")
        data = await get_items_from_redis_fallback()
        if not data:
            return {"source": "REDIS_EMPTY", "data": [], "message": "No hay datos en respaldo"}
        return {"source": "REDIS_CACHE", "message": "Modo de Emergencia - Redis como caché", "data": data}


@router.post("/items")
async def create_global_item(item: ItemCreate, db: Session = Depends(get_db)):
    item_dict = item.model_dump()
    try:
        new_db_item = ItemModel(**item_dict)
        db.add(new_db_item)
        db.commit()
        db.refresh(new_db_item)
        # Dual-write: mantener Redis sincronizado
        item_with_id = {
            "id": new_db_item.id,
            "code": new_db_item.code,
            "type": new_db_item.type,
            "status": new_db_item.status,
            "area": new_db_item.area,
            "acquisition_date": getattr(new_db_item, "acquisition_date", "") or "",
        }
        await add_item_to_redis_cache(item_with_id)
        return {"source": "MySQL", "status": "success", "data": item_with_id}
    except Exception as e:
        print(f"⚠️ [MySQL FALLÓ] Guardando en Redis: {e}")
        await add_item_to_redis_pending_and_cache(item_dict)
        return {
            "source": "REDIS_BACKUP",
            "status": "warning",
            "message": "MySQL no disponible. Guardado en Redis. Se sincronizará cuando MySQL vuelva.",
            "data": item_dict,
        }


@router.put("/items/{item_id}")
async def update_global_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    item_data = item.model_dump()
    try:
        db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item no encontrado en MySQL")

        db_item.code = item.code
        db_item.type = item.type
        db_item.status = item.status
        db_item.area = item.area
        if hasattr(db_item, "acquisition_date"):
            db_item.acquisition_date = item.acquisition_date

        db.commit()
        db.refresh(db_item)
        # Dual-write: actualizar Redis
        updated = {
            "id": db_item.id,
            "code": db_item.code,
            "type": db_item.type,
            "status": db_item.status,
            "area": db_item.area,
            "acquisition_date": getattr(db_item, "acquisition_date", "") or "",
        }
        await update_item_in_redis_cache(item_id, updated)
        return {"source": "MySQL", "status": "updated", "data": updated}
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ [MySQL FALLÓ] Aplicando update en Redis: {e}")
        # Fallback: buscar en caché Redis y actualizar ahí
        found = await update_item_in_redis_cache(
            item_id,
            {k: v for k, v in item_data.items() if k in ("code", "type", "status", "area", "acquisition_date")},
        )
        if not found:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        await add_pending_update(item_id, item_data)
        return {
            "source": "REDIS_BACKUP",
            "status": "warning",
            "message": "MySQL no disponible. Actualización en Redis. Se sincronizará cuando MySQL vuelva.",
            "data": {**item_data, "id": item_id},
        }


@router.delete("/items/{item_id}")
async def delete_global_item(item_id: int, db: Session = Depends(get_db)):
    try:
        db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item no encontrado")

        db.delete(db_item)
        db.commit()
        # Dual-write: eliminar de Redis
        await delete_item_from_redis_cache(item_id)
        return {"source": "MySQL", "status": "deleted", "id": item_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ [MySQL FALLÓ] Aplicando delete en Redis: {e}")
        # Fallback: eliminar de caché Redis
        found = await delete_item_from_redis_cache(item_id)
        if not found:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        await add_pending_delete(item_id)
        return {
            "source": "REDIS_BACKUP",
            "status": "warning",
            "message": "MySQL no disponible. Eliminado de Redis. Se sincronizará cuando MySQL vuelva.",
            "id": item_id,
        }

# ==========================================
# 🟢 PARTE 2: MONGODB (Gestión Detallada de Laboratorios)
# ==========================================

@router.get("/", response_description="Listar laboratorios")
async def list_laboratories():
    laboratories = []
    cursor = mongo_db["laboratories"].find()
    async for document in cursor:
        document["id"] = str(document["_id"])
        del document["_id"]
        laboratories.append(document)
    return laboratories

@router.post("/", response_description="Crear laboratorio", status_code=201)
async def create_laboratory(lab: Laboratory):
    lab_dict = lab.model_dump(by_alias=True, exclude=["id"])
    if "items" not in lab_dict: lab_dict["items"] = [] # Asegurar que exista array
    new_lab = await mongo_db["laboratories"].insert_one(lab_dict)
    created_lab = await mongo_db["laboratories"].find_one({"_id": new_lab.inserted_id})
    created_lab["id"] = str(created_lab["_id"])
    del created_lab["_id"]
    return created_lab

@router.get("/{id}", response_description="Obtener un laboratorio")
async def get_laboratory(id: str):
    if not ObjectId.is_valid(id): raise HTTPException(status_code=400, detail="ID inválido")
    lab = await mongo_db["laboratories"].find_one({"_id": ObjectId(id)})
    if not lab: raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    lab["id"] = str(lab["_id"])
    del lab["_id"]
    return lab

# 7. ELIMINAR LABORATORIO (MONGO)
@router.delete("/{id}", response_description="Eliminar laboratorio")
async def delete_laboratory(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    result = await mongo_db["laboratories"].delete_one({"_id": ObjectId(id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    
    return {"message": "Laboratorio eliminado correctamente"}

# --- ENDPOINT QUE FALTABA 1: AGREGAR ITEM A UN LAB (MONGO) ---
@router.put("/{id}/add-item")
async def add_item_to_lab(id: str, item: ItemCreate):
    # Generamos un ID único para el item dentro de Mongo
    new_item = item.model_dump()
    new_item["id"] = str(uuid.uuid4()) # ID único simulado
    new_item["maintenance_history"] = [] # Array vacío para mantenimientos

    result = await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(id)},
        {"$push": {"items": new_item}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    return {"message": "Máquina agregada a MongoDB", "item": new_item}

# --- ENDPOINT DE ACTUALIZAR (Ya lo tenías) ---
@router.put("/{lab_id}/items/{item_id}")
async def update_mongo_item(lab_id: str, item_id: str, item_data: ItemCreate):
    update_data = {
        "items.$.code": item_data.code,
        "items.$.type": item_data.type,
        "items.$.status": item_data.status,
        "items.$.area": item_data.area
    }
    result = await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(lab_id), "items.id": item_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
         raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"message": "Item actualizado"}

# --- ENDPOINT QUE FALTABA 2: AGREGAR MANTENIMIENTO (MONGO) ---
@router.post("/{lab_id}/items/{item_id}/maintenance")
async def add_maintenance(lab_id: str, item_id: str, maintenance: Dict = Body(...)):
    # maintenance viene como { "date": "...", "description": "..." }
    maintenance["id"] = str(uuid.uuid4())
    
    result = await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(lab_id), "items.id": item_id},
        {"$push": {"items.$.maintenance_history": maintenance}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se pudo agregar mantenimiento")
    return {"message": "Mantenimiento registrado"}


# DELETE

@router.delete("/{lab_id}/items/{item_id}")
async def delete_item_from_lab(lab_id: str, item_id: str):
    """Elimina una máquina específica de un laboratorio"""
    if not ObjectId.is_valid(lab_id):
        raise HTTPException(status_code=400, detail="ID de laboratorio inválido")

    # Usamos $pull para sacar el item del array basado en su 'id' interno
    result = await mongo_db["laboratories"].update_one(
        {"_id": ObjectId(lab_id)},
        {"$pull": {"items": {"id": item_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Máquina no encontrada o Laboratorio no existe")

    return {"message": "Máquina eliminada correctamente"}