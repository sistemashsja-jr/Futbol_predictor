"""
Cuentas de usuario vía Google Sign-In (OAuth 2.0 / OpenID Connect).

No hay contraseñas propias: la identidad la confirma Google (el `sub` del
token es el identificador único e inmutable de esa cuenta de Google), y
aquí solo se guarda el perfil básico que Google entrega. El flujo OAuth en
sí vive en app.py (rutas /login/google, /auth/google/callback, /logout);
este módulo solo persiste el usuario resultante.
"""

import os
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions.db")


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                google_sub   TEXT UNIQUE NOT NULL,
                email        TEXT,
                name         TEXT,
                picture      TEXT,
                created_at   TEXT,
                last_login   TEXT
            )
        """)


def get_or_create_user(google_sub, email, name, picture):
    """Busca al usuario por su `sub` de Google; lo crea si es su primer
    login. Actualiza email/nombre/foto y last_login en cada login, por si
    cambiaron en la cuenta de Google."""
    init_db()
    ahora = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute(
            """INSERT INTO users (google_sub, email, name, picture, created_at, last_login)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(google_sub) DO UPDATE SET
                   email=excluded.email, name=excluded.name,
                   picture=excluded.picture, last_login=excluded.last_login""",
            (google_sub, email, name, picture, ahora, ahora)
        )
        row = con.execute("SELECT * FROM users WHERE google_sub=?", (google_sub,)).fetchone()
        return dict(row) if row else None


def get_user(user_id):
    init_db()
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None
