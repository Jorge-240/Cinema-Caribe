"""Modelo Funcion."""
from utils.db import get_db
from utils.helpers import fix_row, fix_rows


class Funcion:

    @staticmethod
    def obtener_salas():
        """Obtiene todas las salas disponibles."""
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, filas, cols FROM salas ORDER BY nombre")
        salas = cur.fetchall()
        cur.close()
        return fix_rows(salas) if salas else []

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
            # Mostrar solo funciones programadas que aún no han comenzado.
            conditions.append("f.estado = 'programada'")
            conditions.append("(f.fecha > CURDATE() OR (f.fecha = CURDATE() AND f.hora > CURTIME()))")
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
                    TIMESTAMP(fecha, hora),
                    TIMESTAMP(%s, %s))) < (
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
        try:
            # Eliminar primero relaciones de asientos y luego tickets para evitar errores de FK
            cur.execute("DELETE FROM funcion_asiento WHERE funcion_id = %s", (fid,))
            cur.execute("DELETE FROM tiquetes WHERE funcion_id = %s", (fid,))
            cur.execute("DELETE FROM funciones WHERE id = %s", (fid,))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
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

    @staticmethod
    def actualizar_estados_automaticos():
        """
        Actualiza estados de funciones automáticamente:
        - programada -> en_curso (cuando llega la hora)
        - en_curso -> finalizada (cuando termina la película)
        
        Debe ejecutarse periódicamente (cada 5 minutos aproximadamente).
        """
        from datetime import datetime, timedelta
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            ahora = datetime.now()
            
            # 1. Actualizar funciones que deben cambiar a EN_CURSO
            cur.execute("""
                SELECT f.id, f.fecha, f.hora, p.duracion
                FROM funciones f
                JOIN peliculas p ON p.id = f.pelicula_id
                WHERE f.estado = 'programada'
                AND TIMESTAMP(f.fecha, f.hora) <= %s
                AND DATE_ADD(TIMESTAMP(f.fecha, f.hora), INTERVAL p.duracion MINUTE) > %s
            """, (ahora, ahora))
            
            funciones_curso = cur.fetchall()
            ids_curso = [f['id'] for f in funciones_curso]
            
            if ids_curso:
                fmt = ','.join(['%s'] * len(ids_curso))
                cur.execute(f"UPDATE funciones SET estado='en_curso' WHERE id IN ({fmt})", ids_curso)
            
            # 2. Actualizar funciones que deben cambiar a FINALIZADA
            cur.execute("""
                SELECT f.id, f.fecha, f.hora, p.duracion
                FROM funciones f
                JOIN peliculas p ON p.id = f.pelicula_id
                WHERE f.estado = 'en_curso'
                AND DATE_ADD(TIMESTAMP(f.fecha, f.hora), INTERVAL p.duracion MINUTE) <= %s
            """, (ahora,))
            
            funciones_fin = cur.fetchall()
            ids_fin = [f['id'] for f in funciones_fin]
            
            if ids_fin:
                fmt = ','.join(['%s'] * len(ids_fin))
                cur.execute(f"UPDATE funciones SET estado='finalizada' WHERE id IN ({fmt})", ids_fin)
            
            db.commit()
            return len(ids_curso), len(ids_fin)
        finally:
            cur.close()

    @staticmethod
    def mover_finalizadas_a_historial():
        """
        Mueve funciones finalizadas al historial y las elimina de la tabla activa.
        Solo se mueven si tienen datos completos.
        
        Debe ejecutarse periódicamente (cada 1 a 24 horas).
        """
        from datetime import datetime
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            # 1. Obtener funciones finalizadas
            cur.execute("""
                SELECT f.id, f.pelicula_id, f.sala_id, f.fecha, f.hora, 
                       f.precio, p.duracion, p.titulo, s.nombre,
                       COUNT(t.id) AS cantidad_tiquetes,
                       COALESCE(SUM(t.total), 0) AS ingresos_totales
                FROM funciones f
                JOIN peliculas p ON p.id = f.pelicula_id
                JOIN salas s ON s.id = f.sala_id
                LEFT JOIN tiquetes t ON t.funcion_id = f.id AND t.estado IN ('usado', 'valido')
                WHERE f.estado = 'finalizada'
                GROUP BY f.id
            """)
            
            funciones = cur.fetchall()
            movidas = 0
            
            for f in funciones:
                try:
                    # 2. Insertar en historial
                    cur.execute("""
                        INSERT INTO historial_funciones 
                        (pelicula_id, sala_id, fecha_original, hora_original, precio,
                         cantidad_tiquetes, ingresos_totales, duracion_pelicula,
                         fecha_finalizacion, pelicula_titulo, sala_nombre)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        f['pelicula_id'], f['sala_id'], f['fecha'], f['hora'],
                        f['precio'], f['cantidad_tiquetes'], f['ingresos_totales'],
                        f['duracion'], datetime.now(), f['titulo'], f['nombre']
                    ))
                    
                    # 3. Eliminar de funciones
                    cur.execute("DELETE FROM funciones WHERE id = %s", (f['id'],))
                    
                    db.commit()
                    movida = True
                except Exception as e:
                    db.rollback()
                    print(f"Error moviendo función {f['id']}: {e}")
                    movida = False
                
                if movida:
                    movidas += 1
            
            return movidas
        finally:
            cur.close()
