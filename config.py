import streamlit as st

try:
    api_key = st.secrets.get("API_KEY", "")
    odds_api_key = st.secrets.get("ODDS_API_KEY", "")
except Exception:
    api_key = ""
    odds_api_key = ""

BASE_URL_CSV = "https://www.football-data.co.uk/mmz4281"
BASE_URL_API = "https://api.football-data.org/v4"

# Formato: "Nome Visualizzato": ("Codice CSV", "Codice API", "Chiave The-Odds-API")
LEAGUES_CONFIG = {
    "Champions League": (None, "CL", "soccer_uefa_champs_league"),
    "Serie A (Italia)": ("I1", "SA", "soccer_italy_serie_a"),
    "Premier League (Inghilterra)": ("E0", "PL", "soccer_epl"),
    "La Liga (Spagna)": ("SP1", "PD", "soccer_spain_la_liga"),
    "Bundesliga (Germania)": ("D1", "BL1", "soccer_germany_bundesliga"),
    "Ligue 1 (Francia)": ("F1", "FL1", "soccer_france_ligue_one"),
    "Eredivisie (Olanda)": ("N1", "DED", "soccer_netherlands_eredivisie"),
    "Primeira Liga (Portogallo)": ("P1", "PPL", "soccer_portugal_primeira_liga"),
}

TEAM_TRANSLATOR = {
    # OLANDA
    "Telstar 1963": "Telstar", "PSV": "PSV Eindhoven", "NEC": "Nijmegen", "NAC Breda": "NAC",
    "ADO Den Haag": "Den Haag", "SBV Excelsior": "Excelsior", "Sparta Rotterdam": "Sparta Rott",
    "Fortuna Sittard": "For Sittard", "Go Ahead Eagles": "Go Ahead Eagles", "PEC Zwolle": "Zwolle",
    "FC Volendam": "Volendam", "Almere City FC": "Almere City", "AZ": "AZ Alkmaar",
    "Feyenoord Rotterdam": "Feyenoord", "AFC Ajax": "Ajax", "FC Utrecht": "Utrecht", "FC Twente '65": "Twente",

    # ITALIA
    "Internazionale Milano": "Inter", "FC Internazionale Milano": "Inter", "AC Milan": "Milan",
    "AS Roma": "Roma", "SS Lazio": "Lazio", "Hellas Verona FC": "Verona", "Udinese Calcio": "Udinese",
    "Torino FC": "Torino", "Bologna FC 1909": "Bologna", "Empoli FC": "Empoli",
    "ACF Fiorentina": "Fiorentina", "Genoa CFC": "Genoa", "Juventus FC": "Juventus",
    "SSC Napoli": "Napoli", "Cagliari Calcio": "Cagliari", "US Lecce": "Lecce",
    "AC Monza": "Monza", "Atalanta BC": "Atalanta", "Parma Calcio 1913": "Parma",
    "Como 1907": "Como", "Venezia FC": "Venezia",

    # GERMANIA
    "Bayer 04 Leverkusen": "Leverkusen", "Borussia Dortmund": "Dortmund",
    "Borussia Mönchengladbach": "M'gladbach", "Eintracht Frankfurt": "Ein Frankfurt",
    "VfL Wolfsburg": "Wolfsburg", "1. FC Union Berlin": "Union Berlin", "VfB Stuttgart": "Stuttgart",
    "RB Leipzig": "RB Leipzig", "TSG 1899 Hoffenheim": "Hoffenheim", "1. FSV Mainz 05": "Mainz",
    "SV Darmstadt 98": "Darmstadt", "VfL Bochum 1848": "Bochum", "FC Bayern München": "Bayern Munich",
    "FC St. Pauli": "St Pauli", "Holstein Kiel": "Holstein Kiel",

    # SPAGNA
    "Athletic Club": "Ath Bilbao", "Club Atlético de Madrid": "Ath Madrid",
    "RCD Espanyol de Barcelona": "Espanyol", "Deportivo Alavés": "Alaves",
    "Real Betis Balompié": "Betis", "Real Sociedad de Fútbol": "Sociedad",
    "Real Madrid CF": "Real Madrid", "FC Barcelona": "Barcelona", "Sevilla FC": "Sevilla",
    "Villarreal CF": "Villarreal", "Valencia CF": "Valencia", "Girona FC": "Girona",

    # PORTOGALLO
    "Vitória SC": "Guimaraes", "Sporting Clube de Portugal": "Sp Lisbon",
    "Sporting Clube de Braga": "Sp Braga", "SL Benfica": "Benfica", "FC Porto": "Porto",
    "Sport Lisboa e Benfica": "Benfica",

    # FRANCIA
    "Stade Rennais FC 1901": "Rennais", "Paris Saint-Germain FC": "Paris SG",
    "Olympique de Marseille": "Marseille", "AS Monaco FC": "Monaco",
    "Olympique Lyonnais": "Lyon", "LOSC Lille": "Lille", "OGC Nice": "Nice",

    # INGHILTERRA
    "Wolverhampton Wanderers FC": "Wolves", "Manchester United FC": "Man United",
    "Manchester City FC": "Man City", "Tottenham Hotspur FC": "Tottenham",
    "West Ham United FC": "West Ham", "Newcastle United FC": "Newcastle",
    "Nottingham Forest FC": "Nott'm Forest", "Chelsea FC": "Chelsea", "Fulham FC": "Fulham",
    "Brentford FC": "Brentford", "Crystal Palace FC": "Crystal Palace", "Everton FC": "Everton",
    "Arsenal FC": "Arsenal", "Aston Villa FC": "Aston Villa", "Liverpool FC": "Liverpool",
    "Brighton & Hove Albion FC": "Brighton", "AFC Bournemouth": "Bournemouth",
}

# Mapping specifico per i nomi su FBRef (Champions League)
FBREF_TRANSLATOR = {
    "FC Internazionale Milano": "Inter",
    "Internazionale Milano": "Inter",
    "Paris Saint-Germain FC": "Paris S-G",
    "Club Atlético de Madrid": "Atlético Madrid",
    "Sporting Clube de Portugal": "Sporting CP",
    "Sport Lisboa e Benfica": "Benfica",
    "FC Bayern München": "Bayern Munich",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Manchester United FC": "Manchester Utd",
    "Manchester City FC": "Manchester City",
    "Newcastle United FC": "Newcastle Utd",
    "Tottenham Hotspur FC": "Tottenham",
    "Borussia Dortmund": "Dortmund",
    "Real Madrid CF": "Real Madrid",
    "FC Barcelona": "Barcelona",
    "PSV": "PSV Eindhoven",
    "Feyenoord Rotterdam": "Feyenoord",
}
