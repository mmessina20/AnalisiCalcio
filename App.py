# app.py
import streamlit as st
import pandas as pd
import config
import utils

# --- CONFIGURAZIONE PAGINA E STATO ---
st.set_page_config(
    page_title="Analisi Calcio 25/26",
    page_icon="⚽",
    layout="wide"
)

# --- CSS CUSTOM PER STILE PROFESSIONALE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Card delle partite */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: #1f2937 !important;
        border-radius: 16px !important;
        padding: 15px !important;
        transition: transform 0.2s, border-color 0.2s;
        margin-bottom: 10px;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #00ff85 !important;
        transform: translateY(-2px);
    }

    .stButton > button {
        width: 100%;
        background-color: transparent !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        background-color: #00ff85 !important;
        color: #0e1117 !important;
        border: none !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #00ff85 !important;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione Session State
if 'pagina_corrente' not in st.session_state:
    st.session_state.pagina_corrente = "calendario"
if 'match_selezionato' not in st.session_state:
    st.session_state.match_selezionato = None
if 'lega_selezionata' not in st.session_state or st.session_state.lega_selezionata not in config.LEAGUES_CONFIG:
    st.session_state.lega_selezionata = "Serie A (Italia)"

# --- SIDEBAR NAVIGAZIONE ---
with st.sidebar:
    st.markdown("<h1 style='color:#00ff85;'>⚽ PRO ANALYTICS</h1>", unsafe_allow_html=True)
    st.divider()
    
    nuova_lega = st.selectbox(
        "Seleziona Campionato",
        list(config.LEAGUES_CONFIG.keys()),
        index=list(config.LEAGUES_CONFIG.keys()).index(st.session_state.lega_selezionata)
    )
    
    if nuova_lega != st.session_state.lega_selezionata:
        st.session_state.lega_selezionata = nuova_lega
        st.session_state.pagina_corrente = "calendario"
        st.session_state.match_selezionato = None
        st.rerun()
        
    st.info("Statistiche basate su xG, Corner e tiri storici.")

# --- ESTRAZIONE CODICI (FONDAMENTALE) ---
codice_csv, codice_api = config.LEAGUES_CONFIG[st.session_state.lega_selezionata]

# --- SEZIONE CALENDARIO ---
if st.session_state.pagina_corrente == "calendario":
    fixtures, giornata = utils.get_next_matchday_fixtures(codice_api)
    
    st.markdown(f"<h2 style='text-align: center;'>📅 {st.session_state.lega_selezionata} - Giornata {giornata if giornata else '?'}</h2>", unsafe_allow_html=True)
    
    if fixtures:
        cols = st.columns(2)
        for i, match in enumerate(fixtures):
            with cols[i % 2]:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 3])
                    c1.markdown(f"<p style='text-align:right; font-size:1.2rem; font-weight:bold; margin:0;'>{match['Casa']}</p>", unsafe_allow_html=True)
                    c2.markdown("<p style='text-align:center; color:#00ff85; font-weight:bold; margin:0;'>VS</p>", unsafe_allow_html=True)
                    c3.markdown(f"<p style='text-align:left; font-size:1.2rem; font-weight:bold; margin:0;'>{match['Ospite']}</p>", unsafe_allow_html=True)
                    
                    st.write("") # Spazio
                    if st.button("ANALISI MATCH", key=f"btn_{i}"):
                        st.session_state.match_selezionato = (match['Casa'], match['Ospite'])
                        st.session_state.pagina_corrente = "analisi"
                        st.rerun()
    else:
        st.warning("Nessuna partita trovata per questa lega.")

# --- SEZIONE ANALISI ---
elif st.session_state.pagina_corrente == "analisi" and st.session_state.match_selezionato:
    nome_home_api, nome_away_api = st.session_state.match_selezionato
    
    if st.button("⬅️ Torna al Calendario"):
        st.session_state.pagina_corrente = "calendario"
        st.session_state.match_selezionato = None
        st.rerun()
        
    st.markdown(f"<h1 style='text-align:center;'>🏟️ {nome_home_api} vs {nome_away_api}</h1>", unsafe_allow_html=True)
    st.divider()

    if codice_csv is None:
        st.info("ℹ️ Statistiche avanzate non disponibili per questa competizione.")
    else:
        scelta_periodo = st.radio("Dati da analizzare:", ["Stagione 25/26", "Ultime 2 Stagioni"], horizontal=True)
        stagioni_target = ["2425", "2526"] if "Ultime 2" in scelta_periodo else ["2526"]

        with st.spinner("Elaborazione dati..."):
            df_storico = utils.scarica_dati_csv(codice_csv, stagioni_target)

        if df_storico is not None:
            squadre_csv = sorted(list(set(df_storico['HomeTeam'].unique()) | set(df_storico['AwayTeam'].unique())))
            match_home = utils.match_team_name(nome_home_api, squadre_csv)
            match_away = utils.match_team_name(nome_away_api, squadre_csv)
            
            if match_home and match_away:
                s_h = utils.elabora_statistiche(df_storico, match_home)
                s_a = utils.elabora_statistiche(df_storico, match_away)
                
                if s_h and s_a:
                    # Calcolo Predizioni Rapide
                    pred_xg = ((s_h['home']['GF'] + s_a['away']['GS']) / 2) + ((s_a['away']['GF'] + s_h['home']['GS']) / 2)
                    pred_corn = (s_h['home']['Corner_Fatti'] + s_a['away']['Corner_Subiti'] + s_a['away']['Corner_Fatti'] + s_h['home']['Corner_Subiti']) / 2
                    
                    k1, k2 = st.columns(2)
                    k1.metric("xG Totali Previsti", f"{pred_xg:.2f}")
                    k2.metric("Corner Totali Previsti", f"{pred_corn:.1f}")
                    
                    st.write("")
                    
                    # --- SEZIONE TAB ANALISI AVANZATA (VERSIONE COMPLETA) ---
                    tab1, tab2, tab3, tab4 = st.tabs(["⚽ GOL", "🎯 TIRI", "🚩 CORNER", "🟨 DISCIPLINA"])

                    with tab1:
                        st.markdown("### 📊 Media Gol Fatti e Subiti")
                        # Ripristinate tutte le statistiche: Gol Fatti e Gol Subiti
                        st.dataframe(utils.crea_dataframe_confronto(['GF', 'GS'], s_h, s_a, match_home, match_away), use_container_width=True)
                        
                        # Grafico: Focus su Gol Fatti (Potenziale offensivo)
                        fig_gol = utils.crea_grafico_confronto(s_h['home']['GF'], s_a['away']['GF'], "Media Gol Fatti", match_home, match_away)
                        st.plotly_chart(fig_gol, use_container_width=True)

                    with tab2:
                        st.markdown("### 🎯 Analisi Tiri e Precisione")
                        # Ripristinati tutti i dati: Fatti, Subiti, In Porta Fatti, In Porta Subiti
                        st.dataframe(utils.crea_dataframe_confronto(
                            ['Tiri_Fatti', 'Tiri_Subiti', 'Porta_Fatti', 'Porta_Subiti'], 
                            s_h, s_a, match_home, match_away
                        ), use_container_width=True)
                        
                        # Grafico: Focus su Tiri in Porta Fatti
                        fig_tiri = utils.crea_grafico_confronto(s_h['home']['Porta_Fatti'], s_a['away']['Porta_Fatti'], "Tiri in Porta (Media)", match_home, match_away)
                        st.plotly_chart(fig_tiri, use_container_width=True)

                    with tab3:
                        st.markdown("### 🚩 Analisi Corner")
                        # Ripristinati: Corner Fatti e Corner Subiti
                        st.dataframe(utils.crea_dataframe_confronto(['Corner_Fatti', 'Corner_Subiti'], s_h, s_a, match_home, match_away), use_container_width=True)
                        
                        # Grafico: Focus su Corner Guadagnati
                        fig_corn = utils.crea_grafico_confronto(s_h['home']['Corner_Fatti'], s_a['away']['Corner_Fatti'], "Corner a Favore", match_home, match_away)
                        st.plotly_chart(fig_corn, use_container_width=True)

                    with tab4:
                        st.markdown("### 🟨 Disciplina e Falli")
                        # Statistiche cartellini
                        st.dataframe(utils.crea_dataframe_confronto(['Gialli'], s_h, s_a, match_home, match_away), use_container_width=True)
                        
                        # Grafico: Cartellini Gialli
                        fig_cards = utils.crea_grafico_confronto(s_h['home']['Gialli'], s_a['away']['Gialli'], "Media Ammonizioni", match_home, match_away)
                        st.plotly_chart(fig_cards, use_container_width=True)
            else:
                st.error("Squadre non trovate nel database storico.")