import os
import urllib.parse
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging para debugging en Railway
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _parse_mysql_url(url):
    url = url.strip()
    if not url or not url.lower().startswith('mysql://'):
        return None

    parsed = urllib.parse.urlparse(url)
    if not parsed.hostname:
        return None

    db_name = parsed.path.lstrip('/') if parsed.path else None
    return {
        'DB_HOST': parsed.hostname,
        'DB_PORT': parsed.port or 3306,
        'DB_USER': urllib.parse.unquote(parsed.username) if parsed.username else None,
        'DB_PASSWORD': urllib.parse.unquote(parsed.password) if parsed.password else None,
        'DB_NAME': db_name,
    }


def _get_mysql_url_data():
    for name in ('MYSQL_URL', 'MYSQL_PUBLIC_URL', 'DB_URL', 'DATABASE_URL', 'MYSQL_DATABASE', 'MYSQLDATABASE'):
        value = os.environ.get(name)
        if value and value.strip().lower().startswith('mysql://'):
            return _parse_mysql_url(value)
    return None


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cinema-caribe-secret-2024')

    url_data = _get_mysql_url_data()

    if url_data:
        DB_HOST = url_data['DB_HOST']
        DB_PORT = int(url_data['DB_PORT'])
        DB_USER = url_data['DB_USER'] or 'root'
        DB_PASSWORD = url_data['DB_PASSWORD'] or ''
        DB_NAME = url_data['DB_NAME'] or 'cinema_caribe'
        logger.info(f"✅ Config: Usando MySQL URL env vars: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    else:
        DB_HOST = (os.environ.get('MYSQLHOST')
                   or os.environ.get('MYSQL_HOST')
                   or os.environ.get('DB_HOST')
                   or 'localhost')

        DB_PORT = int(os.environ.get('MYSQLPORT')
                      or os.environ.get('MYSQL_PORT')
                      or os.environ.get('DB_PORT')
                      or 3306)

        DB_USER = (os.environ.get('MYSQLUSER')
                   or os.environ.get('MYSQL_USER')
                   or os.environ.get('DB_USER')
                   or 'root')

        DB_PASSWORD = (os.environ.get('MYSQLPASSWORD')
                       or os.environ.get('MYSQL_PASSWORD')
                       or os.environ.get('DB_PASSWORD')
                       or '')

        db_name = (os.environ.get('MYSQLDATABASE')
                   or os.environ.get('MYSQL_DATABASE')
                   or os.environ.get('DB_NAME')
                   or 'cinema_caribe')

        if isinstance(db_name, str) and db_name.strip().lower().startswith('mysql://'):
            parsed = _parse_mysql_url(db_name)
            DB_NAME = parsed['DB_NAME'] if parsed and parsed.get('DB_NAME') else 'cinema_caribe'
        else:
            DB_NAME = db_name
            
        # En Railway, MYSQLDATABASE viene como "railway", así que usarlo
        # Pero si está en desarrollo localmente, usar cinema_caribe
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            # Estamos en Railway - usar la BD que Railway proporciona
            DB_NAME = os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or 'railway'
            logger.info(f"✅ Config Railway: Usando BD: {DB_NAME}")
        else:
            logger.info(f"✅ Config Local: Usando individual env vars: {DB_HOST}:{DB_PORT}/{DB_NAME} user={DB_USER}")

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
