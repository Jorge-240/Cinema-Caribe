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
        cur = db.cursor(dictionary=True)
        try:
            # 0. Verificar que la función esté disponible para venta.
            from datetime import datetime, timedelta
            from utils.timezone import now_colombia
            cur.execute(
                "SELECT f.fecha, f.hora, f.estado, p.duracion "
                "FROM funciones f "
                "JOIN peliculas p ON p.id = f.pelicula_id "
                "WHERE f.id = %s",
                (funcion_id,)
            )
            funcion = cur.fetchone()
            if not funcion:
                raise ValueError('Función inválida.')

            def parse_date_or_time(value, mode='date'):
                if value is None:
                    raise ValueError('Fecha u hora inválida')
                if mode == 'date' and hasattr(value, 'year'):
                    return value
                if mode == 'time' and hasattr(value, 'hour'):
                    return value
                # MySQL TIME fields come as timedelta — convert to time object
                if isinstance(value, timedelta):
                    total_seconds = int(value.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    from datetime import time as dt_time
                    return dt_time(hours % 24, minutes, seconds)
                text = str(value)
                formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'] if mode == 'date' else ['%H:%M:%S', '%H:%M']
                for fmt in formats:
                    try:
                        parsed = datetime.strptime(text, fmt)
                        return parsed.date() if mode == 'date' else parsed.time()
                    except ValueError:
                        continue
                raise ValueError(f'Formato de {mode} no válido: {text}')

            fecha_obj = parse_date_or_time(funcion['fecha'], mode='date')
            hora_obj = parse_date_or_time(funcion['hora'], mode='time')
            inicio_funcion = datetime.combine(fecha_obj, hora_obj)
            fin_funcion = inicio_funcion + timedelta(minutes=funcion['duracion'])
            ahora = now_colombia()

            if funcion['estado'] == 'cancelada':
                raise ValueError('No se pueden comprar entradas para una función cancelada.')
            if ahora >= inicio_funcion:
                raise ValueError('No se pueden comprar entradas para esta función porque ya ha iniciado.')
            if funcion['estado'] not in ('programada', 'en_curso'):
                raise ValueError('La función no está disponible para compra en este momento.')

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

            # 3. Crear tiquete con estado inicial 'inhabilitado'
            # Se habilitará 25 min antes de que inicie la función
            try:
                cur.execute(
                    "INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total, estado, nombre_cliente)"
                    " VALUES (%s,%s,%s,%s,'inhabilitado',%s)",
                    (codigo, usuario_id, funcion_id, total, nombre_cliente)
                )
            except Exception as e:
                msg = str(e)
                if 'Unknown column' in msg or '1054' in msg:
                    cur.execute(
                        "INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total, estado)"
                        " VALUES (%s,%s,%s,%s,'inhabilitado')",
                        (codigo, usuario_id, funcion_id, total)
                    )
                elif 'Data truncated for column' in msg and 'estado' in msg:
                    cur.execute(
                        "INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total, nombre_cliente)"
                        " VALUES (%s,%s,%s,%s,%s)",
                        (codigo, usuario_id, funcion_id, total, nombre_cliente)
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
            "UPDATE tiquetes SET estado='anulado' WHERE id=%s AND estado IN ('valido','inhabilitado')",
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

    @staticmethod
    def validar_con_ventana_25_min(codigo):
        """
        Valida un ticket según la ventana de 25 minutos.
        
        Retorna diccionario con:
        - valid: bool (True si se puede validar)
        - status: 'temprano', 'valido', 'tarde' o 'no_encontrado'
        - mensaje: mensaje descriptivo
        - tiquete: datos del tiquete
        """
        from datetime import datetime, timedelta
        from utils.timezone import now_colombia
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # Obtener datos del tiquete y función
        cur.execute("""
            SELECT t.*, f.fecha, f.hora, f.estado AS funcion_estado,
                   p.duracion, p.titulo AS pelicula_titulo,
                   u.nombre AS usuario_nombre,
                   s.nombre AS sala_nombre
            FROM tiquetes t
            JOIN funciones f ON f.id = t.funcion_id
            JOIN peliculas p ON p.id = f.pelicula_id
            JOIN usuarios u ON u.id = t.usuario_id
            JOIN salas s ON s.id = f.sala_id
            WHERE t.codigo = %s
        """, (codigo,))
        
        resultado = cur.fetchone()
        cur.close()
        
        if not resultado:
            return {
                'valid': False,
                'status': 'no_encontrado',
                'mensaje': 'Ticket no encontrado.',
                'tiquete': None
            }
        
        # Verificar si ya fue validado
        if resultado['estado'] == 'usado':
            return {
                'valid': False,
                'status': 'ya_usado',
                'mensaje': 'Este ticket ya fue validado y utilizado.',
                'tiquete': resultado
            }
        
        if resultado['estado'] == 'anulado':
            return {
                'valid': False,
                'status': 'anulado',
                'mensaje': 'Este ticket ha sido anulado.',
                'tiquete': resultado
            }
        
        # Calcular horarios
        fecha_val = resultado['fecha']
        hora_val = resultado['hora']
        duracion_min = resultado['duracion']

        def parse_date_or_time(value, mode='date'):
            if value is None:
                raise ValueError('Fecha u hora inválida')
            if mode == 'date' and hasattr(value, 'year'):
                return value
            if mode == 'time' and hasattr(value, 'hour'):
                return value
            # MySQL TIME fields come as timedelta — convert to time object
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                from datetime import time as dt_time
                return dt_time(hours % 24, minutes, seconds)
            text = str(value)
            formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'] if mode == 'date' else ['%H:%M:%S', '%H:%M']
            for fmt in formats:
                try:
                    parsed = datetime.strptime(text, fmt)
                    return parsed.date() if mode == 'date' else parsed.time()
                except ValueError:
                    continue
            raise ValueError(f'Formato de {mode} no válido: {text}')

        fecha_obj = parse_date_or_time(fecha_val, mode='date')
        hora_obj = parse_date_or_time(hora_val, mode='time')
        inicio_funcion = datetime.combine(fecha_obj, hora_obj)
        
        # Ventana de 25 minutos antes
        inicio_ventana = inicio_funcion - timedelta(minutes=25)
        fin_ventana = inicio_funcion
        
        # Fin de la función (por si termina después de iniciar)
        fin_funcion = inicio_funcion + timedelta(minutes=duracion_min)
        
        # Hora actual
        ahora = now_colombia()
        
        # Determinar estado
        if resultado['funcion_estado'] == 'cancelada':
            return {
                'valid': False,
                'status': 'funcion_cancelada',
                'mensaje': 'La función ha sido cancelada.',
                'tiquete': resultado
            }
        
        if ahora < inicio_ventana:
            # Aún es temprano - ticket no habilitado
            minutos_falta = int((inicio_ventana - ahora).total_seconds() / 60)
            return {
                'valid': False,
                'status': 'temprano',
                'mensaje': f'El ticket se habilitará en {minutos_falta} minutos.',
                'estado': 'inhabilitado',
                'tiquete': resultado,
                'minutos_para_habilitar': minutos_falta
            }
        
        if ahora < fin_ventana:
            # Dentro de la ventana válida de 25 minutos
            return {
                'valid': True,
                'status': 'valido',
                'mensaje': f'¡Ticket válido! Puedes acceder a la función {resultado["pelicula_titulo"]} en la sala {resultado["sala_nombre"]}.',
                'tiquete': resultado
            }
        
        if ahora >= fin_ventana and ahora < fin_funcion:
            # La película ya comenzó pero aún no termina - ticket inválido pero en horario
            return {
                'valid': False,
                'status': 'tarde',
                'mensaje': 'La función ya ha iniciado. No se puede validar tickets después del inicio.',
                'tiquete': resultado
            }
        
        if ahora >= fin_funcion:
            # La función ya terminó
            return {
                'valid': False,
                'status': 'tarde',
                'mensaje': 'La función ya ha finalizado.',
                'tiquete': resultado
            }
        
        # Fallback: caso no cubierto (no debería ocurrir, pero previene retorno None → 500)
        return {
            'valid': False,
            'status': 'tarde',
            'mensaje': 'No se puede validar el ticket en este momento.',
            'tiquete': resultado
        }

    @staticmethod
    def marcar_validado(codigo):
        """Marca un ticket como 'usado' y registra la fecha/hora de validación."""
        db = get_db()
        cur = db.cursor()
        try:
            from utils.timezone import now_colombia
            ahora = now_colombia()
            # Intentar con columnas extendidas primero; si fallan, usar solo 'estado'
            try:
                cur.execute(
                    """UPDATE tiquetes 
                       SET estado='usado', fecha_validacion=%s, fue_validado=TRUE 
                       WHERE codigo=%s AND estado IN ('valido','inhabilitado')""",
                    (ahora, codigo)
                )
            except Exception as e:
                msg = str(e)
                if 'Unknown column' in msg or '1054' in msg:
                    cur.execute(
                        "UPDATE tiquetes SET estado='usado' WHERE codigo=%s AND estado IN ('valido','inhabilitado')",
                        (codigo,)
                    )
                else:
                    raise
            db.commit()
            afectados = cur.rowcount
            return afectados > 0
        finally:
            cur.close()

    @staticmethod
    def habilitar_tickets_ventana():
        """
        Habilita tickets de funciones que están a menos de 25 minutos del inicio.
        Debe ejecutarse periodicamente (cada 1-5 min).
        """
        from datetime import datetime, timedelta
        from utils.timezone import now_colombia
        
        db = get_db()
        cur = db.cursor()
        try:
            ahora = now_colombia()
            ventana_min = ahora + timedelta(minutes=25)
            ventana_max = ahora + timedelta(minutes=26)
            
            # Encontrar funciones que comienzan en los próximos 25 minutos
            cur.execute("""
                SELECT id FROM funciones
                WHERE estado = 'programada'
                AND CONCAT(fecha, ' ', hora) BETWEEN %s AND %s
            """, (ahora, ventana_max))
            
            funciones = cur.fetchall()
            funciones_ids = [f[0] for f in funciones]
            
            if funciones_ids:
                fmt = ','.join(['%s'] * len(funciones_ids))
                cur.execute(f"""
                    UPDATE tiquetes
                    SET estado='valido'
                    WHERE funcion_id IN ({fmt})
                    AND estado='inhabilitado'
                """, funciones_ids)
                db.commit()
                return cur.rowcount
            
            return 0
        finally:
            cur.close()
