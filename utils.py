import io
import re
import difflib
from datetime import datetime, timezone
import pytz
import requests
import cloudscraper
from bs4 import BeautifulSoup, Comment
import pandas as pd
import numpy as np
from scipy.stats import poisson
import streamlit as st
import plotly.graph_objects as go
import config


def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z]', '', name)
    return name


def match_team_name(api_name, csv_teams_list):
    if csv_teams_list is None or len(csv_teams_list) == 0:
        return None
    if api_name in config.TEAM_TRANSLATOR:
        candidate = config.TEAM_TRANSLATOR[api_name]
        if candidate in csv_teams_list:
            return candidate
    api_clean = normalize_name(api_name)
    best_match, best_score = None, 0.0
    for csv_team in csv_teams_list:
        csv_clean = normalize_name(csv_team)
        score = difflib.SequenceMatcher(None, api_clean, csv_clean).ratio()
        if score > best_score:
            best_score = score
            best_match = csv_team
    return best_match if best_score > 0.55 else None


def match_team_ucl(api_name, fbref_df):
    if fbref_df is None or fbref_df.empty:
        return None
    squad_col = fbref_df.columns[0]
    squadre_db = fbref_df[squad_col].astype(str).tolist()
    nome_target = config.FBREF_TRANSLATOR.get(api_name, config.TEAM_TRANSLATOR.get(api_name, api_name))

    if nome_target in squadre_db:
        return fbref_df[fbref_df[squad_col] == nome_target].iloc[0]

    match = difflib.get_close_matches(nome_target, squadre_db, n=1, cutoff=0.45)
    if match:
        return fbref_df[fbref_df[squad_col] == match[0]].iloc[0]
    return None


def converti_orario_ita(data_utc_str):
    utc_dt = datetime.strptime(data_utc_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(pytz.timezone('Europe/Rome'))


@st.cache_data(ttl=3600)
def get_live_odds_from_odds_api(sport_key):
    """Scarica sia le quote 1X2 (h2h) sia Over/Under 2.5 (totals) da The Odds API."""
    if not config.odds_api_key or not sport_key:
        return {}
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": config.odds_api_key,
        "regions": "eu",
        "markets": "h2h,totals",
        "oddsFormat": "decimal"
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code != 200:
            return {}
        odds_map = {}
        for event in r.json():
            home = normalize_name(event.get("home_team", ""))
            away = normalize_name(event.get("away_team", ""))
            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            q1, qx, q2 = None, None, None
            qo25, qu25 = None, None

            for bm in bookmakers:
                for mkt in bm.get("markets", []):
                    if mkt.get("key") == "h2h" and q1 is None:
                        for out in mkt.get("outcomes", []):
                            name_norm = normalize_name(out.get("name", ""))
                            price = out.get("price")
                            if name_norm == "draw":
                                qx = price
                            elif difflib.SequenceMatcher(None, name_norm, home).ratio() > 0.6:
                                q1 = price
                            elif difflib.SequenceMatcher(None, name_norm, away).ratio() > 0.6:
                                q2 = price
                    elif mkt.get("key") == "totals" and qo25 is None:
                        for out in mkt.get("outcomes", []):
                            if out.get("point") == 2.5:
                                if out.get("name") == "Over":
                                    qo25 = out.get("price")
                                elif out.get("name") == "Under":
                                    qu25 = out.get("price")
                if q1 and qx and q2 and qo25 and qu25:
                    break

            odds_map[(home, away)] = {
                'Q1': round(q1, 2) if q1 else None,
                'QX': round(qx, 2) if qx else None,
                'Q2': round(q2, 2) if q2 else None,
                'QO25': round(qo25, 2) if qo25 else None,
                'QU25': round(qu25, 2) if qu25 else None,
            }
        return odds_map
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def get_all_scheduled_fixtures(api_league_code, odds_sport_key=None):
    """Scarica le partite programmate e integra quote 1X2 e Over/Under 2.5 reali."""
    if not config.api_key:
        return {}, [], "Chiave API mancante. Configura API_KEY in .streamlit/secrets.toml o nei Secrets di Streamlit Cloud."

    headers = {'X-Auth-Token': config.api_key}
    url = f"{config.BASE_URL_API}/competitions/{api_league_code}/matches?status=SCHEDULED"
    live_odds_map = get_live_odds_from_odds_api(odds_sport_key)

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            return {}, [], "Limite chiamate API raggiunto (max 10/minuto su piano gratuito). Attendi 60 secondi e ricarica."
        if response.status_code != 200:
            return {}, [], f"Errore API football-data.org (HTTP {response.status_code}): {response.text[:150]}"

        data = response.json()
        matches = data.get('matches', [])
        if not matches:
            return {}, [], "Nessuna partita programmata trovata per questa competizione."

        future_matches = sorted(matches, key=lambda x: x['utcDate'])
        fixtures_by_day = {}
        for m in future_matches:
            day = m.get('matchday') or 1
            dt = converti_orario_ita(m['utcDate'])
            odds = m.get('odds') or {}

            q1 = odds.get('homeWin') if isinstance(odds.get('homeWin'), (int, float)) else None
            qx = odds.get('draw') if isinstance(odds.get('draw'), (int, float)) else None
            q2 = odds.get('awayWin') if isinstance(odds.get('awayWin'), (int, float)) else None
            qo25, qu25 = None, None

            if live_odds_map:
                h_norm = normalize_name(m['homeTeam']['name'])
                a_norm = normalize_name(m['awayTeam']['name'])
                for (oh, oa), o_dict in live_odds_map.items():
                    if difflib.SequenceMatcher(None, h_norm, oh).ratio() > 0.6 and difflib.SequenceMatcher(None, a_norm, oa).ratio() > 0.6:
                        q1 = q1 or o_dict.get('Q1')
                        qx = qx or o_dict.get('QX')
                        q2 = q2 or o_dict.get('Q2')
                        qo25 = o_dict.get('QO25')
                        qu25 = o_dict.get('QU25')
                        break

            fixtures_by_day.setdefault(day, []).append({
                'Data': dt.strftime("%d/%m"),
                'Ora': dt.strftime("%H:%M"),
                'Casa': m['homeTeam']['name'],
                'Ospite': m['awayTeam']['name'],
                'Logo_Casa': m['homeTeam'].get('crest', ''),
                'Logo_Ospite': m['awayTeam'].get('crest', ''),
                'Q1': f"{q1:.2f}" if q1 else 'N.D.',
                'QX': f"{qx:.2f}" if qx else 'N.D.',
                'Q2': f"{q2:.2f}" if q2 else 'N.D.',
                'QO25': f"{qo25:.2f}" if qo25 else 'N.D.',
                'QU25': f"{qu25:.2f}" if qu25 else 'N.D.',
            })
        giornate_disponibili = sorted(fixtures_by_day.keys())
        return fixtures_by_day, giornate_disponibili, None
    except Exception as e:
        return {}, [], f"Errore di connessione all'API: {str(e)}"


def valuta_value_bets(probs, q1, qx, q2, qo25=None, qu25=None):
    """Confronta le probabilità di Poisson con le quote 1X2 e Over/Under 2.5 (EV > 5%)."""
    value_list = []
    mapping = [
        ("1 (Casa)", probs['P1'], q1),
        ("X (Pareggio)", probs['PX'], qx),
        ("2 (Ospite)", probs['P2'], q2),
        ("Over 2.5 Gol", probs['Over25'], qo25),
        ("Under 2.5 Gol", probs['Under25'], qu25),
    ]
    for label, prob_pct, quota in mapping:
        try:
            q_val = float(quota)
            if q_val > 1.0:
                prob_dec = prob_pct / 100.0
                ev = (prob_dec * q_val) - 1.0
                quota_fair = 1.0 / prob_dec if prob_dec > 0 else 99.0
                if ev > 0.05:
                    value_list.append({
                        'Mercato': label,
                        'Prob_Modello': f"{prob_pct:.1f}%",
                        'Quota_Book': f"{q_val:.2f}",
                        'Quota_Fair': f"{quota_fair:.2f}",
                        'EV': f"+{ev * 100:.1f}%",
                    })
        except (ValueError, TypeError):
            continue
    return value_list


def genera_badge_partita(match, df_csv):
    """Calcola badge rapidi su Over/Under 2.5, Corner e Value Bet (1X2 + O/U 2.5)."""
    if df_csv is None or df_csv.empty:
        return []
    t_h = match_team_name(match['Casa'], df_csv['HomeTeam'].unique())
    t_a = match_team_name(match['Ospite'], df_csv['AwayTeam'].unique())
    if not t_h or not t_a:
        return []

    s_h = elabora_statistiche(df_csv, t_h, usa_forma_recente=True)
    s_a = elabora_statistiche(df_csv, t_a, usa_forma_recente=True)

    exp_gf_h = (s_h['home']['GF'] + s_a['away']['GS']) / 2
    exp_gf_a = (s_a['away']['GF'] + s_h['home']['GS']) / 2
    exp_gf = exp_gf_h + exp_gf_a
    exp_corn = ((s_h['home']['Corner_Fatti'] + s_a['away']['Corner_Subiti']) / 2) + (
        (s_a['away']['Corner_Fatti'] + s_h['home']['Corner_Subiti']) / 2
    )
    probs = calcola_probabilita_poisson(exp_gf_h, exp_gf_a)
    v_bets = valuta_value_bets(
        probs, match['Q1'], match['QX'], match['Q2'],
        match.get('QO25'), match.get('QU25')
    )

    badges = []
    if probs['Over25'] >= 60.0 or exp_gf >= 2.85:
        badges.append((f"🔥 Over 2.5 ({probs['Over25']:.0f}%)", "#ff6b35"))
    elif probs['Under25'] >= 62.0:
        badges.append((f"🛡️ Under 2.5 ({probs['Under25']:.0f}%)", "#3d5afe"))

    if exp_corn >= 10.5:
        badges.append(("🚩 Corner > 10.5", "#00c896"))

    if v_bets:
        badges.append((f"💎 Value: {v_bets[0]['Mercato']} ({v_bets[0]['EV']})", "#d97706"))

    return badges

def _estrai_tabelle_fbref(html_text):
    """Estrae sia le tabelle visibili sia quelle nascoste nei commenti HTML di FBRef."""
    soup = BeautifulSoup(html_text, "lxml")
    html_parts = [str(soup)]
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "<table" in comment:
            html_parts.append(str(comment))

    tabelle_estratte = {}
    for part in html_parts:
        try:
            tables = pd.read_html(io.StringIO(part))
            for t in tables:
                if isinstance(t.columns, pd.MultiIndex):
                    t.columns = [
                        '_'.join([str(c) for c in col if 'Unnamed' not in str(c)]).strip()
                        for col in t.columns.values
                    ]
                cols_str = " ".join([str(c) for c in t.columns])
                if "Squad" in cols_str and "MP" in cols_str:
                    squad_col = [c for c in t.columns if "Squad" in str(c)][0]
                    t = t[t[squad_col].notna() & (t[squad_col] != "Squad")].copy()
                    if "against" in t[squad_col].iloc[0].lower() or "Opponent" in cols_str:
                        tabelle_estratte["opponent"] = t
                    elif "standard" not in tabelle_estratte:
                        tabelle_estratte["standard"] = t
        except Exception:
            continue
    return tabelle_estratte


@st.cache_data(ttl=86400)
def scarica_statistiche_ucl_fbref():
    """Scarica da FBRef sia le statistiche fatte che quelle subite usando cloudscraper."""
    url = "https://fbref.com/en/comps/8/Champions-League-Stats"
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    try:
        r = scraper.get(url, timeout=20)
        if r.status_code != 200:
            return None, None, f"FBRef ha bloccato la richiesta (HTTP {r.status_code}). Riprova più tardi."
        tabelle = _estrai_tabelle_fbref(r.text)
        df_std = tabelle.get("standard")
        df_opp = tabelle.get("opponent")
        if df_std is None or df_std.empty:
            return None, None, "Tabelle UCL non trovate nella pagina FBRef."
        return df_std, df_opp, None
    except Exception as e:
        return None, None, f"Errore durante lo scraping UCL: {str(e)}"


def estrai_metriche_ucl_squadra(api_name, df_std, df_opp):
    """Combina statistiche fatte (df_std) e subite (df_opp) per una squadra UCL."""
    row_std = match_team_ucl(api_name, df_std)
    if row_std is None:
        return None

    def _find_val(row, keywords, default=0.0):
        for col in row.index:
            col_l = str(col).lower()
            if all(k.lower() in col_l for k in keywords):
                try:
                    return float(row[col])
                except (ValueError, TypeError):
                    continue
        return default

    mp = max(_find_val(row_std, ["MP"], 1.0), 1.0)
    gf = _find_val(row_std, ["Performance", "Gls"], _find_val(row_std, ["Gls"], 0.0)) / mp
    xg_f = _find_val(row_std, ["Expected", "xG"], gf * mp) / mp
    tiri_f = _find_val(row_std, ["Standard", "Sh"], _find_val(row_std, ["Sh"], 11.0 * mp)) / mp
    porta_f = _find_val(row_std, ["Standard", "SoT"], _find_val(row_std, ["SoT"], 4.0 * mp)) / mp
    gialli = _find_val(row_std, ["CrdY"], 2.0 * mp) / mp

    # Dati subiti reali dalla tabella Opponent Stats se disponibile
    row_opp = match_team_ucl(api_name, df_opp) if df_opp is not None else None
    if row_opp is not None:
        mp_opp = max(_find_val(row_opp, ["MP"], mp), 1.0)
        gs = _find_val(row_opp, ["Performance", "Gls"], _find_val(row_opp, ["Gls"], 1.2 * mp_opp)) / mp_opp
        xg_s = _find_val(row_opp, ["Expected", "xG"], gs * mp_opp) / mp_opp
        tiri_s = _find_val(row_opp, ["Standard", "Sh"], _find_val(row_opp, ["Sh"], 11.0 * mp_opp)) / mp_opp
        porta_s = _find_val(row_opp, ["Standard", "SoT"], _find_val(row_opp, ["SoT"], 4.0 * mp_opp)) / mp_opp
    else:
        gs, xg_s, tiri_s, porta_s = 1.2, 1.2, 11.0, 4.0

    # Stima proporzionale dei corner dai tiri se non presenti nella tabella base
    corner_f = round(max(2.5, tiri_f * 0.44), 2)
    corner_s = round(max(2.5, tiri_s * 0.44), 2)

    stats = {
        'GF': gf,
        'GS': gs,
        'xG_Fatti': xg_f,
        'xG_Subiti': xg_s,
        'Tiri_Fatti': tiri_f,
        'Tiri_Subiti': tiri_s,
        'Porta_Fatti': porta_f,
        'Porta_Subiti': porta_s,
        'Corner_Fatti': corner_f,
        'Corner_Subiti': corner_s,
        'Gialli': gialli,
    }
    return {'overall': stats}


@st.cache_data(ttl=3600)
def scarica_dati_csv(codice_lega, stagioni):
    dfs = []
    errori = []
    for s in stagioni:
        url = f"{config.BASE_URL_CSV}/{s}/{codice_lega}.csv"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.status_code == 200 and len(r.text) > 100:
                df_temp = pd.read_csv(io.StringIO(r.text), on_bad_lines='skip')
                df_temp['Stagione'] = s
                dfs.append(df_temp)
            else:
                errori.append(f"Stagione {s}: HTTP {r.status_code}")
        except Exception as e:
            errori.append(f"Stagione {s}: {str(e)}")
    if not dfs:
        return None, " | ".join(errori) if errori else "Nessun dato CSV disponibile."
    return pd.concat(dfs, ignore_index=True), None


def _calcola_media_pesata(df_sub, cols, usa_forma_recente=False, n_recenti=5):
    """Calcola la media semplice oppure ponderata (peso 2x sulle ultime N partite)."""
    if df_sub.empty:
        return {k: 0.0 for k in cols}
    for c in cols:
        if c not in df_sub.columns:
            df_sub[c] = 0.0
        df_sub[c] = pd.to_numeric(df_sub[c], errors='coerce').fillna(0.0)

    if not usa_forma_recente or len(df_sub) <= n_recenti:
        return df_sub[cols].mean().to_dict()

    pesi = np.ones(len(df_sub))
    pesi[-n_recenti:] = 2.0  # Peso doppio alle ultime 5 partite
    risultati = {}
    for c in cols:
        risultati[c] = float(np.average(df_sub[c].values, weights=pesi))
    return risultati


def elabora_statistiche(df, squadra, usa_forma_recente=False):
    cols = [
        'GF', 'GS', 'Tiri_Fatti', 'Tiri_Subiti',
        'Porta_Fatti', 'Porta_Subiti', 'Corner_Fatti', 'Corner_Subiti', 'Gialli'
    ]
    if 'Date' in df.columns:
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df = df.sort_values('Date_parsed')

    h = df[df['HomeTeam'] == squadra].copy().rename(columns={
        'FTHG': 'GF', 'FTAG': 'GS', 'HS': 'Tiri_Fatti', 'AS': 'Tiri_Subiti',
        'HST': 'Porta_Fatti', 'AST': 'Porta_Subiti', 'HC': 'Corner_Fatti',
        'AC': 'Corner_Subiti', 'HY': 'Gialli'
    })
    a = df[df['AwayTeam'] == squadra].copy().rename(columns={
        'FTAG': 'GF', 'FTHG': 'GS', 'AS': 'Tiri_Fatti', 'HS': 'Tiri_Subiti',
        'AST': 'Porta_Fatti', 'HST': 'Porta_Subiti', 'AC': 'Corner_Fatti',
        'HC': 'Corner_Subiti', 'AY': 'Gialli'
    })
    overall_df = pd.concat([h, a])
    if 'Date_parsed' in overall_df.columns:
        overall_df = overall_df.sort_values('Date_parsed')

    return {
        'overall': _calcola_media_pesata(overall_df, cols, usa_forma_recente),
        'home': _calcola_media_pesata(h, cols, usa_forma_recente),
        'away': _calcola_media_pesata(a, cols, usa_forma_recente),
    }


def calcola_probabilita_poisson(exp_gf_h, exp_gf_a, max_gol=8):
    """Calcola probabilità 1X2, Over/Under 2.5, BTTS e risultati esatti tramite Poisson."""
    exp_gf_h = max(0.05, float(exp_gf_h))
    exp_gf_a = max(0.05, float(exp_gf_a))

    prob_h = [poisson.pmf(i, exp_gf_h) for i in range(max_gol + 1)]
    prob_a = [poisson.pmf(j, exp_gf_a) for j in range(max_gol + 1)]
    matrice = np.outer(prob_h, prob_a)

    p_1 = float(np.sum(np.tril(matrice, -1)))
    p_x = float(np.sum(np.diag(matrice)))
    p_2 = float(np.sum(np.triu(matrice, 1)))

    # Normalizzazione per residuo > max_gol
    tot = p_1 + p_x + p_2
    p_1, p_x, p_2 = p_1 / tot, p_x / tot, p_2 / tot

    p_under25 = 0.0
    p_btts_yes = 0.0
    risultati_esatti = []

    for i in range(max_gol + 1):
        for j in range(max_gol + 1):
            p = matrice[i, j]
            if i + j <= 2:
                p_under25 += p
            if i >= 1 and j >= 1:
                p_btts_yes += p
            risultati_esatti.append((f"{i}-{j}", float(p)))

    p_over25 = max(0.0, 1.0 - p_under25)
    p_btts_no = max(0.0, 1.0 - p_btts_yes)
    risultati_esatti.sort(key=lambda x: x[1], reverse=True)

    return {
        'P1': p_1 * 100,
        'PX': p_x * 100,
        'P2': p_2 * 100,
        'Over25': p_over25 * 100,
        'Under25': p_under25 * 100,
        'BTTS_Yes': p_btts_yes * 100,
        'BTTS_No': p_btts_no * 100,
        'Top_Scores': risultati_esatti[:3],
    }


def valuta_value_bets(probs, q1, qx, q2):
    """Confronta le probabilità di Poisson con le quote reali per individuare Value Bet (EV > 5%)."""
    value_list = []
    mapping = [
        ("1 (Casa)", probs['P1'], q1),
        ("X (Pareggio)", probs['PX'], qx),
        ("2 (Ospite)", probs['P2'], q2),
    ]
    for label, prob_pct, quota in mapping:
        try:
            q_val = float(quota)
            if q_val > 1.0:
                prob_dec = prob_pct / 100.0
                ev = (prob_dec * q_val) - 1.0
                quota_fair = 1.0 / prob_dec if prob_dec > 0 else 99.0
                if ev > 0.05:  # Margine positivo > 5%
                    value_list.append({
                        'Esito': label,
                        'Prob_Modello': f"{prob_pct:.1f}%",
                        'Quota_Book': f"{q_val:.2f}",
                        'Quota_Fair': f"{quota_fair:.2f}",
                        'EV': f"+{ev * 100:.1f}%",
                    })
        except (ValueError, TypeError):
            continue
    return value_list


def genera_badge_partita(match, df_csv):
    """Calcola badge rapidi per la card del calendario sui campionati nazionali."""
    if df_csv is None or df_csv.empty:
        return []
    t_h = match_team_name(match['Casa'], df_csv['HomeTeam'].unique())
    t_a = match_team_name(match['Ospite'], df_csv['AwayTeam'].unique())
    if not t_h or not t_a:
        return []

    s_h = elabora_statistiche(df_csv, t_h, usa_forma_recente=True)
    s_a = elabora_statistiche(df_csv, t_a, usa_forma_recente=True)

    exp_gf = ((s_h['home']['GF'] + s_a['away']['GS']) / 2) + ((s_a['away']['GF'] + s_h['home']['GS']) / 2)
    exp_corn = ((s_h['home']['Corner_Fatti'] + s_a['away']['Corner_Subiti']) / 2) + (
        (s_a['away']['Corner_Fatti'] + s_h['home']['Corner_Subiti']) / 2
    )
    probs = calcola_probabilita_poisson(
        (s_h['home']['GF'] + s_a['away']['GS']) / 2,
        (s_a['away']['GF'] + s_h['home']['GS']) / 2,
    )
    v_bets = valuta_value_bets(probs, match['Q1'], match['QX'], match['Q2'])

    badges = []
    if probs['Over25'] >= 60.0 or exp_gf >= 2.85:
        badges.append(("🔥 Alto Potenziale Over 2.5", "#ff6b35"))
    elif probs['Under25'] >= 62.0:
        badges.append(("🛡️ Partita Bloccata (Under 2.5)", "#3d5afe"))

    if exp_corn >= 10.5:
        badges.append(("🚩 Pioggia di Corner (>10.5)", "#00c896"))

    if v_bets:
        badges.append((f"💎 Value Bet: {v_bets[0]['Esito']}", "#eab308"))

    return badges


def crea_dataframe_confronto(metrics, s_h, s_a, t_h, t_a):
    """Fix bug: verifica la presenza della chiave 'home'/'away' anziché GF > 0."""
    data = {"Metrica": metrics}
    type_h = 'home' if 'home' in s_h else 'overall'
    type_a = 'away' if 'away' in s_a else 'overall'
    data[f"{t_h} ({type_h.upper()})"] = [f"{s_h[type_h].get(m, 0):.2f}" for m in metrics]
    data[f"{t_a} ({type_a.upper()})"] = [f"{s_a[type_a].get(m, 0):.2f}" for m in metrics]
    return pd.DataFrame(data).set_index("Metrica")


def crea_grafico_confronto(val_h, val_a, label, t_h, t_a, color_h='#00ff85', color_a='#3d5afe'):
    """Grafico comparativo ad alta leggibilità con etichette numeriche esplicite e legenda."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[label],
        x=[val_h],
        orientation='h',
        name=t_h,
        marker_color=color_h,
        text=[f"{val_h:.2f}"],
        textposition='auto',
        textfont=dict(size=14, color='#0e1117', family='Inter')
    ))
    fig.add_trace(go.Bar(
        y=[label],
        x=[val_a],
        orientation='h',
        name=t_a,
        marker_color=color_a,
        text=[f"{val_a:.2f}"],
        textposition='auto',
        textfont=dict(size=14, color='#ffffff', family='Inter')
    ))
    fig.update_layout(
        barmode='group',
        height=170,
        margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color="#ffffff")),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=True, showticklabels=True, color='#aaaaaa'),
        yaxis=dict(showgrid=False, color='#ffffff')
    )
    return fig
