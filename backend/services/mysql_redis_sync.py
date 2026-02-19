"""
Servicio de sincronización bidireccional MySQL ↔ Redis.
- MySQL es la fuente de verdad cuando está disponible.
- Redis actúa como caché/espejo y respaldo cuando MySQL está caído.
- Al recuperarse MySQL, se vacía el backlog de Redis hacia MySQL y se refresca Redis.

MEJORAS IMPLEMENTADAS:
✅ Validación de hash para detectar desincronizaciones
✅ Reconstrucción de caché desde MySQL
✅ Verificación de integridad de datos
✅ Métricas de sincronización
"""

import json
import asyncio
import uuid
import hashlib
from typing import List, Dict, Any, Tuple
from sqlalchemy import text

from backend.database import redis_client, mysql_engine, SessionLocal
from backend.models.inventory import ItemModel

# Claves Redis
REDIS_ITEMS_CACHE = "items:cache"         # Lista JSON de todos los items (espejo de MySQL)
REDIS_ITEMS_HASH = "items:cache:hash"     # Hash SHA256 de la caché para verificación
REDIS_PENDING_ITEMS = "items:pending"     # Items creados cuando MySQL estaba caído
REDIS_PENDING_UPDATES = "items:pending_updates"  # Updates pendientes: [{id, data}]
REDIS_PENDING_DELETES = "items:pending_deletes"  # IDs eliminados pendientes de aplicar a MySQL
REDIS_SYNC_METADATA = "sync:metadata"     # Metadatos de sincronización


def _item_to_dict(item: ItemModel) -> Dict[str, Any]:
    """Convierte ItemModel a diccionario serializable."""
    return {
        "id": item.id,
        "code": item.code,
        "type": item.type,
        "status": item.status,
        "area": item.area,
        "acquisition_date": getattr(item, "acquisition_date", "") or "",
    }


def _compute_hash(data: List[Dict[str, Any]]) -> str:
    """Calcula un hash SHA256 de los datos para verificar integridad."""
    try:
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    except Exception as e:
        print(f"⚠️ Error calculando hash: {e}")
        return ""


def _check_mysql_sync() -> bool:
    """Verificación síncrona de MySQL."""
    try:
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_mysql_available() -> bool:
    """Verifica si MySQL está disponible."""
    return await asyncio.to_thread(_check_mysql_sync)


async def check_redis_available() -> bool:
    """Verifica si Redis está disponible."""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False


def _fetch_all_items_sync() -> List[Dict[str, Any]]:
    """Obtiene todos los items de MySQL (síncrono)."""
    db = SessionLocal()
    try:
        items = db.query(ItemModel).all()
        return [_item_to_dict(i) for i in items]
    finally:
        db.close()


async def sync_mysql_to_redis() -> int:
    """
    Sincroniza todos los items de MySQL hacia Redis (refresca la caché).
    Devuelve el número de items sincronizados.
    """
    try:
        data = await asyncio.to_thread(_fetch_all_items_sync)
        await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
        # Guardar hash para verificación futura
        data_hash = _compute_hash(data)
        await redis_client.set(REDIS_ITEMS_HASH, data_hash)
        return len(data)
    except Exception as e:
        print(f"⚠️ [SYNC] Error MySQL→Redis: {e}")
        return 0


async def verify_cache_integrity() -> Tuple[bool, Dict[str, Any]]:
    """
    Verifica que la caché de Redis sea intacta comparando su hash.
    Devuelve (is_valid, metadata)
    """
    try:
        raw_cache = await redis_client.get(REDIS_ITEMS_CACHE)
        stored_hash = await redis_client.get(REDIS_ITEMS_HASH)
        
        if not raw_cache or not stored_hash:
            return False, {"reason": "Missing cache or hash"}
        
        data = json.loads(raw_cache)
        computed_hash = _compute_hash(data)
        
        is_valid = computed_hash == stored_hash
        metadata = {
            "is_valid": is_valid,
            "items_count": len(data),
            "hash_match": is_valid
        }
        return is_valid, metadata
    except Exception as e:
        print(f"⚠️ Error verificando integridad: {e}")
        return False, {"error": str(e)}


async def rebuild_cache_from_mysql() -> Dict[str, Any]:
    """
    Reconstruye completamente la caché de Redis desde MySQL.
    Esto se usa cuando Redis está vacío o corrupto.
    """
    try:
        print("🔄 [REBUILD] Reconstruyendo caché desde MySQL...")
        count = await sync_mysql_to_redis()
        metadata = {
            "action": "rebuild_from_mysql",
            "items_synced": count,
            "timestamp": await redis_client.time()
        }
        await redis_client.set(REDIS_SYNC_METADATA, json.dumps(metadata))
        print(f"✅ [REBUILD] Caché reconstruida: {count} items")
        return metadata
    except Exception as e:
        print(f"❌ [REBUILD] Error: {e}")
        return {"error": str(e)}


def _insert_pending_item_sync(item_data: Dict[str, Any]) -> None:
    """Inserta un item pendiente en MySQL (síncrono)."""
    item_data = {k: v for k, v in item_data.items() if k != "id"}
    db = SessionLocal()
    try:
        new_item = ItemModel(**item_data)
        db.add(new_item)
        db.commit()
    finally:
        db.close()


async def sync_redis_pending_to_mysql() -> int:
    """
    Vacía los items pendientes de Redis (creados cuando MySQL estaba caído)
    y los inserta en MySQL. Devuelve cuántos se insertaron.
    """
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_ITEMS)
            if not raw:
                break
            item_data = json.loads(raw)
            await asyncio.to_thread(_insert_pending_item_sync, item_data)
            count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error Redis→MySQL (pending): {e}")
        return count


def _update_item_sync(item_id: int, item_data: Dict[str, Any]) -> bool:
    """Actualiza un item en MySQL (síncrono)."""
    db = SessionLocal()
    try:
        item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not item:
            return False
        for k, v in item_data.items():
            if hasattr(item, k) and k != "id":
                setattr(item, k, v)
        db.commit()
        return True
    finally:
        db.close()


async def sync_pending_updates_to_mysql() -> int:
    """Aplica las actualizaciones pendientes a MySQL."""
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_UPDATES)
            if not raw:
                break
            op = json.loads(raw)
            item_id = op.get("id")
            data = op.get("data", {})
            if item_id is not None and isinstance(item_id, int):
                ok = await asyncio.to_thread(_update_item_sync, item_id, data)
                if ok:
                    count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error aplicando updates: {e}")
        return count


def _delete_item_sync(item_id: int) -> bool:
    """Elimina un item en MySQL (síncrono)."""
    db = SessionLocal()
    try:
        item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


async def sync_pending_deletes_to_mysql() -> int:
    """Aplica las eliminaciones pendientes a MySQL."""
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_DELETES)
            if not raw:
                break
            try:
                item_id = int(json.loads(raw))
            except (ValueError, json.JSONDecodeError):
                continue
            if await asyncio.to_thread(_delete_item_sync, item_id):
                count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error aplicando deletes: {e}")
        return count


async def add_pending_update(item_id: int, data: Dict[str, Any]) -> None:
    """Encola una actualización pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_UPDATES, json.dumps({"id": item_id, "data": data}))


async def add_pending_delete(item_id: int) -> None:
    """Encola una eliminación pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_DELETES, json.dumps(item_id))


async def full_sync_on_mysql_recovery() -> Dict[str, int]:
    """
    Ejecuta sincronización completa cuando MySQL vuelve a estar disponible:
    1. Aplica deletes pendientes
    2. Aplica updates pendientes
    3. Inserta creates pendientes
    4. Refresca Redis desde MySQL
    5. Verifica integridad
    """
    result = {
        "deletes_synced": 0,
        "updates_synced": 0,
        "creates_synced": 0,
        "cache_refreshed": 0,
        "integrity_verified": False,
    }
    result["deletes_synced"] = await sync_pending_deletes_to_mysql()
    result["updates_synced"] = await sync_pending_updates_to_mysql()
    result["creates_synced"] = await sync_redis_pending_to_mysql()
    result["cache_refreshed"] = await sync_mysql_to_redis()
    
    # Verificar integridad
    is_valid, metadata = await verify_cache_integrity()
    result["integrity_verified"] = is_valid
    
    return result


async def get_items_from_redis() -> List[Dict[str, Any]]:
    """Obtiene todos los items desde la caché de Redis."""
    try:
        raw = await redis_client.get(REDIS_ITEMS_CACHE)
        if not raw:
            return []
        return json.loads(raw)
    except Exception:
        return []


async def get_items_from_redis_fallback() -> List[Dict[str, Any]]:
    """
    Obtiene items para modo fallback (MySQL caído): caché + pendientes.
    Los pendientes son los creados mientras MySQL estaba caído.
    """
    cache_items = await get_items_from_redis()
    pending_raw = await redis_client.lrange(REDIS_PENDING_ITEMS, 0, -1)
    pending_items = []
    for raw in reversed(pending_raw):  # Orden FIFO
        try:
            pending_items.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return cache_items + pending_items


async def add_item_to_redis_cache(item: Dict[str, Any]) -> None:
    """Agrega un item al caché de Redis (cuando se escribe en MySQL)."""
    try:
        data = await get_items_from_redis()
        # Evitar duplicados por id
        data = [d for d in data if d.get("id") != item.get("id")]
        data.append(item)
        await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
        # Actualizar hash
        data_hash = _compute_hash(data)
        await redis_client.set(REDIS_ITEMS_HASH, data_hash)
    except Exception as e:
        print(f"⚠️ [SYNC] Error actualizando caché Redis: {e}")


async def add_item_to_redis_pending(item: Dict[str, Any]) -> None:
    """Agrega un item a la cola pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_ITEMS, json.dumps(item))


async def add_item_to_redis_pending_and_cache(item: Dict[str, Any]) -> None:
    """
    Agrega un item a pending (para sync futura) y al caché (para lecturas).
    Usa un id temporal para el caché ya que MySQL no lo generó.
    """
    temp_id = f"pending_{uuid.uuid4().hex[:8]}"
    item_with_id = {**item, "id": temp_id}
    await redis_client.lpush(REDIS_PENDING_ITEMS, json.dumps(item))
    await add_item_to_redis_cache(item_with_id)


async def update_item_in_redis_cache(item_id: int, item: Dict[str, Any]) -> bool:
    """Actualiza un item en el caché de Redis. Devuelve True si se encontró y actualizó."""
    try:
        data = await get_items_from_redis()
        found = False
        for i, d in enumerate(data):
            if d.get("id") == item_id:
                data[i] = {**d, **item, "id": item_id}
                found = True
                break
        if found:
            await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
            # Actualizar hash
            data_hash = _compute_hash(data)
            await redis_client.set(REDIS_ITEMS_HASH, data_hash)
        return found
    except Exception as e:
        print(f"⚠️ [SYNC] Error actualizando item en Redis: {e}")
        return False


async def delete_item_from_redis_cache(item_id: int) -> bool:
    """Elimina un item del caché de Redis. Devuelve True si se encontró."""
    try:
        data = await get_items_from_redis()
        original_len = len(data)
        data = [d for d in data if d.get("id") != item_id]
        if len(data) < original_len:
            await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
            # Actualizar hash
            data_hash = _compute_hash(data)
            await redis_client.set(REDIS_ITEMS_HASH, data_hash)
            return True
        return False
    except Exception as e:
        print(f"⚠️ [SYNC] Error eliminando item de Redis: {e}")
        return False


# Compatibilidad con la clave legacy backup_items
async def migrate_backup_items_to_pending() -> int:
    """Migra datos de backup_items (legacy) a items:pending para sincronizar."""
    count = 0
    try:
        backup_raw = await redis_client.lrange("backup_items", 0, -1)
        for raw in backup_raw:
            await redis_client.lpush(REDIS_PENDING_ITEMS, raw)
            count += 1
        if count > 0:
            await redis_client.delete("backup_items")
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error migrando backup_items: {e}")
        return 0


async def get_sync_status() -> Dict[str, Any]:
    """Devuelve el estado actual de la sincronización."""
    try:
        mysql_available = await check_mysql_available()
        redis_available = await check_redis_available()
        cache_items_count = len(await get_items_from_redis())
        pending_items_count = await redis_client.llen(REDIS_PENDING_ITEMS)
        pending_updates_count = await redis_client.llen(REDIS_PENDING_UPDATES)
        pending_deletes_count = await redis_client.llen(REDIS_PENDING_DELETES)
        is_consistent, consistency_details = await verify_cache_integrity()
        
        return {
            "mysql_available": mysql_available,
            "redis_available": redis_available,
            "cache_items": cache_items_count,
            "pending_creates": pending_items_count,
            "pending_updates": pending_updates_count,
            "pending_deletes": pending_deletes_count,
            "is_consistent": is_consistent,
            "consistency_details": consistency_details,
            "status": "synced" if is_consistent else "out_of_sync"
        }
    except Exception as e:
        print(f"⚠️ Error obteniendo estado de sincronización: {e}")
        return {"error": str(e)}



def _item_to_dict(item: ItemModel) -> Dict[str, Any]:
    """Convierte ItemModel a diccionario serializable."""
    return {
        "id": item.id,
        "code": item.code,
        "type": item.type,
        "status": item.status,
        "area": item.area,
        "acquisition_date": getattr(item, "acquisition_date", "") or "",
    }


def _check_mysql_sync() -> bool:
    """Verificación síncrona de MySQL."""
    try:
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_mysql_available() -> bool:
    """Verifica si MySQL está disponible."""
    return await asyncio.to_thread(_check_mysql_sync)


def _fetch_all_items_sync() -> List[Dict[str, Any]]:
    """Obtiene todos los items de MySQL (síncrono)."""
    db = SessionLocal()
    try:
        items = db.query(ItemModel).all()
        return [_item_to_dict(i) for i in items]
    finally:
        db.close()


async def sync_mysql_to_redis() -> int:
    """
    Sincroniza todos los items de MySQL hacia Redis (refresca la caché).
    Devuelve el número de items sincronizados.
    """
    try:
        data = await asyncio.to_thread(_fetch_all_items_sync)
        await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
        return len(data)
    except Exception as e:
        print(f"⚠️ [SYNC] Error MySQL→Redis: {e}")
        return 0


def _insert_pending_item_sync(item_data: Dict[str, Any]) -> None:
    """Inserta un item pendiente en MySQL (síncrono)."""
    item_data = {k: v for k, v in item_data.items() if k != "id"}
    db = SessionLocal()
    try:
        new_item = ItemModel(**item_data)
        db.add(new_item)
        db.commit()
    finally:
        db.close()


async def sync_redis_pending_to_mysql() -> int:
    """
    Vacía los items pendientes de Redis (creados cuando MySQL estaba caído)
    y los inserta en MySQL. Devuelve cuántos se insertaron.
    """
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_ITEMS)
            if not raw:
                break
            item_data = json.loads(raw)
            await asyncio.to_thread(_insert_pending_item_sync, item_data)
            count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error Redis→MySQL (pending): {e}")
        return count


def _update_item_sync(item_id: int, item_data: Dict[str, Any]) -> bool:
    """Actualiza un item en MySQL (síncrono)."""
    db = SessionLocal()
    try:
        item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not item:
            return False
        for k, v in item_data.items():
            if hasattr(item, k) and k != "id":
                setattr(item, k, v)
        db.commit()
        return True
    finally:
        db.close()


async def sync_pending_updates_to_mysql() -> int:
    """Aplica las actualizaciones pendientes a MySQL."""
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_UPDATES)
            if not raw:
                break
            op = json.loads(raw)
            item_id = op.get("id")
            data = op.get("data", {})
            if item_id is not None and isinstance(item_id, int):
                ok = await asyncio.to_thread(_update_item_sync, item_id, data)
                if ok:
                    count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error aplicando updates: {e}")
        return count


def _delete_item_sync(item_id: int) -> bool:
    """Elimina un item en MySQL (síncrono)."""
    db = SessionLocal()
    try:
        item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


async def sync_pending_deletes_to_mysql() -> int:
    """Aplica las eliminaciones pendientes a MySQL."""
    count = 0
    try:
        while True:
            raw = await redis_client.rpop(REDIS_PENDING_DELETES)
            if not raw:
                break
            try:
                item_id = int(json.loads(raw))
            except (ValueError, json.JSONDecodeError):
                continue
            if await asyncio.to_thread(_delete_item_sync, item_id):
                count += 1
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error aplicando deletes: {e}")
        return count


async def add_pending_update(item_id: int, data: Dict[str, Any]) -> None:
    """Encola una actualización pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_UPDATES, json.dumps({"id": item_id, "data": data}))


async def add_pending_delete(item_id: int) -> None:
    """Encola una eliminación pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_DELETES, json.dumps(item_id))


async def full_sync_on_mysql_recovery() -> Dict[str, int]:
    """
    Ejecuta sincronización completa cuando MySQL vuelve a estar disponible:
    1. Aplica deletes pendientes
    2. Aplica updates pendientes
    3. Inserta creates pendientes
    4. Refresca Redis desde MySQL
    """
    result = {
        "deletes_synced": 0,
        "updates_synced": 0,
        "creates_synced": 0,
        "cache_refreshed": 0,
    }
    result["deletes_synced"] = await sync_pending_deletes_to_mysql()
    result["updates_synced"] = await sync_pending_updates_to_mysql()
    result["creates_synced"] = await sync_redis_pending_to_mysql()
    result["cache_refreshed"] = await sync_mysql_to_redis()
    return result


async def get_items_from_redis() -> List[Dict[str, Any]]:
    """Obtiene todos los items desde la caché de Redis."""
    try:
        raw = await redis_client.get(REDIS_ITEMS_CACHE)
        if not raw:
            return []
        return json.loads(raw)
    except Exception:
        return []


async def get_items_from_redis_fallback() -> List[Dict[str, Any]]:
    """
    Obtiene items para modo fallback (MySQL caído): caché + pendientes.
    Los pendientes son los creados mientras MySQL estaba caído.
    """
    cache_items = await get_items_from_redis()
    pending_raw = await redis_client.lrange(REDIS_PENDING_ITEMS, 0, -1)
    pending_items = []
    for raw in reversed(pending_raw):  # Orden FIFO
        try:
            pending_items.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return cache_items + pending_items


async def add_item_to_redis_cache(item: Dict[str, Any]) -> None:
    """Agrega un item al caché de Redis (cuando se escribe en MySQL)."""
    try:
        data = await get_items_from_redis()
        # Evitar duplicados por id
        data = [d for d in data if d.get("id") != item.get("id")]
        data.append(item)
        await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
    except Exception as e:
        print(f"⚠️ [SYNC] Error actualizando caché Redis: {e}")


async def add_item_to_redis_pending(item: Dict[str, Any]) -> None:
    """Agrega un item a la cola pendiente (cuando MySQL está caído)."""
    await redis_client.lpush(REDIS_PENDING_ITEMS, json.dumps(item))


async def add_item_to_redis_pending_and_cache(item: Dict[str, Any]) -> None:
    """
    Agrega un item a pending (para sync futura) y al caché (para lecturas).
    Usa un id temporal para el caché ya que MySQL no lo generó.
    """
    temp_id = f"pending_{uuid.uuid4().hex[:8]}"
    item_with_id = {**item, "id": temp_id}
    await redis_client.lpush(REDIS_PENDING_ITEMS, json.dumps(item))
    await add_item_to_redis_cache(item_with_id)


async def update_item_in_redis_cache(item_id: int, item: Dict[str, Any]) -> bool:
    """Actualiza un item en el caché de Redis. Devuelve True si se encontró y actualizó."""
    try:
        data = await get_items_from_redis()
        found = False
        for i, d in enumerate(data):
            if d.get("id") == item_id:
                data[i] = {**d, **item, "id": item_id}
                found = True
                break
        if found:
            await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
        return found
    except Exception as e:
        print(f"⚠️ [SYNC] Error actualizando item en Redis: {e}")
        return False


async def delete_item_from_redis_cache(item_id: int) -> bool:
    """Elimina un item del caché de Redis. Devuelve True si se encontró."""
    try:
        data = await get_items_from_redis()
        original_len = len(data)
        data = [d for d in data if d.get("id") != item_id]
        if len(data) < original_len:
            await redis_client.set(REDIS_ITEMS_CACHE, json.dumps(data))
            return True
        return False
    except Exception as e:
        print(f"⚠️ [SYNC] Error eliminando item de Redis: {e}")
        return False


# Compatibilidad con la clave legacy backup_items
async def migrate_backup_items_to_pending() -> int:
    """Migra datos de backup_items (legacy) a items:pending para sincronizar."""
    count = 0
    try:
        backup_raw = await redis_client.lrange("backup_items", 0, -1)
        for raw in backup_raw:
            await redis_client.lpush(REDIS_PENDING_ITEMS, raw)
            count += 1
        if count > 0:
            await redis_client.delete("backup_items")
        return count
    except Exception as e:
        print(f"⚠️ [SYNC] Error migrando backup_items: {e}")
        return 0
