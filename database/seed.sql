USE cinema_caribe;

-- Insertar Películas (Tropical / Caribeño Theme + Blockbusters)
INSERT INTO peliculas (titulo, descripcion, duracion_minutos, genero, clasificacion, imagen_url, trailer_url, estado) VALUES
('Misterio en La Habana', 'Un detective busca pistas bajo el sol ardiente de Cuba.', 110, 'Thriller', 'PG-13', 'https://images.unsplash.com/photo-1510255139049-ed6a68361031?q=80&w=800&auto=format&fit=crop', 'https://youtube.com', 'ACTIVA'),
('Aventura en el Arrecife', 'Buceadores descubren un tesoro perdido en el Mar Caribe.', 95, 'Aventura', 'PG', 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=800&auto=format&fit=crop', 'https://youtube.com', 'ACTIVA'),
('El Pirata Fantasma', 'La leyenda cobra vida en las noches de luna llena.', 125, 'Fantasía', 'PG-13', 'https://images.unsplash.com/photo-1534008897995-27a23e859048?q=80&w=800&auto=format&fit=crop', 'https://youtube.com', 'ACTIVA'),
('Salsa, Ritmo y Corazón', 'Un documental sobre la evolución de la música caribeña.', 85, 'Documental', 'G', 'https://images.unsplash.com/photo-1519892300165-cb5542fb47c7?q=80&w=800&auto=format&fit=crop', 'https://youtube.com', 'ACTIVA');

-- Insertar Funciones
-- Asumimos que hoy es cercano a las fechas, ponemos unas fechas futuras genéricas
INSERT INTO funciones (pelicula_id, fecha_hora, precio_base) VALUES
(1, DATE_ADD(NOW(), INTERVAL 1 DAY), 10.50),
(1, DATE_ADD(NOW(), INTERVAL 2 DAY), 10.50),
(2, DATE_ADD(NOW(), INTERVAL 1 DAY), 8.00),
(3, DATE_ADD(NOW(), INTERVAL 3 DAY), 12.00),
(4, DATE_ADD(NOW(), INTERVAL 1 DAY), 7.50);

-- Insertar algunos usuarios admin
-- Nota: En un entorno de producción, las contraseñas deben estar hasheadas (bcrypt).
-- Aquí usaremos un texto plano para facilitar el demo si no implementamos login estricto.
INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES
('Admin Caribe', 'admin@cinemacaribe.com', 'admin123', 'ADMIN');
