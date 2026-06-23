import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class StatsEngine:
    _model_goals = None
    _model_corners = None

    @classmethod
    def _train_models(cls):
        """
        Entrena modelos de Random Forest usando un dataset simulado de alto rendimiento.
        """
        if cls._model_goals is not None:
            return

        np.random.seed(42)
        partidos = 1000
        
        # Simulación de dataset (según lógica del usuario)
        data = pd.DataFrame({
            "home_avg_goals": np.random.uniform(0.8, 2.5, partidos),
            "away_avg_goals": np.random.uniform(0.8, 2.5, partidos),
            "home_avg_corners": np.random.uniform(3, 7, partidos),
            "away_avg_corners": np.random.uniform(3, 7, partidos),
        })

        data["total_goals"] = data["home_avg_goals"] + data["away_avg_goals"] + np.random.normal(0, 0.5, partidos)
        data["total_corners"] = data["home_avg_corners"] + data["away_avg_corners"] + np.random.normal(0, 1, partidos)

        X = data[["home_avg_goals", "away_avg_goals", "home_avg_corners", "away_avg_corners"]]
        
        cls._model_goals = RandomForestRegressor(n_estimators=100, random_state=42)
        cls._model_corners = RandomForestRegressor(n_estimators=100, random_state=42)
        
        cls._model_goals.fit(X, data["total_goals"])
        cls._model_corners.fit(X, data["total_corners"])

    @classmethod
    def predict_advanced(cls, home_avg_g, away_avg_g, home_avg_c, away_avg_c):
        """
        Usa Machine Learning (Random Forest) para predecir goles y córners.
        """
        cls._train_models()
        
        input_data = pd.DataFrame([{
            "home_avg_goals": home_avg_g,
            "away_avg_goals": away_avg_g,
            "home_avg_corners": home_avg_c,
            "away_avg_corners": away_avg_c
        }])
        
        pred_goals = cls._model_goals.predict(input_data)[0]
        pred_corners = cls._model_corners.predict(input_data)[0]
        
        return {
            "ml_goals": round(float(pred_goals), 2),
            "ml_corners": round(float(pred_corners), 2)
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
    def simulate_match(cls, home_stats, away_stats, simulations=10000):
        """
        Simulación Monte Carlo completa para un partido de fútbol, calculando goles,
        córners, tarjetas y disparos al arco usando distribuciones de Poisson.
        """
        # 1. Goles (ajustado por factor ataque/defensa)
        home_goals_lambda = home_stats['attack']['goals_per_game']
        away_goals_lambda = away_stats['attack']['goals_per_game']
        home_defense_factor = home_stats['defense']['goals_conceded']
        away_defense_factor = away_stats['defense']['goals_conceded']
        
        home_lambda_goals = max(0.2, (home_goals_lambda + away_defense_factor) / 2.0)
        away_lambda_goals = max(0.2, (away_goals_lambda + home_defense_factor) / 2.0)
        
        # 2. Córners
        home_corners_lambda = home_stats['attack']['corners']
        away_corners_lambda = away_stats['attack']['corners']
        
        # 3. Tarjetas amarillas
        home_cards_lambda = home_stats['summary'].get('yellow_cards_per_game', 2.0)
        away_cards_lambda = away_stats['summary'].get('yellow_cards_per_game', 2.2)
        
        # 4. Disparos al arco
        home_shots_lambda = home_stats['attack'].get('shots_on_target', 4.5)
        away_shots_lambda = away_stats['attack'].get('shots_on_target', 4.0)
        
        # Generar simulaciones estocásticas
        np.random.seed(42)
        home_goals_sim = np.random.poisson(home_lambda_goals, simulations)
        away_goals_sim = np.random.poisson(away_lambda_goals, simulations)
        total_goals_sim = home_goals_sim + away_goals_sim
        
        home_corners_sim = np.random.poisson(home_corners_lambda, simulations)
        away_corners_sim = np.random.poisson(away_corners_lambda, simulations)
        total_corners_sim = home_corners_sim + away_corners_sim
        
        home_cards_sim = np.random.poisson(home_cards_lambda, simulations)
        away_cards_sim = np.random.poisson(away_cards_lambda, simulations)
        total_cards_sim = home_cards_sim + away_cards_sim
        
        home_shots_sim = np.random.poisson(home_shots_lambda, simulations)
        away_shots_sim = np.random.poisson(away_shots_lambda, simulations)
        total_shots_sim = home_shots_sim + away_shots_sim
        
        # Calcular probabilidades de resultado
        home_wins = int(np.sum(home_goals_sim > away_goals_sim))
        draws = int(np.sum(home_goals_sim == away_goals_sim))
        away_wins = int(np.sum(home_goals_sim < away_goals_sim))
        
        home_win_pct = round((home_wins / simulations) * 100, 1)
        draw_pct = round((draws / simulations) * 100, 1)
        away_win_pct = round((away_wins / simulations) * 100, 1)
        
        # Over/Under y BTTS
        prob_over_2_5_goals = round(float((total_goals_sim > 2).mean() * 100), 1)
        prob_btts = round(float(((home_goals_sim > 0) & (away_goals_sim > 0)).mean() * 100), 1)
        
        # Valores promedio esperados
        expected_home_goals = round(float(home_goals_sim.mean()), 1)
        expected_away_goals = round(float(away_goals_sim.mean()), 1)
        expected_corners = round(float(total_corners_sim.mean()), 1)
        expected_cards = round(float(total_cards_sim.mean()), 1)
        expected_shots = round(float(total_shots_sim.mean()), 1)
        
        # Marcador exacto más probable
        scores = {}
        for h_g, a_g in zip(home_goals_sim, away_goals_sim):
            score_str = f"{h_g}-{a_g}"
            scores[score_str] = scores.get(score_str, 0) + 1
        probable_score = max(scores, key=scores.get)
        probable_score_pct = round((scores[probable_score] / simulations) * 100, 1)
        
        # Proyecciones ML (Random Forest)
        ml_pred = cls.predict_advanced(home_lambda_goals, away_lambda_goals, home_corners_lambda, away_corners_lambda)
        
        return {
            "probabilities": {
                "home_win": home_win_pct,
                "draw": draw_pct,
                "away_win": away_win_pct,
                "over_2_5_goals": prob_over_2_5_goals,
                "btts": prob_btts
            },
            "expected_values": {
                "home_goals": expected_home_goals,
                "away_goals": expected_away_goals,
                "total_corners": expected_corners,
                "total_cards": expected_cards,
                "total_shots": expected_shots
            },
            "exact_score": {
                "score": probable_score,
                "probability": probable_score_pct
            },
            "ml_projections": ml_pred
        }
