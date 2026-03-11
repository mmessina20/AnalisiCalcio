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

# --- CSS CUSTOM PER STILE ---
st.markdown("""
<style>
    /* 1. CENTRA IL CONTENITORE DEL BOTTONE */
    div.stButton {
        display: flex;
        justify-content: center;
        width: 100%;
    }

    /* 2. STILE DEL BOTTONE STESSO */
    div.stButton > button {
        width: 90%;
        max-width: 600px;
        margin: 0 auto;
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
        
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        font-size: 16px;
        background-color: white;
        color: #333;
        transition: all 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
        background-color: #fffbfb;
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    
    /* Nasconde indici tabelle */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* Stile per la Navbar */
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stRadio"] > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        justify-content: center;
        flex-wrap: wrap; 
    }
    div[role="radiogroup"] {
        justify-content: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione Session State
if 'pagina_corrente' not in st.session_state:
    st.session_state.pagina_corrente = "calendario"
if 'match_selezionato' not in st.session_state:
    st.session_state.match_selezionato = None

# FIX: Controllo consistenza lega
if 'lega_selezionata' not in st.session_state or st.session_state.lega_selezionata not in config.LEAGUES_CONFIG:
    st.session_state.lega_selezionata = "Serie A (Italia)"

# --- NAVIGAZIONE IN ALTO (CENTRATA) ---
c1, c2, c3 = st.columns([1, 4, 1])
with c2:
    st.markdown("<h3 style='text-align: center;'>🏆 Seleziona il Campionato</h3>", unsafe_allow_html=True)
    nuova_lega = st.radio(
        "Lega:", 
        list(config.LEAGUES_CONFIG.keys()), 
        horizontal=True,
        index=list(config.LEAGUES_CONFIG.keys()).index(st.session_state.lega_selezionata),
        label_visibility="collapsed"
    )

if nuova_lega != st.session_state.lega_selezionata:
    st.session_state.lega_selezionata = nuova_lega
    st.session_state.pagina_corrente = "calendario"
    st.session_state.match_selezionato = None
    st.rerun()

st.divider()

codice_csv, codice_api = config.LEAGUES_CONFIG[st.session_state.lega_selezionata]

# --- SEZIONE CALENDARIO ---
if st.session_state.pagina_corrente == "calendario":
    fixtures, giornata = utils.get_next_matchday_fixtures(codice_api)
    
    cal_col1, cal_col2, cal_col3 = st.columns([1, 2, 1])
    with cal_col2:
        st.markdown(f"<h4 style='text-align: center;'>📅 Prossimo Turno (Giornata {giornata if giornata else '?'})</h4>", unsafe_allow_html=True)
        if fixtures:
            for i, match in enumerate(fixtures):
                if st.button(match['Display'], key=f"btn_{i}"):
                    st.session_state.match_selezionato = (match['Casa'], match['Ospite'])
                    st.session_state.pagina_corrente = "analisi"
                    st.rerun()
        else:
            st.info("Nessuna partita programmata trovata a breve.")

# --- SEZIONE ANALISI ---
elif st.session_state.pagina_corrente == "analisi" and st.session_state.match_selezionato:
    nome_home_api, nome_away_api = st.session_state.match_selezionato
    
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("⬅️ Torna"):
            st.session_state.pagina_corrente = "calendario"
            st.session_state.match_selezionato = None
            st.rerun()
    with col_title:
        st.markdown(f"## 🏟️ {nome_home_api} vs {nome_away_api}")

    st.markdown("---")
    
    if codice_csv is None:
        st.info("ℹ️ **Nota:** Per questa competizione (es. Champions) sono disponibili solo calendario e risultati. Le statistiche avanzate (xG, Corner) non sono disponibili.")
    else:
        col_opt1, col_opt2 = st.columns([2, 1])
        with col_opt1:
            scelta_periodo = st.radio(
                "📊 Periodo dati da analizzare:", 
                ["Stagione Corrente (25/26)", "Ultime 2 Stagioni (24/25 + 25/26)"],
                horizontal=True
            )
        
        stagioni_target = ["2425", "2526"] if "Ultime 2" in scelta_periodo else ["2526"]

        with st.spinner("Scaricamento ed elaborazione dati storici..."):
            df_storico = utils.scarica_dati_csv(codice_csv, stagioni_target)

        if df_storico is not None:
            squadre_csv = sorted(list(set(df_storico['HomeTeam'].unique()) | set(df_storico['AwayTeam'].unique())))
            match_home = utils.match_team_name(nome_home_api, squadre_csv)
            match_away = utils.match_team_name(nome_away_api, squadre_csv)
            
            if not match_home or not match_away:
                st.warning("⚠️ Alcune squadre non sono state riconosciute.")
                c1, c2 = st.columns(2)
                if not match_home: match_home = c1.selectbox(f"Correggi {nome_home_api}:", squadre_csv, key="fix_h")
                if not match_away: match_away = c2.selectbox(f"Correggi {nome_away_api}:", squadre_csv, key="fix_a")

            if match_home and match_away:
                s_h = utils.elabora_statistiche(df_storico, match_home)
                s_a = utils.elabora_statistiche(df_storico, match_away)
                
                if s_h and s_a:
                    pred_gf_h = (s_h['home']['GF'] + s_a['away']['GS']) / 2
                    pred_gf_a = (s_a['away']['GF'] + s_h['home']['GS']) / 2
                    tot_xg = pred_gf_h + pred_gf_a
                    
                    pred_tiri_h = (s_h['home']['Tiri_Fatti'] + s_a['away']['Tiri_Subiti']) / 2
                    pred_tiri_a = (s_a['away']['Tiri_Fatti'] + s_h['home']['Tiri_Subiti']) / 2
                    
                    pred_corn_h = (s_h['home']['Corner_Fatti'] + s_a['away']['Corner_Subiti']) / 2
                    pred_corn_a = (s_a['away']['Corner_Fatti'] + s_h['home']['Corner_Subiti']) / 2
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Gol Attesi (xG)", f"{tot_xg:.2f}", f"{match_home}: {pred_gf_h:.1f}  -  {match_away}: {pred_gf_a:.1f}")
                    k2.metric("Tiri Totali Previsti", f"{(pred_tiri_h + pred_tiri_a):.1f}", f"{match_home}: {pred_tiri_h:.1f}  -  {match_away}: {pred_tiri_a:.1f}")
                    k3.metric("Corner Totali Previsti", f"{(pred_corn_h + pred_corn_a):.1f}", f"{match_home}: {pred_corn_h:.1f}  -  {match_away}: {pred_corn_a:.1f}")
                    
                    st.divider()

                    tab1, tab2, tab3, tab4 = st.tabs(["⚽ GOL", "🎯 TIRI", "🚩 CORNER", "🟨 DISCIPLINA"])

                    with tab1:
                        st.dataframe(utils.crea_dataframe_confronto(['GF', 'GS'], s_h, s_a, match_home, match_away), use_container_width=True)
                    with tab2:
                        st.dataframe(utils.crea_dataframe_confronto(['Tiri_Fatti', 'Tiri_Subiti', 'Porta_Fatti', 'Porta_Subiti'], s_h, s_a, match_home, match_away), use_container_width=True)
                    with tab3:
                        st.dataframe(utils.crea_dataframe_confronto(['Corner_Fatti', 'Corner_Subiti'], s_h, s_a, match_home, match_away), use_container_width=True)
                        cc1, cc2 = st.columns(2)
                        cc1.markdown("**Corner a Favore (Media)**")
                        cc1.bar_chart(pd.DataFrame({match_home: s_h['home']['Corner_Fatti'], match_away: s_a['away']['Corner_Fatti']}, index=["Media Fatti"]))
                        cc2.markdown("**Corner Subiti (Media)**")
                        cc2.bar_chart(pd.DataFrame({match_home: s_h['home']['Corner_Subiti'], match_away: s_a['away']['Corner_Subiti']}, index=["Media Subiti"]), color=["#FF4B4B", "#FF4B4B"])
                    with tab4:
                        st.dataframe(utils.crea_dataframe_confronto(['Gialli'], s_h, s_a, match_home, match_away), use_container_width=True)
            else:
                st.error("Dati insufficienti.")
        else:
            st.warning(f"Nessun dato storico trovato per {scelta_periodo}.")