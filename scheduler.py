"""
Scheduler de tareas automáticas para Cinema Caribe.

Gestiona:
- Actualización de estados de funciones (programada -> en_curso -> finalizada)
- Habilitación de tickets 25 minutos antes de inicio
- Movimiento de funciones finalizadas al historial
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime
from utils.timezone import now_colombia

logger = logging.getLogger(__name__)


def init_scheduler(app):
    """Inicializa el scheduler cuando la app arranca."""
    scheduler = BackgroundScheduler(daemon=True)
    
    # 1. Actualizar estados cada 1 minuto (para cambios de estado y eliminación inmediatos)
    @scheduler.scheduled_job(IntervalTrigger(minutes=1))
    def actualizar_estados_funciones():
        with app.app_context():
            try:
                from models.funcion import Funcion
                curso, finalizado = Funcion.actualizar_estados_automaticos()
                if curso > 0 or finalizado > 0:
                    logger.info(f"[{now_colombia()}] Estados actualizados: {curso} a en_curso, {finalizado} a finalizada")
            except Exception as e:
                logger.error(f"Error actualizando estados: {e}")
    
    # 2. Habilitar tickets cada 2 minutos
    @scheduler.scheduled_job(IntervalTrigger(minutes=2))
    def habilitar_tickets():
        with app.app_context():
            try:
                from models.tiquete import Tiquete
                habilitados = Tiquete.habilitar_tickets_ventana()
                if habilitados > 0:
                    logger.info(f"[{now_colombia()}] {habilitados} tickets habilitados")
            except Exception as e:
                logger.error(f"Error habilitando tickets: {e}")
    
    # 3. Eliminar funciones finalizadas cada 1 minuto (enseguida que terminen)
    @scheduler.scheduled_job(IntervalTrigger(minutes=1))
    def eliminar_finalizadas():
        with app.app_context():
            try:
                from models.funcion import Funcion
                eliminadas = Funcion.eliminar_funciones_finalizadas()
                if eliminadas > 0:
                    logger.info(f"[{now_colombia()}] {eliminadas} funciones finalizadas eliminadas")
            except Exception as e:
                logger.error(f"Error eliminando funciones finalizadas: {e}")
    
    scheduler.start()
    logger.info("✓ Scheduler inicializado correctamente")
    
    return scheduler
