"""
Utilidad de conexión a MySQL — lazy initialization.
El pool se crea en el primer request, NO al arrancar la app.
Esto evita crashes en Railway cuando la BD todavía no está lista.
"""
import mysql.connector
from mysql.connector import pooling
from flask import current_app, g
import time

_pool = None


def get_pool(app=None):
    global _pool
    if _pool is not None:
        return _pool

    cfg = app.config if app else current_app.config

    # Reintentar hasta 5 veces con backoff (útil en Railway al arrancar)
    last_err = None
    for attempt in range(5):
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="cinema_caribe",
                pool_size=5,
                host=cfg['DB_HOST'],
                port=int(cfg['DB_PORT']),
                user=cfg['DB_USER'],
                password=cfg['DB_PASSWORD'],
                database=cfg['DB_NAME'],
                charset='utf8mb4',
                autocommit=True,
                connection_timeout=10,
            )
            return _pool
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)   # 1s, 2s, 4s, 8s, 16s

    raise RuntimeError(f"No se pudo conectar a MySQL después de 5 intentos: {last_err}")


def get_db():
    """Obtiene (o reutiliza) la conexión del request actual."""
    if 'db' not in g:
        try:
            pool = get_pool()
            g.db = pool.get_connection()
        except RuntimeError as e:
            # Log pero no crashear - devolver None para que routes maneje
            from flask import current_app
            current_app.logger.error(f"No se pudo conectar a BD: {e}")
            raise Exception(f"Base de datos no disponible: {str(e)}")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Registra teardown; NO conecta en startup."""
    app.teardown_appcontext(close_db)
    # ⚠️ NO llamamos get_pool() aquí — conexión lazy en primer request
