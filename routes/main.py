"""Rutas principales (cartelera, detalle película)."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from models.pelicula import Pelicula
from models.funcion import Funcion

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    try:
        peliculas = Pelicula.listar(solo_activas=True)
        funciones_hoy = Funcion.listar(solo_futuras=True)
        return render_template('main/home.html',
                               peliculas=peliculas,
                               funciones_hoy=funciones_hoy)
    except Exception as e:
        current_app.logger.error(f"Error cargando home: {str(e)}", exc_info=True)
        flash('Error conectando a la base de datos. Intenta más tarde.', 'danger')
        return render_template('main/home.html', 
                               peliculas=[], 
                               funciones_hoy=[]), 500


@main_bp.route('/pelicula/<int:pid>')
def detalle_pelicula(pid):
    try:
        pelicula = Pelicula.obtener(pid)
        if not pelicula:
            return render_template('errors/404.html'), 404
        funciones = Funcion.listar(pelicula_id=pid, solo_futuras=True)
        return render_template('main/detalle_pelicula.html',
                               pelicula=pelicula,
                               funciones=funciones)
    except Exception as e:
        current_app.logger.error(f"Error cargando detalle película {pid}: {str(e)}", exc_info=True)
        flash('Error conectando a la base de datos. Intenta más tarde.', 'danger')
        return redirect(url_for('main.home'))
