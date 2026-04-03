const express = require('express');
const router = express.Router();

const peliculaController = require('../controllers/peliculaController');
const funcionController = require('../controllers/funcionController');
const tiqueteController = require('../controllers/tiqueteController');
const authController = require('../controllers/authController');
const authMiddleware = require('../middlewares/authMiddleware');

// Auth
router.post('/login', authController.login);

// Peliculas
router.get('/peliculas', peliculaController.getAllPeliculas);
router.post('/peliculas', authMiddleware, peliculaController.createPelicula);
router.get('/peliculas/:id', peliculaController.getPeliculaById);
router.put('/peliculas/:id', authMiddleware, peliculaController.updatePelicula);
router.delete('/peliculas/:id', authMiddleware, peliculaController.deletePelicula);

// Funciones
router.get('/funciones', funcionController.getAllFunciones);
router.post('/funciones', authMiddleware, funcionController.createFuncion);
router.get('/funciones/:id/asientos', funcionController.getAsientosByFuncion);

// Tiquetes y Ventas
router.post('/tiquetes', tiqueteController.createTiquete);
router.post('/tiquetes/validar', authMiddleware, tiqueteController.validarTiquete);

// Admin Metrics
router.get('/metricas', authMiddleware, tiqueteController.obtenerMetricas);

module.exports = router;
