# Implementación: Sistema de Validación de Tickets y Gestión de Funciones

## 📋 Resumen General

Se ha implementado un sistema automático completo que:

1. ✅ **Valida tickets con ventana de 25 minutos** antes del inicio de cada función
2. ✅ **Actualiza estados de funciones automáticamente** (programada → en_curso → finalizada)
3. ✅ **Archiva funciones finalizadas** en un historial con estadísticas completas
4. ✅ **Genera reportes** de rendimiento por película, sala y fechas

---

## 🔧 Cambios Implementados

### 1. Base de Datos (database.sql)

#### Tabla `funciones` - Campos Agregados:
```sql
- created_at: DATETIME - Marca de creación
- updated_at: DATETIME - Marca de actualización automática
- INDEX idx_fecha_hora: Para búsquedas rápidas por horario
- INDEX idx_estado: Para búsquedas por estado
```

#### Tabla `tiquetes` - Cambios:
```sql
- estado: ENUM actualizado a ('inhabilitado','valido','usado','anulado')
  * inhabilitado: Ticket comprado pero aún no habilitado (< 25 min del inicio)
  * valido: Dentro de la ventana válida (25 min antes a inicio de función)
  * usado: Ya fue validado/escaneado
  * anulado: Cancelado manualmente

- fecha_validacion: DATETIME NULL - Registra cuándo se validó
- fue_validado: BOOLEAN - Control de si fue validado
- INDEX idx_codigo: Búsqueda por código QR
- INDEX idx_estado: Búsqueda por estado
- INDEX idx_funcion_id: Búsqueda por función
```

#### Nueva Tabla `historial_funciones`:
```sql
- Guarda funciones finalizadas con estadísticas
- Campos: pelicula_id, sala_id, fecha_original, hora_original, precio,
          cantidad_tiquetes, ingresos_totales, duracion_pelicula,
          fecha_finalizacion, pelicula_titulo, sala_nombre
- Permite reportes históricos de ocupación e ingresos
```

---

### 2. Modelos Python

#### [models/tiquete.py](models/tiquete.py)
**Métodos Nuevos:**

```python
Tiquete.validar_con_ventana_25_min(codigo)
    ↳ Valida ticket con lógica de 25 minutos
    ↳ Retorna: {valid, status, mensaje, tiquete, minutos_para_habilitar}
    ↳ Posibles status: 'temprano', 'valido', 'tarde', 'no_encontrado', 
                        'ya_usado', 'anulado', 'funcion_cancelada'

Tiquete.marcar_validado(codigo)
    ↳ Marca ticket como 'usado' y registra fecha_validacion

Tiquete.habilitar_tickets_ventana()
    ↳ Busca funciones que comienzan en próximos 25 min
    ↳ Cambia tickets de 'inhabilitado' a 'valido'
    ↳ Ejecutada cada 2 minutos por scheduler
```

**Cambios Existentes:**
- Estado inicial de tickets cambiado de 'valido' a 'inhabilitado'
- Método `marcar_anulado()` actualizado para aceptar inhibilitados

#### [models/funcion.py](models/funcion.py)
**Métodos Nuevos:**

```python
Funcion.actualizar_estados_automaticos()
    ↳ Actualiza estados de funciones cada 5 minutos:
       - programada → en_curso (cuando llega la hora)
       - en_curso → finalizada (cuando termina la película)
    ↳ Retorna: (cantidad_en_curso, cantidad_finalizadas)

Funcion.mover_finalizadas_a_historial()
    ↳ Busca funciones finalizadas
    ↳ Copia con estadísticas a tabla historial_funciones
    ↳ Elimina función de tabla activa
    ↳ Ejecutada cada 1 hora por scheduler
```

#### [models/historial.py](models/historial.py) - NUEVO
**Métodos para Reportes:**

```python
HistorialFuncion.listar(pelicula_id, fecha_desde, fecha_hasta, limite)
    ↳ Lista funciones del historial con filtros

HistorialFuncion.stats_general()
    ↳ Estadísticas totales: total_funciones, total_espectadores, 
                            ingresos_totales, promedios

HistorialFuncion.stats_por_pelicula()
    ↳ Ingresos y ocupación por película

HistorialFuncion.stats_por_sala()
    ↳ Ingresos y ocupación por sala

HistorialFuncion.stats_por_fecha_rango(fecha_desde, fecha_hasta)
    ↳ Ingresos diarios en un rango

HistorialFuncion.reporte_detallado(pelicula_id, sala_id)
    ↳ Reporte completo con todos los detalles
```

---

### 3. Scheduler Automático ([scheduler.py](scheduler.py)) - NUEVO

**Tareas Programadas:**

```
Cada 2 MINUTOS:
  → Tiquete.habilitar_tickets_ventana()
    Habilita tickets 25 min antes de cada función

Cada 5 MINUTOS:
  → Funcion.actualizar_estados_automaticos()
    Actualiza estados: programada → en_curso → finalizada

Cada 1 HORA:
  → Funcion.mover_finalizadas_a_historial()
    Archiva funciones finalizadas en historial
```

**Integración:**
- Inicializado en `app.py` con `init_scheduler(app)`
- Usa APScheduler (BackgroundScheduler)
- Logging de operaciones

---

### 4. Rutas Actualizadas

#### [routes/tiquetes.py](routes/tiquetes.py)
**Ruta `/tiquetes/validar` - Completamente Rediseñada:**

```python
POST /tiquetes/validar
  Parámetros:
    - codigo: Código QR del ticket
    - accion: 'consultar' (ver estado) o 'usar' (marcar como usado)
  
  Respuesta:
    - status: 'temprano', 'valido', 'tarde', 'no_encontrado'
    - mensaje: Descripción clara del estado
    - valid: bool - Si se puede validar
    - tiquete: Datos del ticket
    - minutos_para_habilitar: Si está temprano
    - detalles: Listado de asientos (si se valida)
```

#### [routes/admin.py](routes/admin.py) - Nuevas Rutas

```python
GET /admin/funciones/historial
  ↳ Lista todas las funciones finalizadas
  ↳ Muestra estadísticas generales

GET /admin/funciones/historial/reporte
  ↳ Reporte completo con filtros por fecha
  ↳ Estadísticas por película, sala y fechas
  ↳ Parámetros: fecha_desde, fecha_hasta, pelicula_id

GET /admin/funciones/historial/<id>
  ↳ Detalle de una función archivada
  ↳ Muestra ingresos, ocupación, duración real
```

---

### 5. Dependencias Agregadas (requirements.txt)

```
APScheduler==3.10.4
```

Instalar con:
```bash
pip install APScheduler==3.10.4
```

---

## 🚀 Cómo Usar

### Para el Cliente (Compra de Tickets):
1. Cliente compra ticket → **Estado = "inhabilitado"**
2. 25 minutos antes de la función → **Estado = "valido"** (automático)
3. Cliente se presenta con el QR para entrar
4. Taquillero/Validador escanea y valida → **Estado = "usado"**
5. Después de que termina la película → Función archivada al historial

### Para el Administrador:

**Ver Historial de Funciones:**
- Ir a: `/admin/funciones/historial`
- Muestra todas las funciones finalizadas

**Generar Reportes:**
- Ir a: `/admin/funciones/historial/reporte`
- Filtrar por rango de fechas
- Ver estadísticas por película y sala

**Verificar Ingresos:**
- Total de dinero ganado por cada función
- Ocupación (cantidad de tickets vendidos)
- Comparativas entre películas y salas

---

## ⏱️ Cronograma de Ejecutables

| Tarea | Frecuencia | Función |
|-------|-----------|---------|
| Habilitar tickets | Cada 2 min | `Tiquete.habilitar_tickets_ventana()` |
| Actualizar estados | Cada 5 min | `Funcion.actualizar_estados_automaticos()` |
| Archivar funciones | Cada 1 hora | `Funcion.mover_finalizadas_a_historial()` |

---

## 🧪 Ejemplo de Flujo Completo

**Película: "El Gran Azul"**
- Duración: 122 minutos
- Inicio programado: 14:00 del 10/04/2026
- Tickets precio: $20.000 COP

### Timeline:

```
13:15 - PROGRAMADA
  → Tickets creados con estado "inhabilitado"
  
13:35 - (25 min antes)
  → Scheduler habilita todos los tickets → "valido"
  → Ticket1: "✅ El ticket se habilitará en X minutos"
  
14:00 - EN CURSO (Auto-actualizado)
  → Función cambia a "en_curso"
  → Tickets aún pueden validarse
  
15:42 - (después de 122 min)
  → Función cambia a "finalizada"
  
16:00 - ARCHIVADA
  → Scheduler mueve función al historial:
    * quantity_tiquetes: 45
    * ingresos_totales: $900.000
    * ocupación: 45/150 asientos (30%)
  → Se elimina de funciones activas
```

---

## 📊 Consultas de Ejemplo (Para Reportes)

```sql
-- Ingresos totales por película
SELECT pelicula_titulo, COUNT(*) AS funciones,
       SUM(cantidad_tiquetes) AS espectadores,
       SUM(ingresos_totales) AS ingresos
FROM historial_funciones
GROUP BY pelicula_id, pelicula_titulo
ORDER BY ingresos DESC;

-- Funciones del mes pasado
SELECT * FROM historial_funciones
WHERE fecha_original BETWEEN '2026-03-01' AND '2026-03-31'
ORDER BY ingresos_totales DESC;

-- Ocupación promedio por sala
SELECT sala_nombre,
       AVG(cantidad_tiquetes / 150 * 100) AS ocupacion_promedio
FROM historial_funciones
GROUP BY sala_id, sala_nombre;
```

---

## 🔐 Validaciones de Seguridad

### Ventana de 25 Minutos:

1. **Antes de 25 min**: Ticket INHABILITADO
   - Usuario verá: "⏳ El ticket se habilitará en X minutos"
   - No puede entrar

2. **Dentro de 25 min**: Ticket VÁLIDO
   - Usuario verá: "✅ Puedes acceder"
   - Puede entrar

3. **Después de inicio**: Ticket INVÁLIDO
   - Usuario verá: "❌ La función ya ha iniciado"
   - No puede entrar

4. **Después de terminar**: Ticket INVÁLIDO
   - Usuario verá: "❌ La función ya ha finalizado"
   - No puede entrar

---

## 📝 Próximas Mejoras (Sugerencias)

- [ ] Notificaciones vía email cuando ticket se habilita
- [ ] SMS/WhatsApp recordatorios 30 min antes
- [ ] Integración con pago electrónico
- [ ] Dashboard en tiempo real de ocupación
- [ ] Exportar reportes a PDF/Excel
- [ ] Analytics avanzado (mejor hora, película más popular, etc.)

---

## ❓ Troubleshooting

### Scheduler no funciona:
```bash
# Instalar APScheduler
pip install APScheduler==3.10.4

# Verificar logs en app.py
```

### Tickets no se habilitan:
- Verificar que `created_at` en funciones esté correcto
- Revisar que el scheduler está corriendo (check logs)

### No aparecen en historial:
- Esperar a que función se finalice (duración de película)
- Scheduler mueve cada 1 hora
- Check: `SELECT * FROM historial_funciones;`

---

## 📚 Archivos Modificados/Creados

### Modificados:
- [database.sql](database.sql) - Agregas tablas y campos
- [models/tiquete.py](models/tiquete.py) - Métodos validación 25 min
- [models/funcion.py](models/funcion.py) - Métodos actualización automática
- [routes/tiquetes.py](routes/tiquetes.py) - Ruta validación renovada
- [routes/admin.py](routes/admin.py) - Rutas historial y reportes
- [app.py](app.py) - Inicializar scheduler
- [requirements.txt](requirements.txt) - Agregar APScheduler

### Creados:
- [scheduler.py](scheduler.py) - Tareas automáticas
- [models/historial.py](models/historial.py) - Gestión de historial
- [IMPLEMENTACION.md](IMPLEMENTACION.md) - Este archivo

---

## ✅ Checklist de Verificación

```
Backend:
✅ BD actualizada con nuevas tablas y campos
✅ Modelo Tiquete con lógica 25 minutos
✅ Modelo Funcion con actualización automática
✅ Modelo Historial creado
✅ Scheduler configurado y corriendo
✅ Rutas de validación implementadas
✅ Rutas de reportes implementadas

Deployment:
✅ requirements.txt actualizado
✅ Scheduler inicializa en app.py
✅ No hay breaking changes en rutas existentes

Frontend (Todavía por implementar):
⏳ Templates para historial de funciones
⏳ Templates para reportes
⏳ Actualizar validar.html con nuevos status
```

---

**Fecha de Implementación:** 9 de Abril de 2026
**Versión:** 2.0.0
**Estado:** ✅ COMPLETADO
