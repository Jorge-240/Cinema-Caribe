const pool = require('../config/db');

exports.getAllFunciones = async (req, res) => {
    try {
        const query = `
            SELECT f.*, p.titulo, p.imagen_url, p.duracion_minutos 
            FROM funciones f
            JOIN peliculas p ON f.pelicula_id = p.id
            WHERE f.fecha_hora >= NOW()
            ORDER BY f.fecha_hora ASC
        `;
        const [rows] = await pool.query(query);
        res.json(rows);
    } catch (error) {
        res.status(500).json({ message: 'Error al obtener funciones', error: error.message });
    }
};

exports.createFuncion = async (req, res) => {
    try {
        const { pelicula_id, fecha_hora, precio_base } = req.body;
        const [result] = await pool.query(
            'INSERT INTO funciones (pelicula_id, fecha_hora, precio_base) VALUES (?, ?, ?)',
            [pelicula_id, fecha_hora, precio_base]
        );
        res.status(201).json({ id: result.insertId, message: 'Función generada correctamente' });
    } catch (error) {
        // Manejar el error de clave única (unique_funcion)
        if (error.code === 'ER_DUP_ENTRY') {
            return res.status(400).json({ message: 'Ya existe una función para esta película en esa fecha y hora.' });
        }
        res.status(500).json({ message: 'Error al crear la función', error: error.message });
    }
};

exports.getAsientosByFuncion = async (req, res) => {
    const funcionId = req.params.id;
    try {
        // En lugar de tener los 150 asientos en una tabla por función, leemos los agrupados en detalles_tiquete
        // Determinamos las filas de la A a la J, y 15 asientos por fila (150 total)
        
        const [ocupados] = await pool.query(
            'SELECT asiento_id FROM detalle_tiquete WHERE funcion_id = ?',
            [funcionId]
        );
        const asientosOcupados = ocupados.map(r => r.asiento_id);

        const filas = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
        let asientosTotales = [];

        for (let fila of filas) {
            for (let num = 1; num <= 15; num++) {
                const idAsiento = `${fila}${num}`;
                asientosTotales.push({
                    id: idAsiento,
                    estado: asientosOcupados.includes(idAsiento) ? 'ocupado' : 'disponible'
                });
            }
        }
        
        res.json(asientosTotales);
    } catch (error) {
        res.status(500).json({ message: 'Error al obtener los asientos', error: error.message });
    }
};
