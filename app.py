from flask import Flask, render_template, request, jsonify
from data_fetcher import FootballDataFetcher
from ai_predictor import AIPredictor
from stats_engine import StatsEngine
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
fetcher = FootballDataFetcher()
predictor = AIPredictor()

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
        {"code": "PD", "name": "🇪🇸 LaLiga (España)"},
        {"code": "PL", "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)"},
        {"code": "SA", "name": "🇮🇹 Serie A (Italia)"},
        {"code": "BL1", "name": "🇩🇪 Bundesliga (Alemania)"},
        {"code": "FL1", "name": "🇫🇷 Ligue 1 (Francia)"},
        {"code": "ARG", "name": "🇦🇷 Liga Profesional (Argentina)"},
        {"code": "BRA", "name": "🇧🇷 Brasileirão (Brasil)"},
        {"code": "COL", "name": "🇨🇴 Liga BetPlay (Colombia)"},
        {"code": "MX", "name": "🇲🇽 Liga MX (México)"},
        {"code": "MLS", "name": "🇺🇸 Major League Soccer (EE.UU.)"},
        {"code": "SPL", "name": "🇸🇦 Saudi Pro League (Arabia)"},
        {"code": "PPL", "name": "🇵🇹 Primeira Liga (Portugal)"},
        {"code": "DED", "name": "🇳🇱 Eredivisie (Países Bajos)"},
        {"code": "TSL", "name": "🇹🇷 Süper Lig (Turquía)"},
        {"code": "BEL", "name": "🇧🇪 Jupiler Pro League (Bélgica)"},
        {"code": "SPD", "name": "🇪🇸 Segunda División (España)"},
        {"code": "SB", "name": "🇮🇹 Serie B (Italia)"},
        {"code": "SPR", "name": "🇷🇺 Russian Premier League"},
        {"code": "SPO", "name": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership"},
        {"code": "AUS", "name": "🇦🇹 Austrian Bundesliga"},
        {"code": "ECU", "name": "🇪🇨 LigaPro (Ecuador)"},
        {"code": "CHI", "name": "🇨🇱 Primera División (Chile)"},
        {"code": "URU", "name": "🇺🇾 Primera División (Uruguay)"},
        {"code": "PAR", "name": "🇵🇾 Primera División (Paraguay)"},
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
    Eres FutboltAI, un analista experto del Mundial 2026. Genera un análisis DETALLADO y PRECISO para el partido {home} vs {away} en {league}.
    
    ═══════════════════════════════════════════════════════
    📊 SIMULACIÓN MONTE CARLO (10,000 iteraciones):
    ═══════════════════════════════════════════════════════
    • Victoria {home}: {sim_data['probabilities']['home_win']}%
    • Empate: {sim_data['probabilities']['draw']}%  
    • Victoria {away}: {sim_data['probabilities']['away_win']}%
    • Marcador más probable: {sim_data['exact_score']['score']} (Prob: {sim_data['exact_score']['probability']}%)
    • xG Local: {sim_data['expected_values']['home_goals']} | xG Visitante: {sim_data['expected_values']['away_goals']}
    • Over 2.5 Goles: {sim_data['probabilities']['over_2_5_goals']}%
    • Ambos Marcan (BTTS): {sim_data['probabilities']['btts']}%
    • Córners esperados: {sim_data['expected_values']['total_corners']}
    • Tarjetas amarillas: {sim_data['expected_values']['total_cards']}
    
    ═══════════════════════════════════════════════════════
    🏆 PERFIL REAL DE EQUIPOS (FIFA WC 2026):
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
    (xG, Over/Under, BTTS, marcador más probable y por qué)
    
    ### 📐 Córners y Tarjetas
    (Análisis de la simulación Monte Carlo)
    
    ### 🔮 Conclusión Final
    (Veredicto claro basado en ranking FIFA, forma real y simulación. Menciona al jugador decisivo)
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

@app.route('/api/match_stats')
def get_match_stats():
    date = request.args.get('date', '2026-02-18')
    query = request.args.get('query')
    stats = fetcher.get_apisports_stats(date=date, match_query=query)
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
