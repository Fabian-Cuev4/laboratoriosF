# ⚡ GUÍA RÁPIDA: Verifica todo en 5 minutos

## 🚀 Paso 1: Iniciar (30 segundos)
```bash
cd c:\Users\Fabian\Desktop\arquitectura\laboratorios
docker-compose up -d
docker-compose ps
```

✅ Espera a que todos estén en `healthy` o `running`

---

## 🧪 Paso 2: Ejecutar Script de Verificación (2 minutos)
```bash
.\verify_system.ps1
```

Este script verifica TODO automáticamente:
- ✅ Docker (7 contenedores)
- ✅ API endpoints
- ✅ Login/Register
- ✅ Bases de datos
- ✅ CORS headers

**Resultado esperado:** ✅ Todos los tests pasan

---

## 🌐 Paso 3: Accede a Todo (2 minutos)

| Servicio | URL | Función |
|----------|-----|---------|
| **Frontend** | http://localhost:5173 | Aplicación |
| **Adminer** | http://localhost:8080 | Ver MySQL |
| **Redis Insight** | http://localhost:5540 | Ver Redis |
| **API** | http://localhost:8001 | Backend |

---

## ✅ Paso 4: Test Manual (1 minuto)

### A. Frontend - Register
1. Abre http://localhost:5173
2. Click en "¿No tienes cuenta? Regístrate"
3. Completa:
   - Usuario: `testuser`
   - Email: `test@example.com`
   - Contraseña: `Test123!`
4. Click "Registrarse"
5. ✅ Debería mostrar: "¡Cuenta creada exitosamente!"

### B. Frontend - Login
1. Completa con datos del paso anterior
2. Click "Ingresar al Sistema"
3. ✅ Debería redirigir a `/dashboard`

### C. Adminer - Verificar
1. Abre http://localhost:8080
2. Credenciales:
   - Server: `mysql_db`
   - Usuario: `user`
   - Contraseña: `password`
   - BD: `lab_usuarios`
3. Click en tabla `user`
4. ✅ Deberías ver tu usuario registrado

---

## 📊 Resultado Final

Si pasaste todos los pasos:

✅ **Frontend-Backend Communication:** FUNCIONA  
✅ **Login/Register:** FUNCIONA  
✅ **MySQL:** FUNCIONA (visible en Adminer)  
✅ **Redis:** FUNCIONA (sincronizado)  
✅ **CORS:** FUNCIONA (sin errores de red)  

**¡TODO ESTÁ LISTO PARA PRODUCCIÓN! 🚀**

---

## 🔧 Si Algo Falla

### "Network Error"
```bash
docker-compose restart nginx
```

### "Usuario no encontrado"
Primero haz Register (paso 4A)

### "Contenedor no está healthy"
```bash
docker-compose logs backend -f
# O
docker-compose restart
```

---

## 📚 Para Más Detalles

Ver documentación completa:
- `LOGIN_ADMINER_GUIDE.md` - Guía detallada
- `VERIFICATION_COMPLETE.md` - Verificación completa
- `SYNC_VERIFICATION.md` - Sincronización MySQL ↔ Redis

---

**⏱️ Tiempo total: ~5 minutos**  
**✅ Complejidad: Muy Fácil**
