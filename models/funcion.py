"""Modelo Funcion."""
from utils.db import get_db
from utils.helpers import fix_row, fix_rows


class Funcion:

    @staticmethod
    def listar(pelicula_id=None, solo_futuras=False):
        db = get_db()
        cur = db.cursor(dictionary=True)
        sql = """
            SELECT f.*, p.titulo AS pelicula_titulo,
                   p.imagen_url, p.duracion, p.clasificacion,
                   s.nombre AS sala_nombre,
                   CONCAT(f.fecha, ' ', f.hora) AS fecha_hora
            FROM funciones f
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN salas s ON s.id = f.sala_id
        """
        params = []
        conditions = []
        if pelicula_id:
            conditions.append("f.pelicula_id = %s")
            params.append(pelicula_id)
        if solo_futuras:
            conditions.append("CONCAT(f.fecha,' ',f.hora) >= NOW()")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY f.fecha, f.hora"
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def obtener(fid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT f.*, p.titulo AS pelicula_titulo,
                   p.imagen_url, p.descripcion AS pelicula_descripcion,
                   p.duracion, p.clasificacion, p.genero,
                   s.nombre AS sala_nombre, s.filas, s.cols
            FROM funciones f
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN salas s ON s.id = f.sala_id
            WHERE f.id = %s
        """, (fid,))
        row = cur.fetchone()
        cur.close()
        return fix_row(row)

    @staticmethod
    def verificar_choque(sala_id, fecha, hora, pelicula_id, funcion_id=None):
        db = get_db()
        cur = db.cursor()
        query = """
            SELECT id FROM funciones
            WHERE sala_id = %s AND fecha = %s AND estado != 'cancelada'
              AND ABS(TIMESTAMPDIFF(MINUTE,
                    CONCAT(fecha,' ',hora),
                    CONCAT(%s,' ',%s))) < (
                      SELECT duracion FROM peliculas WHERE id=%s
                  )
        """
        params = [sala_id, fecha, fecha, hora, pelicula_id]
        if funcion_id:
            query += " AND id != %s"
            params.append(funcion_id)
        cur.execute(query, params)
        res = cur.fetchone()
        cur.close()
        if res:
            raise ValueError("Horario no disponible. Ya existe una función programada en esta misma sala para la fecha y hora seleccionadas (existe un choque).")

    @staticmethod
    def crear(pelicula_id, sala_id, fecha, hora, precio, estado='programada'):
        Funcion.verificar_choque(sala_id, fecha, hora, pelicula_id)
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """INSERT INTO funciones
               (pelicula_id, sala_id, fecha, hora, precio, estado)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (pelicula_id, sala_id, fecha, hora, precio, estado)
        )
        db.commit()
        fid = cur.lastrowid
        cur.close()
        return fid

    @staticmethod
    def actualizar_estado(fid, estado):
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE funciones SET estado=%s WHERE id=%s", (estado, fid))
        db.commit()
        cur.close()

    @staticmethod
    def actualizar(fid, pelicula_id, sala_id, fecha, hora, precio, estado):
        Funcion.verificar_choque(sala_id, fecha, hora, pelicula_id, fid)
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            UPDATE funciones
            SET pelicula_id=%s, sala_id=%s, fecha=%s, hora=%s, precio=%s, estado=%s
            WHERE id=%s
        """, (pelicula_id, sala_id, fecha, hora, precio, estado, fid))
        db.commit()
        cur.close()

    @staticmethod
    def eliminar(fid):
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM funciones WHERE id = %s", (fid,))
        db.commit()
        cur.close()

    @staticmethod
    def ocupacion(fid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT s.filas * s.cols AS total_asientos,
                   COUNT(fa.asiento_id) AS ocupados
            FROM funciones f
            JOIN salas s ON s.id = f.sala_id
            LEFT JOIN funcion_asiento fa ON fa.funcion_id = f.id
            WHERE f.id = %s
        """, (fid,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def stats_admin():
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT f.id, f.fecha, f.hora, f.precio,
                   p.titulo AS pelicula,
                   s.nombre AS sala,
                   COUNT(fa.asiento_id) AS ocupados,
                   (s.filas * s.cols) AS total_asientos,
                   COALESCE(SUM(t.total),0) AS ingresos
            FROM funciones f
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN salas s ON s.id = f.sala_id
            LEFT JOIN funcion_asiento fa ON fa.funcion_id = f.id
            LEFT JOIN tiquetes t ON t.funcion_id = f.id AND t.estado != 'anulado'
            GROUP BY f.id
            ORDER BY f.fecha DESC, f.hora DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)
