import warnings
warnings.filterwarnings("ignore", message=".*components.v1.*")

import streamlit as st
import os
import sys
import importlib
import time
import re
import uuid
from modules.seo_utils import add_seo_metatags, add_schema_markup
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
from datetime import datetime, timezone, timedelta
import random
from dotenv import load_dotenv

# Configurazione della pagina deve essere la prima istruzione Streamlit
st.set_page_config(
    page_title="SismaVer2 - Monitoraggio e Prevenzione Rischi",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── ANTI-IBERNAZIONE (prima di tutto il resto) ───────────────────────────────
try:
    from modules.keep_alive import activate as _keepalive_activate
    _keepalive_activate()
except Exception:
    pass  # Non blocca mai l'app se il modulo ha problemi

# Misura le prestazioni di caricamento
start_time = time.time()

# Ottimizzazioni SEO (una sola volta)

# Meta tag SEO e canonical
st.markdown("""
    <link rel="canonical" href="https://sos-italia.streamlit.app" />
    <meta name="robots" content="index, follow" />
    <meta name="language" content="it" />
    <meta name="description" content="SismaVer2 — Piattaforma nazionale di monitoraggio rischi naturali: terremoti, vulcani, meteo, qualità aria, allerte e emergenza in tempo reale." />
    <meta name="keywords" content="terremoti italia, monitoraggio sismico, vulcani, allerta meteo, protezione civile, emergenza" />
    <meta name="revisit-after" content="3 days" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta property="og:title" content="SismaVer2 — Monitoraggio Nazionale Rischi Naturali" />
    <meta property="og:description" content="Terremoti, vulcani, meteo, allerte e qualità aria in tempo reale per tutta Italia." />
    <meta property="og:url" content="https://sos-italia.streamlit.app" />
    <meta property="og:type" content="website" />
""", unsafe_allow_html=True)

# Inizializza query_params
query_params = st.query_params

# Servi robots.txt e sitemap.xml
if 'seo_endpoint' in query_params:
    if query_params.get('seo_endpoint') == 'robots':
        st.text(serve_robots_txt())
        st.stop()
    elif query_params.get('seo_endpoint') == 'sitemap':
        st.text(serve_sitemap_xml())
        st.stop()

# Importa moduli di sicurezza
try:
    from modules.security import sanitize_input, apply_security_headers, log_security_event
    from modules.csrf_protection import cleanup_expired_tokens
    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    def sanitize_input(text): return text
    def apply_security_headers(): pass
    def log_security_event(message, severity="INFO"): print(f"[{severity}] {message}")
    def cleanup_expired_tokens(): pass

# Configura il fuso orario italiano (UTC+1 o UTC+2 con ora legale)
# L'Italia è a UTC+1 standard e UTC+2 durante l'ora legale
# Calcolo automatico dell'ora legale in Italia (attiva da fine marzo a fine ottobre)
now = datetime.now()
y = now.year
# Calcolo automatico del periodo di ora legale in Italia
inizio_ora_legale = datetime(y, 3, 31 - (datetime(y, 3, 31).weekday() + 1) % 7)
fine_ora_legale = datetime(y, 10, 31 - (datetime(y, 10, 31).weekday() + 1) % 7)
ora_legale = inizio_ora_legale <= now.replace(tzinfo=None) < fine_ora_legale  # Calcolo automatico

# Esportiamo la costante per tutti i moduli
FUSO_ORARIO_ITALIA = timezone(timedelta(hours=2 if ora_legale else 1))

# Cache di precaricamento dei moduli (più veloce)
moduli_cache = {}

# Carica le variabili d'ambiente dal file .env
load_dotenv(verbose=False, override=True)  # Ottimizzato

# Inizializzazione del session state per tracciamento e sicurezza
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Livello moderazione attivo
if "moderazione_attiva" not in st.session_state:
    st.session_state.moderazione_attiva = "standard"

# Auto-refresh per chat
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# Timestamp ultimo refresh
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Log accesso sicuro se abilitato
if SECURITY_ENABLED:
    log_security_event(f"Accesso applicazione da utente {st.session_state.user_id}", "INFO")
    # Pulizia token CSRF scaduti
    cleanup_expired_tokens()


try:
    from modules.seo_utils import add_seo_metatags, add_schema_markup
    add_seo_metatags()
    add_schema_markup()
except ImportError:
    pass

# ─── CSS GLOBALE RESTYLING v3.0 ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Import Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Base app ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Rimuovi padding eccessivo dal container principale ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

/* ── Sidebar moderna ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 50%, #0F172A 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #CBD5E1 !important;
    transition: all 0.2s ease;
    padding: 2px 0;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #60A5FA !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #94A3B8 !important;
}
[data-testid="stSidebar"] .stExpander {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stSuccess {
    background: rgba(16,185,129,0.15) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stSuccess p {
    color: #6EE7B7 !important;
}

/* ── Cards con ombra e bordo ── */
.sisma-card {
    background: white;
    border-radius: 12px;
    padding: 16px 18px;
    margin: 6px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
    border: 1px solid #E2E8F0;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.sisma-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    transform: translateY(-1px);
}

/* ── Card terremoto con indicatore laterale ── */
.quake-card {
    border-radius: 10px;
    padding: 10px 14px;
    margin: 5px 0;
    background: white;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: all 0.2s ease;
}
.quake-card:hover {
    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    transform: translateX(2px);
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 14px 16px !important;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
[data-testid="stMetricValue"] {
    color: #1E40AF !important;
    font-weight: 700 !important;
}

/* ── Tabs moderni ── */
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    border: none !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}

/* ── Info/Warning/Success box ── */
.warning-box {
    background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
    border-left: 5px solid #F59E0B;
    padding: 1rem 1.2rem;
    border-radius: 0 10px 10px 0;
    box-shadow: 0 2px 8px rgba(245,158,11,0.15);
}
.info-box {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    border-left: 5px solid #3B82F6;
    padding: 1rem 1.2rem;
    border-radius: 0 10px 10px 0;
    box-shadow: 0 2px 8px rgba(59,130,246,0.12);
}
.success-box {
    background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    border-left: 5px solid #10B981;
    padding: 1rem 1.2rem;
    border-radius: 0 10px 10px 0;
    box-shadow: 0 2px 8px rgba(16,185,129,0.12);
}

/* ── Stat pill badge ── */
.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #EFF6FF;
    color: #1D4ED8;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    border: 1px solid #BFDBFE;
}

/* ── Separatori ── */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 1.5rem 0 !important;
}

/* ── Footer ── */
.footer {
    font-size: 0.82rem;
    color: #64748B;
    text-align: center;
    margin-top: 3rem;
    background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.2rem 1rem;
}
.footer a {
    color: #2563EB !important;
    text-decoration: none;
    font-weight: 500;
}
.footer a:hover {
    text-decoration: underline;
}
.footer-badge {
    display: inline-block;
    background: #DBEAFE;
    color: #1E40AF;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0 4px;
}

/* ── Emergency banner ── */
.emergency-bar {
    background: linear-gradient(90deg, #DC2626 0%, #B91C1C 100%);
    color: white;
    text-align: center;
    padding: 8px 16px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px rgba(220,38,38,0.3);
    margin: 12px 0;
}

/* ── Sidebar title ── */
.sidebar-logo {
    font-size: 1.6rem;
    font-weight: 800;
    color: white !important;
    letter-spacing: -0.5px;
    margin: 0;
    padding: 0;
}
.sidebar-tagline {
    font-size: 0.78rem;
    color: #94A3B8 !important;
    margin-top: 2px;
    font-style: italic;
}
.sidebar-section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #64748B !important;
    margin: 14px 0 4px 0;
    padding-left: 2px;
}

/* ── Scrollbar personalizzata ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── Animazioni fade-in ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.stMarkdown, .stDataFrame, [data-testid="stMetric"] {
    animation: fadeInUp 0.35s ease both;
}

/* ── Link globali ── */
a { color: #2563EB !important; }
a:hover { color: #1E40AF !important; text-decoration: underline; }

/* ── Plotly charts ── */
.js-plotly-plot .plotly { border-radius: 12px; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #2563EB !important; }

/* ── Sidebar radio: voce selezionata chiaramente visibile ── */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    padding: 5px 8px;
    border-radius: 6px;
    cursor: pointer;
    border-left: 2px solid transparent;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.09) !important;
    color: #93C5FD !important;
}
/* voce attiva radio */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input[type="radio"]:checked) {
    background: rgba(96,165,250,0.18) !important;
    border-left: 2px solid #60A5FA !important;
    color: #93C5FD !important;
    font-weight: 600;
}

/* ── SIDEBAR: Input text / number — sfondo dark, testo leggibile ── */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: rgba(255,255,255,0.09) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: rgba(148,163,184,0.7) !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 1px #60A5FA !important;
    outline: none !important;
}

/* ── SIDEBAR: Selectbox — sfondo dark, valore selezionato visibile ── */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] {
    background: rgba(255,255,255,0.09) !important;
    border-color: rgba(255,255,255,0.22) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="value"],
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="placeholder"],
[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #94A3B8 !important;
}

/* ── Dropdown selectbox — light theme affidabile (vince sulla regola sidebar *) ── */
/* Il popover eredita color:#E2E8F0 dalla regola sidebar * → testo bianco su sfondo bianco.
   Soluzione: forzare sfondo BIANCO e testo SCURO con specificità superiore. */
body div[data-baseweb="popover"],
body div[data-baseweb="popover"] > div,
body div[data-baseweb="popover"] > div > div,
body div[data-baseweb="popover"] [data-baseweb="menu"],
body div[data-baseweb="popover"] [role="listbox"],
body div[data-baseweb="popover"] ul {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18) !important;
}
body div[data-baseweb="popover"] li,
body div[data-baseweb="popover"] [role="option"],
body div[data-baseweb="popover"] [data-baseweb="menu-item"],
body div[data-baseweb="popover"] span,
body div[data-baseweb="popover"] div,
body div[data-baseweb="popover"] p {
    color: #1E293B !important;
    background-color: transparent !important;
}
body div[data-baseweb="popover"] li:hover,
body div[data-baseweb="popover"] [role="option"]:hover {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
}
body div[data-baseweb="popover"] [aria-selected="true"],
body div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #DBEAFE !important;
    color: #1D4ED8 !important;
    font-weight: 600 !important;
}

/* ── SIDEBAR: Number input stepper buttons ── */
[data-testid="stSidebar"] [data-testid="stNumberInput"] button {
    background: rgba(255,255,255,0.1) !important;
    color: #E2E8F0 !important;
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button:hover {
    background: rgba(96,165,250,0.2) !important;
}

/* ── SIDEBAR: Slider label e valore ── */
[data-testid="stSidebar"] [data-testid="stSlider"] label,
[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSidebar"] [data-testid="stTickBarMax"] {
    color: #CBD5E1 !important;
}

/* ── SIDEBAR: subheader e labels dei widget ── */
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    color: #E2E8F0 !important;
}

/* ── Fix sezione label troppo scura ── */
.sidebar-section-label {
    color: #94A3B8 !important;
}

/* ── SIDEBAR: selectbox label (testo sopra il widget) ── */
[data-testid="stSidebar"] label {
    color: #CBD5E1 !important;
    font-size: 0.84rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar moderna v3.0 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 14px 4px 10px 4px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px;">
        <div class="sidebar-logo">🇮🇹 SismaVer2</div>
        <div class="sidebar-tagline">Sistema Nazionale di Monitoraggio Rischi</div>
    </div>
    """, unsafe_allow_html=True)

    pagine = {
        "🏠 Home": "home",
        "🗺️ Mappa Rischi": "mappa_rischi",
        "🌊 Monitoraggio Sismico": "monitoraggio",
        "🌋 Vulcani": "vulcani",
        "📊 Allerte e Rischi": "rischi_allerte",
        "📈 Statistiche Sismiche": "statistiche",
        "🌦 Meteo": "meteo",
        "🌬️ Qualità dell'Aria": "qualita_aria",
        "📞 Numeri Utili": "numeri_utili",
        "💬 Chat Pubblica": "chat_enhanced",
        "🚨 Punti di Emergenza": "emergenza",
        "🩺 Primo Soccorso": "primo_soccorso",
        "📱 Segnala Evento": "segnala_evento_enhanced",
        "💰 Donazioni": "donazioni",
        "📚 Fonti dei Dati": "fonti",
        "📋 Note di Rilascio": "note_rilascio",
        "ℹ️ Licenza e Info": "licenza"
    }

    st.markdown('<div class="sidebar-section-label">Navigazione</div>', unsafe_allow_html=True)

    selezione = st.radio("Menu di navigazione", list(pagine.keys()), label_visibility="collapsed")
    pagina_selezionata = pagine[selezione]

    st.markdown('<div style="border-top: 1px solid rgba(255,255,255,0.08); margin: 12px 0 10px 0;"></div>', unsafe_allow_html=True)

    # ── Banner supporto / monetizzazione ────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(0,48,135,0.25),rgba(0,48,135,0.10));
                border:1px solid rgba(0,48,135,0.35); border-radius:10px;
                padding:10px 12px; margin-bottom:10px; text-align:center;">
        <div style="color:#93C5FD; font-size:0.78rem; font-weight:700; letter-spacing:0.5px;
                    text-transform:uppercase; margin-bottom:8px;">❤️ Supporta il progetto</div>
        <a href="https://www.paypal.com/donate/?business=meteotorre%40gmail.com" target="_blank"
           style="background:#003087; color:white; padding:7px 18px; border-radius:16px;
                  font-weight:700; text-decoration:none; font-size:0.84rem;
                  display:inline-block;">💙 Dona con PayPal</a>
    </div>
    """, unsafe_allow_html=True)

    ora_attuale = datetime.now(FUSO_ORARIO_ITALIA)
    st.markdown(f"""
    <div style="background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.25);
         border-radius: 8px; padding: 8px 10px; margin-bottom: 8px;">
        <span style="color: #6EE7B7; font-size: 0.82rem; font-weight: 600;">
            ✅ Nessuna allerta critica
        </span>
    </div>
    <div style="color: #94A3B8; font-size: 0.72rem; text-align: center; padding: 2px 0;">
        🕒 {ora_attuale.strftime('%d/%m/%Y %H:%M')} (IT)
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label" style="margin-top:14px;">Informazioni</div>', unsafe_allow_html=True)
    with st.expander("ℹ️ Guida alle sezioni"):
        st.markdown("""
        - **Home**: Panoramica live — KPI reali, terremoti, vulcani, EMSC
        - **🗺️ Mappa Rischi**: Mappa interattiva allerte per regione · MeteoAlarm · EMSC · Vulcani
        - **📊 Allerte e Rischi**: Tab dettagliati · Tsunami · Sismica · Vulcani · Meteo · Idrogeologico
        - **Monitoraggio Sismico**: Dati INGV real-time, mappa, grafici
        - **Vulcani**: 20+ vulcani con schede e webcam
        - **Statistiche Sismiche**: Tendenze e analisi storiche *(NUOVO)*
        - **Meteo**: Previsioni 7 giorni per ogni comune
        - **Qualità Aria**: AQI europeo per 20 città
        - **Numeri Utili**: Tutti i numeri di emergenza
        - **Chat Pubblica**: Comunicazione tra cittadini
        - **Punti Emergenza**: Mappa raccolta per regione
        - **Primo Soccorso**: Guide pratiche di intervento
        - **Segnala Evento**: Segnala terremoti e frane
        """)

# Cache di caricamento moduli e misura performance
def load_module(module_name):
    """Carica un modulo con cache ottimizzata, misurando le performance."""
    # Sanitizzazione del nome del modulo per prevenire path traversal
    if not re.match(r'^[a-zA-Z0-9_]+$', module_name):
        if SECURITY_ENABLED:
            log_security_event(f"Tentativo di path traversal: {module_name}", "CRITICAL")
        raise ValueError(f"Nome modulo non valido: {module_name}")

    module_path = f"modules.{module_name}"

    # Verifica se il modulo è già in cache
    if module_path in moduli_cache:
        return moduli_cache[module_path]

    # Misurazione del tempo di caricamento
    module_load_start = time.time()

    try:
        # Se il modulo è già importato, ricarichiamolo
        if module_path in sys.modules:
            module = importlib.reload(sys.modules[module_path])
        else:
            module = importlib.import_module(module_path)

        # Salva nella cache
        moduli_cache[module_path] = module

        # Log del tempo di caricamento (solo in sviluppo)
        load_time = time.time() - module_load_start
        if load_time > 0.1:  # Log solo per moduli lenti (>100ms)
            print(f"⚡ Caricato modulo {module_name} in {load_time:.3f}s")

        return module
    except Exception as e:
        error_msg = f"⚠️ Errore caricamento modulo {module_name}: {str(e)}"
        print(error_msg)
        if SECURITY_ENABLED:
            log_security_event(error_msg, "ERROR")
        raise

# Inizializza query_params
query_params = st.query_params

# Sanitizza e gestisce i parametri URL
try:
    # Sanitizza tutti i parametri URL per prevenire attacchi XSS
    if query_params:
        for key, value in dict(query_params).items():
            if SECURITY_ENABLED:
                # Se è un parametro pericoloso, lo sanitizziamo o rimuoviamo
                safe_value = sanitize_input(value)
                if safe_value != value:
                    log_security_event(f"Parametro URL sanitizzato: {key}={value}", "WARNING")
                    query_params[key] = safe_value
except Exception as e:
    if SECURITY_ENABLED:
        log_security_event(f"Errore nella gestione dei parametri URL: {str(e)}", "ERROR")

# Applica security headers se disponibili
if SECURITY_ENABLED:
    try:
        apply_security_headers()
    except Exception as e:
        log_security_event(f"Errore nell'applicazione dei security headers: {str(e)}", "ERROR")

# Carica il modulo selezionato
try:
    # Importa il modulo selezionato con precaricamento per migliori performance
    with st.spinner(f"Caricamento {pagina_selezionata}..."):
        if pagina_selezionata in moduli_cache:
            # Ottimizzazione: usa modulo già in cache
            modulo = moduli_cache[pagina_selezionata]
        else:
            # Carica con sistema ottimizzato (con controlli di sicurezza)
            modulo = load_module(pagina_selezionata)

    # Mostra il modulo
    modulo.show()

    # Misura e log tempo totale di caricamento (solo per debug)
    total_load_time = time.time() - start_time
    print(f"⏱️ Tempo totale caricamento: {total_load_time:.3f}s")

except Exception as e:
    error_message = f"Errore nel caricamento del modulo {pagina_selezionata}: {e}"
    st.error(error_message)

    if SECURITY_ENABLED:
        log_security_event(error_message, "ERROR")

    # Mostra un messaggio di errore specifico con suggerimenti
    # Sanitizza il messaggio di errore per evitare XSS
    safe_error = sanitize_input(str(e)) if SECURITY_ENABLED else str(e)

    st.markdown(f"""
    <div class="warning-box">
    <h3>Impossibile caricare il modulo: {sanitize_input(pagina_selezionata) if SECURITY_ENABLED else pagina_selezionata}</h3>
    <p>Si è verificato un errore durante il caricamento di questa sezione.</p>
    <p><strong>Dettagli tecnici:</strong> {safe_error}</p>
    <p>Prova a:</p>
    <ul>
        <li>Aggiornare la pagina</li>
        <li>Selezionare un'altra sezione dal menu</li>
        <li>Verificare la connessione internet</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # Fallback alla home
    if pagina_selezionata != "home":
        st.markdown("### Ritorno alla Home")
        try:
            # Caricamento sicuro della home
            if "home" in sys.modules:
                module = importlib.reload(sys.modules["modules.home"])
            else:
                module = importlib.import_module("modules.home")

            if hasattr(module, 'show'):
                module.show()
            else:
                st.info("Modulo home non ha la funzione show(). Ricarica la pagina.")
        except Exception as home_error:
            if SECURITY_ENABLED:
                log_security_event(f"Errore nel caricamento del fallback home: {str(home_error)}", "ERROR") 
            st.info("Impossibile caricare la home. Ricarica la pagina.")

# Messaggio sul tempo di caricamento (solo per debug)
# print(f"⏱️ Tempo totale caricamento: {time.time() - start_time:.3f}s")

# Contatore visite: incrementa solo una volta per sessione browser (non ad ogni rerun)
from modules.security import increment_visit_counter, read_visit_counter
if "visit_counted" not in st.session_state:
    st.session_state.visit_counted = True
    visit_count = increment_visit_counter()
else:
    visit_count = read_visit_counter()

# Footer moderno v3.0
st.markdown(f"""
<div class="footer">
    <div style="margin-bottom: 8px;">
        <span style="font-size: 1.1rem; font-weight: 700; color: #1E293B;">🇮🇹 SismaVer2</span>
        &nbsp;
        <span class="footer-badge">v3.0</span>
        <span class="footer-badge" style="background:#DCFCE7; color:#166534;">LIVE</span>
    </div>
    <p style="color: #475569; margin: 4px 0;">Sistema Nazionale di Monitoraggio e Prevenzione Rischi Naturali</p>
    <p style="margin: 6px 0;">
        <a href="https://github.com/ScelzoF/SismaVer2" target="_blank">GitHub</a> &nbsp;·&nbsp;
        <a href="mailto:meteotorre@gmail.com">Contatti</a> &nbsp;·&nbsp;
        <a href="https://www.protezionecivile.gov.it/it/privacy" target="_blank">Privacy</a>
    </p>
    <p style="color: #94A3B8; font-size: 0.75rem; margin: 6px 0;">
        👥 Visite totali: <strong style="color:#475569;">{visit_count:,}</strong>
        &nbsp;·&nbsp;
        🕒 {ora_attuale.strftime('%d/%m/%Y %H:%M')} (IT)
        &nbsp;·&nbsp;
        © {ora_attuale.year} Fabio Scelzo
    </p>
    <p style="color: #CBD5E1; font-size: 0.72rem; margin: 4px 0;">
        Dati: INGV · Protezione Civile · EMSC · MeteoAlarm · Open-Meteo · Copernicus CAMS
    </p>
</div>
""", unsafe_allow_html=True)
