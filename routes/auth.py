"""Rutas de autenticación."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuario import Usuario
from werkzeug.security import check_password_hash
import functools

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('rol') not in ['admin', 'taquilla', 'validador']:
            flash('Acceso restringido a personal autorizado.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.before_app_request
def restrict_validador():
    """
    Restricción de rol validador: solo puede acceder a:
    - Validación de tiquetes
    - Logout
    - Static files
    - APIs de validación
    """
    if session.get('rol') == 'validador':
        allowed_endpoints = {
            'tiquetes.validar',      # GET y POST para validar
            'auth.logout',            # Cerrar sesión
            'static',                 # Recursos estáticos
            'tiquetes.api_validar',   # API de validación
            'admin.dashboard'         # Solo para mostrar dashboard limitado
        }
        if request.endpoint and request.endpoint not in allowed_endpoints:
            flash('Acceso restringido. Solo puedes validar tiquetes.', 'warning')
            return redirect(url_for('tiquetes.validar'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        usuario  = Usuario.obtener_por_email(email)
        if usuario and usuario.verificar_password(password):
            session.clear()
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['rol'] = usuario.rol
            flash(f'¡Bienvenido, {usuario.nombre}!', 'success')
            next_url = request.args.get('next') or url_for('main.home')
            return redirect(next_url)
        flash('Credenciales incorrectas.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        if not all([nombre, email, password]):
            flash('Todos los campos son obligatorios.', 'danger')
        elif password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
        elif Usuario.obtener_por_email(email):
            flash('El email ya está registrado.', 'danger')
        else:
            try:
                uid = Usuario.crear(nombre, email, password)
                session['usuario_id'] = uid
                session['usuario_nombre'] = nombre
                session['rol'] = 'cliente'
                flash('¡Cuenta creada exitosamente!', 'success')
                return redirect(url_for('main.home'))
            except Exception as e:
                flash(f'Error al crear cuenta: {e}', 'danger')
    return render_template('auth/registro.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('main.home'))
