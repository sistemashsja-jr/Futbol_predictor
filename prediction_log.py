"""
Registro de pronósticos y medición real de precisión.

La precisión solo significa algo si se cumplen dos reglas, y ambas se
imponen aquí, no por convención:

  1. Un pronóstico se registra SOLO antes del pitido inicial (state == "pre").
     Nunca se pronostica un partido en juego o terminado.
  2. Un pronóstico registrado NUNCA se reescribe (INSERT OR IGNORE). No se
     puede "mejorar" el pronóstico una vez que se conoce el resultado.

Sin esas dos reglas, cualquier cifra de acierto es decorativa.
"""

import os
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions.db")

# Nº mínimo de partidos resueltos antes de publicar una tasa de acierto.
# Por debajo de esto la muestra no dice nada y la UI debe mostrarlo así.
MIN_MUESTRA = 20


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
            CREATE TABLE IF NOT EXISTS predictions (
                match_id     TEXT PRIMARY KEY,
                league_slug  TEXT,
                league_name  TEXT,
                home         TEXT,
                away         TEXT,
                kickoff      TEXT,
                pick         TEXT CHECK (pick IN ('1','X','2')),
                p_home       REAL,
                p_draw       REAL,
                p_away       REAL,
                created_at   TEXT,
                actual       TEXT,
                home_score   INTEGER,
                away_score   INTEGER,
                correct      INTEGER,
                resolved_at  TEXT
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_pendientes ON predictions(actual, kickoff)")


def _pick_from(p_home, p_draw, p_away):
    return max((("1", p_home), ("X", p_draw), ("2", p_away)), key=lambda t: t[1])[0]


def record(match_id, league_slug, league_name, home, away, kickoff,
           p_home, p_draw, p_away, state="pre"):
    """Registra un pronóstico. Devuelve True si se guardó por primera vez.

    Se rechaza si el partido ya empezó: pronosticar un resultado conocido
    contaminaría la precisión.
    """
    if state != "pre" or not match_id:
        return False

    init_db()
    with _conn() as con:
        cur = con.execute(
            """INSERT OR IGNORE INTO predictions
               (match_id, league_slug, league_name, home, away, kickoff,
                pick, p_home, p_draw, p_away, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (str(match_id), league_slug, league_name, home, away, kickoff,
             _pick_from(p_home, p_draw, p_away),
             float(p_home), float(p_draw), float(p_away),
             datetime.now(timezone.utc).isoformat())
        )
        return cur.rowcount == 1


def _resultado_real(m):
    """'1' | 'X' | '2' a partir del marcador final, o None si no es fiable."""
    try:
        h = int(m["home"].get("score"))
        a = int(m["away"].get("score"))
    except (TypeError, ValueError):
        return None, None, None
    return ("1" if h > a else "2" if a > h else "X"), h, a


def resolve_pending(espn, max_fechas=8):
    """Cierra los pronósticos cuyos partidos ya terminaron.

    Agrupa los pendientes por fecha de partido y consulta el marcador real
    a ESPN una vez por fecha. Devuelve el nº de pronósticos resueltos.
    """
    init_db()
    ahora = datetime.now(timezone.utc).isoformat()

    with _conn() as con:
        pendientes = con.execute(
            "SELECT match_id, kickoff FROM predictions WHERE actual IS NULL AND kickoff < ?",
            (ahora,)
        ).fetchall()

    if not pendientes:
        return 0

    por_fecha = {}
    for row in pendientes:
        fecha = (row["kickoff"] or "")[:10]
        if fecha:
            por_fecha.setdefault(fecha, set()).add(str(row["match_id"]))

    resueltos = 0
    for fecha in sorted(por_fecha, reverse=True)[:max_fechas]:
        ids = por_fecha[fecha]
        try:
            bloques = espn.get_matches_by_date(fecha)
        except Exception:
            continue

        for bloque in bloques or []:
            for m in bloque.get("matches", []):
                mid = str(m.get("id"))
                if mid not in ids or not m.get("completed"):
                    continue
                actual, h, a = _resultado_real(m)
                if actual is None:
                    continue
                with _conn() as con:
                    con.execute(
                        """UPDATE predictions
                           SET actual=?, home_score=?, away_score=?,
                               correct = CASE WHEN pick = ? THEN 1 ELSE 0 END,
                               resolved_at=?
                           WHERE match_id=? AND actual IS NULL""",
                        (actual, h, a, actual, ahora, mid)
                    )
                resueltos += 1

    return resueltos


def stats():
    """Precisión medida. Nunca inventa: si no hay muestra, lo dice."""
    init_db()
    with _conn() as con:
        fila = con.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(correct),0) aciertos FROM predictions WHERE actual IS NOT NULL"
        ).fetchone()
        pendientes = con.execute(
            "SELECT COUNT(*) n FROM predictions WHERE actual IS NULL"
        ).fetchone()["n"]
        por_liga = con.execute(
            """SELECT league_name liga, COUNT(*) n, COALESCE(SUM(correct),0) aciertos
               FROM predictions WHERE actual IS NOT NULL
               GROUP BY league_name HAVING n >= ? ORDER BY n DESC LIMIT 6""",
            (MIN_MUESTRA,)
        ).fetchall()

    resueltos = fila["n"]
    aciertos = fila["aciertos"]
    suficiente = resueltos >= MIN_MUESTRA

    return {
        "resueltos": resueltos,
        "aciertos": aciertos,
        "pendientes": pendientes,
        "muestra_minima": MIN_MUESTRA,
        # None mientras la muestra sea insuficiente. La UI NO debe rellenarlo.
        "precision": round(aciertos / resueltos * 100, 1) if suficiente else None,
        "por_liga": [
            {"liga": r["liga"], "n": r["n"],
             "precision": round(r["aciertos"] / r["n"] * 100, 1)}
            for r in por_liga
        ],
    }
