"""
Script para validar que todo esté configurado correctamente en Railway.
Ejecutar: python validate_railway.py
"""
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_env_vars():
    """Valida que las variables de entorno estén configuradas."""
    logger.info("🔍 Validando variables de entorno...")
    
    required_keys = [
        ('MYSQLHOST', ['MYSQL_HOST', 'DB_HOST']),
        ('MYSQLPORT', ['MYSQL_PORT', 'DB_PORT']),
        ('MYSQLUSER', ['MYSQL_USER', 'DB_USER']),
        ('MYSQLPASSWORD', ['MYSQL_PASSWORD', 'DB_PASSWORD']),
        ('MYSQLDATABASE', ['MYSQL_DATABASE', 'DB_NAME']),
    ]
    
    all_ok = True
    for primary, alternatives in required_keys:
        value = os.environ.get(primary)
        if not value:
            for alt in alternatives:
                value = os.environ.get(alt)
                if value:
                    logger.warning(f"⚠️  {primary} no configurada, usando {alt}")
                    break
        
        if value:
            if 'password' in primary.lower() or 'password' in alternatives[0].lower():
                logger.info(f"✅ {primary} configurada (***)")
            else:
                logger.info(f"✅ {primary} = {value}")
        else:
            logger.error(f"❌ {primary} NO configurada")
            all_ok = False
    
    return all_ok

def validate_db_connection():
    """Intenta conectar a la BD."""
    logger.info("\n🔍 Validando conexión a base de datos...")
    
    try:
        import mysql.connector
        
        conn_params = {
            'host': (os.environ.get('MYSQLHOST') or 
                    os.environ.get('MYSQL_HOST') or 
                    os.environ.get('DB_HOST')),
            'port': int(os.environ.get('MYSQLPORT') or 
                       os.environ.get('MYSQL_PORT') or 
                       os.environ.get('DB_PORT') or 3306),
            'user': (os.environ.get('MYSQLUSER') or 
                    os.environ.get('MYSQL_USER') or 
                    os.environ.get('DB_USER')),
            'password': (os.environ.get('MYSQLPASSWORD') or 
                        os.environ.get('MYSQL_PASSWORD') or 
                        os.environ.get('DB_PASSWORD')),
            'database': (os.environ.get('MYSQLDATABASE') or 
                        os.environ.get('MYSQL_DATABASE') or 
                        os.environ.get('DB_NAME')),
        }
        
        logger.info(f"Conectando a {conn_params['host']}:{conn_params['port']}/{conn_params['database']}...")
        
        conn = mysql.connector.connect(**conn_params)
        logger.info("✅ Conexión a BD exitosa!")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("Cinema Caribe — Validador de Railway")
    logger.info("=" * 60 + "\n")
    
    env_ok = validate_env_vars()
    db_ok = validate_db_connection()
    
    logger.info("\n" + "=" * 60)
    if env_ok and db_ok:
        logger.info("✅ TODO LISTO - Sistema configurado correctamente")
        return 0
    else:
        logger.error("❌ Hay errores de configuración")
        return 1

if __name__ == '__main__':
    sys.exit(main())
