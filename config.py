import streamlit as st

try:
    api_key = st.secrets.get("API_KEY", "")
    odds_api_key = st.secrets.get("ODDS_API_KEY", "")
except Exception:
    api_key = ""
    odds_api_key = ""

BASE_URL_CSV = "https://www.football-data.co.uk/mmz4281"
BASE_URL_API = "https://api.football-data.org/v4"

# Formato: "Nome Visualizzato": ("Codice CSV", "Codice API", "Chiave The-Odds-API", "URL FBRef")
LEAGUES_CONFIG = {
    "Champions League": (None, "CL", "soccer_uefa_champs_league", "https://fbref.com/en/comps/8/Champions-League-Stats"),
    "Europa League": (None, "EL", "soccer_uefa_europa_league", "https://fbref.com/en/comps/19/Europa-League-Stats"),
    "Conference League": (None, "ECL", "soccer_uefa_europa_conference_league", "https://fbref.com/en/comps/882/Conference-League-Stats"),
    "Serie A (Italia)": ("I1", "SA", "soccer_italy_serie_a", None),
    "Premier League (Inghilterra)": ("E0", "PL", "soccer_epl", None),
    "La Liga (Spagna)": ("SP1", "PD", "soccer_spain_la_liga", None),
    "Bundesliga (Germania)": ("D1", "BL1", "soccer_germany_bundesliga", None),
    "Ligue 1 (Francia)": ("F1", "FL1", "soccer_france_ligue_one", None),
    "Eredivisie (Olanda)": ("N1", "DED", "soccer_netherlands_eredivisie", None),
    "Primeira Liga (Portogallo)": ("P1", "PPL", "soccer_portugal_primeira_liga", None),
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

FBREF_TRANSLATOR = {
    # ITALIA
    "FC Internazionale Milano": "Inter", "Internazionale Milano": "Inter",
    "AC Milan": "Milan", "Juventus FC": "Juventus", "Atalanta BC": "Atalanta",
    "Bologna FC 1909": "Bologna", "SSC Napoli": "Napoli",
    "AS Roma": "Roma", "SS Lazio": "Lazio", "ACF Fiorentina": "Fiorentina",

    # INGHILTERRA
    "Arsenal FC": "Arsenal", "Manchester City FC": "Manchester City",
    "Liverpool FC": "Liverpool", "Aston Villa FC": "Aston Villa",
    "Manchester United FC": "Manchester Utd", "Newcastle United FC": "Newcastle Utd",
    "Tottenham Hotspur FC": "Tottenham", "Chelsea FC": "Chelsea",
    "West Ham United FC": "West Ham", "Brighton & Hove Albion FC": "Brighton",

    # SPAGNA
    "Real Madrid CF": "Real Madrid", "FC Barcelona": "Barcelona",
    "Club Atlético de Madrid": "Atlético Madrid", "Girona FC": "Girona",
    "Athletic Club": "Athletic Club", "Real Sociedad de Fútbol": "Real Sociedad",
    "Real Betis Balompié": "Betis", "Villarreal CF": "Villarreal", "Sevilla FC": "Sevilla",

    # GERMANIA
    "FC Bayern München": "Bayern Munich", "Bayer 04 Leverkusen": "Leverkusen",
    "Borussia Dortmund": "Dortmund", "RB Leipzig": "RB Leipzig",
    "VfB Stuttgart": "Stuttgart", "Eintracht Frankfurt": "Eintracht Frankfurt",
    "TSG 1899 Hoffenheim": "Hoffenheim", "1. FC Heidenheim 1846": "Heidenheim",
    "SC Freiburg": "Freiburg",

    # FRANCIA
    "Paris Saint-Germain FC": "Paris S-G", "AS Monaco FC": "Monaco",
    "LOSC Lille": "Lille", "Stade Brestois 29": "Brest",
    "Olympique de Marseille": "Marseille", "Olympique Lyonnais": "Lyon",
    "OGC Nice": "Nice", "RC Lens": "Lens",

    # PORTOGALLO & OLANDA & BELGIO
    "Sporting Clube de Portugal": "Sporting CP", "Sport Lisboa e Benfica": "Benfica",
    "SL Benfica": "Benfica", "FC Porto": "Porto",
    "Sporting Clube de Braga": "Braga", "Vitória SC": "Vitória Guimarães",
    "PSV": "PSV Eindhoven", "PSV Eindhoven": "PSV Eindhoven",
    "Feyenoord Rotterdam": "Feyenoord", "AFC Ajax": "Ajax",
    "AZ": "AZ Alkmaar", "AZ Alkmaar": "AZ Alkmaar", "FC Twente '65": "Twente",
    "Club Brugge KV": "Club Brugge", "RSC Anderlecht": "Anderlecht",
    "Royale Union Saint-Gilloise": "Union SG", "KAA Gent": "Gent",

    # RESTO D'EUROPA (UCL / UEL / UECL)
    "Celtic FC": "Celtic", "Rangers FC": "Rangers",
    "FC Red Bull Salzburg": "RB Salzburg", "SK Sturm Graz": "Sturm Graz",
    "SK Rapid Wien": "Rapid Wien", "LASK": "LASK",
    "BSC Young Boys": "Young Boys", "FC Lugano": "Lugano", "FC Basel 1893": "Basel",
    "AC Sparta Praha": "Sparta Prague", "SK Slavia Praha": "Slavia Prague",
    "FC Viktoria Plzeň": "Viktoria Plzeň", "FK Mladá Boleslav": "Mladá Boleslav",
    "GNK Dinamo Zagreb": "Dinamo Zagreb", "HNK Rijeka": "Rijeka",
    "FK Crvena Zvezda": "Red Star", "FK TSC Bačka Topola": "TSC Bačka Topola",
    "FC Shakhtar Donetsk": "Shakhtar", "FC Dynamo Kyiv": "Dynamo Kyiv",
    "ŠK Slovan Bratislava": "Slovan Bratislava",
    "Galatasaray SK": "Galatasaray", "Fenerbahçe SK": "Fenerbahçe",
    "Beşiktaş JK": "Beşiktaş", "İstanbul Başakşehir FK": "Başakşehir",
    "Olympiacos CFP": "Olympiacos", "PAOK FC": "PAOK", "Panathinaikos FC": "Panathinaikos",
    "FK Bodø/Glimt": "Bodø/Glimt", "Molde FK": "Molde",
    "Malmö FF": "Malmö", "IF Elfsborg": "Elfsborg", "Djurgårdens IF": "Djurgården",
    "FC København": "FC Copenhagen", "FC Midtjylland": "Midtjylland",
    "Ferencvárosi TC": "Ferencváros", "Qarabağ FK": "Qarabağ",
    "Legia Warszawa": "Legia Warsaw", "Jagiellonia Białystok": "Jagiellonia",
    "APOEL FC": "APOEL", "AC Omonia": "Omonia", "Pafos FC": "Pafos",
    "Maccabi Tel Aviv FC": "Maccabi Tel Aviv", "PFC Ludogorets 1945": "Ludogorets",
}
ALL_NATIONAL_CSV_CODES = ["I1", "E0", "SP1", "D1", "F1", "N1", "P1"]
