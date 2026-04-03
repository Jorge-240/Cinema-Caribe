CREATE DATABASE IF NOT EXISTS cinema_caribe;
USE cinema_caribe;

-- Usuarios (Para el panel administrativo)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('ADMIN', 'EMPLEADO') DEFAULT 'EMPLEADO',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Películas
CREATE TABLE IF NOT EXISTS peliculas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    duracion_minutos INT NOT NULL,
    genero VARCHAR(50),
    clasificacion VARCHAR(10),
    imagen_url VARCHAR(255),
    trailer_url VARCHAR(255),
    estado ENUM('ACTIVA', 'INACTIVA') DEFAULT 'ACTIVA',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Funciones reales donde se proyectan las películas
CREATE TABLE IF NOT EXISTS funciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pelicula_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    precio_base DECIMAL(10, 2) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pelicula_id) REFERENCES peliculas(id) ON DELETE CASCADE,
    -- Previene que se cree dos veces la misma función a la misma hora
    UNIQUE KEY unique_funcion (pelicula_id, fecha_hora)
);

-- Tiquetes que agrupan las compras
CREATE TABLE IF NOT EXISTS tiquetes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_unico VARCHAR(100) UNIQUE NOT NULL,
    nombre_cliente VARCHAR(100) NOT NULL,
    email_cliente VARCHAR(100) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    estado ENUM('VALIDO', 'USADO', 'INVALIDO') DEFAULT 'VALIDO',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detalle de Tiquete (relación Tiquete -> Función -> Asiento)
CREATE TABLE IF NOT EXISTS detalle_tiquete (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tiquete_id INT NOT NULL,
    funcion_id INT NOT NULL,
    asiento_id VARCHAR(10) NOT NULL, -- Ej: 'A1', 'B5', 'J15'
    precio_pagado DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (tiquete_id) REFERENCES tiquetes(id) ON DELETE CASCADE,
    FOREIGN KEY (funcion_id) REFERENCES funciones(id) ON DELETE CASCADE,
    -- REGLA DE NEGOCIO: Ninguna función puede tener el mismo asiento vendido dos veces
    UNIQUE KEY unique_asiento_funcion (funcion_id, asiento_id)
);
