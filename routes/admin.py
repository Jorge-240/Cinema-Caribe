"""Rutas del panel de administración."""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify)
from models.pelicula import Pelicula
from models.funcion  import Funcion
from models.tiquete  import Tiquete
from models.usuario  import Usuario
from routes.auth     import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Dashboard ────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    stats     = Tiquete.stats_admin()
    funciones = Funcion.stats_admin()
    top_peliculas = Pelicula.mas_vistas()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           funciones=funciones,
                           top_peliculas=top_peliculas)


# ── Películas ────────────────────────────────────────────────
@admin_bp.route('/peliculas')
@admin_required
def peliculas():
    lista = Pelicula.listar()
    return render_template('admin/peliculas.html', peliculas=lista)


@admin_bp.route('/peliculas/nueva', methods=['GET', 'POST'])
@admin_required
def nueva_pelicula():
    if request.method == 'POST':
        try:
            Pelicula.crear(
                titulo       = request.form['titulo'],
                descripcion  = request.form.get('descripcion', ''),
                duracion     = int(request.form.get('duracion', 90)),
                genero       = request.form.get('genero', ''),
                clasificacion= request.form.get('clasificacion', 'PG'),
                imagen_url   = request.form.get('imagen_url', ''),
                trailer_url  = request.form.get('trailer_url', ''),
                estado       = request.form.get('estado', 'activa')
            )
            flash('Película creada exitosamente.', 'success')
            return redirect(url_for('admin.peliculas'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/form_pelicula.html', pelicula=None)


@admin_bp.route('/peliculas/editar/<int:pid>', methods=['GET', 'POST'])
@admin_required
def editar_pelicula(pid):
    pelicula = Pelicula.obtener(pid)
    if not pelicula:
        flash('Película no encontrada.', 'danger')
        return redirect(url_for('admin.peliculas'))
    if request.method == 'POST':
        try:
            Pelicula.actualizar(
                pid,
                titulo       = request.form['titulo'],
                descripcion  = request.form.get('descripcion', ''),
                duracion     = int(request.form.get('duracion', 90)),
                genero       = request.form.get('genero', ''),
                clasificacion= request.form.get('clasificacion', 'PG'),
                imagen_url   = request.form.get('imagen_url', ''),
                trailer_url  = request.form.get('trailer_url', ''),
                estado       = request.form.get('estado', 'activa')
            )
            flash('Película actualizada.', 'success')
            return redirect(url_for('admin.peliculas'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/form_pelicula.html', pelicula=pelicula)


@admin_bp.route('/peliculas/eliminar/<int:pid>', methods=['POST'])
@admin_required
def eliminar_pelicula(pid):
    try:
        Pelicula.eliminar(pid)
        flash('Película eliminada.', 'success')
    except Exception as e:
        flash(f'No se pudo eliminar: {e}', 'danger')
    return redirect(url_for('admin.peliculas'))


# ── Funciones ────────────────────────────────────────────────
@admin_bp.route('/funciones')
@admin_required
def funciones():
    lista = Funcion.listar()
    return render_template('admin/funciones.html', funciones=lista)


@admin_bp.route('/funciones/nueva', methods=['GET', 'POST'])
@admin_required
def nueva_funcion():
    peliculas = Pelicula.listar(solo_activas=True)
    salas = Funcion.obtener_salas()
    if request.method == 'POST':
        try:
            # Usar la primera sala disponible si no se proporciona
            sala_id = int(request.form.get('sala_id'))
            if not sala_id and salas:
                sala_id = salas[0]['id']
            
            Funcion.crear(
                pelicula_id = int(request.form['pelicula_id']),
                sala_id     = sala_id,
                fecha       = request.form['fecha'],
                hora        = request.form['hora'],
                precio      = float(request.form['precio']),
                estado      = request.form.get('estado', 'programada')
            )
            flash('Función creada exitosamente.', 'success')
            return redirect(url_for('admin.funciones'))
        except ValueError as e:
            flash(str(e), 'warning')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/form_funcion.html',
                           funcion=None, peliculas=peliculas, salas=salas)


@admin_bp.route('/funciones/eliminar/<int:fid>', methods=['POST'])
@admin_required
def eliminar_funcion(fid):
    try:
        Funcion.eliminar(fid)
        flash('Función eliminada.', 'success')
    except Exception as e:
        flash(f'No se pudo eliminar: {e}', 'danger')
    return redirect(url_for('admin.funciones'))


@admin_bp.route('/funciones/editar/<int:fid>', methods=['GET', 'POST'])
@admin_required
def editar_funcion(fid):
    funcion = Funcion.obtener(fid)
    if not funcion:
        flash('Función no encontrada.', 'danger')
        return redirect(url_for('admin.funciones'))
    peliculas = Pelicula.listar(solo_activas=True)
    salas = Funcion.obtener_salas()
    if request.method == 'POST':
        try:
            sala_id = int(request.form.get('sala_id'))
            if not sala_id and salas:
                sala_id = salas[0]['id']
            
            Funcion.actualizar(
                fid,
                pelicula_id = int(request.form['pelicula_id']),
                sala_id     = sala_id,
                fecha       = request.form['fecha'],
                hora        = request.form['hora'],
                precio      = float(request.form['precio']),
                estado      = request.form.get('estado', 'programada')
            )
            flash('Función actualizada.', 'success')
            return redirect(url_for('admin.funciones'))
        except ValueError as e:
            flash(str(e), 'warning')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/form_funcion.html',
                           funcion=funcion, peliculas=peliculas, salas=salas)


# ── Usuarios ─────────────────────────────────────────────────
@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@admin_required
def usuarios():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol', 'cliente')
        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios', 'warning')
        else:
            try:
                Usuario.crear(nombre, email, password, rol)
                flash('Personal creado exitosamente.', 'success')
            except Exception as e:
                flash(f'Error al crear usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))
        
    lista = Usuario.listar_todos()
    return render_template('admin/usuarios.html', usuarios=lista)


# ── Historial de Tiquetes ────────────────────────────────────
@admin_bp.route('/tiquetes/historial')
@admin_required
def historial_tiquetes():
    tiquetes = Tiquete.listar_todos()
    return render_template('admin/historial_tiquetes.html', tiquetes=tiquetes)


# ── API REST ─────────────────────────────────────────────────
@admin_bp.route('/api/peliculas', methods=['GET'])
def api_peliculas():
    return jsonify(Pelicula.listar())


@admin_bp.route('/api/peliculas', methods=['POST'])
@admin_required
def api_crear_pelicula():
    d = request.get_json()
    try:
        pid = Pelicula.crear(**d)
        return jsonify({'id': pid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/funciones', methods=['GET'])
def api_funciones():
    return jsonify(Funcion.listar())


@admin_bp.route('/api/funciones', methods=['POST'])
@admin_required
def api_crear_funcion():
    d = request.get_json()
    try:
        fid = Funcion.crear(**d)
        return jsonify({'id': fid}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 400
