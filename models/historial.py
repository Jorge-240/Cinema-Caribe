"""Modelo Historial de Funciones."""
from utils.db import get_db
from utils.helpers import fix_row, fix_rows


class HistorialFuncion:
    """Gestiona el historial de funciones finalizadas."""

    @staticmethod
    def listar(pelicula_id=None, fecha_desde=None, fecha_hasta=None, limite=100):
        """
        Lista funciones del historial.
        
        Args:
            pelicula_id: filtrar por película
            fecha_desde: filtrar funciones desde esta fecha
            fecha_hasta: filtrar funciones hasta esta fecha
            limite: cantidad máxima de registros
        """
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        sql = """
            SELECT * FROM historial_funciones
            WHERE 1=1
        """
        params = []
        
        if pelicula_id:
            sql += " AND pelicula_id = %s"
            params.append(pelicula_id)
        
        if fecha_desde:
            sql += " AND fecha_original >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            sql += " AND fecha_original <= %s"
            params.append(fecha_hasta)
        
        sql += f" ORDER BY fecha_original DESC, hora_original DESC LIMIT {limite}"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def obtener(id):
        """Obtiene el detalle de una función del historial."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM historial_funciones WHERE id = %s", (id,))
        row = cur.fetchone()
        cur.close()
        return fix_row(row)

    @staticmethod
    def stats_general():
        """Obtiene estadísticas generales del historial."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                COUNT(*) AS total_funciones,
                COALESCE(SUM(cantidad_tiquetes), 0) AS total_espectadores,
                COALESCE(SUM(ingresos_totales), 0) AS ingresos_totales,
                COALESCE(AVG(cantidad_tiquetes), 0) AS promedio_espectadores,
                COALESCE(AVG(ingresos_totales), 0) AS promedio_ingresos,
                MIN(fecha_original) AS fecha_mas_antigua,
                MAX(fecha_original) AS fecha_mas_reciente
            FROM historial_funciones
        """)
        row = cur.fetchone()
        cur.close()
        return fix_row(row)

    @staticmethod
    def stats_por_pelicula():
        """Obtiene estadísticas agrupadas por película."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                pelicula_id,
                pelicula_titulo,
                COUNT(*) AS funciones_realizadas,
                COALESCE(SUM(cantidad_tiquetes), 0) AS total_espectadores,
                COALESCE(SUM(ingresos_totales), 0) AS ingresos_totales,
                COALESCE(AVG(cantidad_tiquetes), 0) AS promedio_espectadores_por_funcion,
                COALESCE(AVG(ingresos_totales), 0) AS promedio_ingresos_por_funcion
            FROM historial_funciones
            GROUP BY pelicula_id, pelicula_titulo
            ORDER BY ingresos_totales DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def stats_por_sala():
        """Obtiene estadísticas agrupadas por sala."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                sala_id,
                sala_nombre,
                COUNT(*) AS funciones_realizadas,
                COALESCE(SUM(cantidad_tiquetes), 0) AS total_espectadores,
                COALESCE(SUM(ingresos_totales), 0) AS ingresos_totales
            FROM historial_funciones
            GROUP BY sala_id, sala_nombre
            ORDER BY ingresos_totales DESC
        """)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def stats_por_fecha_rango(fecha_desde, fecha_hasta):
        """Obtiene estadísticas en un rango de fechas."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                DATE(fecha_original) AS fecha,
                COUNT(*) AS funciones,
                COALESCE(SUM(cantidad_tiquetes), 0) AS espectadores,
                COALESCE(SUM(ingresos_totales), 0) AS ingresos
            FROM historial_funciones
            WHERE fecha_original BETWEEN %s AND %s
            GROUP BY DATE(fecha_original)
            ORDER BY fecha_original DESC
        """, (fecha_desde, fecha_hasta))
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)

    @staticmethod
    def reporte_detallado(pelicula_id=None, sala_id=None):
        """Genera un reporte detallado del historial."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        sql = """
            SELECT
                h.*,
                CONCAT(h.fecha_original, ' ', h.hora_original) AS fecha_hora_original,
                TIMEDIFF(h.fecha_finalizacion, CONCAT(h.fecha_original, ' ', h.hora_original)) AS tiempo_real_duracion
            FROM historial_funciones h
            WHERE 1=1
        """
        params = []
        
        if pelicula_id:
            sql += " AND h.pelicula_id = %s"
            params.append(pelicula_id)
        
        if sala_id:
            sql += " AND h.sala_id = %s"
            params.append(sala_id)
        
        sql += " ORDER BY h.fecha_original DESC"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return fix_rows(rows)
