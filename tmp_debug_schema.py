from app import create_app
from utils.db import get_pool

app = create_app('default')
with app.app_context():
    pool = get_pool(app)
    conn = pool.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SHOW CREATE TABLE tiquetes')
    print('tiquetes schema:')
    print(cur.fetchone())
    cur.execute('SHOW CREATE TABLE funciones')
    print('funciones schema:')
    print(cur.fetchone())
    cur.execute("SELECT id, pelicula_id, sala_id, fecha, hora, estado FROM funciones ORDER BY fecha, hora LIMIT 30")
    rows = cur.fetchall()
    print('funciones rows:', len(rows))
    for r in rows:
        print(r)
    cur.close()
    conn.close()
