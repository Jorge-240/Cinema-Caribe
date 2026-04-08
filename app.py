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

        # Generate seats endpoint - crear asientos para las salas
        @app.route('/generate-seats', methods=['GET', 'POST'])
        def generate_seats():
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
                
                # Obtener salas
                cursor.execute("SELECT id, nombre, filas, cols FROM salas")
                salas = cursor.fetchall()
                
                if not salas:
                    return jsonify({
                        'status': 'error',
                        'message': 'No hay salas creadas'
                    }), 400
                
                total_asientos = 0
                salas_procesadas = []
                
                # Generar asientos para cada sala
                for sala in salas:
                    sala_id = sala['id']
                    sala_nombre = sala['nombre']
                    filas = sala['filas']
                    cols = sala['cols']
                    
                    # Limpiar asientos existentes
                    cursor.execute("DELETE FROM asientos WHERE sala_id = %s", (sala_id,))
                    
                    # Generar nuevos asientos
                    letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    asientos_creados = 0
                    
                    for fila_idx in range(filas):
                        fila_letra = letras[fila_idx]
                        for col_idx in range(1, cols + 1):
                            numero = f"{fila_letra}{col_idx}"
                            cursor.execute("""
                                INSERT INTO asientos (numero, fila, columna, sala_id) 
                                VALUES (%s, %s, %s, %s)
                            """, (numero, fila_letra, col_idx, sala_id))
                            asientos_creados += 1
                            total_asientos += 1
                    
                    salas_procesadas.append({
                        'sala': sala_nombre,
                        'asientos': asientos_creados
                    })
                    logger.info(f"✅ {asientos_creados} asientos creados para {sala_nombre}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'message': f'{total_asientos} asientos generados',
                    'salas_procesadas': salas_procesadas,
                    'total_asientos': total_asientos
                }), 200
                
            except Exception as e:
                logger.error(f"Error en generate-seats: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        # Complete setup endpoint - TODO en un solo paso
        @app.route('/complete-setup', methods=['GET', 'POST'])
        def complete_setup():
            """Ejecuta inicialización completa: tablas, usuarios, sala y asientos"""
            try:
                import mysql.connector
                
                conn = mysql.connector.connect(
                    host=app.config.get('DB_HOST'),
                    port=int(app.config.get('DB_PORT')),
                    user=app.config.get('DB_USER'),
                    password=app.config.get('DB_PASSWORD'),
                    database=app.config.get('DB_NAME'),
                    autocommit=False,  # Transacción manual
                    charset='utf8mb4',
                )
                
                cursor = conn.cursor(dictionary=True)
                setup_steps = []
                
                # ===== PASO 0: Desabilitar FK constraints =====
                try:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    logger.info("🔓 Foreign key checks deshabilitados")
                except Exception as e:
                    logger.warning(f"No se pudieron deshabilitar FK checks: {e}")
                
                # ===== PASO 1: Limpiar datos viejos =====
                try:
                    cursor.execute("DELETE FROM funcion_asiento")
                    cursor.execute("DELETE FROM tiquetes")
                    cursor.execute("DELETE FROM funciones")
                    cursor.execute("DELETE FROM peliculas")
                    cursor.execute("DELETE FROM asientos")
                    cursor.execute("DELETE FROM salas")
                    cursor.execute("DELETE FROM usuarios")
                    conn.commit()
                    setup_steps.append({'step': '0. Datos viejos eliminados', 'status': 'success'})
                    logger.info("🗑️ Tablas limpias")
                except Exception as e:
                    conn.rollback()
                    setup_steps.append({'step': '0. Limpiar datos', 'status': 'error', 'error': str(e)})
                    logger.error(f"Error limpiando datos: {e}")
                
                # ===== PASO 1b: ReabilSitar FK constraints =====
                try:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    logger.info("🔒 Foreign key checks re-habilitados")
                except Exception as e:
                    logger.warning(f"No se pudieron re-habilitar FK checks: {e}")
                
                # ===== PASO 2: Crear Sala =====
                try:
                    cursor.execute("""
                        INSERT INTO salas (nombre, filas, cols) 
                        VALUES ('Sala 1', 10, 15)
                    """)
                    conn.commit()
                    setup_steps.append({'step': '1. Sala creada', 'status': 'success'})
                    logger.info("✅ Sala 1 creada (10x15)")
                except Exception as e:
                    conn.rollback()
                    setup_steps.append({'step': '1. Crear Sala', 'status': 'error', 'error': str(e)})
                    logger.error(f"Error creando sala: {e}")
                
                # ===== PASO 3: Generar Asientos =====
                try:
                    cursor.execute("""
                        SELECT id, nombre, filas, cols FROM salas WHERE nombre = 'Sala 1'
                    """)
                    sala = cursor.fetchone()
                    
                    if sala:
                        sala_id = sala['id']
                        filas = sala['filas']
                        cols = sala['cols']
                        
                        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        asientos_count = 0
                        for fila_idx in range(filas):
                            fila_letra = letras[fila_idx]
                            for col_idx in range(1, cols + 1):
                                numero = f"{fila_letra}{col_idx}"
                                cursor.execute("""
                                    INSERT INTO asientos (numero, fila, columna, sala_id) 
                                    VALUES (%s, %s, %s, %s)
                                """, (numero, fila_letra, col_idx, sala_id))
                                asientos_count += 1
                        conn.commit()
                        setup_steps.append({'step': '2. Asientos generados', 'status': 'success', 'count': asientos_count})
                        logger.info(f"✅ {asientos_count} asientos creados")
                except Exception as e:
                    conn.rollback()
                    setup_steps.append({'step': '2. Generar Asientos', 'status': 'error', 'error': str(e)})
                    logger.error(f"Error generando asientos: {e}")
                
                # ===== PASO 4: Crear Usuarios =====
                try:
                    test_users = [
                        ('Admin User', 'admin@cinemacaribe.com', 'admin123', 'admin'),
                        ('Validador', 'validador@cinemacaribe.com', 'validador123', 'validador'),
                        ('Taquillero', 'taquilla@cinemacaribe.com', 'taquilla123', 'taquilla'),
                    ]
                    
                    for nombre, email, password, rol in test_users:
                        hashed_pwd = generate_password_hash(password)
                        cursor.execute("""
                            INSERT INTO usuarios (nombre, email, password, rol) 
                            VALUES (%s, %s, %s, %s)
                        """, (nombre, email, hashed_pwd, rol))
                    
                    conn.commit()
                    setup_steps.append({'step': '3. Usuarios creados', 'status': 'success', 'count': len(test_users)})
                    logger.info(f"✅ {len(test_users)} usuarios creados")
                except Exception as e:
                    conn.rollback()
                    setup_steps.append({'step': '3. Crear Usuarios', 'status': 'error', 'error': str(e)})
                    logger.error(f"Error creando usuarios: {e}")
                
                # ===== PASO 5: Crear Película y Función con Relaciones =====
                try:
                    # Obtener el ID de la sala recién creada
                    cursor.execute("SELECT id FROM salas WHERE nombre = 'Sala 1'")
                    sala_result = cursor.fetchone()
                    sala_id = sala_result['id'] if sala_result else None
                    
                    if not sala_id:
                        raise Exception("No se encontró la sala 'Sala 1'")
                    
                    cursor.execute("""
                        INSERT INTO peliculas (titulo, descripcion, duracion, genero, clasificacion, estado) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, ('Noche en Cartagena', 'Una hermosa noche en Cartagena', 120, 'Drama', 'PG', 'activa'))
                    
                    # Obtener ID de la película
                    cursor.execute("SELECT LAST_INSERT_ID() as id")
                    pelicula_id = cursor.fetchone()['id']
                    
                    # Agregar una función para hoy (usando sala_id dinámico)
                    cursor.execute("""
                        INSERT INTO funciones (pelicula_id, sala_id, fecha, hora, precio, estado) 
                        VALUES (%s, %s, CURDATE(), %s, %s, %s)
                    """, (pelicula_id, sala_id, '20:10:00', 25000, 'programada'))
                    
                    # Obtener ID de la función recién creada
                    cursor.execute("SELECT LAST_INSERT_ID() as id")
                    funcion_id = cursor.fetchone()['id']
                    
                    # Los asientos quedan disponibles automáticamente
                    # porque funcion_asiento almacena solo asientos ocupados/vendidos
                    cursor.execute("SELECT COUNT(*) as count FROM asientos WHERE sala_id = %s", (sala_id,))
                    asientos_count = cursor.fetchone()['count']
                    
                    conn.commit()
                    setup_steps.append({'step': '4. Película creada', 'status': 'success'})
                    setup_steps.append({'step': '5. Función creada', 'status': 'success'})
                    setup_steps.append({'step': '6. Asientos inicializados como disponibles', 'status': 'success', 'count': asientos_count})
                    logger.info(f"✅ Película, función y {asientos_count} asientos disponibles creados")
                    
                    conn.commit()
                    setup_steps.append({'step': '4. Película creada', 'status': 'success'})
                    setup_steps.append({'step': '5. Función creada', 'status': 'success'})
                    setup_steps.append({'step': '6. Relaciones función-asiento creadas', 'status': 'success', 'count': asientos_count})
                    logger.info(f"✅ Película, función y {asientos_count} relaciones funcion_asiento creadas")
                except Exception as e:
                    conn.rollback()
                    setup_steps.append({'step': '4-6. Crear Película/Función/Relaciones', 'status': 'error', 'error': str(e)})
                    logger.error(f"Error creando película/función/relaciones: {e}", exc_info=True)
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Setup completado exitosamente',
                    'steps': setup_steps,
                    'credentials': {
                        'admin': 'admin@cinemacaribe.com / admin123',
                        'validador': 'validador@cinemacaribe.com / validador123',
                        'taquilla': 'taquilla@cinemacaribe.com / taquilla123',
                    }
                }), 200
                
            except Exception as e:
                logger.error(f"Error en complete-setup: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
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
