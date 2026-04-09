"""
Utilidades de zona horaria para Cinema Caribe.
Colombia: UTC-5 (no tiene horario de verano).
"""
from datetime import datetime, timezone, timedelta

# Zona horaria Colombia (UTC-5)
TZ_COLOMBIA = timezone(timedelta(hours=-5))


def now_colombia() -> datetime:
    """
    Retorna la fecha y hora actual en la zona horaria de Colombia (UTC-5),
    sin información de zona (naive), lista para comparar con fechas
    almacenadas en la base de datos.
    """
    return datetime.now(tz=TZ_COLOMBIA).replace(tzinfo=None)
