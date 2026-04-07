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

# Update ENUM type for roles to include the two new ones
cur.execute("ALTER TABLE usuarios MODIFY COLUMN rol ENUM('admin','cliente','taquilla','validador') NOT NULL DEFAULT 'cliente'")

users = [
    ('Taquilla', 'taquilla@cinemacaribe.com', generate_password_hash('taquilla123'), 'taquilla'),
    ('Validador', 'validador@cinemacaribe.com', generate_password_hash('validador123'), 'validador')
]

for nombre, email, pwhash, rol in users:
    cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    if cur.fetchone():
        cur.execute("UPDATE usuarios SET password=%s, rol=%s WHERE email=%s", (pwhash, rol, email))
        print(f"✅ Actualizado: {email}")
    else:
        cur.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)", (nombre, email, pwhash, rol))
        print(f"✅ Creado: {email}")

conn.commit()
cur.close()
conn.close()
print("Roles and users setup complete.")
