"""Modelo Asiento."""
from utils.db import get_db


class Asiento:

    @staticmethod
    def listar_por_funcion(funcion_id):
        """Devuelve todos los asientos con su estado para una función."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT a.id, a.numero, a.fila, a.columna,
                   IF(fa.asiento_id IS NOT NULL, 'ocupado', 'disponible') AS estado
            FROM asientos a
            JOIN funciones f ON f.sala_id = a.sala_id AND f.id = %s
            LEFT JOIN funcion_asiento fa
                   ON fa.asiento_id = a.id AND fa.funcion_id = %s
            ORDER BY a.fila, a.columna
        """, (funcion_id, funcion_id))
        rows = cur.fetchall()
        cur.close()
        return rows

    @staticmethod
    def obtener(aid):
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM asientos WHERE id = %s", (aid,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def verificar_disponibles(funcion_id, asiento_ids: list) -> bool:
        """Verifica que ninguno de los asientos esté ocupado en esa función."""
        if not asiento_ids:
            return False
        db = get_db()
        cur = db.cursor()
        fmt = ','.join(['%s'] * len(asiento_ids))
        cur.execute(
            f"SELECT COUNT(*) FROM funcion_asiento "
            f"WHERE funcion_id=%s AND asiento_id IN ({fmt})",
            [funcion_id] + asiento_ids
        )
        count = cur.fetchone()[0]
        cur.close()
        return count == 0
