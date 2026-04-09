# 🚀 Guía de Instalación y Prueba - Sistema de Validación de Tickets

## Paso 1: Actualizar Dependencies

```bash
cd c:\Users\admin\Desktop\cine_app

# Activar venv (si aún no está)
.\venv\Scripts\Activate.ps1

# Instalar nuevas dependencias
pip install -r requirements.txt

# Verificar instalación de APScheduler
pip show APScheduler
```

**Salida Esperada:**
```
Name: APScheduler
Version: 3.10.4
Location: c:\Users\admin\...\site-packages\apscheduler
```

---

## Paso 2: Actualizar Base de Datos

### Opción A: Usando el endpoint `/initialize` (Recomendado)

```bash
# Iniciar la app
python app.py

# Luego en el navegador:
http://localhost:5000/initialize

# Debería retornar:
{
  "status": "success",
  "database": "cinema_caribe",
  "executed": 180+,
  "skipped": 0,
  "errors": 0
}
```

### Opción B: Manualmente en MySQL

```bash
# Abrir MySQL
mysql -u root -p cinema_caribe < database.sql

# O si tienes PhpMyAdmin:
1. Importar database.sql
2. Ejecutar
```

### Verificar que las nuevas tablas existen:

```sql
USE cinema_caribe;

-- Verificar campos nuevos en funciones
SHOW COLUMNS FROM funciones;
-- Debe mostrar: created_at, updated_at

-- Verificar campos nuevos en tiquetes
SHOW COLUMNS FROM tiquetes;
-- Debe mostrar: fue_validado, fecha_validacion,
--               estado debe tener 'inhabilitado'

-- Verificar tabla historial
SHOW TABLES LIKE 'historial%';
-- Debe retornar: historial_funciones
```

---

## Paso 3: Probar el Sistema

### 3.1 Verificar Scheduler está Corriendo

```bash
# Iniciar app
python app.py

# Observar console:
```
✓ Scheduler inicializado correctamente
```

Si ves este mensaje, ✅ el scheduler está activo.

### 3.2 Crear Función de Prueba

```python
# Script: test_sistema.py

from datetime import datetime, timedelta
from models.funcion import Funcion
from models.pelicula import Pelicula
from models.tiquete import Tiquete
from utils.db import init_app
from flask import Flask

app = Flask(__name__)
# ... config ...
init_app(app)

with app.app_context():
    # 1. Obtener película
    peliculas = Pelicula.listar(solo_activas=True)
    pelicula_id = peliculas[0]['id']
    print(f"Película: {peliculas[0]['titulo']} ({peliculas[0]['duracion']} min)")
    
    # 2. Crear función para ahora + 25 minutos
    ahora = datetime.now()
    fecha_funcion = (ahora + timedelta(minutes=25)).date()
    hora_funcion = (ahora + timedelta(minutes=25)).time()
    
    funcion_id = Funcion.crear(
        pelicula_id=pelicula_id,
        sala_id=1,
        fecha=fecha_funcion,
        hora=hora_funcion,
        precio=18000,
        estado='programada'
    )
    print(f"✅ Función creada: ID {funcion_id}")
    
    # 3. Comprar un ticket (con usuario existente)
    usuario_id = 2  # Usuario cliente
    tiquete_id, codigo = Tiquete.crear(
        usuario_id=usuario_id,
        funcion_id=funcion_id,
        asiento_ids=[1, 2],
        precio_unitario=18000,
        qr_folder='static/img/qr',
        nombre_cliente='Cliente Prueba'
    )
    print(f"✅ Ticket creado: {codigo}")
    
    # 4. Verificar estado inhabilitado
    tiquete = Tiquete.obtener(tiquete_id)
    print(f"Estado inicial: {tiquete['estado']}")  # Debería ser "inhabilitado"
    
    # 5. Simular validación (ahora)
    validacion = Tiquete.validar_con_ventana_25_min(codigo)
    print(f"Status: {validacion['status']}")
    print(f"Mensaje: {validacion['mensaje']}")
    print(f"Valid: {validacion['valid']}")
```

**Ejecución:**
```bash
python test_sistema.py
```

**Salida Esperada:**
```
Película: El Gran Azul (122 min)
✅ Función creada: ID 10
✅ Ticket creado: ABC123DEF456GHI
Estado inicial: inhabilitado
Status: temprano
Mensaje: El ticket se habilitará en 24 minutos.
Valid: False
```

### 3.3 Aguardar 2 Minutos (Para que Scheduler Habilite)

```bash
# Esperar a que el scheduler ejecute:
# - Cada 2 min: habilitar_tickets_ventana()
# - Debe cambiar ticket de "inhabilitado" a "valido"

# Script para monitorear:
import time
from models.tiquete import Tiquete

while True:
    tiquete = Tiquete.obtener(tiquete_id)
    print(f"[{datetime.now()}] Estado: {tiquete['estado']}")
    
    if tiquete['estado'] == 'valido':
        print("✅ Ticket habilitado por scheduler!")
        break
    
    time.sleep(30)  # Revisar cada 30 seg
```

### 3.4 Validar Ticket + Entrar

```python
# Cuando estado sea "valido"

# Simular validación (como si taquillero escanea QR)
validacion = Tiquete.validar_con_ventana_25_min(codigo)
print(validacion)

# Retorno:
{
    'valid': True,
    'status': 'valido',
    'mensaje': '✅ ¡Ticket válido! Puedes acceder...',
    'tiquete': {...},
}

# Marcar como usado (entrada concedida)
Tiquete.marcar_validado(codigo)

# Verificar:
tiquete = Tiquete.obtener(tiquete_id)
print(tiquete['estado'])  # Debe ser "usado"
print(tiquete['fue_validado'])  # True
print(tiquete['fecha_validacion'])  # Timestamp actual
```

---

## Paso 4: Probar Actualización Automática de Estados

### 4.1 Crear Función que Comience en 5 Segundos

```python
from datetime import datetime, timedelta

# Función comienza en 5 segundos
ahora = datetime.now()
fecha_proximo = ahora.date()
hora_proximo = (ahora + timedelta(seconds=5)).time()

pelicula = Pelicula.listar(solo_activas=True)[0]
funcion_id = Funcion.crear(
    pelicula_id=pelicula['id'],
    sala_id=1,
    fecha=fecha_proximo,
    hora=hora_proximo,
    precio=20000,
    estado='programada'
)

# Verificar estado actual
funcion = Funcion.obtener(funcion_id)
print(f"Estado: {funcion['estado']}")  # programada
```

### 4.2 Esperar 5 Segundos + Check

```python
import time

time.sleep(7)  # Esperar a que pase la hora

# Ejecutar actualizador (o esperar 5 min a scheduler)
curso, fin = Funcion.actualizar_estados_automaticos()
print(f"En curso: {curso}, Finalizadas: {fin}")

# Verificar
funcion = Funcion.obtener(funcion_id)
print(f"Estado ahora: {funcion['estado']}")  # Debe ser "en_curso"
```

---

## Paso 5: Validación Completa (E2E)

```bash
# Script completo de prueba:
python -c "
from datetime import datetime, timedelta
from models.funcion import Funcion
from models.tiquete import Tiquete
from models.pelicula import Pelicula
import time

# Test 1: Ticket inhabilitado
print('==== TEST 1: Ticket Inhabilitado ====')
# ... crear función con ticket ...
validacion = Tiquete.validar_con_ventana_25_min(codigo)
assert validacion['status'] == 'temprano', 'Error: debería estar temprano'
print('✅ Ticket correctamente inhabilitado')

# Test 2: Esperar habilitación
print('\\n==== TEST 2: Habilitación Automática ====')
# ... esperar scheduler ...
Tiquete.habilitar_tickets_ventana()
tiquete = Tiquete.obtener(tiquete_id)
assert tiquete['estado'] == 'valido', 'Error: no se habilitó'
print('✅ Ticket habilitado por scheduler')

# Test 3: Validación exitosa
print('\\n==== TEST 3: Validación Exitosa ====')
validacion = Tiquete.validar_con_ventana_25_min(codigo)
assert validacion['valid'] == True, 'Error: no debería ser válido'
print('✅ Ticket validado correctamente')

# Test 4: Marcar como usado
print('\\n==== TEST 4: Marcar Como Usado ====')
Tiquete.marcar_validado(codigo)
tiquete = Tiquete.obtener(tiquete_id)
assert tiquete['estado'] == 'usado', 'Error: no se marcó como usado'
assert tiquete['fue_validado'] == True, 'Error: fue_validado no es True'
print('✅ Ticket marcado como usado')

print('\\n✅ TODOS LOS TESTS PASARON')
"
```

---

## Paso 6: Probar Historial

### 6.1 Crear Función Que Termine Inmediatamente

```python
# Crear película de 1 minuto (para testing)
pelicula_test_id = Pelicula.crear(
    titulo='Test Rápido',
    descripcion='Test',
    duracion=1,  # 1 minuto
    genero='Testing',
    clasificacion='G'
)

# Función comienza hace 1 minuto (ya terminó)
hace_1_min = datetime.now() - timedelta(minutes=1)
funcion_id = Funcion.crear(
    pelicula_id=pelicula_test_id,
    sala_id=1,
    fecha=hace_1_min.date(),
    hora=hace_1_min.time(),
    precio=15000
)

# Vender algunos tickets
for i in range(1, 4):
    Tiquete.crear(
        usuario_id=2,
        funcion_id=funcion_id,
        asiento_ids=[i],
        precio_unitario=15000,
        qr_folder='static/img/qr'
    )

# Actualizar estado a finalizada
Funcion.actualizar_estados_automaticos()

# Verificar que está finalizada
funcion = Funcion.obtener(funcion_id)
print(f"Estado: {funcion['estado']}")  # Debe ser "finalizada"
```

### 6.2 Mover al Historial

```python
# Ejecutar movimiento
movidas = Funcion.mover_finalizadas_a_historial()
print(f"✅ {movidas} función(es) movida(s) al historial")

# Verificar en historial
historial = HistorialFuncion.listar()
print(f"Total en historial: {len(historial)}")
for h in historial:
    print(f"  - {h['pelicula_titulo']}: {h['cantidad_tiquetes']} tickets, ${h['ingresos_totales']}")

# Obtener estadísticas
stats = HistorialFuncion.stats_general()
print(f"Stats generales: {stats}")
```

---

## Paso 7: Verificar Rutas en Navegador

### Test Manual de Rutas

```
Validación de Tickets:
- GET  http://localhost:5000/tiquetes/validar
- POST http://localhost:5000/tiquetes/validar
  Parámetro: codigo=ABC123DEF456GHI
  Parámetro: accion=consultar

Historial de Funciones:
- GET http://localhost:5000/admin/funciones/historial

Reportes:
- GET http://localhost:5000/admin/funciones/historial/reporte
- GET http://localhost:5000/admin/funciones/historial/reporte?fecha_desde=2026-04-01&fecha_hasta=2026-04-30

Detalle de Función:
- GET http://localhost:5000/admin/funciones/historial/1
```

---

## 📋 Checklist de Pruebas

```
Backend:
☑ APScheduler instalado (pip show APScheduler)
☑ BD actualizada (SHOW COLUMNS FROM funciones)
☑ Tablas nuevas existen (SHOW TABLES)
☑ Scheduler inicializa sin errores
☑ Ticket créado con estado "inhabilitado"
☑ Scheduler habilita tickets a tiempo
☑ Validación con ventana 25 min funciona
☑ Estados de funciones se actualizan
☑ Funciones se archivan en historial
☑ Reportes generan datos correctos

Frontend (Por Implementar):
☐ Template para /tiquetes/validar con nuevos estados
☐ Template para /admin/funciones/historial
☐ Template para /admin/funciones/historial/reporte
☐ Mostrar estadísticas en dashboard
```

---

## 🔍 Debugging

### Ver logs del scheduler

```bash
# En app.py, aumentar nivel de logging:
logging.basicConfig(level=logging.DEBUG)

# Reiniciar app para ver logs detallados
python app.py
```

### Verificar qué funciones están en cola

```sql
SELECT id, pelicula_id, fecha, hora, estado, 
       DATE_ADD(CONCAT(fecha, ' ', hora), INTERVAL 1 DAY) AS fin_estimada
FROM funciones
ORDER BY fecha DESC, hora DESC;
```

### Ver tickets en historial

```sql
SELECT * FROM historial_funciones ORDER BY fecha_original DESC;
```

### Limpiar para testing

```sql
-- ⚠️ SOLO EN DEVELOPMENT
DELETE FROM historial_funciones;
DELETE FROM tiquetes;
DELETE FROM funciones;
```

---

## 📞 Soporte

Si encuentras errores:

1. **Scheduler no ejecuta:**
   - Verificar: `pip show APScheduler`
   - Instalar: `pip install APScheduler==3.10.4`
   - Reiniciar app

2. **Tickets no se habilitan:**
   - Check: `SELECT COUNT(*) FROM apscheduler_jobs;`
   - Revisar logs de scheduler

3. **Funciones no se archivan:**
   - Esperar 1+ hora
   - O ejecutar manualmente: `Funcion.mover_finalizadas_a_historial()`

---

**¡Tu sistema está listo para usar!** 🎬🎉
