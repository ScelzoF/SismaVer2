"""
qualita_aria.py — Qualità dell'aria in tempo reale per le principali città italiane
Fonte: Open-Meteo Air Quality API (gratuita, nessuna API key)
"""
import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
try:
    from streamlit_autorefresh import st_autorefresh as _sar
    _AR = True
except ImportError:
    _AR = False

def _get_tz():
    n = datetime.now(); y = n.year
    ds = datetime(y,3,31-(datetime(y,3,31).weekday()+1)%7)
    de = datetime(y,10,31-(datetime(y,10,31).weekday()+1)%7)
    return timezone(timedelta(hours=2 if ds<=n<de else 1))

FUSO_IT = _get_tz()

CITTA = {
    "Roma":    (41.8955, 12.4823), "Milano":  (45.4642, 9.1900),
    "Napoli":  (40.8517, 14.2681), "Torino":  (45.0703, 7.6869),
    "Palermo": (38.1157, 13.3613), "Firenze": (43.7696, 11.2558),
    "Bologna": (44.4934, 11.3420), "Venezia": (45.4408, 12.3155),
    "Bari":    (41.1171, 16.8719), "Catania": (37.5079, 15.0830),
    "Genova":  (44.4056, 8.9463),  "Cagliari":(39.2238, 9.1217),
    "Messina": (38.1938, 15.5540), "Verona":  (45.4384, 10.9916),
    "Trieste": (45.6495, 13.7768), "Taranto": (40.4756, 17.2291),
    "Brescia": (45.5416, 10.2118), "Padova":  (45.4064, 11.8768),
    "Parma":   (44.8015, 10.3279), "Reggio Calabria": (38.1112, 15.6476),
}

def _aqi_label(v):
    if v is None: return "N/D", "#94A3B8"
    v = int(v)
    if v <= 20:  return f"Ottima ({v})",     "#22c55e"
    if v <= 40:  return f"Buona ({v})",      "#86efac"
    if v <= 60:  return f"Moderata ({v})",   "#facc15"
    if v <= 80:  return f"Scarsa ({v})",     "#f97316"
    if v <= 100: return f"Pessima ({v})",    "#ef4444"
    return f"Critica ({v})", "#7c3aed"

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_aqi(lat, lon):
    try:
        url = (f"https://air-quality-api.open-meteo.com/v1/air-quality"
               f"?latitude={lat}&longitude={lon}"
               f"&current=european_aqi,pm10,pm2_5,carbon_monoxide,"
               f"nitrogen_dioxide,sulphur_dioxide,ozone"
               f"&timezone=Europe%2FRome")
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            c = r.json().get("current", {})
            return {
                "aqi":  c.get("european_aqi"),
                "pm10": c.get("pm10"),
                "pm25": c.get("pm2_5"),
                "no2":  c.get("nitrogen_dioxide"),
                "o3":   c.get("ozone"),
                "co":   c.get("carbon_monoxide"),
                "so2":  c.get("sulphur_dioxide"),
            }
    except Exception:
        pass
    return {}

def show():
    if _AR:
        _sar(interval=1_800_000, limit=None, key="aria_autorefresh")

    from modules.banner_utils import banner_qualita_aria
    banner_qualita_aria()
    ora = datetime.now(FUSO_IT)
    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;margin-top:0;'>"
        f"Indice EEA (European Air Quality Index) in tempo reale · "
        f"Fonte: Open-Meteo · Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> "
        f"· <i>Auto-aggiornamento ogni 30 min</i></p>",
        unsafe_allow_html=True
    )

    # Legenda
    with st.expander("📊 Legenda Indice AQI europeo"):
        cols = st.columns(6)
        livelli = [
            ("🟢 Ottima", "0–20", "#22c55e"),
            ("🟩 Buona", "21–40", "#86efac"),
            ("🟡 Moderata", "41–60", "#facc15"),
            ("🟠 Scarsa", "61–80", "#f97316"),
            ("🔴 Pessima", "81–100", "#ef4444"),
            ("🟣 Critica", "100+", "#7c3aed"),
        ]
        for i, (l, r, c) in enumerate(livelli):
            cols[i].markdown(f"<div style='background:{c};color:white;padding:6px;border-radius:4px;text-align:center;'><b>{l}</b><br><small>AQI {r}</small></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Selezione città
    citta_scelta = st.selectbox("Seleziona città per dettaglio", ["Tutte le città"] + sorted(CITTA.keys()))

    if citta_scelta != "Tutte le città":
        lat, lon = CITTA[citta_scelta]
        with st.spinner(f"Caricamento dati {citta_scelta}..."):
            d = _fetch_aqi(lat, lon)

        if d:
            aqi_label, aqi_color = _aqi_label(d.get("aqi"))
            st.markdown(f"""
            <div style='background:{aqi_color};color:white;padding:20px;border-radius:10px;text-align:center;margin:10px 0;'>
                <h2 style='margin:0;'>🌬️ {citta_scelta}</h2>
                <h1 style='margin:5px 0;font-size:3rem;'>{aqi_label}</h1>
                <p style='margin:0;opacity:0.9;'>Indice di Qualità dell'Aria Europeo</p>
            </div>
            """, unsafe_allow_html=True)

            c1,c2,c3,c4,c5,c6 = st.columns(6)
            def _m(col, label, val, unit):
                v = f"{val:.1f} {unit}" if val is not None else "N/D"
                col.metric(label, v)
            _m(c1,"PM10",     d.get("pm10"),  "µg/m³")
            _m(c2,"PM2.5",    d.get("pm25"),  "µg/m³")
            _m(c3,"NO₂",      d.get("no2"),   "µg/m³")
            _m(c4,"O₃",       d.get("o3"),    "µg/m³")
            _m(c5,"CO",       d.get("co"),    "µg/m³")
            _m(c6,"SO₂",      d.get("so2"),   "µg/m³")

            st.markdown("---")
            st.subheader("📋 Valori limite OMS (WHO 2021)")
            import pandas as pd
            df_who = pd.DataFrame({
                "Inquinante": ["PM2.5 (media 24h)", "PM10 (media 24h)", "NO₂ (media annua)", "O₃ (media 8h)", "SO₂ (media 24h)"],
                "Limite OMS": ["15 µg/m³", "45 µg/m³", "10 µg/m³", "100 µg/m³", "40 µg/m³"],
                "Limite UE vigente": ["25 µg/m³", "50 µg/m³", "40 µg/m³", "120 µg/m³", "125 µg/m³"],
            })
            st.dataframe(df_who, use_container_width=True, hide_index=True)
        else:
            st.warning("Dati non disponibili per questa città. Riprova tra qualche minuto.")
    else:
        st.subheader("📍 Panoramica qualità aria — tutte le principali città")
        st.info("Caricamento di 20 città in parallelo — potrebbe richiedere alcuni secondi...")

        from concurrent.futures import ThreadPoolExecutor, as_completed
        import pandas as pd

        risultati = {}
        with st.spinner("Recupero dati in corso..."):
            with ThreadPoolExecutor(max_workers=10) as ex:
                futures = {ex.submit(_fetch_aqi, lat, lon): nome for nome, (lat,lon) in CITTA.items()}
                for f in as_completed(futures):
                    nome = futures[f]
                    try:
                        risultati[nome] = f.result()
                    except Exception:
                        risultati[nome] = {}

        rows = []
        for nome in sorted(CITTA.keys()):
            d = risultati.get(nome, {})
            aqi = d.get("aqi")
            label, color = _aqi_label(aqi)
            rows.append({
                "Città": nome,
                "AQI": aqi if aqi is not None else "N/D",
                "Livello": label.split("(")[0].strip(),
                "PM10": f"{d['pm10']:.1f}" if d.get("pm10") is not None else "N/D",
                "PM2.5": f"{d['pm25']:.1f}" if d.get("pm25") is not None else "N/D",
                "NO₂": f"{d['no2']:.1f}" if d.get("no2") is not None else "N/D",
                "_color": color,
            })

        df = pd.DataFrame(rows)

        color_map = df.set_index(df.index)["_color"].to_dict()

        def _style_row(row):
            c = color_map.get(row.name, "#ffffff")
            return [
                f"background-color:{c};color:white;font-weight:600" if col == "Livello" else ""
                for col in row.index
            ]

        display_df = df.drop(columns=["_color"])
        st.dataframe(
            display_df.style.apply(_style_row, axis=1),
            use_container_width=True, height=700, hide_index=True
        )

    st.markdown("---")
    st.caption(
        "Fonte: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) · "
        "Dati basati su modello Copernicus CAMS · Aggiornamento ogni 30 minuti"
    )
