"""
Script para crear/actualizar el usuario admin con la contraseña correcta.
Ejecutar una sola vez: python crear_admin.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from werkzeug.security import generate_password_hash
import mysql.connector

conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST', '127.0.0.1'),
    port=int(os.environ.get('DB_PORT', 3311)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', '1234'),
    database=os.environ.get('DB_NAME', 'cinema_caribe'),
)
cur = conn.cursor()

email = 'admin@cinemacaribe.com'
password = 'admin123'
nombre = 'Administrador'
pw_hash = generate_password_hash(password)

# Si ya existe, actualiza el hash; si no, crea el usuario
cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
row = cur.fetchone()
if row:
    cur.execute("UPDATE usuarios SET password = %s, rol = 'admin' WHERE email = %s", (pw_hash, email))
    print(f"✅ Admin actualizado. Email: {email} | Contraseña: {password}")
else:
    cur.execute(
        "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, 'admin')",
        (nombre, email, pw_hash)
    )
    print(f"✅ Admin creado. Email: {email} | Contraseña: {password}")

conn.commit()
cur.close()
conn.close()
