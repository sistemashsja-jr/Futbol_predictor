import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class StatsEngine:
    _model_goals = None
    _model_corners = None
    _model_shots = None
    _model_cards = None
    _model_goalkicks = None
    _model_throwins = None
    _model_saves = None
    _model_total_shots = None

    @classmethod
    def _train_models(cls):
        """
        Entrena modelos de Random Forest usando un dataset simulado con correlación estocástica real.
        """
        if cls._model_goals is not None:
            return

        np.random.seed(42)
        partidos = 2000
        
        # Simular variables explicativas
        home_rating = np.random.uniform(6.2, 7.8, partidos)
        away_rating = np.random.uniform(6.2, 7.8, partidos)
        home_form = np.random.uniform(0.1, 0.9, partidos)
        away_form = np.random.uniform(0.1, 0.9, partidos)
        
        home_goals_base = np.random.uniform(1.0, 2.5, partidos)
        away_goals_base = np.random.uniform(1.0, 2.5, partidos)
        home_corners_base = np.random.uniform(3.5, 7.0, partidos)
        away_corners_base = np.random.uniform(3.5, 7.0, partidos)
        home_shots_base = np.random.uniform(3.0, 7.0, partidos)
        away_shots_base = np.random.uniform(3.0, 7.0, partidos)
        home_cards_base = np.random.uniform(1.0, 3.5, partidos)
        away_cards_base = np.random.uniform(1.0, 3.5, partidos)
        home_goalkicks_base = np.random.uniform(5.0, 10.0, partidos)
        away_goalkicks_base = np.random.uniform(5.0, 10.0, partidos)
        home_throwins_base = np.random.uniform(17.0, 25.0, partidos)
        away_throwins_base = np.random.uniform(17.0, 25.0, partidos)
        home_saves_base = np.random.uniform(2.0, 4.5, partidos)
        away_saves_base = np.random.uniform(2.0, 4.5, partidos)
        home_total_shots_base = np.random.uniform(8.0, 18.0, partidos)
        away_total_shots_base = np.random.uniform(8.0, 18.0, partidos)
        
        # Relaciones para goles (correlacionado)
        rating_diff = home_rating - away_rating
        q_home = 1.0 + rating_diff * 0.20
        q_away = 1.0 - rating_diff * 0.20
        f_home = 0.85 + 0.3 * home_form
        f_away = 0.85 + 0.3 * away_form
        
        # Lambdas ajustadas
        home_lambda = np.clip(home_goals_base * q_home * f_home * 1.08, 0.2, 4.0)
        away_lambda = np.clip(away_goals_base * q_away * f_away * 0.92, 0.2, 4.0)
        
        # Goles reales simulados
        goals_h = np.random.poisson(home_lambda)
        goals_a = np.random.poisson(away_lambda)
        total_goals = goals_h + goals_a
        
        # Córners reales simulados
        corners_h = np.random.poisson(home_corners_base * (1.0 + rating_diff * 0.05) * 1.05)
        corners_a = np.random.poisson(away_corners_base * (1.0 - rating_diff * 0.05) * 0.95)
        total_corners = corners_h + corners_a
        
        # Tiros al arco reales simulados
        home_lambda_shots = np.clip(home_shots_base * q_home * (0.9 + 0.2 * home_form) * 1.05, 1.0, 15.0)
        away_lambda_shots = np.clip(away_shots_base * q_away * (0.9 + 0.2 * away_form) * 0.95, 1.0, 15.0)
        shots_h = np.random.poisson(home_lambda_shots)
        shots_a = np.random.poisson(away_lambda_shots)
        total_shots = shots_h + shots_a
        
        # Tarjetas reales simuladas
        home_lambda_cards = np.clip(home_cards_base * (1.0 + abs(rating_diff) * -0.05) * (1.1 - 0.2 * home_form), 0.5, 10.0)
        away_lambda_cards = np.clip(away_cards_base * (1.0 + abs(rating_diff) * -0.05) * (1.1 - 0.2 * away_form), 0.5, 10.0)
        cards_h = np.random.poisson(home_lambda_cards)
        cards_a = np.random.poisson(away_lambda_cards)
        total_cards = cards_h + cards_a

        # Saques de puerta simulados (weaker team has more goalkicks)
        home_lambda_gk = np.clip(home_goalkicks_base * q_away * (1.05 - 0.1 * home_form), 3.0, 18.0)
        away_lambda_gk = np.clip(away_goalkicks_base * q_home * (1.05 - 0.1 * away_form), 3.0, 18.0)
        gk_h = np.random.poisson(home_lambda_gk)
        gk_a = np.random.poisson(away_lambda_gk)
        total_goalkicks = gk_h + gk_a

        # Saques de banda simulados
        home_lambda_ti = np.clip(home_throwins_base * (1.1 - 0.2 * home_form), 10.0, 35.0)
        away_lambda_ti = np.clip(away_throwins_base * (1.1 - 0.2 * away_form), 10.0, 35.0)
        ti_h = np.random.poisson(home_lambda_ti)
        ti_a = np.random.poisson(away_lambda_ti)
        total_throwins = ti_h + ti_a

        # Paradas de portero simuladas
        home_lambda_saves = np.clip(home_saves_base * (1.05 - 0.1 * home_form), 1.0, 10.0)
        away_lambda_saves = np.clip(away_saves_base * (1.05 - 0.1 * away_form), 1.0, 10.0)
        saves_h = np.random.poisson(home_lambda_saves)
        saves_a = np.random.poisson(away_lambda_saves)
        total_saves = saves_h + saves_a

        # Remates totales simulados
        home_lambda_total_shots = np.clip(home_total_shots_base * q_home * (0.9 + 0.2 * home_form) * 1.05, 5.0, 30.0)
        away_lambda_total_shots = np.clip(away_total_shots_base * q_away * (0.9 + 0.2 * away_form) * 0.95, 5.0, 30.0)
        tot_shots_h = np.random.poisson(home_lambda_total_shots)
        tot_shots_a = np.random.poisson(away_lambda_total_shots)
        total_tot_shots = tot_shots_h + tot_shots_a
        
        X = pd.DataFrame({
            "home_rating": home_rating,
            "away_rating": away_rating,
            "home_form": home_form,
            "away_form": away_form,
            "home_goals_base": home_goals_base,
            "away_goals_base": away_goals_base,
            "home_corners_base": home_corners_base,
            "away_corners_base": away_corners_base,
            "home_shots_base": home_shots_base,
            "away_shots_base": away_shots_base,
            "home_cards_base": home_cards_base,
            "away_cards_base": away_cards_base,
            "home_goalkicks_base": home_goalkicks_base,
            "away_goalkicks_base": away_goalkicks_base,
            "home_throwins_base": home_throwins_base,
            "away_throwins_base": away_throwins_base,
            "home_saves_base": home_saves_base,
            "away_saves_base": away_saves_base,
            "home_total_shots_base": home_total_shots_base,
            "away_total_shots_base": away_total_shots_base
        })
        
        cls._model_goals = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_corners = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_shots = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_cards = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_goalkicks = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_throwins = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_saves = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_total_shots = RandomForestRegressor(n_estimators=100, random_state=42)
        
        cls._model_goals.fit(X, total_goals)
        cls._model_corners.fit(X, total_corners)
        cls._model_shots.fit(X, total_shots)
        cls._model_cards.fit(X, total_cards)
        cls._model_goalkicks.fit(X, total_goalkicks)
        cls._model_throwins.fit(X, total_throwins)
        cls._model_saves.fit(X, total_saves)
        cls._model_total_shots.fit(X, total_tot_shots)

    @classmethod
    def predict_advanced(cls, home_rating, away_rating, home_form, away_form, home_goals_base, away_goals_base, home_corners_base, away_corners_base, home_shots_base, away_shots_base, home_cards_base, away_cards_base, home_goalkicks_base, away_goalkicks_base, home_throwins_base, away_throwins_base, home_saves_base, away_saves_base, home_total_shots_base, away_total_shots_base):
        """
        Usa Machine Learning (Random Forest) con variables avanzadas para predecir goles, córners, tiros al arco, tarjetas, saques de puerta, saques de banda, paradas y remates.
        """
        cls._train_models()
        
        input_data = pd.DataFrame([{
            "home_rating": home_rating,
            "away_rating": away_rating,
            "home_form": home_form,
            "away_form": away_form,
            "home_goals_base": home_goals_base,
            "away_goals_base": away_goals_base,
            "home_corners_base": home_corners_base,
            "away_corners_base": away_corners_base,
            "home_shots_base": home_shots_base,
            "away_shots_base": away_shots_base,
            "home_cards_base": home_cards_base,
            "away_cards_base": away_cards_base,
            "home_goalkicks_base": home_goalkicks_base,
            "away_goalkicks_base": away_goalkicks_base,
            "home_throwins_base": home_throwins_base,
            "away_throwins_base": away_throwins_base,
            "home_saves_base": home_saves_base,
            "away_saves_base": away_saves_base,
            "home_total_shots_base": home_total_shots_base,
            "away_total_shots_base": away_total_shots_base
        }])
        
        pred_goals = cls._model_goals.predict(input_data)[0]
        pred_corners = cls._model_corners.predict(input_data)[0]
        pred_shots = cls._model_shots.predict(input_data)[0]
        pred_cards = cls._model_cards.predict(input_data)[0]
        pred_goalkicks = cls._model_goalkicks.predict(input_data)[0]
        pred_throwins = cls._model_throwins.predict(input_data)[0]
        pred_saves = cls._model_saves.predict(input_data)[0]
        pred_tot_shots = cls._model_total_shots.predict(input_data)[0]
        
        return {
            "ml_goals": round(float(pred_goals), 2),
            "ml_corners": round(float(pred_corners), 2),
            "ml_shots": round(float(pred_shots), 2),
            "ml_cards": round(float(pred_cards), 2),
            "ml_goalkicks": round(float(pred_goalkicks), 2),
            "ml_throwins": round(float(pred_throwins), 2),
            "ml_saves": round(float(pred_saves), 2),
            "ml_total_shots": round(float(pred_tot_shots), 2)
        }

    @staticmethod
    def simulate_corners(lambda_home, lambda_away, simulations=10000):
        """
        Realiza una simulación Monte Carlo para predecir el total de córners.
        """
        # Simulación de córners basada en distribución de Poisson
        corners_home = np.random.poisson(lambda_home, simulations)
        corners_away = np.random.poisson(lambda_away, simulations)
        corners_total = corners_home + corners_away

        df = pd.DataFrame({
            "Home": corners_home,
            "Away": corners_away,
            "Total": corners_total
        })

        # Cálculo de probabilidades
        media_total = df["Total"].mean()
        prob_over_85 = (df["Total"] > 8).mean() * 100
        prob_over_95 = (df["Total"] > 9).mean() * 100
        prob_over_105 = (df["Total"] > 10).mean() * 100

        return {
            "media_simulada": round(media_total, 2),
            "probabilidades": {
                "over_8_5": round(prob_over_85, 2),
                "over_9_5": round(prob_over_95, 2),
                "over_10_5": round(prob_over_105, 2)
            },
            "detalles": {
                "lambda_home": lambda_home,
                "lambda_away": lambda_away,
                "simulaciones": simulations
            }
        }

    @classmethod
    def simulate_match(cls, home_stats, away_stats, simulations=10000, return_raw=False):
        """
        Simulación Monte Carlo completa para un partido de fútbol, calculando goles,
        córners, tarjetas y disparos al arco usando distribuciones de Poisson y modificadores.
        """
        # Obtener ratings y promedios de forma
        home_rating = home_stats.get('sofa_rating', 7.0)
        away_rating = away_stats.get('sofa_rating', 7.0)
        
        home_form_arr = home_stats.get('form', [])
        away_form_arr = away_stats.get('form', [])
        
        home_form_score = sum(1.0 if r=="W" else 0.5 if r=="D" else 0.0 for r in home_form_arr) / len(home_form_arr) if home_form_arr else 0.5
        away_form_score = sum(1.0 if r=="W" else 0.5 if r=="D" else 0.0 for r in away_form_arr) / len(away_form_arr) if away_form_arr else 0.5
        
        # 1. Modificadores de rendimiento
        # A. Calidad SofaScore (Quality Modifier)
        rating_diff = home_rating - away_rating
        quality_modifier_home = max(0.4, min(2.5, 1.0 + rating_diff * 0.25))
        quality_modifier_away = max(0.4, min(2.5, 1.0 - rating_diff * 0.25))
        
        quality_def_home = max(0.4, min(2.5, 1.0 - rating_diff * 0.20))
        quality_def_away = max(0.4, min(2.5, 1.0 + rating_diff * 0.20))
        
        # B. Momento de Forma (Form Modifier)
        form_modifier_home = 0.85 + 0.3 * home_form_score
        form_modifier_away = 0.85 + 0.3 * away_form_score
        
        form_def_home = 1.15 - 0.3 * home_form_score
        form_def_away = 1.15 - 0.3 * away_form_score
        
        # C. Factor Local (Home Advantage Modifier)
        home_adv_attack = 1.10
        home_adv_defense = 0.90
        
        # Calcular modificador de rendimiento agregado (%)
        home_mod_total = round((home_adv_attack * quality_modifier_home * form_modifier_home - 1.0) * 100, 1)
        away_mod_total = round((quality_modifier_away * form_modifier_away - 1.0) * 100, 1)

        # 2. Goles (ajustado por factor ataque/defensa y modificadores)
        home_goals_base = home_stats['attack']['goals_per_game']
        away_goals_base = away_stats['attack']['goals_per_game']
        home_defense_factor = home_stats['defense']['goals_conceded']
        away_defense_factor = away_stats['defense']['goals_conceded']
        
        home_lambda_goals = max(0.15, (home_goals_base * quality_modifier_home * form_modifier_home * home_adv_attack + away_defense_factor * quality_def_away * form_def_away) / 2.0)
        away_lambda_goals = max(0.15, (away_goals_base * quality_modifier_away * form_modifier_away + home_defense_factor * quality_def_home * form_def_home * home_adv_defense) / 2.0)
        
        # 3. Córners
        home_corners_base = home_stats['attack']['corners']
        away_corners_base = away_stats['attack']['corners']
        
        home_lambda_corners = max(1.5, home_corners_base * (1.0 + rating_diff * 0.08) * (0.95 + 0.1 * home_form_score) * 1.05)
        away_lambda_corners = max(1.5, away_corners_base * (1.0 - rating_diff * 0.08) * (0.95 + 0.1 * away_form_score) * 0.95)
        
        # 4. Tarjetas amarillas
        home_cards_base = home_stats['summary'].get('yellow_cards_per_game', 2.0)
        away_cards_base = away_stats['summary'].get('yellow_cards_per_game', 2.2)
        
        home_lambda_cards = max(0.5, home_cards_base * (1.0 + abs(rating_diff) * -0.05) * (1.1 - 0.2 * home_form_score))
        away_lambda_cards = max(0.5, away_cards_base * (1.0 + abs(rating_diff) * -0.05) * (1.1 - 0.2 * away_form_score))
        
        # 5. Disparos al arco
        home_shots_base = home_stats['attack'].get('shots_on_target', 4.5)
        away_shots_base = away_stats['attack'].get('shots_on_target', 4.0)
        
        home_lambda_shots = max(1.0, home_shots_base * quality_modifier_home * (0.9 + 0.2 * home_form_score) * 1.05)
        away_lambda_shots = max(1.0, away_shots_base * quality_modifier_away * (0.9 + 0.2 * away_form_score) * 0.95)
        
        # 6. Saques de puerta
        home_goalkicks_base = home_stats['summary'].get('avg_goal_kicks', 7.5)
        away_goalkicks_base = away_stats['summary'].get('avg_goal_kicks', 7.5)
        home_lambda_goalkicks = max(3.0, home_goalkicks_base * quality_modifier_away * (1.05 - 0.1 * home_form_score))
        away_lambda_goalkicks = max(3.0, away_goalkicks_base * quality_modifier_home * (1.05 - 0.1 * away_form_score))

        # 7. Saques de banda
        home_throwins_base = home_stats['summary'].get('avg_throw_ins', 21.0)
        away_throwins_base = away_stats['summary'].get('avg_throw_ins', 21.0)
        home_lambda_throwins = max(10.0, home_throwins_base * (1.1 - 0.2 * home_form_score))
        away_lambda_throwins = max(10.0, away_throwins_base * (1.1 - 0.2 * away_form_score))
        
        # 8. Paradas de portero
        home_saves_base = home_stats['summary'].get('avg_saves', 3.0)
        away_saves_base = away_stats['summary'].get('avg_saves', 3.0)
        home_lambda_saves = max(1.0, home_saves_base * (1.05 - 0.1 * home_form_score))
        away_lambda_saves = max(1.0, away_saves_base * (1.05 - 0.1 * away_form_score))

        # 9. Remates totales
        home_total_shots_base = home_stats['attack'].get('total_shots', 10.0)
        away_total_shots_base = away_stats['attack'].get('total_shots', 10.0)
        home_lambda_total_shots = max(2.0, home_total_shots_base * quality_modifier_home * (0.9 + 0.2 * home_form_score) * 1.05)
        away_lambda_total_shots = max(2.0, away_total_shots_base * quality_modifier_away * (0.9 + 0.2 * away_form_score) * 0.95)
        
        # Generar simulaciones estocásticas
        np.random.seed(42)
        home_goals_sim = np.random.poisson(home_lambda_goals, simulations)
        away_goals_sim = np.random.poisson(away_lambda_goals, simulations)
        total_goals_sim = home_goals_sim + away_goals_sim
        
        home_corners_sim = np.random.poisson(home_lambda_corners, simulations)
        away_corners_sim = np.random.poisson(away_lambda_corners, simulations)
        total_corners_sim = home_corners_sim + away_corners_sim
        
        home_cards_sim = np.random.poisson(home_lambda_cards, simulations)
        away_cards_sim = np.random.poisson(away_lambda_cards, simulations)
        total_cards_sim = home_cards_sim + away_cards_sim
        
        home_shots_sim = np.random.poisson(home_lambda_shots, simulations)
        away_shots_sim = np.random.poisson(away_lambda_shots, simulations)
        total_shots_sim = home_shots_sim + away_shots_sim

        home_goalkicks_sim = np.random.poisson(home_lambda_goalkicks, simulations)
        away_goalkicks_sim = np.random.poisson(away_lambda_goalkicks, simulations)
        total_goalkicks_sim = home_goalkicks_sim + away_goalkicks_sim

        home_throwins_sim = np.random.poisson(home_lambda_throwins, simulations)
        away_throwins_sim = np.random.poisson(away_lambda_throwins, simulations)
        total_throwins_sim = home_throwins_sim + away_throwins_sim

        home_saves_sim = np.random.poisson(home_lambda_saves, simulations)
        away_saves_sim = np.random.poisson(away_lambda_saves, simulations)
        total_saves_sim = home_saves_sim + away_saves_sim

        home_total_shots_sim = np.random.poisson(home_lambda_total_shots, simulations)
        away_total_shots_sim = np.random.poisson(away_lambda_total_shots, simulations)
        total_total_shots_sim = home_total_shots_sim + away_total_shots_sim
        
        # Calcular probabilidades de resultado
        home_wins = int(np.sum(home_goals_sim > away_goals_sim))
        draws = int(np.sum(home_goals_sim == away_goals_sim))
        away_wins = int(np.sum(home_goals_sim < away_goals_sim))
        
        # Proteger de división por cero
        home_win_pct = max(0.1, round((home_wins / simulations) * 100, 1))
        draw_pct = max(0.1, round((draws / simulations) * 100, 1))
        away_win_pct = max(0.1, round((away_wins / simulations) * 100, 1))
        
        # Over/Under y BTTS
        prob_over_2_5_goals = max(0.1, round(float((total_goals_sim > 2).mean() * 100), 1))
        prob_btts = max(0.1, round(float(((home_goals_sim > 0) & (away_goals_sim > 0)).mean() * 100), 1))
        prob_over_8_5_shots = max(0.1, round(float((total_shots_sim > 8).mean() * 100), 1))
        
        # Valores promedio esperados
        expected_home_goals = round(float(home_goals_sim.mean()), 1)
        expected_away_goals = round(float(away_goals_sim.mean()), 1)
        expected_corners = round(float(total_corners_sim.mean()), 1)
        expected_cards = round(float(total_cards_sim.mean()), 1)
        expected_shots = round(float(total_shots_sim.mean()), 1)
        expected_home_shots = round(float(home_shots_sim.mean()), 1)
        expected_away_shots = round(float(away_shots_sim.mean()), 1)
        
        # Marcador exacto más probable
        scores = {}
        for h_g, a_g in zip(home_goals_sim, away_goals_sim):
            score_str = f"{h_g}-{a_g}"
            scores[score_str] = scores.get(score_str, 0) + 1
        probable_score = max(scores, key=scores.get)
        probable_score_pct = round((scores[probable_score] / simulations) * 100, 1)
        
        # Calcular matriz de marcadores exactos (0 a 4 goles) para heatmap
        score_matrix = {}
        for h in range(5):
            score_matrix[str(h)] = {}
            for a in range(5):
                count = int(np.sum((home_goals_sim == h) & (away_goals_sim == a)))
                score_matrix[str(h)][str(a)] = round((count / simulations) * 100, 2)
        
        # Calcular Cuotas Proyectadas (Decimales)
        odds_home = round(100.0 / home_win_pct, 2)
        odds_draw = round(100.0 / draw_pct, 2)
        odds_away = round(100.0 / away_win_pct, 2)
        odds_over25 = round(100.0 / prob_over_2_5_goals, 2)
        odds_btts = round(100.0 / prob_btts, 2)
        
        # Proyecciones ML (Random Forest)
        ml_pred = cls.predict_advanced(
            home_rating, away_rating,
            home_form_score, away_form_score,
            home_goals_base, away_goals_base,
            home_corners_base, away_corners_base,
            home_shots_base, away_shots_base,
            home_cards_base, away_cards_base,
            home_goalkicks_base, away_goalkicks_base,
            home_throwins_base, away_throwins_base,
            home_saves_base, away_saves_base,
            home_total_shots_base, away_total_shots_base
        )
        
        # Calcular probabilidades de Over/Under para Tiros al Arco (SOT)
        prob_over_7_5_shots = max(0.1, round(float((total_shots_sim > 7).mean() * 100), 1))
        prob_over_8_5_shots = max(0.1, round(float((total_shots_sim > 8).mean() * 100), 1))
        prob_over_9_5_shots = max(0.1, round(float((total_shots_sim > 9).mean() * 100), 1))
        
        prob_over_home_3_5 = max(0.1, round(float((home_shots_sim > 3).mean() * 100), 1))
        prob_over_home_4_5 = max(0.1, round(float((home_shots_sim > 4).mean() * 100), 1))
        
        prob_over_away_3_5 = max(0.1, round(float((away_shots_sim > 3).mean() * 100), 1))
        prob_over_away_4_5 = max(0.1, round(float((away_shots_sim > 4).mean() * 100), 1))

        shots_analysis = {
            "home_expected": expected_home_shots,
            "away_expected": expected_away_shots,
            "total_expected": expected_shots,
            "ml_projected": ml_pred["ml_shots"],
            "over_under": {
                "total_o75": prob_over_7_5_shots,
                "total_u75": round(100.0 - prob_over_7_5_shots, 1),
                "total_o85": prob_over_8_5_shots,
                "total_u85": round(100.0 - prob_over_8_5_shots, 1),
                "total_o95": prob_over_9_5_shots,
                "total_u95": round(100.0 - prob_over_9_5_shots, 1),
                "home_o35": prob_over_home_3_5,
                "home_u35": round(100.0 - prob_over_home_3_5, 1),
                "home_o45": prob_over_home_4_5,
                "home_u45": round(100.0 - prob_over_home_4_5, 1),
                "away_o35": prob_over_away_3_5,
                "away_u35": round(100.0 - prob_over_away_3_5, 1),
                "away_o45": prob_over_away_4_5,
                "away_u45": round(100.0 - prob_over_away_4_5, 1)
            }
        }

        # Calcular probabilidades de Over/Under para Remates Totales (Total Shots)
        expected_home_total_shots = round(float(home_total_shots_sim.mean()), 1)
        expected_away_total_shots = round(float(away_total_shots_sim.mean()), 1)
        expected_total_total_shots = round(float(total_total_shots_sim.mean()), 1)
        
        prob_over_22_5_tot_shots = max(0.1, round(float((total_total_shots_sim > 22).mean() * 100), 1))
        prob_over_24_5_tot_shots = max(0.1, round(float((total_total_shots_sim > 24).mean() * 100), 1))
        prob_over_26_5_tot_shots = max(0.1, round(float((total_total_shots_sim > 26).mean() * 100), 1))
        
        prob_over_home_11_5_tot_shots = max(0.1, round(float((home_total_shots_sim > 11).mean() * 100), 1))
        prob_over_home_13_5_tot_shots = max(0.1, round(float((home_total_shots_sim > 13).mean() * 100), 1))
        
        prob_over_away_11_5_tot_shots = max(0.1, round(float((away_total_shots_sim > 11).mean() * 100), 1))
        prob_over_away_13_5_tot_shots = max(0.1, round(float((away_total_shots_sim > 13).mean() * 100), 1))

        total_shots_analysis = {
            "home_expected": expected_home_total_shots,
            "away_expected": expected_away_total_shots,
            "total_expected": expected_total_total_shots,
            "ml_projected": ml_pred["ml_total_shots"],
            "over_under": {
                "total_o225": prob_over_22_5_tot_shots,
                "total_u225": round(100.0 - prob_over_22_5_tot_shots, 1),
                "total_o245": prob_over_24_5_tot_shots,
                "total_u245": round(100.0 - prob_over_24_5_tot_shots, 1),
                "total_o265": prob_over_26_5_tot_shots,
                "total_u265": round(100.0 - prob_over_26_5_tot_shots, 1),
                "home_o115": prob_over_home_11_5_tot_shots,
                "home_u115": round(100.0 - prob_over_home_11_5_tot_shots, 1),
                "home_o135": prob_over_home_13_5_tot_shots,
                "home_u135": round(100.0 - prob_over_home_13_5_tot_shots, 1),
                "away_o115": prob_over_away_11_5_tot_shots,
                "away_u115": round(100.0 - prob_over_away_11_5_tot_shots, 1),
                "away_o135": prob_over_away_13_5_tot_shots,
                "away_u135": round(100.0 - prob_over_away_13_5_tot_shots, 1)
            }
        }

        # Calcular probabilidades de Over/Under para Tarjetas Amarillas
        expected_home_cards = round(float(home_cards_sim.mean()), 1)
        expected_away_cards = round(float(away_cards_sim.mean()), 1)
        
        prob_over_3_5_cards = max(0.1, round(float((total_cards_sim > 3).mean() * 100), 1))
        prob_over_4_5_cards = max(0.1, round(float((total_cards_sim > 4).mean() * 100), 1))
        prob_over_5_5_cards = max(0.1, round(float((total_cards_sim > 5).mean() * 100), 1))
        
        prob_over_home_1_5 = max(0.1, round(float((home_cards_sim > 1).mean() * 100), 1))
        prob_over_home_2_5 = max(0.1, round(float((home_cards_sim > 2).mean() * 100), 1))
        
        prob_over_away_1_5 = max(0.1, round(float((away_cards_sim > 1).mean() * 100), 1))
        prob_over_away_2_5 = max(0.1, round(float((away_cards_sim > 2).mean() * 100), 1))

        cards_analysis = {
            "home_expected": expected_home_cards,
            "away_expected": expected_away_cards,
            "total_expected": expected_cards,
            "ml_projected": ml_pred["ml_cards"],
            "over_under": {
                "total_o35": prob_over_3_5_cards,
                "total_u35": round(100.0 - prob_over_3_5_cards, 1),
                "total_o45": prob_over_4_5_cards,
                "total_u45": round(100.0 - prob_over_4_5_cards, 1),
                "total_o55": prob_over_5_5_cards,
                "total_u55": round(100.0 - prob_over_5_5_cards, 1),
                "home_o15": prob_over_home_1_5,
                "home_u15": round(100.0 - prob_over_home_1_5, 1),
                "home_o25": prob_over_home_2_5,
                "home_u25": round(100.0 - prob_over_home_2_5, 1),
                "away_o15": prob_over_away_1_5,
                "away_u15": round(100.0 - prob_over_away_1_5, 1),
                "away_o25": prob_over_away_2_5,
                "away_u25": round(100.0 - prob_over_away_2_5, 1)
            }
        }

        # Calcular probabilidades de Over/Under para Saques de Puerta (Goal Kicks)
        expected_home_gk = round(float(home_goalkicks_sim.mean()), 1)
        expected_away_gk = round(float(away_goalkicks_sim.mean()), 1)
        expected_total_gk = round(float(total_goalkicks_sim.mean()), 1)
        
        prob_over_12_5_gk = max(0.1, round(float((total_goalkicks_sim > 12).mean() * 100), 1))
        prob_over_14_5_gk = max(0.1, round(float((total_goalkicks_sim > 14).mean() * 100), 1))
        prob_over_16_5_gk = max(0.1, round(float((total_goalkicks_sim > 16).mean() * 100), 1))
        
        prob_over_home_6_5_gk = max(0.1, round(float((home_goalkicks_sim > 6).mean() * 100), 1))
        prob_over_home_8_5_gk = max(0.1, round(float((home_goalkicks_sim > 8).mean() * 100), 1))
        
        prob_over_away_6_5_gk = max(0.1, round(float((away_goalkicks_sim > 6).mean() * 100), 1))
        prob_over_away_8_5_gk = max(0.1, round(float((away_goalkicks_sim > 8).mean() * 100), 1))

        goalkicks_analysis = {
            "home_expected": expected_home_gk,
            "away_expected": expected_away_gk,
            "total_expected": expected_total_gk,
            "ml_projected": ml_pred["ml_goalkicks"],
            "over_under": {
                "total_o125": prob_over_12_5_gk,
                "total_u125": round(100.0 - prob_over_12_5_gk, 1),
                "total_o145": prob_over_14_5_gk,
                "total_u145": round(100.0 - prob_over_14_5_gk, 1),
                "total_o165": prob_over_16_5_gk,
                "total_u165": round(100.0 - prob_over_16_5_gk, 1),
                "home_o65": prob_over_home_6_5_gk,
                "home_u65": round(100.0 - prob_over_home_6_5_gk, 1),
                "home_o85": prob_over_home_8_5_gk,
                "home_u85": round(100.0 - prob_over_home_8_5_gk, 1),
                "away_o65": prob_over_away_6_5_gk,
                "away_u65": round(100.0 - prob_over_away_6_5_gk, 1),
                "away_o85": prob_over_away_8_5_gk,
                "away_u85": round(100.0 - prob_over_away_8_5_gk, 1)
            }
        }

        # Calcular probabilidades de Over/Under para Saques de Banda (Throw-ins)
        expected_home_ti = round(float(home_throwins_sim.mean()), 1)
        expected_away_ti = round(float(away_throwins_sim.mean()), 1)
        expected_total_ti = round(float(total_throwins_sim.mean()), 1)
        
        prob_over_36_5_ti = max(0.1, round(float((total_throwins_sim > 36).mean() * 100), 1))
        prob_over_40_5_ti = max(0.1, round(float((total_throwins_sim > 40).mean() * 100), 1))
        prob_over_44_5_ti = max(0.1, round(float((total_throwins_sim > 44).mean() * 100), 1))
        
        prob_over_home_18_5_ti = max(0.1, round(float((home_throwins_sim > 18).mean() * 100), 1))
        prob_over_home_22_5_ti = max(0.1, round(float((home_throwins_sim > 22).mean() * 100), 1))
        
        prob_over_away_18_5_ti = max(0.1, round(float((away_throwins_sim > 18).mean() * 100), 1))
        prob_over_away_22_5_ti = max(0.1, round(float((away_throwins_sim > 22).mean() * 100), 1))

        throwins_analysis = {
            "home_expected": expected_home_ti,
            "away_expected": expected_away_ti,
            "total_expected": expected_total_ti,
            "ml_projected": ml_pred["ml_throwins"],
            "over_under": {
                "total_o365": prob_over_36_5_ti,
                "total_u365": round(100.0 - prob_over_36_5_ti, 1),
                "total_o405": prob_over_40_5_ti,
                "total_u405": round(100.0 - prob_over_40_5_ti, 1),
                "total_o445": prob_over_44_5_ti,
                "total_u445": round(100.0 - prob_over_44_5_ti, 1),
                "home_o185": prob_over_home_18_5_ti,
                "home_u185": round(100.0 - prob_over_home_18_5_ti, 1),
                "home_o225": prob_over_home_22_5_ti,
                "home_u225": round(100.0 - prob_over_home_22_5_ti, 1),
                "away_o185": prob_over_away_18_5_ti,
                "away_u185": round(100.0 - prob_over_away_18_5_ti, 1),
                "away_o225": prob_over_away_22_5_ti,
                "away_u225": round(100.0 - prob_over_away_22_5_ti, 1)
            }
        }

        # Calcular probabilidades de Over/Under para Paradas de Portero (Goalkeeper Saves)
        expected_home_saves = round(float(home_saves_sim.mean()), 1)
        expected_away_saves = round(float(away_saves_sim.mean()), 1)
        expected_total_saves = round(float(total_saves_sim.mean()), 1)
        
        prob_over_4_5_saves = max(0.1, round(float((total_saves_sim > 4).mean() * 100), 1))
        prob_over_6_5_saves = max(0.1, round(float((total_saves_sim > 6).mean() * 100), 1))
        prob_over_8_5_saves = max(0.1, round(float((total_saves_sim > 8).mean() * 100), 1))
        
        prob_over_home_2_5_saves = max(0.1, round(float((home_saves_sim > 2).mean() * 100), 1))
        prob_over_home_3_5_saves = max(0.1, round(float((home_saves_sim > 3).mean() * 100), 1))
        
        prob_over_away_2_5_saves = max(0.1, round(float((away_saves_sim > 2).mean() * 100), 1))
        prob_over_away_3_5_saves = max(0.1, round(float((away_saves_sim > 3).mean() * 100), 1))

        saves_analysis = {
            "home_expected": expected_home_saves,
            "away_expected": expected_away_saves,
            "total_expected": expected_total_saves,
            "ml_projected": ml_pred["ml_saves"],
            "over_under": {
                "total_o45": prob_over_4_5_saves,
                "total_u45": round(100.0 - prob_over_4_5_saves, 1),
                "total_o65": prob_over_6_5_saves,
                "total_u65": round(100.0 - prob_over_6_5_saves, 1),
                "total_o85": prob_over_8_5_saves,
                "total_u85": round(100.0 - prob_over_8_5_saves, 1),
                "home_o25": prob_over_home_2_5_saves,
                "home_u25": round(100.0 - prob_over_home_2_5_saves, 1),
                "home_o35": prob_over_home_3_5_saves,
                "home_u35": round(100.0 - prob_over_home_3_5_saves, 1),
                "away_o25": prob_over_away_2_5_saves,
                "away_u25": round(100.0 - prob_over_away_2_5_saves, 1),
                "away_o35": prob_over_away_3_5_saves,
                "away_u35": round(100.0 - prob_over_away_3_5_saves, 1)
            }
        }

        # ── MERCADOS PRINCIPALES: goles, córners, tarjetas y 1er tiempo ──
        prob_over_1_5_goals = max(0.1, round(float((total_goals_sim > 1).mean() * 100), 1))
        prob_over_3_5_goals = max(0.1, round(float((total_goals_sim > 3).mean() * 100), 1))

        prob_over_7_5_corners = max(0.1, round(float((total_corners_sim > 7).mean() * 100), 1))
        prob_over_8_5_corners = max(0.1, round(float((total_corners_sim > 8).mean() * 100), 1))
        prob_over_9_5_corners = max(0.1, round(float((total_corners_sim > 9).mean() * 100), 1))
        prob_over_10_5_corners = max(0.1, round(float((total_corners_sim > 10).mean() * 100), 1))

        # Primer tiempo: históricamente ~44% de los goles caen antes del descanso
        fh_home_sim = np.random.poisson(home_lambda_goals * 0.44, simulations)
        fh_away_sim = np.random.poisson(away_lambda_goals * 0.44, simulations)
        fh_total_sim = fh_home_sim + fh_away_sim
        fh_expected = round(float(fh_total_sim.mean()), 2)
        prob_fh_over_0_5 = max(0.1, round(float((fh_total_sim > 0).mean() * 100), 1))
        prob_fh_over_1_5 = max(0.1, round(float((fh_total_sim > 1).mean() * 100), 1))
        prob_fh_over_2_5 = max(0.1, round(float((fh_total_sim > 2).mean() * 100), 1))

        markets = {
            "goals": {
                "expected": round(expected_home_goals + expected_away_goals, 1),
                "o15": prob_over_1_5_goals, "u15": round(100.0 - prob_over_1_5_goals, 1),
                "o25": prob_over_2_5_goals, "u25": round(100.0 - prob_over_2_5_goals, 1),
                "o35": prob_over_3_5_goals, "u35": round(100.0 - prob_over_3_5_goals, 1),
            },
            "first_half": {
                "expected": fh_expected,
                "o05": prob_fh_over_0_5, "u05": round(100.0 - prob_fh_over_0_5, 1),
                "o15": prob_fh_over_1_5, "u15": round(100.0 - prob_fh_over_1_5, 1),
                "o25": prob_fh_over_2_5, "u25": round(100.0 - prob_fh_over_2_5, 1),
            },
            "corners": {
                "expected": expected_corners,
                "o75": prob_over_7_5_corners, "u75": round(100.0 - prob_over_7_5_corners, 1),
                "o85": prob_over_8_5_corners, "u85": round(100.0 - prob_over_8_5_corners, 1),
                "o95": prob_over_9_5_corners, "u95": round(100.0 - prob_over_9_5_corners, 1),
                "o105": prob_over_10_5_corners, "u105": round(100.0 - prob_over_10_5_corners, 1),
            },
            "cards": {
                "expected": expected_cards,
                "o35": prob_over_3_5_cards, "u35": round(100.0 - prob_over_3_5_cards, 1),
                "o45": prob_over_4_5_cards, "u45": round(100.0 - prob_over_4_5_cards, 1),
                "o55": prob_over_5_5_cards, "u55": round(100.0 - prob_over_5_5_cards, 1),
            },
        }

        resultado = {
            "markets": markets,
            "probabilities": {
                "home_win": home_win_pct,
                "draw": draw_pct,
                "away_win": away_win_pct,
                "over_2_5_goals": prob_over_2_5_goals,
                "btts": prob_btts,
                "over_8_5_shots": prob_over_8_5_shots
            },
            "expected_values": {
                "home_goals": expected_home_goals,
                "away_goals": expected_away_goals,
                "total_corners": expected_corners,
                "total_cards": expected_cards,
                "total_shots": expected_shots,
                "home_shots": expected_home_shots,
                "away_shots": expected_away_shots,
                "home_cards": expected_home_cards,
                "away_cards": expected_away_cards,
                "home_goalkicks": expected_home_gk,
                "away_goalkicks": expected_away_gk,
                "total_goalkicks": expected_total_gk,
                "home_throwins": expected_home_ti,
                "away_throwins": expected_away_ti,
                "total_throwins": expected_total_ti,
                "home_saves": expected_home_saves,
                "away_saves": expected_away_saves,
                "total_saves": expected_total_saves,
                "home_total_shots": expected_home_total_shots,
                "away_total_shots": expected_away_total_shots,
                "total_total_shots": expected_total_total_shots
            },
            "exact_score": {
                "score": probable_score,
                "probability": probable_score_pct
            },
            "score_matrix": score_matrix,
            "shots_analysis": shots_analysis,
            "total_shots_analysis": total_shots_analysis,
            "cards_analysis": cards_analysis,
            "goalkicks_analysis": goalkicks_analysis,
            "throwins_analysis": throwins_analysis,
            "saves_analysis": saves_analysis,
            "ml_projections": ml_pred,
            "odds": {
                "home": odds_home,
                "draw": odds_draw,
                "away": odds_away,
                "over_2_5": odds_over25,
                "btts": odds_btts
            },
            "modifiers": {
                "home_modifier": home_mod_total,
                "away_modifier": away_mod_total,
                "home_advantage": round((home_adv_attack - 1.0) * 100, 1),
                "quality_diff": round(rating_diff, 2),
                "home_form": round(home_form_score * 100, 1),
                "away_form": round(away_form_score * 100, 1)
            }
        }

        if not return_raw:
            return resultado

        # Arrays crudos por iteración (10.000 simulaciones), correlacionados
        # entre sí porque salen de LA MISMA corrida. Permiten calcular la
        # probabilidad CONJUNTA real de combinar mercados distintos (p. ej.
        # "gana el local Y más de 8.5 córners") en vez de multiplicar
        # probabilidades sueltas como si fueran independientes, que es lo
        # que infla las cuotas de una casa de apuestas.
        # No se exponen en el dict JSON normal (bloatearía cada respuesta
        # con ~80.000 números); solo viajan cuando se piden explícitamente.
        raw = {
            "home_goals": home_goals_sim, "away_goals": away_goals_sim,
            "home_corners": home_corners_sim, "away_corners": away_corners_sim,
            "home_cards": home_cards_sim, "away_cards": away_cards_sim,
            "home_shots": home_shots_sim, "away_shots": away_shots_sim,
            "home_total_shots": home_total_shots_sim, "away_total_shots": away_total_shots_sim,
            "fh_home_goals": fh_home_sim, "fh_away_goals": fh_away_sim,
        }
        return resultado, raw
