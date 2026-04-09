# 🚀 Despliegue en Railway - Sistema Completo

## Pre-requisitos

✅ App funciona en local con todos los tests pasando
✅ `requirements.txt` actualizado con APScheduler
✅ Git configurado en la carpeta

---

## Paso 1: Actualizar requirements.txt en Git

```bash
cd c:\Users\admin\Desktop\cine_app

# Verificar que APScheduler está en requirements.txt
cat requirements.txt | findstr APScheduler

# Debe mostrar: APScheduler==3.10.4
```

Si no está, agregar:
```bash
echo "APScheduler==3.10.4" >> requirements.txt
```

---

## Paso 2: Commit y Push a GitHub

```bash
# Agregar todos los cambios
git add -A

# Commit con mensaje descriptivo
git commit -m "feat: Sistema de validacion tickets 25min + scheduler

- Validacion de tickets con ventana de 25 minutos
- Estados automaticos de funciones (programada -> en_curso -> finalizada)
- Historial de funciones con estadisticas
- Scheduler con APScheduler ejecutando tareas automaticas
- Reportes de ingresos y ocupacion
- Nuevos modelos: historial.py y scheduler.py"

# Push a main/master
git push origin main
# o si es en branch diferente:
# git push origin tu-rama
```

---

## Paso 3: Actualizar Railway.toml

El archivo actual debe verse así:

```toml
[build]
builder = "nixpacks"

[env]
FLASK_ENV = "production"
```

Puede dejarse así. Railway detectará `Procfile` y `requirements.txt` automáticamente.

---

## Paso 4: Verificar Procfile

```bash
cat Procfile
```

Debe contener:
```
web: gunicorn -b 0.0.0.0:$PORT wsgi:app
```

---

## Paso 5: Desplegar en Railway

### Opción A: Usando Railway CLI
```bash
# Instalar Railway CLI (si no lo tienes)
npm install -g @railway/cli

# O con Chocolatey en Windows:
choco install railway

# Loguear
railway login

# Desplegar (desde carpeta del proyecto)
railway up
```

### Opción B: Conectar GitHub a Railway

1. Ir a: https://railway.app
2. Login con GitHub
3. New Project → GitHub Repo
4. Seleccionar `cine_app`
5. Railway auto-detecta y despliega

### Opción C: Dashboard de Railway

1. Ir a proyecto existente en Railway
2. Settings → Redeploy
3. O: Disconnect GitHub → Reconectar

---

## Paso 6: Variables de Entorno en Railway

En el dashboard de Railway, agregar variables:

```
DB_HOST = tu_host_mysql
DB_PORT = 3306
DB_USER = tu_usuario
DB_PASSWORD = tu_password
DB_NAME = cinema_caribe
FLASK_ENV = production
PORT = 8000
```

---

## Paso 7: Inicializar BD en Railway

Una vez deployed, ejecutar en navegador:

```
https://tu-app.railway.app/initialize
```

Debe retornar:
```json
{
  "status": "success",
  "database": "cinema_caribe",
  "executed": 180,
  "skipped": 0,
  "errors": 0
}
```

---

## Paso 8: Verificar Scheduler en Producción

El scheduler debe iniciar automáticamente cuando arranca la app.

Para verificar logs en Railway:

```bash
railway logs -f  # Follow logs en tiempo real
```

Buscar mensajes como:
```
✓ Scheduler inicializado correctamente
[...] Los tickets habilitados
[...] Estados actualizados
[...] Funciones archivadas
```

---

## Paso 9: Pruebas en Producción

### Test 1: Crear Función y Ticket

```bash
curl -X POST https://tu-app.railway.app/tiquetes/comprar \
  -H "Cookie: session=..." \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "funcion_id=1&asiento_ids[]=1&asiento_ids[]=2"
```

### Test 2: Validar Ticket

```bash
curl https://tu-app.railway.app/tiquetes/validar \
  -X POST \
  -d "codigo=ABC123DEF456&accion=consultar"
```

Respuesta esperada:
```json
{
  "valid": false,
  "status": "temprano",
  "mensaje": "El ticket se habilitará en X minutos."
}
```

### Test 3: Ver Historial

```bash
curl -H "Cookie: session=..." \
  https://tu-app.railway.app/admin/funciones/historial
```

### Test 4: Ver Reportes

```bash
curl -H "Cookie: session=..." \
  'https://tu-app.railway.app/admin/funciones/historial/reporte?fecha_desde=2026-04-01&fecha_hasta=2026-04-30'
```

---

## Paso 10: Monitorear en Producción

### Usar Railway CLI para monitorear

```bash
# Ver logs en tiempo real
railway logs -f

# Filtrar por palabra clave
railway logs -f | findstr "Scheduler"
```

### Verificar salud de la app

```bash
curl https://tu-app.railway.app/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "version": "1.0"
}
```

---

## Paso 11: Configurar Monitoreo Automático

### Usando Railway Alerts (Opcional)

1. Ir a: Railway Dashboard → Project Settings
2. Deployments → Add Alert
3. Configurar:
   - Error Rate > 5%
   - CPU > 80%
   - Memory > 80%

### Usando Healthchecks.io (Gratuito)

1. Ir a: https://healthchecks.io
2. Crear new check
3. Usar endpoint `/health` de tu app

---

## 🔍 Troubleshooting en Railway

### El scheduler no se ejecuta

**Solución:**
```bash
# Verificar logs
railway logs -f | findstr "Scheduler"

# Si no aparece, verificar import en app.py:
# from scheduler import init_scheduler
# init_scheduler(app)

# Reinstalar APScheduler
railway run pip install --upgrade APScheduler==3.10.4
```

### Tickets no se habilitan

**Verificar:**
```sql
-- En tu BD en Railway
SELECT COUNT(*) FROM tiquetes WHERE estado='inhabilitado';
SELECT COUNT(*) FROM tiquetes WHERE estado='valido';

-- Si están sin cambiar en 5+ minutos:
-- El scheduler no está ejecutando
```

**Solución:**
```bash
# Forzar redeploy
railway redeploy

# O recrear desde 0:
railway down
railway up
```

### Funciones no se archivan

**Esperar a que:**
- Función llegue a estado `finalizada`
- Pasen 1 hora desde fin
- Scheduler ejecute mover_finalizadas_a_historial

**Forzar manualmente:**
```bash
# Conectar a app en Railway
railway shell

# Entrar a Python
python

# Ejecutar:
from models.funcion import Funcion
Funcion.mover_finalizadas_a_historial()
```

---

## 📦 Resumen de Archivos a Desplegar

Git DEBE incluir:
```
cine_app/
├── app.py ✅ (Actualizado con scheduler)
├── scheduler.py ✅ (NUEVO)
├── requirements.txt ✅ (APScheduler agregado)
├── database.sql ✅ (Nuevas tablas)
├── Procfile ✅ (gunicorn)
├── railway.toml ✅
├── models/
│   ├── tiquete.py ✅ (Actualizado)
│   ├── funcion.py ✅ (Actualizado)
│   └── historial.py ✅ (NUEVO)
├── routes/
│   ├── tiquetes.py ✅ (Actualizado)
│   └── admin.py ✅ (Actualizado)
├── IMPLEMENTACION.md ✅ (Documentación)
├── INSTALACION_TESTING.md ✅ (Testing)
├── FLUJOS_DIAGRAMAS.md ✅ (Diagramas)
└── DESPLIEGUE_RAILWAY.md ✅ (Este archivo)
```

---

## 🎯 Verificación Final

Después del despliegue, verificar:

```bash
# 1. App está corriendo
curl https://tu-app.railway.app/health
# Response: {"status": "ok"}

# 2. BD está disponible
curl https://tu-app.railway.app/check-creds
# Response: {"status": "ok", "users_count": 1+}

# 3. Scheduler está activo
railway logs -f | grep -i scheduler
# Debe mostrar: "✓ Scheduler inicializado"

# 4. Tabla historial existe
railway run mysql -e "SHOW TABLES FROM cinema_caribe" | grep historial
# Debe mostrar: historial_funciones

# 5. Tareas scheduler se ejecutan
railway logs -f | grep -i "habilitados\|actualizados\|archivadas"
# Esperar 2+ minutos
```

---

## 📊 Monitoreo Continuo

Después de deploying, monitorear:

1. **Logs cada 1 hora:**
   ```bash
   railway logs -f | head -100
   ```

2. **BD crece correctamente:**
   ```bash
   railway run mysql -e "SELECT COUNT(*) FROM historial_funciones;"
   ```

3. **No hay errores:**
   ```bash
   railway logs -f | grep -i "error\|exception" 
   ```

---

## 🆘 Soporte

Si hay problemas:

1. Revisar: `railway logs -f`
2. Verificar: `railway env`
3. Reinstalar: `railway run pip install -r requirements.txt`
4. Rebuild: `railway redeploy`

O contactar a soporte de Railway: https://railway.app/support

---

**¡Tu app está lista en Railway!** 🚀
