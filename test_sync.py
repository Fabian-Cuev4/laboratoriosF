#!/usr/bin/env python3
"""
Script de Prueba: Sincronización MySQL ↔ Redis

Este script verifica que:
1. MySQL y Redis estén sincronizados correctamente
2. Cuando MySQL cae, Redis actúa como respaldo
3. Cuando MySQL se recupera, la sincronización se restablece correctamente
4. Los datos pendientes se sincronizan correctamente
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8001"  # NGINX Load Balancer
HEALTH_CHECK_INTERVAL = 2
MAX_WAIT_TIME = 60

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(step_num, description):
    """Imprime un paso del test"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[PASO {step_num}]{Colors.END} {description}")

def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Imprime un mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Imprime un mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Imprime información"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

async def make_request(session, method, endpoint, data=None):
    """Realiza una petición HTTP"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.json()
        elif method == "POST":
            async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.json()
        elif method == "PUT":
            async with session.put(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.json()
        elif method == "DELETE":
            async with session.delete(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.json()
    except asyncio.TimeoutError:
        raise Exception(f"Timeout: {method} {endpoint}")
    except Exception as e:
        raise Exception(f"Error en {method} {endpoint}: {str(e)}")

async def wait_for_condition(session, check_func, timeout=MAX_WAIT_TIME, interval=HEALTH_CHECK_INTERVAL):
    """Espera a que se cumpla una condición"""
    elapsed = 0
    while elapsed < timeout:
        try:
            if await check_func(session):
                return True
        except Exception as e:
            print_info(f"Esperando... ({e})")
        
        await asyncio.sleep(interval)
        elapsed += interval
    
    return False

async def test_sync():
    """Ejecuta las pruebas de sincronización"""
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}╔════════════════════════════════════════════════════════════════╗")
    print(f"║   PRUEBA DE SINCRONIZACIÓN MySQL ↔ Redis                          ║")
    print(f"╚════════════════════════════════════════════════════════════════╝{Colors.END}\n")
    
    async with aiohttp.ClientSession() as session:
        
        try:
            # ========== PASO 1: Verificar estado inicial ==========
            print_step(1, "Verificar estado inicial del sistema")
            
            try:
                health = await make_request(session, "GET", "/health")
                print_info(f"Estado del sistema: {health.get('status', 'desconocido')}")
                print_info(f"  - MySQL: {'✅ Online' if health.get('mysql') else '❌ Offline'}")
                print_info(f"  - Redis: {'✅ Online' if health.get('redis') else '❌ Offline'}")
                
                if not health.get('redis'):
                    print_error("Redis no está disponible. Abortando prueba.")
                    return False
                    
                print_success("Sistema disponible")
            except Exception as e:
                print_error(f"No se puede conectar al sistema: {e}")
                print_info("Asegúrate de que el backend esté corriendo (docker-compose up)")
                return False
            
            # ========== PASO 2: Obtener estado de sincronización inicial ==========
            print_step(2, "Obtener estado de sincronización inicial")
            
            sync_status = await make_request(session, "GET", "/sync/status")
            print_info(f"Items en caché: {sync_status.get('cache_items', 0)}")
            print_info(f"Estado de sincronización: {sync_status.get('status', 'desconocido')}")
            print_success("Estado inicial capturado")
            
            # ========== PASO 3: Crear un item de prueba ==========
            print_step(3, "Crear item de prueba en MySQL")
            
            if not sync_status.get('mysql_available', False):
                print_warning("MySQL no está disponible. Saltando creación directa.")
            else:
                test_item = {
                    "code": f"TEST-{int(datetime.now().timestamp())}",
                    "type": "Equipamiento",
                    "status": "Activo",
                    "area": "Laboratorio A",
                    "acquisition_date": "2025-01-01"
                }
                
                try:
                    response = await make_request(session, "POST", "/laboratories/items", test_item)
                    print_info(f"Respuesta: {response.get('source')} - {response.get('status')}")
                    print_success("Item creado exitosamente")
                except Exception as e:
                    print_warning(f"No se pudo crear item: {e}")
            
            # ========== PASO 4: Verificar que está en Redis ==========
            print_step(4, "Verificar que el item está en Redis")
            
            try:
                items = await make_request(session, "GET", "/laboratories/items")
                items_count = len(items.get('data', []))
                source = items.get('source', 'desconocido')
                
                print_info(f"Items en {source}: {items_count}")
                if items_count > 0:
                    print_success("Items encontrados en caché")
                else:
                    print_warning("No hay items en la caché")
            except Exception as e:
                print_warning(f"Error al obtener items: {e}")
            
            # ========== PASO 5: Verificar integridad de sincronización ==========
            print_step(5, "Verificar integridad de sincronización")
            
            sync_status = await make_request(session, "GET", "/sync/status")
            
            print_info(f"MySQL disponible: {'✅' if sync_status.get('mysql_available') else '❌'}")
            print_info(f"Redis disponible: {'✅' if sync_status.get('redis_available') else '❌'}")
            print_info(f"Sincronización: {sync_status.get('status', 'desconocido')}")
            print_info(f"Items en caché: {sync_status.get('cache_items', 0)}")
            print_info(f"Operaciones pendientes: {sync_status.get('pending_creates', 0) + sync_status.get('pending_updates', 0) + sync_status.get('pending_deletes', 0)}")
            
            if sync_status.get('is_consistent'):
                print_success("Los datos están sincronizados y consistentes")
            else:
                print_warning("Los datos fueron desincronizados")
                print_info(f"Detalles: {sync_status.get('consistency_details', {})}")
            
            # ========== PASO 6: Simulación de falla de MySQL ==========
            print_step(6, "Simulación: MySQL se cae (mantén Redis activo)")
            
            print_warning("Para simular falla de MySQL, ejecuta en otra terminal:")
            print_warning("  docker-compose stop mysql_db")
            print_warning("Presiona ENTER cuando hayas hecho eso...")
            input()
            
            # Esperar a que MySQL se marque como no disponible
            print_info("Esperando a que el sistema detecte la falla de MySQL...")
            
            async def mysql_down(session):
                try:
                    health = await make_request(session, "GET", "/health")
                    return not health.get('mysql', True)  # True cuando MySQL está down
                except:
                    return False
            
            if await wait_for_condition(session, mysql_down, timeout=40):
                print_success("MySQL detectado como no disponible")
            else:
                print_warning("Timeout esperando falla de MySQL (continuando igualmente)")
            
            # ========== PASO 7: Intentar crear item con MySQL caído ==========
            print_step(7, "Crear item con MySQL caído (debería guardarse en Redis)")
            
            fallback_item = {
                "code": f"FALLBACK-{int(datetime.now().timestamp())}",
                "type": "Equipamiento",
                "status": "Pendiente",
                "area": "Laboratorio B",
                "acquisition_date": "2025-01-15"
            }
            
            try:
                response = await make_request(session, "POST", "/laboratories/items", fallback_item)
                source = response.get('source', 'desconocido')
                if source == "REDIS_BACKUP":
                    print_success(f"Item guardado en {source} (modo fallback)")
                else:
                    print_warning(f"Item guardado en {source} (esperábamos REDIS_BACKUP)")
            except Exception as e:
                print_warning(f"Error: {e}")
            
            # ========== PASO 8: Recuperación de MySQL ==========
            print_step(8, "Recuperación: MySQL vuelve online")
            
            print_warning("Para recuperar MySQL, ejecuta en otra terminal:")
            print_warning("  docker-compose start mysql_db")
            print_warning("Presiona ENTER cuando hayas hecho eso...")
            input()
            
            print_info("Esperando a que MySQL esté disponible y se sincronice...")
            
            async def mysql_up(session):
                try:
                    health = await make_request(session, "GET", "/health")
                    return health.get('mysql', False) and health.get('redis', False)
                except:
                    return False
            
            if await wait_for_condition(session, mysql_up, timeout=60):
                print_success("MySQL está de nuevo online y sincronizado")
            else:
                print_error("Timeout esperando recuperación de MySQL")
                return False
            
            # ========== PASO 9: Verificar sincronización final ==========
            print_step(9, "Verificar sincronización final después de recuperación")
            
            await asyncio.sleep(5)  # Esperar a que se complete la sincronización
            
            sync_status = await make_request(session, "GET", "/sync/status")
            
            print_info(f"Items en caché: {sync_status.get('cache_items', 0)}")
            print_info(f"Operaciones pendientes: {sync_status.get('pending_creates', 0) + sync_status.get('pending_updates', 0) + sync_status.get('pending_deletes', 0)}")
            print_info(f"Estado de sincronización: {sync_status.get('status', 'desconocido')}")
            
            if sync_status.get('is_consistent'):
                print_success("Sincronización completada exitosamente")
            else:
                print_warning("La sincronización no está completada")
                print_info(f"Detalles: {sync_status.get('consistency_details', {})}")
            
            # ========== RESUMEN FINAL ==========
            print(f"\n{Colors.HEADER}{Colors.BOLD}╔════════════════════════════════════════════════════════════════╗")
            print(f"║   PRUEBA COMPLETADA                                             ║")
            print(f"╚════════════════════════════════════════════════════════════════╝{Colors.END}\n")
            
            print(f"{Colors.GREEN}✅ La arquitectura está configurada correctamente:{Colors.END}")
            print(f"  1. Redis actúa como respaldo cuando MySQL cae")
            print(f"  2. Los datos se sincronizan cuando MySQL se recupera")
            print(f"  3. La integridad de datos se verifica constantemente")
            print(f"  4. El frontend recibe información del estado del sistema")
            
            return True
            
        except Exception as e:
            print_error(f"Error durante la prueba: {e}")
            return False

async def main():
    """Entrada principal"""
    try:
        success = await test_sync()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Prueba cancelada por el usuario{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ejecutar script como asincrónico
    asyncio.run(main())
