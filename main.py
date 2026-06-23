import os
from dotenv import load_dotenv
from data_fetcher import FootballDataFetcher
from ai_predictor import AIPredictor

load_dotenv()

def main():
    # Verificar llaves de API
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("FOOTBALL_DATA_API_KEY"):
        print("Error: Por favor configura GEMINI_API_KEY y FOOTBALL_DATA_API_KEY en el archivo .env")
        print("Puedes usar .env.example como guía.")
        return

    fetcher = FootballDataFetcher()
    predictor = AIPredictor()

    print("--- Sistema de Pronósticos de Fútbol con IA ---")
    print("Obteniendo próximos partidos de La Liga (España)...")
    
    # PD = Primera División (La Liga)
    matches = fetcher.get_fixtures(league="PD")

    if not matches:
        print("No se encontraron partidos o error en la API.")
        return

    # Tomar el primer partido como ejemplo
    match = matches[0]
    home_name = match['homeTeam']['name']
    away_name = match['awayTeam']['name']
    home_id = match['homeTeam']['id']
    away_id = match['awayTeam']['id']

    print(f"\nAnalizando el partido: {home_name} vs {away_name}...")
    
    # Obtener estadísticas para la IA
    stats = fetcher.get_match_data_for_ai(home_id, away_id)
    
    match_info = {
        "home_team": home_name,
        "away_team": away_name,
        "stats": stats
    }

    print("Generando pronóstico con IA (Gemini)...")
    prediction = predictor.get_prediction(match_info)
    
    print("\n--- PRONÓSTICO ---")
    print(prediction)

if __name__ == "__main__":
    main()
