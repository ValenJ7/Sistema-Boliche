# db.py
import sqlite3

DB_PATH = "disco.db"

def get_conn():
    """Conexión SQLite con row_factory + WAL + FK."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Crea/actualiza tablas si no existen."""
    with get_conn() as conn:
        # Eventos
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            fecha     TEXT NOT NULL,   -- YYYY-MM-DD
            hora      TEXT NOT NULL,   -- HH:MM
            capacidad INTEGER NOT NULL,
            estado    TEXT NOT NULL CHECK (estado IN ('activo','inactivo')) DEFAULT 'activo',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Lotes de venta (batches)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sale_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        );
        """)

        # Ventas (drinks)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            nombre    TEXT NOT NULL,
            precio    REAL NOT NULL,
            cantidad  INTEGER NOT NULL CHECK (cantidad > 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            batch_id  INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY (batch_id) REFERENCES sale_batches(id) ON DELETE SET NULL
        );
        """)

        # Si la tabla drinks ya existía sin batch_id, lo agregamos (ignorar error si ya está)
        try:
            conn.execute("ALTER TABLE drinks ADD COLUMN batch_id INTEGER;")
        except sqlite3.OperationalError:
            pass

# ---------- EVENTS ----------
def fetch_all_events():
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, nombre, fecha, hora, capacidad, estado
            FROM events
            ORDER BY date(fecha) ASC, time(hora) ASC, id ASC
        """)
        return [dict(r) for r in cur.fetchall()]

def fetch_event_by_id(event_id: int):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, nombre, fecha, hora, capacidad, estado
            FROM events
            WHERE id = ?
        """, (event_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def insert_event(nombre: str, fecha: str, hora: str, capacidad: int, estado: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO events (nombre, fecha, hora, capacidad, estado)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, fecha, hora, capacidad, estado))

def update_event(event_id: int, nombre: str, fecha: str, hora: str, capacidad: int, estado: str):
    with get_conn() as conn:
        conn.execute("""
            UPDATE events
            SET nombre = ?, fecha = ?, hora = ?, capacidad = ?, estado = ?
            WHERE id = ?
        """, (nombre, fecha, hora, capacidad, estado, event_id))

def delete_event(event_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

# ---------- BATCHES ----------
def create_sale_batch(event_id: int) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO sale_batches (event_id) VALUES (?)", (event_id,))
        return cur.lastrowid

def fetch_batches_by_event(event_id: int):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT b.id, b.created_at,
                   COALESCE(SUM(d.cantidad), 0) AS items_count,
                   COALESCE(SUM(d.precio * d.cantidad), 0) AS total_amount
            FROM sale_batches b
            LEFT JOIN drinks d ON d.batch_id = b.id
            WHERE b.event_id = ?
            GROUP BY b.id
            ORDER BY b.created_at DESC, b.id DESC
        """, (event_id,))
        return [dict(r) for r in cur.fetchall()]

def fetch_drinks_by_batch(batch_id: int):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, event_id, nombre, precio, cantidad, created_at, batch_id
            FROM drinks
            WHERE batch_id = ?
            ORDER BY id ASC
        """, (batch_id,))
        return [dict(r) for r in cur.fetchall()]

# ---------- DRINKS ----------
def fetch_drinks_by_event(event_id: int):
    """Detalle plano (por registro). Útil para búsquedas/eliminar."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, event_id, nombre, precio, cantidad, created_at, batch_id
            FROM drinks
            WHERE event_id = ?
            ORDER BY created_at DESC, id DESC
        """, (event_id,))
        return [dict(r) for r in cur.fetchall()]

def fetch_drink_by_id(drink_id: int):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, event_id, nombre, precio, cantidad, created_at, batch_id
            FROM drinks
            WHERE id = ?
        """, (drink_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def insert_drink(event_id: int, nombre: str, precio: float, cantidad: int, batch_id: int | None = None):
    with get_conn() as conn:
        if batch_id is None:
            conn.execute("""
                INSERT INTO drinks (event_id, nombre, precio, cantidad)
                VALUES (?, ?, ?, ?)
            """, (event_id, nombre, precio, cantidad))
        else:
            conn.execute("""
                INSERT INTO drinks (event_id, nombre, precio, cantidad, batch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (event_id, nombre, precio, cantidad, batch_id))

def update_drink(drink_id: int, nombre: str, precio: float, cantidad: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE drinks
            SET nombre = ?, precio = ?, cantidad = ?
            WHERE id = ?
        """, (nombre, precio, cantidad, drink_id))

def delete_drink(drink_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM drinks WHERE id = ?", (drink_id,))

def fetch_drinks_summary_by_event(event_id: int):
    """Resumen agrupado por trago."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT nombre, precio,
                   SUM(cantidad) AS cantidad,
                   SUM(precio * cantidad) AS total
            FROM drinks
            WHERE event_id = ?
            GROUP BY nombre, precio
            ORDER BY total DESC, nombre ASC
        """, (event_id,))
        return [dict(r) for r in cur.fetchall()]
