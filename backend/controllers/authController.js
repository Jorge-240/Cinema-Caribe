const jwt = require('jsonwebtoken');
const pool = require('../config/db');

// En un entorno de producción real, usaríamos bcrypt para comparar,
// pero por ahora el seed insertó texto plano ('admin123').
// Implementaremos la verificación directa para no romper el seed,
// pero dejaremos importado bcrypt por si se decide encriptar luego.
const bcrypt = require('bcrypt');

exports.login = async (req, res) => {
    const { email, password } = req.body;
    try {
        const [rows] = await pool.query('SELECT * FROM usuarios WHERE email = ?', [email]);
        if (rows.length === 0) {
            return res.status(401).json({ message: 'Credenciales inválidas' });
        }

        const usuario = rows[0];

        // Validar contraseña (aquí, para simplificar el seed inicial usamos comparación directa, 
        // pero puedes cambiar a bcrypt.compare(password, usuario.password_hash) si actualizas la db)
        if (password !== usuario.password_hash) {
            return res.status(401).json({ message: 'Credenciales inválidas' });
        }

        const token = jwt.sign(
            { id: usuario.id, rol: usuario.rol },
            process.env.JWT_SECRET || 'super_secret_caribe_key',
            { expiresIn: '1d' }
        );

        res.json({
            message: 'Inicio de sesión exitoso',
            token,
            usuario: {
                nombre: usuario.nombre,
                rol: usuario.rol
            }
        });

    } catch (error) {
        res.status(500).json({ message: 'Error en el servidor', error: error.message });
    }
};
