# -*- coding: utf-8 -*-
"""
Módulo de integración con la API pública de ESPN.
Cubre las 17 ligas del Excel "TABLAS DE POSICIONES.xlsx":
posiciones en vivo, partidos por fecha (estilo SofaScore) y
últimos partidos por equipo con estadísticas derivadas.
"""
import os
import requests
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

BASE = "https://site.api.espn.com/apis"

# API-Football (api-sports.io) aporta TODOS los partidos del día que ESPN no
# cubre (solo funciona de ayer a mañana en el plan gratuito).
APISPORTS_FLAGS = {
    "Portugal": "🇵🇹", "Belgium": "🇧🇪", "Poland": "🇵🇱", "South-Korea": "🇰🇷",
    "Egypt": "🇪🇬", "Ukraine": "🇺🇦", "Croatia": "🇭🇷", "Serbia": "🇷🇸",
    "Hungary": "🇭🇺", "Bulgaria": "🇧🇬", "Slovakia": "🇸🇰", "Japan": "🇯🇵",
    "Morocco": "🇲🇦", "Qatar": "🇶🇦", "United-Arab-Emirates": "🇦🇪", "Panama": "🇵🇦",
    "Brazil": "🇧🇷", "Argentina": "🇦🇷", "Chile": "🇨🇱", "Peru": "🇵🇪",
    "Bolivia": "🇧🇴", "Ecuador": "🇪🇨", "Colombia": "🇨🇴", "Uruguay": "🇺🇾",
    "Paraguay": "🇵🇾", "Venezuela": "🇻🇪", "Mexico": "🇲🇽", "USA": "🇺🇸",
    "Canada": "🇨🇦", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Spain": "🇪🇸", "Italy": "🇮🇹",
    "Germany": "🇩🇪", "France": "🇫🇷", "Netherlands": "🇳🇱", "Turkey": "🇹🇷",
    "Greece": "🇬🇷", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Ireland": "🇮🇪", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Sweden": "🇸🇪", "Norway": "🇳🇴", "Denmark": "🇩🇰", "Finland": "🇫🇮",
    "Iceland": "🇮🇸", "Estonia": "🇪🇪", "Latvia": "🇱🇻", "Lithuania": "🇱🇹",
    "Russia": "🇷🇺", "Kazakhstan": "🇰🇿", "Belarus": "🇧🇾", "Georgia": "🇬🇪",
    "Armenia": "🇦🇲", "Azerbaijan": "🇦🇿", "Switzerland": "🇨🇭", "Austria": "🇦🇹",
    "Czech-Republic": "🇨🇿", "Romania": "🇷🇴", "Israel": "🇮🇱", "Cyprus": "🇨🇾",
    "China": "🇨🇳", "India": "🇮🇳", "Thailand": "🇹🇭", "Indonesia": "🇮🇩",
    "Vietnam": "🇻🇳", "Malaysia": "🇲🇾", "Singapore": "🇸🇬", "Australia": "🇦🇺",
    "New-Zealand": "🇳🇿", "Saudi-Arabia": "🇸🇦", "South-Africa": "🇿🇦",
    "Nigeria": "🇳🇬", "Ghana": "🇬🇭", "Kenya": "🇰🇪", "Zimbabwe": "🇿🇼",
    "Zambia": "🇿🇲", "Tanzania": "🇹🇿", "Uganda": "🇺🇬", "Algeria": "🇩🇿",
    "Tunisia": "🇹🇳", "Costa-Rica": "🇨🇷", "Guatemala": "🇬🇹", "Honduras": "🇭🇳",
    "El-Salvador": "🇸🇻", "Nicaragua": "🇳🇮", "Jamaica": "🇯🇲", "Bhutan": "🇧🇹",
    "World": "🌍",
}
APISPORTS_COUNTRY_ES = {
    "Belgium": "Bélgica", "Poland": "Polonia", "South-Korea": "Corea del Sur",
    "Egypt": "Egipto", "Ukraine": "Ucrania", "Croatia": "Croacia",
    "Hungary": "Hungría", "Slovakia": "Eslovaquia", "Japan": "Japón",
    "Morocco": "Marruecos", "Qatar": "Catar", "United-Arab-Emirates": "Emiratos Árabes",
    "Panama": "Panamá", "Brazil": "Brasil", "Peru": "Perú", "Mexico": "México",
    "USA": "Estados Unidos", "Canada": "Canadá", "England": "Inglaterra",
    "Spain": "España", "Italy": "Italia", "Germany": "Alemania", "France": "Francia",
    "Netherlands": "Países Bajos", "Turkey": "Turquía", "Greece": "Grecia",
    "Scotland": "Escocia", "Ireland": "Irlanda", "Wales": "Gales", "Sweden": "Suecia",
    "Norway": "Noruega", "Denmark": "Dinamarca", "Finland": "Finlandia",
    "Iceland": "Islandia", "Russia": "Rusia", "Kazakhstan": "Kazajistán",
    "Belarus": "Bielorrusia", "Switzerland": "Suiza", "Czech-Republic": "Chequia",
    "Romania": "Rumania", "Cyprus": "Chipre", "China": "China", "India": "India",
    "Thailand": "Tailandia", "Indonesia": "Indonesia", "Australia": "Australia",
    "New-Zealand": "Nueva Zelanda", "Saudi-Arabia": "Arabia Saudita",
    "South-Africa": "Sudáfrica", "Costa-Rica": "Costa Rica",
    "El-Salvador": "El Salvador", "World": "Internacional",
}

# Ligas tomadas del Excel del usuario (hoja → liga ESPN)
LEAGUES = {
    "eng.1": {"name": "Premier League",     "country": "Inglaterra",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "eng.2": {"name": "Championship",       "country": "Inglaterra",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "esp.1": {"name": "LaLiga",             "country": "España",        "flag": "🇪🇸"},
    "ita.1": {"name": "Serie A",            "country": "Italia",        "flag": "🇮🇹"},
    "ger.1": {"name": "Bundesliga",         "country": "Alemania",      "flag": "🇩🇪"},
    "fra.1": {"name": "Ligue 1",            "country": "Francia",       "flag": "🇫🇷"},
    "por.1": {"name": "Primeira Liga",      "country": "Portugal",      "flag": "🇵🇹"},
    "ned.1": {"name": "Eredivisie",         "country": "Países Bajos",  "flag": "🇳🇱"},
    "bel.1": {"name": "Pro League",         "country": "Bélgica",       "flag": "🇧🇪"},
    "tur.1": {"name": "Süper Lig",          "country": "Turquía",       "flag": "🇹🇷"},
    "gre.1": {"name": "Super League",       "country": "Grecia",        "flag": "🇬🇷"},
    "col.1": {"name": "Primera A",          "country": "Colombia",      "flag": "🇨🇴"},
    "ecu.1": {"name": "LigaPro",            "country": "Ecuador",       "flag": "🇪🇨"},
    "mex.1": {"name": "Liga MX",            "country": "México",        "flag": "🇲🇽"},
    "ksa.1": {"name": "Pro League Saudí",   "country": "Arabia Saudita","flag": "🇸🇦"},
    "jpn.1": {"name": "J1 League",          "country": "Japón",         "flag": "🇯🇵"},
    "chn.1": {"name": "Super League",       "country": "China",         "flag": "🇨🇳"},
    "bra.1": {"name": "Brasileirão Serie A","country": "Brasil",        "flag": "🇧🇷"},
    "sco.1": {"name": "Premiership",        "country": "Escocia",       "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    "nor.1": {"name": "Eliteserien",        "country": "Noruega",       "flag": "🇳🇴"},
    "swe.1": {"name": "Allsvenskan",        "country": "Suecia",        "flag": "🇸🇪"},
    "chi.1": {"name": "Primera División",   "country": "Chile",         "flag": "🇨🇱"},
    "bol.1": {"name": "Liga Profesional",   "country": "Bolivia",       "flag": "🇧🇴"},
    "per.1": {"name": "Liga 1",             "country": "Perú",          "flag": "🇵🇪"},
    # Finlandia y Rumania: slug correcto, pero ESPN no está devolviendo
    # tabla ni partidos ahora mismo (verificado). Se dejan aquí para que
    # aparezcan en cuanto ESPN publique datos de la temporada en curso.
    "fin.1": {"name": "Veikkausliiga",      "country": "Finlandia",     "flag": "🇫🇮"},
    "rou.1": {"name": "Liga 1",             "country": "Rumania",       "flag": "🇷🇴"},
}


# Ligas secundarias y de otros países: se consultan directo por su código
# porque el scoreboard global de ESPN solo trae las ligas destacadas.
SECONDARY_LEAGUES = {
    # Segundas divisiones de Europa
    "esp.2": {"name": "LaLiga 2",             "country": "España",        "flag": "🇪🇸"},
    "ita.2": {"name": "Serie B",              "country": "Italia",        "flag": "🇮🇹"},
    "ger.2": {"name": "2. Bundesliga",        "country": "Alemania",      "flag": "🇩🇪"},
    "fra.2": {"name": "Ligue 2",              "country": "Francia",       "flag": "🇫🇷"},
    "ned.2": {"name": "Keuken Divisie",       "country": "Países Bajos",  "flag": "🇳🇱"},
    "tur.2": {"name": "1. Lig",               "country": "Turquía",       "flag": "🇹🇷"},
    "eng.3": {"name": "League One",           "country": "Inglaterra",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "eng.4": {"name": "League Two",           "country": "Inglaterra",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "eng.5": {"name": "National League",      "country": "Inglaterra",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "sco.2": {"name": "Championship",         "country": "Escocia",       "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    # Sudamérica
    "arg.1": {"name": "Liga Profesional",     "country": "Argentina",     "flag": "🇦🇷"},
    "arg.2": {"name": "Nacional B",           "country": "Argentina",     "flag": "🇦🇷"},
    "bra.2": {"name": "Serie B",              "country": "Brasil",        "flag": "🇧🇷"},
    "chi.2": {"name": "Segunda División",     "country": "Chile",         "flag": "🇨🇱"},
    "per.2": {"name": "Segunda División",     "country": "Perú",          "flag": "🇵🇪"},
    "par.1": {"name": "Primera División",     "country": "Paraguay",      "flag": "🇵🇾"},
    "uru.1": {"name": "Liga AUF",             "country": "Uruguay",       "flag": "🇺🇾"},
    "ven.1": {"name": "Primera División",     "country": "Venezuela",     "flag": "🇻🇪"},
    "col.2": {"name": "Primera B",            "country": "Colombia",      "flag": "🇨🇴"},
    "ecu.2": {"name": "Serie B",              "country": "Ecuador",       "flag": "🇪🇨"},
    # Norte y Centroamérica
    "usa.1": {"name": "MLS",                  "country": "Estados Unidos","flag": "🇺🇸"},
    "usa.usl.l1": {"name": "USL League One",  "country": "Estados Unidos","flag": "🇺🇸"},
    "mex.2": {"name": "Liga de Expansión",    "country": "México",        "flag": "🇲🇽"},
    "crc.1": {"name": "Primera División",     "country": "Costa Rica",    "flag": "🇨🇷"},
    "gua.1": {"name": "Liga Nacional",        "country": "Guatemala",     "flag": "🇬🇹"},
    "hon.1": {"name": "Liga Nacional",        "country": "Honduras",      "flag": "🇭🇳"},
    "slv.1": {"name": "Primera División",     "country": "El Salvador",   "flag": "🇸🇻"},
    # Resto de Europa
    "rus.1": {"name": "Premier League",       "country": "Rusia",         "flag": "🇷🇺"},
    "cze.1": {"name": "Liga Checa",           "country": "Chequia",       "flag": "🇨🇿"},
    "aut.1": {"name": "Bundesliga",           "country": "Austria",       "flag": "🇦🇹"},
    "sui.1": {"name": "Super League",         "country": "Suiza",         "flag": "🇨🇭"},
    "den.1": {"name": "Superliga",            "country": "Dinamarca",     "flag": "🇩🇰"},
    "irl.1": {"name": "Premier Division",     "country": "Irlanda",       "flag": "🇮🇪"},
    "cyp.1": {"name": "Primera División",     "country": "Chipre",        "flag": "🇨🇾"},
    "isr.1": {"name": "Premier League",       "country": "Israel",        "flag": "🇮🇱"},
    # Asia, África y Oceanía
    "aus.1": {"name": "A-League",             "country": "Australia",     "flag": "🇦🇺"},
    "ind.1": {"name": "Super League",         "country": "India",         "flag": "🇮🇳"},
    "tha.1": {"name": "Thai League 1",        "country": "Tailandia",     "flag": "🇹🇭"},
    "idn.1": {"name": "Super League",         "country": "Indonesia",     "flag": "🇮🇩"},
    "rsa.1": {"name": "Premiership",          "country": "Sudáfrica",     "flag": "🇿🇦"},
    "nga.1": {"name": "Liga Profesional",     "country": "Nigeria",       "flag": "🇳🇬"},
}

# País (en español) por prefijo del slug ESPN, para agrupar por país
PREFIX_COUNTRY_ES = {
    "arg": "Argentina", "bol": "Bolivia", "bra": "Brasil", "chi": "Chile",
    "col": "Colombia", "crc": "Costa Rica", "ecu": "Ecuador", "mex": "México",
    "par": "Paraguay", "per": "Perú", "uru": "Uruguay", "ven": "Venezuela",
    "usa": "Estados Unidos", "can": "Canadá", "eng": "Inglaterra",
    "sco": "Escocia", "wal": "Gales", "irl": "Irlanda", "nir": "Irlanda del Norte",
    "fra": "Francia", "esp": "España", "ita": "Italia", "ger": "Alemania",
    "por": "Portugal", "ned": "Países Bajos", "bel": "Bélgica", "tur": "Turquía",
    "gre": "Grecia", "swe": "Suecia", "nor": "Noruega", "den": "Dinamarca",
    "fin": "Finlandia", "sui": "Suiza", "aut": "Austria", "pol": "Polonia",
    "rus": "Rusia", "ukr": "Ucrania", "cze": "Chequia", "rou": "Rumania",
    "jpn": "Japón", "chn": "China", "kor": "Corea del Sur", "aus": "Australia",
    "ind": "India", "idn": "Indonesia", "tha": "Tailandia", "ksa": "Arabia Saudita",
    "qat": "Catar", "uae": "Emiratos Árabes", "rsa": "Sudáfrica", "nga": "Nigeria",
    "isr": "Israel", "cyp": "Chipre",
    "fifa": "Internacional", "uefa": "Internacional", "conmebol": "Internacional",
    "concacaf": "Internacional", "caf": "Internacional", "afc": "Internacional",
    "club": "Internacional", "global": "Internacional", "nonfifa": "Internacional",
}

# Banderas para las demás competiciones (por prefijo del slug ESPN)
EXTRA_FLAGS = {
    "arg": "🇦🇷", "bol": "🇧🇴", "bra": "🇧🇷", "chi": "🇨🇱", "col": "🇨🇴",
    "crc": "🇨🇷", "ecu": "🇪🇨", "mex": "🇲🇽", "par": "🇵🇾", "per": "🇵🇪",
    "uru": "🇺🇾", "ven": "🇻🇪", "usa": "🇺🇸", "can": "🇨🇦",
    "eng": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "sco": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "wal": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "irl": "🇮🇪", "nir": "🇬🇧",
    "fra": "🇫🇷", "esp": "🇪🇸", "ita": "🇮🇹", "ger": "🇩🇪", "por": "🇵🇹",
    "ned": "🇳🇱", "bel": "🇧🇪", "tur": "🇹🇷", "gre": "🇬🇷", "swe": "🇸🇪",
    "nor": "🇳🇴", "den": "🇩🇰", "fin": "🇫🇮", "sui": "🇨🇭", "aut": "🇦🇹",
    "pol": "🇵🇱", "rus": "🇷🇺", "ukr": "🇺🇦", "cze": "🇨🇿", "rou": "🇷🇴",
    "jpn": "🇯🇵", "chn": "🇨🇳", "kor": "🇰🇷", "aus": "🇦🇺", "ind": "🇮🇳",
    "ksa": "🇸🇦", "qat": "🇶🇦", "uae": "🇦🇪", "rsa": "🇿🇦", "nga": "🇳🇬",
    "fifa": "🌍", "uefa": "🇪🇺", "conmebol": "🌎", "concacaf": "🌎",
    "caf": "🌍", "afc": "🌏", "club": "🤝", "global": "🌍", "nonfifa": "⚽",
}


class ESPNFetcher:
    def __init__(self):
        self._cache = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (FootballPredictor)"})
        self.apisports_key = os.getenv("APISPORTS_API_KEY")
        self._apisports_ok = bool(self.apisports_key)  # se desactiva solo si da 401/403
        # iSports (api.isportsapi.com) — distinto de API-Sports (api-sports.io)
        self.isports_key = (
            os.getenv("ISPORTS_API_KEY")
            or os.getenv("ISPORTSAPI_API_KEY")
            or ""
        ).strip()
        self._isports_ok = bool(self.isports_key)
        self._isports_bases = (
            "https://api.isportsapi.com",
            "https://api2.isportsapi.com",
            "http://api.isportsapi.com",
            "http://api2.isportsapi.com",
        )

    # ── caché simple con TTL ──────────────────────────────
    def _get(self, url, ttl=300):
        now = time.time()
        hit = self._cache.get(url)
        if hit and now - hit[0] < ttl:
            return hit[1]
        try:
            r = self.session.get(url, timeout=12)
            r.raise_for_status()
            data = r.json()
            self._cache[url] = (now, data)
            return data
        except Exception as e:
            print(f"ESPN error [{url}]: {e}")
            return hit[1] if hit else None

    def get_leagues(self):
        principales = [{"slug": k, **v, "extra": False} for k, v in LEAGUES.items()]
        secundarias = [{"slug": k, **v, "extra": True} for k, v in SECONDARY_LEAGUES.items()]
        return principales + secundarias

    # ── NOTICIAS ───────────────────────────────────────────
    def get_news(self, limit=6):
        """Últimas noticias reales de fútbol (ESPN). Cada una enlaza al
        artículo original: no se reescribe ni resume contenido de terceros
        aquí, solo se enlaza."""
        data = self._get(f"{BASE}/site/v2/sports/soccer/all/news", ttl=600)
        articulos = []
        for a in (data or {}).get("articles", [])[:limit]:
            imagenes = a.get("images") or []
            enlace = (a.get("links") or {}).get("web", {}).get("href", "")
            if not a.get("headline") or not enlace:
                continue
            articulos.append({
                "titular": a["headline"],
                "publicado": a.get("published", ""),
                "enlace": enlace,
                "imagen": imagenes[0].get("url", "") if imagenes else "",
            })
        return articulos

    # ── POSICIONES ────────────────────────────────────────
    def get_standings(self, slug):
        """Tabla de posiciones. Si la temporada nueva está en cero,
        cae automáticamente a la temporada anterior."""
        year = datetime.now().year
        last = None
        for season in (None, year, year - 1):
            url = f"{BASE}/v2/sports/soccer/{slug}/standings"
            if season:
                url += f"?season={season}"
            data = self._get(url, ttl=600)
            if not data:
                continue
            table = self._parse_standings(data)
            if table:
                last = table
                if any(t["played"] > 0 for t in table["entries"]):
                    table["season"] = season or "actual"
                    return table
        return last or {"league": LEAGUES.get(slug, {}).get("name", slug), "entries": []}

    def _parse_standings(self, data):
        children = data.get("children") or []
        if not children:
            return None
        entries_out = []
        # algunas ligas (ej. MX con Apertura/Clausura) traen varios grupos
        for child in children:
            for e in child.get("standings", {}).get("entries", []):
                stats = {s.get("name"): s for s in e.get("stats", [])}
                def val(name, default=0):
                    s = stats.get(name) or {}
                    v = s.get("value")
                    return int(v) if v is not None else default
                team = e.get("team", {})
                logos = team.get("logos") or [{}]
                entries_out.append({
                    "group": child.get("name", ""),
                    "rank": val("rank"),
                    "team": team.get("displayName", "?"),
                    "team_id": team.get("id"),
                    "logo": logos[0].get("href", ""),
                    "played": val("gamesPlayed"),
                    "wins": val("wins"),
                    "draws": val("ties"),
                    "losses": val("losses"),
                    "goals_for": val("pointsFor"),
                    "goals_against": val("pointsAgainst"),
                    "goal_diff": val("pointDifferential"),
                    "points": val("points"),
                    "note": (e.get("note") or {}).get("description", ""),
                    "note_color": (e.get("note") or {}).get("color", ""),
                })
        entries_out.sort(key=lambda x: (x["group"], x["rank"]))
        return {"league": data.get("name", ""), "entries": entries_out}

    # ── PARTIDOS POR FECHA (estilo SofaScore) ─────────────
    def get_matches_by_date(self, date_str=None, externas=True):
        """Partidos de TODAS las ligas para una fecha (YYYY-MM-DD).
        Devuelve lista agrupada por liga.
        externas=False: solo ESPN (más rápido para rangos de varios días)."""
        if date_str:
            espn_date = date_str.replace("-", "")
        else:
            espn_date = datetime.now().strftime("%Y%m%d")
        # los scoreboards en vivo se refrescan más seguido
        today = datetime.now().strftime("%Y%m%d")
        ttl = 60 if espn_date == today else 600

        results = []
        extras = []
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {
                pool.submit(self._league_scoreboard, slug, espn_date, ttl): slug
                for slug in list(LEAGUES) + list(SECONDARY_LEAGUES)
            }
            f_global = pool.submit(self._global_scoreboard, espn_date, ttl)
            for fut in as_completed(futures):
                block = fut.result()
                if block and block["matches"]:
                    if block.get("extra"):
                        extras.append(block)
                    else:
                        results.append(block)
            extras += f_global.result()
            api_blocks = []
            isports_blocks = []
            if externas:
                fecha_iso = date_str or datetime.now().strftime("%Y-%m-%d")
                f_apisports = pool.submit(self._apisports_scoreboard, fecha_iso, espn_date == today)
                f_isports = pool.submit(self._isports_scoreboard, fecha_iso, espn_date == today)
                api_blocks = f_apisports.result()
                isports_blocks = f_isports.result()

        # quitar de fuentes externas los partidos que ESPN ya cubre:
        # mismo minuto de inicio (UTC) + nombre similar en local o visitante
        espn_idx = {}
        for b in results + extras:
            for m in b["matches"]:
                tk = (m.get("date") or "")[:16]
                espn_idx.setdefault(tk, []).append(
                    (self._norm_name(m["home"]["name"]), self._norm_name(m["away"]["name"])))

        def es_duplicado(m):
            tk = (m.get("date") or "")[:16]
            nh = self._norm_name(m["home"]["name"])
            na = self._norm_name(m["away"]["name"])
            for eh, ea in espn_idx.get(tk, []):
                if self._similar(nh, eh) or self._similar(na, ea):
                    return True
            return False

        for b in api_blocks + isports_blocks:
            b["matches"] = [m for m in b["matches"] if not es_duplicado(m)]
            if b["matches"]:
                for m in b["matches"]:
                    tk = (m.get("date") or "")[:16]
                    espn_idx.setdefault(tk, []).append(
                        (self._norm_name(m["home"]["name"]), self._norm_name(m["away"]["name"]))
                    )
                extras.append(b)

        # orden fijo según el Excel, luego las demás competiciones del día
        order = list(LEAGUES.keys())
        results.sort(key=lambda b: order.index(b["slug"]))
        extras.sort(key=lambda b: (b["country"], b["league"]))
        return results + extras

    @staticmethod
    def _norm_name(s):
        """Normaliza el nombre de un equipo ('Manta F.C.' → 'manta')."""
        import unicodedata
        s = unicodedata.normalize("NFD", (s or "").lower())
        s = "".join(c for c in s if c.isalnum())
        for fix in ("fc", "cf", "sc", "ac", "cd", "fk", "if", "bk", "us", "kf"):
            if s.startswith(fix) and len(s) > len(fix) + 3:
                s = s[len(fix):]
            if s.endswith(fix) and len(s) > len(fix) + 3:
                s = s[: -len(fix)]
        return s

    @staticmethod
    def _similar(a, b):
        """True si un nombre normalizado contiene al otro ('dila'/'dilagori')."""
        if not a or not b or min(len(a), len(b)) < 4:
            return a == b and a != ""
        return a in b or b in a

    def _apisports_scoreboard(self, date_str, is_today):
        """Partidos de ligas que ESPN no cubre (Portugal 2, Bélgica 2, Polonia,
        Corea, Egipto, etc.) vía API-Football. Una sola petición por fecha.
        Si la clave no es válida se desactiva silenciosamente."""
        if not self._apisports_ok:
            return []
        # el plan gratuito solo permite consultar de ayer a mañana
        try:
            from datetime import timedelta
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
            hoy = datetime.now().date()
            if abs((target - hoy).days) > 1:
                return []
        except ValueError:
            return []
        # cuota gratuita = 100 peticiones/día → caché larga
        ttl = 1800 if is_today else 86400
        url = f"https://v3.football.api-sports.io/fixtures?date={date_str}"
        now = time.time()
        hit = self._cache.get(url)
        if hit and now - hit[0] < ttl:
            data = hit[1]
        else:
            try:
                r = requests.get(url, headers={"x-apisports-key": self.apisports_key}, timeout=20)
                if r.status_code in (401, 403, 499):
                    print(f"API-Sports desactivada (HTTP {r.status_code}): revisa APISPORTS_API_KEY en .env")
                    self._apisports_ok = False
                    return []
                r.raise_for_status()
                data = r.json()
                errors = data.get("errors")
                if errors:
                    print(f"API-Sports error: {errors}")
                    # solo desactivar si es problema de clave/suscripción
                    if isinstance(errors, dict) and ("token" in errors or "requests" in errors):
                        self._apisports_ok = False
                    return []
                self._cache[url] = (now, data)
            except Exception as e:
                print(f"API-Sports error: {e}")
                return hit[1] if hit else []

        # estado API-Sports → estado tipo ESPN
        state_map = {
            "TBD": "pre", "NS": "pre", "PST": "pre",
            "1H": "in", "HT": "in", "2H": "in", "ET": "in", "BT": "in", "P": "in", "LIVE": "in", "INT": "in", "SUSP": "in",
            "FT": "post", "AET": "post", "PEN": "post", "CANC": "post", "ABD": "post", "AWD": "post", "WO": "post",
        }
        groups = {}
        for fx in data.get("response", []):
            lg = fx.get("league", {})
            country = lg.get("country", "")
            lname = lg.get("name", "")
            st = fx.get("fixture", {}).get("status", {})
            short = st.get("short", "NS")
            state = state_map.get(short, "pre")
            goals = fx.get("goals", {})
            teams = fx.get("teams", {})
            th, ta = teams.get("home", {}), teams.get("away", {})
            fid = fx.get("fixture", {}).get("id")
            hid = th.get("id")
            aid = ta.get("id")
            match = {
                "id": f"as{fid}",
                "date": fx.get("fixture", {}).get("date", ""),
                "state": state,
                "status_text": st.get("long", "") if state != "in" else f"{st.get('elapsed', '')}'",
                "completed": state == "post",
                "home": {
                    "name": th.get("name", "?"),
                    "short": th.get("name", ""),
                    "id": f"apisports:{hid}" if hid else f"apisports:h:{fid}",
                    "logo": th.get("logo", ""),
                    "score": goals.get("home"),
                    "winner": th.get("winner", False),
                },
                "away": {
                    "name": ta.get("name", "?"),
                    "short": ta.get("name", ""),
                    "id": f"apisports:{aid}" if aid else f"apisports:a:{fid}",
                    "logo": ta.get("logo", ""),
                    "score": goals.get("away"),
                    "winner": ta.get("winner", False),
                },
                "venue": (fx.get("fixture", {}).get("venue") or {}).get("name", ""),
            }
            key = (country, lname)
            groups.setdefault(key, []).append(match)

        blocks = []
        ckey = lambda c: c if c in APISPORTS_FLAGS else c.replace(" ", "-")
        for (country, lname), matches in groups.items():
            matches.sort(key=lambda m: m["date"])
            blocks.append({
                "slug": f"apisports:{country}:{lname}",
                "league": lname,
                "country": APISPORTS_COUNTRY_ES.get(ckey(country), country),
                "flag": APISPORTS_FLAGS.get(ckey(country), "⚽"),
                "extra": True,
                "apisports": True,
                "matches": matches,
            })
        return blocks

    def _isports_get(self, path, params, ttl=1800):
        """GET a iSports (api / api2). Devuelve data[] o None."""
        if not self._isports_ok:
            return None
        q = {"api_key": self.isports_key, **params}
        cache_key = f"isports:{path}:{sorted((k, v) for k, v in params.items())}"
        now = time.time()
        hit = self._cache.get(cache_key)
        if hit and now - hit[0] < ttl:
            return hit[1]
        last_err = None
        for base in self._isports_bases:
            url = f"{base}{path}"
            try:
                r = self.session.get(url, params=q, timeout=20)
                if r.status_code in (401, 403):
                    print(f"iSports desactivada (HTTP {r.status_code}): revisa ISPORTS_API_KEY")
                    self._isports_ok = False
                    return None
                r.raise_for_status()
                payload = r.json()
                code = payload.get("code")
                if code not in (0, "0", None):
                    msg = str(payload.get("message") or payload.get("msg") or code)
                    low = msg.lower()
                    if "api_key" in low or "invalid" in low or "unauthorized" in low:
                        print(f"iSports desactivada: {msg}")
                        self._isports_ok = False
                        return None
                    print(f"iSports error [{path}]: {msg}")
                    last_err = msg
                    continue
                data = payload.get("data")
                if data is None:
                    data = []
                self._cache[cache_key] = (now, data)
                return data
            except Exception as e:
                last_err = e
                continue
        if last_err:
            print(f"iSports error [{path}]: {last_err}")
        return hit[1] if hit else None

    @staticmethod
    def _isports_state(status):
        """Mapa status iSports → pre/in/post."""
        try:
            st = int(status)
        except (TypeError, ValueError):
            return "pre"
        if st == 0:
            return "pre"
        if st in (1, 2, 3, 4, 5):
            return "in"
        if st == -1:
            return "post"
        # cancelado / aplazado / TBD…
        if st <= -10:
            return "post"
        return "pre"

    def _isports_rows_to_blocks(self, rows):
        """Convierte filas livescores/schedule iSports a bloques tipo ESPN."""
        groups = {}
        for row in rows or []:
            mid = row.get("matchId") or row.get("match_id")
            home_name = row.get("homeName") or row.get("home_name") or "?"
            away_name = row.get("awayName") or row.get("away_name") or "?"
            if not mid or home_name == "?" or away_name == "?":
                continue
            state = self._isports_state(row.get("status"))
            mt = row.get("matchTime") or row.get("match_time") or 0
            try:
                mt = int(mt)
            except (TypeError, ValueError):
                mt = 0
            date_iso = (
                datetime.fromtimestamp(mt, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if mt else ""
            )
            hid = row.get("homeId") or row.get("home_id")
            aid = row.get("awayId") or row.get("away_id")
            hs = row.get("homeScore", row.get("home_score"))
            aws = row.get("awayScore", row.get("away_score"))
            league = row.get("leagueName") or row.get("league_name") or "iSports"
            league_id = str(row.get("leagueId") or row.get("league_id") or "0")
            minute = ((row.get("extraExplain") or {}) or {}).get("minute")
            status_text = ""
            if state == "in" and minute:
                status_text = f"{minute}'"
            elif state == "pre":
                status_text = "No iniciado"
            elif state == "post":
                status_text = "Finalizado"
            match = {
                "id": f"isports:{mid}",
                "date": date_iso,
                "state": state,
                "status_text": status_text,
                "completed": state == "post",
                "home": {
                    "name": home_name,
                    "short": home_name,
                    "id": f"isports:{hid}" if hid else f"isports:h:{mid}",
                    "logo": "",
                    "score": hs,
                    "winner": False,
                },
                "away": {
                    "name": away_name,
                    "short": away_name,
                    "id": f"isports:{aid}" if aid else f"isports:a:{mid}",
                    "logo": "",
                    "score": aws,
                    "winner": False,
                },
                "venue": row.get("location") or "",
            }
            key = (league_id, league)
            groups.setdefault(key, []).append(match)

        blocks = []
        for (league_id, league), matches in groups.items():
            matches.sort(key=lambda m: m["date"] or "")
            blocks.append({
                "slug": f"isports:{league_id}",
                "league": league,
                "country": "Internacional",
                "flag": "🌍",
                "extra": True,
                "isports": True,
                "matches": matches,
            })
        return blocks

    def _isports_scoreboard(self, date_str, is_today):
        """Partidos vía iSports: livescores (hoy) + schedule/basic (fecha)."""
        if not self._isports_ok:
            return []
        ttl = 900 if is_today else 3600
        rows = []
        seen = set()

        def add_rows(chunk):
            for row in chunk or []:
                mid = str(row.get("matchId") or row.get("match_id") or "")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                rows.append(row)

        # Hoy: livescores trae más campos (homeId/awayId, corners…).
        if is_today:
            add_rows(self._isports_get("/sport/football/livescores", {}, ttl=ttl))

        # Cualquier fecha (GMT+0): schedule básico.
        add_rows(self._isports_get(
            "/sport/football/schedule/basic",
            {"date": date_str},
            ttl=ttl,
        ))
        return self._isports_rows_to_blocks(rows)

    def _global_scoreboard(self, espn_date, ttl):
        """Todas las demás competiciones del día (amistosos, copas,
        segundas divisiones, otras ligas) vía el scoreboard global de ESPN."""
        url = f"https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=soccer&dates={espn_date}"
        data = self._get(url, ttl=ttl)
        if not data:
            return []
        sports = data.get("sports") or [{}]
        blocks = []
        for lg in sports[0].get("leagues", []):
            slug = lg.get("slug", "")
            if slug in LEAGUES or slug in SECONDARY_LEAGUES:
                continue  # ya cubierta por consulta directa
            matches = []
            for ev in lg.get("events", []):
                ftype = (ev.get("fullStatus") or {}).get("type", {})
                home, away = {}, {}
                for c in ev.get("competitors", []):
                    side = {
                        "name": c.get("displayName", "?"),
                        "short": c.get("name", ""),
                        "id": c.get("id"),
                        "logo": f"https://a.espncdn.com/i/teamlogos/soccer/500/{c.get('id')}.png",
                        "score": c.get("score", ""),
                        "winner": c.get("winner", False),
                    }
                    if c.get("homeAway") == "home":
                        home = side
                    else:
                        away = side
                if not home or not away:
                    continue
                matches.append({
                    "id": ev.get("id"),
                    "date": ev.get("date"),
                    "state": ftype.get("state", "pre"),
                    "status_text": ftype.get("shortDetail", ev.get("summary", "")),
                    "completed": ftype.get("completed", False),
                    "home": home,
                    "away": away,
                    "venue": "",
                })
            if not matches:
                continue
            matches.sort(key=lambda m: m["date"])
            prefix = slug.split(".")[0]
            blocks.append({
                "slug": slug,
                "league": lg.get("name", slug),
                "country": PREFIX_COUNTRY_ES.get(prefix, "Internacional"),
                "flag": EXTRA_FLAGS.get(prefix, "⚽"),
                "extra": True,
                "matches": matches,
            })
        blocks.sort(key=lambda b: b["league"])
        return blocks

    def _league_scoreboard(self, slug, espn_date, ttl):
        url = f"{BASE}/site/v2/sports/soccer/{slug}/scoreboard?dates={espn_date}"
        data = self._get(url, ttl=ttl)
        if not data:
            return None
        info = LEAGUES.get(slug) or SECONDARY_LEAGUES[slug]
        matches = []
        for ev in data.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            status = ev.get("status", {}).get("type", {})
            home, away = {}, {}
            for c in comp.get("competitors", []):
                side = {
                    "name": c.get("team", {}).get("displayName", "?"),
                    "short": c.get("team", {}).get("shortDisplayName", ""),
                    "id": c.get("team", {}).get("id"),
                    "logo": c.get("team", {}).get("logo", ""),
                    "score": c.get("score", ""),
                    "winner": c.get("winner", False),
                }
                if c.get("homeAway") == "home":
                    home = side
                else:
                    away = side
            matches.append({
                "id": ev.get("id"),
                "date": ev.get("date"),
                "state": status.get("state", "pre"),        # pre | in | post
                "status_text": status.get("shortDetail", ""),
                "completed": status.get("completed", False),
                "home": home,
                "away": away,
                "venue": (comp.get("venue") or {}).get("fullName", ""),
            })
        matches.sort(key=lambda m: m["date"])
        return {"slug": slug, "league": info["name"], "country": info["country"],
                "flag": info["flag"], "extra": slug in SECONDARY_LEAGUES,
                "matches": matches}

    # Estadísticas del boxscore que sí trae ESPN para partidos en vivo,
    # con su etiqueta en español y sufijo de visualización.
    _STATS_VIVO = [
        ("possessionPct", "Posesión", "%"),
        ("totalShots", "Remates", ""),
        ("shotsOnTarget", "A puerta", ""),
        ("wonCorners", "Córners", ""),
        ("foulsCommitted", "Faltas", ""),
        ("yellowCards", "Amarillas", ""),
        ("redCards", "Rojas", ""),
        ("saves", "Atajadas", ""),
    ]

    def get_match_live(self, slug, event_id):
        """Estado en vivo real de un partido: último evento del play-by-play
        de ESPN (con su posición real en la cancha, si ESPN la trae para
        ese tipo de evento) + estadísticas reales del boxscore.

        Nada aquí se inventa: si ESPN no trae coordenadas para el último
        evento, o no trae boxscore para esa liga/partido, esos campos
        simplemente vienen en None/[] — el llamador decide cómo mostrarlo.
        """
        url = f"{BASE}/site/v2/sports/soccer/{slug}/summary?event={event_id}"
        data = self._get(url, ttl=15)
        if not data:
            return None

        header = data.get("header", {})
        comp = (header.get("competitions") or [{}])[0]
        status = comp.get("status", {}).get("type", {})
        home_t, away_t = {}, {}
        for c in comp.get("competitors", []):
            side = {"name": c.get("team", {}).get("displayName", "?"), "score": c.get("score", "")}
            if c.get("homeAway") == "home":
                home_t = side
            else:
                away_t = side

        # ── último evento con datos de la jugada (ESPN los da en orden
        # cronológico ascendente, así que el más reciente es el último) ──
        ultimo = None
        for item in reversed(data.get("commentary", [])):
            play = item.get("play")
            if not play:
                continue
            ultimo = {
                "minuto": (play.get("clock") or {}).get("displayValue", ""),
                "texto": play.get("shortText") or play.get("text") or item.get("text", ""),
                "equipo": (play.get("team") or {}).get("displayName", ""),
                "tipo": (play.get("type") or {}).get("text", ""),
                "x": item.get("fieldPositionX"), "y": item.get("fieldPositionY"),
                "x2": item.get("fieldPosition2X"), "y2": item.get("fieldPosition2Y"),
            }
            break

        # ── estadísticas reales del boxscore, si el partido las trae ──
        stats = []
        equipos_box = (data.get("boxscore") or {}).get("teams") or []
        by_name = {t.get("team", {}).get("displayName"): t for t in equipos_box}
        h_box, a_box = by_name.get(home_t.get("name")), by_name.get(away_t.get("name"))
        if h_box and a_box:
            h_vals = {s.get("name"): s.get("displayValue") for s in h_box.get("statistics", [])}
            a_vals = {s.get("name"): s.get("displayValue") for s in a_box.get("statistics", [])}
            for key, label, suffix in self._STATS_VIVO:
                if key in h_vals and key in a_vals:
                    stats.append({"label": label, "home": h_vals[key], "away": a_vals[key], "suffix": suffix})

        return {
            "estado": status.get("state", ""),
            "minuto_actual": status.get("shortDetail", ""),
            "home": home_t, "away": away_t,
            "ultimo_evento": ultimo,
            "stats": stats,
        }

    # ── ÚLTIMOS PARTIDOS + ESTADÍSTICAS ───────────────────
    def get_team_analysis(self, slug, team_id, limit=8):
        """Últimos partidos de un equipo y estadísticas derivadas
        (forma, promedios de goles, over 2.5, ambos marcan)."""
        year = datetime.now().year
        events = []
        for season in (year, year - 1):
            url = f"{BASE}/site/v2/sports/soccer/{slug}/teams/{team_id}/schedule?season={season}"
            data = self._get(url, ttl=600)
            if not data:
                continue
            for ev in data.get("events", []):
                comp = (ev.get("competitions") or [{}])[0]
                if comp.get("status", {}).get("type", {}).get("state") != "post":
                    continue
                events.append(ev)
            if len(events) >= limit:
                break
        events.sort(key=lambda e: e.get("date", ""), reverse=True)
        events = events[:limit]

        recent, form = [], []
        gf = ga = over25 = btts = wins = draws = losses = 0
        for ev in events:
            comp = (ev.get("competitions") or [{}])[0]
            mine, rival = None, None
            for c in comp.get("competitors", []):
                score_raw = c.get("score")
                score = score_raw.get("value") if isinstance(score_raw, dict) else score_raw
                try:
                    score = int(float(score))
                except (TypeError, ValueError):
                    score = 0
                side = {
                    "name": c.get("team", {}).get("displayName", "?"),
                    "logo": (c.get("team", {}).get("logos") or [{}])[0].get("href", ""),
                    "score": score,
                    "home": c.get("homeAway") == "home",
                }
                if str(c.get("team", {}).get("id")) == str(team_id):
                    mine = side
                else:
                    rival = side
            if not mine or not rival:
                continue
            gf += mine["score"]
            ga += rival["score"]
            total = mine["score"] + rival["score"]
            if total > 2.5:
                over25 += 1
            if mine["score"] > 0 and rival["score"] > 0:
                btts += 1
            if mine["score"] > rival["score"]:
                res = "G"; wins += 1
            elif mine["score"] < rival["score"]:
                res = "P"; losses += 1
            else:
                res = "E"; draws += 1
            form.append(res)
            recent.append({
                "date": ev.get("date", "")[:10],
                "result": res,
                "home_name": mine["name"] if mine["home"] else rival["name"],
                "away_name": rival["name"] if mine["home"] else mine["name"],
                "home_score": mine["score"] if mine["home"] else rival["score"],
                "away_score": rival["score"] if mine["home"] else mine["score"],
            })

        n = max(len(recent), 1)
        return {
            "team_id": team_id,
            "matches": recent,
            "stats": {
                "played": len(recent),
                "wins": wins, "draws": draws, "losses": losses,
                "form": form,  # más reciente primero
                "goals_for_avg": round(gf / n, 2),
                "goals_against_avg": round(ga / n, 2),
                "over25_pct": round(100 * over25 / n),
                "btts_pct": round(100 * btts / n),
                "win_pct": round(100 * wins / n),
            },
        }

    def get_match_analysis(self, slug, home_id, away_id):
        """Análisis comparativo de un partido: últimos partidos de ambos
        equipos + posiciones en la tabla."""
        with ThreadPoolExecutor(max_workers=3) as pool:
            f_home = pool.submit(self.get_team_analysis, slug, home_id)
            f_away = pool.submit(self.get_team_analysis, slug, away_id)
            f_std = pool.submit(self.get_standings, slug)
            home, away, standings = f_home.result(), f_away.result(), f_std.result()

        def rank_of(team_id):
            for e in standings.get("entries", []):
                if str(e.get("team_id")) == str(team_id):
                    return {"rank": e["rank"], "points": e["points"], "played": e["played"]}
            return None

        info = LEAGUES.get(slug) or SECONDARY_LEAGUES.get(slug) or {}
        league_name = info.get("name", slug)
        if info.get("country"):
            league_name += f" ({info['country']})"
        return {
            "league": league_name,
            "home": {**home, "table": rank_of(home_id)},
            "away": {**away, "table": rank_of(away_id)},
        }

    @staticmethod
    def _league_label(slug):
        info = LEAGUES.get(slug) or SECONDARY_LEAGUES.get(slug) or {}
        name = info.get("name", slug)
        if info.get("country"):
            name += f" ({info['country']})"
        return name

    def get_match_analysis_cross(self, home_slug, home_id, away_slug, away_id):
        """Igual que get_match_analysis, pero cada equipo con SU PROPIA liga.

        Necesario para cruces entre equipos de competiciones distintas (la
        opción "Todas las Ligas" del predictor): local y visitante no
        comparten standings, así que cada uno se resuelve contra su propia
        tabla en lugar de forzar un único slug compartido.
        """
        with ThreadPoolExecutor(max_workers=4) as pool:
            f_home = pool.submit(self.get_team_analysis, home_slug, home_id)
            f_away = pool.submit(self.get_team_analysis, away_slug, away_id)
            f_std_h = pool.submit(self.get_standings, home_slug)
            f_std_a = pool.submit(self.get_standings, away_slug)
            home, away = f_home.result(), f_away.result()
            std_h, std_a = f_std_h.result(), f_std_a.result()

        def rank_of(standings, team_id):
            for e in standings.get("entries", []):
                if str(e.get("team_id")) == str(team_id):
                    return {"rank": e["rank"], "points": e["points"], "played": e["played"]}
            return None

        return {
            "home": {**home, "table": rank_of(std_h, home_id), "league": self._league_label(home_slug)},
            "away": {**away, "table": rank_of(std_a, away_id), "league": self._league_label(away_slug)},
        }


if __name__ == "__main__":
    f = ESPNFetcher()
    print("Ligas:", len(f.get_leagues()))
    std = f.get_standings("esp.1")
    print("Posiciones LaLiga:", [(e["rank"], e["team"], e["points"]) for e in std["entries"][:3]])
    hoy = f.get_matches_by_date()
    print("Ligas con partidos hoy:", [(b["league"], len(b["matches"])) for b in hoy])
