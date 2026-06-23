import requests
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

class FootballDataFetcher:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        self.apisports_key = os.getenv("APISPORTS_API_KEY")
        self.base_url = "https://api.football-data.org/v4"
        self.apisports_url = "https://v3.football.api-sports.io"
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        self.apisports_headers = {"x-apisports-key": self.apisports_key} if self.apisports_key else {}

        # ── MASTER TEAM ID MAP ──────────────────────────────────
        self.master_teams = {
            # LaLiga
            "Real Madrid CF": 86, "FC Barcelona": 81, "Atlético de Madrid": 78,
            "Villarreal CF": 299, "Real Betis": 90, "RCD Espanyol": 80,
            "RC Celta": 82, "Real Sociedad": 92, "Athletic Club": 77,
            "CA Osasuna": 79, "Getafe CF": 88, "Sevilla FC": 559,
            "Deportivo Alavés": 263, "Valencia CF": 95, "Girona FC": 298,
            "Rayo Vallecano": 87, "RCD Mallorca": 89, "Levante UD": 264,
            "Real Valladolid": 250, "UD Las Palmas": 275, "CD Leganés": 345,
            # Premier League
            "Arsenal FC": 57, "Manchester City FC": 65, "Liverpool FC": 64,
            "Aston Villa FC": 58, "Manchester United FC": 66, "Chelsea FC": 61,
            "Tottenham Hotspur FC": 73, "Newcastle United FC": 67,
            "West Ham United FC": 563, "Brighton & Hove Albion FC": 397,
            "Everton FC": 62, "Fulham FC": 63, "Bournemouth": 1044,
            "Crystal Palace FC": 354, "Wolverhampton Wanderers": 76,
            "Leicester City FC": 338, "Brentford FC": 402, "Nottingham Forest FC": 351,
            # Serie A
            "Inter Milan": 108, "AC Milan": 98, "Juventus FC": 109,
            "SSC Napoli": 113, "AS Roma": 100, "Atalanta": 102, "SS Lazio": 110,
            "Bologna": 103, "ACF Fiorentina": 99, "Torino FC": 586,
            "Genoa CFC": 107, "Monza": 586, "Como 1907": 5890,
            # Bundesliga
            "FC Bayern München": 5, "Bayer 04 Leverkusen": 3, "Borussia Dortmund": 4,
            "RB Leipzig": 721, "VfB Stuttgart": 10, "Eintracht Frankfurt": 9,
            "SC Freiburg": 17, "TSG Hoffenheim": 533, "Werder Bremen": 12,
            "Union Berlin": 28513, "Borussia Mönchengladbach": 18,
            "FC Augsburg": 16, "VfL Wolfsburg": 11,
            # Ligue 1
            "Paris Saint-Germain FC": 524, "AS Monaco FC": 548,
            "Olympique de Marseille": 516, "Lille OSC": 521,
            "Olympique Lyonnais": 523, "OGC Nice": 522, "Stade Rennais FC": 529,
            "RC Lens": 532, "Stade de Reims": 547,
            # Serie B
            "Sassuolo": 105, "Sampdoria": 103, "Palermo": 115,
            # Argentina
            "River Plate": 3211, "Boca Juniors": 3201, "Vélez Sarsfield": 3215,
            "Racing Club": 3203, "Independiente": 3207, "San Lorenzo": 3214,
            "Estudiantes L.P.": 3204, "Rosario Central": 3213,
            "Newell's Old Boys": 3209, "Talleres": 3217, "Huracán": 3205,
            "Belgrano": 3202, "Defensa y Justicia": 3220, "Lanús": 3208,
            # Brasil
            "Flamengo": 5981, "Palmeiras": 1963, "Botafogo": 1967,
            "Corinthians": 1977, "São Paulo FC": 5982, "Fluminense": 1961,
            "Internacional": 1974, "Grêmio": 1972, "Atlético Mineiro": 1966,
            "Vasco da Gama": 1980, "Bahia": 1968, "Cruzeiro": 1971,
            "Fortaleza": 3573, "Santos FC": 1978,
            # Colombia
            "Atlético Nacional": 2274, "Millonarios": 2283, "Santa Fe": 2285,
            "Junior": 2279, "América de Cali": 2272, "Deportivo Cali": 2276,
            "Deportes Tolima": 2277, "Once Caldas": 2284,
            # México
            "Cruz Azul": 1951, "Tigres UANL": 1958, "Club América": 1946,
            "Chivas Guadalajara": 1953, "Monterrey": 1955, "Pumas UNAM": 1956,
            "Toluca": 1959, "Atlas": 1949, "León": 1954, "Tijuana": 1957,
            "Atlético San Luis": 10255, "Mazatlán": 2282,
            # Saudi Pro League
            "Al Hilal": 2822, "Al Ittihad": 2814, "Al Nassr": 2818,
            "Al Ahli": 2808, "Al Shabab": 2823, "Al Ettifaq": 2811,
            # MLS
            "Inter Miami CF": 306781, "LA Galaxy": 351, "LAFC": 31277,
            "Columbus Crew": 326, "Real Salt Lake": 1903, "Orlando City SC": 8586,
            # Other
            "Sporting CP": 498, "FC Porto": 503, "SL Benfica": 294,
            "PSV Eindhoven": 397, "Ajax": 678, "Feyenoord": 675,
            "Galatasaray": 442, "Fenerbahçe": 441, "Beşiktaş": 440,
        }

        # ── TEAM DATABASE (stadium, coach, country) ──────────────
        self.team_database = {
            "Real Madrid CF": {"stadium": "Santiago Bernabéu", "coach": "Carlo Ancelotti", "country": "España", "league": "LaLiga"},
            "FC Barcelona": {"stadium": "Spotify Camp Nou", "coach": "Hansi Flick", "country": "España", "league": "LaLiga"},
            "Atlético de Madrid": {"stadium": "Cívitas Metropolitano", "coach": "Diego Simeone", "country": "España", "league": "LaLiga"},
            "Manchester City FC": {"stadium": "Etihad Stadium", "coach": "Pep Guardiola", "country": "Inglaterra", "league": "Premier League"},
            "Liverpool FC": {"stadium": "Anfield", "coach": "Arne Slot", "country": "Inglaterra", "league": "Premier League"},
            "Arsenal FC": {"stadium": "Emirates Stadium", "coach": "Mikel Arteta", "country": "Inglaterra", "league": "Premier League"},
            "Inter Milan": {"stadium": "San Siro", "coach": "Simone Inzaghi", "country": "Italia", "league": "Serie A"},
            "FC Bayern München": {"stadium": "Allianz Arena", "coach": "Vincent Kompany", "country": "Alemania", "league": "Bundesliga"},
            "Paris Saint-Germain FC": {"stadium": "Parc des Princes", "coach": "Luis Enrique", "country": "Francia", "league": "Ligue 1"},
            "River Plate": {"stadium": "Más Monumental", "coach": "Marcelo Gallardo", "country": "Argentina", "league": "Liga Profesional"},
            "Boca Juniors": {"stadium": "La Bombonera", "coach": "Fernando Gago", "country": "Argentina", "league": "Liga Profesional"},
            "Flamengo": {"stadium": "Maracanã", "coach": "Filipe Luís", "country": "Brasil", "league": "Brasileirão"},
            "Palmeiras": {"stadium": "Allianz Parque", "coach": "Abel Ferreira", "country": "Brasil", "league": "Brasileirão"},
        }

    def get_crest(self, name):
        tid = self.master_teams.get(name)
        if not tid:
            for n, i in self.master_teams.items():
                if name.lower() in n.lower() or n.lower() in name.lower():
                    tid = i
                    break
        if tid and tid < 3000:
            return f"https://crests.football-data.org/{tid}.png"
        initials = "".join([w[0] for w in name.split()[:2]]).upper()
        return f"https://ui-avatars.com/api/?name={initials}&background=0d1117&color=00e87a&bold=true&size=40"

    def _get_complete_table_data(self):
        return {
            # ── EUROPA ──────────────────────────────────
            "PD": ["Real Madrid CF", "FC Barcelona", "Atlético de Madrid", "Villarreal CF", "Real Betis",
                   "Real Sociedad", "Athletic Club", "Girona FC", "CA Osasuna", "Sevilla FC",
                   "RCD Espanyol", "RC Celta", "Valencia CF", "Getafe CF", "Deportivo Alavés",
                   "Rayo Vallecano", "RCD Mallorca", "Levante UD", "Real Valladolid", "UD Las Palmas"],
            "PL": ["Manchester City FC", "Arsenal FC", "Liverpool FC", "Aston Villa FC", "Chelsea FC",
                   "Tottenham Hotspur FC", "Manchester United FC", "Newcastle United FC",
                   "West Ham United FC", "Brighton & Hove Albion FC", "Everton FC", "Fulham FC",
                   "Bournemouth", "Crystal Palace FC", "Wolverhampton Wanderers",
                   "Leicester City FC", "Brentford FC", "Nottingham Forest FC"],
            "SA": ["Inter Milan", "AC Milan", "Juventus FC", "SSC Napoli", "AS Roma", "Atalanta",
                   "SS Lazio", "Bologna", "ACF Fiorentina", "Torino FC", "Genoa CFC",
                   "Monza", "Como 1907", "Hellas Verona FC", "Cagliari Calcio",
                   "US Lecce", "Parma Calcio 1913", "Venezia FC", "Empoli FC", "Udinese Calcio"],
            "BL1": ["FC Bayern München", "Bayer 04 Leverkusen", "Borussia Dortmund", "RB Leipzig",
                    "VfB Stuttgart", "Eintracht Frankfurt", "SC Freiburg", "TSG Hoffenheim",
                    "Werder Bremen", "Union Berlin", "Borussia Mönchengladbach", "FC Augsburg",
                    "VfL Wolfsburg", "1. FC Heidenheim 1846", "FC St. Pauli", "1. FSV Mainz 05"],
            "FL1": ["Paris Saint-Germain FC", "AS Monaco FC", "Olympique de Marseille", "Lille OSC",
                    "Olympique Lyonnais", "OGC Nice", "Stade Rennais FC", "RC Lens",
                    "Stade de Reims", "RC Strasbourg Alsace", "Stade Brestois 29", "Montpellier HSC",
                    "Le Havre AC", "FC Nantes", "Toulouse FC", "Angers SCO"],
            "PPL": ["Sporting CP", "FC Porto", "SL Benfica", "SC Braga", "Vitória SC",
                    "Moreirense FC", "Famalicão", "Santa Clara", "Boavista FC", "Casa Pia AC",
                    "Gil Vicente FC", "Arouca FC", "FC Vizela", "Estoril Praia"],
            "DED": ["PSV Eindhoven", "Ajax", "Feyenoord", "AZ Alkmaar", "FC Twente",
                    "FC Utrecht", "Go Ahead Eagles", "NEC Nijmegen", "Sparta Rotterdam",
                    "FC Groningen", "SC Heerenveen", "PEC Zwolle", "Almere City FC", "NAC Breda"],
            "TSL": ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor", "Başakşehir",
                    "Samsunspor", "Eyüpspor", "Konyaspor", "Sivasspor", "Antalyaspor",
                    "Kasımpaşa", "Rizespor", "Gaziantep FK", "Alanyaspor"],
            "BEL": ["RSC Anderlecht", "Club Brugge KV", "K.A.A. Gent", "Royal Antwerp FC",
                    "KRC Genk", "Union Saint-Gilloise", "Standard Liège", "KV Mechelen",
                    "Cercle Brugge KSV", "OH Leuven", "Westerlo", "Beerschot VA"],
            "SPD": ["Real Zaragoza", "UD Almería", "Racing Santander", "CD Castellón",
                    "Sporting Gijón", "Málaga CF", "SD Eibar", "Real Oviedo",
                    "CD Leganés", "Granada CF", "Levante UD", "Tenerife",
                    "Eldense", "Ferrol", "Mirandes", "Albacete"],
            "SB": ["Sassuolo", "Sampdoria", "Palermo", "Cremonese", "Pisa SC",
                   "Spezia Calcio", "Modena FC", "Brescia Calcio", "Bari",
                   "Frosinone Calcio", "Cosenza Calcio", "Catanzaro"],
            "SPR": ["Zenit St. Petersburg", "CSKA Moscow", "Spartak Moscow", "Lokomotiv Moscow",
                    "Dynamo Moscow", "Krasnodar", "Akhmat Grozny", "Rubin Kazan"],
            "SPO": ["Celtic FC", "Rangers FC", "Heart of Midlothian FC", "Hibernian FC",
                    "Aberdeen FC", "St. Mirren FC", "Dundee United FC", "Motherwell FC"],
            "AUS": ["Red Bull Salzburg", "SK Sturm Graz", "FK Austria Wien",
                    "Rapid Wien", "RB Salzburg", "LASK"],
            # ── AMÉRICAS ────────────────────────────────
            "ARG": ["Vélez Sarsfield", "River Plate", "Racing Club", "Talleres", "Huracán",
                    "Boca Juniors", "Independiente", "Estudiantes L.P.", "Lanús", "Godoy Cruz",
                    "Unión", "Belgrano", "Instituto", "Argentinos Juniors", "Defensa y Justicia",
                    "Rosario Central", "Platense", "San Lorenzo", "Banfield", "Gimnasia L.P.",
                    "Tigre", "Barracas Central", "Newell's Old Boys", "Tucumán",
                    "Ind. Rivadavia", "Sarmiento", "Central Córdoba", "Riestra"],
            "BRA": ["Botafogo", "Palmeiras", "Flamengo", "Fortaleza", "Internacional",
                    "São Paulo FC", "Bahia", "Cruzeiro", "Atlético Mineiro", "Vasco da Gama",
                    "Corinthians", "Grêmio", "Fluminense", "Santos FC", "Bragantino",
                    "Athletico Paranaense", "Goiás EC", "Cuiabá", "América Mineiro", "Criciúma"],
            "COL": ["Deportivo Cali", "Atlético Nacional", "Millonarios", "Santa Fe", "Junior",
                    "América de Cali", "Once Caldas", "Deportes Tolima", "Peñarol",
                    "Ind. Medellín", "Envigado FC", "Bucaramanga"],
            "MX": ["Cruz Azul", "Tigres UANL", "Toluca", "Pumas UNAM", "Monterrey",
                   "Club América", "Atlético San Luis", "Chivas Guadalajara", "Tijuana",
                   "Atlas", "León", "Necaxa", "Puebla", "Juárez", "Mazatlán",
                   "Pachuca", "Santos Laguna", "FC Juárez"],
            "MLS": ["Inter Miami CF", "Columbus Crew", "LA Galaxy", "LAFC", "FC Cincinnati",
                    "Real Salt Lake", "Orlando City SC", "Portland Timbers", "Seattle Sounders",
                    "New York City FC", "Atlanta United FC", "Nashville SC",
                    "New England Revolution", "Colorado Rapids", "Austin FC"],
            "ECU": ["LDU Quito", "Emelec", "Barcelona SC", "Independiente del Valle",
                    "El Nacional", "Aucas", "Delfín", "Orense"],
            "CHI": ["Club Universidad de Chile", "Colo-Colo", "Universidad Católica",
                    "Deportes Antofagasta", "Huachipato", "Audax Italiano"],
            "URU": ["Peñarol", "Club Nacional de Football", "Defensor Sporting",
                    "CA Rentistas", "Danubio", "River Plate Montevideo"],
            "PAR": ["Club Olimpia", "Cerro Porteño", "Libertad", "Guaraní",
                    "Sol de América", "Deportivo Luqueño"],
            # ── ASIA Y OTROS ────────────────────────────
            "SPL": ["Al Hilal", "Al Ittihad", "Al Nassr", "Al Ahli", "Al Shabab",
                    "Al Ettifaq", "Al Taawoun", "Al Qadsiah", "Al Fayha", "Damac FC"],
            "J1": ["Vissel Kobe", "Sanfrecce Hiroshima", "Machida Zelvia", "Gamba Osaka",
                   "Kashima Antlers", "Kawasaki Frontale", "Yokohama F. Marinos",
                   "Cerezo Osaka", "Nagoya Grampus", "Urawa Red Diamonds"],
            "CSL": ["Shanghai Port", "Shanghai Shenhua", "Chengdu Rongcheng",
                    "Beijing Guoan", "Wuhan Three Towns", "Shandong Taishan",
                    "Zhejiang FC", "Tianjin Jinmen Tiger"],
            "ISL": ["Mumbai City FC", "Mohun Bagan SG", "Bengaluru FC", "Kerala Blasters",
                    "FC Goa", "ATK Mohun Bagan", "Hyderabad FC", "Odisha FC",
                    "Jamshedpur FC", "Northeast United FC"],
            "CAF": ["Ahly SC", "Zamalek SC", "Pyramids FC", "Esperance Sportive",
                    "Mamelodi Sundowns", "Kaizer Chiefs", "Al-Merrikh", "Wydad Athletic"],
            "NIG": ["Enyimba FC", "Shooting Stars SC", "Rivers United", "Kano Pillars",
                    "Heartland FC", "Lobi Stars", "Plateau United"],
        }

    # ── WORLD CUP 2026 DATA ──────────────────────────────────────
    def get_worldcup_data(self):
        """Returns FIFA World Cup 2026 group data with standings and matches."""
        draw = {
            "A": ["México", "Sudáfrica", "Corea del Sur", "Chequia"],
            "B": ["Canadá", "Bosnia", "Qatar", "Suiza"],
            "C": ["Brasil", "Marruecos", "Haití", "Escocia"],
            "D": ["Estados Unidos", "Paraguay", "Australia", "Turquía"],
            "E": ["Alemania", "Curazao", "Costa de Marfil", "Ecuador"],
            "F": ["Países Bajos", "Japón", "Ucrania", "Túnez"],
            "G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
            "H": ["España", "Cabo Verde", "Arabia Saudí", "Uruguay"],
            "I": ["Francia", "Senegal", "Bolivia", "Noruega"],
            "J": ["Argentina", "Argelia", "Austria", "Jordania"],
            "K": ["Portugal", "Jamaica", "Uzbekistán", "Colombia"],
            "L": ["Inglaterra", "Croacia", "Ghana", "Panamá"]
        }
        
        flags = {
            "México": "🇲🇽", "Sudáfrica": "🇿🇦", "Corea del Sur": "🇰🇷", "Chequia": "🇨🇿",
            "Canadá": "🇨🇦", "Bosnia": "🇧🇦", "Qatar": "🇶🇦", "Suiza": "🇨🇭",
            "Brasil": "🇧🇷", "Marruecos": "🇲🇦", "Haití": "🇭🇹", "Escocia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
            "Estados Unidos": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Turquía": "🇹🇷",
            "Alemania": "🇩🇪", "Curazao": "🇨🇼", "Costa de Marfil": "🇨🇮", "Ecuador": "🇪🇨",
            "Países Bajos": "🇳🇱", "Japón": "🇯🇵", "Ucrania": "🇺🇦", "Túnez": "🇹🇳",
            "Bélgica": "🇧🇪", "Egipto": "🇪🇬", "Irán": "🇮🇷", "Nueva Zelanda": "🇳🇿",
            "España": "🇪🇸", "Cabo Verde": "🇨🇻", "Arabia Saudí": "🇸🇦", "Uruguay": "🇺🇾",
            "Francia": "🇫🇷", "Senegal": "🇸🇳", "Bolivia": "🇧🇴", "Noruega": "🇳🇴",
            "Argentina": "🇦🇷", "Argelia": "🇩🇿", "Austria": "🇦🇹", "Jordania": "🇯🇴",
            "Portugal": "🇵🇹", "Jamaica": "🇯🇲", "Uzbekistán": "🇺🇿", "Colombia": "🇨🇴",
            "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croacia": "🇭🇷", "Ghana": "🇬🇭", "Panamá": "🇵🇦"
        }

        groups = {}
        
        # J3 dates and schedule mapping
        dates = {
            "A": ("11 Jun", "15 Jun", "19 Jun"),
            "B": ("11 Jun", "15 Jun", "19 Jun"),
            "C": ("12 Jun", "16 Jun", "20 Jun"),
            "D": ("12 Jun", "16 Jun", "20 Jun"),
            "E": ("12 Jun", "16 Jun", "21 Jun"),
            "F": ("13 Jun", "17 Jun", "21 Jun"),
            "G": ("13 Jun", "17 Jun", "21 Jun"),
            "H": ("13 Jun", "17 Jun", "22 Jun"),
            "I": ("14 Jun", "18 Jun", "22 Jun"),
            "J": ("14 Jun", "18 Jun", "22 Jun"),
            "K": ("14 Jun", "18 Jun", "23 Jun"),
            "L": ("14 Jun", "18 Jun", "23 Jun"),
        }
        
        # Precooked realistic results for (M1, M2, M3, M4) per group
        # Each group gets slightly different but realistic results to make the standings interesting
        precooked_scores = {
            "A": ("2-1", "1-1", "2-0", "1-1"), # Mex-RSA: 2-1, Kor-Cze: 1-1, Mex-Kor: 2-0, RSA-Cze: 1-1
            "B": ("1-1", "1-2", "6-0", "0-2"), # Can-Bos: 1-1, Qat-Sui: 1-2, Can-Qat: 6-0, Bos-Sui: 0-2
            "C": ("3-1", "1-2", "2-0", "1-1"), # Bra-Mar: 3-1, Hai-Sco: 1-2, Bra-Hai: 2-0, Mar-Sco: 1-1
            "D": ("2-1", "1-2", "3-1", "0-2"), # USA-Par: 2-1, Aus-Tur: 1-2, USA-Aus: 3-1, Par-Tur: 0-2
            "E": ("2-0", "1-2", "1-1", "1-3"), # Ger-Cur: 2-0, Civ-Ecu: 1-2, Ger-Civ: 1-1, Cur-Ecu: 1-3
            "F": ("2-1", "2-0", "3-1", "1-1"), # Ned-Jap: 2-1, Ukr-Tun: 2-0, Ned-Ukr: 3-1, Jap-Tun: 1-1
            "G": ("1-0", "0-0", "2-1", "1-1"), # Bel-Egy: 1-0, Ira-NZL: 0-0, Bel-Ira: 2-1, Egy-NZL: 1-1
            "H": ("2-0", "1-3", "2-1", "0-2"), # Esp-CPV: 2-0, Sau-Uru: 1-3, Esp-Sau: 2-1, CPV-Uru: 0-2
            "I": ("3-0", "1-2", "2-1", "1-1"), # Fra-Sen: 3-0, Bol-Nor: 1-2, Fra-Bol: 2-1, Sen-Nor: 1-1
            "J": ("2-0", "1-1", "3-1", "1-2"), # Arg-Alg: 2-0, Aut-Jor: 1-1, Arg-Aut: 3-1, Alg-Jor: 1-2
            "K": ("1-0", "1-2", "2-0", "1-1"), # Por-Jam: 1-0, Uzb-Col: 1-2, Por-Uzb: 2-0, Jam-Col: 1-1
            "L": ("2-1", "1-1", "2-0", "1-2"), # Eng-Cro: 2-1, Gha-Pan: 1-1, Eng-Gha: 2-0, Cro-Pan: 1-2
        }

        for letter, teams_list in draw.items():
            g_dates = dates[letter]
            scores = precooked_scores[letter]
            
            # Setup teams structures
            g_teams = []
            for name in teams_list:
                g_teams.append({
                    "name": name,
                    "flag": flags.get(name, "🏳️"),
                    "pj": 0, "v": 0, "e": 0, "d": 0,
                    "gf": 0, "gc": 0, "dg": 0, "pts": 0
                })
                
            # Setup matches structures
            t0, t1, t2, t3 = teams_list
            g_matches = [
                # J1
                {"home": t0, "away": t1, "hflag": flags[t0], "aflag": flags[t1], "score": scores[0], "date": g_dates[0], "status": "FT"},
                {"home": t2, "away": t3, "hflag": flags[t2], "aflag": flags[t3], "score": scores[1], "date": g_dates[0], "status": "FT"},
                # J2
                {"home": t0, "away": t2, "hflag": flags[t0], "aflag": flags[t2], "score": scores[2], "date": g_dates[1], "status": "FT"},
                {"home": t1, "away": t3, "hflag": flags[t1], "aflag": flags[t3], "score": scores[3], "date": g_dates[1], "status": "FT"},
                # J3 (PR)
                {"home": t3, "away": t0, "hflag": flags[t3], "aflag": flags[t0], "score": "-", "date": g_dates[2], "status": "PR"},
                {"home": t1, "away": t2, "hflag": flags[t1], "aflag": flags[t2], "score": "-", "date": g_dates[2], "status": "PR"},
            ]
            
            # Calculate standings for J1 & J2
            for m in g_matches:
                if m["status"] == "FT":
                    h_goals, a_goals = map(int, m["score"].split("-"))
                    home_team = next(t for t in g_teams if t["name"] == m["home"])
                    away_team = next(t for t in g_teams if t["name"] == m["away"])
                    
                    home_team["pj"] += 1
                    away_team["pj"] += 1
                    home_team["gf"] += h_goals
                    home_team["gc"] += a_goals
                    away_team["gf"] += a_goals
                    away_team["gc"] += h_goals
                    
                    if h_goals > a_goals:
                        home_team["v"] += 1
                        home_team["pts"] += 3
                        away_team["d"] += 1
                    elif a_goals > h_goals:
                        away_team["v"] += 1
                        away_team["pts"] += 3
                        home_team["d"] += 1
                    else:
                        home_team["e"] += 1
                        home_team["pts"] += 1
                        away_team["e"] += 1
                        away_team["pts"] += 1
            
            for t in g_teams:
                t["dg"] = t["gf"] - t["gc"]
                
            # Sort: Pts -> DG -> GF
            g_teams.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
            
            groups[letter] = {
                "teams": g_teams,
                "matches": g_matches
            }
            
        return groups
        return groups

    def get_standings(self, league="PD"):
        data = self._get_complete_table_data()
        teams = data.get(league, data["PD"])
        base_pts = 60
        result = []
        for i, t in enumerate(teams):
            won = max(0, (base_pts - i*2) // 3)
            draw = max(0, (base_pts - i*2) % 3)
            lost = max(0, 24 - won - draw)
            result.append({
                "position": i+1,
                "team": {"name": t, "crest": self.get_crest(t)},
                "playedGames": 24,
                "won": won, "draw": draw, "lost": lost,
                "points": max(5, base_pts - i*2),
                "goalsFor": max(10, 50-i),
                "goalsAgainst": max(8, 20+i),
                "goalDifference": max(-20, 30-i*2)
            })
        return result

    def get_fixtures(self, league="PD"):
        data = self._get_complete_table_data()
        teams = data.get(league, data["PD"])
        fixtures = []
        today = datetime.now()
        for i in range(0, min(12, len(teams)-1), 2):
            home_t = teams[i]
            away_t = teams[i+1]
            fixtures.append({
                "homeTeam": {"name": home_t, "id": self.master_teams.get(home_t, random.randint(1000, 9999))},
                "awayTeam": {"name": away_t, "id": self.master_teams.get(away_t, random.randint(1000, 9999))},
                "utcDate": (today + timedelta(days=random.randint(1, 7))).isoformat() + "Z"
            })
        return fixtures

    def get_team_stats(self, team_name):
        info = self.team_database.get(team_name, {
            "stadium": f"Estadio de {team_name}",
            "coach": "Entrenador Pro",
            "country": "Internacional",
            "capacity": f"{random.randint(20, 80)},000"
        })
        if "capacity" not in info:
            info["capacity"] = f"{random.randint(20, 80)},000"
        rating = round(random.uniform(6.5, 7.8), 2)
        form = [random.choice(["W","D","L"]) for _ in range(5)]
        return {
            "name": team_name,
            "crest": self.get_crest(team_name),
            "sofa_rating": rating,
            "form": form,
            "summary": {
                "goals_scored": random.randint(30,60),
                "clean_sheets": random.randint(5,15),
                "avg_possession": f"{random.randint(45,62)}%",
                "avg_sofacore_rating": rating,
                "yellow_cards": random.randint(30,60),
                "yellow_cards_per_game": round(random.uniform(1.2,3.2),1)
            },
            "attack": {
                "goals_per_game": round(random.uniform(1.0,2.5),1),
                "total_shots": random.randint(10,16),
                "shots_on_target": round(random.uniform(3.0,7.0),1),
                "big_chances_created": random.randint(1,5),
                "key_passes": random.randint(8,14),
                "corners": round(random.uniform(4.0,8.0),1)
            },
            "defense": {
                "goals_conceded": round(random.uniform(0.5,1.5),1),
                "tackles": random.randint(12,18),
                "interceptions": random.randint(7,12),
                "clearances": random.randint(10,20),
                "duels_won": f"{random.randint(48,58)}%"
            },
            "matches": {
                "results": [
                    {"competition": "Champions League", "date": "18/02/26", "time": "21:00", "home": "Bayern Munich", "away": team_name, "score": "1-1", "result": "D"},
                    {"competition": "Liga", "date": "14/02/26", "time": "21:00", "home": team_name, "away": "Athletic Club", "score": "2-1", "result": "W"},
                    {"competition": "Copa", "date": "11/02/26", "time": "19:00", "home": "Atlético de Madrid", "away": team_name, "score": "0-1", "result": "W"},
                    {"competition": "Champions League", "date": "04/02/26", "time": "21:00", "home": team_name, "away": "AC Milan", "score": "3-1", "result": "W"},
                    {"competition": "Liga", "date": "01/02/26", "time": "21:00", "home": "FC Barcelona", "away": team_name, "score": "2-2", "result": "D"},
                ],
                "fixtures": [
                    {"competition": "Champions League", "date": "04/03/26", "time": "21:00", "home": team_name, "away": "Bayern Munich", "score": "-"},
                    {"competition": "Liga", "date": "22/02/26", "time": "21:00", "home": "Rival D", "away": team_name, "score": "-"}
                ]
            },
            "top_players": [
                {"name": f"Estrella 1 de {team_name}", "rating": round(rating+0.5,2), "goals": random.randint(5,15), "image": "https://api.sofascore.app/api/v1/player/895311/image"},
                {"name": f"Estrella 2 de {team_name}", "rating": round(rating+0.3,2), "goals": random.randint(2,10), "image": "https://api.sofascore.app/api/v1/player/981504/image"}
            ],
            "info": info,
            "squad": [
                {"name": f"Portero {team_name}", "pos": "G", "no": 1, "age": 28, "value": "€10M"},
                {"name": f"Defensa {team_name}", "pos": "D", "no": 4, "age": 25, "value": "€30M"},
                {"name": f"Medio {team_name}",   "pos": "M", "no": 10, "age": 23, "value": "€50M"},
                {"name": f"Delantero {team_name}","pos": "F", "no": 7, "age": 24, "value": "€80M"}
            ],
            "transfers": [
                {"player": "Fichaje Invierno", "from": "Club Origen", "type": "Comprado", "fee": "€20M", "date": "Ene 2026"},
                {"player": "Venta Verano", "from": "Club Destino", "type": "Vendido", "fee": "€40M", "date": "Ago 2025"}
            ]
        }

    def get_teams_by_league(self, league):
        if league == "WORLD_CUP_2026":
            wc_data = self.get_worldcup_data()
            teams = []
            for g_name, g_data in wc_data.items():
                for t in g_data["teams"]:
                    teams.append(t["name"])
            return sorted(list(set(teams)))
        else:
            data = self._get_complete_table_data()
            return data.get(league, [])

    def get_match_data_for_ai(self, h, v):
        return {"match": f"{h} vs {v}"}

    def get_apisports_stats(self, date="2026-06-22", match_query=None):
        if not self.apisports_key or "your_apisports" in self.apisports_key:
            return {"error": "API Key de API-Sports no configurada"}
        try:
            url = f"{self.apisports_url}/fixtures"
            params = {"date": date}
            response = requests.get(url, headers=self.apisports_headers, params=params)
            data = response.json()
            if not data.get("response"):
                return {"error": f"No se encontraron partidos para la fecha {date}"}
            fixture_id = None
            if match_query:
                for res in data["response"]:
                    home = res["teams"]["home"]["name"].lower()
                    away = res["teams"]["away"]["name"].lower()
                    if match_query.lower() in home or match_query.lower() in away:
                        fixture_id = res["fixture"]["id"]
                        break
            if not fixture_id:
                fixture_id = data["response"][0]["fixture"]["id"]
            stats_url = f"{self.apisports_url}/fixtures/statistics?fixture={fixture_id}"
            stats_response = requests.get(stats_url, headers=self.apisports_headers).json()
            return stats_response
        except Exception as e:
            return {"error": str(e)}
