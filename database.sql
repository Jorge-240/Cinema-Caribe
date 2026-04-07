-- ============================================================
--  Cinema Caribe - Base de Datos
-- ============================================================

CREATE DATABASE IF NOT EXISTS cinema_caribe
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cinema_caribe;

-- ----------------------------------------------------------
-- Tabla: usuarios
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    email           VARCHAR(180) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    rol             ENUM('admin','cliente','taquilla','validador') NOT NULL DEFAULT 'cliente',
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: peliculas
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS peliculas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    titulo          VARCHAR(200) NOT NULL,
    descripcion     TEXT,
    duracion        INT NOT NULL COMMENT 'minutos',
    genero          VARCHAR(80),
    clasificacion   ENUM('G','PG','PG-13','R','NC-17') DEFAULT 'PG',
    imagen_url      VARCHAR(500),
    trailer_url     VARCHAR(500),
    estado          ENUM('activa','inactiva') DEFAULT 'activa',
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: salas
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS salas (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nombre  VARCHAR(60) NOT NULL,
    filas   INT NOT NULL DEFAULT 10,
    cols    INT NOT NULL DEFAULT 15
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: funciones
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS funciones (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    pelicula_id INT NOT NULL,
    sala_id     INT NOT NULL DEFAULT 1,
    fecha       DATE NOT NULL,
    hora        TIME NOT NULL,
    precio      DECIMAL(10,2) NOT NULL,
    estado      ENUM('programada','en_curso','finalizada','cancelada') DEFAULT 'programada',
    FOREIGN KEY (pelicula_id) REFERENCES peliculas(id) ON DELETE CASCADE,
    FOREIGN KEY (sala_id)     REFERENCES salas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: asientos  (150 = 10 filas × 15 columnas)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS asientos (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    numero  VARCHAR(10) NOT NULL,
    fila    VARCHAR(5) NOT NULL,
    columna INT NOT NULL,
    sala_id INT NOT NULL DEFAULT 1,
    UNIQUE KEY uq_asiento_sala (sala_id, fila, columna),
    FOREIGN KEY (sala_id) REFERENCES salas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: tiquetes
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS tiquetes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo          VARCHAR(36) NOT NULL UNIQUE,
    usuario_id      INT NOT NULL,
    funcion_id      INT NOT NULL,
    fecha_compra    DATETIME DEFAULT CURRENT_TIMESTAMP,
    total           DECIMAL(10,2) NOT NULL,
    estado          ENUM('valido','usado','anulado') DEFAULT 'valido',
    qr_path         VARCHAR(500),
    nombre_cliente  VARCHAR(120),
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id),
    FOREIGN KEY (funcion_id)  REFERENCES funciones(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Tabla: detalle_tiquete
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_tiquete (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tiquete_id      INT NOT NULL,
    asiento_id      INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    -- REGLA CRÍTICA: un asiento no puede venderse dos veces por función
    UNIQUE KEY uq_funcion_asiento (tiquete_id, asiento_id),
    FOREIGN KEY (tiquete_id) REFERENCES tiquetes(id) ON DELETE CASCADE,
    FOREIGN KEY (asiento_id) REFERENCES asientos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Restricción adicional a nivel de BD: asiento único por función
-- Se aplica via la lógica de negocio + índice en tiquetes+detalle
CREATE TABLE IF NOT EXISTS funcion_asiento (
    funcion_id  INT NOT NULL,
    asiento_id  INT NOT NULL,
    tiquete_id  INT NOT NULL,
    PRIMARY KEY (funcion_id, asiento_id),
    FOREIGN KEY (funcion_id)  REFERENCES funciones(id),
    FOREIGN KEY (asiento_id)  REFERENCES asientos(id),
    FOREIGN KEY (tiquete_id)  REFERENCES tiquetes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
--  DATOS INICIALES
-- ============================================================

-- Sala principal
INSERT INTO salas (nombre, filas, cols) VALUES ('Sala Principal', 10, 15);

-- Admin por defecto  (password: admin123)
INSERT INTO usuarios (nombre, email, password, rol)
VALUES ('Administrador', 'admin@cinemacaribe.com',
        'pbkdf2:sha256:600000$cinema2024$a7d8e9f0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8',
        'admin');

-- Películas de muestra
INSERT INTO peliculas (titulo, descripcion, duracion, genero, clasificacion, imagen_url, trailer_url, estado) VALUES
('El Gran Azul', 'Un épico viaje bajo las olas del Caribe donde la amistad y el misterio se entrelazan en un mundo de coral y luz.', 122, 'Aventura', 'PG', 'https://picsum.photos/seed/movie1/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa'),
('Noche en Cartagena', 'Romance y suspenso en las calles empedradas de la ciudad amurallada bajo una luna caribeña.', 98, 'Romance', 'PG-13', 'https://picsum.photos/seed/movie2/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa'),
('Tormenta de Arena', 'Un thriller de acción trepidante en las playas del Caribe colombiano.', 110, 'Acción', 'R', 'https://picsum.photos/seed/movie3/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa'),
('Mariposas del Trópico', 'Documental sobre la biodiversidad única del Caribe: sus corales, manglares y especies endémicas.', 85, 'Documental', 'G', 'https://picsum.photos/seed/movie4/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa'),
('Cumbia Eterna', 'La historia de una familia que une generaciones a través del ritmo y la tradición musical del Caribe.', 105, 'Drama', 'PG', 'https://picsum.photos/seed/movie5/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa'),
('Isla Prohibida', 'Terror psicológico en una isla desierta donde nada es lo que parece.', 118, 'Terror', 'R', 'https://picsum.photos/seed/movie6/400/600', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'activa');

-- Funciones de muestra
INSERT INTO funciones (pelicula_id, sala_id, fecha, hora, precio, estado) VALUES
(1, 1, CURDATE(), '14:00:00', 18000, 'programada'),
(1, 1, CURDATE(), '17:30:00', 20000, 'programada'),
(1, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '19:00:00', 22000, 'programada'),
(2, 1, CURDATE(), '15:00:00', 18000, 'programada'),
(2, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '18:00:00', 20000, 'programada'),
(3, 1, CURDATE(), '20:00:00', 22000, 'programada'),
(4, 1, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '11:00:00', 15000, 'programada'),
(5, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '16:00:00', 18000, 'programada'),
(6, 1, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '21:30:00', 22000, 'programada');

-- ============================================================
--  Procedimiento: poblar 150 asientos (10 filas × 15 cols)
-- ============================================================
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS poblar_asientos()
BEGIN
    DECLARE filas_letras VARCHAR(26) DEFAULT 'ABCDEFGHIJ';
    DECLARE i INT DEFAULT 1;
    DECLARE j INT DEFAULT 1;
    DECLARE letra CHAR(1);

    WHILE i <= 10 DO
        SET letra = SUBSTRING(filas_letras, i, 1);
        SET j = 1;
        WHILE j <= 15 DO
            INSERT IGNORE INTO asientos (numero, fila, columna, sala_id)
            VALUES (CONCAT(letra, j), letra, j, 1);
            SET j = j + 1;
        END WHILE;
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL poblar_asientos();
