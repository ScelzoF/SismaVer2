"""
rischi_allerte.py — Monitoraggio live allerte e rischi per SismaVer2
Fonti:
  • INGV FDSN  — eventi sismici Italia/Mediterraneo in tempo reale
  • EMSC       — eventi sismici mediterraneo (cross-check)
  • MeteoAlarm — allerte meteo ufficiali per l'Italia (feed Atom)
  • Open-Meteo — previsioni orarie per rischio meteo secondario
  • CAT-INGV   — link ufficiale allerta tsunami
"""

import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH = True
except ImportError:
    _AUTOREFRESH = False


# ─── Fuso orario DST-aware ─────────────────────────────────────────────────
def _get_tz():
    n = datetime.now()
    y = n.year
    ds = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
    de = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if ds <= n < de else 1))

FUSO_IT = _get_tz()


# ─── Fetch helpers (tutte con cache) ───────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)   # 2 minuti per sismica
def _ingv_recent(min_mag: float, days: float, lat_min=35.0, lat_max=48.0,
                 lon_min=5.0, lon_max=20.0):
    """Recupera eventi INGV nel riquadro geografico dato."""
    start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    url = (f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
           f"&starttime={start}&minmag={min_mag}"
           f"&minlat={lat_min}&maxlat={lat_max}&minlon={lon_min}&maxlon={lon_max}"
           f"&limit=50&orderby=time")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json().get("features", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=120, show_spinner=False)
def _emsc_mediterranean(min_mag: float, days: float):
    """Recupera eventi EMSC nel Mediterraneo (area estesa, incluso Mar Nero)."""
    start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    url = (f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
           f"&starttime={start}&minmag={min_mag}"
           f"&minlat=28.0&maxlat=48.0&minlon=-10.0&maxlon=42.0"
           f"&limit=30&orderby=time")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            return data.get("features", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=1800, show_spinner=False)  # 30 min per meteo
def _meteoalarm_italy():
    """Fetch del feed MeteoAlarm per l'Italia (Atom XML)."""
    urls = [
        "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-italy",
        "https://feeds.meteoalarm.org/api/v1/warnings/feeds-italy/",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "SismaVer2/2.5"})
            if r.status_code == 200 and len(r.content) > 200:
                return r.content
        except Exception:
            pass
    return None


@st.cache_data(ttl=300, show_spinner=False)
def _ingv_vulcani_counts():
    """Conta eventi sismici recenti attorno ai principali vulcani italiani."""
    vulcani = {
        "Etna":          (37.755, 14.995, 0.15),
        "Stromboli":     (38.789, 15.213, 0.10),
        "Vulcano":       (38.404, 14.962, 0.08),
        "Campi Flegrei": (40.827, 14.139, 0.12),
        "Vesuvio":       (40.821, 14.426, 0.08),
        "Ischia":        (40.731, 13.897, 0.07),
        "Pantelleria":   (36.769, 12.021, 0.10),
    }
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    result = {}

    def _fetch(name, lat, lon, rad):
        url = (f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
               f"&starttime={start}&minmag=0.5&lat={lat}&lon={lon}&maxradius={rad}&limit=50")
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                return name, len(r.json().get("features", []))
        except Exception:
            pass
        return name, None

    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(_fetch, n, la, lo, ra): n for n, (la, lo, ra) in vulcani.items()}
        for f in as_completed(futures):
            name, count = f.result()
            result[name] = count
    return result


# ─── Parsing e classificazione ─────────────────────────────────────────────

def _parse_event(feat):
    """Estrae mag, luogo, ora, lat, lon da una feature GeoJSON."""
    p = feat.get("properties", {})
    g = feat.get("geometry", {}).get("coordinates", [])
    t = p.get("time") or p.get("lastupdate")
    mag = p.get("mag") or p.get("magnitude") or 0
    try:
        mag = float(mag)
    except Exception:
        mag = 0.0
    luogo = p.get("place") or p.get("flynn_region") or "N/D"
    depth = round(float(g[2]), 1) if len(g) > 2 else None
    lat = float(g[1]) if len(g) > 1 else None
    lon = float(g[0]) if len(g) > 0 else None
    ora_str = "N/D"
    if t:
        try:
            if isinstance(t, (int, float)):
                dt = datetime.fromtimestamp(t / 1000.0, FUSO_IT)
            else:
                dt = datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(FUSO_IT)
            ora_str = dt.strftime("%d/%m %H:%M")
        except Exception:
            ora_str = str(t)[:16]
    return {"mag": mag, "luogo": luogo, "ora": ora_str, "depth": depth, "lat": lat, "lon": lon}


def _tsunami_level(events_med):
    """
    Calcola livello tsunami dal più forte evento mediterraneo recente.
    Non è un sistema ufficiale — è un indicatore derivato.
    """
    if not events_med:
        return 0, "🟢 Nessun rischio rilevato", "Nessun evento M≥5.5 nel Mediterraneo nelle ultime 24 ore.", "#10B981"
    best = max(events_med, key=lambda f: float(f.get("properties", {}).get("mag") or 0))
    ev = _parse_event(best)
    m = ev["mag"]
    if m >= 7.0:
        return 4, "🔴 ALLERTA TSUNAMI", f"Evento M{m:.1f} rilevato nel Mediterraneo ({ev['luogo']}, {ev['ora']}). Monitorare CAT-INGV.", "#EF4444"
    elif m >= 6.0:
        return 3, "🟠 ATTENZIONE TSUNAMI", f"Evento M{m:.1f} nel Mediterraneo ({ev['luogo']}, {ev['ora']}). Verificare aggiornamenti CAT-INGV.", "#F97316"
    elif m >= 5.5:
        return 2, "🟡 SORVEGLIANZA", f"Evento M{m:.1f} nel Mediterraneo ({ev['luogo']}, {ev['ora']}). Situazione sotto osservazione.", "#EAB308"
    else:
        return 1, "🟢 Livello normale", f"Evento più forte M{m:.1f} — sotto soglia tsunami ({ev['luogo']}).", "#10B981"


def _seismic_level(events_ita):
    """Calcola livello allerta sismica per il territorio italiano."""
    if not events_ita:
        return 0, "🟢 Attività sismica nella norma", "Nessun evento M≥3.0 registrato nelle ultime 48 ore.", "#10B981"
    best = max(events_ita, key=lambda f: float(f.get("properties", {}).get("mag") or 0))
    ev = _parse_event(best)
    m = ev["mag"]
    if m >= 5.0:
        return 4, "🔴 EVENTO FORTE", f"Evento M{m:.1f} in Italia ({ev['luogo']}, {ev['ora']}). Seguire aggiornamenti ufficiali.", "#EF4444"
    elif m >= 4.0:
        return 3, "🟠 SCOSSE SIGNIFICATIVE", f"Evento M{m:.1f} registrato ({ev['luogo']}, {ev['ora']}).", "#F97316"
    elif m >= 3.0:
        return 2, "🟡 ATTIVITÀ MODERATA", f"Evento M{m:.1f} rilevato ({ev['luogo']}, {ev['ora']}).", "#EAB308"
    return 1, "🟢 Attività sismica nella norma", f"Massimo evento M{m:.1f} nelle ultime 48 ore.", "#10B981"


def _vulcan_level(count):
    """Classifica livello attività vulcanica da conteggio eventi 7 giorni."""
    if count is None:
        return "⚫ N/D", "#94A3B8"
    elif count == 0:
        return "🟢 Silente", "#10B981"
    elif count < 5:
        return f"🟡 {count} eventi", "#EAB308"
    elif count < 15:
        return f"🟠 {count} eventi", "#F97316"
    else:
        return f"🔴 {count} eventi", "#EF4444"


def _traduci_allerta(testo: str) -> str:
    """Traduce il testo MeteoAlarm dall'inglese all'italiano."""
    sostituzioni = [
        ("Yellow Thunderstorm Warning",   "Allerta Gialla Temporali"),
        ("Yellow Rain Warning",           "Allerta Gialla Pioggia"),
        ("Yellow Wind Warning",           "Allerta Gialla Vento"),
        ("Yellow Snow/Ice Warning",       "Allerta Gialla Neve/Ghiaccio"),
        ("Yellow Fog Warning",            "Allerta Gialla Nebbia"),
        ("Yellow Coastal Event Warning",  "Allerta Gialla Maremoto"),
        ("Yellow Flooding Warning",       "Allerta Gialla Alluvioni"),
        ("Yellow Forest Fire Warning",    "Allerta Gialla Incendi"),
        ("Orange Thunderstorm Warning",   "Allerta Arancione Temporali"),
        ("Orange Rain Warning",           "Allerta Arancione Pioggia"),
        ("Orange Wind Warning",           "Allerta Arancione Vento"),
        ("Orange Snow/Ice Warning",       "Allerta Arancione Neve/Ghiaccio"),
        ("Orange Flooding Warning",       "Allerta Arancione Alluvioni"),
        ("Orange Forest Fire Warning",    "Allerta Arancione Incendi"),
        ("Red Thunderstorm Warning",      "Allerta Rossa Temporali"),
        ("Red Rain Warning",              "Allerta Rossa Pioggia"),
        ("Red Wind Warning",              "Allerta Rossa Vento"),
        ("Red Flooding Warning",          "Allerta Rossa Alluvioni"),
        ("issued for Italy - ",           "— "),
        ("issued for Italy",              ""),
        ("Thunderstorm Warning",          "Allerta Temporali"),
        ("Rain Warning",                  "Allerta Pioggia"),
        ("Wind Warning",                  "Allerta Vento"),
        ("Snow/Ice Warning",              "Allerta Neve/Ghiaccio"),
        ("Flooding Warning",              "Allerta Alluvioni"),
        ("Forest Fire Warning",           "Allerta Incendi Boschivi"),
        ("Fog Warning",                   "Allerta Nebbia"),
        ("Avalanche Warning",             "Allerta Valanghe"),
        ("Coastal Event Warning",         "Allerta Evento Costiero"),
        ("Warning",                       "Allerta"),
        ("Advisory",                      "Avviso"),
        ("Watch",                         "Sorveglianza"),
        ("Yellow",                        "Giallo"),
        ("Orange",                        "Arancione"),
        ("Red",                           "Rosso"),
        ("Sardinia",                      "Sardegna"),
        ("Sicily",                        "Sicilia"),
        ("Tuscany",                       "Toscana"),
        ("Liguria",                       "Liguria"),
        ("Lombardy",                      "Lombardia"),
        ("Piedmont",                      "Piemonte"),
        ("Veneto",                        "Veneto"),
        ("Campania",                      "Campania"),
        ("Apulia",                        "Puglia"),
        ("Calabria",                      "Calabria"),
        ("Basilicata",                    "Basilicata"),
        ("Abruzzo",                       "Abruzzo"),
        ("Molise",                        "Molise"),
        ("Marche",                        "Marche"),
        ("Umbria",                        "Umbria"),
        ("Lazio",                         "Lazio"),
        ("Emilia-Romagna",                "Emilia-Romagna"),
        ("Trentino-South Tyrol",          "Trentino-Alto Adige"),
        ("Friuli-Venezia Giulia",         "Friuli-Venezia Giulia"),
        ("Valle d'Aosta",                 "Valle d'Aosta"),
    ]
    for en, it in sostituzioni:
        testo = testo.replace(en, it)
    return testo.strip()


def _parse_meteoalarm(raw_bytes):
    """Estrae allerte dal feed Atom di MeteoAlarm."""
    try:
        root = ET.fromstring(raw_bytes)
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "cap":  "urn:oasis:names:tc:emergency:cap:1.2"}
        alerts = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            updated = (entry.findtext("atom:updated", default="", namespaces=ns) or "")[:16]
            # Traduzione in italiano
            title_it = _traduci_allerta(title)
            summary_it = _traduci_allerta(summary)
            # Cerca livello di severità nel testo originale (inglese)
            txt = (title + summary).lower()
            if "red" in txt or "extreme" in txt:
                color, lvl = "#EF4444", "🔴 Rosso"
            elif "orange" in txt or "severe" in txt:
                color, lvl = "#F97316", "🟠 Arancione"
            elif "yellow" in txt or "moderate" in txt:
                color, lvl = "#EAB308", "🟡 Giallo"
            elif "green" in txt:
                color, lvl = "#10B981", "🟢 Verde"
            else:
                color, lvl = "#94A3B8", "⚫ N/D"
            if title:
                alerts.append({"title": title_it, "summary": summary_it[:200],
                                "updated": updated, "color": color, "livello": lvl})
        return alerts[:10]
    except Exception:
        return []


# ─── UI principale ─────────────────────────────────────────────────────────

def show():
    ora = datetime.now(FUSO_IT)

    from modules.banner_utils import banner_allerte
    banner_allerte()
    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;margin-top:0;'>"
        f"Dashboard live di allerte sismiche, tsunami, meteo e vulcaniche · "
        f"Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> (IT) · "
        f"<i>Aggiornamento automatico ogni 2 min</i></p>",
        unsafe_allow_html=True,
    )

    # Auto-refresh ogni 2 minuti (JavaScript nativo)
    if _AUTOREFRESH:
        st_autorefresh(interval=120_000, limit=None, key="allerte_autorefresh")

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        if st.button("🔄 Aggiorna ora"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # ── Caricamento dati in parallelo ──────────────────────────────────────
    with st.spinner("Caricamento allerte in corso…"):
        with ThreadPoolExecutor(max_workers=4) as ex:
            f_med   = ex.submit(_emsc_mediterranean, 5.5, 1.0)
            f_ita   = ex.submit(_ingv_recent, 3.0, 2.0)
            f_volc  = ex.submit(_ingv_vulcani_counts)
            f_meteo = ex.submit(_meteoalarm_italy)

        ev_med   = f_med.result()
        ev_ita   = f_ita.result()
        vc       = f_volc.result()
        ma_raw   = f_meteo.result()

    # ── SEZIONE 1: Banner stato generale ───────────────────────────────────
    ts_lvl, ts_label, ts_desc, ts_color = _tsunami_level(ev_med)
    ss_lvl, ss_label, ss_desc, ss_color = _seismic_level(ev_ita)

    col_ts, col_ss = st.columns(2)
    with col_ts:
        st.markdown(
            f"<div style='background:{ts_color}18;border-left:5px solid {ts_color};"
            f"padding:14px 18px;border-radius:6px;margin-bottom:8px;'>"
            f"<h3 style='margin:0;color:{ts_color};font-size:1.1rem;'>🌊 TSUNAMI</h3>"
            f"<p style='font-weight:700;color:{ts_color};margin:4px 0;'>{ts_label}</p>"
            f"<small style='color:#475569;'>{ts_desc}</small></div>",
            unsafe_allow_html=True,
        )
        st.caption("[📡 CAT-INGV — Centro Allerta Tsunami ufficiale](https://www.ingv.it/cat/)")

    with col_ss:
        st.markdown(
            f"<div style='background:{ss_color}18;border-left:5px solid {ss_color};"
            f"padding:14px 18px;border-radius:6px;margin-bottom:8px;'>"
            f"<h3 style='margin:0;color:{ss_color};font-size:1.1rem;'>🌊 SISMICA ITALIA</h3>"
            f"<p style='font-weight:700;color:{ss_color};margin:4px 0;'>{ss_label}</p>"
            f"<small style='color:#475569;'>{ss_desc}</small></div>",
            unsafe_allow_html=True,
        )
        st.caption("[📡 INGV — Monitoraggio sismico nazionale](https://cnt.rm.ingv.it/)")

    st.markdown("---")

    # ── SEZIONE 2: Tab dettaglio ────────────────────────────────────────────
    tab_ts, tab_ss, tab_vc, tab_mt, tab_idr = st.tabs([
        "🌊 Tsunami", "🌊 Sismica", "🌋 Vulcani", "🌦️ Meteo", "🏔️ Idrogeologico"
    ])

    # ─ Tab Tsunami ────────────────────────────────────────────────────────
    with tab_ts:
        st.subheader("🌊 Allerta Tsunami — Mediterraneo")

        st.info(
            "**Nota**: Questo pannello mostra un indicatore derivato da dati sismici EMSC in tempo reale. "
            "Per l'allerta ufficiale italiana fare sempre riferimento a **[CAT-INGV](https://www.ingv.it/cat/)**."
        )

        st.markdown(
            f"<div style='background:{ts_color}22;border:2px solid {ts_color};"
            f"border-radius:8px;padding:16px 20px;text-align:center;margin:10px 0;'>"
            f"<h2 style='color:{ts_color};margin:0;'>{ts_label}</h2>"
            f"<p style='color:#334155;margin:8px 0 0;'>{ts_desc}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### 📋 Scala di allerta tsunami (CAT-INGV)")
        cols = st.columns(4)
        livelli = [
            ("🟢 Livello 0", "Nessun evento rilevante nel Mediterraneo", "#10B981"),
            ("🟡 Sorveglianza", "M≥5.5 in mare. Nessuna anomalia attesa ma monitoraggio attivo.", "#EAB308"),
            ("🟠 Attenzione", "M≥6.0 in mare. Possibile perturbazione locale. Allontanarsi dalle spiagge.", "#F97316"),
            ("🔴 Allerta", "M≥7.0. Tsunami probabile. Evacuare le coste immediatamente.", "#EF4444"),
        ]
        for col, (titolo, desc, col_c) in zip(cols, livelli):
            with col:
                st.markdown(
                    f"<div style='background:{col_c}18;border:1px solid {col_c};"
                    f"border-radius:6px;padding:10px;text-align:center;height:130px;'>"
                    f"<b style='color:{col_c};'>{titolo}</b><br>"
                    f"<small style='color:#475569;'>{desc}</small></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("### 🔎 Ultimi eventi M≥5.5 nel Mediterraneo (24h)")
        if ev_med:
            for feat in ev_med[:8]:
                ev = _parse_event(feat)
                m = ev["mag"]
                color = "#EF4444" if m >= 6.5 else "#F97316" if m >= 6.0 else "#EAB308" if m >= 5.5 else "#94A3B8"
                depth_txt = f"prof. {ev['depth']} km" if ev['depth'] else ""
                st.markdown(
                    f"<div style='border-left:4px solid {color};padding:6px 12px;"
                    f"margin:4px 0;background:#F8FAFC;border-radius:0 4px 4px 0;'>"
                    f"<b style='color:{color};font-size:1.05rem;'>M {m:.1f}</b> &nbsp;"
                    f"<span style='color:#334155;'>{ev['luogo']}</span><br>"
                    f"<small style='color:#94A3B8;'>⏱ {ev['ora']} · {depth_txt}</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("✅ Nessun evento M≥5.5 registrato nel Mediterraneo nelle ultime 24 ore.")

        with st.expander("ℹ️ Cosa fare in caso di allerta tsunami"):
            st.markdown("""
            1. **Non aspettare** l'onda: se avverti un forte terremoto sulla costa o vedi il mare ritirarsi anomalamente, allontanati subito
            2. **Raggiungi quote elevate**: almeno 30 m sul livello del mare o 1 km dalla riva
            3. **Non tornare** sulla costa fino a cessata allerta ufficiale
            4. **Ascolta la radio** (RAI Radio 1 trasmette allerte ufficiali) o segui [CAT-INGV](https://www.ingv.it/cat/)
            5. **Prima ondata ≠ ultima**: attendi almeno 1 ora dall'ultima scossa prima di scendere
            """)

    # ─ Tab Sismica ────────────────────────────────────────────────────────
    with tab_ss:
        st.subheader("🌊 Attività Sismica — Italia (ultimi 2 giorni, M≥3.0)")

        if ev_ita:
            evs = [_parse_event(f) for f in ev_ita]
            evs.sort(key=lambda x: -x["mag"])
            for ev in evs[:15]:
                m = ev["mag"]
                color = "#EF4444" if m >= 5.0 else "#F97316" if m >= 4.0 else "#EAB308" if m >= 3.0 else "#94A3B8"
                depth_txt = f"prof. {ev['depth']} km" if ev['depth'] else ""
                st.markdown(
                    f"<div style='border-left:4px solid {color};padding:6px 12px;"
                    f"margin:4px 0;background:#F8FAFC;border-radius:0 4px 4px 0;'>"
                    f"<b style='color:{color};font-size:1.05rem;'>M {m:.1f}</b> &nbsp;"
                    f"<span style='color:#334155;'>{ev['luogo']}</span><br>"
                    f"<small style='color:#94A3B8;'>⏱ {ev['ora']} · {depth_txt}</small></div>",
                    unsafe_allow_html=True,
                )
            st.caption("Fonte: INGV FDSN · aggiornamento ogni 2 minuti")
        else:
            st.success("✅ Nessun evento M≥3.0 registrato in Italia nelle ultime 48 ore.")

        st.markdown("---")
        st.markdown("### 📎 Soglie di riferimento")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("🟢 **M < 3.0**\nNormale attività microsismica — non avvertita dalla popolazione")
        with c2:
            st.markdown("🟡 **M 3.0 – 3.9**\nAvvertita vicino epicentro — danni improbabili")
        with c3:
            st.markdown("🟠 **M 4.0 – 4.9**\nAvvertita in ampia zona — danni leggeri possibili")
        with c4:
            st.markdown("🔴 **M ≥ 5.0**\nEvento forte — danni probabili — seguire Protezione Civile")

    # ─ Tab Vulcani ───────────────────────────────────────────────────────
    with tab_vc:
        st.subheader("🌋 Attività Vulcanica — Ultimi 7 giorni")
        st.markdown("Numero di eventi sismici M≥0.5 nell'area di ciascun vulcano (fonte INGV FDSN)")

        if vc:
            for name, count in vc.items():
                label, col_c = _vulcan_level(count)
                ingv_links = {
                    "Etna": "https://www.ct.ingv.it/",
                    "Stromboli": "https://www.ct.ingv.it/",
                    "Vulcano": "https://www.ct.ingv.it/",
                    "Campi Flegrei": "https://www.ov.ingv.it/",
                    "Vesuvio": "https://www.ov.ingv.it/",
                    "Ischia": "https://www.ov.ingv.it/",
                    "Pantelleria": "https://www.ct.ingv.it/",
                }
                link = ingv_links.get(name, "https://www.ingv.it/")
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:10px 16px;margin:5px 0;background:#F8FAFC;"
                    f"border-radius:6px;border:1px solid #E2E8F0;'>"
                    f"<div><b style='font-size:1.05rem;color:#1E293B;'>🌋 {name}</b></div>"
                    f"<div><span style='color:{col_c};font-weight:600;font-size:1rem;'>{label}</span>"
                    f"&nbsp;<a href='{link}' target='_blank' style='font-size:0.8rem;color:#64748B;'>INGV →</a></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.warning("Dati vulcanici temporaneamente non disponibili.")

        st.markdown("---")
        st.info(
            "**Scala livelli vulcanici INGV** (semplificata): 🟢 Nessuna attività rilevante · "
            "🟡 Attività bassa (< 5 eventi/7gg) · 🟠 Attività moderata (5-15 eventi) · "
            "🔴 Attività elevata (> 15 eventi)"
        )
        st.markdown("""
        **Bollettini ufficiali settimanali:**
        - [Osservatorio Etneo (Etna, Stromboli, Vulcano)](https://www.ct.ingv.it/)
        - [Osservatorio Vesuviano (Vesuvio, Campi Flegrei, Ischia)](https://www.ov.ingv.it/)
        - [Bollettini settimanali INGV](https://www.ingv.it/it/vulcani/bollettini)
        """)

    # ─ Tab Meteo ─────────────────────────────────────────────────────────
    with tab_mt:
        st.subheader("🌦️ Allerte Meteo — Italia")

        ma_alerts = []
        if ma_raw:
            ma_alerts = _parse_meteoalarm(ma_raw)

        if ma_alerts:
            st.markdown(f"**{len(ma_alerts)} allerte attive da MeteoAlarm:**")
            for a in ma_alerts:
                st.markdown(
                    f"<div style='border-left:4px solid {a['color']};padding:8px 14px;"
                    f"margin:5px 0;background:#F8FAFC;border-radius:0 4px 4px 0;'>"
                    f"<b style='color:{a['color']};'>{a['livello']}</b> — {a['title']}<br>"
                    f"<small style='color:#94A3B8;'>{a['summary']}</small><br>"
                    f"<small style='color:#CBD5E1;'>Aggiornato: {a['updated']}</small>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.caption("Fonte: MeteoAlarm (rete EUMETNET) · aggiornamento ogni 30 min")
        else:
            st.info("Feed MeteoAlarm temporaneamente non disponibile o nessuna allerta attiva in questo momento.")

        st.markdown("---")
        st.markdown("### 🔗 Fonti ufficiali allerta meteo")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            - [🌍 MeteoAlarm Italia](https://www.meteoalarm.org/it/live/region/#IT)
            - [🌩️ Protezione Civile — Allerta Meteo](https://mappe.protezionecivile.gov.it/it/)
            - [📡 Aeronautica Militare CNMCA](http://www.meteoam.it/)
            """)
        with c2:
            st.markdown("""
            - [🌦️ ARPA Lombardia](https://www.arpalombardia.it/meteo/previsioni-meteo/)
            - [🌦️ ARPAE Emilia-Romagna](https://allertameteo.regione.emilia-romagna.it/)
            - [🌦️ Centro Funzionale DPC](https://mappe.protezionecivile.gov.it/)
            """)

        st.markdown("### 📋 Scala colori allerta meteo Italia (DPC)")
        cs = st.columns(4)
        livelli_mt = [
            ("🟢 Verde", "Nessuna allerta. Fenomeni meteo ordinari.", "#10B981"),
            ("🟡 Giallo", "Criticità ordinaria. Prestare attenzione.", "#EAB308"),
            ("🟠 Arancione", "Criticità moderata. Possibili danni locali.", "#F97316"),
            ("🔴 Rosso", "Criticità elevata. Pericolo per l'incolumità.", "#EF4444"),
        ]
        for col, (titolo, desc, c) in zip(cs, livelli_mt):
            with col:
                st.markdown(
                    f"<div style='background:{c}18;border:1px solid {c};"
                    f"border-radius:6px;padding:10px;text-align:center;'>"
                    f"<b style='color:{c};'>{titolo}</b><br>"
                    f"<small style='color:#475569;'>{desc}</small></div>",
                    unsafe_allow_html=True,
                )

    # ─ Tab Idrogeologico ─────────────────────────────────────────────────
    with tab_idr:
        st.subheader("🏔️ Rischio Idrogeologico e Idraulico")

        st.warning(
            "**Nota**: Non esiste un'API pubblica in tempo reale per il rischio idrogeologico nazionale. "
            "I dati ufficiali sono pubblicati da ISPRA e dalle Protezioni Civili regionali. "
            "Di seguito i link diretti alle fonti aggiornate."
        )

        st.markdown("### 🔗 Fonti ufficiali aggiornate in tempo reale")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
            **🌍 Nazionali:**
            - [Mappa Allerta DPC (ufficiale)](https://mappe.protezionecivile.gov.it/it/)
            - [IdroGEO — ISPRA frane e alluvioni](https://idrogeo.isprambiente.it/)
            - [ReNDiS — ISPRA dissesto idrogeologico](https://rendis.isprambiente.it/)
            - [AVI — Archivio Nazionale Dissesti](http://avi.gndci.cnr.it/)
            """)
        with col_b:
            st.markdown("""
            **🗺️ Mappa rischio PAI (piani di assetto idrogeologico):**
            - [ISPRA — Portale rischio frane](https://www.isprambiente.gov.it/it/temi/suolo-e-territorio/il-dissesto-idrogeologico)
            - [WebGIS ISPRA](https://www.sgi2.isprambiente.it/mapserver/index.html)
            - [Allerta Meteo DPC mappe](https://mappe.protezionecivile.gov.it/)
            """)

        st.markdown("---")
        st.markdown("### 📊 Rischio per macro-area geografica")
        dati_rischio = [
            ("Nordovest (Piemonte, Liguria, VdA)", "Elevato", "Frane alpine, alluvioni Po/Tanaro, eventi lampo costieri", "#F97316"),
            ("Nordest (Veneto, FVG, TAA)", "Alto", "Frane dolomitiche, alluvioni Piave/Adige, acqua alta veneziana", "#F97316"),
            ("Centro (Marche, Umbria, Lazio)", "Elevato", "Frane appenniniche, alluvioni Tevere/Arno, subsidenza costiera", "#EF4444"),
            ("Sud (Campania, Calabria, Basilicata)", "Molto elevato", "Frane, colate rapide (Sarno 1998), fiumare calabresi", "#EF4444"),
            ("Isole (Sicilia, Sardegna)", "Alto", "Alluvioni lampo, frane, erosione costiera", "#F97316"),
            ("Pianura Padana", "Moderato", "Esondazioni Po e tributari, subsidenza, nebbia", "#EAB308"),
        ]
        for zona, livello, rischi, col_c in dati_rischio:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
                f"padding:10px 16px;margin:5px 0;background:#F8FAFC;"
                f"border-radius:6px;border-left:4px solid {col_c};'>"
                f"<div><b style='color:#1E293B;'>{zona}</b><br>"
                f"<small style='color:#64748B;'>{rischi}</small></div>"
                f"<div style='text-align:right;min-width:120px;'>"
                f"<span style='color:{col_c};font-weight:600;'>{livello}</span></div></div>",
                unsafe_allow_html=True,
            )
        st.caption("Dati: ISPRA — classificazione rischio idrogeologico nazionale (aggiornamento annuale)")

    st.markdown("---")
    st.caption(
        "⚠️ Questo pannello è a scopo informativo. "
        "In caso di emergenza seguire sempre le istruzioni ufficiali di Protezione Civile e autorità locali. "
        "Fonte dati: INGV · EMSC · MeteoAlarm · ISPRA · DPC"
    )
