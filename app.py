from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from data_fetcher import FootballDataFetcher
from ai_predictor import AIPredictor
from stats_engine import StatsEngine
from espn_fetcher import ESPNFetcher
import auth
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv

load_dotenv()

import sys

# Determinar si la aplicación se ejecuta dentro de un paquete PyInstaller
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

# Detrás del proxy HTTPS de Render, para que url_for(_external=True)
# (callback de Google OAuth) genere https:// y no http://.
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Necesaria para firmar la cookie de sesión (quién quedó logueado). En
# producción real hay que fijar FLASK_SECRET_KEY en el .env; sin ella,
# cada reinicio del server invalida las sesiones existentes.
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)
if os.getenv("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["PREFERRED_URL_SCHEME"] = "https"

fetcher = FootballDataFetcher()
predictor = AIPredictor()
espn = ESPNFetcher()

# ── Login con Google (OAuth 2.0 / OpenID Connect) ──────────────────────
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


def _google_configurado():
    cid = os.getenv('GOOGLE_CLIENT_ID') or ''
    csec = os.getenv('GOOGLE_CLIENT_SECRET') or ''
    return bool(cid) and bool(csec) and 'your_google' not in cid


@app.route('/login/google')
def login_google():
    if not _google_configurado():
        return ("Falta configurar GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET en el .env "
                "(ver .env.example para instrucciones)."), 500
    redirect_uri = url_for('auth_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def auth_google_callback():
    token = oauth.google.authorize_access_token()
    perfil = token.get('userinfo') or {}
    if not perfil.get('sub'):
        return "No se pudo confirmar la cuenta de Google.", 400
    user = auth.get_or_create_user(
        google_sub=perfil['sub'], email=perfil.get('email'),
        name=perfil.get('name'), picture=perfil.get('picture'),
    )
    session['user_id'] = user['id']
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(request.referrer or url_for('index'))


@app.route('/api/me')
def api_me():
    uid = session.get('user_id')
    if not uid:
        return jsonify(None)
    user = auth.get_user(uid)
    if not user:
        session.pop('user_id', None)
        return jsonify(None)
    return jsonify({'name': user['name'], 'email': user['email'], 'picture': user['picture']})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/predictor')
def predictor_page():
    return render_template('predictor.html')

@app.route('/api/leagues')
def api_leagues():
    leagues = [
        {"code": "WORLD_CUP_2026", "name": "🏆 Copa del Mundo 2026"},
        {"code": "UCL", "name": "🇪🇺 UEFA Champions League"},
        {"code": "LIB", "name": "🏆 Copa Libertadores"},
        {"code": "PD", "name": "🇪🇸 LaLiga (España)"},
        {"code": "PL", "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)"},
        {"code": "SA", "name": "🇮🇹 Serie A (Italia)"},
        {"code": "BL1", "name": "🇩🇪 Bundesliga (Alemania)"},
        {"code": "FL1", "name": "🇫🇷 Ligue 1 (Francia)"},
        {"code": "ELC", "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EFL Championship (Inglaterra)"},
        {"code": "ARG", "name": "🇦🇷 Liga Profesional (Argentina)"},
        {"code": "BRA", "name": "🇧🇷 Brasileirão (Brasil)"},
        {"code": "COL", "name": "🇨🇴 Liga BetPlay (Colombia)"},
        {"code": "MX", "name": "🇲🇽 Liga MX (México)"},
        {"code": "ECU", "name": "🇪🇨 LigaPro (Ecuador)"},
        {"code": "CHI", "name": "🇨🇱 Primera División (Chile)"},
        {"code": "URU", "name": "🇺🇾 Primera División (Uruguay)"},
        {"code": "PAR", "name": "🇵🇾 Primera División (Paraguay)"},
        {"code": "PER", "name": "🇵🇪 Liga 1 (Perú)"},
        {"code": "VEN", "name": "🇻🇪 Liga FUTVE (Venezuela)"},
        {"code": "BOL", "name": "🇧🇴 Liga Tecno (Bolivia)"},
        {"code": "MLS", "name": "🇺🇸 Major League Soccer (EE.UU.)"},
        {"code": "SPL", "name": "🇸🇦 Saudi Pro League (Arabia)"},
        {"code": "PPL", "name": "🇵🇹 Primeira Liga (Portugal)"},
        {"code": "DED", "name": "🇳🇱 Eredivisie (Países Bajos)"},
        {"code": "TSL", "name": "🇹🇷 Süper Lig (Turquía)"},
        {"code": "GRE", "name": "🇬🇷 Super League (Grecia)"},
        {"code": "BEL", "name": "🇧🇪 Jupiler Pro League (Bélgica)"},
        {"code": "SPD", "name": "🇪🇸 Segunda División (España)"},
        {"code": "SB", "name": "🇮🇹 Serie B (Italia)"},
        {"code": "SPR", "name": "🇷🇺 Russian Premier League"},
        {"code": "SPO", "name": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership"},
        {"code": "AUS", "name": "🇦🇹 Austrian Bundesliga"},
        {"code": "J1", "name": "🇯🇵 J1 League (Japón)"},
        {"code": "CSL", "name": "🇨🇳 Chinese Super League"},
        {"code": "ISL", "name": "🇮🇳 Indian Super League"},
        {"code": "CAF", "name": "🌍 CAF Champions League"},
        {"code": "NIG", "name": "🇳🇬 Nigerian Professional League"}
    ]
    return jsonify(leagues)

@app.route('/api/teams')
def api_teams():
    league = request.args.get('league')
    if not league:
        return jsonify([])
    teams = fetcher.get_teams_by_league(league)
    return jsonify(teams)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.json
    home = data.get('home')
    away = data.get('away')
    league = data.get('league')
    
    if not home or not away:
        return jsonify({"error": "Faltan equipos"}), 400
        
    home_stats = fetcher.get_team_stats(home)
    away_stats = fetcher.get_team_stats(away)
    
    # Simulación Monte Carlo
    sim_data = StatsEngine.simulate_match(home_stats, away_stats)
    
    # Datos reales de equipos
    home_rank = home_stats.get('fifa_rank', 50)
    away_rank = away_stats.get('fifa_rank', 50)
    home_form = home_stats.get('form', ['?']*5)
    away_form = away_stats.get('form', ['?']*5)
    home_form_str = " → ".join(home_form)
    away_form_str = " → ".join(away_form)
    home_key = home_stats.get('key_player', 'Desconocido')
    away_key = away_stats.get('key_player', 'Desconocido')
    home_style = home_stats.get('style', '')
    away_style = away_stats.get('style', '')
    home_wc = home_stats.get('wc_history', '')
    away_wc = away_stats.get('wc_history', '')

    # Prompt enriquecido para la IA
    prompt = f"""
    Eres FutboltAI, un analista experto en pronósticos de fútbol de alta precisión. Genera un análisis DETALLADO y PRECISO para el partido {home} vs {away} en {league}.
    
    ═══════════════════════════════════════════════════════
    📊 SIMULACIÓN MONTE CARLO (10,000 iteraciones):
    ═══════════════════════════════════════════════════════
    • Victoria {home}: {sim_data['probabilities']['home_win']}% (Cuota proyectada: {sim_data['odds']['home']})
    • Empate: {sim_data['probabilities']['draw']}% (Cuota proyectada: {sim_data['odds']['draw']})
    • Victoria {away}: {sim_data['probabilities']['away_win']}% (Cuota proyectada: {sim_data['odds']['away']})
    • Marcador más probable: {sim_data['exact_score']['score']} (Prob: {sim_data['exact_score']['probability']}%)
    • xG Local: {sim_data['expected_values']['home_goals']} | xG Visitante: {sim_data['expected_values']['away_goals']}
    • Over 2.5 Goles: {sim_data['probabilities']['over_2_5_goals']}% (Cuota: {sim_data['odds']['over_2_5']})
    • Ambos Marcan (BTTS): {sim_data['probabilities']['btts']}% (Cuota: {sim_data['odds']['btts']})
    • Córners esperados: {sim_data['expected_values']['total_corners']}
    • Tarjetas amarillas: {sim_data['expected_values']['total_cards']}
    • Saques de puerta (Goal Kicks): {sim_data['expected_values']['total_goalkicks']}
    • Saques de banda (Throw-ins): {sim_data['expected_values']['total_throwins']}
    • Paradas del portero (Saves): {sim_data['expected_values']['total_saves']} (Local: {sim_data['expected_values']['home_saves']} | Visitante: {sim_data['expected_values']['away_saves']})
    • Remates Totales (Total Shots): {sim_data['expected_values']['total_total_shots']} (Local: {sim_data['expected_values']['home_total_shots']} | Visitante: {sim_data['expected_values']['away_total_shots']})
    • Tiros al Arco (Shots on Target): {sim_data['expected_values']['total_shots']} (Local: {sim_data['expected_values']['home_shots']} | Visitante: {sim_data['expected_values']['away_shots']})
    
    ═══════════════════════════════════════════════════════
    📈 MODIFICADORES E IMPULSORES CLAVE:
    ═══════════════════════════════════════════════════════
    • Ajuste total de rendimiento local: {sim_data['modifiers']['home_modifier']}%
    • Ajuste total de rendimiento visitante: {sim_data['modifiers']['away_modifier']}%
    • Ventaja por factor local: +{sim_data['modifiers']['home_advantage']}%
    • Diferencia de calidad SofaScore: {sim_data['modifiers']['quality_diff']} pts
    • Nivel de forma local: {sim_data['modifiers']['home_form']}% | Visitante: {sim_data['modifiers']['away_form']}%
    
    ═══════════════════════════════════════════════════════
    🏆 PERFIL REAL DE EQUIPOS:
    ═══════════════════════════════════════════════════════
    
    🏠 {home} (Ranking FIFA: #{home_rank}):
    • Forma reciente (últimos 5): {home_form_str}
    • Goles por partido: {home_stats['attack']['goals_per_game']} | Concedidos: {home_stats['defense']['goals_conceded']}
    • Tiros al arco: {home_stats['attack']['shots_on_target']} | Córners: {home_stats['attack']['corners']}
    • Estilo de juego: {home_style}
    • Jugador clave: {home_key}
    • Historia en Mundiales: {home_wc}
    
    ✈️ {away} (Ranking FIFA: #{away_rank}):
    • Forma reciente (últimos 5): {away_form_str}
    • Goles por partido: {away_stats['attack']['goals_per_game']} | Concedidos: {away_stats['defense']['goals_conceded']}
    • Tiros al arco: {away_stats['attack']['shots_on_target']} | Córners: {away_stats['attack']['corners']}
    • Estilo de juego: {away_style}
    • Jugador clave: {away_key}
    • Historia en Mundiales: {away_wc}
    
    ═══════════════════════════════════════════════════════
    Escribe en ESPAÑOL con tono analítico profesional:
    
    ### 🏟️ Análisis Táctico y de Forma
    (Compara estilos, forma reciente, ventajas/desventajas tácticas, jugadores clave)
    
    ### ⚽ Pronóstico de Goles y Marcador
    (xG, Over/Under, BTTS, marcador más probable, cuota proyectada de valor y por qué)
    
    ### 📐 Córners y Tarjetas
    (Análisis de la simulación Monte Carlo e implicaciones tácticas)
    
    ### 🔮 Conclusión Final y Veredicto
    (Veredicto claro y cuota de apuesta con mejor balance de riesgo/recompensa basada en los modificadores)
    """

    
    ai_response = predictor.get_prediction({
        "message": prompt,
        "data_context": sim_data
    })
    
    return jsonify({
        "sim_data": sim_data,
        "ai_prediction": ai_response,
        "home_crest": fetcher.get_crest(home),
        "away_crest": fetcher.get_crest(away),
        "home_rank": home_stats.get('fifa_rank', ''),
        "away_rank": away_stats.get('fifa_rank', ''),
        "home_form": home_stats.get('form', []),
        "away_form": away_stats.get('form', []),
    })

# ══════════ INTEGRACIÓN CON OBSIDIAN ══════════
import re
from datetime import datetime

# En local apunta a tu bóveda; en Render (sin OBSIDIAN_VAULT) se desactiva.
OBSIDIAN_VAULT = os.getenv("OBSIDIAN_VAULT", r"D:\OBSIDIAN MEMORY\HIKI")
_OBSIDIAN_ACTIVO = bool(os.getenv("OBSIDIAN_VAULT")) or not os.getenv("RENDER")


def _obsidian_write(subcarpeta, nombre, contenido):
    """Escribe una nota Markdown en la bóveda de Obsidian (solo si hay ruta usable)."""
    if not _OBSIDIAN_ACTIVO:
        return None
    carpeta = os.path.join(OBSIDIAN_VAULT, "FutboltAI", subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    seguro = re.sub(r'[<>:"/\\|?*]', '', nombre).strip()
    ruta = os.path.join(carpeta, seguro)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta

def _guardar_prediccion(d):
    """Escribe (o sobreescribe) la nota de una predicción en Obsidian."""
    home, away = d.get('home', '?'), d.get('away', '?')
    liga = d.get('league', '')
    fecha = d.get('date') or datetime.now().strftime('%Y-%m-%d')
    sim = d.get('sim_data') or {}
    ai = d.get('ai_prediction', '')
    p = sim.get('probabilities', {})
    ex = sim.get('exact_score', {})
    odds = sim.get('odds', {})
    mk = sim.get('markets', {})

    def tabla_mercado(titulo, m, lineas):
        if not m:
            return ""
        filas = "\n".join(
            f"| Más de {ln} | {m.get('o' + ln.replace('.', ''), '?')}% | {m.get('u' + ln.replace('.', ''), '?')}% |"
            for ln in lineas)
        return f"\n### {titulo} (esperados: {m.get('expected', '?')})\n| Línea | Sí | No |\n|---|---|---|\n{filas}\n"

    contenido = f"""---
tipo: prediccion
fecha: {fecha}
liga: "{liga}"
local: "{home}"
visitante: "{away}"
prob_local: {p.get('home_win', '')}
prob_empate: {p.get('draw', '')}
prob_visitante: {p.get('away_win', '')}
marcador_probable: "{ex.get('score', '')}"
tags: [futboltai, prediccion]
---

# ⚽ {home} vs {away}
**Liga:** {liga} · **Fecha:** {fecha}

## 🎯 Probabilidades (Monte Carlo 10,000 sim.)
| Resultado | Probabilidad | Cuota |
|---|---|---|
| {home} | {p.get('home_win', '?')}% | {odds.get('home', '?')} |
| Empate | {p.get('draw', '?')}% | {odds.get('draw', '?')} |
| {away} | {p.get('away_win', '?')}% | {odds.get('away', '?')} |

**Marcador probable:** {ex.get('score', '?')} ({ex.get('probability', '?')}%) · **Ambos marcan:** {p.get('btts', '?')}%

## 📊 Mercados
{tabla_mercado('⚽ Goles', mk.get('goals'), ['1.5', '2.5', '3.5'])}{tabla_mercado('⏱️ Goles 1er Tiempo', mk.get('first_half'), ['0.5', '1.5', '2.5'])}{tabla_mercado('🚩 Córners', mk.get('corners'), ['8.5', '9.5', '10.5'])}{tabla_mercado('🟨 Tarjetas', mk.get('cards'), ['3.5', '4.5', '5.5'])}
## 🤖 Análisis IA
{ai}

---
*Generado por FutboltAI el {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    try:
        ruta = _obsidian_write("Predicciones", f"{fecha} {home} vs {away}.md", contenido)
        if ruta is None:
            return jsonify({"ok": False, "error": "Obsidian no disponible en este servidor"}), 501
        return jsonify({"ok": True, "path": ruta})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/obsidian/daily_note', methods=['POST'])
def obsidian_daily_note():
    d = request.json or {}
    fecha = d.get('date') or datetime.now().strftime('%Y-%m-%d')
    blocks = d.get('blocks') or espn.get_matches_by_date(fecha)

    lineas = []
    total = 0
    for b in blocks:
        lineas.append(f"\n## {b.get('flag', '')} {b.get('league', '')} ({b.get('country', '')})")
        for m in b.get('matches', []):
            total += 1
            hora = (m.get('date') or '')[11:16]
            h, a = m.get('home', {}), m.get('away', {})
            if m.get('state') in ('in', 'post'):
                estado = '🔴 EN VIVO' if m['state'] == 'in' else '✅ Final'
                lineas.append(f"- {estado} · **{h.get('name')} {h.get('score', '')} - {a.get('score', '')} {a.get('name')}**")
            else:
                lineas.append(f"- 🕐 {hora} UTC · {h.get('name')} vs {a.get('name')}")

    contenido = f"""---
tipo: partidos-del-dia
fecha: {fecha}
total_partidos: {total}
tags: [futboltai, partidos]
---

# 📅 Partidos del {fecha}
{chr(10).join(lineas)}

---
*Generado por FutboltAI el {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    try:
        ruta = _obsidian_write("Partidos", f"{fecha} Partidos.md", contenido)
        if ruta is None:
            return jsonify({"ok": False, "error": "Obsidian no disponible en este servidor", "total": total}), 501
        return jsonify({"ok": True, "path": ruta, "total": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/health')
def health():
    """Healthcheck para Render / monitoreo."""
    return jsonify({"ok": True, "service": "futbol-predictor"})

# ══════════ PARTIDOS / POSICIONES (ESPN) ══════════

@app.route('/partidos')
def partidos():
    return render_template('partidos.html')

@app.route('/api/espn/leagues')
def espn_leagues():
    return jsonify(espn.get_leagues())


@app.route('/api/news')
def api_news():
    return jsonify(espn.get_news(limit=6))

@app.route('/api/espn/matches')
def espn_matches():
    date = request.args.get('date')  # YYYY-MM-DD (opcional, por defecto hoy)
    return jsonify(espn.get_matches_by_date(date))

@app.route('/api/espn/standings')
def espn_standings():
    league = request.args.get('league', 'esp.1')
    return jsonify(espn.get_standings(league))

@app.route('/api/espn/match_live')
def espn_match_live():
    """Último evento real + estadísticas reales del boxscore para un
    partido en vivo (vista 'Cancha' de Partidos)."""
    slug = request.args.get('league')
    event_id = request.args.get('event')
    if not slug or not event_id:
        return jsonify({'error': 'faltan parámetros league/event'}), 400
    data = espn.get_match_live(slug, event_id)
    if not data:
        return jsonify({'error': 'sin datos para este partido'}), 404
    return jsonify(data)

@app.route('/api/espn/analysis')
def espn_analysis():
    league = request.args.get('league')
    home = request.args.get('home')
    away = request.args.get('away')
    if not league or not home or not away:
        return jsonify({"error": "Faltan parámetros (league, home, away)"}), 400
    return jsonify(espn.get_match_analysis(league, home, away))

def _to_engine_stats(side):
    """Convierte el análisis ESPN al formato que espera StatsEngine.
    Compartida por /api/predict_league y /api/predict_cross."""
    s = side.get('stats', {})
    table = side.get('table') or {}
    gf = s.get('goals_for_avg', 1.3)
    ga = s.get('goals_against_avg', 1.3)
    win_pct = s.get('win_pct', 40) / 100.0
    # rating estimado a partir de rendimiento reciente y posición
    rank = table.get('rank')
    rank_q = max(0.0, 1.0 - (rank - 1) / 19.0) if rank else 0.5
    rating = round(6.3 + 1.4 * (0.55 * win_pct + 0.45 * rank_q), 2)
    form = ['W' if f == 'G' else 'D' if f == 'E' else 'L' for f in s.get('form', [])][:5]
    return {
        "sofa_rating": rating,
        "form": form,
        "attack": {
            "goals_per_game": gf,
            "shots_on_target": round(2.2 + gf * 1.8, 1),
            "corners": round(3.8 + gf * 0.9, 1),
            "total_shots": round(7.5 + gf * 3.0, 1),
        },
        "defense": {"goals_conceded": ga},
        "summary": {
            "yellow_cards_per_game": 2.1,
            "avg_goal_kicks": 7.5,
            "avg_throw_ins": 21.0,
            "avg_saves": round(1.5 + ga * 1.2, 1),
        },
    }


def _recent_str(side):
    return "\n".join(
        f"      {m['date']}: {m['home_name']} {m['home_score']}-{m['away_score']} {m['away_name']} ({m['result']})"
        for m in side.get('matches', [])[:5]
    ) or "      Sin datos"


_ANALYSIS_FOCUS = {
    'completo': 'Análisis completo de todos los mercados.',
    'corners': 'Enfócate especialmente en el mercado de CÓRNERS.',
    'goles': 'Enfócate especialmente en el mercado de GOLES (Over/Under, marcador exacto).',
    'tactico': 'Enfócate especialmente en el ANÁLISIS TÁCTICO de ambos equipos.',
    'btts': 'Enfócate especialmente en el mercado AMBOS MARCAN (BTTS).',
}


@app.route('/api/predict_league', methods=['POST'])
def api_predict_league():
    """Predicción para partidos de liga con datos reales de ESPN:
    últimos partidos + posiciones → Monte Carlo → análisis IA."""
    try:
        data = request.json or {}
        slug = data.get('league_slug')
        home_id = data.get('home_id')
        away_id = data.get('away_id')
        home = data.get('home')
        away = data.get('away')
        league_name = data.get('league', slug)
        analysis_type = data.get('analysis_type', 'completo')

        if not slug or not home_id or not away_id:
            return jsonify({"error": "Faltan parámetros (league_slug, home_id, away_id)"}), 400

        an = espn.get_match_analysis(slug, home_id, away_id)

        home_engine = _to_engine_stats(an['home'])
        away_engine = _to_engine_stats(an['away'])
        n_sims = 2500 if os.getenv("RENDER") else 10000
        sim_data, sim_raw = StatsEngine.simulate_match(
            home_engine, away_engine, simulations=n_sims, return_raw=True
        )

        recent_str = _recent_str
        ht, at = an['home'].get('table') or {}, an['away'].get('table') or {}
        hs, as_ = an['home']['stats'], an['away']['stats']

        focus = _ANALYSIS_FOCUS.get(analysis_type, 'Análisis completo.')

        prompt = f"""
    Eres FutboltAI, analista experto en pronósticos de fútbol. Genera un análisis DETALLADO para {home} vs {away} en {league_name}. {focus}

    ═══ SIMULACIÓN MONTE CARLO (10,000 iteraciones, datos reales ESPN) ═══
    • Victoria {home}: {sim_data['probabilities']['home_win']}% (Cuota: {sim_data['odds']['home']})
    • Empate: {sim_data['probabilities']['draw']}% (Cuota: {sim_data['odds']['draw']})
    • Victoria {away}: {sim_data['probabilities']['away_win']}% (Cuota: {sim_data['odds']['away']})
    • Marcador más probable: {sim_data['exact_score']['score']} ({sim_data['exact_score']['probability']}%)
    • xG: {sim_data['expected_values']['home_goals']} vs {sim_data['expected_values']['away_goals']}
    • BTTS (ambos marcan): {sim_data['probabilities']['btts']}%

    ═══ MERCADOS (probabilidades Monte Carlo) ═══
    ⚽ GOLES (esperados: {sim_data['markets']['goals']['expected']}):
    • Over 1.5: {sim_data['markets']['goals']['o15']}% | Under 1.5: {sim_data['markets']['goals']['u15']}%
    • Over 2.5: {sim_data['markets']['goals']['o25']}% | Under 2.5: {sim_data['markets']['goals']['u25']}%
    • Over 3.5: {sim_data['markets']['goals']['o35']}% | Under 3.5: {sim_data['markets']['goals']['u35']}%
    ⏱️ GOLES 1er TIEMPO (esperados: {sim_data['markets']['first_half']['expected']}):
    • Over 0.5 HT: {sim_data['markets']['first_half']['o05']}% | Under 0.5 HT: {sim_data['markets']['first_half']['u05']}%
    • Over 1.5 HT: {sim_data['markets']['first_half']['o15']}% | Under 1.5 HT: {sim_data['markets']['first_half']['u15']}%
    • Over 2.5 HT: {sim_data['markets']['first_half']['o25']}% | Under 2.5 HT: {sim_data['markets']['first_half']['u25']}%
    🚩 CÓRNERS (esperados: {sim_data['markets']['corners']['expected']}):
    • Over 7.5: {sim_data['markets']['corners']['o75']}% | Over 8.5: {sim_data['markets']['corners']['o85']}%
    • Over 9.5: {sim_data['markets']['corners']['o95']}% | Over 10.5: {sim_data['markets']['corners']['o105']}%
    🟨 TARJETAS (esperadas: {sim_data['markets']['cards']['expected']}):
    • Over 3.5: {sim_data['markets']['cards']['o35']}% | Over 4.5: {sim_data['markets']['cards']['o45']}% | Over 5.5: {sim_data['markets']['cards']['o55']}%

    ═══ DATOS REALES (últimos {hs.get('played', 0)} partidos, fuente ESPN) ═══
    🏠 {home} — Posición #{ht.get('rank', '?')} con {ht.get('points', '?')} pts:
    • Forma: {' '.join(hs.get('form', []))} | {hs.get('wins')}G-{hs.get('draws')}E-{hs.get('losses')}P
    • Goles: {hs.get('goals_for_avg')} a favor / {hs.get('goals_against_avg')} en contra por partido
    • Over 2.5: {hs.get('over25_pct')}% | BTTS: {hs.get('btts_pct')}%
    • Últimos resultados:
{recent_str(an['home'])}

    ✈️ {away} — Posición #{at.get('rank', '?')} con {at.get('points', '?')} pts:
    • Forma: {' '.join(as_.get('form', []))} | {as_.get('wins')}G-{as_.get('draws')}E-{as_.get('losses')}P
    • Goles: {as_.get('goals_for_avg')} a favor / {as_.get('goals_against_avg')} en contra por partido
    • Over 2.5: {as_.get('over25_pct')}% | BTTS: {as_.get('btts_pct')}%
    • Últimos resultados:
{recent_str(an['away'])}

    Escribe en ESPAÑOL con tono analítico profesional:
    ### 🏟️ Análisis de Forma y Contexto en la Tabla
    ### ⚽ Pronóstico de Goles y Marcador
    ### 📐 Córners y Tarjetas
    ### 🔮 Conclusión Final y Veredicto (apuesta con mejor balance riesgo/recompensa)
    """

        ai_response = predictor.get_prediction({
            "message": prompt,
            "data_context": sim_data
        })

        import combos as C
        combinadas = C.combinadas_de(sim_data, home, away, raw=sim_raw)

        return jsonify({
            "sim_data": sim_data,
            "ai_prediction": ai_response,
            "home_crest": data.get('home_logo', ''),
            "away_crest": data.get('away_logo', ''),
            "home_rank": ht.get('rank', ''),
            "away_rank": at.get('rank', ''),
            "home_form": home_engine['form'],
            "away_form": away_engine['form'],
            "home_recent": an['home'].get('matches', [])[:5],
            "away_recent": an['away'].get('matches', [])[:5],
            "combinadas": combinadas,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error en predicción: {e}"}), 500


@app.route('/api/espn/all_teams')
def espn_all_teams():
    """Todos los equipos de las ligas principales en una sola lista, cada
    uno con su liga de origen. Alimenta la opción "Todas las Ligas" del
    predictor: buscar cualquier equipo sin fijar antes una sola competición.
    """
    from concurrent.futures import ThreadPoolExecutor

    leagues = espn.get_leagues()

    def cargar(liga):
        try:
            data = espn.get_standings(liga['slug'])
        except Exception:
            return []
        vistos, out = set(), []
        for e in data.get('entries', []):
            tid = e.get('team_id')
            if not tid or tid in vistos:
                continue
            vistos.add(tid)
            out.append({
                'team_id': tid, 'team': e.get('team', '?'), 'logo': e.get('logo', ''),
                'league_slug': liga['slug'], 'league_name': liga['name'], 'flag': liga.get('flag', ''),
            })
        return out

    equipos = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        for lote in pool.map(cargar, leagues):
            equipos.extend(lote)
    equipos.sort(key=lambda t: t['team'])
    return jsonify(equipos)


@app.route('/api/predict_cross', methods=['POST'])
def api_predict_cross():
    """Predicción entre equipos de CUALQUIER liga ("Todas las Ligas"): cada
    equipo conserva su propia competición, tabla y calendario — ESPN no
    permite mezclarlas bajo un slug compartido, así que aquí no se fuerza
    uno. Misma Monte Carlo, mismas combinadas; solo cambia de dónde sale
    el análisis de cada lado."""
    try:
        data = request.json or {}
        home_slug = data.get('home_slug')
        away_slug = data.get('away_slug')
        home_id = data.get('home_id')
        away_id = data.get('away_id')
        home = data.get('home')
        away = data.get('away')
        analysis_type = data.get('analysis_type', 'completo')

        if not all([home_slug, away_slug, home_id, away_id, home, away]):
            return jsonify({"error": "Faltan parámetros (home_slug, away_slug, home_id, away_id, home, away)"}), 400

        an = espn.get_match_analysis_cross(home_slug, home_id, away_slug, away_id)

        home_engine = _to_engine_stats(an['home'])
        away_engine = _to_engine_stats(an['away'])
        n_sims = 2500 if os.getenv("RENDER") else 10000
        sim_data, sim_raw = StatsEngine.simulate_match(
            home_engine, away_engine, simulations=n_sims, return_raw=True
        )

        ht, at = an['home'].get('table') or {}, an['away'].get('table') or {}
        hs, as_ = an['home']['stats'], an['away']['stats']
        home_league, away_league = an['home']['league'], an['away']['league']

        focus = _ANALYSIS_FOCUS.get(analysis_type, 'Análisis completo.')

        prompt = f"""
    Eres FutboltAI, analista experto en pronósticos de fútbol. Genera un análisis DETALLADO
    para {home} ({home_league}) vs {away} ({away_league}). Es un cruce hipotético entre equipos
    de competiciones distintas: acláralo en el análisis en vez de tratarlos como si compartieran liga. {focus}

    ═══ SIMULACIÓN MONTE CARLO (10,000 iteraciones, datos reales ESPN) ═══
    • Victoria {home}: {sim_data['probabilities']['home_win']}% (Cuota: {sim_data['odds']['home']})
    • Empate: {sim_data['probabilities']['draw']}% (Cuota: {sim_data['odds']['draw']})
    • Victoria {away}: {sim_data['probabilities']['away_win']}% (Cuota: {sim_data['odds']['away']})
    • Marcador más probable: {sim_data['exact_score']['score']} ({sim_data['exact_score']['probability']}%)
    • xG: {sim_data['expected_values']['home_goals']} vs {sim_data['expected_values']['away_goals']}
    • BTTS (ambos marcan): {sim_data['probabilities']['btts']}%

    ═══ MERCADOS (probabilidades Monte Carlo) ═══
    ⚽ GOLES (esperados: {sim_data['markets']['goals']['expected']}):
    • Over 1.5: {sim_data['markets']['goals']['o15']}% | Under 1.5: {sim_data['markets']['goals']['u15']}%
    • Over 2.5: {sim_data['markets']['goals']['o25']}% | Under 2.5: {sim_data['markets']['goals']['u25']}%
    • Over 3.5: {sim_data['markets']['goals']['o35']}% | Under 3.5: {sim_data['markets']['goals']['u35']}%
    🚩 CÓRNERS (esperados: {sim_data['markets']['corners']['expected']}):
    • Over 8.5: {sim_data['markets']['corners']['o85']}% | Over 9.5: {sim_data['markets']['corners']['o95']}%
    🟨 TARJETAS (esperadas: {sim_data['markets']['cards']['expected']}):
    • Over 3.5: {sim_data['markets']['cards']['o35']}% | Over 4.5: {sim_data['markets']['cards']['o45']}%

    ═══ DATOS REALES (cada equipo en SU PROPIA liga) ═══
    🏠 {home} — {home_league} · Posición #{ht.get('rank', '?')} con {ht.get('points', '?')} pts:
    • Forma: {' '.join(hs.get('form', []))} | {hs.get('wins')}G-{hs.get('draws')}E-{hs.get('losses')}P
    • Goles: {hs.get('goals_for_avg')} a favor / {hs.get('goals_against_avg')} en contra por partido
    • Over 2.5: {hs.get('over25_pct')}% | BTTS: {hs.get('btts_pct')}%
    • Últimos resultados:
{_recent_str(an['home'])}

    ✈️ {away} — {away_league} · Posición #{at.get('rank', '?')} con {at.get('points', '?')} pts:
    • Forma: {' '.join(as_.get('form', []))} | {as_.get('wins')}G-{as_.get('draws')}E-{as_.get('losses')}P
    • Goles: {as_.get('goals_for_avg')} a favor / {as_.get('goals_against_avg')} en contra por partido
    • Over 2.5: {as_.get('over25_pct')}% | BTTS: {as_.get('btts_pct')}%
    • Últimos resultados:
{_recent_str(an['away'])}

    Escribe en ESPAÑOL con tono analítico profesional:
    ### 🏟️ Análisis de Forma y Contexto (dos ligas distintas)
    ### ⚽ Pronóstico de Goles y Marcador
    ### 📐 Córners y Tarjetas
    ### 🔮 Conclusión Final y Veredicto (apuesta con mejor balance riesgo/recompensa)
    """

        ai_response = predictor.get_prediction({
            "message": prompt,
            "data_context": sim_data
        })

        import combos as C
        combinadas = C.combinadas_de(sim_data, home, away, raw=sim_raw)

        return jsonify({
            "sim_data": sim_data,
            "ai_prediction": ai_response,
            "home_crest": data.get('home_logo', ''),
            "away_crest": data.get('away_logo', ''),
            "home_rank": ht.get('rank', ''),
            "away_rank": at.get('rank', ''),
            "home_form": home_engine['form'],
            "away_form": away_engine['form'],
            "home_recent": an['home'].get('matches', [])[:5],
            "away_recent": an['away'].get('matches', [])[:5],
            "combinadas": combinadas,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error en predicción: {e}"}), 500


@app.route('/worldcup')
def worldcup():
    return render_template('worldcup.html')

@app.route('/api/worldcup')
def get_worldcup():
    data = fetcher.get_worldcup_data()
    return jsonify(data)

@app.route('/api/sim_match', methods=['POST'])
def api_sim_match():
    data = request.json
    home = data.get('home')
    away = data.get('away')
    is_knockout = data.get('knockout', False)
    
    if not home or not away:
        return jsonify({"error": "Faltan equipos"}), 400
        
    home_stats = fetcher.get_team_stats(home)
    away_stats = fetcher.get_team_stats(away)
    
    home_goals_lambda = home_stats['attack']['goals_per_game']
    away_goals_lambda = away_stats['attack']['goals_per_game']
    home_defense_factor = home_stats['defense']['goals_conceded']
    away_defense_factor = away_stats['defense']['goals_conceded']
    
    home_lambda = max(0.2, (home_goals_lambda + away_defense_factor) / 2.0)
    away_lambda = max(0.2, (away_goals_lambda + home_defense_factor) / 2.0)
    
    import numpy as np
    import random
    
    home_goals = int(np.random.poisson(home_lambda))
    away_goals = int(np.random.poisson(away_lambda))
    
    detail = "FT"
    winner = home if home_goals > away_goals else (away if away_goals > home_goals else None)
    
    if is_knockout and home_goals == away_goals:
        home_et = int(np.random.poisson(home_lambda * 0.33))
        away_et = int(np.random.poisson(away_lambda * 0.33))
        home_goals += home_et
        away_goals += away_et
        detail = "AET"
        winner = home if home_goals > away_goals else (away if away_goals > home_goals else None)
        
        if home_goals == away_goals:
            home_rating = home_stats.get('sofa_rating', 7.0)
            away_rating = away_stats.get('sofa_rating', 7.0)
            p_home = home_rating / (home_rating + away_rating)
            
            if random.random() < p_home:
                winner = home
                home_pen = 5
                away_pen = 4
            else:
                winner = away
                home_pen = 4
                away_pen = 5
            detail = f"PEN ({home_pen}-{away_pen})"
            
    return jsonify({
        "home": home,
        "away": away,
        "home_score": home_goals,
        "away_score": away_goals,
        "detail": detail,
        "winner": winner
    })

@app.route('/team/<name>')
def team_profile(name):
    stats_data = fetcher.get_team_stats(name)
    return render_template('team_stats.html', stats=stats_data)

@app.route('/api/data')
def get_stats_data():
    league = request.args.get('league', 'PD') # Por defecto La Liga
    standings = fetcher.get_standings(league)
    fixtures = fetcher.get_fixtures(league)
    return jsonify({
        "standings": standings,
        "fixtures": fixtures
    })

@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Si el mensaje menciona un partido o equipo, intentamos obtener datos
    # Para este chat, dejaremos que la IA maneje la conversación general,
    # pero le daremos contexto si detectamos intención de pronóstico.
    
    try:
        # Intentar obtener contexto extendido (basado en soccerdata/ClubElo)
        # Esto enriquece la respuesta de la IA
        match_context = fetcher.get_match_data_for_ai("Equipo Local", "Equipo Visitante")
        
        # Usar el método robusto del predictor que incluye reintentos y fallback
        # Pasamos el mensaje del usuario y el contexto de datos enriquecido
        prediction = predictor.get_prediction({
            "message": user_message,
            "data_context": match_context
        })
        return jsonify({"response": prediction})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

# ── QUINIELA REAL ─────────────────────────────────────────
# Partidos reales de ESPN + Monte Carlo alimentada con datos reales.
# Nada aquí usa random: mismas entradas, mismo pronóstico.

@app.route('/preview')
def preview():
    return render_template('preview.html')


@app.route('/combinadas')
def combinadas_page():
    return render_template('combinadas.html')


@app.route('/api/quiniela')
def api_quiniela():
    """1-X-2 real de los próximos partidos. Registra cada pronóstico."""
    from datetime import datetime, timedelta
    import real_stats, prediction_log

    dias = int(request.args.get('dias', 3))
    limite = int(request.args.get('limite', 8))

    partidos = []
    for i in range(dias):
        fecha = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
        try:
            bloques = espn.get_matches_by_date(fecha)
        except Exception:
            continue
        for b in bloques or []:
            if b.get('extra'):
                continue  # solo ligas principales
            for m in b.get('matches', []):
                if m.get('state') != 'pre':
                    continue
                m['_slug'] = b['slug']
                m['_league'] = b['league']
                m['_flag'] = b.get('flag', '')
                partidos.append(m)

    filas = real_stats.quiniela_de(espn, partidos)[:limite]

    # Se registra el pronóstico ANTES del partido. INSERT OR IGNORE:
    # una vez emitido, no se reescribe nunca.
    for f in filas:
        prediction_log.record(
            match_id=f['match_id'], league_slug=f['league_slug'],
            league_name=f['league_name'], home=f['home']['name'],
            away=f['away']['name'], kickoff=f['kickoff'],
            p_home=f['probs']['1'], p_draw=f['probs']['X'], p_away=f['probs']['2'],
            state='pre'
        )

    return jsonify({
        'partidos': filas,
        'mercados': real_stats.mercados_fiables(),
    })


@app.route('/api/combos')
def api_combos():
    """Apuestas combinadas con cuota justa del modelo, sobre partidos reales.

    En Render (plan free) se calcula en serie, con pocas sims y sin arrays
    crudos, para no tumbar el worker (HTTP 500/502 HTML).
    """
    import gc
    from datetime import datetime, timedelta
    import real_stats, combos as C
    from stats_engine import StatsEngine

    on_render = bool(os.getenv("RENDER"))
    try:
        dias = max(1, min(int(request.args.get("dias", 1 if on_render else 3)), 7))
        limite = max(1, min(int(request.args.get("limite", 5 if on_render else 8)), 8 if on_render else 16))
    except (TypeError, ValueError):
        dias, limite = 1, 5
    # En plan free limitar el rango aunque el front pida 7 días.
    if on_render:
        dias = min(dias, 2)
        limite = min(limite, 5)

    n_sims = 600 if on_render else 8000
    usar_raw = not on_render

    try:
        partidos = []
        vistos = set()
        for i in range(dias):
            fecha = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                bloques = espn.get_matches_by_date(fecha)
            except Exception:
                continue
            for b in bloques or []:
                for m in b.get("matches", []):
                    if m.get("state") != "pre":
                        continue
                    mid = str(m.get("id") or "")
                    if mid and mid in vistos:
                        continue
                    if mid:
                        vistos.add(mid)
                    home, away = m.get("home") or {}, m.get("away") or {}
                    if not home.get("id") or not away.get("id"):
                        continue
                    partidos.append({
                        "home": home,
                        "away": away,
                        "date": m.get("date"),
                        "_slug": b.get("slug"),
                        "_league": b.get("league"),
                        "_flag": b.get("flag", ""),
                        "_extra": bool(b.get("extra")),
                        "_fecha": fecha,
                    })

        partidos.sort(key=lambda m: (
            1 if m.get("_extra") else 0,
            m.get("date") or m.get("_fecha") or "",
        ))

        tarjetas = []
        for m in partidos:
            if len(tarjetas) >= limite:
                break
            slug = m.get("_slug")
            if not slug:
                continue
            try:
                local = real_stats.team_strength(
                    espn, slug, m["home"].get("id"), m["home"].get("name", "?")
                )
                visit = real_stats.team_strength(
                    espn, slug, m["away"].get("id"), m["away"].get("name", "?")
                )
            except Exception:
                continue
            if not local or not visit:
                continue
            try:
                if usar_raw:
                    sim, sim_raw = StatsEngine.simulate_match(
                        local, visit, simulations=n_sims, return_raw=True
                    )
                    combis = C.combinadas_de(
                        sim, local["name"], visit["name"], raw=sim_raw
                    )
                    del sim_raw
                else:
                    sim = StatsEngine.simulate_match(
                        local, visit, simulations=n_sims, return_raw=False
                    )
                    combis = C.combinadas_de(sim, local["name"], visit["name"])
            except Exception:
                combis = []
                continue
            finally:
                gc.collect()

            if not combis:
                continue

            combis_safe = [{
                "selecciones": cb.get("selecciones") or [],
                "probabilidad": float(cb.get("probabilidad") or 0),
                "cuota": float(cb.get("cuota") or 0),
            } for cb in combis]

            tarjetas.append({
                "home": {
                    "name": local["name"],
                    "logo": m["home"].get("logo"),
                    "id": m["home"].get("id"),
                },
                "away": {
                    "name": visit["name"],
                    "logo": m["away"].get("logo"),
                    "id": m["away"].get("id"),
                },
                "liga": m["_league"],
                "league_slug": slug,
                "kickoff": m.get("date"),
                "fecha": m.get("_fecha"),
                "flag": m.get("_flag", ""),
                "tipo": "real",
                "combinadas": combis_safe,
            })

        return jsonify({
            "tarjetas": tarjetas,
            "dias": dias,
            "total": len(tarjetas),
            "modo": "ligero" if on_render else "completo",
            "nota": "Cuota justa del modelo (100 / probabilidad), sin margen de casa. "
                    "Sirve para detectar valor: si tu casa paga mas, hay valor. "
                    "No son garantias. Juega con responsabilidad · +18.",
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "tarjetas": [],
            "total": 0,
            "error": f"Error al calcular combinadas: {e}",
        }), 500


@app.route('/api/combo_selecciones')
def api_combo_selecciones():
    """Combinada de un cruce de selecciones (Mundial). Datos de perfil reales.

    Cruce hipotético de eliminatoria: 'clasifica' = gana en 90' o penaltis.
    """
    import combos as C
    from stats_engine import StatsEngine

    local_n = request.args.get('local', 'Inglaterra')
    visit_n = request.args.get('visitante', 'Argentina')

    l = fetcher.get_team_stats(local_n)
    v = fetcher.get_team_stats(visit_n)
    if not l or not v:
        return jsonify({'error': 'Selección sin perfil'}), 404

    sim, sim_raw = StatsEngine.simulate_match(l, v, simulations=10000, return_raw=True)
    combis = C.combinadas_de(sim, local_n, visit_n, raw=sim_raw, es_eliminatoria=True)

    return jsonify({
        'tarjeta': {
            'home': {'name': local_n}, 'away': {'name': visit_n},
            'liga': 'Mundial 2026 · cruce hipotético', 'kickoff': None,
            'tipo': 'hipotetico', 'combinadas': combis,
        },
        'nota': 'Cruce hipotético con datos de perfil reales de cada selección. '
                'Cuota justa del modelo, sin margen de casa. +18.',
    })


@app.route('/api/accuracy')
def api_accuracy():
    """Precisión REAL. Combina en vivo (forward) + backtest histórico.

    - 'live': pronósticos emitidos antes del partido y resueltos después.
      Es la evidencia fuerte, pero tarda en acumular muestra.
    - 'backtest': el modelo corrido sobre partidos pasados con datos
      punto-en-el-tiempo. Evidencia más débil, disponible ya.
    """
    import prediction_log, backtest
    try:
        prediction_log.resolve_pending(espn)
    except Exception:
        pass
    datos = prediction_log.stats()
    bt = backtest.leer_cache()
    if bt:
        datos['backtest'] = {
            'precision': bt.get('precision'),
            'total': bt.get('total'),
            'por_liga': bt.get('por_liga', []),
            'generado': bt.get('generado'),
        }
    return jsonify(datos)


@app.route('/api/match_stats')
def get_match_stats():
    date = request.args.get('date', '2026-02-18')
    query = request.args.get('query')
    stats = fetcher.get_apisports_stats(date=date, match_query=query)
    return jsonify(stats)

if __name__ == '__main__':
    is_frozen = getattr(sys, 'frozen', False)
    debug_mode = not is_frozen
    # El ejecutable empaquetado no recibe PORT del entorno, así que cae en
    # el 5001 de siempre; en desarrollo, el runner de preview asigna el
    # puerto libre vía esta variable en vez de un valor fijo.
    port = int(os.environ.get('PORT', 5001))

    if is_frozen:
        import webbrowser
        import threading
        # Abrir el navegador automáticamente a los 1.5 segundos
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    # 0.0.0.0 permite acceso externo (Render / Docker); en local sigue OK.
    app.run(host="0.0.0.0", debug=debug_mode, port=port)
