# 🎬 Cinema Caribe

> Sistema web completo de gestión de cine — Cine Clásico y Calidez Tropical

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

---

## 📋 Características

- 🎥 **Cartelera** — CRUD completo de películas
- 📅 **Funciones** — Programación con validación de traslapes
- 💺 **Selección de asientos** — Grid interactivo de 150 sillas (10×15)
- 🎟️ **Tiquetes** — Compra, generación de código único + QR
- ✅ **Validación** — Estado en tiempo real: válido / usado / inválido
- 👤 **Autenticación** — Login, registro, roles admin/cliente
- 📊 **Panel Admin** — Dashboard con estadísticas de ventas y ocupación
- 🔒 **Seguridad** — Transacciones atómicas, UNIQUE constraint por asiento/función

---

## 🚀 Instalación y ejecución local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/cinema-caribe.git
cd cinema-caribe
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus credenciales de MySQL
```

### 5. Crear la base de datos
```bash
# Asegúrate de que MySQL esté corriendo, luego:
mysql -u root -p < database.sql
```

### 6. Ejecutar la aplicación
```bash
python app.py
```

Abre tu navegador en: **http://localhost:5000**

---

## 🔑 Credenciales de prueba

| Rol       | Email                       | Contraseña   |
|-----------|-----------------------------|--------------|
| Admin     | admin@cinemacaribe.com      | admin123     |
| Validador | validador@cinemacaribe.com  | validador123 |
| Taquilla  | taquilla@cinemacaribe.com   | taquilla123  |

---

## 🏗️ Estructura del proyecto

```
cine_app/
├── app.py                  # Punto de entrada, factory
├── config.py               # Configuración por entorno
├── requirements.txt
├── database.sql            # Schema + datos iniciales
├── Procfile                # Para Railway
├── railway.toml
├── .env.example
│
├── models/                 # Capa de datos (MySQL)
│   ├── usuario.py
│   ├── pelicula.py
│   ├── funcion.py
│   ├── asiento.py
│   └── tiquete.py
│
├── routes/                 # Blueprints / controladores
│   ├── auth.py             # Login, registro, logout
│   ├── main.py             # Cartelera, detalle película
│   ├── tiquetes.py         # Asientos, compra, validación
│   └── admin.py            # Panel administrativo + API REST
│
├── templates/
│   ├── base.html
│   ├── main/
│   ├── auth/
│   ├── tiquetes/
│   ├── admin/
│   └── errors/
│
├── static/
│   ├── css/main.css
│   ├── js/main.js
│   └── img/
│       ├── logo.png
│       └── qr/             # QRs generados automáticamente
│
└── utils/
    ├── db.py               # Pool de conexiones MySQL
    └── helpers.py          # UUID, QR generator
```

---

## 🌐 API REST

| Método | Endpoint                        | Descripción                     |
|--------|---------------------------------|---------------------------------|
| GET    | `/admin/api/peliculas`          | Listar películas                |
| POST   | `/admin/api/peliculas`          | Crear película (JSON)           |
| GET    | `/admin/api/funciones`          | Listar funciones                |
| POST   | `/admin/api/funciones`          | Crear función (JSON)            |
| GET    | `/tiquetes/api/asientos/<id>`   | Asientos de una función         |
| POST   | `/tiquetes/api/crear`           | Crear tiquete vía API           |
| POST   | `/tiquetes/api/validar`         | Validar código de tiquete       |

---

## 🚂 Despliegue en Railway

**⚡ Sin necesidad de venv local** — Railway maneja el entorno automáticamente.

### ✅ Pasos para desplegar

1. **Sube el proyecto a GitHub**
   ```bash
   git init
   git add .
   git commit -m "Cinema Caribe - inicial"
   git remote add origin https://github.com/tu-usuario/cinema-caribe.git
   git push -u origin main
   ```

2. **Crea un proyecto en [Railway](https://railway.app)**
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub"
   - Autoriza GitHub y elige el repositorio

3. **Agrega el plugin MySQL**
   - En el proyecto, haz clic en "+ Add"
   - Busca "MySQL" y agrégalo
   - Railway creará automáticamente la base de datos

4. **Configura variables de entorno del servicio web**
   - Ve al servicio "web" → Pestaña "Variables"
   - **Reemplaza** las variables manuales con referencias del plugin MySQL:
   ```
   DB_HOST=${{MySQL.MYSQL_HOST}}
   DB_PORT=${{MySQL.MYSQL_PORT}}
   DB_USER=${{MySQL.MYSQL_USER}}
   DB_PASSWORD=${{MySQL.MYSQL_PASSWORD}}
   DB_NAME=${{MySQL.MYSQL_DATABASE}}
   SECRET_KEY=tu-clave-secreta-muy-larga-aleatoria
   FLASK_ENV=production
   ```

5. **¡Listo!**
   - Railway detecta `railway.toml` automáticamente
   - El script `init_db_auto.py` crea la BD y las tablas al desplegar
   - Tu app está lista en la URL que Railway te asigna

### 📌 Puntos clave

- **Sin venv**: Railway instala dependencias automáticamente desde `requirements.txt`
- **Auto-inicialización**: El script `init_db_auto.py` crea la BD, tablas y datos de muestra
- **Health check**: Endpoint `/health` disponible para Railway
- **Logs**: Revisa los logs en Railway → Deployments → View Logs si hay problemas

### 🔧 Troubleshooting

| Problema | Solución |
|----------|----------|
| Error 500 | Revisa logs en Railway. Asegúrate de que `DB_USER` no esté vacío |
| Tablas no existen | Espera a que `init_db_auto.py` termine (mira los logs del deployment) |
| Conexión rechazada | Verifica que las variables `DB_*` usen referencias del plugin (`${{MySQL....}}`) |
| Puerto incorrecto | Railway asigna automáticamente el `PORT`. No lo hardcodees. |

---

## 💻 Desarrollo local (sin Railway)

Si quieres trabajar localmente:

1. **Instala MySQL en tu máquina**
2. **Crea el archivo `.env`:**
   ```
   FLASK_ENV=development
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=tu-contraseña
   DB_NAME=cinema_caribe
   SECRET_KEY=clave-secreta-local
   ```
3. **Instala dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Inicializa la BD:**
   ```bash
   python init_db.py
   ```
5. **Ejecuta la app:**
   ```bash
   python app.py
   ```
   - Accede a `http://localhost:5000`



## 🗄️ Esquema de base de datos

```
usuarios ──────────────────────────────────┐
peliculas ──┬── funciones ──┬── tiquetes ──┤
            │               │              └── detalle_tiquete
salas ──────┘    asientos ──┘
                             └── funcion_asiento  (UNIQUE: funcion_id + asiento_id)
```

### Regla crítica de integridad
La tabla `funcion_asiento` tiene **PRIMARY KEY compuesta (funcion_id, asiento_id)**, garantizando a nivel de base de datos que ningún asiento pueda venderse dos veces para la misma función. Además, la lógica de negocio usa **SELECT ... FOR UPDATE** para prevenir race-conditions bajo concurrencia.

---

## 🛠️ Tecnologías

| Capa       | Tecnología                              |
|------------|-----------------------------------------|
| Backend    | Python 3.10+, Flask 3.0                 |
| Base datos | MySQL 8.0, mysql-connector-python       |
| Frontend   | Bootstrap 5.3, Vanilla JS               |
| Fuentes    | Google Fonts (Pacifico, Bebas Neue, Nunito) |
| QR         | qrcode + Pillow                         |
| Deploy     | Railway + Gunicorn                      |

---

## 📝 Licencia

MIT — Cinema Caribe © 2024
