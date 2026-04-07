#!/usr/bin/env python3
"""
Script para inicializar la base de datos de Cinema Caribe en Railway.
Ejecuta: python init_db.py
"""
import os
import sys
import mysql.connector
from config import config

def init_database():
    """Lee database.sql y ejecuta todos los comandos."""
    
    cfg = config['production']
    
    print(f"🔌 Conectando a MySQL...")
    print(f"   Host: {cfg.DB_HOST}")
    print(f"   User: {cfg.DB_USER}")
    print(f"   Database: {cfg.DB_NAME}")
    
    try:
        conn = mysql.connector.connect(
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD,
            autocommit=False,
            charset='utf8mb4',
        )
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa.\n")
        
        # Leer el archivo SQL
        with open('database.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir por puntos y coma, ignorar comentarios y líneas vacías
        statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            # Ignorar comentarios
            if line.strip().startswith('--') or line.strip() == '':
                continue
            
            current_statement += line + "\n"
            
            # Si la línea termina con ";" es fin de statement
            if line.rstrip().endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Ejecutar todos los statements
        total = len(statements)
        for idx, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"[{idx}/{total}] Ejecutando: {statement[:60]}...")
                    cursor.execute(statement)
                    if cursor.rowcount >= 0:
                        print(f"      ✅ OK (filas afectadas: {cursor.rowcount})")
                except mysql.connector.Error as e:
                    print(f"      ⚠️  {e.msg}")
        
        conn.commit()
        print(f"\n✅ Base de datos inicializada correctamente.")
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()
