#!/usr/bin/env python
"""Script para agregar campo nombre_cliente a la tabla tiquetes"""

from app import create_app
from utils.db import get_db

# Crear contexto de aplicación
app = create_app()

with app.app_context():
    db = get_db()
    cur = db.cursor()
    try:
        # Verificar si el campo ya existe
        cur.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME='tiquetes' AND COLUMN_NAME='nombre_cliente'
        """)
        if cur.fetchone():
            print("✓ Campo nombre_cliente ya existe en tiquetes")
        else:
            # Agregar el campo si no existe
            cur.execute("""
                ALTER TABLE tiquetes 
                ADD COLUMN nombre_cliente VARCHAR(120) DEFAULT NULL
            """)
            db.commit()
            print("✓ Campo nombre_cliente agregado exitosamente a tiquetes")
    except Exception as e:
        print(f"✗ Error al agregar campo: {e}")
    finally:
        cur.close()
