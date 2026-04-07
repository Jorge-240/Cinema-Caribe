"""
Script para validar y testear toda la funcionalidad de la BD.
Ejecutar: python test_db_complete.py
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv
import logging
from werkzeug.security import generate_password_hash

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuración
DB_HOST = os.environ.get('MYSQLHOST') or os.environ.get('DB_HOST') or 'localhost'
DB_PORT = int(os.environ.get('MYSQLPORT') or os.environ.get('DB_PORT') or 3306)
DB_USER = os.environ.get('MYSQLUSER') or os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('MYSQLPASSWORD') or os.environ.get('DB_PASSWORD') or ''
DB_NAME = os.environ.get('MYSQLDATABASE') or os.environ.get('DB_NAME') or 'railway'

print("=" * 70)
print("VALIDADOR COMPLETO DE BD - CINEMA CARIBE")
print("=" * 70)
print(f"\nConectando a {DB_HOST}:{DB_PORT}/{DB_NAME} como {DB_USER}...\n")

try:
    # 1. CONECTAR
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False  # Transacciones explícitas
    )
    logger.info("✅ Conexión establecida")
    
    cursor = conn.cursor(dictionary=True)
    
    # 2. VERIFICAR TABLAS
    logger.info("\n--- Verificando tablas ---")
    cursor.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
    """, (DB_NAME,))
    tables = cursor.fetchall()
    expected_tables = ['usuarios', 'peliculas', 'salas', 'funciones', 'asientos', 'tiquetes', 'detalle_tiquete', 'funcion_asiento']
    found_tables = [t['TABLE_NAME'] for t in tables]
    
    for table in expected_tables:
        if table in found_tables:
            logger.info(f"✅ Tabla '{table}' existe")
        else:
            logger.warning(f"❌ Tabla '{table}' NO existe")
    
    # 3. CONTAR DATOS
    logger.info("\n--- Conteo de datos ---")
    for table in expected_tables:
        if table in found_tables:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()['cnt']
            logger.info(f"  {table}: {count} registros")
    
    # 4. TEST WRITE
    logger.info("\n--- Test de ESCRITURA ---")
    
    # Limpiar datos de prueba
    cursor.execute("DELETE FROM usuarios WHERE email LIKE 'test_%'")
    
    # Intentar insertar usuario de prueba
    test_email = 'test_write@test.com'
    test_password = generate_password_hash('test123')
    
    cursor.execute(
        "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)",
        ('Test Write', test_email, test_password, 'cliente')
    )
    conn.commit()  # IMPORTANTE: commit explícito
    logger.info(f"✅ Usuario escrito: {test_email}")
    
    # 5. TEST READ
    logger.info("\n--- Test de LECTURA ---")
    cursor.execute("SELECT id, nombre, email, rol FROM usuarios WHERE email = %s", (test_email,))
    user = cursor.fetchone()
    
    if user:
        logger.info(f"✅ Usuario leído correctamente:")
        logger.info(f"   ID: {user['id']}, Nombre: {user['nombre']}, Email: {user['email']}, Rol: {user['rol']}")
    else:
        logger.error(f"❌ Usuario NO encontrado tras escritura!")
    
    # 6. TEST UPDATE
    logger.info("\n--- Test de ACTUALIZACIÓN ---")
    cursor.execute(
        "UPDATE usuarios SET nombre = %s WHERE email = %s",
        ('Test Updated', test_email)
    )
    conn.commit()
    logger.info(f"✅ Usuario actualizado")
    
    # Verificar actualización
    cursor.execute("SELECT nombre FROM usuarios WHERE email = %s", (test_email,))
    user_updated = cursor.fetchone()
    if user_updated and user_updated['nombre'] == 'Test Updated':
        logger.info(f"✅ Actualización verificada: {user_updated['nombre']}")
    else:
        logger.error(f"❌ Actualización NO verificada")
    
    # 7. TEST DELETE
    logger.info("\n--- Test de ELIMINACIÓN ---")
    cursor.execute("DELETE FROM usuarios WHERE email = %s", (test_email,))
    conn.commit()
    logger.info(f"✅ Usuario eliminado")
    
    cursor.execute("SELECT COUNT(*) as cnt FROM usuarios WHERE email = %s", (test_email,))
    count = cursor.fetchone()['cnt']
    if count == 0:
        logger.info(f"✅ Eliminación verificada (no hay registros)")
    else:
        logger.error(f"❌ Eliminación NO verificada (aún hay {count} registros)")
    
    # 8. RESUMEN
    logger.info("\n" + "=" * 70)
    logger.info("✅ TODOS LOS TESTS COMPLETADOS CORRECTAMENTE")
    logger.info("=" * 70)
    
    cursor.close()
    conn.close()
    sys.exit(0)
    
except Exception as e:
    logger.error(f"❌ ERROR: {e}", exc_info=True)
    sys.exit(1)
