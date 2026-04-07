"""Rutas de tiquetes (selección de asientos, compra, validación)."""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify, current_app)
from models.funcion  import Funcion
from models.asiento  import Asiento
from models.tiquete  import Tiquete
from routes.auth     import login_required, admin_required
import os

tiquetes_bp = Blueprint('tiquetes', __name__, url_prefix='/tiquetes')


@tiquetes_bp.route('/seleccionar/<int:funcion_id>')
@login_required
def seleccionar_asientos(funcion_id):
    funcion  = Funcion.obtener(funcion_id)
    if not funcion:
        flash('Función no encontrada.', 'danger')
        return redirect(url_for('main.home'))
    asientos = Asiento.listar_por_funcion(funcion_id)
    # Organizar en grid
    grid = {}
    for a in asientos:
        grid.setdefault(a['fila'], []).append(a)
    filas_ordenadas = sorted(grid.keys())
    return render_template('tiquetes/seleccionar.html',
                           funcion=funcion,
                           grid=grid,
                           filas_ordenadas=filas_ordenadas)


@tiquetes_bp.route('/comprar', methods=['POST'])
@login_required
def comprar():
    funcion_id  = request.form.get('funcion_id', type=int)
    asiento_ids = request.form.getlist('asiento_ids[]', type=int)
    nombre_cliente = request.form.get('nombre_cliente', '').strip()
    
    if not funcion_id or not asiento_ids:
        flash('Debes seleccionar al menos un asiento.', 'warning')
        return redirect(request.referrer or url_for('main.home'))

    funcion = Funcion.obtener(funcion_id)
    if not funcion:
        flash('Función inválida.', 'danger')
        return redirect(url_for('main.home'))

    qr_folder = os.path.join(current_app.static_folder, 'img', 'qr')
    try:
        tiquete_id, codigo = Tiquete.crear(
            usuario_id=session['usuario_id'],
            funcion_id=funcion_id,
            asiento_ids=asiento_ids,
            precio_unitario=float(funcion['precio']),
            qr_folder=qr_folder,
            nombre_cliente=nombre_cliente if nombre_cliente else None
        )
        
        # Save POS calculations in session temporarily for the current receipt
        if 'dinero_recibido' in request.form:
            session['pos_data'] = {
                'tiquete_id': tiquete_id,
                'recibido': float(request.form.get('dinero_recibido', 0)),
                'cambio': float(request.form.get('cambio', 0))
            }
            
        flash('¡Compra exitosa! Tu tiquete ha sido generado.', 'success')
        return redirect(url_for('tiquetes.detalle', tiquete_id=tiquete_id))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('tiquetes.seleccionar_asientos', funcion_id=funcion_id))
    except Exception as e:
        flash(f'Error al procesar la compra: {e}', 'danger')
        return redirect(url_for('tiquetes.seleccionar_asientos', funcion_id=funcion_id))


@tiquetes_bp.route('/detalle/<int:tiquete_id>')
@login_required
def detalle(tiquete_id):
    tiquete  = Tiquete.obtener(tiquete_id)
    if not tiquete or tiquete['usuario_id'] != session['usuario_id']:
        flash('Tiquete no encontrado.', 'danger')
        return redirect(url_for('main.home'))
    detalles = Tiquete.obtener_detalles(tiquete_id)
    from utils.helpers import generar_qr_base64
    qr_b64 = generar_qr_base64(tiquete['codigo'])
    return render_template('tiquetes/detalle.html',
                           tiquete=tiquete,
                           detalles=detalles,
                           qr_b64=qr_b64)


@tiquetes_bp.route('/mis-tiquetes')
@login_required
def mis_tiquetes():
    tiquetes = Tiquete.listar_usuario(session['usuario_id'])
    return render_template('tiquetes/mis_tiquetes.html', tiquetes=tiquetes)


@tiquetes_bp.route('/validar', methods=['GET', 'POST'])
@admin_required
def validar():
    resultado = None
    if request.method == 'POST':
        codigo  = request.form.get('codigo', '').strip()
        accion  = request.form.get('accion', 'consultar')
        tiquete = Tiquete.obtener_por_codigo(codigo)
        if not tiquete:
            resultado = {'estado': 'invalido', 'mensaje': 'Código no encontrado.'}
        elif accion == 'usar' and tiquete['estado'] == 'valido':
            Tiquete.marcar_usado(codigo)
            tiquete['estado'] = 'usado'
            detalles = Tiquete.obtener_detalles(tiquete['id'])
            resultado = {'estado': 'usado', 'mensaje': '¡Tiquete marcado como usado!', 'tiquete': tiquete, 'detalles': detalles}
        else:
            detalles = Tiquete.obtener_detalles(tiquete['id'])
            resultado = {'estado': tiquete['estado'], 'tiquete': tiquete,
                         'mensaje': f"Estado: {tiquete['estado'].upper()}",
                         'detalles': detalles}
    return render_template('tiquetes/validar.html', resultado=resultado)


# --- API REST ---

@tiquetes_bp.route('/api/asientos/<int:funcion_id>')
def api_asientos(funcion_id):
    asientos = Asiento.listar_por_funcion(funcion_id)
    return jsonify(asientos)


@tiquetes_bp.route('/api/crear', methods=['POST'])
@login_required
def api_crear():
    data        = request.get_json()
    funcion_id  = data.get('funcion_id')
    asiento_ids = data.get('asiento_ids', [])
    funcion     = Funcion.obtener(funcion_id)
    if not funcion or not asiento_ids:
        return jsonify({'error': 'Datos inválidos'}), 400
    qr_folder = os.path.join(current_app.static_folder, 'img', 'qr')
    try:
        tiquete_id, codigo = Tiquete.crear(
            session['usuario_id'], funcion_id, asiento_ids,
            float(funcion['precio']), qr_folder
        )
        return jsonify({'tiquete_id': tiquete_id, 'codigo': codigo})
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tiquetes_bp.route('/api/validar', methods=['POST'])
def api_validar():
    data    = request.get_json()
    codigo  = data.get('codigo', '').strip()
    tiquete = Tiquete.obtener_por_codigo(codigo)
    if not tiquete:
        return jsonify({'valido': False, 'estado': 'invalido'}), 404
    return jsonify({'valido': tiquete['estado'] == 'valido',
                    'estado': tiquete['estado'],
                    'pelicula': tiquete['pelicula_titulo'],
                    'fecha': str(tiquete['fecha']),
                    'hora': str(tiquete['hora'])})
