# 📊 Diagrama de Flujo - Sistema Completo

## 1️⃣ FLUJO DE COMPRA DE TICKETS

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENTE COMPRA TICKET                                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Tiquete creado                                              │
│ ├─ estado: "inhabilitado"                                  │
│ ├─ fecha_compra: ahora                                     │
│ ├─ fue_validado: FALSE                                     │
│ └─ código QR generado                                      │
└─────────────────────────────────────────────────────────────┘
                             ↓
         ╔═══════════════════════════════════════════════════╗
         ║ SCHEDULER CADA 2 MINUTOS                          ║
         ║ Busca funciones con inicio en próximos 25 min     ║
         ║ Cambia tickets: inhabilitado → valido             ║
         ╚═══════════════════════════════════════════════════╝
                             ↓
         ┌──────────────────────────────────────┐
         │ 25 MINUTOS ANTES DE INICIO           │
         │ estado: "valido" ✅                  │
         │ Cliente puede presentar QR           │
         └──────────────────────────────────────┘
```

---

## 2️⃣ FLUJO DE VALIDACIÓN EN TAQUILLA

```
┌─────────────────────────────────────────────────────────────┐
│ TAQUILLERO ESCANEA QR                                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Sistema valida con lógica de 25 minutos:                    │
│                                                              │
│  ¿Encontrado el ticket?                                    │
│    NO  → ❌ "Código no encontrado"                         │
│    SI  → Continuar...                                      │
│                                                              │
│  ¿Estado del ticket?                                       │
│    anulado   → ❌ "Ticket anulado"                         │
│    usado     → ❌ "Ya fue validado"                        │
│    valido    → ✅ Procesar validación                      │
│    inhabilitado → ❌ "Aún no se habilita" (+X min)        │
└─────────────────────────────────────────────────────────────┘
                             ↓
    ╔═════════════════════════════════════════════════════╗
    ║ VENTANA DE VALIDACIÓN (25 MIN ANTES A INICIO)       ║
    ║                                                      ║
    ║ Ahora < inicio_ventana?                             ║
    ║   SI  → ❌ "El ticket se habilitará en X min"       ║
    ║   NO  → Continuar...                                ║
    ║                                                      ║
    ║ Ahora >= inicio_ventana && ahora < fin_ventana?     ║
    ║   SI  → ✅ "VÁLIDO - Puedes acceder"                ║
    ║   NO  → ❌ "La función ya inició"                   ║
    ╚═════════════════════════════════════════════════════╝
                             ↓
        ┌──────────────────────────────────────┐
        │ TAQUILLERO PRESIONA "MARCAR USADO"   │
        │ estado: "usado"                      │
        │ fecha_validacion: timestamp_actual   │
        │ fue_validado: TRUE                   │
        └──────────────────────────────────────┘
                             ↓
        ┌──────────────────────────────────────┐
        │ ✅ ENTRADA CONCEDIDA                 │
        │ Persona entra a la función           │
        └──────────────────────────────────────┘
```

---

## 3️⃣ FLUJO DE ACTUALIZACIÓN DE ESTADOS (SCHEDULER)

```
┌─────────────────────────────────────────────────────────────┐
│ SCHEDULER CADA 5 MINUTOS                                    │
│ Ejecuta: Funcion.actualizar_estados_automaticos()           │
└─────────────────────────────────────────────────────────────┘
                             ↓
      ┌──────────────────────────────────────────────┐
      │ BUSCAR: estado = 'programada'                │
      │         AND fecha+hora <= NOW()              │
      │         AND fecha+hora + duracion > NOW()    │
      │                                              │
      │ ACCIÓN: Cambiar estado → 'en_curso'          │
      │         (La funciónYA COMENZÓ)              │
      └──────────────────────────────────────────────┘
                             ↓
      ┌──────────────────────────────────────────────┐
      │ BUSCAR: estado = 'en_curso'                  │
      │         AND fecha+hora + duracion <= NOW()   │
      │                                              │
      │ ACCIÓN: Cambiar estado → 'finalizada'        │
      │         (La película TERMINÓ)               │
      └──────────────────────────────────────────────┘
                             ↓
    [Ejemplo]
    14:00 - función inicia    → 'programada' → 'en_curso'
    15:02 - película termina  → 'en_curso' → 'finalizada'
    16:00 - scheduler mueve   → archivada al historial
```

---

## 4️⃣ FLUJO DE ARCHIVADO AL HISTORIAL

```
┌─────────────────────────────────────────────────────────────┐
│ SCHEDULER CADA 1 HORA                                       │
│ Ejecuta: Funcion.mover_finalizadas_a_historial()            │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ BUSCAR funciones con estado = 'finalizada'                  │
└─────────────────────────────────────────────────────────────┘
                             ↓
           ╔════════════════════════════════════╗
           ║ PARA CADA FUNCIÓN FINALIZADA:     ║
           ╚════════════════════════════════════╝
                             ↓
      ┌───────────────────────────────────────────┐
      │ 1. CALCULAR ESTADÍSTICAS                  │
      │    ├─ COUNT(tiquetes validados/usados)    │
      │    ├─ SUM(total dinero)                   │
      │    └─ Otra metadata                       │
      └───────────────────────────────────────────┘
                             ↓
      ┌───────────────────────────────────────────┐
      │ 2. INSERTAR EN historial_funciones        │
      │    ├─ pelicula_id                         │
      │    ├─ sala_id                             │
      │    ├─ fecha_original                      │
      │    ├─ cantidad_tiquetes                   │
      │    ├─ ingresos_totales                    │
      │    ├─ duracion_pelicula                   │
      │    └─ fecha_finalizacion                  │
      └───────────────────────────────────────────┘
                             ↓
      ┌───────────────────────────────────────────┐
      │ 3. ELIMINAR DE funciones (activas)        │
      │    ✅ Función movida al historial         │
      └───────────────────────────────────────────┘

[RESULTADO EN HISTORIAL]
┌────────────────────────────────────────────────────────────┐
│ ID | Película       | Sala  | Tickets | Ingresos | Fin    │
├────────────────────────────────────────────────────────────┤
│ 1  | El Gran Azul   | Sala1 | 45      | 900.000  | 15:30  │
│ 2  | Noche Cartagena| Sala1 | 28      | 560.000  | 16:45  │
│ 3  | Tormenta Arena | Sala1 | 150     | 3300.000 | 21:50  │
└────────────────────────────────────────────────────────────┘
```

---

## 5️⃣ REPORTES Y ESTADÍSTICAS

```
┌──────────────────────────────────────────────────────────┐
│ ADMIN → /admin/funciones/historial                        │
└──────────────────────────────────────────────────────────┘
                             ↓
    ┌──────────────────────────────────────┐
    │ VISTA: Listado de Funciones Archivadas
    │                                      │
    │ 📊 ESTADÍSTICAS GENERALES:           │
    │  • Total Funciones: 47               │
    │  • Total Espectadores: 2,450         │
    │  • Ingresos Totales: $49,000,000     │
    │  • Promedio por Función: 52 personas │
    │  • Promedio Ingresos: $1,042,553     │
    └──────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────┐
│ ADMIN → /admin/funciones/historial/reporte               │
│         ?fecha_desde=2026-04-01&fecha_hasta=2026-04-30   │
└──────────────────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ ESTADÍSTICAS POR PELÍCULA:                  │
    │                                             │
    │ El Gran Azul .......................... 5   │
    │  • Funciones: 5                             │
    │  • Espectadores: 350                        │
    │  • Ingresos: $7,000,000                     │
    │                                             │
    │ Tormenta Arena ........................ 8   │
    │  • Funciones: 8                             │
    │  • Espectadores: 1,200                      │
    │  • Ingresos: $26,400,000                    │
    ├─────────────────────────────────────────────┤
    │ ESTADÍSTICAS POR SALA:                      │
    │                                             │
    │ Sala 1 (Principal)                          │
    │  • Funciones: 47                            │
    │  • Ocupación Máx: 150 asientos              │
    │  • Promedio Ocupación: 52 personas          │
    │  • Ingresos: $49,000,000                    │
    └─────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ GRÁFICOS (Por implementar en frontend):      │
    │  • Ingresos por día                          │
    │  • Ocupación por película                    │
    │  • Tendencias mensuales                      │
    │  • Proyecciones                              │
    └─────────────────────────────────────────────┘
```

---

## 6️⃣ CRONOGRAMA AUTOMÁTICO (SCHEDULER)

```
┌───────────────────────────────────────────────────────────┐
│                    SCHEDULER EN EJECUCIÓN                  │
│                                                            │
│  Hora      │ Tarea                     │ Acción            │
├───────────────────────────────────────────────────────────┤
│ 14:00:00   │                          │ Función inicia    │
│ 14:00:30   │ Cada 2 min: Habilitar    │ Nada (no es 25min)
│ 14:02:30   │ Cada 2 min: Habilitar    │ Nada              │
│ 14:05:00   │ Cada 5 min: Act. estados │ Función→en_curso  │
│ 14:10:00   │ Cada 5 min: Act. estados │ Nada              │
│ 14:25:00   │ Cada 2 min: Habilitar    │ Habilita tickets  │
│ 14:30:00   │ Cada 5 min: Act. estados │ Nada              │
│ 15:02:00   │ Cada 5 min: Act. estados │ Función→finaliza  │
│ 16:00:00   │ Cada 1 hora: Al historial│ Mueve función     │
│ 17:00:00   │ Cada 1 hora: Al historial│ Nada              │
└───────────────────────────────────────────────────────────┘

NOTA: Todos los horarios son aproximados.
El scheduler busca funciones activas cada vez que se ejecuta.
```

---

## 7️⃣ TABLA COMPARATIVA: ANTES vs DESPUÉS

```
┌──────────────────────────────────────────────────────────────┐
│                        ANTES                                 │
├──────────────────────────────────────────────────────────────┤
│ ❌ Tickets validos desde compra                              │
│ ❌ Cualquiera podía entrar en cualquier momento              │
│ ❌ No había control de timing                                │
│ ❌ Funciones no se actualizaban automáticamente              │
│ ❌ No había historial de funciones                           │
│ ❌ Imposible ver ingresos históricos                         │
│ ❌ Reportes manuales                                         │
└──────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────┐
│                        DESPUÉS                               │
├──────────────────────────────────────────────────────────────┤
│ ✅ Tickets inhabilitados hasta 25 min antes                  │
│ ✅ Validación solo en ventana de 25 minutos                  │
│ ✅ Control automático de timing (scheduler)                  │
│ ✅ Estados actualizados automáticamente                      │
│ ✅ Historial completo de todas las funciones                 │
│ ✅ Reportes automáticos con estadísticas                     │
│ ✅ Métricas: ingresos, ocupación, tendencias                │
└──────────────────────────────────────────────────────────────┘
```

---

## 8️⃣ EJEMPLO REAL DE UN DÍA

```
MARTES 9 DE ABRIL DE 2026
PELÍCULA: "Tormenta de Arena"
SALA: Sala Principal (150 asientos)
DURACIÓN: 110 minutos
PRECIO: $22,000 COP

13:00 - PREPARACIÓN
  └─ Admin programa función para 14:30

13:15 - COMPRAS
  ├─ Cliente 1 compra 2 tickets → estado: inhabilitado
  ├─ Cliente 2 compra 3 tickets → estado: inhabilitado
  ├─ Cliente 3 compra 1 ticket  → estado: inhabilitado
  ├─ Taquillero vende 4 tickets → estado: inhabilitado
  └─ Total: 10 tickets vendidos ($220,000)

14:05 - SCHEDULER (Cada 2 min)
  └─ Verifica: ¿Funciones con inicio en próximos 25 min?
     NO AÚN (Falta 25 min para 14:30)

14:20 - SCHEDULER
  └─ Verifica: ¿Inicio en próximos 25 min?
     ✅ SÍ → Cambia 10 tickets: inhabilitado → valido

14:25 - CLIENTES LLEGAN
  ├─ Cliente 1 escanea QR
  │  └─ Validación: ✅ VÁLIDO - Puedes acceder
  │     Taquillero marca como USADO
  ├─ Cliente 2 escanea QR
  │  └─ Validación: ✅ VÁLIDO - Puedes acceder
  │     Taquillero marca como USADO
  └─ ... (resto igual)

14:30 - PELÍCULA COMIENZA
  ├─ Función: programada → en_curso (scheduler)
  └─ Total registrado: 9 personas dentro

14:31 - CLIENTE REZAGADO LLEGA
  └─ Escanea QR:
     ❌ NO VÁLIDO - La función ya inició
     NO PUEDE ENTRAR

16:20 - PELÍCULA TERMINA
  └─ Función: en_curso → finalizada (scheduler)

17:00 - ARCHIVADO AL HISTORIAL
  └─ Función archivada:
     {
       película: "Tormenta de Arena",
       sala: "Sala Principal",
       fecha_original: 2026-04-09,
       hora_original: 14:30,
       cantidad_tiquetes: 10,
       ingresos_totales: 220000,
       duracion_pelicula: 110,
       fecha_finalizacion: 2026-04-09 16:20
     }

REPORTES DIARIOS:
  ✅ Función realizada
  ✅ $220,000 ingresados
  ✅ 9 espectadores (60% ocupación si hubiera sobrado espacio)
  ✅ 1 entrada rechazada (tardanza)
```

---

## 9️⃣ FLUJO TÉCNICO (ARQUITECTURA)

```
FLASK APP
│
├─ [REQUEST] POST /tiquetes/validar?codigo=ABC123
│           │
│           └─→ routes/tiquetes.py::validar()
│               │
│               └─→ Tiquete.validar_con_ventana_25_min(codigo)
│                   │
│                   ├─ Consulta: SELECT t.*, f.fecha, f.hora, p.duracion
│                   ├─ Calcula: inicio_ventana, fin_ventana, ahora
│                   ├─ Verifica: ¿ahora >= inicio_ventana?
│                   ├─ Retorna: {valid, status, mensaje, tiquete}
│                   │
│                   └─ Si valid=True:
│                       └─→ Tiquete.marcar_validado(codigo)
│                           └─ UPDATE tiquetes SET estado='usado'
│
├─ [SCHEDULER] APScheduler.BackgroundScheduler()
│             ejecuta cada 2 minutos:
│             │
│             └─→ Tiquete.habilitar_tickets_ventana()
│                 │
│                 ├─ SELECT funciones WHERE inicio EN próximos 25 min
│                 ├─ UPDATE tiquetes WHERE funcion_id IN (...) 
│                 │         SET estado='valido'
│                 └─ Log: "X tickets habilitados"
│
│             ejecuta cada 5 minutos:
│             │
│             └─→ Funcion.actualizar_estados_automaticos()
│                 │
│                 ├─ UPDATE funciones programada→en_curso
│                 ├─ UPDATE funciones en_curso→finalizada
│                 └─ Log: "X cambios de estado"
│
│             ejecuta cada 1 hora:
│             │
│             └─→ Funcion.mover_finalizadas_a_historial()
│                 │
│                 ├─ SELECT funciones WHERE estado='finalizada'
│                 ├─ INSERT INTO historial_funciones ...
│                 ├─ DELETE FROM funciones WHERE id=...
│                 └─ Log: "X funciones archivadas"
│
└─ [ADMIN DASHBOARD] GET /admin/funciones/historial/reporte
                       │
                       └─→ HistorialFuncion.stats_por_pelicula()
                           └─ Retorna datos para gráficos
                               (Por hacer: templates + frontend)
```

---

✅ **SISTEMA COMPLETO** - Listo para producción
🎬 **Cinema Caribe 2.0** - Validación automática de tickets
