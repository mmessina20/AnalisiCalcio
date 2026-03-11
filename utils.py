# utils.py
import requests
import pandas as pd
import io
import difflib
import re
import pytz
from datetime import datetime, timezone
import streamlit as st
import config  # Importa le configurazioni dal file config.py

def normalize_name(name):
    """Pulisce i nomi delle squadre per facilitare il confronto."""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'\b(19|20)\d{2}\b', '', name) 
    name = re.sub(r'\b\d{2}\b', '', name) 
    for garbage in ["fc", "ac", "as", "sc", "us", "cd", "cf", "vfl", "fsv", "tsg", "rb", "sv", "sbv", "pec", "rkc", "mvv", "jc", "sl", "acf", "ssc", "rcd"]:
        name = name.replace(garbage, "")
    name = re.sub(r'[^a-z]', '', name)
    return name

def match_team_name(api_name, csv_teams_list):
    """Trova la corrispondenza tra il nome API e il nome nel CSV."""
    if api_name in config.TEAM_TRANSLATOR:
        candidate = config.TEAM_TRANSLATOR[api_name]
        matches_dict = difflib.get_close_matches(candidate, csv_teams_list, n=1, cutoff=0.6)
        if matches_dict: return matches_dict[0]

    api_clean = normalize_name(api_name)
    best_match = None
    best_score = 0.0
    
    for csv_team in csv_teams_list:
        csv_clean = normalize_name(csv_team)
        if api_clean == csv_clean: return csv_team
        if (len(api_clean) > 2 and len(csv_clean) > 2) and (api_clean in csv_clean or csv_clean in api_clean):
            return csv_team
        score = difflib.SequenceMatcher(None, api_clean, csv_clean).ratio()
        if score > best_score:
            best_score = score
            best_match = csv_team
            
    if best_score > 0.55: return best_match
    return None

def converti_orario_ita(data_utc_str):
    """Converte l'orario UTC in orario Italiano."""
    utc_dt = datetime.strptime(data_utc_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(pytz.timezone('Europe/Rome'))

@st.cache_data(ttl=3600)
def get_next_matchday_fixtures(api_league_code):
    """Scarica il calendario dal provider API."""
    headers = {'X-Auth-Token': config.api_key}
    url = f"{config.BASE_URL_API}/competitions/{api_league_code}/matches?status=SCHEDULED"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        matches = data.get('matches', [])
        if not matches: return [], None

        now_utc = datetime.now(timezone.utc)
        future_matches = [m for m in matches if datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > now_utc]
        
        if not future_matches: return [], None
        
        # Logica speciale per ordinare le partite (utile per Champions e coppe)
        future_matches.sort(key=lambda x: x['utcDate'])
        next_matchday_num = future_matches[0]['matchday']
        fixtures_raw = [m for m in future_matches if m['matchday'] == next_matchday_num]
        
        # Limite visualizzazione se ci sono troppe partite
        if len(fixtures_raw) > 20: 
            fixtures_raw = fixtures_raw[:20]

        fixtures_clean = []
        for m in fixtures_raw:
            dt_ita = converti_orario_ita(m['utcDate'])
            fixtures_clean.append({
                'Data': dt_ita.strftime("%d/%m"),
                'Ora': dt_ita.strftime("%H:%M"),
                'Casa': m['homeTeam']['name'],
                'Ospite': m['awayTeam']['name'],
                'Display': f"📅  {dt_ita.strftime('%d/%m %H:%M')}  |  🏠  **{m['homeTeam']['name']}**   vs   ✈️  **{m['awayTeam']['name']}**"
            })
        return fixtures_clean, next_matchday_num
    except Exception as e:
        print(f"Errore API: {e}")
        return [], None

@st.cache_data(ttl=3600)
def scarica_dati_csv(codice_lega, stagioni):
    """Scarica i dati storici statistici (CSV)."""
    if codice_lega is None:
        return None
        
    lista_df = []
    for stag in stagioni:
        url = f"{config.BASE_URL_CSV}/{stag}/{codice_lega}.csv"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            df_temp = pd.read_csv(io.StringIO(r.text))
            df_temp['Stagione'] = stag 
            lista_df.append(df_temp)
        except Exception:
            continue
    if not lista_df: return None
    df_finale = pd.concat(lista_df, ignore_index=True)
    df_finale['Date'] = pd.to_datetime(df_finale['Date'], dayfirst=True, errors='coerce')
    return df_finale.sort_values(by='Date', ascending=False)

def elabora_statistiche(df, squadra):
    """Calcola le medie statistiche per casa/fuori/overall."""
    if df is None: return None
    if squadra not in df['HomeTeam'].unique() and squadra not in df['AwayTeam'].unique(): return None
    cols = ['GF', 'GS', 'Tiri_Fatti', 'Tiri_Subiti', 'Porta_Fatti', 'Porta_Subiti', 'Corner_Fatti', 'Corner_Subiti', 'Gialli']
    
    # Casa
    df_home = df[df['HomeTeam'] == squadra].copy()
    df_home_norm = df_home.rename(columns={'FTHG': 'GF', 'FTAG': 'GS', 'HS': 'Tiri_Fatti', 'AS': 'Tiri_Subiti', 'HST': 'Porta_Fatti', 'AST': 'Porta_Subiti', 'HC': 'Corner_Fatti', 'AC': 'Corner_Subiti', 'HY': 'Gialli'})

    # Fuori
    df_away = df[df['AwayTeam'] == squadra].copy()
    df_away_norm = df_away.rename(columns={'FTAG': 'GF', 'FTHG': 'GS', 'AS': 'Tiri_Fatti', 'HS': 'Tiri_Subiti', 'AST': 'Porta_Fatti', 'HST': 'Porta_Subiti', 'AC': 'Corner_Fatti', 'HC': 'Corner_Subiti', 'AY': 'Gialli'})

    for c in cols:
        if c not in df_home_norm.columns: df_home_norm[c] = 0
        if c not in df_away_norm.columns: df_away_norm[c] = 0
        df_home_norm[c] = pd.to_numeric(df_home_norm[c], errors='coerce').fillna(0)
        df_away_norm[c] = pd.to_numeric(df_away_norm[c], errors='coerce').fillna(0)

    df_general = pd.concat([df_home_norm[cols], df_away_norm[cols]])

    def get_means(dataset):
        if dataset.empty: return {k: 0.0 for k in cols}
        return dataset[cols].mean(numeric_only=True).to_dict()

    return {'overall': get_means(df_general), 'home': get_means(df_home_norm), 'away': get_means(df_away_norm)}

def crea_dataframe_confronto(metrics_list, home_stats, away_stats, team_home, team_away):
    """Crea la tabella comparativa per Streamlit."""
    data = {
        "Metrica": metrics_list,
        f"{team_home} (Gen)": [f"{home_stats['overall'][m]:.2f}" for m in metrics_list],
        f"{team_home} (CASA)": [f"{home_stats['home'][m]:.2f}" for m in metrics_list], 
        f"{team_away} (FUORI)": [f"{away_stats['away'][m]:.2f}" for m in metrics_list], 
        f"{team_away} (Gen)": [f"{away_stats['overall'][m]:.2f}" for m in metrics_list],
    }
    return pd.DataFrame(data).set_index("Metrica")