import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL COLLATE NOCASE,
    precio    INTEGER NOT NULL CHECK (precio >= 0),    -- en pesos (sin decimales)
    cantidad  INTEGER NOT NULL CHECK (cantidad >= 0)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_productos_nombre ON productos(nombre);

CREATE TABLE IF NOT EXISTS facturas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    numero    TEXT,
    fecha     TEXT    NOT NULL,
    cliente   TEXT    NOT NULL,
    total     INTEGER NOT NULL,
    pdf_ruta  TEXT
);

CREATE TABLE IF NOT EXISTS factura_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id      INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    producto_id     INTEGER REFERENCES productos(id) ON DELETE SET NULL,
    nombre          TEXT    NOT NULL,   -- copia: la factura no cambia si editan el producto
    precio_unitario INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    subtotal        INTEGER NOT NULL
);
"""


def conectar(ruta_db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(ruta_db), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.executescript(ESQUEMA)
    return con
