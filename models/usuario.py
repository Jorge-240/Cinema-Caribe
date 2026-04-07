"""Modelo Usuario."""
from utils.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario:
    def __init__(self, data: dict):
        self.id            = data.get('id')
        self.nombre        = data.get('nombre')
        self.email         = data.get('email')
        self.password      = data.get('password')
        self.rol           = data.get('rol', 'cliente')
        self.fecha_creacion = data.get('fecha_creacion')

    # ---- Flask-Login interface ----
    @property
    def is_authenticated(self): return True
    @property
    def is_active(self): return True
    @property
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

    # ---- Métodos de acceso ----
    @staticmethod
    def obtener_por_id(uid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (uid,))
        row = cur.fetchone()
        cur.close()
        return Usuario(row) if row else None

    @staticmethod
    def obtener_por_email(email):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        return Usuario(row) if row else None

    @staticmethod
    def crear(nombre, email, password, rol='cliente'):
        db = get_db()
        cur = db.cursor()
        pw_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s,%s,%s,%s)",
            (nombre, email, pw_hash, rol)
        )
        uid = cur.lastrowid
        cur.close()
        return uid

    def verificar_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def listar_todos():
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, email, rol, fecha_creacion FROM usuarios ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        return rows
