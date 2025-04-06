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

# Misura le prestazioni di caricamento
start_time = time.time()

# Ottimizzazioni SEO complete
add_seo_metatags()
add_schema_markup()

# Aggiungi meta tag verifica Google Search Console
st.markdown("""
    <meta name="google-site-verification" content="INSERISCI_QUI_IL_CODICE_DI_VERIFICA" />
""", unsafe_allow_html=True)

# Aggiungi tag canonical e altri meta tag importanti
st.markdown("""
    <link rel="canonical" href="https://sos-italia.streamlit.app" />
    <meta name="robots" content="index, follow" />
    <meta name="language" content="it" />
    <meta name="revisit-after" content="7 days" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
""", unsafe_allow_html=True)

# Aggiungi canonical URL
st.markdown('<link rel="canonical" href="https://sos-italia.streamlit.app" />', unsafe_allow_html=True)

# Inizializza query_params
query_params = st.query_params

# Servi robots.txt e sitemap.xml
if 'seo_endpoint' in query_params:
    if query_params['seo_endpoint'] == 'robots':
        st.text(serve_robots_txt())
        st.stop()
    elif query_params['seo_endpoint'] == 'sitemap':
        st.text(serve_sitemap_xml())
        st.stop()

# Genera e servi sitemap.xml e robots.txt
if 'seo_endpoint' in query_params:
    if query_params.get('seo_endpoint') == 'sitemap':
        st.markdown(serve_sitemap_xml(), unsafe_allow_html=True)
    elif query_params.get('seo_endpoint') == 'robots':
        st.markdown(serve_robots_txt(), unsafe_allow_html=True)

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


# Integrazione metatag SEO e schema markup per i motori di ricerca
try:
    from modules.seo_utils import add_seo_metatags, add_schema_markup
    # Aggiungi metatag per SEO
    add_seo_metatags()
    # Aggiungi markup strutturato JSON-LD
    add_schema_markup()
except ImportError:
    pass

# Configura il tema personalizzato
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem !important;
        color: #1E3A8A;
    }
    .subtitle {
        font-size: 1.2rem;
        font-style: italic;
        color: #64748B;
    }
    .stApp a {
        color: #2563EB;
    }
    .stApp a:hover {
        color: #1E40AF;
        text-decoration: underline;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 1rem;
        border-radius: 5px;
    }
    .info-box {
        background-color: #E0F2FE;
        border-left: 5px solid #0EA5E9;
        padding: 1rem; 
        border-radius: 5px;
    }
    .success-box {
        background-color: #DCFCE7;
        border-left: 5px solid #10B981;
        padding: 1rem;
        border-radius: 5px;
    }
    .sidebar-header {
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        color: #1E3A8A;
    }
    .sidebar-subheader {
        font-weight: bold;
        font-size: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        color: #334155;
    }
    .footer {
        font-size: 0.8rem;
        color: #64748B;
        text-align: center;
        margin-top: 3rem;
        border-top: 1px solid #E2E8F0;
        padding-top: 1rem;
    }
    .footer p:last-child {
        margin-top: 0.5rem;
        color: #94A3B8;
        font-size: 0.75rem;
    }
    .visit-counter {
        background: #F1F5F9;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 500;
        color: #475569;
        display: inline-block;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar con menu di navigazione
with st.sidebar:
    # Logo SismaVer2
    st.markdown("## 🇮🇹 SismaVer2")
    st.markdown('<div class="sidebar-header">Sistema Nazionale di Monitoraggio</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.9rem; margin-bottom:15px; color:#475569;">
    Piattaforma integrata per il monitoraggio e la gestione delle emergenze sul territorio italiano.
    Dati in tempo reale da fonti ufficiali e strumenti di segnalazione per i cittadini.
    </div>
    """, unsafe_allow_html=True)

    pagine = {
        "🏠 Home": "home",
        "🌊 Monitoraggio Sismico": "monitoraggio",
        "🌋 Vulcani": "vulcani",
        "🌦 Meteo": "meteo",
        "💬 Chat Pubblica": "chat_enhanced",  # Usa la versione migliorata della chat
        "🚨 Punti di Emergenza": "emergenza",
        "🩺 Primo Soccorso": "primo_soccorso",
        "📱 Segnala Evento": "segnala_evento_enhanced",  # Usa la versione migliorata della segnalazione eventi
        "💰 Donazioni": "donazioni",
        "📋 Note di Rilascio": "note_rilascio",
        "ℹ️ Licenza e Info": "licenza"
    }

    st.markdown('<div class="sidebar-subheader">Navigazione</div>', unsafe_allow_html=True)

    # Spiegazione delle sezioni
    with st.expander("ℹ️ Guida alle sezioni"):
        st.markdown("""
        - **Home**: Panoramica generale e informazioni principali
        - **Monitoraggio Sismico**: Dati in tempo reale su eventi sismici in Italia
        - **Vulcani**: Monitoraggio attività vulcanica sul territorio italiano
        - **Meteo**: Previsioni meteo e condizioni attuali per ogni località
        - **Chat Pubblica**: Comunicazione in tempo reale tra utenti
        - **Punti di Emergenza**: Mappa dei punti di raccolta e strutture di emergenza
        - **Primo Soccorso**: Guide e procedure di primo intervento
        - **Segnala Evento**: Sistema per segnalare eventi o situazioni di rischio
        - **Donazioni**: Supporta il progetto e la sua evoluzione
        - **Note di Rilascio**: Cronologia degli aggiornamenti dell'applicazione
        - **Licenza e Info**: Informazioni sullo sviluppatore e termini d'uso
        """)

    selezione = st.radio("Menu di navigazione", list(pagine.keys()), label_visibility="collapsed")
    pagina_selezionata = pagine[selezione]

    # Banner allerta
    st.markdown("""---""")
    if random.random() > 0.9:  # Mostra allerta casualmente per simulazione (ridotto al 10%)
        st.warning("⚠️ Allerta in corso: forti temporali in Lombardia")
    else:
        st.success("✅ Nessuna allerta critica in corso")

    # Data e ora con fuso orario italiano
    ora_attuale = datetime.now(FUSO_ORARIO_ITALIA)
    st.markdown(f"Aggiornato: {ora_attuale.strftime('%d/%m/%Y %H:%M:%S')} (IT)")

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

# Incrementa contatore visite
from modules.security import increment_visit_counter
visit_count = increment_visit_counter()

# Footer
st.markdown(f"""
<div class="footer">
<p>🇮🇹 SismaVer2 - Sistema Nazionale di Monitoraggio e Prevenzione</p>
<p>© 2025 – Versione 2.3.2 (Aprile 2025) – Dati da fonti ufficiali</p>
<p><a href="https://github.com/sismaver-project/sismaver2" target="_blank">GitHub</a> · 
<a href="mailto:meteotorre@gmail.com">Contatti</a> · 
<a href="https://www.protezionecivile.gov.it/it/privacy" target="_blank">Privacy</a></p>
<p>👥 Visite totali: {visit_count:,}</p>
<p>🔄 Ultimo aggiornamento: {ora_attuale.strftime('%d/%m/%Y %H:%M:%S')} (IT)</p>
</div>
""", unsafe_allow_html=True)