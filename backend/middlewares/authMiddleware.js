const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ message: 'Acceso no autorizado. Token faltante.' });
    }

    const token = authHeader.split(' ')[1];

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'super_secret_caribe_key');
        req.usuario = decoded; // inyectar data del usuario en el request
        next();
    } catch (error) {
        return res.status(403).json({ message: 'Token inválido o expirado.' });
    }
};
