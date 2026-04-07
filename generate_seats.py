"""
Script para generar asientos en la sala de cine.
Ejecutar: python generate_seats.py
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
DB_NAME = os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or os.environ.get('DB_NAME') or 'railway'

logger.info(f"Conectando a {DB_HOST}:{DB_PORT}/{DB_NAME}...")

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )
    
    cursor = conn.cursor()
    
    # Obtener salas
    cursor.execute("SELECT id, nombre, filas, cols FROM salas")
    salas = cursor.fetchall()
    
    if not salas:
        logger.warning("⚠️  No hay salas creadas. Crea una sala primero.")
        sys.exit(1)
    
    total_asientos = 0
    
    # Generar asientos para cada sala
    for sala_id, sala_nombre, filas, cols in salas:
        logger.info(f"Generando asientos para {sala_nombre} ({filas}x{cols})...")
        
        # Limpiar asientos existentes
        cursor.execute("DELETE FROM asientos WHERE sala_id = %s", (sala_id,))
        
        # Generar nuevos asientos
        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for fila_idx in range(filas):
            fila_letra = letras[fila_idx]
            for col_idx in range(1, cols + 1):
                numero = f"{fila_letra}{col_idx}"
                cursor.execute("""
                    INSERT INTO asientos (numero, fila, columna, sala_id) 
                    VALUES (%s, %s, %s, %s)
                """, (numero, fila_letra, col_idx, sala_id))
                total_asientos += 1
        
        logger.info(f"✅ {filas * cols} asientos creados para {sala_nombre}")
    
    cursor.close()
    conn.close()
    
    logger.info(f"\n✅ Total de asientos generados: {total_asientos}")
    sys.exit(0)
    
except Exception as e:
    logger.error(f"❌ Error: {e}")
    sys.exit(1)
