"""Script opcional (no forma parte del servidor web).
Instalar aparte: python -m pip install soccerdata
"""
import soccerdata as sd
import pandas as pd
import sys

def get_soccerdata_stats(league='ESP-La Liga', season='2324'):
    try:
        print(f"--- Intentando cargar datos de FBref para {league} {season} ---")
        fbref = sd.FBref(leagues=[league], seasons=[season])
        schedule = fbref.read_schedule()
        
        print("\nPróximos partidos encontrados:")
        print(schedule.head())
        
        return schedule
    except Exception as e:
        print(f"\nError al usar soccerdata: {e}")
        print("\nNota: Soccerdata requiere pandas y lxml instalado.")
        return None

if __name__ == "__main__":
    get_soccerdata_stats()
