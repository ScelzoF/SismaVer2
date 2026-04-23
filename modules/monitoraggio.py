import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh as _st_autorefresh
    _AUTOREFRESH = True
except ImportError:
    _AUTOREFRESH = False
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
import requests
import json
import os
import re as _re_prov
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Fuso orario italiano con ora legale automatica ───────────────────────────
def _get_tz_italia():
    _now = datetime.now()
    _y = _now.year
    _dst_s = datetime(_y, 3, 31 - (datetime(_y, 3, 31).weekday() + 1) % 7)
    _dst_e = datetime(_y, 10, 31 - (datetime(_y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if _dst_s <= _now < _dst_e else 1))

FUSO_ORARIO_ITALIA = _get_tz_italia()

# ── Mappatura Province → Regione ─────────────────────────────────────────────
_PROVINCE_TO_REGION = {
    "AQ": "Abruzzo", "CH": "Abruzzo", "PE": "Abruzzo", "TE": "Abruzzo",
    "MT": "Basilicata", "PZ": "Basilicata",
    "CS": "Calabria", "CZ": "Calabria", "KR": "Calabria", "RC": "Calabria", "VV": "Calabria",
    "AV": "Campania", "BN": "Campania", "CE": "Campania", "NA": "Campania", "SA": "Campania",
    "BO": "Emilia-Romagna", "FC": "Emilia-Romagna", "FE": "Emilia-Romagna", "MO": "Emilia-Romagna",
    "PC": "Emilia-Romagna", "PR": "Emilia-Romagna", "RA": "Emilia-Romagna", "RE": "Emilia-Romagna", "RN": "Emilia-Romagna",
    "GO": "Friuli-Venezia Giulia", "PN": "Friuli-Venezia Giulia", "TS": "Friuli-Venezia Giulia", "UD": "Friuli-Venezia Giulia",
    "FR": "Lazio", "LT": "Lazio", "RI": "Lazio", "RM": "Lazio", "VT": "Lazio",
    "GE": "Liguria", "IM": "Liguria", "SP": "Liguria", "SV": "Liguria",
    "BG": "Lombardia", "BS": "Lombardia", "CO": "Lombardia", "CR": "Lombardia", "LC": "Lombardia",
    "LO": "Lombardia", "MB": "Lombardia", "MI": "Lombardia", "MN": "Lombardia", "PV": "Lombardia",
    "SO": "Lombardia", "VA": "Lombardia",
    "AN": "Marche", "AP": "Marche", "FM": "Marche", "MC": "Marche", "PU": "Marche",
    "CB": "Molise", "IS": "Molise",
    "AL": "Piemonte", "AT": "Piemonte", "BI": "Piemonte", "CN": "Piemonte", "NO": "Piemonte",
    "TO": "Piemonte", "VB": "Piemonte", "VC": "Piemonte",
    "BA": "Puglia", "BR": "Puglia", "BT": "Puglia", "FG": "Puglia", "LE": "Puglia", "TA": "Puglia",
    "CA": "Sardegna", "NU": "Sardegna", "OR": "Sardegna", "SS": "Sardegna", "SU": "Sardegna",
    "AG": "Sicilia", "CL": "Sicilia", "CT": "Sicilia", "EN": "Sicilia", "ME": "Sicilia",
    "PA": "Sicilia", "RG": "Sicilia", "SR": "Sicilia", "TP": "Sicilia",
    "AR": "Toscana", "FI": "Toscana", "GR": "Toscana", "LI": "Toscana", "LU": "Toscana",
    "MS": "Toscana", "PI": "Toscana", "PO": "Toscana", "PT": "Toscana", "SI": "Toscana",
    "BZ": "Trentino-Alto Adige", "TN": "Trentino-Alto Adige",
    "PG": "Umbria", "TR": "Umbria",
    "AO": "Valle d'Aosta",
    "BL": "Veneto", "PD": "Veneto", "RO": "Veneto", "TV": "Veneto", "VE": "Veneto", "VI": "Veneto", "VR": "Veneto",
}

_REGIONI_BBOX = {
    "Abruzzo": (41.68, 42.90, 13.02, 14.79),
    "Basilicata": (39.90, 41.14, 15.34, 16.87),
    "Calabria": (37.91, 40.15, 15.63, 17.21),
    "Campania": (39.99, 41.51, 13.75, 15.81),
    "Emilia-Romagna": (43.73, 45.14, 9.20, 12.76),
    "Friuli-Venezia Giulia": (45.58, 46.65, 12.32, 13.92),
    "Lazio": (40.78, 42.84, 11.45, 14.03),
    "Liguria": (43.77, 44.68, 7.49, 10.07),
    "Lombardia": (44.68, 46.64, 8.50, 11.42),
    "Marche": (42.69, 43.97, 12.18, 13.92),
    "Molise": (41.36, 42.06, 14.10, 15.16),
    "Piemonte": (44.06, 46.46, 6.62, 9.21),
    "Puglia": (39.79, 42.22, 14.94, 18.55),
    "Sardegna": (38.85, 41.32, 8.13, 9.83),
    "Sicilia": (35.49, 38.81, 11.93, 15.65),
    "Toscana": (42.24, 44.47, 9.69, 12.37),
    "Trentino-Alto Adige": (45.67, 47.10, 10.38, 12.48),
    "Umbria": (42.36, 43.62, 11.89, 13.27),
    "Valle d'Aosta": (45.46, 45.99, 6.79, 7.94),
    "Veneto": (44.79, 46.68, 10.62, 13.10),
}

# Coordinate dei vulcani monitorati con raggio bbox in gradi
_VULCANI_MON = {
    "Etna":          {"lat": 37.755, "lon": 14.995, "rad": 0.20, "obs": "INGV-CT", "ult_eruz": "Attivo"},
    "Stromboli":     {"lat": 38.789, "lon": 15.213, "rad": 0.12, "obs": "INGV-CT", "ult_eruz": "Attivo"},
    "Campi Flegrei": {"lat": 40.827, "lon": 14.139, "rad": 0.15, "obs": "INGV-OV", "ult_eruz": "1538"},
    "Vesuvio":       {"lat": 40.821, "lon": 14.426, "rad": 0.10, "obs": "INGV-OV", "ult_eruz": "1944"},
    "Vulcano":       {"lat": 38.404, "lon": 14.962, "rad": 0.12, "obs": "INGV-CT", "ult_eruz": "1888-90"},
    "Ischia":        {"lat": 40.731, "lon": 13.897, "rad": 0.10, "obs": "INGV-OV", "ult_eruz": "1302"},
    "Pantelleria":   {"lat": 36.769, "lon": 12.021, "rad": 0.10, "obs": "INGV-CT", "ult_eruz": "1891 (sub.)"},
    "Colli Albani":  {"lat": 41.757, "lon": 12.700, "rad": 0.12, "obs": "INGV-RM", "ult_eruz": "5000 a.f."},
    "Marsili":       {"lat": 39.270, "lon": 14.400, "rad": 0.30, "obs": "INGV",    "ult_eruz": "Non doc. (sub.)"},
    "Panarea":       {"lat": 38.636, "lon": 15.064, "rad": 0.10, "obs": "INGV-CT", "ult_eruz": "2002 (sub.)"},
}


def _evento_in_regione(place: str, lat, lon, regione: str) -> bool:
    """Filtro robusto: prima sigla provincia tra parentesi, poi bounding box come fallback."""
    if not regione or regione.startswith("Italia"):
        return True
    try:
        if isinstance(place, str):
            m = _re_prov.search(r"\(([A-Z]{2})\)", place)
            if m:
                sigla = m.group(1)
                reg_match = _PROVINCE_TO_REGION.get(sigla)
                if reg_match is not None:
                    return reg_match == regione
        bbox = _REGIONI_BBOX.get(regione)
        if bbox and lat is not None and lon is not None:
            lat_min, lat_max, lon_min, lon_max = bbox
            return (lat_min <= float(lat) <= lat_max) and (lon_min <= float(lon) <= lon_max)
    except Exception:
        return False
    return False


# ── Fetch INGV sismicità (modulo-level, cache 5 minuti) ──────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_ingv_seismic(url: str):
    """
    Recupera eventi sismici da INGV FDSN con fallback a USGS.
    Returns (geojson_dict, warning_message_or_None)
    """
    headers = {
        "User-Agent": "SismaVer2/3.3 (https://sisma-ver-2.replit.app/)",
        "Accept": "application/json",
    }
    # 1) Prova INGV principale
    try:
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("features"), list):
                print(f"INFO INGV: {len(data['features'])} eventi")
                return data, None
    except Exception as e:
        print(f"INGV primario fallito: {e}")

    # 2) Fallback INGV mirror cnt.rm.ingv.it
    try:
        mirror_url = url.replace("webservices.ingv.it", "cnt.rm.ingv.it")
        r = requests.get(mirror_url, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("features"), list):
                print(f"INFO INGV mirror: {len(data['features'])} eventi")
                return data, None
    except Exception as e:
        print(f"INGV mirror fallito: {e}")

    # 3) Fallback EMSC (European-Mediterranean Seismological Centre)
    try:
        start_time = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        emsc_url = (
            f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
            f"&starttime={start_time}&minlatitude=35.0&maxlatitude=47.5"
            f"&minlongitude=6.0&maxlongitude=20.0&minmagnitude=1.5"
            f"&orderby=time&limit=300"
        )
        r = requests.get(emsc_url, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("features"), list) and data["features"]:
                print(f"INFO EMSC fallback: {len(data['features'])} eventi")
                return data, "⚠️ INGV temporaneamente non disponibile. Dati da EMSC (European-Mediterranean Seismological Centre)."
    except Exception as e:
        print(f"EMSC fallback fallito: {e}")

    # 4) Fallback USGS — nota: USGS non dispone di eventi italiani M<2.0
    try:
        start_time = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        usgs_url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&starttime={start_time}&minlatitude=35.0&maxlatitude=47.5"
            f"&minlongitude=6.0&maxlongitude=20.0&minmagnitude=1.5"
            f"&limit=300"
        )
        r = requests.get(usgs_url, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get("features"), list) and data["features"]:
                print(f"INFO USGS fallback: {len(data['features'])} eventi")
                return data, "⚠️ INGV temporaneamente non disponibile. Dati da USGS (United States Geological Survey)."
    except Exception as e:
        print(f"USGS fallback fallito: {e}")

    # 5) Struttura vuota valida
    return {"features": [], "type": "FeatureCollection", "metadata": {}}, \
           "⚠️ Impossibile accedere ai dati sismici — riprova tra qualche minuto."


# ── Fetch attività sismica per vulcano (cache 5 minuti) ─────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _fetch_volcano_seismicity_all():
    """
    Fetch parallelo INGV FDSN per ogni vulcano monitorato.
    Ritorna dict: nome_vulcano -> {count, level, label, emoji, col}
    """
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    _HDR_V = {"User-Agent": "SismaVer2/3.3 (https://sisma-ver-2.replit.app/)"}

    def _classify_v(count):
        if count >= 20:
            return {"count": count, "level": "ROSSO",    "emoji": "🔴", "label": f"Alta ({count} ev/7gg)",    "col": "#DC2626"}
        elif count >= 5:
            return {"count": count, "level": "ARANCIONE","emoji": "🟠", "label": f"Moderata ({count} ev/7gg)","col": "#EA580C"}
        elif count >= 1:
            return {"count": count, "level": "GIALLO",   "emoji": "🟡", "label": f"Bassa ({count} ev/7gg)",   "col": "#D97706"}
        else:
            return {"count": 0,     "level": "VERDE",    "emoji": "🟢", "label": "Silente (0 ev/7gg)",       "col": "#16A34A"}

    def _one(name, cfg):
        lat, lon, rad = cfg["lat"], cfg["lon"], cfg["rad"]
        # Tentativo 1: INGV
        try:
            r = requests.get(
                f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                f"&starttime={start}&minmag=0.5&lat={lat}&lon={lon}&maxradius={rad}&limit=100",
                timeout=8, headers=_HDR_V)
            if r.status_code == 200:
                count = len(r.json().get("features", []))
                return name, _classify_v(count)
        except Exception as e:
            print(f"Vulcano {name} INGV error: {e}")
        # Tentativo 2: EMSC fallback (M≥1.0 nell'area)
        try:
            r = requests.get(
                f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
                f"&starttime={start}&minmagnitude=1.0"
                f"&lat={lat}&lon={lon}&maxradius={rad}&limit=100",
                timeout=8, headers=_HDR_V)
            if r.status_code == 200:
                count = len(r.json().get("features", []))
                result = _classify_v(count)
                result["fonte"] = "EMSC"
                return name, result
        except Exception as e:
            print(f"Vulcano {name} EMSC error: {e}")
        return name, {"count": None, "level": "N/D", "emoji": "⚫", "label": "N/D", "col": "#94A3B8"}

    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(_one, n, d): n for n, d in _VULCANI_MON.items()}
        for ft in as_completed(futs):
            n, d = ft.result()
            results[n] = d
    return results


def show():
    # Auto-refresh ogni 5 minuti
    if _AUTOREFRESH:
        _st_autorefresh(interval=300_000, limit=None, key="monit_autorefresh")

    from modules.banner_utils import banner_monitoraggio
    banner_monitoraggio()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.subheader("🗄️ Filtra visualizzazione")
    regioni = [
        "Italia (Visione nazionale)",
        "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
        "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche",
        "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana",
        "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"
    ]
    regione_scelta = st.sidebar.selectbox("Seleziona regione", regioni)
    current_time = datetime.now(FUSO_ORARIO_ITALIA)
    st.sidebar.markdown(f"**🕒 Ultimo aggiornamento:** {current_time.strftime('%d/%m/%Y %H:%M:%S')} (IT)")
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Fonti dati:**\n"
        "- INGV (Istituto Nazionale di Geofisica e Vulcanologia)\n"
        "- Dipartimento della Protezione Civile\n"
        "- ISPRA (Istituto Superiore per la Protezione e la Ricerca Ambientale)\n"
        "- MeteoAlarm (EUMETNET)"
    )

    # Coordinate centroidi regioni per centrare la mappa
    regioni_coords = {
        "Abruzzo": [42.35, 13.40], "Basilicata": [40.50, 16.08],
        "Calabria": [39.30, 16.34], "Campania": [40.83, 14.25],
        "Emilia-Romagna": [44.49, 11.34], "Friuli-Venezia Giulia": [46.07, 13.23],
        "Lazio": [41.89, 12.48], "Liguria": [44.41, 8.95],
        "Lombardia": [45.47, 9.19], "Marche": [43.62, 13.51],
        "Molise": [41.56, 14.65], "Piemonte": [45.07, 7.68],
        "Puglia": [41.12, 16.86], "Sardegna": [39.22, 9.10],
        "Sicilia": [37.50, 14.00], "Toscana": [43.77, 11.24],
        "Trentino-Alto Adige": [46.06, 11.12], "Umbria": [43.11, 12.39],
        "Valle d'Aosta": [45.73, 7.32], "Veneto": [45.44, 12.32],
    }

    sensor_tab1, sensor_tab2 = st.tabs([
        "🔔 Sismicità", "🌋 Vulcani attivi"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SISMICITÀ
    # ══════════════════════════════════════════════════════════════════════════
    with sensor_tab1:
        col_refresh, col_time = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Aggiorna dati"):
                st.cache_data.clear()
                st.rerun()
        with col_time:
            st.markdown(f"**🕒 Dati aggiornati:** {current_time.strftime('%d/%m/%Y %H:%M:%S')} (IT) · Cache 5 min")

        # Costruisci URL INGV
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        min_mag = 0.5
        if regione_scelta == "Italia (Visione nazionale)":
            ingv_url = (
                f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                f"&starttime={start_date}&minmag={min_mag}&limit=300"
            )
        else:
            lat_c, lon_c = regioni_coords.get(regione_scelta, [42.0, 12.5])
            ingv_url = (
                f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                f"&starttime={start_date}&minmag={min_mag}"
                f"&lat={lat_c}&lon={lon_c}&maxradius=1.5&limit=300"
            )

        with st.spinner("⏳ Recupero dati sismici INGV in corso..."):
            sensor_data, error_msg = _fetch_ingv_seismic(ingv_url)
            features = sensor_data.get("features", [])

        # Filtro bbox Italia (solo visione nazionale) o per regione
        _is_nazionale = (not regione_scelta) or regione_scelta.startswith("Italia")
        _ITA_BBOX = (35.5, 47.1, 6.6, 18.55)
        _tot_pre = len(features)
        _filtered = []
        for _f in features:
            try:
                _props = _f.get("properties", {}) or {}
                _geom = (_f.get("geometry", {}) or {}).get("coordinates", []) or []
                _place = _props.get("place", "") or ""
                _lon = _geom[0] if len(_geom) > 0 else None
                _lat = _geom[1] if len(_geom) > 1 else None
                if _is_nazionale:
                    if _lat is None or _lon is None:
                        continue
                    la, lo = float(_lat), float(_lon)
                    if _ITA_BBOX[0] <= la <= _ITA_BBOX[1] and _ITA_BBOX[2] <= lo <= _ITA_BBOX[3]:
                        _filtered.append(_f)
                else:
                    if _evento_in_regione(_place, _lat, _lon, regione_scelta):
                        _filtered.append(_f)
            except Exception:
                continue
        features = _filtered
        _label = "Italia" if _is_nazionale else regione_scelta

        if error_msg:
            if error_msg.startswith("✅"):
                st.success(error_msg)
            else:
                st.warning(error_msg)

        if _tot_pre and not features:
            st.info(f"Nessun evento nelle ultime 24 ore con epicentro in {_label} "
                    f"(esclusi {_tot_pre} eventi esteri/limitrofi).")
        elif _tot_pre != len(features) and len(features) > 0:
            st.caption(f"🔎 Filtrati {len(features)} eventi su {_tot_pre} con epicentro effettivo in {_label}.")

        if not features:
            st.info(f"Nessun evento sismico rilevato negli ultimi 7 giorni "
                    f"{'in ' + regione_scelta if regione_scelta != 'Italia (Visione nazionale)' else 'in Italia'}.")
            st.markdown(
                "🔗 [Portale eventi INGV](https://terremoti.ingv.it/events) · "
                "[Bollettini ufficiali](https://www.ingv.it/cat/it/comunicati-stampa)"
            )
        else:
            max_events = 100
            limited_features = features[:max_events]

            seismic_data = []
            for feature in limited_features:
                props = feature["properties"]
                geom = feature["geometry"]["coordinates"]
                event_time = props.get("time", "")
                try:
                    if isinstance(event_time, (int, float)):
                        dt_it = datetime.fromtimestamp(event_time / 1000.0, FUSO_ORARIO_ITALIA)
                        formatted_time = dt_it.strftime("%d/%m/%Y %H:%M:%S") + " (IT)"
                    elif isinstance(event_time, str):
                        et = event_time.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(et)
                        dt_it = dt.astimezone(FUSO_ORARIO_ITALIA)
                        formatted_time = dt_it.strftime("%d/%m/%Y %H:%M:%S") + " (IT)"
                    else:
                        formatted_time = str(event_time)
                except Exception:
                    formatted_time = str(event_time)

                seismic_data.append({
                    "Luogo": props.get("place", "N/A"),
                    "Magnitudo": props.get("mag", 0),
                    "Data/Ora": formatted_time,
                    "Profondità (km)": round(geom[2], 1) if len(geom) > 2 else 0,
                    "Latitudine": geom[1],
                    "Longitudine": geom[0],
                })

            df_seismic = pd.DataFrame(seismic_data)
            df_seismic.index = range(1, len(df_seismic) + 1)

            st.subheader(f"🔍 Eventi sismici in tempo reale — {regione_scelta}")
            if len(features) > max_events:
                st.caption(f"Visualizzati {max_events} eventi su {len(features)} totali (ultimi 7 giorni, M≥{min_mag})")
            st.dataframe(df_seismic, width='stretch')

            # ── Mappa eventi ─────────────────────────────────────────────────
            map_center = regioni_coords.get(regione_scelta, [41.9, 12.5]) \
                if regione_scelta != "Italia (Visione nazionale)" else [41.9, 12.5]
            zoom = 6 if regione_scelta == "Italia (Visione nazionale)" else 8
            m = folium.Map(location=map_center, zoom_start=zoom)

            for _, row in df_seismic.iterrows():
                mag = row["Magnitudo"]
                color = "green" if mag < 3.0 else "orange" if mag < 4.0 else "red"
                eq_lat, eq_lon = row["Latitudine"], row["Longitudine"]
                _eqg  = f"https://www.google.com/maps/dir/?api=1&destination={eq_lat},{eq_lon}&travelmode=driving"
                _eqwz = f"https://waze.com/ul?ll={eq_lat},{eq_lon}&navigate=yes"
                _eqam = f"https://maps.apple.com/?daddr={eq_lat},{eq_lon}&dirflg=d"
                popup_text = (
                    '<div style="min-width:210px;font-family:sans-serif;font-size:12px;">'
                    f'<h4 style="color:#DC2626;margin:0 0 5px 0;font-size:13px;border-bottom:2px solid #DC2626;padding-bottom:3px;">🌊 Evento sismico</h4>'
                    f'<p style="margin:0 0 2px 0;"><b>Luogo:</b> {row["Luogo"]}</p>'
                    f'<p style="margin:0 0 2px 0;"><b>Magnitudo:</b> {mag}</p>'
                    f'<p style="margin:0 0 2px 0;"><b>Data/Ora:</b> {row["Data/Ora"]}</p>'
                    f'<p style="margin:0 0 6px 0;"><b>Profondità:</b> {row["Profondità (km)"]} km</p>'
                    '<div style="font-size:10px;color:#888;margin-bottom:4px;">📍 Naviga all\'epicentro:</div>'
                    '<div style="display:flex;gap:4px;">'
                    f'<a href="{_eqg}" target="_blank" style="background:#4285F4;color:white;padding:3px 6px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🗺️ GMaps</a>'
                    f'<a href="{_eqwz}" target="_blank" style="background:#00BCD4;color:#000;padding:3px 6px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🚗 Waze</a>'
                    f'<a href="{_eqam}" target="_blank" style="background:#555;color:white;padding:3px 6px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🍎 Maps</a>'
                    '</div></div>'
                )
                folium.Circle(
                    location=[eq_lat, eq_lon],
                    radius=mag * 5000,
                    color=color, fill=True, fill_opacity=0.4,
                    popup=folium.Popup(popup_text, max_width=270)
                ).add_to(m)

            st.subheader("🗺️ Mappa eventi sismici in tempo reale")
            folium_static(m, width=1100, height=520)

            # ── Grafico magnitudo nel tempo ───────────────────────────────────
            st.subheader("📈 Andamento sismico eventi recenti")
            try:
                def _parse_date(date_str):
                    s = str(date_str).replace(" (IT)", "")
                    try:
                        return pd.to_datetime(s)
                    except Exception:
                        return pd.Timestamp.now()

                df_seismic["Data/Ora Obj"] = df_seismic["Data/Ora"].apply(_parse_date)
                df_seismic = df_seismic.sort_values("Data/Ora Obj")

                fig = px.scatter(
                    df_seismic, x="Data/Ora Obj", y="Magnitudo",
                    color="Magnitudo", size="Magnitudo",
                    hover_data=["Luogo", "Profondità (km)"],
                    color_continuous_scale=px.colors.sequential.Reds,
                    title=f"Sismicità negli ultimi 7 giorni — {regione_scelta}",
                    labels={"Data/Ora Obj": "Data/Ora"}
                )
                fig.add_trace(go.Scatter(
                    x=df_seismic["Data/Ora Obj"], y=df_seismic["Magnitudo"],
                    mode="lines", line=dict(width=1, color="rgba(200,200,200,0.5)"),
                    showlegend=False
                ))
                fig.update_layout(xaxis_title="Data/Ora", yaxis_title="Magnitudo", hovermode="closest")
                st.plotly_chart(fig, width='stretch')
            except Exception as e:
                st.warning(f"Impossibile generare il grafico temporale: {e}")

            # ── Statistiche rapide ────────────────────────────────────────────
            st.subheader("📊 Statistiche sismiche")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Numero eventi", len(df_seismic))
            with col2:
                st.metric("Magnitudo massima", round(df_seismic["Magnitudo"].max(), 1))
            with col3:
                st.metric("Profondità media (km)", round(df_seismic["Profondità (km)"].mean(), 1))

            # ── Analisi avanzata ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("📈 Analisi avanzata degli eventi")
            col_a1, col_a2 = st.columns(2)

            with col_a1:
                bins = [0, 1.0, 2.0, 3.0, 4.0, 10.0]
                labels = ["<1 (Micro)", "1-2 (Molto debole)", "2-3 (Debole)", "3-4 (Leggero)", "4+ (Moderato+)"]
                df_seismic["Fascia Magnitudo"] = pd.cut(df_seismic["Magnitudo"], bins=bins, labels=labels)
                fascia_counts = df_seismic["Fascia Magnitudo"].value_counts().sort_index()
                fig_pie = px.pie(
                    values=fascia_counts.values, names=fascia_counts.index,
                    title="Distribuzione eventi per magnitudo",
                    color_discrete_sequence=px.colors.sequential.Reds_r
                )
                st.plotly_chart(fig_pie, width='stretch')

            with col_a2:
                fig_hist = px.histogram(
                    df_seismic, x="Profondità (km)", nbins=10,
                    title="Distribuzione della profondità degli eventi",
                    color_discrete_sequence=["#e5394d"]
                )
                st.plotly_chart(fig_hist, width='stretch')

            # ── Mappa di intensità sismica ────────────────────────────────────
            st.subheader("🗺️ Mappa di intensità sismica")
            try:
                intensity_map = folium.Map(location=map_center, zoom_start=zoom, tiles="CartoDB positron")
                città_italiane = {
                    "Roma": [41.9028, 12.4964], "Milano": [45.4642, 9.1900],
                    "Napoli": [40.8518, 14.2681], "Palermo": [38.1157, 13.3615],
                    "Torino": [45.0703, 7.6869], "Bologna": [44.4949, 11.3426],
                }
                for città, pos in città_italiane.items():
                    folium.Marker(pos, popup=città, icon=folium.Icon(color="blue", icon="info-sign")).add_to(intensity_map)

                for _, row in df_seismic.iterrows():
                    try:
                        lat = float(row["Latitudine"])
                        lon = float(row["Longitudine"])
                        mag = float(row["Magnitudo"])
                        depth = float(row["Profondità (km)"])
                        if not (35.0 <= lat <= 48.0 and 6.0 <= lon <= 19.0):
                            continue
                        color = "red" if mag >= 4.0 else "orange" if mag >= 3.0 else "yellow" if mag >= 2.0 else "green"
                        _ig  = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                        _iwz = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
                        _iam = f"https://maps.apple.com/?daddr={lat},{lon}&dirflg=d"
                        popup_text = (
                            '<div style="min-width:200px;font-family:sans-serif;font-size:12px;">'
                            f'<h4 style="color:#DC2626;margin:0 0 5px 0;font-size:13px;border-bottom:2px solid #DC2626;padding-bottom:3px;">🌊 Evento sismico</h4>'
                            f'<p style="margin:0 0 2px 0;"><b>Magnitudo:</b> {mag}</p>'
                            f'<p style="margin:0 0 2px 0;"><b>Profondità:</b> {depth} km</p>'
                            f'<p style="margin:0 0 2px 0;"><b>Data:</b> {row.get("Data/Ora", "N/D")}</p>'
                            f'<p style="margin:0 0 6px 0;"><b>Località:</b> {row.get("Luogo", "N/D")}</p>'
                            '<div style="display:flex;gap:3px;">'
                            f'<a href="{_ig}" target="_blank" style="background:#4285F4;color:white;padding:3px 5px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🗺️ GMaps</a>'
                            f'<a href="{_iwz}" target="_blank" style="background:#00BCD4;color:#000;padding:3px 5px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🚗 Waze</a>'
                            f'<a href="{_iam}" target="_blank" style="background:#555;color:white;padding:3px 5px;text-decoration:none;border-radius:3px;font-size:10px;font-weight:600;">🍎 Maps</a>'
                            '</div></div>'
                        )
                        folium.Circle(
                            location=[lat, lon], radius=mag * 5000,
                            color=color, fill=True, fill_opacity=0.4,
                            popup=folium.Popup(popup_text, max_width=260)
                        ).add_to(intensity_map)
                    except Exception:
                        continue

                folium_static(intensity_map, width=1100, height=520)
                st.caption("La dimensione e il colore dei cerchi rappresentano la magnitudo dell'evento.")
            except Exception as map_err:
                st.error(f"Errore nella mappa di intensità: {map_err}")
                st.markdown("🔗 [Portale eventi INGV](https://terremoti.ingv.it/events)")

            # ── Terremoti storici significativi ──────────────────────────────
            st.markdown("---")
            st.subheader("📜 Terremoti storici significativi in Italia")
            df_historic = pd.DataFrame([
                {"Data": "1693-01-11", "Magnitudo": 7.4, "Località": "Sicilia Orientale",       "Regione": "Sicilia",        "Vittime": "~60.000"},
                {"Data": "1783-02-05", "Magnitudo": 7.0, "Località": "Calabria meridionale",     "Regione": "Calabria",       "Vittime": "~30.000"},
                {"Data": "1857-12-16", "Magnitudo": 7.0, "Località": "Basilicata (Val d'Agri)", "Regione": "Basilicata",     "Vittime": "~11.000"},
                {"Data": "1905-09-08", "Magnitudo": 7.1, "Località": "Calabria centrale",        "Regione": "Calabria",       "Vittime": "~4.000"},
                {"Data": "1908-12-28", "Magnitudo": 7.1, "Località": "Messina e Reggio Calabria","Regione": "Sicilia/Calabria","Vittime": "~80.000"},
                {"Data": "1915-01-13", "Magnitudo": 7.0, "Località": "Avezzano",                 "Regione": "Abruzzo",        "Vittime": "~30.000"},
                {"Data": "1930-07-23", "Magnitudo": 6.7, "Località": "Vulture (Irpinia)",        "Regione": "Campania",       "Vittime": "~1.400"},
                {"Data": "1968-01-15", "Magnitudo": 6.4, "Località": "Valle del Belice",         "Regione": "Sicilia",        "Vittime": "~289"},
                {"Data": "1976-05-06", "Magnitudo": 6.5, "Località": "Friuli (Gemona)",          "Regione": "Friuli-Venezia Giulia", "Vittime": "~990"},
                {"Data": "1980-11-23", "Magnitudo": 6.9, "Località": "Irpinia",                  "Regione": "Campania",       "Vittime": "~3.000"},
                {"Data": "1997-09-26", "Magnitudo": 6.0, "Località": "Umbria-Marche",            "Regione": "Umbria/Marche",  "Vittime": "~11"},
                {"Data": "2002-10-31", "Magnitudo": 5.7, "Località": "Molise (San Giuliano)",    "Regione": "Molise",         "Vittime": "~30"},
                {"Data": "2009-04-06", "Magnitudo": 6.3, "Località": "L'Aquila",                 "Regione": "Abruzzo",        "Vittime": "309"},
                {"Data": "2012-05-20", "Magnitudo": 6.1, "Località": "Emilia (Finale Emilia)",  "Regione": "Emilia-Romagna", "Vittime": "27"},
                {"Data": "2016-08-24", "Magnitudo": 6.0, "Località": "Centro Italia (Amatrice)","Regione": "Lazio/Marche",   "Vittime": "299"},
                {"Data": "2016-10-30", "Magnitudo": 6.5, "Località": "Centro Italia (Norcia)",  "Regione": "Umbria",         "Vittime": "0"},
                {"Data": "2017-01-18", "Magnitudo": 5.7, "Località": "Amatrice (sequenza)",     "Regione": "Lazio",          "Vittime": "29"},
            ])
            if regione_scelta != "Italia (Visione nazionale)":
                df_filtered = df_historic[df_historic["Regione"].str.contains(
                    regione_scelta.split("/")[0], case=False, na=False)]
                if len(df_filtered) > 0:
                    df_historic = df_filtered
            st.dataframe(df_historic, width='stretch')
            st.caption("Fonte: INGV CPTI (Catalogo Parametrico dei Terremoti Italiani)")

        with st.expander("ℹ️ Informazioni sui dati sismici"):
            st.markdown("""
            ### 🔍 Rete sismica INGV in tempo reale
            La rete sismica nazionale INGV è composta da oltre **400 stazioni sismiche** su tutto il territorio italiano.
            I dati visualizzati provengono dall'API ufficiale INGV FDSN (Federation of Digital Seismograph Networks).

            **Periodo:** ultimi 7 giorni · **Magnitudo minima:** M≥0.5 · **Cache:** 5 minuti

            **Interpretazione colori sulla mappa:**
            - 🟢 Verde: M < 3.0 (molto debole, raramente avvertito)
            - 🟠 Arancione: M 3.0–3.9 (leggero, avvertito in zona epicentrale)
            - 🔴 Rosso: M ≥ 4.0 (moderato, potenzialmente dannoso)

            **Fonte:** [INGV FDSN Web Services](https://webservices.ingv.it/) · [Portale terremoti INGV](https://terremoti.ingv.it/)
            """)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — VULCANI ATTIVI
    # ══════════════════════════════════════════════════════════════════════════
    with sensor_tab2:
        st.info("🔗 Per schede dettagliate con bollettini INGV → apri **Vulcani** dal menu laterale")

        with st.spinner("⏳ Recupero attività sismica vulcani da INGV..."):
            vulc_live = _fetch_volcano_seismicity_all()

        # ── Vista nazionale ───────────────────────────────────────────────────
        if regione_scelta == "Italia (Visione nazionale)":
            st.subheader("🌋 Monitoraggio vulcani attivi italiani — dati LIVE INGV")

            # Tabella dinamica con livelli da INGV FDSN
            vulc_rows = []
            for nome, cfg in _VULCANI_MON.items():
                live = vulc_live.get(nome, {})
                count_str = f"{live.get('count', 'N/D')}" if live.get("count") is not None else "N/D"
                vulc_rows.append({
                    "Vulcano": nome,
                    "Osservatorio": cfg["obs"],
                    "Ultima eruzione": cfg["ult_eruz"],
                    "Sismicità 7gg": count_str + " eventi",
                    "Livello attività": live.get("level", "N/D"),
                    "Stato": live.get("emoji", "⚫") + " " + live.get("label", "N/D"),
                })

            df_vulcani = pd.DataFrame(vulc_rows)

            def _color_a(val):
                m = {
                    "VERDE":    "background-color:#4ade80;color:#000",
                    "GIALLO":   "background-color:#fde047;color:#000",
                    "ARANCIONE":"background-color:#fb923c;color:#000",
                    "ROSSO":    "background-color:#f87171;color:#000",
                }
                return m.get(val, "")

            df_vulcani.index = range(1, len(df_vulcani) + 1)
            n_rows = len(df_vulcani)
            tbl_h = min(500, 38 + n_rows * 36)
            st.dataframe(
                df_vulcani.style.map(_color_a, subset=["Livello attività"]),
                width='stretch', height=tbl_h
            )
            st.caption(
                f"Fonte: INGV FDSN (M≥0.5, ultimi 7 giorni) · "
                f"Aggiornato: {datetime.now(FUSO_ORARIO_ITALIA).strftime('%d/%m/%Y %H:%M')} · Cache 30 min"
            )

            # ── Mappa vulcani ─────────────────────────────────────────────────
            st.subheader("🗺️ Mappa vulcani attivi italiani")
            alert_color_map = {
                "ROSSO": "red", "ARANCIONE": "orange", "GIALLO": "beige",
                "VERDE": "green", "N/D": "gray",
            }
            vmap = folium.Map(location=[39.5, 13.5], zoom_start=5)
            for nome, cfg in _VULCANI_MON.items():
                live = vulc_live.get(nome, {})
                col_m = alert_color_map.get(live.get("level", "N/D"), "gray")
                coords = [cfg["lat"], cfg["lon"]]
                _vmg  = f"https://www.google.com/maps/dir/?api=1&destination={cfg['lat']},{cfg['lon']}&travelmode=driving"
                _vmwz = f"https://waze.com/ul?ll={cfg['lat']},{cfg['lon']}&navigate=yes"
                _vmam = f"https://maps.apple.com/?daddr={cfg['lat']},{cfg['lon']}&dirflg=d"
                popup_html = (
                    '<div style="min-width:230px;font-family:sans-serif;font-size:13px;">'
                    f'<h4 style="color:#DC2626;margin:0 0 6px 0;font-size:14px;border-bottom:2px solid #DC2626;padding-bottom:3px;">🌋 {nome}</h4>'
                    f'<p style="margin:0 0 2px 0;"><b>Osservatorio:</b> {cfg["obs"]}</p>'
                    f'<p style="margin:0 0 2px 0;"><b>Ultima eruzione:</b> {cfg["ult_eruz"]}</p>'
                    f'<p style="margin:0 0 2px 0;"><b>Sismicità (7gg):</b> {live.get("label", "N/D")}</p>'
                    f'<p style="margin:0 0 6px 0;"><b>Livello:</b> {live.get("emoji","⚫")} {live.get("level","N/D")}</p>'
                    f'<p style="font-size:10px;color:#888;font-family:monospace;">{cfg["lat"]:.4f}, {cfg["lon"]:.4f}</p>'
                    '<div style="display:flex;gap:4px;">'
                    f'<a href="{_vmg}" target="_blank" style="background:#4285F4;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🗺️ GMaps</a>'
                    f'<a href="{_vmwz}" target="_blank" style="background:#00BCD4;color:#000;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🚗 Waze</a>'
                    f'<a href="{_vmam}" target="_blank" style="background:#555;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🍎 Maps</a>'
                    '</div></div>'
                )
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html, max_width=280),
                    icon=folium.Icon(color=col_m, icon="fire", prefix="fa"),
                    tooltip=nome,
                ).add_to(vmap)

            folium_static(vmap, width=1100, height=520)
            st.caption("Colori: 🟢 Verde=Silente · 🟡 Giallo=Bassa attività · 🟠 Arancione=Moderata · 🔴 Rosso=Elevata")

            # Tabella vulcani estesa (inclusi tutti i vulcani italiani)
            st.markdown("---")
            st.subheader("📋 Elenco completo vulcani italiani monitorati INGV")
            df_full = pd.DataFrame([
                {"Vulcano": "Etna",              "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "Attivo"},
                {"Vulcano": "Stromboli",          "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "Attivo"},
                {"Vulcano": "Campi Flegrei",      "Regione": "Campania",             "Monitoraggio": "INGV-OV", "Ultima eruzione": "1538"},
                {"Vulcano": "Vesuvio",            "Regione": "Campania",             "Monitoraggio": "INGV-OV", "Ultima eruzione": "1944"},
                {"Vulcano": "Ischia",             "Regione": "Campania",             "Monitoraggio": "INGV-OV", "Ultima eruzione": "1302"},
                {"Vulcano": "Vulcano",            "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "1888-90"},
                {"Vulcano": "Pantelleria",        "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "1891 (sub.)"},
                {"Vulcano": "Lipari-Vulcanello",  "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "1230"},
                {"Vulcano": "Panarea",            "Regione": "Sicilia (Eolie)",      "Monitoraggio": "INGV-CT", "Ultima eruzione": "2002 (sub.)"},
                {"Vulcano": "Marsili",            "Regione": "Mar Tirreno",          "Monitoraggio": "INGV",    "Ultima eruzione": "Non doc. (sub.)"},
                {"Vulcano": "Ferdinandea",        "Regione": "Canale di Sicilia",    "Monitoraggio": "INGV",    "Ultima eruzione": "1831 (sub.)"},
                {"Vulcano": "Colli Albani",       "Regione": "Lazio",                "Monitoraggio": "INGV-RM", "Ultima eruzione": "5000 a.f."},
                {"Vulcano": "Monte Amiata",       "Regione": "Toscana",              "Monitoraggio": "INGV-RM", "Ultima eruzione": "180 a.f."},
                {"Vulcano": "Ustica",             "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "Quiescente"},
                {"Vulcano": "Linosa",             "Regione": "Sicilia",              "Monitoraggio": "INGV-CT", "Ultima eruzione": "Quiescente"},
            ])
            df_full.index = range(1, len(df_full) + 1)
            st.dataframe(df_full, width='stretch')

        else:
            # ── Vista per regione specifica ───────────────────────────────────
            # Solo vulcani presenti in _VULCANI_MON (con dati live INGV/EMSC)
            # Lipari-Vulcanello, Ustica, Linosa, Monte Amiata non hanno monitoraggio
            # in tempo reale → sono nell'elenco completo ma non nel selectbox
            # Marsili è in mare aperto → solo vista nazionale
            regioni_vulcaniche = {
                "Campania": ["Vesuvio", "Campi Flegrei", "Ischia"],
                "Sicilia":  ["Etna", "Stromboli", "Vulcano", "Pantelleria", "Panarea"],
                "Lazio":    ["Colli Albani"],
            }

            if regione_scelta in regioni_vulcaniche:
                st.subheader(f"🌋 Monitoraggio vulcanico — {regione_scelta}")
                vulcani_disponibili = regioni_vulcaniche[regione_scelta]
                vulcano_selezionato = st.selectbox("Seleziona vulcano", vulcani_disponibili)

                # ── Scheda dettaglio per ogni vulcano ─────────────────────────
                live_v = vulc_live.get(vulcano_selezionato, {})
                count_v = live_v.get("count")
                level_v = live_v.get("level", "N/D")
                emoji_v = live_v.get("emoji", "⚫")
                label_v = live_v.get("label", "N/D")

                # Colore banner stato
                if level_v == "ROSSO":
                    st.error(f"🔴 Attività vulcanica ELEVATA — {vulcano_selezionato}: {label_v}")
                elif level_v == "ARANCIONE":
                    st.warning(f"🟠 Attività vulcanica MODERATA — {vulcano_selezionato}: {label_v}")
                elif level_v == "GIALLO":
                    st.warning(f"🟡 Attività vulcanica BASSA — {vulcano_selezionato}: {label_v}")
                else:
                    st.success(f"🟢 Vulcano SILENTE — {vulcano_selezionato}: {label_v}")

                cfg_v = _VULCANI_MON.get(vulcano_selezionato, {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Sismicità (ultimi 7gg)",
                        f"{count_v} eventi" if count_v is not None else "N/D",
                        help="M≥0.5 · Fonte INGV FDSN · Cache 30 min"
                    )
                with col2:
                    st.metric("Livello attività INGV FDSN", f"{emoji_v} {level_v}")
                with col3:
                    st.metric("Osservatorio", cfg_v.get("obs", "INGV"))

                # Link diretti INGV per questo vulcano
                ingv_links = {
                    "Vesuvio":       "https://www.ov.ingv.it/index.php/rete-fissa",
                    "Campi Flegrei": "https://www.ov.ingv.it/index.php/rete-fissa",
                    "Ischia":        "https://www.ov.ingv.it/index.php/rete-fissa",
                    "Etna":          "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
                    "Stromboli":     "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
                    "Vulcano":       "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
                    "Pantelleria":   "https://www.ct.ingv.it/",
                    "Panarea":       "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
                    "Colli Albani":  "https://www.roma2.ingv.it/",
                }
                ingv_webcam = {
                    "Etna":      "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/immagini-da-webcam",
                    "Stromboli": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/immagini-da-webcam",
                    "Vesuvio":   "https://www.ov.ingv.it/",
                }
                link = ingv_links.get(vulcano_selezionato, "https://www.ingv.it/")
                webcam = ingv_webcam.get(vulcano_selezionato)

                st.markdown(f"📄 [Bollettino settimanale INGV per {vulcano_selezionato}]({link})")
                if webcam:
                    st.markdown(f"📷 [Webcam in tempo reale INGV]({webcam})")
                st.caption(
                    f"Dati sismici: INGV FDSN · M≥0.5 · Raggio {cfg_v.get('rad', 0)*111:.0f} km · "
                    f"Aggiornato: {datetime.now(FUSO_ORARIO_ITALIA).strftime('%H:%M')} · Cache 30 min"
                )

                # Informazioni descrittive per vulcano
                vulc_info = {
                    "Vesuvio": """
**Il Vesuvio** è un vulcano attivo situato in Campania, nell'area metropolitana di Napoli.
L'ultima eruzione significativa è avvenuta nel **marzo 1944**.
Il monitoraggio interessa 25 comuni, con **circa 700.000 abitanti** nell'area a rischio.

**Livelli di allerta DPC:**
- 🟢 VERDE: Attività di base (livello attuale)
- 🟡 GIALLO: Variazioni significative dei parametri
- 🟠 ARANCIONE: Ulteriore incremento dei parametri
- 🔴 ROSSO: Eruzione imminente o in corso

[Osservatorio Vesuviano INGV](https://www.ov.ingv.it/)
                    """,
                    "Campi Flegrei": """
**I Campi Flegrei** sono un'ampia area vulcanica situata ad ovest di Napoli. L'ultima eruzione è avvenuta nel **1538** con la formazione di Monte Nuovo.
**Fenomeno attuale:** bradisismo, con sollevamento del suolo e intensa attività sismica.
Il monitoraggio interessa **7 comuni** con circa **500.000 abitanti**.

**Livelli di allerta DPC:**
- 🟢 VERDE: Attività di base
- 🟡 GIALLO: Variazioni significative dei parametri (livello attuale)
- 🟠 ARANCIONE: Ulteriore incremento
- 🔴 ROSSO: Eruzione imminente o in corso

[Osservatorio Vesuviano INGV](https://www.ov.ingv.it/)
                    """,
                    "Etna": """
**L'Etna** è il più grande vulcano attivo d'Europa e uno dei più attivi al mondo, sulla costa orientale della Sicilia.
**Attività tipica:** frequenti eruzioni sommitali con attività stromboliana, fontane di lava ed emissioni di cenere.
**Popolazione esposta:** oltre **500.000 abitanti** nella provincia di Catania.

[INGV Catania](https://www.ct.ingv.it/)
                    """,
                    "Stromboli": """
**Lo Stromboli** è un vulcano attivo sull'omonima isola delle Eolie, noto per la sua **attività esplosiva persistente** (esplosioni ogni 10–20 minuti).
**Popolazione:** circa **500 residenti**, che aumentano significativamente in estate.
Occasionalmente genera **parossismi** e colate laviche.

[INGV Catania](https://www.ct.ingv.it/)
                    """,
                    "Vulcano": """
**Vulcano** è un'isola vulcanica delle Eolie. L'ultima eruzione è avvenuta nel **1888-1890**.
**Attività attuale:** intensa attività fumarolica con temperature elevate e significative emissioni di gas.
**Crisi 2021:** aumento delle temperature fumaroliche, emissioni di gas e sismicità.

[INGV Catania](https://www.ct.ingv.it/)
                    """,
                    "Ischia": """
**Ischia** è un'isola vulcanica nel Golfo di Napoli. L'ultima eruzione risale al **1302**.
L'isola è caratterizzata da intensa attività idrotermale e fumarolica.
Sismicità locale significativa (terremoto M4.0 agosto 2017).

[Osservatorio Vesuviano INGV](https://www.ov.ingv.it/)
                    """,
                    "Pantelleria": """
**Pantelleria** è un'isola vulcanica nel Canale di Sicilia. L'ultima eruzione sottomarina risale al **1891**.
L'isola presenta attività fumarolica e sorgenti termali.

[INGV Catania](https://www.ct.ingv.it/)
                    """,
                    "Colli Albani": """
**I Colli Albani** sono un sistema vulcanico nel Lazio a sud-est di Roma. L'ultima eruzione è avvenuta circa **5000 anni fa**.
Il vulcano è considerato **potenzialmente attivo** con sismicità locale e degassamento.

[INGV Roma](https://www.roma2.ingv.it/)
                    """,
                    "Panarea": """
**Panarea** è la più piccola isola delle Eolie (Messina) ed è un vulcano sottomarino attivo.
Nel **2002** si è verificata un'improvvisa emissione gassosa sottomarina con formazione di nuova attività idrotermale.
Presenta costante attività fumarolica sottomarina e sorgenti idrotermali.
Il settore submarino si trova a profondità tra 10 e 300 m.

[INGV Catania](https://www.ct.ingv.it/)
                    """,
                }
                with st.expander(f"ℹ️ Informazioni su {vulcano_selezionato}"):
                    st.markdown(vulc_info.get(vulcano_selezionato,
                        f"Consulta il portale INGV per informazioni dettagliate su {vulcano_selezionato}."))

            else:
                st.info(f"Non ci sono vulcani con monitoraggio sismico live nella regione **{regione_scelta}**.")
                st.markdown("""
                ### 🌋 Regioni con vulcani monitorati in tempo reale (INGV FDSN):
                - **Campania**: Vesuvio, Campi Flegrei, Ischia
                - **Sicilia**: Etna, Stromboli, Vulcano, Pantelleria, Panarea
                - **Lazio**: Colli Albani

                _Altri vulcani quiescenti (Monte Amiata, Lipari, Ustica, Linosa) e subacquei (Marsili)
                sono presenti nell'**elenco completo** nella vista nazionale._

                Seleziona una di queste regioni o **"Italia (Visione nazionale)"** per i dati live.
                """)

        with st.expander("ℹ️ Metodologia livelli di allerta vulcanica"):
            st.markdown("""
            ### 🌋 Livelli attività vulcanica — Metodologia INGV FDSN

            I livelli sono derivati dal conteggio degli **eventi sismici M≥0.5** negli ultimi 7 giorni
            nell'area circostante ogni vulcano, tramite l'API ufficiale INGV FDSN:

            | Livello | Soglia | Significato |
            |---------|--------|-------------|
            | 🟢 VERDE    | 0 eventi   | Vulcano silente |
            | 🟡 GIALLO   | 1–4 eventi | Bassa attività sismica |
            | 🟠 ARANCIONE| 5–19 eventi| Attività sismica moderata |
            | 🔴 ROSSO    | 20+ eventi | Elevata attività sismica |

            **Nota:** La sismicità è un parametro primario di monitoraggio.
            Per il livello di allerta ufficiale DPC, consultare [Protezione Civile](https://www.protezionecivile.gov.it/).

            **Cache:** dati aggiornati ogni 30 minuti · Fonte: webservices.ingv.it/fdsnws
            """)

    # Nota: il monitoraggio idrogeologico è disponibile nella sezione
    # "📊 Allerte e Rischi" del menu laterale (tab Idrogeologico).

    # ── placeholder per futura espansione ────────────────────────────────────
    if False:
        regione_link = {
            "Abruzzo": "https://allarmeteo.regione.abruzzo.it/",
            "Basilicata": "http://www.centrofunzionalebasilicata.it/it/home.php",
            "Calabria": "http://www.cfd.calabria.it/",
            "Campania": "http://centrofunzionale.regione.campania.it/#/pages/dashboard",
            "Emilia-Romagna": "https://allertameteo.regione.emilia-romagna.it/",
            "Friuli-Venezia Giulia": "https://www.osmer.fvg.it/udine.php",
            "Lazio": "https://www.regione.lazio.it/centrofunzionale",
            "Liguria": "https://allertaliguria.regione.liguria.it/",
            "Lombardia": "https://www.arpalombardia.it/temi-ambientali/idrologia/siti-enti-terzi/",
            "Marche": "https://www.regione.marche.it/Regione-Utile/Protezione-Civile/Strutture-Operative/Centro-Funzionale-Multirischi",
            "Molise": "http://www.protezionecivile.molise.it/meteo-e-centro-funzionale/previsioni-meteo.html",
            "Piemonte": "https://www.arpa.piemonte.it/rischi_naturali/index.html",
            "Puglia": "https://www.protezionecivile.puglia.it/centro-funzionale",
            "Sardegna": "https://www.sardegnaambiente.it/servizi/allertediprotezionecivile/",
            "Sicilia": "https://www.protezionecivilesicilia.it/it/",
            "Toscana": "https://www.cfr.toscana.it/",
            "Trentino-Alto Adige": "https://allerte.provincia.bz.it/",
            "Umbria": "https://www.cfumbria.it/",
            "Valle d'Aosta": "https://cf.regione.vda.it/",
            "Veneto": "https://www.arpa.veneto.it/bollettini/meteo60gg/prociv.php",
            "Italia (Visione nazionale)": "https://www.protezionecivile.gov.it/it/risk-activities/meteo-hydro/activities/forecasting-prevention/central-functional-center",
        }

        # ── Allerte MeteoAlarm live ───────────────────────────────────────────
        @st.cache_data(ttl=1800, show_spinner=False)
        def _meteoalarm_allerte_italia():
            try:
                url = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-italy"
                r = requests.get(url, timeout=10)
                if r.status_code != 200:
                    return []
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                ns = {"atom": "http://www.w3.org/2005/Atom",
                      "cap":  "urn:oasis:names:tc:emergency:cap:1.2"}
                allerte = []
                for entry in root.findall("atom:entry", ns):
                    title   = entry.findtext("atom:title", "", ns)
                    summary = entry.findtext("atom:summary", "", ns)
                    allerte.append({"titolo": title, "sommario": summary})
                return allerte
            except Exception:
                return []

        allerte = _meteoalarm_allerte_italia()
        st.subheader("🚨 Allerta idrogeologica e meteo")

        regione_key = regione_scelta.lower().replace("-", " ").replace("'", "")
        allerte_reg = [a for a in allerte
                       if regione_key in a["titolo"].lower() or regione_key in a["sommario"].lower()]

        if allerte_reg:
            for a in allerte_reg:
                titolo = a["titolo"]
                tl = titolo.lower()
                if "red" in tl or "rossa" in tl:
                    st.error(f"🔴 {titolo}")
                elif "orange" in tl or "arancione" in tl:
                    st.warning(f"🟠 {titolo}")
                elif "yellow" in tl or "gialla" in tl:
                    st.warning(f"🟡 {titolo}")
                else:
                    st.info(f"ℹ️ {titolo}")
        elif allerte:
            st.success(f"✅ Nessuna allerta MeteoAlarm attiva per {regione_scelta}")
        else:
            st.info("ℹ️ Feed MeteoAlarm temporaneamente non disponibile — consulta il portale regionale")

        st.caption(f"Fonte: MeteoAlarm (EUMETNET) · Aggiornato: {datetime.now(FUSO_ORARIO_ITALIA).strftime('%d/%m/%Y %H:%M')}")

        # ── Dati ISPRA nazionali ──────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Rischio idrogeologico nazionale — dati ISPRA")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Zone a rischio frana",    "1.281.970 ha", "Classificazione PAI")
        c2.metric("Comuni a rischio frana",  "7.275",        "su 7.904 totali (91,9%)")
        c3.metric("Zone a rischio alluvione","2.062.475 ha", "Classificazione PAI")
        c4.metric("Popolazione esposta",     "≈ 7,5 M",      "abitanti (12,5% d'Italia)")
        st.caption("Fonte: ISPRA — Rapporto sul dissesto idrogeologico in Italia")

        st.markdown("#### 🗺️ Mappa pericolosità da frana — ISPRA IdroGEO")
        st.markdown(
            "[![Mappa ISPRA pericolosità frane]"
            "(https://idrogeo.isprambiente.it/app/static/img/idrogeo-logo.png)]"
            "(https://idrogeo.isprambiente.it/app/page/Italy)"
        )
        st.info(
            "📍 Consulta la mappa interattiva IdroGEO di ISPRA per visualizzare la pericolosità "
            "da frana e alluvione fino al livello comunale: "
            "[idrogeo.isprambiente.it](https://idrogeo.isprambiente.it/app/page/Italy)"
        )

        # ── Portali ufficiali ─────────────────────────────────────────────────
        with st.expander("🔗 Portali ufficiali monitoraggio idrogeologico"):
            if regione_scelta in regione_link:
                st.markdown(f"**[Centro Funzionale {regione_scelta}]({regione_link[regione_scelta]})**")
            st.markdown("""
            **Portali nazionali:**
            - [DPC — Mappa allerte in tempo reale](https://mappe.protezionecivile.gov.it/)
            - [DPC — Centro Funzionale Centrale](https://www.protezionecivile.gov.it/it/risk-activities/meteo-hydro/activities/forecasting-prevention/central-functional-center)
            - [ISPRA — IdroGEO (frane e alluvioni)](https://idrogeo.isprambiente.it/)
            - [MeteoAlarm Italia](https://www.meteoalarm.org/it/live/?s=italy)
            - [Aeronautica Militare — CNMCA](https://www.meteoam.it/)
            """)


def show_monitoraggio_idrogeologico():
    st.subheader("📊 Monitoraggio idrogeologico — Italia")
    st.markdown("### 📈 Dati di rischio idrogeologico nazionale")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Zone a rischio frana",    "1.281.970 ha", "Alta criticità")
        st.metric("Comuni interessati",      "7.275",         "su 7.904 totali")
    with col2:
        st.metric("Zone a rischio alluvione","2.062.475 ha", "Alta criticità")
        st.metric("Popolazione esposta",     "≈ 7,5 M",      "abitanti")
    st.caption("Dati: ISPRA · Aggiornato: " + datetime.now(FUSO_ORARIO_ITALIA).strftime("%d/%m/%Y %H:%M") + " (IT)")
    st.markdown("### 🗺️ Mappa delle zone a rischio idrogeologico")
    st.info(
        "📍 Consulta la mappa interattiva ISPRA IdroGEO: "
        "[idrogeo.isprambiente.it](https://idrogeo.isprambiente.it/app/page/Italy)"
    )
