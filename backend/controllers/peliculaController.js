const pool = require('../config/db');

exports.getAllPeliculas = async (req, res) => {
    try {
        const [rows] = await pool.query('SELECT * FROM peliculas WHERE estado = "ACTIVA"');
        res.json(rows);
    } catch (error) {
        res.status(500).json({ message: 'Error al obtener películas', error: error.message });
    }
};

exports.getPeliculaById = async (req, res) => {
    try {
        const [rows] = await pool.query('SELECT * FROM peliculas WHERE id = ?', [req.params.id]);
        if (rows.length === 0) return res.status(404).json({ message: 'Película no encontrada' });
        res.json(rows[0]);
    } catch (error) {
        res.status(500).json({ message: 'Error al obtener la película', error: error.message });
    }
};

exports.createPelicula = async (req, res) => {
    try {
        const { titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url } = req.body;
        const [result] = await pool.query(
            'INSERT INTO peliculas (titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url]
        );
        res.status(201).json({ id: result.insertId, message: 'Película creada exitosamente' });
    } catch (error) {
        res.status(500).json({ message: 'Error al crear la película', error: error.message });
    }
};

exports.updatePelicula = async (req, res) => {
    try {
        const { titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url, estado } = req.body;
        await pool.query(
            'UPDATE peliculas SET titulo = ?, descripcion = ?, duracion_minutos = ?, genero = ?, clasificacion = ?, imagen_url = ?, trailer_url = ?, estado = ? WHERE id = ?',
            [titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url, estado, req.params.id]
        );
        res.json({ message: 'Película actualizada exitosamente' });
    } catch (error) {
        res.status(500).json({ message: 'Error al actualizar la película', error: error.message });
    }
};

exports.deletePelicula = async (req, res) => {
    try {
        // En lugar de borrar físicamente, cambiamos el estado
        await pool.query('UPDATE peliculas SET estado = "INACTIVA" WHERE id = ?', [req.params.id]);
        res.json({ message: 'Película eliminada lógicamente.' });
    } catch (error) {
        res.status(500).json({ message: 'Error al eliminar la película', error: error.message });
    }
};
