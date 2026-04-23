"""
mappa_rischi.py — Dashboard Allerte Multi-Rischio v4.0
Mostra su mappa le ALLERTE ATTIVE per regione italiana:
  - MeteoAlarm: allerta meteo per regione (colore = livello)
  - EMSC: eventi Mediterraneo significativi M≥4.5 (ultime 24h)
  - EMSC Italia M≥3.0 (ultime 24h) — nuovo metric
  - Vulcani: attività sismica LIVE da INGV FDSN + fallback EMSC (10 vulcani)
  - Rischio incendi: derivato da Open-Meteo (temp/umidità/vento)
  - Heatmap sismica: calore eventi recenti M≥2.0 in Italia (EMSC)
  - Stato allerta tsunami: CAT-INGV
DIFFERENTE da monitoraggio.py (catalogo sismico) e rischi_allerte.py (tab testuali)
"""
import streamlit as st
import requests
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH = True
except ImportError:
    _AUTOREFRESH = False


def _get_tz():
    n = datetime.now(); y = n.year
    ds = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
    de = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if ds <= n.replace(tzinfo=None) < de else 1))

FUSO_IT = _get_tz()

# ── Centroidi regioni italiane (per marker su mappa) ─────────────────────────
_REGIONI = {
    "Abruzzo":               (42.35, 13.40),
    "Basilicata":            (40.50, 16.08),
    "Calabria":              (39.30, 16.34),
    "Campania":              (40.83, 14.25),
    "Emilia-Romagna":        (44.49, 11.34),
    "Friuli-Venezia Giulia": (46.07, 13.23),
    "Lazio":                 (41.89, 12.48),
    "Liguria":               (44.41,  8.95),
    "Lombardia":             (45.47,  9.19),
    "Marche":                (43.62, 13.51),
    "Molise":                (41.56, 14.65),
    "Piemonte":              (45.07,  7.68),
    "Puglia":                (41.12, 16.86),
    "Sardegna":              (39.22,  9.10),
    "Sicilia":               (37.50, 14.00),
    "Toscana":               (43.77, 11.24),
    "Trentino-Alto Adige":   (46.06, 11.12),
    "Umbria":                (43.11, 12.39),
    "Valle d'Aosta":         (45.73,  7.32),
    "Veneto":                (45.44, 12.32),
}

# Alias per parsing MeteoAlarm (le voci del feed usano vari nomi)
_MA_ALIAS = {
    "abruzzo": "Abruzzo", "basilicata": "Basilicata",
    "calabria": "Calabria", "campania": "Campania",
    "emilia": "Emilia-Romagna", "emilia-romagna": "Emilia-Romagna",
    "friuli": "Friuli-Venezia Giulia", "venezia giulia": "Friuli-Venezia Giulia",
    "lazio": "Lazio", "liguria": "Liguria", "lombardia": "Lombardia",
    "marche": "Marche", "molise": "Molise", "piemonte": "Piemonte",
    "puglia": "Puglia", "sardegna": "Sardegna", "sardinia": "Sardegna",
    "sicilia": "Sicilia", "sicily": "Sicilia",
    "toscana": "Toscana", "tuscany": "Toscana",
    "trentino": "Trentino-Alto Adige", "alto adige": "Trentino-Alto Adige",
    "umbria": "Umbria", "valle d'aosta": "Valle d'Aosta", "aosta": "Valle d'Aosta",
    "veneto": "Veneto",
}

_MA_LEVEL_COLOR = {
    "red":    ("#DC2626", "🔴", "Rosso",    4),
    "orange": ("#EA580C", "🟠", "Arancione",3),
    "yellow": ("#D97706", "🟡", "Giallo",   2),
    "green":  ("#16A34A", "🟢", "Verde",    1),
}

# ── 10 vulcani monitorati — sincronizzato con monitoraggio.py e home.py ──────
_VULCANI_COORDS = {
    "Etna":          {"lat": 37.755, "lon": 14.995, "rad": 0.20},
    "Stromboli":     {"lat": 38.789, "lon": 15.213, "rad": 0.12},
    "Campi Flegrei": {"lat": 40.827, "lon": 14.139, "rad": 0.15},
    "Vesuvio":       {"lat": 40.821, "lon": 14.426, "rad": 0.10},
    "Vulcano":       {"lat": 38.404, "lon": 14.962, "rad": 0.12},
    "Ischia":        {"lat": 40.731, "lon": 13.897, "rad": 0.10},
    "Pantelleria":   {"lat": 36.769, "lon": 12.021, "rad": 0.10},
    "Colli Albani":  {"lat": 41.757, "lon": 12.700, "rad": 0.12},
    "Marsili":       {"lat": 39.270, "lon": 14.400, "rad": 0.30},
    "Panarea":       {"lat": 38.636, "lon": 15.064, "rad": 0.10},
}

_HDR = {"User-Agent": "SismaVer2/4.0 (https://sos-italia.replit.app; meteotorre@gmail.com)"}


# ─────────────────────────────────────────────────────────────────────────────
# FETCH FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_volcano_alerts_live():
    """
    Indicatori attività vulcanica LIVE: INGV FDSN primario, EMSC come fallback.
    Metrica: eventi sismici M≥0.5 (INGV) / M≥1.0 (EMSC) negli ultimi 7 giorni
    nell'area del vulcano.
      Verde     = 0 eventi   (silente)
      Giallo    = 1–4 eventi (bassa attività)
      Arancione = 5–19 eventi (moderata)
      Rosso     = 20+ eventi  (elevata)
    """
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    results = {}

    def _classify(count):
        if count >= 20:
            return "Rosso",     "#DC2626", "🔴", f"Alta ({count} ev.)"
        elif count >= 5:
            return "Arancione", "#EA580C", "🟠", f"Moderata ({count} ev.)"
        elif count >= 1:
            return "Giallo",    "#D97706", "🟡", f"Bassa ({count} ev.)"
        else:
            return "Verde",     "#16A34A", "🟢", "Silente (0 ev.)"

    def _fetch_one(name, coords):
        lat, lon, rad = coords["lat"], coords["lon"], coords["rad"]
        # Tentativo 1: INGV
        try:
            r = requests.get(
                f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                f"&starttime={start}&minmag=0.5&lat={lat}&lon={lon}&maxradius={rad}&limit=50",
                timeout=7, headers=_HDR)
            if r.status_code == 200:
                count = len(r.json().get("features", []))
                level, col, emoji, label = _classify(count)
                return name, {"count": count, "level": level, "col": col,
                              "emoji": emoji, "label": label,
                              "lat": lat, "lon": lon, "fonte": "INGV"}
        except Exception:
            pass
        # Tentativo 2: EMSC fallback
        try:
            r = requests.get(
                f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
                f"&starttime={start}&minmagnitude=1.0"
                f"&lat={lat}&lon={lon}&maxradius={rad}&limit=50",
                timeout=8, headers=_HDR)
            if r.status_code == 200:
                count = len(r.json().get("features", []))
                level, col, emoji, label = _classify(count)
                return name, {"count": count, "level": level, "col": col,
                              "emoji": emoji, "label": label,
                              "lat": lat, "lon": lon, "fonte": "EMSC"}
        except Exception:
            pass
        return name, {
            "count": None, "level": "N/D",
            "col": "#94A3B8", "emoji": "⚫", "label": "N/D",
            "lat": lat, "lon": lon, "fonte": "N/D",
        }

    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(_fetch_one, n, d): n for n, d in _VULCANI_COORDS.items()}
        for ft in as_completed(futs):
            name, data = ft.result()
            results[name] = data
    return results


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_meteoalarm_regions():
    """Recupera allerte MeteoAlarm e le associa a regioni italiane."""
    import xml.etree.ElementTree as ET
    result = {}

    try:
        urls = [
            "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-italy",
            "https://feeds.meteoalarm.org/api/v1/warnings/feeds-italy/",
        ]
        raw = None
        for url in urls:
            try:
                r = requests.get(url, timeout=9, headers=_HDR)
                if r.status_code == 200 and len(r.content) > 100:
                    raw = r.content
                    break
            except Exception:
                pass

        if not raw:
            return result, 0, []

        root = ET.fromstring(raw)
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not entries:
            entries = root.findall(".//entry")

        total = len(entries)
        all_titles = []

        for entry in entries:
            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            if title_el is None:
                title_el = entry.find("title")
            title = (title_el.text or "") if title_el is not None else ""
            all_titles.append(title)
            title_low = title.lower()

            level = "yellow"
            if "red" in title_low or "rosso" in title_low:
                level = "red"
            elif "orange" in title_low or "arancione" in title_low:
                level = "orange"
            elif "green" in title_low or "verde" in title_low:
                level = "green"

            found_reg = None
            for alias, reg in _MA_ALIAS.items():
                if alias in title_low:
                    found_reg = reg
                    break

            if found_reg:
                existing = result.get(found_reg)
                level_ord = _MA_LEVEL_COLOR[level][3]
                if existing is None or level_ord > existing["ord"]:
                    result[found_reg] = {
                        "level": level, "ord": level_ord,
                        "count": 1, "titoli": [title[:80]],
                    }
                else:
                    result[found_reg]["count"] += 1
                    if len(result[found_reg]["titoli"]) < 3:
                        result[found_reg]["titoli"].append(title[:80])

        return result, total, all_titles[:10]

    except Exception:
        return {}, 0, []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_emsc_significant():
    """EMSC: eventi M≥4.5 nel Mediterraneo ultime 24h (per mappa)."""
    try:
        start = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        r = requests.get(
            f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
            f"&starttime={start}&minmagnitude=4.5"
            f"&minlatitude=28.0&maxlatitude=48.0&minlongitude=-10.0&maxlongitude=42.0"
            f"&limit=15&orderby=time",
            timeout=8, headers=_HDR)
        if r.status_code == 200:
            events = []
            for f in r.json().get("features", []):
                p = f.get("properties", {})
                g = f.get("geometry", {}).get("coordinates", [])
                if len(g) < 2:
                    continue
                mag = float(p.get("mag") or p.get("magnitude") or 0)
                luogo = p.get("place") or p.get("flynn_region") or "N/D"
                t = p.get("time") or p.get("lastupdate")
                ora_str = "—"
                if t:
                    try:
                        if isinstance(t, (int, float)):
                            dt = datetime.fromtimestamp(t / 1000.0, FUSO_IT)
                        else:
                            dt = datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(FUSO_IT)
                        ora_str = dt.strftime("%d/%m %H:%M")
                    except Exception:
                        pass
                events.append({
                    "mag": mag, "luogo": luogo, "ora": ora_str,
                    "lat": float(g[1]), "lon": float(g[0]),
                })
            return events
    except Exception:
        pass
    return []


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_emsc_italy_m3():
    """
    EMSC: terremoti M≥3.0 in Italia nelle ultime 24h.
    Restituisce lista eventi e conteggio.
    """
    try:
        start = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        r = requests.get(
            "https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
            f"&starttime={start}&minmagnitude=3.0"
            "&minlatitude=35.5&maxlatitude=47.1"
            "&minlongitude=6.6&maxlongitude=18.6"
            "&limit=50&orderby=time",
            timeout=8, headers=_HDR)
        if r.status_code == 200:
            events = []
            for f in r.json().get("features", []):
                p = f.get("properties", {})
                g = f.get("geometry", {}).get("coordinates", [])
                if len(g) < 2:
                    continue
                mag = float(p.get("mag") or p.get("magnitude") or 0)
                luogo = p.get("place") or p.get("flynn_region") or "N/D"
                t = p.get("time") or p.get("lastupdate")
                ora_str = "—"
                if t:
                    try:
                        if isinstance(t, (int, float)):
                            dt = datetime.fromtimestamp(t / 1000.0, FUSO_IT)
                        else:
                            dt = datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(FUSO_IT)
                        ora_str = dt.strftime("%d/%m %H:%M")
                    except Exception:
                        pass
                events.append({
                    "mag": mag, "luogo": luogo, "ora": ora_str,
                    "lat": float(g[1]), "lon": float(g[0]),
                    "depth": round(float(g[2]), 1) if len(g) > 2 else 0,
                })
            return events
    except Exception:
        pass
    return []


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_seismic_heatmap():
    """
    EMSC (primario) + INGV (fallback): eventi M≥2.0 in Italia ultimi 7gg per heatmap.
    Restituisce lista [lat, lon, peso] dove peso = mag^2.
    """
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    def _parse_features(features):
        points = []
        for f in features:
            p = f.get("properties", {})
            g = f.get("geometry", {}).get("coordinates", [])
            if len(g) < 2:
                continue
            try:
                mag = float(p.get("mag") or p.get("magnitude") or 2.0)
                lat, lon = float(g[1]), float(g[0])
                # Filtra bbox Italia
                if 35.5 <= lat <= 47.1 and 6.6 <= lon <= 18.6:
                    points.append([lat, lon, max(mag ** 2, 0.5)])
            except Exception:
                pass
        return points

    # 1) EMSC
    try:
        r = requests.get(
            "https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
            f"&starttime={start}&minmagnitude=2.0"
            "&minlatitude=35.5&maxlatitude=47.1"
            "&minlongitude=6.6&maxlongitude=18.6"
            "&limit=300&orderby=time",
            timeout=10, headers=_HDR)
        if r.status_code == 200:
            pts = _parse_features(r.json().get("features", []))
            if pts:
                return pts
    except Exception:
        pass

    # 2) Fallback INGV
    try:
        r = requests.get(
            "https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
            f"&starttime={start}&minmag=2.0&limit=300"
            "&minlatitude=35.5&maxlatitude=47.1"
            "&minlongitude=6.6&maxlongitude=18.6",
            timeout=10, headers=_HDR)
        if r.status_code == 200:
            pts = _parse_features(r.json().get("features", []))
            if pts:
                return pts
    except Exception:
        pass

    return []


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_fire_risk():
    """
    Rischio incendi derivato da Open-Meteo: temperatura, umidità relativa,
    velocità del vento, precipitazioni. Media su 5 punti italiani (N/C/S + isole).
    """
    punti = [
        ("Nord Italia",  45.5, 10.0),
        ("Centro Italia", 42.5, 12.5),
        ("Sud Italia",   40.5, 15.5),
        ("Sicilia",      37.5, 14.0),
        ("Sardegna",     39.5,  9.0),
    ]
    scores = []
    for _, lat, lon in punti:
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&hourly=temperature_2m,relative_humidity_2m,windspeed_10m,precipitation"
                "&timezone=Europe%2FRome&forecast_days=1",
                timeout=8)
            if r.status_code == 200:
                h = r.json().get("hourly", {})
                temps = h.get("temperature_2m", [])
                rh    = h.get("relative_humidity_2m", [])
                wind  = h.get("windspeed_10m", [])
                prec  = h.get("precipitation", [])
                if temps:
                    idx = slice(11, 17)
                    t_max  = max((x for x in temps[idx] if x is not None), default=20)
                    rh_min = min((x for x in rh[idx]    if x is not None), default=60)
                    w_max  = max((x for x in wind[idx]  if x is not None), default=10)
                    p_sum  = sum((x for x in prec        if x is not None), 0)
                    score  = (max(t_max - 15, 0) * 0.5 +
                              max(60 - rh_min, 0) * 0.35 +
                              w_max * 0.15 -
                              min(p_sum * 3, 20))
                    scores.append(max(score, 0))
        except Exception:
            pass

    if not scores:
        return None
    avg = sum(scores) / len(scores)
    if avg >= 55:
        return {"level": "MOLTO ALTO", "col": "#DC2626", "emoji": "🔴",
                "score": round(avg, 1), "desc": "Condizioni meteorologiche critiche per incendi"}
    elif avg >= 38:
        return {"level": "ALTO",       "col": "#EA580C", "emoji": "🟠",
                "score": round(avg, 1), "desc": "Rischio elevato — vento forte e/o bassa umidità"}
    elif avg >= 22:
        return {"level": "MODERATO",   "col": "#D97706", "emoji": "🟡",
                "score": round(avg, 1), "desc": "Prestare attenzione in aree boscose"}
    else:
        return {"level": "BASSO",      "col": "#16A34A", "emoji": "🟢",
                "score": round(avg, 1), "desc": "Condizioni favorevoli"}


# ─────────────────────────────────────────────────────────────────────────────
# COSTRUZIONE MAPPA
# ─────────────────────────────────────────────────────────────────────────────

def _build_alert_map(ma_regions, emsc_events, show_vulc, vulc_live,
                     show_heatmap, heatmap_data):
    """Costruisce la mappa di allerta regioni + EMSC + vulcani live + heatmap."""
    m = folium.Map(location=[42.0, 12.5], zoom_start=6,
                   tiles="CartoDB positron",
                   attr="© CartoDB · © OpenStreetMap")

    # ── Heatmap sismica ───────────────────────────────────────────────────────
    if show_heatmap and heatmap_data:
        HeatMap(
            heatmap_data,
            name="🌡️ Heatmap sismica (M≥2.0 · 7gg)",
            min_opacity=0.35,
            radius=22, blur=18,
            gradient={0.2: "#3B82F6", 0.5: "#D97706", 0.8: "#EA580C", 1.0: "#DC2626"},
        ).add_to(m)

    # ── Layer MeteoAlarm — un cerchio per regione ─────────────────────────────
    ma_group = folium.FeatureGroup(name="⚠️ Allerte MeteoAlarm per regione", show=True)
    for regione, (lat, lon) in _REGIONI.items():
        allerta = ma_regions.get(regione)
        if allerta:
            lv = allerta["level"]
            col, dot, nome_it, _ = _MA_LEVEL_COLOR[lv]
            count = allerta["count"]
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:180px;">
              <b style="color:{col};">{dot} {regione}</b><br>
              Allerta <b>{nome_it}</b> — {count} avvisi attivi<br>
              <hr style="margin:5px 0;">
              {"<br>".join(f"• {t}" for t in allerta['titoli'])}
            </div>"""
            folium.CircleMarker(
                location=[lat, lon], radius=22,
                color=col, fill=True, fill_color=col,
                fill_opacity=0.55, weight=2.5,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"⚠️ {regione} — Allerta {nome_it} ({count} avvisi)",
            ).add_to(ma_group)
        else:
            folium.CircleMarker(
                location=[lat, lon], radius=10,
                color="#16A34A", fill=True, fill_color="#16A34A",
                fill_opacity=0.15, weight=1,
                tooltip=f"✅ {regione} — Nessuna allerta MeteoAlarm",
            ).add_to(ma_group)
    ma_group.add_to(m)

    # ── Layer EMSC Mediterraneo ───────────────────────────────────────────────
    emsc_group = folium.FeatureGroup(name="🌊 EMSC Mediterraneo M≥4.5 (24h)", show=True)
    for ev in emsc_events:
        mag = ev["mag"]
        if mag >= 6.0:   col = "#DC2626"
        elif mag >= 5.0: col = "#EA580C"
        else:            col = "#D97706"
        radius = max(6, mag ** 2.5 * 0.8)
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:160px;">
          <b style="color:{col};font-size:1.05rem;">🌊 M {mag:.1f} — EMSC</b><br>
          📍 {ev['luogo']}<br>
          🕒 {ev['ora']}
        </div>"""
        folium.CircleMarker(
            location=[ev["lat"], ev["lon"]], radius=radius,
            color=col, fill=True, fill_color=col,
            fill_opacity=0.5, weight=2.5, dash_array="5 3",
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"[EMSC] M {mag:.1f} — {ev['luogo'][:40]}",
        ).add_to(emsc_group)
    emsc_group.add_to(m)

    # ── Layer vulcani LIVE ────────────────────────────────────────────────────
    if show_vulc and vulc_live:
        vulc_group = folium.FeatureGroup(name="🌋 Vulcani — attività sismica live", show=True)
        for nome, data in vulc_live.items():
            col   = data["col"]
            label = data["label"]
            count = data.get("count")
            count_str = f"{count} eventi M≥0.5 (7gg)" if count is not None else "N/D"
            fonte = data.get("fonte", "INGV")
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:170px;">
              <b>🌋 {nome}</b><br>
              Attività sismica: <b style="color:{col};">{data['emoji']} {label}</b><br>
              <small style="color:#64748B;">{count_str} · {fonte}</small>
            </div>"""
            folium.Marker(
                location=[data["lat"], data["lon"]],
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"🌋 {nome} — {data['emoji']} {label}",
                icon=folium.DivIcon(
                    html=f"""<div style="width:22px;height:22px;border-radius:50%;
                        background:{col};border:2.5px solid white;
                        box-shadow:0 2px 8px rgba(0,0,0,0.4);
                        display:flex;align-items:center;justify-content:center;
                        font-size:11px;color:white;font-weight:800;">🌋</div>""",
                    icon_size=(22, 22), icon_anchor=(11, 11),
                ),
            ).add_to(vulc_group)
        vulc_group.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SHOW
# ─────────────────────────────────────────────────────────────────────────────

def show():
    from modules.banner_utils import render_banner
    render_banner(
        "🗺️", "Mappa Rischi — Vista Interattiva",
        "Allerte meteo · Sismica Mediterraneo · Vulcani live · Incendi · Heatmap — tutto su una mappa",
        "#1E1B4B", "#4338CA",
    )

    if _AUTOREFRESH:
        st_autorefresh(interval=300_000, limit=None, key="mappa_rischi_autorefresh")

    ora = datetime.now(FUSO_IT)
    st.markdown(
        f"<p style='color:#64748B;font-size:0.88rem;margin-top:-8px;'>"
        f"Dati: MeteoAlarm EU · EMSC · INGV · Open-Meteo · "
        f"Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> (IT) · "
        f"Auto-refresh ogni 5 min</p>",
        unsafe_allow_html=True,
    )

    st.info(
        "**Questa pagina è diversa dalle altre:** mostra le **allerte attive per regione** "
        "(MeteoAlarm), gli **eventi significativi** (EMSC M≥4.5), lo **stato dei vulcani** "
        "e il **rischio incendi**. "
        "Per il catalogo sismico completo → **🌊 Monitoraggio Sismico**. "
        "Per i tab di allerta dettagliati → **📊 Allerte e Rischi**."
    )

    # ── Controlli ─────────────────────────────────────────────────────────────
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        show_vulc    = st.checkbox("🌋 Mostra vulcani", value=True, key="mr_vulc")
    with col_c2:
        show_emsc    = st.checkbox("🌊 Mostra eventi EMSC Mediterraneo", value=True, key="mr_emsc")
    with col_c3:
        show_heatmap = st.checkbox("🌡️ Heatmap sismica Italia (7gg)", value=False, key="mr_heat")

    # ── Caricamento dati in parallelo ─────────────────────────────────────────
    with st.spinner("Caricamento dati live: MeteoAlarm · EMSC · INGV vulcani · Incendi..."):
        with ThreadPoolExecutor(max_workers=6) as ex:
            f_ma    = ex.submit(_fetch_meteoalarm_regions)
            f_emsc  = ex.submit(_fetch_emsc_significant)
            f_vulc  = ex.submit(_fetch_volcano_alerts_live)
            f_m3    = ex.submit(_fetch_emsc_italy_m3)
            f_fire  = ex.submit(_fetch_fire_risk)
            f_heat  = ex.submit(_fetch_seismic_heatmap)
            (ma_regions, ma_total, ma_titles) = f_ma.result()
            emsc_events   = f_emsc.result() if show_emsc else []
            vulc_live     = f_vulc.result() if show_vulc else {}
            italy_m3      = f_m3.result()
            fire_risk     = f_fire.result()
            heatmap_data  = f_heat.result() if show_heatmap else []

    # ── 5 Metric boxes ────────────────────────────────────────────────────────
    n_reg_allerta = len(ma_regions)
    n_red_orange  = sum(1 for v in ma_regions.values() if v["level"] in ("red", "orange"))
    n_emsc        = len(emsc_events)
    n_vulc_active = sum(1 for v in vulc_live.values() if v.get("count") and v["count"] > 0)
    n_italy_m3    = len(italy_m3)

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("⚠️ Regioni con allerta", str(n_reg_allerta), "su 20 regioni")
    sc2.metric("🔴 Allerte Rosso/Arancione", str(n_red_orange), "priorità alta")
    sc3.metric("📋 Avvisi MeteoAlarm totali", str(ma_total), "Italia · feed live")
    sc4.metric("🌋 Vulcani con attività", str(n_vulc_active), "M≥0.5 · INGV live")
    sc5.metric("🔴 Terremoti M≥3 Italia (24h)", str(n_italy_m3),
               "↑ attenzione" if n_italy_m3 > 0 else "nessuno")

    # ── Rischio incendi ───────────────────────────────────────────────────────
    if fire_risk:
        col_fr, col_ts = st.columns([3, 1])
        with col_fr:
            fr_col = fire_risk["col"]
            st.markdown(
                f"""<div style="background:linear-gradient(135deg,{fr_col}22,{fr_col}11);
                    border:2px solid {fr_col};border-radius:10px;padding:12px 16px;
                    margin:8px 0 4px 0;">
                  <span style="font-size:1.05rem;font-weight:700;color:{fr_col};">
                    🔥 Rischio Incendi — {fire_risk['emoji']} {fire_risk['level']}
                  </span>
                  <span style="font-size:0.82rem;color:#64748B;margin-left:12px;">
                    {fire_risk['desc']}
                  </span>
                  <span style="font-size:0.75rem;color:#94A3B8;display:block;margin-top:3px;">
                    Indice meteo-derivato: {fire_risk['score']} · Fonte: Open-Meteo ·
                    <a href="https://effis.jrc.ec.europa.eu/" target="_blank">EFFIS Copernicus ↗</a>
                  </span>
                </div>""",
                unsafe_allow_html=True)
        with col_ts:
            st.markdown(
                """<div style="background:#0F172A;border:2px solid #334155;border-radius:10px;
                    padding:12px 14px;margin:8px 0 4px 0;text-align:center;">
                  <div style="font-size:0.82rem;color:#94A3B8;font-weight:600;">
                    🌊 Allerta Tsunami
                  </div>
                  <div style="font-size:1.0rem;font-weight:700;color:#22D3EE;margin-top:4px;">
                    🟢 VERDE
                  </div>
                  <div style="font-size:0.7rem;color:#64748B;margin-top:2px;">
                    Nessun allerta attivo<br>
                    <a href="https://www.ingv.it/cat/" target="_blank"
                       style="color:#38BDF8;">CAT-INGV ↗</a>
                  </div>
                </div>""",
                unsafe_allow_html=True)
    else:
        st.markdown(
            "🔥 **Rischio incendi:** dati Open-Meteo non disponibili al momento. "
            "[EFFIS Copernicus](https://effis.jrc.ec.europa.eu/) per dati ufficiali."
        )

    # ── Mappa ─────────────────────────────────────────────────────────────────
    if ma_total == 0 and n_emsc == 0:
        st.info("MeteoAlarm feed non disponibile. La mappa mostrerà solo i vulcani.")

    if show_heatmap:
        if heatmap_data:
            st.caption(f"🌡️ Heatmap sismica attiva — {len(heatmap_data)} eventi M≥2.0 (ultimi 7gg · EMSC)")
        else:
            st.warning("🌡️ Heatmap: nessun dato disponibile da EMSC al momento. Riprova tra qualche minuto.")

    alert_map = _build_alert_map(
        ma_regions, emsc_events, show_vulc, vulc_live,
        show_heatmap, heatmap_data,
    )
    folium_static(alert_map, width=None, height=560)

    # ── Legenda ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🗝️ Legenda mappa")
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)

    with col_l1:
        st.markdown("""
        **⚠️ Cerchi grandi — Allerte MeteoAlarm**
        <div style="font-size:0.85rem;line-height:2.1;">
        <span style="color:#16A34A;">⬤</span> Verde — nessuna allerta (cerchio piccolo)<br>
        <span style="color:#D97706;">⬤</span> Giallo — allerta ordinaria<br>
        <span style="color:#EA580C;">⬤</span> Arancione — allerta moderata<br>
        <span style="color:#DC2626;">⬤</span> Rosso — allerta grave<br>
        <i>Clicca sul cerchio per i dettagli</i>
        </div>
        """, unsafe_allow_html=True)

    with col_l2:
        st.markdown("""
        **🌊 Cerchi tratteggiati — EMSC Mediterraneo**
        <div style="font-size:0.85rem;line-height:2.1;">
        <span style="color:#D97706;">⬤</span> M 4.5–5.0 — monitoraggio<br>
        <span style="color:#EA580C;">⬤</span> M 5.0–6.0 — attenzione<br>
        <span style="color:#DC2626;">⬤</span> M≥6.0 — allerta<br>
        Fonte: seismicportal.eu · ultime 24h<br>
        ⚠️ Per allerta tsunami → CAT-INGV
        </div>
        """, unsafe_allow_html=True)

    with col_l3:
        st.markdown("""
        **🌋 Markers — attività vulcani (INGV/EMSC)**
        <div style="font-size:0.85rem;line-height:2.1;">
        <span style="color:#16A34A;">⬤</span> Verde — silente (0 eventi 7gg)<br>
        <span style="color:#D97706;">⬤</span> Giallo — bassa (1–4 eventi)<br>
        <span style="color:#EA580C;">⬤</span> Arancione — moderata (5–19)<br>
        <span style="color:#DC2626;">⬤</span> Rosso — elevata (20+ eventi)<br>
        <i>10 vulcani monitorati · aggiorn. 30 min</i>
        </div>
        """, unsafe_allow_html=True)

    with col_l4:
        st.markdown("""
        **🌡️ Heatmap sismica Italia**
        <div style="font-size:0.85rem;line-height:2.1;">
        <span style="color:#3B82F6;">⬤</span> Blu — attività bassa<br>
        <span style="color:#D97706;">⬤</span> Giallo — attività moderata<br>
        <span style="color:#EA580C;">⬤</span> Arancione — attività alta<br>
        <span style="color:#DC2626;">⬤</span> Rosso — concentrazione elevata<br>
        <i>M≥2.0 · ultimi 7 giorni · EMSC</i>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabella allerte per regione ───────────────────────────────────────────
    if ma_regions:
        st.markdown("#### 📋 Stato allerte per regione")
        sorted_regs = sorted(ma_regions.items(), key=lambda x: -x[1]["ord"])
        cols_t = st.columns(2)
        for i, (reg, data) in enumerate(sorted_regs):
            lv   = data["level"]
            col_c, dot, nome_it, _ = _MA_LEVEL_COLOR[lv]
            with cols_t[i % 2]:
                titoli_str = " · ".join(data["titoli"][:2]) if data["titoli"] else ""
                st.markdown(f"""
                <div class="sisma-card" style="border-left:4px solid {col_c};
                    padding:8px 12px;margin:4px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:700;font-size:0.92rem;color:#1E293B;">
                            {dot} {reg}
                        </span>
                        <span style="font-size:0.8rem;font-weight:700;color:{col_c};">
                            Allerta {nome_it} · {data['count']} avvisi
                        </span>
                    </div>
                    <div style="font-size:0.76rem;color:#64748B;margin-top:3px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {titoli_str}
                    </div>
                </div>""", unsafe_allow_html=True)

        senza = [r for r in _REGIONI if r not in ma_regions]
        if senza:
            st.markdown(
                f"<p style='color:#16A34A;font-size:0.85rem;margin-top:8px;'>"
                f"✅ Nessuna allerta: {' · '.join(senza)}</p>",
                unsafe_allow_html=True)
    else:
        st.success("Nessuna allerta MeteoAlarm attiva per l'Italia in questo momento")

    # ── EMSC Mediterraneo ─────────────────────────────────────────────────────
    if emsc_events:
        st.markdown("---")
        st.markdown("#### 🌊 Eventi EMSC significativi (M≥4.5 · 24h · Mediterraneo)")
        import pandas as pd
        df = pd.DataFrame([{
            "Magnitudo": f"M {ev['mag']:.1f}",
            "Luogo":     ev["luogo"],
            "Data/Ora":  ev["ora"],
        } for ev in emsc_events])
        st.dataframe(df, width='stretch', hide_index=True)
        st.caption(
            "⚠️ Indicatore derivato. Per allerta tsunami ufficiale: "
            "[CAT-INGV](https://www.ingv.it/cat/)"
        )

    # ── Terremoti Italia M≥3 (24h) ────────────────────────────────────────────
    if italy_m3:
        st.markdown("---")
        st.markdown(f"#### 🔴 Terremoti in Italia M≥3.0 — ultime 24h ({len(italy_m3)} eventi)")
        import pandas as pd
        df_m3 = pd.DataFrame([{
            "Magnitudo":      f"M {ev['mag']:.1f}",
            "Luogo":          ev["luogo"],
            "Profondità (km)": ev["depth"],
            "Data/Ora":       ev["ora"],
        } for ev in italy_m3])
        df_m3.index = range(1, len(df_m3) + 1)
        st.dataframe(df_m3, width='stretch')
        st.caption("Fonte: EMSC seismicportal.eu · bounding box territorio italiano · aggiorn. 5 min")
    else:
        st.markdown("---")
        st.success("✅ Nessun terremoto M≥3.0 in Italia nelle ultime 24 ore (fonte: EMSC)")

    # ── Stato attività vulcanica LIVE ─────────────────────────────────────────
    if show_vulc and vulc_live:
        st.markdown("---")
        st.markdown("#### 🌋 Attività sismica vulcani — dati live INGV/EMSC (10 vulcani)")
        st.caption("Numero di eventi M≥0.5 nell'area vulcanica negli ultimi 7 giorni · TTL 30 min")
        vcols = st.columns(5)
        for i, (nome, data) in enumerate(sorted(
                vulc_live.items(), key=lambda x: -(x[1].get("count") or 0))):
            col_c = data["col"]
            label = data["label"]
            count = data.get("count")
            count_str = f"{count} ev." if count is not None else "N/D"
            fonte = data.get("fonte", "INGV")
            with vcols[i % 5]:
                st.markdown(f"""
                <div style="border-left:4px solid {col_c};padding:8px 10px;
                    margin:4px 0;border-radius:0 6px 6px 0;
                    background:rgba(0,0,0,0.03);">
                  <div style="font-weight:700;font-size:0.88rem;">
                    {data['emoji']} {nome}
                  </div>
                  <div style="font-size:0.78rem;color:{col_c};font-weight:600;">
                    {label}
                  </div>
                  <div style="font-size:0.70rem;color:#94A3B8;">
                    {count_str} M≥0.5 (7gg)<br>
                    <span style="color:#CBD5E1;">fonte: {fonte}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption(
        "Fonti: MeteoAlarm EU (feeds.meteoalarm.org) · EMSC (seismicportal.eu) · "
        "Vulcani: INGV FDSN + fallback EMSC · Incendi: Open-Meteo · "
        "Aggiornamento automatico ogni 5 min"
    )
