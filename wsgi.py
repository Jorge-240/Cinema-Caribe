"""
WSGI entry point para gunicorn.
Este archivo reemplaza 'app:app' en el Procfile.
"""
import os
import logging
import sys

# Setup logging antes de todo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("🚀 Iniciando wsgi.py...")
    logger.info(f"Python {sys.version}")
    logger.info(f"CWD: {os.getcwd()}")
    logger.info(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'not set')}")
    logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
    
    # Importar y crear la app
    from app import app
    
    logger.info("✅ App importada exitosamente desde app.py")
    logger.info(f"✅ Flask app está lista: {app}")
    
except Exception as e:
    logger.error(f"❌ Error crítico en wsgi.py: {e}", exc_info=True)
    raise
