"""
Backtest histórico honesto del modelo 1-X-2.

Regla que lo hace válido (y que distingue un backtest real de uno tramposo):
para predecir un partido jugado el día D, la fuerza de cada equipo se calcula
SOLO con sus partidos anteriores a D. Nada de usar la forma "de ahora" para
adivinar el pasado — eso es mirar el resultado antes de apostar (lookahead) y
dispara la precisión de forma ficticia.

Esto NO es lo mismo que la precisión en vivo (pronósticos emitidos antes del
partido y resueltos después). El backtest es evidencia más débil: dice cómo
habría acertado el modelo en el pasado con los datos de entonces. Se etiqueta
siempre como "backtest", nunca como precisión en vivo.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

from stats_engine import StatsEngine
import real_stats

BASE = "https://site.api.espn.com/apis"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest.json")

PARTIDOS_MINIMOS = 4   # historial previo mínimo para modelar un equipo


def _historial(espn, slug, team_id):
    """Todos los partidos terminados de un equipo, con fecha y perspectiva propia.

    Devuelve lista [{date, gf, ga, res}] ordenada de más antiguo a más nuevo.
    res: 'W' | 'D' | 'L' desde el punto de vista del equipo.
    """
    year = datetime.now().year
    out = []
    for season in (year, year - 1):
        url = f"{BASE}/site/v2/sports/soccer/{slug}/teams/{team_id}/schedule?season={season}"
        try:
            data = espn._get(url, ttl=3600)
        except Exception:
            data = None
        for ev in (data or {}).get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            if comp.get("status", {}).get("type", {}).get("state") != "post":
                continue
            mine = rival = None
            for c in comp.get("competitors", []):
                sc = c.get("score")
                sc = sc.get("value") if isinstance(sc, dict) else sc
                try:
                    sc = int(float(sc))
                except (TypeError, ValueError):
                    continue
                if str(c.get("team", {}).get("id")) == str(team_id):
                    mine = sc
                else:
                    rival = sc
            if mine is None or rival is None:
                continue
            res = "W" if mine > rival else "L" if mine < rival else "D"
            out.append({"date": ev.get("date", "")[:10], "gf": mine, "ga": rival, "res": res})
    out.sort(key=lambda m: m["date"])
    # dedup por fecha (las dos temporadas pueden solapar)
    visto, limpio = set(), []
    for m in out:
        if m["date"] in visto:
            continue
        visto.add(m["date"]); limpio.append(m)
    return limpio


def _fuerza_asof(historial, antes_de, nombre):
    """Fuerza del equipo usando SOLO partidos anteriores a `antes_de`."""
    previos = [m for m in historial if m["date"] < antes_de][-8:]
    if len(previos) < PARTIDOS_MINIMOS:
        return None
    n = len(previos)
    gf = sum(m["gf"] for m in previos) / n
    ga = sum(m["ga"] for m in previos) / n
    win_pct = 100.0 * sum(1 for m in previos if m["res"] == "W") / n
    forma = [m["res"] for m in previos[-5:]][::-1]  # más reciente primero
    return {
        "name": nombre,
        "sofa_rating": real_stats._rating(win_pct, gf, ga),
        "form": forma,
        "attack": {"goals_per_game": gf, "corners": 5.0, "shots_on_target": 4.5},
        "defense": {"goals_conceded": ga},
        "summary": {"yellow_cards_per_game": 2.0},
    }


def correr(espn, dias_atras=60, dias_min_antiguedad=2, max_partidos=400):
    """Recorre partidos pasados terminados y mide el acierto 1-X-2 del modelo.

    dias_min_antiguedad: ignora lo muy reciente (deja que ESPN consolide).
    Devuelve dict con totales y desglose por liga.
    """
    hoy = datetime.now(timezone.utc).date()
    fechas = [(hoy - timedelta(days=d)).strftime("%Y-%m-%d")
              for d in range(dias_min_antiguedad, dias_atras + dias_min_antiguedad)]

    # Recolecta partidos terminados de ligas principales.
    partidos = []
    for f in fechas:
        try:
            bloques = espn.get_matches_by_date(f)
        except Exception:
            continue
        for b in bloques or []:
            if b.get("extra"):
                continue
            for m in b.get("matches", []):
                if not m.get("completed"):
                    continue
                try:
                    h = int(m["home"].get("score")); a = int(m["away"].get("score"))
                except (TypeError, ValueError):
                    continue
                partidos.append({
                    "slug": b["slug"], "liga": b["league"], "fecha": (m.get("date") or "")[:10],
                    "hid": m["home"].get("id"), "aid": m["away"].get("id"),
                    "home": m["home"].get("name"), "away": m["away"].get("name"),
                    "real": "1" if h > a else "2" if a > h else "X",
                    "real_btts": (h > 0 and a > 0),
                    "real_o25": (h + a) > 2.5,
                })
                if len(partidos) >= max_partidos:
                    break

    # Cachea el historial de cada equipo una sola vez.
    equipos = {}
    for p in partidos:
        equipos[(p["slug"], str(p["hid"]))] = None
        equipos[(p["slug"], str(p["aid"]))] = None

    def cargar(clave):
        slug, tid = clave
        return clave, _historial(espn, slug, tid)

    with ThreadPoolExecutor(max_workers=12) as pool:
        for clave, hist in pool.map(cargar, list(equipos)):
            equipos[clave] = hist

    # Bandas de confianza: ¿un pick al 70% de verdad acierta ~70% de las
    # veces, o el modelo está mal calibrado (dice más de lo que sabe)?
    # Se mide para 1X2, BTTS y Over 2.5 por separado, porque son los
    # mercados que más se combinan.
    BANDAS = [(0, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 101)]

    def banda_de(pct):
        for lo, hi in BANDAS:
            if lo <= pct < hi:
                return f"{lo}-{hi}%"
        return "?"

    total = aciertos = descartados = 0
    por_liga = {}
    calibracion = {"1x2": {}, "btts": {}, "o25": {}}

    for p in partidos:
        hl = equipos.get((p["slug"], str(p["hid"])))
        al = equipos.get((p["slug"], str(p["aid"])))
        if not hl or not al:
            descartados += 1; continue
        local = _fuerza_asof(hl, p["fecha"], p["home"])
        visit = _fuerza_asof(al, p["fecha"], p["away"])
        if not local or not visit:
            descartados += 1; continue

        sim = StatsEngine.simulate_match(local, visit, simulations=6000)
        pr = sim["probabilities"]
        pick, pick_prob = max((("1", pr["home_win"]), ("X", pr["draw"]), ("2", pr["away_win"])),
                               key=lambda t: t[1])
        ok = (pick == p["real"])
        total += 1; aciertos += 1 if ok else 0
        L = por_liga.setdefault(p["liga"], {"n": 0, "aciertos": 0})
        L["n"] += 1; L["aciertos"] += 1 if ok else 0

        def registrar(mercado, prob_pick, acierto):
            b = calibracion[mercado].setdefault(banda_de(prob_pick), {"n": 0, "aciertos": 0})
            b["n"] += 1
            b["aciertos"] += 1 if acierto else 0

        registrar("1x2", pick_prob, ok)

        btts_pick_si = pr["btts"] >= 50
        btts_prob = pr["btts"] if btts_pick_si else (100 - pr["btts"])
        registrar("btts", btts_prob, btts_pick_si == p["real_btts"])

        o25_pick_si = pr["over_2_5_goals"] >= 50
        o25_prob = pr["over_2_5_goals"] if o25_pick_si else (100 - pr["over_2_5_goals"])
        registrar("o25", o25_prob, o25_pick_si == p["real_o25"])

    calibracion_out = {}
    for mercado, bandas in calibracion.items():
        calibracion_out[mercado] = sorted(
            [{"banda": k, "n": v["n"], "aciertos": v["aciertos"],
              "precision_real": round(v["aciertos"] / v["n"] * 100, 1)}
             for k, v in bandas.items() if v["n"] >= 5],
            key=lambda x: x["banda"])

    resultado = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "aciertos": aciertos,
        "descartados": descartados,
        "precision": round(aciertos / total * 100, 1) if total else None,
        "por_liga": sorted(
            [{"liga": k, "n": v["n"], "aciertos": v["aciertos"],
              "precision": round(v["aciertos"] / v["n"] * 100, 1)}
             for k, v in por_liga.items() if v["n"] >= 10],
            key=lambda x: -x["n"]),
        "calibracion": calibracion_out,
        "nota": "Backtest con datos punto-en-el-tiempo (forma previa a cada partido). "
                "Evidencia retrospectiva, no precisión en vivo.",
    }
    return resultado


def guardar_cache(resultado):
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=1)


def leer_cache():
    try:
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


if __name__ == "__main__":
    from espn_fetcher import ESPNFetcher
    import sys
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f"Backtest sobre {dias} días... (puede tardar)")
    r = correr(ESPNFetcher(), dias_atras=dias)
    guardar_cache(r)
    print(f"  partidos evaluados: {r['total']}  (descartados por falta de historial: {r['descartados']})")
    print(f"  precisión 1-X-2: {r['precision']}%")
    for L in r["por_liga"][:8]:
        print(f"   {L['precision']:>5}%  {L['liga']}  ({L['n']})")
    print()
    print("  CALIBRACIÓN (¿un pick al X% acierta ~X% de las veces?)")
    for mercado, bandas in r["calibracion"].items():
        print(f"   -- {mercado} --")
        for b in bandas:
            print(f"      banda {b['banda']:>7}  ->  acierto real {b['precision_real']:>5}%  (n={b['n']})")
