import streamlit as st
# config.py

api_key = st.secrets["API_KEY"]

BASE_URL_CSV = "https://www.football-data.co.uk/mmz4281"
BASE_URL_API = "https://api.football-data.org/v4"

# Formato: "Nome Visualizzato": ("Codice CSV", "Codice API")
LEAGUES_CONFIG = {
    "Serie A (Italia)": ("I1", "SA"),
    "Premier League (Inghilterra)": ("E0", "PL"),
    "La Liga (Spagna)": ("SP1", "PD"),
    "Bundesliga (Germania)": ("D1", "BL1"),
    "Ligue 1 (Francia)": ("F1", "FL1"),
    "Eredivisie (Olanda)": ("N1", "DED"),
    "Primeira Liga (Portogallo)": ("P1", "PPL"),
}

TEAM_TRANSLATOR = {
    # OLANDA
    "Telstar 1963": "Telstar", "PSV": "PSV Eindhoven", "NEC": "Nijmegen", "NAC Breda": "NAC",
    "ADO Den Haag": "Den Haag", "SBV Excelsior": "Excelsior", "Sparta Rotterdam": "Sparta Rott",
    "Fortuna Sittard": "For Sittard", "Go Ahead Eagles": "Go Ahead Eagles", "PEC Zwolle": "Zwolle",
    "FC Volendam": "Volendam", "Almere City FC": "Almere City",
    
    # ITALIA
    "Internazionale Milano": "Inter", "AC Milan": "Milan", "AS Roma": "Roma", "SS Lazio": "Lazio",
    "Hellas Verona FC": "Verona", "Udinese Calcio": "Udinese", "Torino FC": "Torino",
    "Bologna FC 1909": "Bologna", "Empoli FC": "Empoli", "ACF Fiorentina": "Fiorentina",
    "Genoa CFC": "Genoa", "Juventus FC": "Juventus", "SSC Napoli": "Napoli",
    "Cagliari Calcio": "Cagliari", "US Lecce": "Lecce", "AC Monza": "Monza", "Atalanta BC": "Atalanta",
    "Parma Calcio 1913": "Parma", "Como 1907": "Como", "Venezia FC": "Venezia",
    
    # GERMANIA
    "Bayer 04 Leverkusen": "Leverkusen", "Borussia Dortmund": "Dortmund", "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt", "VfL Wolfsburg": "Wolfsburg", "1. FC Union Berlin": "Union Berlin",
    "VfB Stuttgart": "Stuttgart", "RB Leipzig": "RB Leipzig", "TSG 1899 Hoffenheim": "Hoffenheim",
    "1. FSV Mainz 05": "Mainz", "SV Darmstadt 98": "Darmstadt", "VfL Bochum 1848": "Bochum",
    "FC Bayern München": "Bayern Munich", "FC St. Pauli": "St Pauli", "Holstein Kiel": "Holstein Kiel",
    
    # SPAGNA
    "Athletic Club": "Ath Bilbao", "Club Atlético de Madrid": "Ath Madrid", "RCD Espanyol de Barcelona": "Espanyol",
    "Deportivo Alavés": "Alaves", "Real Betis Balompié": "Betis", "Real Sociedad de Fútbol": "Sociedad",
    "Real Madrid CF": "Real Madrid", "FC Barcelona": "Barcelona", "Sevilla FC": "Sevilla",
    
    # PORTOGALLO
    "Vitória SC": "Guimaraes", "Sporting Clube de Portugal": "Sp Lisbon", "Sporting Clube de Braga": "Sp Braga",
    "SL Benfica": "Benfica", "FC Porto": "Porto",
    
    # FRANCIA
    "Stade Rennais FC 1901": "Rennais", "Paris Saint-Germain FC": "Paris SG", "Olympique de Marseille": "Marseille",
    "AS Monaco FC": "Monaco", "Olympique Lyonnais": "Lyon", "LOSC Lille": "Lille",
    
    # INGHILTERRA
    "Wolverhampton Wanderers FC": "Wolves", "Manchester United FC": "Man United", "Manchester City FC": "Man City",
    "Tottenham Hotspur FC": "Tottenham", "West Ham United FC": "West Ham", "Newcastle United FC": "Newcastle",
    "Nottingham Forest FC": "Nott'm Forest", "Chelsea FC": "Chelsea", "Fulham FC": "Fulham",
    "Brentford FC": "Brentford", "Crystal Palace FC": "Crystal Palace", "Everton FC": "Everton",
}