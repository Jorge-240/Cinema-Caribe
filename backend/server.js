require('dotenv').config();
const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');

const app = express();

app.use(cors());
app.use(express.json());

const path = require('path');

// Routes
app.use('/api', apiRoutes);

// Servir frontend en producción
if (process.env.NODE_ENV === 'production' || process.env.RAILWAY_ENVIRONMENT) {
    app.use(express.static(path.join(__dirname, '../frontend/dist')));
    
    app.get('*', (req, res) => {
        res.sendFile(path.join(__dirname, '../frontend/dist/index.html'));
    });
} else {
    // Manejo de rutas desconocidas en desarrollo
    app.use((req, res, next) => {
        res.status(404).json({ message: 'Ruta no encontrada' });
    });
}

// Manejo de errores globales
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ message: 'Error interno del servidor', error: err.message });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`Servidor de Cinema Caribe ejecutándose en el puerto ${PORT}`);
});
