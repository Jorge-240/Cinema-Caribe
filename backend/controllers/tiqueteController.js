const pool = require('../config/db');
const { v4: uuidv4 } = require('uuid');

exports.createTiquete = async (req, res) => {
    // Usaremos transacciones para evitar la doble venta
    const { nombre_cliente, email_cliente, funcion_id, asientos, precio_pagado_por_asiento } = req.body;
    
    if (!asientos || asientos.length === 0) {
        return res.status(400).json({ message: 'No hay asientos seleccionados.' });
    }

    const connection = await pool.getConnection();

    try {
        await connection.beginTransaction();

        const total = asientos.length * precio_pagado_por_asiento;
        const codigo_unico = uuidv4();

        // 1. Insertar el tiquete principal
        const [tiqueteResult] = await connection.query(
            'INSERT INTO tiquetes (codigo_unico, nombre_cliente, email_cliente, total) VALUES (?, ?, ?, ?)',
            [codigo_unico, nombre_cliente, email_cliente, total]
        );
        const tiqueteId = tiqueteResult.insertId;

        // 2. Insertar cada asiento reservado
        for (let asiento_id of asientos) {
            await connection.query(
                'INSERT INTO detalle_tiquete (tiquete_id, funcion_id, asiento_id, precio_pagado) VALUES (?, ?, ?, ?)',
                [tiqueteId, funcion_id, asiento_id, precio_pagado_por_asiento]
            );
        }

        // Si todo sale bien, aplicamos la transacción
        await connection.commit();
        res.status(201).json({ 
            message: 'Tiquete comprado con éxito.', 
            codigo: codigo_unico 
        });

    } catch (error) {
        // Hacemos rollback si hay doble venta o cualquier otro error
        await connection.rollback();
        // ER_DUP_ENTRY es el código queMySQL arrojará gracias a nuestra clave UNIQUE
        if (error.code === 'ER_DUP_ENTRY') {
            return res.status(409).json({ message: 'Error: Uno o más de los asientos seleccionados ya han sido vendidos. Transacción rechazada.' });
        }
        res.status(500).json({ message: 'Error en la transacción', error: error.message });
    } finally {
        connection.release();
    }
};

exports.validarTiquete = async (req, res) => {
    const { codigo } = req.body;
    try {
        const [rows] = await pool.query('SELECT * FROM tiquetes WHERE codigo_unico = ?', [codigo]);
        
        if (rows.length === 0) {
            return res.status(404).json({ message: 'Tiquete no encontrado.', estado: 'INVALIDO' });
        }

        const tiquete = rows[0];

        if (tiquete.estado === 'USADO') {
            return res.status(400).json({ message: 'El tiquete ya fue utilizado.', estado: 'USADO' });
        }
        if (tiquete.estado === 'INVALIDO') {
            return res.status(400).json({ message: 'El tiquete no es válido.', estado: 'INVALIDO' });
        }

        // Marcar como usado
        await pool.query('UPDATE tiquetes SET estado = "USADO" WHERE id = ?', [tiquete.id]);
        
        res.json({ message: 'Tiquete validado con éxito. Acceso permitido.', estado: 'USADO' });

    } catch (error) {
        res.status(500).json({ message: 'Error al validar', error: error.message });
    }
};

exports.obtenerMetricas = async (req, res) => {
    try {
        const [tiquetesCountRows] = await pool.query("SELECT COUNT(*) as tiquetesVendidos, COALESCE(SUM(total), 0) as ingresosTotales FROM tiquetes WHERE estado != 'INVALIDO'");
        const [peliculasCountRows] = await pool.query("SELECT COUNT(*) as peliculasTotales FROM peliculas WHERE estado = 'ACTIVA'");
        res.json({
            ventasTotales: tiquetesCountRows[0].ingresosTotales,
            tiquetesVendidos: tiquetesCountRows[0].tiquetesVendidos,
            peliculasActivas: peliculasCountRows[0].peliculasTotales,
        });
    } catch(err) {
        res.status(500).json({error: err.message});
    }
};
