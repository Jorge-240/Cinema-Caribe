"""
Cinema Caribe - Punto de entrada principal.
Ejecutar: python app.py
Sin venv: Se ejecuta directamente en Railway o en el sistema.
"""
from flask import Flask, render_template, session, jsonify
from config import config
from utils import db as db_utils
import os
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(env='default'):
    try:
        app = Flask(__name__)
        app.config.from_object(config[env])

        # Registrar teardown de BD (conexión LAZY — no conecta al arrancar)
        db_utils.init_app(app)

        # Health-check para Railway (ANTES de blueprints, no requiere BD)
        @app.route('/health')
        def health():
            return jsonify({'status': 'ok', 'version': '1.0'}), 200

        # Debug endpoint
        @app.route('/debug')
        def debug_info():
            data = {
                'app_running': True,
                'environment': os.environ.get('FLASK_ENV'),
                'db_host': app.config.get('DB_HOST'),
                'db_user': app.config.get('DB_USER'),
                'db_name': app.config.get('DB_NAME'),
                'railway_env': os.environ.get('RAILWAY_ENVIRONMENT'),
            }
            return jsonify(data), 200

        # Setup endpoint - verificar e inicializar BD si es necesario
        @app.route('/setup')
        def setup_db():
            try:
                from utils.db import get_pool
                pool = get_pool(app)
                conn = pool.get_connection()
                cur = conn.cursor()
                
                # Verificar si existen las tablas principales
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME IN ('peliculas', 'funciones', 'usuarios', 'tiquetes')
                """, (app.config.get('DB_NAME'),))
                
                existing_tables = cur.fetchone()[0]
                cur.close()
                conn.close()
                
                if existing_tables >= 4:
                    return jsonify({
                        'status': 'ready',
                        'message': 'Base de datos inicializada correctamente',
                        'tables_found': existing_tables
                    }), 200
                else:
                    return jsonify({
                        'status': 'needs_init',
                        'message': f'Base de datos necesita inicialización. Tablas encontradas: {existing_tables}/4',
                        'action': 'Por favor contacta al administrador para ejecutar: python init_db.py'
                    }), 503
                    
            except Exception as e:
                logger.error(f"Error en setup: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        # Initialize endpoint - crear tablas si no existen
        @app.route('/initialize', methods=['GET', 'POST'])
        def initialize_database():
            try:
                import mysql.connector
                
                # Conectar a la BD especificada
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),  # Conectar a la BD directamente
                    autocommit=True,
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor()
                executed_count = 0
                
                # Leer el archivo SQL
                sql_file = os.path.join(os.path.dirname(__file__), 'database.sql')
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Reemplazar referencias a "cinema_caribe" con la BD actual
                db_name = app.config.get('DB_NAME')
                sql_content = sql_content.replace('cinema_caribe', db_name)
                sql_content = sql_content.replace('CREATE DATABASE IF NOT EXISTS', '-- CREATE DATABASE IF NOT EXISTS')
                
                # Ejecutar cada comando SQL
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                            executed_count += 1
                            logger.info(f"✅ SQL: {statement[:50]}...")
                        except Exception as e:
                            if 'already exists' in str(e).lower():
                                logger.info(f"ℹ️  Table ya existe: {e}")
                            else:
                                logger.warning(f"⚠️  SQL error: {e}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'message': f'Base de datos {db_name} inicializada',
                    'statements_executed': executed_count,
                    'database': db_name
                }), 200
                
            except Exception as e:
                logger.error(f"Error inicializando BD: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'database': app.config.get('DB_NAME')
                }), 500

        # Blueprints - envoltos en try-catch para evitar crashear en startup
        try:
            from routes.main     import main_bp
            from routes.auth     import auth_bp
            from routes.tiquetes import tiquetes_bp
            from routes.admin    import admin_bp

            app.register_blueprint(main_bp)
            app.register_blueprint(auth_bp)
            app.register_blueprint(tiquetes_bp)
            app.register_blueprint(admin_bp)
        except Exception as e:
            logger.error(f"Error al registrar blueprints: {e}")
            # La app aún puede servir el /health

        # Context processor: datos de sesión disponibles en todos los templates
        @app.context_processor
        def inject_user():
            return {
                'usuario_id':     session.get('usuario_id'),
                'usuario_nombre': session.get('usuario_nombre'),
                'usuario_rol':    session.get('rol')
            }

        # Manejadores de error
        @app.errorhandler(404)
        def not_found(e):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def server_error(e):
            logger.error(f"Error 500: {str(e)}", exc_info=True)
            
            # Si es error de conexión a BD, mostrar mensaje amigable
            if 'mysql' in str(e).lower() or 'database' in str(e).lower() or 'connection' in str(e).lower():
                return render_template('errors/500.html', 
                                       error_msg='Error de conexión a la base de datos. Por favor intenta más tarde.'), 500
            
            return render_template('errors/500.html', 
                                   error_msg='Error interno del servidor. Nuestro equipo está trabajando en ello.'), 500

        # Carpeta QR
        os.makedirs(os.path.join(app.static_folder, 'img', 'qr'), exist_ok=True)

        logger.info(f"✅ App creada con éxito en modo {env}")
        return app
        
    except Exception as e:
        logger.error(f"❌ Error crítico creando app: {e}", exc_info=True)
        raise


# Auto-detectar entorno Railway
_env = 'production' if os.environ.get('RAILWAY_ENVIRONMENT') else os.environ.get('FLASK_ENV', 'development')
app = create_app(_env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = app.config.get('DEBUG', True)
    print(f"🚀 Iniciando Cinema Caribe en puerto {port} ({_env})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
