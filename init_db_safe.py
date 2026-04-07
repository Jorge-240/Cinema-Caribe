"""
Script para inicializar la BD si no existe.
Ejecutar: python init_db_safe.py
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Obtener configuración
DB_HOST = os.environ.get('MYSQLHOST') or os.environ.get('MYSQL_HOST') or os.environ.get('DB_HOST') or 'localhost'
DB_PORT = int(os.environ.get('MYSQLPORT') or os.environ.get('MYSQL_PORT') or os.environ.get('DB_PORT') or 3306)
DB_USER = os.environ.get('MYSQLUSER') or os.environ.get('MYSQL_USER') or os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD') or os.environ.get('DB_PASSWORD') or ''
DB_NAME = os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or os.environ.get('DB_NAME') or 'cinema_caribe'

logger.info(f"Conectando a {DB_HOST}:{DB_PORT}/{DB_NAME}...")

try:
    # Conectar
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cur = conn.cursor()
    
    # Verificar si existen las tablas
    cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (DB_NAME,))
    table_count = cur.fetchone()[0]
    
    if table_count > 0:
        logger.info(f"✅ Base de datos ya existe con {table_count} tablas")
    else:
        logger.warning(f"⚠️  Base de datos existe pero no hay tablas. Necesitas correr las migraciones.")
        logger.info("Para inicializar, ejecuta: python init_db.py")
    
    cur.close()
    conn.close()
    logger.info("✅ Conexión exitosa!")
    sys.exit(0)
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    sys.exit(1)
