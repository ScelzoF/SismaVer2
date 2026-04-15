import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

def _get_tz():
    now = datetime.now()
    y = now.year
    dst_start = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
    dst_end   = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
    is_dst = dst_start <= now.replace(tzinfo=None) < dst_end
    return timezone(timedelta(hours=2 if is_dst else 1))

FUSO_ORARIO_ITALIA = _get_tz()

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_last_quakes():
    try:
        start = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={start}&minmag=1.5&limit=5&orderby=time"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            events = []
            for f in data.get("features", []):
                p = f.get("properties", {})
                g = f.get("geometry", {}).get("coordinates", [])
                t = p.get("time")
                if isinstance(t, int):
                    dt = datetime.fromtimestamp(t / 1000.0, FUSO_ORARIO_ITALIA)
                else:
                    dt = datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(FUSO_ORARIO_ITALIA)
                events.append({
                    "mag": p.get("mag", "—"),
                    "luogo": p.get("place", "N/D"),
                    "ora": dt.strftime("%d/%m %H:%M"),
                    "prof": round(g[2], 1) if len(g) > 2 else "—",
                })
            return events
    except Exception:
        pass
    return []

@st.cache_data(ttl=600, show_spinner=False)
def _fetch_volcano_activity():
    vulcani = {
        "Etna":         (37.755, 14.995, 0.15),
        "Stromboli":    (38.789, 15.213, 0.10),
        "Campi Flegrei":(40.827, 14.139, 0.12),
        "Vesuvio":      (40.821, 14.426, 0.08),
    }
    result = {}
    try:
        start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        for name, (lat, lon, rad) in vulcani.items():
            url = (f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                   f"&starttime={start}&minmag=0.5&lat={lat}&lon={lon}&maxradius={rad}&limit=20")
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    n = len(r.json().get("features", []))
                    result[name] = n
                else:
                    result[name] = None
            except Exception:
                result[name] = None
    except Exception:
        pass
    return result

def show():
    query_params = st.query_params

    if 'seo_endpoint' in query_params:
        ep = query_params.get('seo_endpoint')
        if ep == 'sitemap':
            try:
                from modules.seo_utils import serve_sitemap_xml
                content = serve_sitemap_xml()
                st.download_button("Scarica Sitemap XML", data=content,
                                   file_name="sitemap.xml", mime="application/xml",
                                   key="sitemap_dl")
                st.code(content, language="xml")
            except ImportError:
                pass
            return
        elif ep == 'robots':
            try:
                from modules.seo_utils import serve_robots_txt
                content = serve_robots_txt()
                st.download_button("Scarica Robots.txt", data=content,
                                   file_name="robots.txt", mime="text/plain",
                                   key="robots_dl")
                st.code(content, language="text")
            except ImportError:
                pass
            return

    ora = datetime.now(FUSO_ORARIO_ITALIA)

    st.title("🇮🇹 SismaVer2 — Monitoraggio Nazionale")
    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;margin-top:-12px;'>"
        f"Sistema integrato di monitoraggio rischi naturali · "
        f"Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> (IT)</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col_q, col_v = st.columns(2, gap="large")

    with col_q:
        st.subheader("🌊 Ultimi terremoti in Italia")
        with st.spinner("Caricamento dati INGV..."):
            quakes = _fetch_last_quakes()
        if quakes:
            for q in quakes:
                mag = q["mag"]
                color = "#EF4444" if mag >= 4 else "#F59E0B" if mag >= 3 else "#10B981"
                st.markdown(
                    f"<div style='border-left:4px solid {color};padding:6px 10px;"
                    f"margin:4px 0;background:#F8FAFC;border-radius:0 4px 4px 0;'>"
                    f"<b style='color:{color};font-size:1.1rem;'>M {mag}</b> &nbsp;"
                    f"<span style='color:#334155;'>{q['luogo']}</span><br>"
                    f"<small style='color:#94A3B8;'>⏱ {q['ora']} &nbsp;·&nbsp; "
                    f"🔻 prof. {q['prof']} km</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Dati INGV temporaneamente non disponibili.")
        st.caption("Fonte: INGV FDSN · soglia M≥1.5 · ultimi 2 giorni")

    with col_v:
        st.subheader("🌋 Attività vulcanica (7 giorni)")
        with st.spinner("Controllo attività vulcani..."):
            vact = _fetch_volcano_activity()
        if vact:
            for name, n in vact.items():
                if n is None:
                    badge = "⚫ N/D"
                    color = "#94A3B8"
                elif n == 0:
                    badge = "🟢 Silente"
                    color = "#10B981"
                elif n < 5:
                    badge = f"🟡 {n} eventi"
                    color = "#F59E0B"
                else:
                    badge = f"🔴 {n} eventi"
                    color = "#EF4444"
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:6px 10px;margin:4px 0;background:#F8FAFC;"
                    f"border-radius:4px;border:1px solid #E2E8F0;'>"
                    f"<span style='font-weight:600;color:#1E293B;'>{name}</span>"
                    f"<span style='color:{color};font-weight:500;'>{badge}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Dati vulcani temporaneamente non disponibili.")
        st.caption("Fonte: INGV FDSN · eventi M≥0.5 nelle aree vulcaniche")

    st.markdown("---")

    st.subheader("🔍 Cosa puoi fare con SismaVer2")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        **🌊 Monitoraggio Sismico**  
        Dati in tempo reale da INGV per tutte le regioni italiane. Filtro per regione, mappa interattiva e grafici.

        **🌋 Vulcani**  
        Attività di Etna, Vesuvio, Stromboli, Campi Flegrei, Isola di Vulcano e altri.
        """)
    with c2:
        st.markdown("""
        **🌦 Meteo**  
        Condizioni attuali e previsioni 7 giorni per qualsiasi comune italiano. Nessuna API key richiesta.

        **🚨 Emergenza**  
        Mappa punti di raccolta e strutture di emergenza per ogni regione.
        """)
    with c3:
        st.markdown("""
        **💬 Chat Pubblica**  
        Segnalazioni e comunicazioni tra cittadini. Moderazione automatica multi-livello.

        **📱 Segnala Evento**  
        Segnala terremoti, frane, alluvioni o altri eventi direttamente dalla app.
        """)

    st.markdown("---")

    col_s, col_i = st.columns([2, 1])
    with col_s:
        st.metric("Vulcani monitorati", "9")
        st.metric("Stazioni sismiche INGV", "500+")
        st.metric("Aggiornamento dati", "Ogni 5 min")
    with col_i:
        st.info(
            "**SismaVer2** è l'evoluzione nazionale di "
            "[sismocampania.streamlit.app](https://sismocampania.streamlit.app).  \n"
            "Sviluppato da **Fabio Scelzo** · meteotorre@gmail.com"
        )
