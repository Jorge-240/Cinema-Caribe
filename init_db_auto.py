#!/usr/bin/env python3
"""
Script de inicialización automática para Railway.
Se ejecuta una sola vez al deployar.
Crea la BD, las tablas e inserta datos iniciales.
"""
import os
import sys
import time
import mysql.connector
from mysql.connector import Error

def get_connection_params():
    """Extrae parámetros de conexión del entorno."""
    # Soportar múltiples formatos de variables de Railway
    host = (os.environ.get('MYSQLHOST') 
            or os.environ.get('MYSQL_HOST')
            or os.environ.get('DB_HOST')
            or 'localhost')
    
    port = int(os.environ.get('MYSQLPORT')
               or os.environ.get('MYSQL_PORT')
               or os.environ.get('DB_PORT')
               or 3306)
    
    user = (os.environ.get('MYSQLUSER')
            or os.environ.get('MYSQL_USER')
            or os.environ.get('DB_USER')
            or 'root')
    
    password = (os.environ.get('MYSQLPASSWORD')
                or os.environ.get('MYSQL_PASSWORD')
                or os.environ.get('DB_PASSWORD')
                or '')
    
    db_name = (os.environ.get('MYSQLDATABASE')
               or os.environ.get('MYSQL_DATABASE')
               or os.environ.get('DB_NAME')
               or 'cinema_caribe')
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': db_name,
        'charset': 'utf8mb4',
        'autocommit': False,
        'connection_timeout': 10,
    }


def execute_sql_file():
    """Ejecuta el archivo database.sql."""
    params = get_connection_params()
    
    print(f"🔧 Inicializando base de datos...")
    print(f"   Host: {params['host']}")
    print(f"   User: {params['user']}")
    print(f"   DB: {params['database']}")
    print()
    
    # Reintentar hasta 3 veces
    for attempt in range(3):
        try:
            conn = mysql.connector.connect(**params)
            cursor = conn.cursor()
            
            print(f"✅ Conexión exitosa (intento {attempt + 1}/3)")
            break
            
        except Error as e:
            print(f"⚠️  Intento {attempt + 1} falló: {e.msg if hasattr(e, 'msg') else str(e)}")
            if attempt < 2:
                print(f"   Reintentando en 3 segundos...")
                time.sleep(3)
            else:
                print(f"\n❌ No se pudo conectar después de 3 intentos.")
                return False
    
    try:
        # Leer el archivo SQL
        with open('database.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir statements (separados por ;)
        statements = []
        current = ""
        
        for line in sql_content.split('\n'):
            # Ignorar comentarios y líneas vacías
            if line.strip().startswith('--') or line.strip() == '':
                continue
            
            current += line + "\n"
            
            if line.rstrip().endswith(';'):
                statements.append(current.strip())
                current = ""
        
        # Ejecutar statements
        total = len(statements)
        executed = 0
        skipped = 0
        
        for idx, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
            
            try:
                # Mostrar progreso
                preview = statement[:50].replace('\n', ' ')
                print(f"[{idx}/{total}] {preview}...", end=' ')
                
                cursor.execute(statement)
                
                # Algunas queries no devuelven rowcount significativo
                rows = cursor.rowcount if cursor.rowcount > -1 else 0
                if rows == 0 and 'CREATE' in statement.upper():
                    print("(créado)")
                    executed += 1
                elif rows > 0:
                    print(f"({rows} filas)")
                    executed += 1
                else:
                    print("(ok)")
                    executed += 1
                    
            except Error as e:
                # Algunos errores son esperados (tablas ya existen, etc.)
                if '1050' in str(e) or 'already exists' in str(e).lower():
                    print("(ya existe)")
                    skipped += 1
                else:
                    print(f"❌ {e.msg if hasattr(e, 'msg') else str(e)}")
        
        conn.commit()
        
        print(f"\n✅ Inicialización completada:")
        print(f"   - {executed} sentencias ejecutadas")
        print(f"   - {skipped} sentencias omitidas (ya existían)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False


def main():
    """Punto de entrada."""
    # Si estamos en desarrollo local, solo avisar
    if os.environ.get('FLASK_ENV') != 'production':
        print("⏭️  Omitiendo inicialización automática (no es producción)")
        return True
    
    # En producción, ejecutar
    success = execute_sql_file()
    
    if not success:
        print("\n⚠️  La base de datos NO se inicializó correctamente.")
        print("   La app podría no funcionar.")
        # No fallar el deployment, dejar que la app intente conectar
        return True
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
