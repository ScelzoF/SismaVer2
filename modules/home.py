"""
home.py — Home page SismaVer2 v3.1
Dashboard live: KPI reali (1 sola chiamata INGV), vulcani, EMSC, MeteoAlarm, notizie DPC
"""
import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH = True
except ImportError:
    _AUTOREFRESH = False


def _get_tz():
    now = datetime.now(); y = now.year
    ds = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
    de = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if ds <= now.replace(tzinfo=None) < de else 1))

FUSO_ORARIO_ITALIA = _get_tz()


# ── Unica chiamata INGV per tutti i KPI + lista terremoti ────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_ingv_7days():
    """Una sola chiamata INGV (7 giorni, M≥1.0). Usata da KPI e lista recenti."""
    try:
        start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        r = requests.get(
            f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
            f"&starttime={start}&minmag=1.0"
            f"&minlat=35.0&maxlat=48.0&minlon=5.0&maxlon=20.0"
            f"&limit=500&orderby=time",
            timeout=10)
        if r.status_code == 200:
            return r.json().get("features", [])
    except Exception:
        pass
    return []


def _parse_ingv_kpi(features):
    """Calcola KPI dalla lista features INGV già scaricata."""
    oggi_str = datetime.utcnow().strftime("%Y-%m-%dT00:00:00")
    oggi_dt  = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    quakes_today = 0
    quakes_week  = len(features)
    max_mag_val  = None
    max_mag_feat = None
    recenti = []  # ultimi 7 M≥1.5

    for f in features:
        p = f.get("properties", {})
        g = f.get("geometry", {}).get("coordinates", [])
        mag  = float(p.get("mag") or 0)
        t    = p.get("time")

        # Data/ora
        try:
            if isinstance(t, (int, float)):
                dt = datetime.utcfromtimestamp(t / 1000.0)
            else:
                raw = str(t).replace("Z", "").replace("+00:00", "")
                dt  = datetime.fromisoformat(raw)
        except Exception:
            dt = None

        # Conta oggi
        if dt and dt >= oggi_dt:
            quakes_today += 1

        # Max magnitude
        if max_mag_val is None or mag > max_mag_val:
            max_mag_val  = mag
            max_mag_feat = f

        # Lista recenti M≥1.5
        if mag >= 1.5 and len(recenti) < 7:
            if dt:
                dt_it = datetime.fromtimestamp(
                    t / 1000.0 if isinstance(t, (int, float)) else dt.timestamp(),
                    FUSO_ORARIO_ITALIA)
                ora_str = dt_it.strftime("%d/%m %H:%M")
            else:
                ora_str = "—"
            recenti.append({
                "mag":   mag,
                "luogo": p.get("place", "N/D"),
                "ora":   ora_str,
                "prof":  round(float(g[2]), 1) if len(g) > 2 else None,
            })

    # Max mag info
    max_mag_str = "—"
    max_mag_ora = "—"
    if max_mag_feat and max_mag_val:
        p = max_mag_feat.get("properties", {})
        max_mag_str = f"M {max_mag_val:.1f}"
        t = p.get("time")
        if isinstance(t, (int, float)):
            dt_it = datetime.fromtimestamp(t / 1000.0, FUSO_ORARIO_ITALIA)
            max_mag_ora = dt_it.strftime("%H:%M")

    return {
        "quakes_today": str(quakes_today),
        "quakes_week":  str(quakes_week),
        "max_mag":      max_mag_str,
        "max_mag_ora":  max_mag_ora,
        "recenti":      recenti,
    }


def _fetch_meteoalarm():
    """
    MeteoAlarm: conta allerte attive Italia + lista dettagli (regione, tipo, livello).
    Usa fetch_meteoalarm_raw() dalla cache CONDIVISA con rischi_allerte.py →
    home e Allerte mostrano SEMPRE lo stesso numero.
    """
    import xml.etree.ElementTree as ET
    from modules.meteoalarm_cache import fetch_meteoalarm_raw
    NS = "{http://www.w3.org/2005/Atom}"
    TYPE_MAP = {
        "Wind": "Vento", "Thunderstorm": "Temporali", "Rain": "Pioggia",
        "Snow": "Neve", "Ice": "Ghiaccio", "Fog": "Nebbia",
        "Flood": "Alluvione", "Coast": "Coste", "Fire": "Incendi",
        "Avalanche": "Valanghe", "Heat": "Caldo", "Cold": "Freddo",
        "Dust": "Sabbia/Polvere",
    }
    LEVEL_MAP = {
        "Red":    ("🔴", "Rossa"),
        "Orange": ("🟠", "Arancione"),
        "Yellow": ("🟡", "Gialla"),
        "Green":  ("🟢", "Verde"),
    }
    raw = fetch_meteoalarm_raw()   # cache condivisa 2 min
    if not raw:
        return None, []
    try:
        root = ET.fromstring(raw)
        entries = root.findall(f".//{NS}entry")
        if not entries:
            entries = root.findall(".//entry")
        details = []
        for entry in entries:
            title = (entry.findtext(f"{NS}title") or
                     entry.findtext("title") or "").strip()
            region = title.split(" - ")[-1].strip() if " - " in title else "Italia"
            dot, level_it = "🟡", "Gialla"
            for lvl_en, (d, l) in LEVEL_MAP.items():
                if lvl_en in title:
                    dot, level_it = d, l
                    break
            tipo = "Meteo"
            for t_en, t_it in TYPE_MAP.items():
                if t_en in title:
                    tipo = t_it
                    break
            details.append({
                "region": region, "tipo": tipo,
                "level": level_it, "dot": dot,
            })
        _ord = {"Rossa": 0, "Arancione": 1, "Gialla": 2, "Verde": 3}
        details.sort(key=lambda x: _ord.get(x["level"], 9))
        return len(entries), details
    except Exception:
        pass
    return None, []


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_emsc_quick():
    """EMSC: eventi M≥4.5 nel Mediterraneo ultime 24h."""
    try:
        start = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        r = requests.get(
            f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json"
            f"&starttime={start}&minmag=4.5"
            f"&minlat=28.0&maxlat=48.0&minlon=-10.0&maxlon=42.0"
            f"&limit=10&orderby=time",
            timeout=8)
        if r.status_code == 200:
            events = []
            for f in r.json().get("features", []):
                p = f.get("properties", {})
                g = f.get("geometry", {}).get("coordinates", [])
                mag = float(p.get("mag") or p.get("magnitude") or 0)
                luogo = p.get("place") or p.get("flynn_region") or "N/D"
                t = p.get("time") or p.get("lastupdate")
                ora_str = "—"
                if t:
                    try:
                        if isinstance(t, (int, float)):
                            dt = datetime.fromtimestamp(t / 1000.0, FUSO_ORARIO_ITALIA)
                        else:
                            dt = datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(FUSO_ORARIO_ITALIA)
                        ora_str = dt.strftime("%d/%m %H:%M")
                    except Exception:
                        pass
                events.append({"mag": mag, "luogo": luogo, "ora": ora_str})
            return events
    except Exception:
        pass
    return []


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_dpc_news():
    """
    Notizie rilevanti: INGV Blog (sismica/vulcani) + ANSA Cronaca filtrata per emergenza.
    governo.it rimosso: mostra solo comunicati CdM, non pertinenti a Protezione Civile.
    """
    import re as _re
    import xml.etree.ElementTree as ET

    # Parole chiave SPECIFICHE per notizie di emergenza/rischio naturale
    # Solo il TITOLO viene controllato per ANSA (descrizioni troppo rumorose)
    _KW = {
        "terremot", "sisma", "vulcan", "eruzion",
        "alluvion", "inondazion", "frana", "emergenza",
        "protezione civile", "allerta", "maremoto", "tsunami",
        "esondazion", "valanga", "calamit", "disastro",
        "stato di emergenza",
    }

    def _is_relevant(title: str) -> bool:
        t = title.lower()
        return any(kw in t for kw in _KW)

    def _parse_feed(content: bytes, label: str, max_items: int, filter_kw: bool):
        """Pulisce il feed XML e ne estrae gli item."""
        cleaned = _re.sub(rb"\s+async(?=[\s/>])", b"", content)
        cleaned = _re.sub(rb"\s+defer(?=[\s/>])", b"", cleaned)
        root = ET.fromstring(cleaned)
        out = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link  = item.findtext("link",  "#").strip()
            date  = item.findtext("pubDate", "").strip()
            if not title:
                continue
            # Per ANSA: controllo solo il TITOLO (non la descrizione — troppo rumorosa)
            if filter_kw and not _is_relevant(title):
                continue
            out.append({"title": title, "link": link, "date": date, "source": label})
            if len(out) >= max_items:
                break
        return out

    sources = [
        # INGV Blog — tutti gli articoli sono pertinenti, nessun filtro
        ("https://ingvterremoti.com/feed",
         "INGV Blog — Comunicati scientifici", 5, False),
        # ANSA Cronaca — solo notizie di emergenza/disastro naturale
        ("https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",
         "ANSA — Emergenza & Sicurezza", 4, True),
    ]

    all_items = []
    for url, label, max_n, do_filter in sources:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "SismaVer2/3.4"})
            if r.status_code == 200 and len(r.content) > 200:
                all_items.extend(_parse_feed(r.content, label, max_n, do_filter))
        except Exception:
            pass
    return all_items[:8]


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_volcano_activity():
    """Sismicità aree vulcaniche principali INGV — 10 vulcani (incl. Marsili e Panarea)."""
    vulcani = {
        "Etna":          (37.755, 14.995, 0.20),
        "Stromboli":     (38.789, 15.213, 0.12),
        "Campi Flegrei": (40.827, 14.139, 0.15),
        "Vesuvio":       (40.821, 14.426, 0.10),
        "Vulcano":       (38.404, 14.962, 0.12),
        "Ischia":        (40.731, 13.897, 0.10),
        "Pantelleria":   (36.769, 12.021, 0.10),
        "Colli Albani":  (41.757, 12.700, 0.12),
        "Marsili":       (39.270, 14.400, 0.30),   # più grande vulcano europeo - sottomarino
        "Panarea":       (38.636, 15.064, 0.10),   # sistema idrotermale Eolie
    }
    result = {}
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

    def _one(name, lat, lon, rad):
        try:
            r = requests.get(
                f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
                f"&starttime={start}&minmag=0.5&lat={lat}&lon={lon}&maxradius={rad}&limit=50",
                timeout=6)
            if r.status_code == 200:
                return name, len(r.json().get("features", []))
        except Exception:
            pass
        return name, None

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_one, n, la, lo, ra): n for n, (la, lo, ra) in vulcani.items()}
        for ft in as_completed(futs):
            name, count = ft.result()
            result[name] = count
    # Ordina per attività decrescente (silente in fondo)
    return dict(sorted(result.items(), key=lambda x: (x[1] or -1), reverse=True))


def _mag_color(mag):
    try:
        m = float(mag)
        if m >= 5.0: return "#EF4444", "🔴"
        if m >= 4.0: return "#F97316", "🟠"
        if m >= 3.0: return "#FBBF24", "🟡"
        return "#10B981", "🟢"
    except Exception:
        return "#94A3B8", "⚫"


def _tsunami_level(events):
    if not events:
        return 0, "🟢 Nessun rischio", "#10B981"
    max_mag = max(e["mag"] for e in events)
    if max_mag >= 7.0:
        return 3, f"🔴 RISCHIO ELEVATO — evento M{max_mag:.1f} rilevato", "#EF4444"
    if max_mag >= 5.5:
        return 2, f"🟠 ATTENZIONE — M{max_mag:.1f} nel Mediterraneo", "#F97316"
    if max_mag >= 4.5:
        return 1, f"🟡 Monitoraggio — M{max_mag:.1f} nel Mediterraneo", "#FBBF24"
    return 0, "🟢 Nessun rischio rilevato", "#10B981"


# ── MAIN SHOW ────────────────────────────────────────────────────────────────

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

    if _AUTOREFRESH:
        st_autorefresh(interval=300_000, limit=None, key="home_autorefresh")

    ora = datetime.now(FUSO_ORARIO_ITALIA)
    from modules.banner_utils import banner_home
    banner_home()

    st.markdown(
        f"<p style='color:#64748B;font-size:0.9rem;margin-top:0;margin-bottom:1rem;'>"
        f"Dati da INGV · EMSC · Protezione Civile · MeteoAlarm · Open-Meteo · "
        f"Aggiornato: <b>{ora.strftime('%d/%m/%Y %H:%M')}</b> (IT) · "
        f"<i>Auto-refresh 5 min</i></p>",
        unsafe_allow_html=True,
    )

    # ── Caricamento parallelo ─────────────────────────────────────────────────
    with st.spinner("Caricamento dati in tempo reale..."):
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_ingv  = ex.submit(_fetch_ingv_7days)
            f_emsc  = ex.submit(_fetch_emsc_quick)
            f_ma    = ex.submit(_fetch_meteoalarm)
            ingv_features = f_ingv.result()
            emsc_events   = f_emsc.result()
            ma_count, ma_details = f_ma.result()

    kpi = _parse_ingv_kpi(ingv_features)

    # ── Banner allerta dinamico ───────────────────────────────────────────────
    ts_level, ts_msg, ts_color = _tsunami_level(emsc_events)
    if ts_level >= 2:
        st.markdown(f"""
        <div style="background:linear-gradient(90deg,{ts_color} 0%,{ts_color}CC 100%);
                    color:white;text-align:center;padding:10px 16px;border-radius:10px;
                    font-weight:700;font-size:1rem;margin-bottom:12px;
                    box-shadow:0 4px 12px rgba(0,0,0,0.25);">
            ⚠️ {ts_msg} —
            <a href='https://www.ingv.it/cat/' target='_blank'
               style='color:white;text-decoration:underline;'>CAT-INGV ufficiale</a>
        </div>""", unsafe_allow_html=True)
    elif ma_count and ma_count > 5:
        st.markdown(f"""
        <div style="background:linear-gradient(90deg,#F97316 0%,#EA580C 100%);
                    color:white;text-align:center;padding:8px 16px;border-radius:10px;
                    font-weight:700;font-size:0.95rem;margin-bottom:12px;">
            ⚠️ MeteoAlarm: {ma_count} allerte meteo attive per l'Italia
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:linear-gradient(90deg,#059669 0%,#047857 100%);
                    color:white;text-align:center;padding:7px 16px;border-radius:10px;
                    font-weight:600;font-size:0.88rem;margin-bottom:12px;">
            ✅ Nessuna allerta critica in corso · tutti i sistemi operativi
        </div>""", unsafe_allow_html=True)

    # ── KPI live ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍 Terremoti oggi",    kpi["quakes_today"],    "M≥1.0 — INGV")
    c2.metric("📅 Questa settimana",  kpi["quakes_week"],     "M≥1.0 · 7 giorni")
    c3.metric("⚡ Più forte (7gg)",   kpi["max_mag"],         kpi["max_mag_ora"] or "—")
    ma_label = f"{ma_count} allerte" if ma_count is not None else "N/D"
    c4.metric("⚠️ Allerte MeteoAlarm", ma_label,             "Italia · MeteoAlarm EU")

    if ma_count and ma_count > 0:
        st.caption(
            f"📋 Dettaglio allerte per regione → sezione **📊 Allerte e Rischi** (Tab Meteo)"
        )

    st.markdown("---")

    # ── Terremoti recenti + attività vulcanica ────────────────────────────────
    col_q, col_v = st.columns([3, 2], gap="medium")

    with col_q:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <span style="font-size:1.4rem;">🌊</span>
            <span style="font-size:1.15rem;font-weight:700;color:#0F172A;">Ultimi terremoti in Italia</span>
            <span style="background:#EFF6FF;color:#1D4ED8;font-size:0.72rem;font-weight:700;
                padding:2px 8px;border-radius:10px;border:1px solid #BFDBFE;">LIVE</span>
        </div>""", unsafe_allow_html=True)

        recenti = kpi["recenti"]
        if recenti:
            for q in recenti:
                color, dot = _mag_color(q["mag"])
                try:
                    bar_w = min(100, int((q["mag"] / 7.0) * 100))
                except Exception:
                    bar_w = 20
                prof_str = f"{q['prof']} km" if q["prof"] else "—"
                st.markdown(
                    f"""<div class="quake-card" style="border-left:4px solid {color};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:1.2rem;font-weight:800;color:{color};">
                            {dot} M {q['mag']:.1f}
                        </span>
                        <span style="font-size:0.78rem;color:#94A3B8;font-weight:500;">
                            ⏱ {q['ora']} &nbsp;|&nbsp; 🔻 {prof_str}
                        </span>
                    </div>
                    <div style="font-size:0.9rem;color:#334155;margin-top:3px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {q['luogo']}
                    </div>
                    <div style="margin-top:5px;height:4px;background:#F1F5F9;
                        border-radius:2px;overflow:hidden;">
                        <div style="height:4px;width:{bar_w}%;background:{color};
                            border-radius:2px;opacity:0.6;"></div>
                    </div></div>""",
                    unsafe_allow_html=True)
        else:
            st.info("Dati INGV in caricamento — riprova tra qualche secondo")

        st.caption("Fonte: INGV FDSN · M≥1.5 · ultimi 7 giorni · max 7 eventi")

    with col_v:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-size:1.4rem;">🌋</span>
            <span style="font-size:1.15rem;font-weight:700;color:#0F172A;">Attività vulcanica — 7 giorni</span>
        </div>""", unsafe_allow_html=True)

        with st.spinner("Controllo attività vulcani..."):
            vact = _fetch_volcano_activity()

        # Griglia 2 colonne per riempire lo spazio verticale
        vnames = list(vact.items())
        vcol1, vcol2 = st.columns(2, gap="small")
        for i, (name, n) in enumerate(vnames):
            if n is None:
                dot, label, bg, fg = "⚫", "N/D",          "#F8FAFC", "#94A3B8"
            elif n == 0:
                dot, label, bg, fg = "🟢", "Silente",      "#F0FDF4", "#166534"
            elif n < 5:
                dot, label, bg, fg = "🟡", f"{n} ev",      "#FFFBEB", "#92400E"
            elif n < 20:
                dot, label, bg, fg = "🟠", f"{n} ev",      "#FFF7ED", "#C2410C"
            else:
                dot, label, bg, fg = "🔴", f"{n} ev",      "#FFF5F5", "#991B1B"
            # Barra attività proporzionale
            bar_w = min(100, int((n or 0) / 20 * 100)) if n else 0
            card_html = (
                f'<div style="padding:8px 10px;margin:3px 0;border-radius:8px;'
                f'background:{bg};border:1px solid {fg}33;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="font-weight:700;color:#1E293B;font-size:0.82rem;">🌋 {name}</span>'
                f'<span style="font-size:0.75rem;font-weight:700;color:{fg};">{dot}</span>'
                f'</div>'
                f'<div style="font-size:0.72rem;color:{fg};font-weight:600;margin-top:1px;">{label}</div>'
                f'<div style="margin-top:4px;height:3px;background:#E2E8F0;border-radius:2px;">'
                f'<div style="height:3px;width:{bar_w}%;background:{fg};border-radius:2px;opacity:0.7;"></div>'
                f'</div></div>'
            )
            if i % 2 == 0:
                vcol1.markdown(card_html, unsafe_allow_html=True)
            else:
                vcol2.markdown(card_html, unsafe_allow_html=True)

        st.caption("Fonte: INGV FDSN · M≥0.5 · 7gg · cache 10 min")

    st.markdown("---")

    # ── Feature grid ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:1.15rem;font-weight:700;color:#0F172A;margin-bottom:14px;">
        Cosa puoi fare con SismaVer2
    </div>""", unsafe_allow_html=True)

    features = [
        ("🌊", "Monitoraggio Sismico",   "Mappa INGV real-time · Grafici magnitudo e profondità · Filtro per regione · Analisi 7 giorni",            "#EFF6FF", "#1D4ED8"),
        ("🌋", "Vulcani",                "20+ vulcani italiani · Schede dettagliate · Stato allerta · Webcam e bollettini ufficiali",                 "#FFF7ED", "#C2410C"),
        ("⚠️", "Allerte e Rischi",       "Mappa MeteoAlarm per regione · Tab: Tsunami · Sismica · Vulcani · Meteo · Idrogeologico",                  "#FFF5F5", "#991B1B"),
        ("📈", "Statistiche Sismiche",   "Analisi storica · Distribuzione magnitudo · Tendenze · Mappe densità epicentri",                           "#F5F3FF", "#6D28D9"),
        ("🌦", "Meteo",                  "Previsioni 7 giorni · Radar precipitazioni · Allerte per qualsiasi comune italiano",                       "#F0F9FF", "#075985"),
        ("🌬️", "Qualità dell'Aria",      "Indice AQI europeo (EEA) · 20 città · Dati CAMS · Aggiornamento orario",                                  "#F0FDF4", "#166534"),
        ("💬", "Chat Pubblica",          "Comunicazione in tempo reale · Segnalazioni tra cittadini · Moderazione automatica",                       "#FAF5FF", "#6D28D9"),
        ("🚨", "Punti di Emergenza",     "Mappa punti raccolta · Strutture emergenza · Navigazione GPS integrata · Tutte le regioni",                 "#FFF5F5", "#991B1B"),
        ("🩺", "Primo Soccorso",         "Guide pratiche · RCP adulti e bambini · Manovre disostruzione · Numero 118",                               "#FFF0F0", "#9B1C1C"),
        ("📞", "Numeri Utili",           "Tutti i numeri di emergenza nazionali e regionali · 112 · 118 · 115 · 113 · 1515",                         "#F0FDF4", "#166534"),
    ]

    cols = st.columns(2)
    for i, (icon, titolo, desc, bg, color) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="sisma-card" style="background:{bg};border-color:{color}22;min-height:110px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">{icon}</div>
                <div style="font-weight:700;color:{color};font-size:0.92rem;margin-bottom:4px;">{titolo}</div>
                <div style="color:#475569;font-size:0.8rem;line-height:1.45;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Notizie INGV & Emergenza ──────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;
                margin-bottom:6px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.4rem;">📰</span>
            <span style="font-size:1.15rem;font-weight:700;color:#0F172A;">
                Aggiornamenti INGV &amp; Notizie di Emergenza
            </span>
        </div>
        <a href="https://www.protezionecivile.gov.it/it/notizie"
           target="_blank"
           style="font-size:0.78rem;color:#0EA5E9;text-decoration:none;
                  white-space:nowrap;padding:4px 10px;border:1px solid #0EA5E9;
                  border-radius:20px;">
            🛡️ Portale DPC →
        </a>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Caricamento notizie..."):
        news = _fetch_dpc_news()

    if news:
        for n in news:
            date_str = n['date'][:22] if n['date'] else ''
            src = n.get("source", "")
            is_ansa = "ansa" in src.lower()
            src_color = "#7C3AED" if is_ansa else "#166534"
            src_bg    = "#FAF5FF"  if is_ansa else "#F0FDF4"
            st.markdown(
                f"""<div class="sisma-card" style="
                    background:{src_bg};border-color:#0EA5E933;
                    padding:10px 14px;margin:4px 0;">
                    <a href='{n["link"]}' target='_blank'
                       style='color:{src_color};font-weight:600;
                              text-decoration:none;font-size:0.9rem;'>
                        {n["title"]}
                    </a>
                    <div style='display:flex;gap:12px;margin-top:4px;'>
                        <span style='color:#94A3B8;font-size:0.72rem;'>📅 {date_str}</span>
                        <span style='color:{src_color};font-size:0.72rem;
                                    opacity:0.7;'>📡 {src}</span>
                    </div></div>""",
                unsafe_allow_html=True)
        st.caption("Fonti: INGV Blog · ANSA (filtrato per emergenza) · Cache 10 min")
    else:
        st.warning(
            "Feed notizie temporaneamente non disponibili — "
            "[Portale DPC](https://www.protezionecivile.gov.it/it/notizie) · "
            "[INGV Blog](https://ingvterremoti.com)"
        )

    st.markdown("---")

    # ── Barra emergenza ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="emergency-bar">
        🚨 <b>EMERGENZA:</b> &nbsp;
        112 — Numero Unico &nbsp;|&nbsp;
        118 — Pronto Soccorso &nbsp;|&nbsp;
        115 — Vigili del Fuoco &nbsp;|&nbsp;
        113 — Polizia &nbsp;|&nbsp;
        1515 — Guardia Costiera
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;color:#94A3B8;font-size:0.78rem;margin-top:10px;">
        <b>SismaVer2 v3.4</b> — sviluppato da <b>Fabio Scelzo</b> ·
        <a href="mailto:meteotorre@gmail.com">meteotorre@gmail.com</a> ·
        Evoluzione di <a href="https://sismocampania.streamlit.app" target="_blank">SismoCampania</a>
    </div>""", unsafe_allow_html=True)
