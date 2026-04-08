"""Modelo Tiquete."""
from utils.db import get_db
from utils.helpers import generar_codigo, guardar_qr, fix_row, fix_rows
import os


class Tiquete:

    @staticmethod
    def crear(usuario_id, funcion_id, asiento_ids: list, precio_unitario: float,
              qr_folder: str, nombre_cliente: str = None):
        """
        Crea un tiquete de forma atómica con transacción.
        Lanza ValueError si algún asiento ya está ocupado.
        """
        db = get_db()
        cur = db.cursor()
        try:
            # 1. Bloquear filas para evitar race-condition
            fmt = ','.join(['%s'] * len(asiento_ids))
            cur.execute(
                f"SELECT asiento_id FROM funcion_asiento "
                f"WHERE funcion_id=%s AND asiento_id IN ({fmt}) FOR UPDATE",
                [funcion_id] + asiento_ids
            )
            if cur.fetchone():
                raise ValueError("Uno o más asientos ya fueron vendidos. Selecciona otros.")

            # 2. Calcular total
            total = precio_unitario * len(asiento_ids)
            codigo = generar_codigo()

            # 3. Crear tiquete
            try:
                cur.execute(
                    """INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total, estado, nombre_cliente)
                       VALUES (%s,%s,%s,%s,'valido',%s)""",
                    (codigo, usuario_id, funcion_id, total, nombre_cliente)
                )
            except Exception as e:
                # En caso de que la tabla no tenga la columna nombre_cliente aún,
                # seguir con la inserción sin ese campo para que la compra no falle.
                if 'Unknown column' in str(e) or '1054' in str(e):
                    cur.execute(
                        "INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total, estado)"
                        " VALUES (%s,%s,%s,%s,'valido')",
                        (codigo, usuario_id, funcion_id, total)
                    )
                else:
                    raise
            tiquete_id = cur.lastrowid

            # 4. Detalles + bloqueo de asientos
            for aid in asiento_ids:
                cur.execute(
                    "INSERT INTO detalle_tiquete (tiquete_id, asiento_id, precio_unitario) VALUES (%s,%s,%s)",
                    (tiquete_id, aid, precio_unitario)
                )
                cur.execute(
                    "INSERT INTO funcion_asiento (funcion_id, asiento_id, tiquete_id) VALUES (%s,%s,%s)",
                    (funcion_id, aid, tiquete_id)
                )

            # 5. Generar QR
            qr_path = guardar_qr(codigo, qr_folder, codigo)
            cur.execute("UPDATE tiquetes SET qr_path=%s WHERE id=%s",
                        (f"static/img/qr/{codigo}.png", tiquete_id))

            db.commit()
            return tiquete_id, codigo

        except Exception:
            db.rollback()
            raise
        finally:
            cur.close()

    @staticmethod
    def obtener(tid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT t.*, u.nombre AS usuario_nombre, u.email AS usuario_email,
                   f.fecha, f.hora, f.precio AS precio_funcion,
                   p.titulo AS pelicula_titulo, p.imagen_url,
                   s.nombre AS sala_nombre
            FROM tiquetes t
            JOIN usuarios u ON u.id = t.usuario_id
            JOIN funciones f ON f.id = t.funcion_id
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN salas s ON s.id = f.sala_id
            WHERE t.id = %s
        """, (tid,))
        row = cur.fetchone()
        cur.close()
        return fix_row(row)

    @staticmethod
    def obtener_por_codigo(codigo):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT t.*, u.nombre AS usuario_nombre, u.email AS usuario_email,
                   f.fecha, f.hora,
                   p.titulo AS pelicula_titulo,
                   s.nombre AS sala_nombre
            FROM tiquetes t
            JOIN usuarios u ON u.id = t.usuario_id
            JOIN funciones f ON f.id = t.funcion_id
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN salas s ON s.id = f.sala_id
            WHERE t.codigo = %s
        """, (codigo,))
        row = cur.fetchone()
        cur.close()
        return fix_row(row)

    @staticmethod
    def obtener_detalles(tiquete_id):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT dt.*, a.numero AS asiento_numero, a.fila, a.columna
            FROM detalle_tiquete dt
            JOIN asientos a ON a.id = dt.asiento_id
            WHERE dt.tiquete_id = %s
        """, (tiquete_id,))
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def marcar_usado(codigo):
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE tiquetes SET estado='usado' WHERE codigo=%s AND estado='valido'",
            (codigo,)
        )
        afectados = cur.rowcount
        db.commit()
        cur.close()
        return afectados > 0

    @staticmethod
    def marcar_anulado(tiquete_id):
        """Marca un tiquete como anulado (solo si está válido)."""
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE tiquetes SET estado='anulado' WHERE id=%s AND estado='valido'",
            (tiquete_id,)
        )
        afectados = cur.rowcount
        db.commit()
        cur.close()
        return afectados > 0

    @staticmethod
    def listar_usuario(usuario_id):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT t.*, p.titulo AS pelicula_titulo,
                   f.fecha, f.hora, p.imagen_url
            FROM tiquetes t
            JOIN funciones f ON f.id = t.funcion_id
            JOIN peliculas p ON p.id = f.pelicula_id
            WHERE t.usuario_id = %s
            ORDER BY t.fecha_compra DESC
        """, (usuario_id,))
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def stats_admin():
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                COUNT(*) AS total_tiquetes,
                COALESCE(SUM(total),0) AS ingresos_totales,
                COUNT(CASE WHEN estado='valido' THEN 1 END) AS validos,
                COUNT(CASE WHEN estado='usado' THEN 1 END) AS usados,
                COUNT(CASE WHEN estado='anulado' THEN 1 END) AS anulados
            FROM tiquetes
        """)
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def listar_todos():
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT t.*, u.nombre AS usuario_nombre, p.titulo AS pelicula_titulo,
                   f.fecha, f.hora, p.imagen_url
            FROM tiquetes t
            JOIN usuarios u ON u.id = t.usuario_id
            JOIN funciones f ON f.id = t.funcion_id
            JOIN peliculas p ON p.id = f.pelicula_id
            ORDER BY t.fecha_compra DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)
