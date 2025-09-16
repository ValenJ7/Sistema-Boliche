import sqlite3

DB_NAME = "disco.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha TEXT NOT NULL,
            capacidad INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activo'
        )
        """)
        conn.commit()

def fetch_all_events():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, fecha, capacidad, estado FROM events ORDER BY fecha")
        rows = cursor.fetchall()
    return rows

def insert_event(nombre, fecha, hora, capacidad, estado):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (nombre, fecha, hora, capacidad, estado) VALUES (?, ?, ?, ?, ?)",
            (nombre, fecha, hora, capacidad, estado)
        )
        conn.commit()
