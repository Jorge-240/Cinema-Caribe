"""
Endpoint para inicializar la BD directamente desde la app en Railway.
"""

def get_initialize_endpoint(app):
    """Crea el endpoint /initialize para una app Flask."""
    from flask import jsonify, current_app
    import mysql.connector
    
    @app.route('/initialize', methods=['GET', 'POST'])
    def initialize_database():
        """
        Endpoint para inicializar la BD.
        Ejecuta database.sql en la BD conectada.
        """
        try:
            # Leer el archivo SQL
            with open('database.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Conectar directamente a MySQL (sin usar el pool)
            import mysql.connector
            
            conn = mysql.connector.connect(
                host=app.config.get('DB_HOST'),
                port=int(app.config.get('DB_PORT')),
                user=app.config.get('DB_USER'),
                password=app.config.get('DB_PASSWORD'),
                autocommit=True,
                charset='utf8mb4',
            )
            
            cursor = conn.cursor()
            
            # Ejecutar cada comando SQL
            for statement in sql_content.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        current_app.logger.info(f"✅ Ejecutado: {statement[:60]}...")
                    except Exception as e:
                        current_app.logger.warning(f"⚠️  Error en SQL: {e}")
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'status': 'success',
                'message': 'Base de datos inicializada correctamente',
                'action': 'Las tablas han sido creadas/verificadas'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error inicializando BD: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
