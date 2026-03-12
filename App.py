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
    
    st.markdown(f"<h2 style='text-align: center; margin-bottom: 20px;'>📅 {st.session_state.lega_selezionata} - Giornata {giornata if giornata else '?'}</h2>", unsafe_allow_html=True)
    
    if fixtures:
        cols = st.columns(2)
        for i, match in enumerate(fixtures):
            with cols[i % 2]:
                # Il container 'border=True' crea la card
                with st.container(border=True):
                    # HTML UNIFICATO PER LOGHI E NOMI SULLA STESSA LINEA
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; height: 40px;">
                            <!-- SQUADRA CASA (Logo + Nome) -->
                            <div style="display: flex; align-items: center; flex: 1; overflow: hidden;">
                                <img src="{match.get('Logo_Casa')}" width="30" height="30" style="margin-right: 10px; object-fit: contain;">
                                <span style="font-weight: 700; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                    {match['Casa']}
                                </span>
                            </div>
                            
                            <!-- SEPARATORE VS -->
                            <div style="width: 40px; text-align: center; color: #00ff85; font-weight: 900; font-size: 0.8rem; flex-shrink: 0;">
                                VS
                            </div>
                            
                            <!-- SQUADRA OSPITE (Nome + Logo) -->
                            <div style="display: flex; align-items: center; flex: 1; justify-content: flex-end; overflow: hidden;">
                                <span style="font-weight: 700; font-size: 0.95rem; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-left: 10px;">
                                    {match['Ospite']}
                                </span>
                                <img src="{match.get('Logo_Ospite')}" width="30" height="30" style="margin-left: 10px; object-fit: contain;">
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Spazio minimo tra info e bottone
                    st.write('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
                    
                    # Bottone che occupa tutta la larghezza della card
                    if st.button("ANALISI MATCH", key=f"btn_{i}", use_container_width=True):
                        st.session_state.match_selezionato = {
                            'casa': match['Casa'],
                            'ospite': match['Ospite'],
                            'logo_h': match.get('Logo_Casa'),
                            'logo_a': match.get('Logo_Ospite')
                        }
                        st.session_state.pagina_corrente = "analisi"
                        st.rerun()
    else:
        st.warning("Nessuna partita trovata per questa lega.")

# --- SEZIONE ANALISI ---
elif st.session_state.pagina_corrente == "analisi" and st.session_state.match_selezionato:
    # Recupero dati dal dizionario del session state
    m = st.session_state.match_selezionato
    nome_home_api, nome_away_api = m['casa'], m['ospite']
    logo_h, logo_a = m['logo_h'], m['logo_a']
    
    if st.button("⬅️ Torna al Calendario"):
        st.session_state.pagina_corrente = "calendario"
        st.session_state.match_selezionato = None
        st.rerun()
        
    # Header con Loghi
    h_col1, h_col2, h_col3 = st.columns([2, 1, 2])
    with h_col1:
        if logo_h: st.image(logo_h, width=100)
        st.header(nome_home_api)
    with h_col2:
        st.markdown("<h1 style='text-align:center; padding-top:20px;'>VS</h1>", unsafe_allow_html=True)
    with h_col3:
        if logo_a: st.markdown(f"<div style='text-align:right;'><img src='{logo_a}' width='100'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:right;'>{nome_away_api}</h1>", unsafe_allow_html=True)

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
                    
                    # --- SEZIONE TAB ANALISI AVANZATA ---
                    tab1, tab2, tab3, tab4 = st.tabs(["⚽ GOL", "🎯 TIRI", "🚩 CORNER", "🟨 DISCIPLINA"])

                    with tab1:
                        st.markdown("### 📊 Media Gol Fatti e Subiti")
                        st.dataframe(utils.crea_dataframe_confronto(['GF', 'GS'], s_h, s_a, match_home, match_away), use_container_width=True)
                        fig_gol = utils.crea_grafico_confronto(s_h['home']['GF'], s_a['away']['GF'], "Media Gol Fatti", match_home, match_away)
                        st.plotly_chart(fig_gol, use_container_width=True)

                    with tab2:
                        st.markdown("### 🎯 Analisi Tiri e Precisione")
                        st.dataframe(utils.crea_dataframe_confronto(
                            ['Tiri_Fatti', 'Tiri_Subiti', 'Porta_Fatti', 'Porta_Subiti'], 
                            s_h, s_a, match_home, match_away
                        ), use_container_width=True)
                        fig_tiri = utils.crea_grafico_confronto(s_h['home']['Porta_Fatti'], s_a['away']['Porta_Fatti'], "Tiri in Porta (Media)", match_home, match_away)
                        st.plotly_chart(fig_tiri, use_container_width=True)

                    with tab3:
                        st.markdown("### 🚩 Analisi Corner")
                        st.dataframe(utils.crea_dataframe_confronto(['Corner_Fatti', 'Corner_Subiti'], s_h, s_a, match_home, match_away), use_container_width=True)
                        fig_corn = utils.crea_grafico_confronto(s_h['home']['Corner_Fatti'], s_a['away']['Corner_Fatti'], "Corner a Favore", match_home, match_away)
                        st.plotly_chart(fig_corn, use_container_width=True)

                    with tab4:
                        st.markdown("### 🟨 Disciplina e Falli")
                        st.dataframe(utils.crea_dataframe_confronto(['Gialli'], s_h, s_a, match_home, match_away), use_container_width=True)
                        fig_cards = utils.crea_grafico_confronto(s_h['home']['Gialli'], s_a['away']['Gialli'], "Media Ammonizioni", match_home, match_away)
                        st.plotly_chart(fig_cards, use_container_width=True)
            else:
                st.error("Squadre non trovate nel database storico.")