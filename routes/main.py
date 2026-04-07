"""Rutas principales (cartelera, detalle película)."""
from flask import Blueprint, render_template, request
from models.pelicula import Pelicula
from models.funcion import Funcion

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    peliculas = Pelicula.listar(solo_activas=True)
    funciones_hoy = Funcion.listar(solo_futuras=True)
    return render_template('main/home.html',
                           peliculas=peliculas,
                           funciones_hoy=funciones_hoy)


@main_bp.route('/pelicula/<int:pid>')
def detalle_pelicula(pid):
    pelicula = Pelicula.obtener(pid)
    if not pelicula:
        return render_template('errors/404.html'), 404
    funciones = Funcion.listar(pelicula_id=pid, solo_futuras=True)
    return render_template('main/detalle_pelicula.html',
                           pelicula=pelicula,
                           funciones=funciones)
