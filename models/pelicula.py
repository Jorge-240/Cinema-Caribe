"""Modelo Pelicula."""
from utils.db import get_db


class Pelicula:

    @staticmethod
    def listar(solo_activas=False):
        db = get_db()
        cur = db.cursor(dictionary=True)
        if solo_activas:
            cur.execute("SELECT * FROM peliculas WHERE estado='activa' ORDER BY id DESC")
        else:
            cur.execute("SELECT * FROM peliculas ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def obtener(pid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM peliculas WHERE id = %s", (pid,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def crear(titulo, descripcion, duracion, genero, clasificacion,
              imagen_url, trailer_url, estado='activa'):
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """INSERT INTO peliculas
               (titulo, descripcion, duracion, genero, clasificacion,
                imagen_url, trailer_url, estado)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (titulo, descripcion, duracion, genero, clasificacion,
             imagen_url, trailer_url, estado)
        )
        db.commit()
        pid = cur.lastrowid
        cur.close()
        return pid

    @staticmethod
    def actualizar(pid, titulo, descripcion, duracion, genero, clasificacion,
                   imagen_url, trailer_url, estado):
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """UPDATE peliculas SET titulo=%s, descripcion=%s, duracion=%s,
               genero=%s, clasificacion=%s, imagen_url=%s,
               trailer_url=%s, estado=%s WHERE id=%s""",
            (titulo, descripcion, duracion, genero, clasificacion,
             imagen_url, trailer_url, estado, pid)
        )
        db.commit()
        cur.close()

    @staticmethod
    def eliminar(pid):
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM peliculas WHERE id = %s", (pid,))
        db.commit()
        cur.close()

    @staticmethod
    def mas_vistas(limite=5):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT p.id, p.titulo, p.imagen_url,
                   COUNT(t.id) AS total_tiquetes,
                   SUM(t.total) AS ingresos
            FROM peliculas p
            LEFT JOIN funciones f ON f.pelicula_id = p.id
            LEFT JOIN tiquetes t ON t.funcion_id = f.id AND t.estado != 'anulado'
            GROUP BY p.id
            ORDER BY total_tiquetes DESC
            LIMIT %s
        """, (limite,))
        rows = cur.fetchall()
        cur.close()
        return rows
