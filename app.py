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
from werkzeug.security import generate_password_hash

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
                import re
                
                # Conectar a la BD especificada
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),
                    autocommit=True,
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor()
                executed_count = 0
                skipped_count = 0
                error_count = 0
                
                # Leer el archivo SQL
                sql_file = os.path.join(os.path.dirname(__file__), 'database.sql')
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Procesar línea por línea - eliminar comentarios y espacios
                lines = []
                for line in sql_content.split('\n'):
                    line = line.strip()
                    # Saltar líneas vacías y comentarios
                    if line and not line.startswith('--'):
                        lines.append(line)
                
                # Recombinar y dividir por punto y coma
                full_sql = '\n'.join(lines)
                # Reemplazar referencias a cinema_caribe
                full_sql = full_sql.replace('USE cinema_caribe;', '')
                
                # Dividir statements - pero cuidado con los puntos y comas dentro de COMMENT
                statements = []
                current_stmt = ""
                for line in full_sql.split('\n'):
                    if line:
                        current_stmt += " " + line
                        if line.endswith(';'):
                            statements.append(current_stmt.strip())
                            current_stmt = ""
                
                if current_stmt.strip():
                    statements.append(current_stmt.strip())
                
                # Ejecutar cada statement
                for stmt in statements:
                    if stmt and not stmt.startswith('--'):
                        try:
                            cursor.execute(stmt)
                            executed_count += 1
                            logger.info(f"✅ Ejecutado: {stmt[:60]}...")
                        except mysql.connector.Error as e:
                            if 'already exists' in str(e).lower():
                                skipped_count += 1
                                logger.info(f"ℹ️  Ya existe: {stmt[:60]}...")
                            else:
                                error_count += 1
                                logger.warning(f"⚠️  Error: {e}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'database': app.config.get('DB_NAME'),
                    'executed': executed_count,
                    'skipped': skipped_count,
                    'errors': error_count,
                    'total_statements': len(statements)
                }), 200
                
            except Exception as e:
                logger.error(f"Error inicializando BD: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'database': app.config.get('DB_NAME'),
                    'message': str(e)
                }), 500

        # Check credentials endpoint - verificar si las credenciales funcionan
        @app.route('/check-creds', methods=['GET'])
        def check_credentials():
            try:
                import mysql.connector
                
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),
                    autocommit=True,
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, email, rol FROM usuarios LIMIT 10")
                users = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'ok',
                    'database': app.config.get('DB_NAME'),
                    'users_count': len(users),
                    'users': users
                }), 200
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        # Reset users endpoint - limpiar y recrear usuarios
        @app.route('/reset-users', methods=['GET', 'POST'])
        def reset_users():
            try:
                import mysql.connector
                
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),
                    autocommit=True,
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor()
                
                # Limpiar usuarios existentes
                cursor.execute("DELETE FROM usuarios")
                logger.info("✅ Usuarios eliminados")
                
                # Usuarios de prueba
                test_users = [
                    {
                        'nombre': 'Admin User',
                        'email': 'admin@cinemacaribe.com',
                        'password': 'admin123',
                        'rol': 'admin'
                    },
                    {
                        'nombre': 'Validador',
                        'email': 'validador@cinemacaribe.com',
                        'password': 'validador123',
                        'rol': 'validador'
                    },
                    {
                        'nombre': 'Taquillero',
                        'email': 'taquilla@cinemacaribe.com',
                        'password': 'taquilla123',
                        'rol': 'taquilla'
                    },
                ]
                
                # Insertar usuarios
                inserted = 0
                for user in test_users:
                    hashed_pwd = generate_password_hash(user['password'])
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, email, password, rol) 
                        VALUES (%s, %s, %s, %s)
                    """, (user['nombre'], user['email'], hashed_pwd, user['rol']))
                    inserted += 1
                    logger.info(f"✅ Usuario creado: {user['email']}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Usuarios recreados exitosamente',
                    'users_inserted': inserted,
                    'credentials': {
                        'admin': {'email': 'admin@cinemacaribe.com', 'password': 'admin123'},
                        'validador': {'email': 'validador@cinemacaribe.com', 'password': 'validador123'},
                        'taquilla': {'email': 'taquilla@cinemacaribe.com', 'password': 'taquilla123'},
                    }
                }), 200
                
            except Exception as e:
                logger.error(f"Error en reset-users: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            try:
                import mysql.connector
                
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),
                    autocommit=True,
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor()
                inserted = 0
                skipped = 0
                
                # Usuarios de prueba
                test_users = [
                    {
                        'nombre': 'Admin User',
                        'email': 'admin@cinemacaribe.com',
                        'password': 'admin123',
                        'rol': 'admin'
                    },
                    {
                        'nombre': 'Validador',
                        'email': 'validador@cinemacaribe.com',
                        'password': 'validador123',
                        'rol': 'validador'
                    },
                    {
                        'nombre': 'Taquillero',
                        'email': 'taquilla@cinemacaribe.com',
                        'password': 'taquilla123',
                        'rol': 'taquilla'
                    },
                ]
                
                # También agregar una sala por defecto
                try:
                    cursor.execute("""
                        INSERT INTO salas (nombre, filas, cols) 
                        VALUES ('Sala 1', 10, 15)
                    """)
                    logger.info("✅ Sala agregada")
                except Exception as e:
                    logger.info(f"ℹ️  Sala ya existe: {e}")
                
                # Insertar usuarios
                for user in test_users:
                    try:
                        # Verificar si existe
                        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (user['email'],))
                        if cursor.fetchone():
                            skipped += 1
                            logger.info(f"ℹ️  Usuario ya existe: {user['email']}")
                        else:
                            # Insertar nuevo usuario
                            hashed_pwd = generate_password_hash(user['password'])
                            cursor.execute("""
                                INSERT INTO usuarios (nombre, email, password, rol) 
                                VALUES (%s, %s, %s, %s)
                            """, (user['nombre'], user['email'], hashed_pwd, user['rol']))
                            inserted += 1
                            logger.info(f"✅ Usuario creado: {user['email']}")
                    except Exception as e:
                        logger.error(f"Error insertando usuario: {e}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Base de datos poblada con datos de prueba',
                    'users_inserted': inserted,
                    'users_skipped': skipped,
                    'credentials': {
                        'admin': {'email': 'admin@cinemacaribe.com', 'password': 'admin123'},
                        'validador': {'email': 'validador@cinemacaribe.com', 'password': 'validador123'},
                        'taquilla': {'email': 'taquilla@cinemacaribe.com', 'password': 'taquilla123'},
                    }
                }), 200
                
            except Exception as e:
                logger.error(f"Error en seed: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': str(e)
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
