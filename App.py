import streamlit as st
import pandas as pd
import config
import utils

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Pro Analytics 26/27", page_icon="⚽", layout="wide")

# CSS Professionale
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e1117; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255,255,255,0.12) !important;
        background-color: #1f2937 !important;
        border-radius: 12px !important;
    }
    [data-testid="stMetricValue"] { font-size: 2.0rem !important; font-weight: 900 !important; color: #00ff85 !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 700; text-transform: uppercase; }
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        color: #ffffff;
        margin-right: 6px;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione Session State
if 'pagina_corrente' not in st.session_state:
    st.session_state.pagina_corrente = "calendario"
if 'lega_selezionata' not in st.session_state:
    st.session_state.lega_selezionata = "Serie A (Italia)"
if 'giornata_selezionata' not in st.session_state:
    st.session_state.giornata_selezionata = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#00ff85;'>⚽ PRO ANALYTICS</h1>", unsafe_allow_html=True)
    nuova_lega = st.selectbox(
        "Seleziona Competizione",
        list(config.LEAGUES_CONFIG.keys()),
        index=list(config.LEAGUES_CONFIG.keys()).index(st.session_state.lega_selezionata)
    )
    if nuova_lega != st.session_state.lega_selezionata:
        st.session_state.lega_selezionata = nuova_lega
        st.session_state.pagina_corrente = "calendario"
        st.session_state.giornata_selezionata = None
        st.rerun()

    st.divider()
    st.info("💡 Modello Poisson + Incrocio Offesa vs Difesa + Rilevamento Value Bet.")

codice_csv, codice_api, codice_odds, url_fbref = config.LEAGUES_CONFIG[st.session_state.lega_selezionata]

# --- PAGINA CALENDARIO ---
if st.session_state.pagina_corrente == "calendario":
    fixtures_by_day, giornate_disponibili, err_api = utils.get_all_scheduled_fixtures(codice_api, codice_odds)

    if err_api:
        st.error(f"⚠️ {err_api}")
    elif giornate_disponibili:
        # Selettore Giornata
        col_title, col_day = st.columns([3, 1])
        with col_day:
            default_idx = 0
            if st.session_state.giornata_selezionata in giornate_disponibili:
                default_idx = giornate_disponibili.index(st.session_state.giornata_selezionata)
            giornata_scelta = st.selectbox(
                "Giornata",
                giornate_disponibili,
                index=default_idx,
                format_func=lambda x: "Prossimi Match" if x == 0 else f"Giornata {x}"
            )
            st.session_state.giornata_selezionata = giornata_scelta

        with col_title:
            label_giornata = "Prossimi Match" if giornata_scelta == 0 else f"Giornata {giornata_scelta}"
            st.markdown(
                f"<h2 style='margin-top:10px;'>📅 {st.session_state.lega_selezionata} - {label_giornata}</h2>",
                unsafe_allow_html=True
            )

        # Precaricamento CSV stagione corrente 26/27 per i badge rapidi sulle card
        df_csv_rapido = None
        if codice_csv is not None:
            df_csv_rapido, _ = utils.scarica_dati_csv(codice_csv, ["2627"])

        fixtures = fixtures_by_day.get(giornata_scelta, [])
        cols = st.columns(2)
        for i, match in enumerate(fixtures):
            with cols[i % 2]:
                with st.container(border=True):
                    badges = utils.genera_badge_partita(match, df_csv_rapido)
                    badges_html = ""
                    if badges:
                        badges_html = "<div style='margin-bottom:8px;'>" + "".join(
                            [f"<span class='badge-pill' style='background-color:{col};'>{txt}</span>" for txt, col in badges]
                        ) + "</div>"

                    html_card = f"""
                    {badges_html}
                    <div style="display: flex; align-items: center; justify-content: space-between; height: 60px;">
                        <div style="display: flex; align-items: center; flex: 1; overflow: hidden;">
                            <img src="{match['Logo_Casa']}" width="35" style="margin-right: 10px;">
                            <span style="font-weight: 700; font-size: 1rem;">{match['Casa']}</span>
                        </div>
                        <div style="width: 85px; text-align: center; border-left: 1px solid #444; border-right: 1px solid #444;">
                            <div style="font-size: 0.72rem; color: #aaa;">{match['Data']}</div>
                            <div style="font-size: 1rem; color: #00ff85; font-weight: 900;">{match['Ora']}</div>
                        </div>
                        <div style="display: flex; align-items: center; flex: 1; justify-content: flex-end; overflow: hidden;">
                            <span style="font-weight: 700; font-size: 1rem; text-align: right;">{match['Ospite']}</span>
                            <img src="{match['Logo_Ospite']}" width="35" style="margin-left: 10px;">
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin: 10px 0; background: #161b22; padding: 6px; border-radius: 6px; font-size: 0.85rem;">
                        <span>1: <b>{match['Q1']}</b></span>
                        <span>X: <b>{match['QX']}</b></span>
                        <span>2: <b>{match['Q2']}</b></span>
                        <span style="color: #444;">|</span>
                        <span style="color: #00ff85;">O2.5: <b>{match['QO25']}</b></span>
                        <span style="color: #60a5fa;">U2.5: <b>{match['QU25']}</b></span>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
                    if st.button("ANALIZZA STATISTICHE", key=f"btn_{giornata_scelta}_{i}", use_container_width=True):
                        st.session_state.match_selezionato = match
                        st.session_state.pagina_corrente = "analisi"
                        st.rerun()
    else:
        st.warning("Nessuna partita programmata trovata.")

# --- PAGINA ANALISI ---
elif st.session_state.pagina_corrente == "analisi":
    m = st.session_state.match_selezionato
    if st.button("⬅️ Torna al Calendario"):
        st.session_state.pagina_corrente = "calendario"
        st.rerun()

    col_h, col_vs, col_a = st.columns([2, 1, 2])
    with col_h:
        if m['Logo_Casa']:
            st.image(m['Logo_Casa'], width=95)
        st.header(m['Casa'])
    with col_vs:
        st.markdown("<h1 style='text-align:center; margin-top:30px;'>VS</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align:center; color:#aaa;'>{m['Data']} - {m['Ora']}</p>",
            unsafe_allow_html=True
        )
    with col_a:
        if m['Logo_Ospite']:
            st.markdown(f"<div style='text-align:right;'><img src='{m['Logo_Ospite']}' width='95'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:right;'>{m['Ospite']}</h1>", unsafe_allow_html=True)

    st.divider()

    # Caricamento Dati
    s_h, s_a = None, None
    err_dati = None

    if codice_csv is None:  # Coppe Europee (API Standings + CSV Campionati Nazionali)
        with st.spinner(f"Recupero dati {st.session_state.lega_selezionata} e campionati nazionali..."):
            standings_map, df_europa_csv, err_dati = utils.scarica_statistiche_coppe_europee(codice_api)
            s_h = utils.estrai_metriche_coppa_squadra(m['Casa'], standings_map, df_europa_csv)
            s_a = utils.estrai_metriche_coppa_squadra(m['Ospite'], standings_map, df_europa_csv)
    else:  # Campionati Nazionali (CSV aggiornati al 26/27)
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            opt_periodo = st.radio(
                "Finestra storica:",
                ["Stagione 26/27", "Ultime 2 Stagioni (25/26 + 26/27)"],
                horizontal=True
            )
        with col_opt2:
            usa_forma = st.toggle(
                "🔥 Dai peso doppio alle ultime 5 partite (Forma Recente)",
                value=True
            )

        stagioni = ["2526", "2627"] if "Ultime" in opt_periodo else ["2627"]
        df_csv, err_dati = utils.scarica_dati_csv(codice_csv, stagioni)
        if df_csv is not None and not df_csv.empty:
            t_h = utils.match_team_name(m['Casa'], df_csv['HomeTeam'].unique())
            t_a = utils.match_team_name(m['Ospite'], df_csv['AwayTeam'].unique())
            if t_h and t_a:
                s_h = utils.elabora_statistiche(df_csv, t_h, usa_forma_recente=usa_forma)
                s_a = utils.elabora_statistiche(df_csv, t_a, usa_forma_recente=usa_forma)

    if err_dati:
        st.warning(f"Dettaglio caricamento dati: {err_dati}")

    # VISUALIZZAZIONE STATISTICHE E MODELLO POISSON
    if s_h and s_a:
        h_type = 'home' if 'home' in s_h and codice_csv else 'overall'
        a_type = 'away' if 'away' in s_a and codice_csv else 'overall'

        # Logica incrociata (Offesa Squadra A vs Difesa Squadra B)
        exp_gf_h = (s_h[h_type]['GF'] + s_a[a_type]['GS']) / 2
        exp_gf_a = (s_a[a_type]['GF'] + s_h[h_type]['GS']) / 2
        pred_xg = exp_gf_h + exp_gf_a

        exp_tiri_h = (s_h[h_type]['Tiri_Fatti'] + s_a[a_type]['Tiri_Subiti']) / 2
        exp_tiri_a = (s_a[a_type]['Tiri_Fatti'] + s_h[h_type]['Tiri_Subiti']) / 2
        pred_tiri = exp_tiri_h + exp_tiri_a

        exp_corn_h = (s_h[h_type]['Corner_Fatti'] + s_a[a_type]['Corner_Subiti']) / 2
        exp_corn_a = (s_a[a_type]['Corner_Fatti'] + s_h[h_type]['Corner_Subiti']) / 2
        pred_corner = exp_corn_h + exp_corn_a

        # Calcolo Probabilità di Poisson & Value Bets
        probs = utils.calcola_probabilita_poisson(exp_gf_h, exp_gf_a)
        value_bets = utils.valuta_value_bets(probs, m['Q1'], m['QX'], m['Q2'])

        # Metriche Principali
        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Goal Previsti (Tot)", f"{pred_xg:.2f}", f"{exp_gf_h:.2f} - {exp_gf_a:.2f}")
        met2.metric("Over 2.5 (Poisson)", f"{probs['Over25']:.1f}%", f"Under: {probs['Under25']:.1f}%")
        met3.metric("Tiri Previsti", f"{pred_tiri:.1f}", f"{exp_tiri_h:.1f} - {exp_tiri_a:.1f}")
        met4.metric("Corner Previsti", f"{pred_corner:.1f}", f"{exp_corn_h:.1f} - {exp_corn_a:.1f}")

        st.divider()

        # Tabs Dettagliate (inclusa nuova tab Poisson & Quote)
        t0, t1, t2, t3, t4 = st.tabs([
            "📊 POISSON & VALUE BET",
            "⚽ GOL",
            "🎯 TIRI",
            "🚩 CORNER",
            "🟨 DISCIPLINA"
        ])

        with t0:
            st.subheader("Probabilità Calcolate (Distribuzione di Poisson)")
            p1_col, px_col, p2_col, btts_col = st.columns(4)
            p1_col.metric(f"1 ({m['Casa']})", f"{probs['P1']:.1f}%", f"Quota: {m['Q1']}")
            px_col.metric("X (Pareggio)", f"{probs['PX']:.1f}%", f"Quota: {m['QX']}")
            p2_col.metric(f"2 ({m['Ospite']})", f"{probs['P2']:.1f}%", f"Quota: {m['Q2']}")
            btts_col.metric("Goal / No Goal", f"{probs['BTTS_Yes']:.1f}%", f"No Goal: {probs['BTTS_No']:.1f}%")

            st.markdown("#### Focus Linea Gol: Over / Under 2.5")
            ou1, ou2, ou3 = st.columns(3)
            ou1.metric("Over 2.5 (Modello)", f"{probs['Over25']:.1f}%", f"Quota Book: {m['QO25']}")
            ou2.metric("Under 2.5 (Modello)", f"{probs['Under25']:.1f}%", f"Quota Book: {m['QU25']}")
            ou3.metric("Quota Fair Over 2.5", f"{(100.0 / max(probs['Over25'], 1.0)):.2f}", f"Fair Under: {(100.0 / max(probs['Under25'], 1.0)):.2f}")

            st.markdown("#### Risultati Esatti Più Probabili")
            top_cols = st.columns(3)
            for idx, (score_str, prob_val) in enumerate(probs['Top_Scores']):
                top_cols[idx].info(f"**{score_str}** — Probabilità: **{prob_val * 100:.1f}%**")

            st.markdown("#### Analisi Quote & Value Bet (1X2 e Over/Under 2.5)")
            st.caption("Le quote vengono caricate automaticamente se hai impostato ODDS_API_KEY, oppure puoi modificarle qui sotto:")
            qc1, qc2, qc3, qc4, qc5 = st.columns(5)
            q1_val = qc1.number_input("Quota 1", min_value=1.01, max_value=50.0, value=float(m['Q1']) if m['Q1'] != 'N.D.' else 2.00, step=0.05)
            qx_val = qc2.number_input("Quota X", min_value=1.01, max_value=50.0, value=float(m['QX']) if m['QX'] != 'N.D.' else 3.30, step=0.05)
            q2_val = qc3.number_input("Quota 2", min_value=1.01, max_value=50.0, value=float(m['Q2']) if m['Q2'] != 'N.D.' else 3.50, step=0.05)
            qo25_val = qc4.number_input("Over 2.5", min_value=1.01, max_value=50.0, value=float(m['QO25']) if m['QO25'] != 'N.D.' else 1.85, step=0.05)
            qu25_val = qc5.number_input("Under 2.5", min_value=1.01, max_value=50.0, value=float(m['QU25']) if m['QU25'] != 'N.D.' else 1.95, step=0.05)

            value_bets = utils.valuta_value_bets(probs, q1_val, qx_val, q2_val, qo25_val, qu25_val)
            if value_bets:
                st.success("💎 Rilevate opportunità con valore matematico positivo (EV > 5%):")
                st.dataframe(pd.DataFrame(value_bets), use_container_width=True, hide_index=True)
            else:
                st.info("Nessuna Value Bet significativa rilevata con queste quote (EV ≤ 5%).")

        with t1:
            st.dataframe(utils.crea_dataframe_confronto(['GF', 'GS'], s_h, s_a, m['Casa'], m['Ospite']), use_container_width=True)
            st.write(f"**Potenziale Offensivo (Incrociato: {exp_gf_h:.2f} - {exp_gf_a:.2f})**")
            st.plotly_chart(
                utils.crea_grafico_confronto(s_h[h_type]['GF'], s_a[a_type]['GF'], "Media Gol Fatti", m['Casa'], m['Ospite']),
                use_container_width=True
            )

        with t2:
            st.markdown("### Analisi Incrociata dei Tiri")
            st.dataframe(
                utils.crea_dataframe_confronto(['Tiri_Fatti', 'Tiri_Subiti', 'Porta_Fatti', 'Porta_Subiti'], s_h, s_a, m['Casa'], m['Ospite']),
                use_container_width=True
            )
            c1, c2 = st.columns(2)
            c1.write(f"**Tiri Previsti {m['Casa']}: {exp_tiri_h:.1f}**")
            c1.plotly_chart(
                utils.crea_grafico_confronto(
                    s_h[h_type]['Tiri_Fatti'], s_a[a_type]['Tiri_Subiti'],
                    "Tiri Fatti vs Subiti", m['Casa'], f"Subiti {m['Ospite']}", '#00ff85', '#ff4b4b'
                ),
                use_container_width=True
            )
            c2.write(f"**Tiri Previsti {m['Ospite']}: {exp_tiri_a:.1f}**")
            c2.plotly_chart(
                utils.crea_grafico_confronto(
                    s_a[a_type]['Tiri_Fatti'], s_h[h_type]['Tiri_Subiti'],
                    "Tiri Fatti vs Subiti", m['Ospite'], f"Subiti {m['Casa']}", '#3d5afe', '#ff4b4b'
                ),
                use_container_width=True
            )

        with t3:
            st.dataframe(
                utils.crea_dataframe_confronto(['Corner_Fatti', 'Corner_Subiti'], s_h, s_a, m['Casa'], m['Ospite']),
                use_container_width=True
            )
            st.plotly_chart(
                utils.crea_grafico_confronto(
                    s_h[h_type]['Corner_Fatti'], s_a[a_type]['Corner_Fatti'],
                    "Media Corner Fatti", m['Casa'], m['Ospite']
                ),
                use_container_width=True
            )

        with t4:
            st.dataframe(
                utils.crea_dataframe_confronto(['Gialli'], s_h, s_a, m['Casa'], m['Ospite']),
                use_container_width=True
            )
            st.plotly_chart(
                utils.crea_grafico_confronto(
                    s_h[h_type]['Gialli'], s_a[a_type]['Gialli'],
                    "Media Cartellini Gialli", m['Casa'], m['Ospite'], '#f1c40f', '#e67e22'
                ),
                use_container_width=True
            )

     else:
        st.error("⚠️ Squadre non trovate nel database storico. Controlla il Mapping in config.py.")
        with st.expander("Debug nomi squadre"):
            st.write(f"Casa API: `{m['Casa']}` | Ospite API: `{m['Ospite']}`")
            if codice_csv is None:
                standings_dbg, df_eu_dbg, err_dbg = utils.scarica_statistiche_coppe_europee(codice_api)
                if err_dbg:
                    st.info(err_dbg)
                if standings_dbg:
                    st.write("**Squadre trovate in Classifica Coppa (API):**", sorted(list(standings_dbg.keys())))
                if df_eu_dbg is not None and not df_eu_dbg.empty:
                    st.write("**Squadre disponibili nei CSV Nazionali:**", sorted(df_eu_dbg['HomeTeam'].dropna().unique().tolist()))
