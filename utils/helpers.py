"""
Helpers generales: generación de códigos, QR, etc.
"""
import uuid
import datetime


def fix_row(row: dict) -> dict:
    """
    Convierte objetos timedelta (campo TIME de MySQL) a string 'HH:MM'
    para que los templates Jinja2 puedan usarlos sin error.
    """
    if not row:
        return row
    result = {}
    for k, v in row.items():
        if isinstance(v, datetime.timedelta):
            total = int(v.total_seconds())
            h, rem = divmod(total, 3600)
            m = rem // 60
            result[k] = f"{h:02d}:{m:02d}"
        else:
            result[k] = v
    return result


def fix_rows(rows: list) -> list:
    """Aplica fix_row a una lista de diccionarios."""
    return [fix_row(r) for r in (rows or [])]
import os
import qrcode
from io import BytesIO
import base64

def generar_codigo():
    """Genera un UUID único para el tiquete."""
    return str(uuid.uuid4())

def generar_qr_base64(datos: str) -> str:
    """
    Genera una imagen QR en base64 lista para <img src="...">.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2
    )
    qr.add_data(datos)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#E8580A", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

def guardar_qr(datos: str, carpeta: str, nombre: str) -> str:
    """
    Guarda el QR en disco y devuelve la ruta relativa.
    """
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.png")
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(datos)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#E8580A", back_color="white")
    img.save(ruta)
    return ruta

def formato_precio(valor):
    """Formatea un número como precio colombiano."""
    return f"${valor:,.0f} COP"
