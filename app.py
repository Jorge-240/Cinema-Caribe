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
