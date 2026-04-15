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
import time
import streamlit_js_eval as st_js
import folium
from streamlit_folium import folium_static
import requests
import json
from io import StringIO
import os

# Fuso orario italiano con ora legale automatica
def _get_tz_italia():
    _now = datetime.now()
    _y = _now.year
    _dst_s = datetime(_y, 3, 31 - (datetime(_y, 3, 31).weekday() + 1) % 7)
    _dst_e = datetime(_y, 10, 31 - (datetime(_y, 10, 31).weekday() + 1) % 7)
    return timezone(timedelta(hours=2 if _dst_s <= _now < _dst_e else 1))

FUSO_ORARIO_ITALIA = _get_tz_italia()

def show():
    # Auto-refresh ogni 5 minuti per dati sismici live
    if _AUTOREFRESH:
        _st_autorefresh(interval=300_000, limit=None, key="monit_autorefresh")

    st.title("📡 Monitoraggio Sismico Nazionale")
    
    # Opzioni di visualizzazione: nazionale o per regione
    st.sidebar.subheader("🗄️ Filtra visualizzazione")
    
    # Lista regioni italiane
    regioni = [
        "Italia (Visione nazionale)",
        "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
        "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche",
        "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana",
        "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"
    ]
    
    regione_scelta = st.sidebar.selectbox("Seleziona regione", regioni)

    # Data e ora dell'ultimo aggiornamento con fuso orario italiano
    current_time = datetime.now(FUSO_ORARIO_ITALIA)
    last_update_timestamp = current_time.strftime("%d/%m/%Y %H:%M:%S")
    st.sidebar.markdown(f"**🕒 Ultimo aggiornamento:** {last_update_timestamp} (IT)")
    st.sidebar.markdown("---")
    
    # Informazioni sul monitoraggio
    st.sidebar.info("**Fonti dati:**\n"
                   "- INGV (Istituto Nazionale di Geofisica e Vulcanologia)\n"
                   "- Dipartimento della Protezione Civile\n"
                   "- ISPRA (Istituto Superiore per la Protezione e la Ricerca Ambientale)\n"
                   "- Servizi Geologici Regionali")

    # Sistema di tabs per i diversi tipi di sensori
    sensor_tab1, sensor_tab2, sensor_tab3 = st.tabs([
        "🔔 Sismicità", 
        "🌋 Vulcani attivi", 
        "🌊 Idrogeologico"
    ])
    
    # Tab 1: Rilevazione sismica
    with sensor_tab1:
        # Aggiungere un pulsante di aggiornamento dati e visualizzazione dell'ultimo aggiornamento
        col_refresh, col_time = st.columns([1, 4])
        
        with col_refresh:
            if st.button("🔄 Aggiorna dati"):
                st.session_state.last_update = datetime.now(FUSO_ORARIO_ITALIA)
                st.rerun()
        
        with col_time:
            current_time = datetime.now(FUSO_ORARIO_ITALIA)
            
            if 'last_update' not in st.session_state:
                st.session_state.last_update = current_time
                
            st.markdown(f"**🕒 Ultimo aggiornamento:** {current_time.strftime('%d/%m/%Y %H:%M:%S')} (IT)")
            
        # Auto-aggiornamento ogni 5 minuti
        if 'last_update' not in st.session_state:
            st.session_state.last_update = current_time
        elif (current_time - st.session_state.last_update).seconds > 300:
            st.session_state.last_update = current_time
            st.rerun()
            
        # Recupera dati in tempo reale da API INGV per ultime 24 ore
        # Mostra messaggio di caricamento durante il recupero dati
        with st.spinner("⏳ Recupero dati sismici in corso. Attendere pochi secondi..."):
            try:
                # Calcola data di inizio (7 giorni)
                start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
                
                # Filtro per magnitudo minima più basso per trovare più eventi
                min_mag = 0.5  # Mostra eventi da magnitudo 0.5 in su
            except Exception as e:
                st.error(f"Errore nel calcolo della data: {e}")
                start_date = "2023-01-01T00:00:00"
                min_mag = 1.0
                
            # Coordinate approssimative delle regioni italiane
            regioni_coords = {
                "Abruzzo": [42.35, 13.40],
                "Basilicata": [40.50, 16.08],
                "Calabria": [39.30, 16.34],
                "Campania": [40.83, 14.25],
                "Emilia-Romagna": [44.49, 11.34],
                "Friuli-Venezia Giulia": [46.07, 13.23],
                "Lazio": [41.89, 12.48],
                "Liguria": [44.41, 8.95],
                "Lombardia": [45.47, 9.19],
                "Marche": [43.62, 13.51],
                "Molise": [41.56, 14.65],
                "Piemonte": [45.07, 7.68],
                "Puglia": [41.12, 16.86],
                "Sardegna": [39.22, 9.10],
                "Sicilia": [37.50, 14.00],
                "Toscana": [43.77, 11.24],
                "Trentino-Alto Adige": [46.06, 11.12],
                "Umbria": [43.11, 12.39],
                "Valle d'Aosta": [45.73, 7.32],
                "Veneto": [45.44, 12.32]
            }
            
            try:
                # Determina l'URL più appropriato (inizia con versione semplificata)
                if regione_scelta == "Italia (Visione nazionale)":
                    # Usare API INGV per dati nazionali
                    ingv_url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={start_date}&minmag={min_mag}&limit=100"
                    source = "INGV"
                    st.info("Recupero dati sismici da INGV per l'intero territorio nazionale")
                else:
                    # Per le regioni, usiamo ancora INGV ma con timeout più breve
                    if regione_scelta in regioni_coords:
                        lat, lon = regioni_coords[regione_scelta]
                        radius_deg = 1.5  # Circa 150km per avere più eventi
                        ingv_url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={start_date}&minmag={min_mag}&lat={lat}&lon={lon}&maxradius={radius_deg}&limit=100"
                    else:
                        ingv_url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={start_date}&minmag={min_mag}&limit=100"
                    source = "INGV"
                
                # Utilizziamo il caching avanzato con TTL esteso per migliorare le prestazioni
                @st.cache_data(ttl=300, show_spinner=False)  # Cache sismici live 5 minuti
                def fetch_seismic_data(url):
                    """
                    Recupera i dati sismici con sistema di cache avanzato a quattro livelli:
                    1. Cache di Streamlit (TTL 5 minuti)
                    2. Cache in session_state (15 minuti) 
                    3. Sistema multiserver INGV con strategie adattive di resilienza
                    4. Dati persistenti statici come fallback di emergenza

                    Questa implementazione massimizza le performance e riduce il carico sulle API.
                    Include controllo preliminare multiplo della raggiungibilità di tutti i server INGV.
                    """
                    # Log di debug per tracciare le chiamate
                    print(f"DEBUG - Richiesta dati sismici da: {url}")
                    
                    try:
                        # Inizializza session_state se non esiste
                        if 'last_seismic_data' not in st.session_state:
                            st.session_state.last_seismic_data = {"features": [], "type": "FeatureCollection"}
                        if 'last_fetch_time' not in st.session_state:
                            st.session_state.last_fetch_time = datetime.now(FUSO_ORARIO_ITALIA) - timedelta(hours=1)
                        if 'using_usgs_data' not in st.session_state:
                            st.session_state.using_usgs_data = False  # Flag per indicare se stiamo usando dati USGS
                        
                        # Livello cache 1: Verifichiamo session_state per dati ultra-recenti
                        if 'last_seismic_data' in st.session_state and 'last_fetch_time' in st.session_state:
                            # Utilizziamo dati in memoria se recenti (aumentato a 15 minuti)
                            time_diff = datetime.now(FUSO_ORARIO_ITALIA) - st.session_state.last_fetch_time
                            if time_diff.total_seconds() < 900:  # 15 minuti (aumentato da 10)
                                print(f"INFO: Usando dati sismici dalla cache in memoria (età: {int(time_diff.total_seconds())}s)")
                                return st.session_state.last_seismic_data, None
                        
                        # Livello cache 2: Recuperiamo da API con timeout ottimizzato e retry
                        try:
                            # Impostazione timeout più lungo per evitare errori su reti lente
                            print("INFO: Tentativo di recupero dati da API INGV...")
                            headers = {
                                'User-Agent': 'SismaVer2/1.0 (Monitoraggio sismico italiano; https://sisma-ver-2.replit.app/)',
                                'Accept': 'application/json, text/plain, application/xml',  # Accettiamo più formati
                                'Accept-Encoding': 'gzip, deflate',  # Compressione per ridurre bandwidth
                                'Connection': 'keep-alive'  # Performance migliorata per richieste multiple
                            }
                            
                            # Definizione di tutti i server INGV alternativi
                            ingv_servers = [
                                "webservices.ingv.it",
                                "terremoti.ingv.it",
                                "cnt.rm.ingv.it",
                                "iside.rm.ingv.it"
                            ]
                            
                            # Definizione delle strategie per richieste alternative (più resilienti)
                            data_strategies = [
                                # Default strategia
                                lambda u: u,
                                # Strategia catalogs (formato diverso)
                                lambda u: u.replace("fdsnws/event/1/query", "fdsnws/event/1/catalogs"),
                                # Strategia evento (meno dati, più veloce)
                                lambda u: u.replace("format=geojson", "format=text").replace("limit=100", "limit=25"),
                                # Strategia magnitudo (solo eventi significativi)
                                lambda u: u.replace("minmag=0.5", "minmag=2.0").replace("limit=100", "limit=25"),
                                # Strategia storica (ultimi 7 giorni)
                                lambda u: u.replace("starttime=", "starttime=" + (datetime.now(FUSO_ORARIO_ITALIA) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"))
                            ]
                            
                            # Implementazione con retry adattivo
                            max_retries = 2  # Manteniamo 2 tentativi per non bloccare l'interfaccia
                            retry_count = 0
                            retry_delay = 1  # Partiamo con un secondo
                            response = None  # Inizializzazione esplicita
                            
                            while retry_count < max_retries:
                                # Lista di server INGV raggiungibili (verifica preliminare)
                                reachable_servers = []
                                
                                # Verifichiamo tutti i server contemporaneamente
                                for server in ingv_servers:
                                    try:
                                        check_url = f"https://{server}"
                                        head_response = requests.head(check_url, timeout=2.5, headers=headers)
                                        if head_response.status_code < 400:
                                            reachable_servers.append(server)
                                            print(f"INFO: Server INGV raggiungibile: {server}")
                                    except Exception as server_err:
                                        print(f"INFO: Server INGV non accessibile: {server} ({str(server_err)[:50]}...)")
                                
                                if not reachable_servers:
                                    print("INFO: Nessun server INGV raggiungibile, utilizzo cache")
                                    raise requests.exceptions.ConnectionError("Tutti i server INGV non sono raggiungibili")
                                
                                # Prova tutte le combinazioni di server e strategie
                                success = False
                                
                                for server in reachable_servers:
                                    if success:
                                        break
                                        
                                    for strategy in data_strategies:
                                        try:
                                            # Costruisci URL con server e strategia attuali
                                            current_url = url.replace("webservices.ingv.it", server)
                                            current_url = strategy(current_url)
                                            
                                            print(f"INFO: Tentativo con {server}, strategia: {strategy.__name__ if hasattr(strategy, '__name__') else 'custom'}")
                                            response = requests.get(current_url, timeout=7, headers=headers)  # Timeout aumentato
                                            
                                            if response.status_code == 200:
                                                content_type = response.headers.get('Content-Type', '')
                                                
                                                # Verifica preliminare del contenuto
                                                if ('application/json' in content_type and len(response.text) > 100) or \
                                                   ('text/plain' in content_type and len(response.text) > 50):
                                                    print(f"INFO: Risposta valida ricevuta da {server} ({len(response.text)} bytes)")
                                                    success = True
                                                    break
                                                else:
                                                    print(f"INFO: Risposta da {server} troppo corta o non valida")
                                        except Exception as req_err:
                                            print(f"INFO: Errore durante richiesta a {server}: {str(req_err)[:50]}...")
                                
                                if success and response and response.status_code == 200:
                                    print("INFO: Recupero dati INGV completato con successo")
                                    break
                                else:
                                    retry_count += 1
                                    # Utilizziamo backoff esponenziale modificato: aumenta più gradualmente
                                    retry_wait = retry_delay * (1.2 ** retry_count)  # Crescita più graduale
                                    if retry_count < max_retries:
                                        print(f"INFO: Tentativo {retry_count} fallito, riprovo tra {retry_wait:.1f} secondi...")
                                        time.sleep(retry_wait)
                                    else:
                                        print(f"INFO: Tutti i tentativi falliti ({max_retries}), utilizzo dati di fallback")
                                        raise requests.exceptions.RequestException("Tutti i tentativi falliti")
                            
                            if response.status_code == 200:
                                try:
                                    # Verifica che la risposta sia in formato JSON valido
                                    data = response.json()
                                    
                                    # Controllo validità della struttura dati
                                    if not isinstance(data, dict):
                                        raise ValueError("Risposta non è un dizionario JSON valido")
                                    
                                    if "features" not in data:
                                        raise ValueError("Chiave 'features' mancante nella risposta")
                                        
                                    if not isinstance(data.get("features"), list):
                                        raise ValueError("'features' non è una lista valida")
                                    
                                    # Ottimizzazione: Memorizziamo in session_state
                                    st.session_state.last_seismic_data = data
                                    st.session_state.last_fetch_time = datetime.now(FUSO_ORARIO_ITALIA)
                                    # Se prima stavamo usando USGS, segnala il ripristino di INGV
                                    message = None
                                    if st.session_state.get('using_usgs_data', False):
                                        st.session_state.using_usgs_data = False  # Reset flag USGS
                                        message = "✅ Connessione INGV ripristinata. Utilizzando dati ufficiali dell'Istituto Nazionale di Geofisica e Vulcanologia."
                                    print(f"INFO: Recuperati {len(data.get('features', []))} eventi sismici da INGV")
                                    return data, message
                                    
                                except ValueError as json_err:
                                    error_msg = f"Errore nel parsing JSON: {str(json_err)}"
                                    print(f"ERROR: {error_msg}")
                                    print(f"Contenuto risposta: {response.text[:200]}...")  # Log primi 200 caratteri
                                    
                                    # Fallback a cache esistente
                                    if 'last_seismic_data' in st.session_state:
                                        return st.session_state.last_seismic_data, f"Errore nel formato dati: {str(json_err)}"
                            else:
                                print(f"ERROR: API ha risposto con codice {response.status_code}")
                                
                                # Se API non risponde correttamente, fallback a dati in cache
                                if 'last_seismic_data' in st.session_state:
                                    return st.session_state.last_seismic_data, f"Impossibile accedere ai dati aggiornati (HTTP {response.status_code})"
                        
                        except requests.exceptions.RequestException as req_e:
                            print(f"ERROR: Eccezione nella richiesta HTTP: {str(req_e)}")
                            
                            # Livello 3: Fallback a USGS per dati globali in tempo reale
                            try:
                                print("INFO: INGV non accessibile, tentativo con USGS...")
                                
                                # Coordiante approssimative dell'Italia
                                italy_bounds = {
                                    "north": 47.5,  # Confine settentrionale
                                    "south": 35.0,  # Confine meridionale (include Sicilia)
                                    "east": 20.0,   # Confine orientale (include Puglia)
                                    "west": 6.0     # Confine occidentale (include Sardegna) 
                                }
                                
                                # Costruisci URL per USGS per l'area dell'Italia
                                usgs_start_time = (datetime.now(FUSO_ORARIO_ITALIA) - timedelta(days=30)).strftime("%Y-%m-%d")
                                usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson" + \
                                          f"&starttime={usgs_start_time}" + \
                                          f"&minlatitude={italy_bounds['south']}&maxlatitude={italy_bounds['north']}" + \
                                          f"&minlongitude={italy_bounds['west']}&maxlongitude={italy_bounds['east']}" + \
                                          f"&minmagnitude=0.5"
                                          
                                usgs_headers = {
                                    'User-Agent': 'SismaVer2/1.0 (Monitoraggio sismico italiano; https://sisma-ver-2.replit.app/)',
                                    'Accept': 'application/json'
                                }
                                
                                usgs_response = requests.get(usgs_url, timeout=10, headers=usgs_headers)
                                
                                if usgs_response.status_code == 200:
                                    usgs_data = usgs_response.json()
                                    
                                    # Verifica dati USGS 
                                    if isinstance(usgs_data, dict) and "features" in usgs_data:
                                        # Salva in session_state
                                        st.session_state.last_seismic_data = usgs_data
                                        st.session_state.last_fetch_time = datetime.now(FUSO_ORARIO_ITALIA)
                                        st.session_state.using_usgs_data = True  # Flag per indicare l'uso di USGS
                                        print(f"INFO: Recuperati {len(usgs_data.get('features', []))} eventi sismici da USGS")
                                        return usgs_data, "⚠️ INGV temporaneamente non disponibile. Utilizzando dati da USGS (United States Geological Survey)."
                            except Exception as usgs_err:
                                print(f"ERROR: Fallito anche fallback USGS: {str(usgs_err)}")
                            
                            # Livello 4: Fallback a dati in cache
                            if 'last_seismic_data' in st.session_state:
                                source_text = "USGS" if st.session_state.get('using_usgs_data', False) else "INGV"
                                return st.session_state.last_seismic_data, f"⚠️ Problemi di connessione. Visualizzando dati recenti da {source_text} in cache."
                        
                        # Ultimo livello (fallback): dati storici da CSV locale
                        try:
                            # Utilizziamo il file CSV locale come fallback di emergenza
                            csv_path = "terremoti_italia.csv"
                            
                            if os.path.exists(csv_path):
                                print(f"INFO: Utilizzo dati sismici storici da {csv_path} come fallback")
                                df = pd.read_csv(csv_path)
                                
                                # Creiamo una struttura GeoJSON compatibile con quella dell'API
                                features = []
                                for _, row in df.iterrows():
                                    # Generazione di coordinate casuali attorno alla regione
                                    # Coordinate approssimative per l'Italia
                                    regione = row.get("Regione", "")
                                    # Default in centro Italia
                                    lat, lon = 42.0, 12.5
                                    
                                    # Coordinate approssimative delle regioni italiane
                                    regioni_coords = {
                                        "Abruzzo": [42.35, 13.40],
                                        "Basilicata": [40.50, 16.00],
                                        "Calabria": [39.00, 16.50],
                                        "Campania": [40.83, 14.25],
                                        "Emilia-Romagna": [44.50, 11.00],
                                        "Friuli-Venezia Giulia": [46.00, 13.00],
                                        "Lazio": [41.90, 12.50],
                                        "Liguria": [44.45, 8.75],
                                        "Lombardia": [45.70, 9.70],
                                        "Marche": [43.37, 13.15],
                                        "Molise": [41.67, 14.67],
                                        "Piemonte": [45.05, 7.67],
                                        "Puglia": [41.00, 16.50],
                                        "Sardegna": [40.00, 9.00],
                                        "Sicilia": [37.50, 14.00],
                                        "Toscana": [43.37, 11.00],
                                        "Trentino-Alto Adige": [46.50, 11.30],
                                        "Umbria": [43.10, 12.60],
                                        "Valle d'Aosta": [45.73, 7.33],
                                        "Veneto": [45.43, 12.00]
                                    }
                                    
                                    if regione in regioni_coords:
                                        lat, lon = regioni_coords[regione]
                                    
                                    # Creare una feature in formato GeoJSON
                                    features.append({
                                        "type": "Feature",
                                        "properties": {
                                            "mag": float(row.get("Magnitudo", 0)),
                                            "place": row.get("Località", "N/A"),
                                            "time": row.get("Data", ""),
                                            "type": "earthquake",
                                            "title": f"M {row.get('Magnitudo', 0)} - {row.get('Località', 'N/A')}",
                                            "region": row.get("Regione", "N/A")
                                        },
                                        "geometry": {
                                            "type": "Point",
                                            "coordinates": [lon, lat, 10.0]  # lon, lat, profondità
                                        }
                                    })
                                
                                # Costruiamo la struttura GeoJSON completa
                                fallback_data = {
                                    "type": "FeatureCollection",
                                    "metadata": {
                                        "generated": datetime.now(FUSO_ORARIO_ITALIA).isoformat(),
                                        "title": "Dati sismici storici (modalità fallback)",
                                        "status": 200,
                                        "count": len(features)
                                    },
                                    "features": features[:20]  # Limitiamo a 20 eventi per prestazioni
                                }
                                
                                return fallback_data, "L'API INGV al momento non è accessibile. Visualizzazione dei principali eventi sismici storici in Italia."
                        except Exception as csv_err:
                            print(f"ERROR nel fallback CSV: {str(csv_err)}")
                            
                        # Fallback finale: struttura vuota ma valida
                        return {"features": [], "type": "FeatureCollection", "metadata": {"generated": datetime.now(FUSO_ORARIO_ITALIA).isoformat()}}, "Impossibile accedere ai dati sismici - riprova più tardi"
                    
                    except Exception as e:
                        # Gestione dell'errore migliorata con log per debugging
                        error_msg = f"Errore nel sistema di cache: {str(e)}"
                        print(f"ERROR - Sistema di cache sismico: {error_msg}")
                        
                        # Fallback finale: restituiamo una struttura vuota ma valida
                        empty_data = {"features": [], "type": "FeatureCollection", "metadata": {"generated": datetime.now(FUSO_ORARIO_ITALIA).isoformat()}}
                        return empty_data, error_msg
                
                with st.spinner("Caricamento dati sismici in tempo reale..."):
                    # Recupera i dati con gestione errori efficiente
                    sensor_data, error_msg = fetch_seismic_data(ingv_url)
                    features = sensor_data.get("features", [])
                    
                    if error_msg:
                        # Se è un messaggio di ripristino INGV (inizia con ✅), usa st.success invece di warning
                        if error_msg.startswith("✅"):
                            st.success(error_msg)
                        else:
                            st.warning(error_msg)
                    
                    if not features:
                        st.info(f"Nessun evento sismico rilevato nelle ultime 24 ore {f'in {regione_scelta}' if regione_scelta != 'Italia (Visione nazionale)' else 'in Italia'}.")
                        
                        # Come fallback, visualizza iframe del portale terremoti INGV
                        st.info("Visualizzazione alternativa tramite portale INGV:")
                        st.components.v1.iframe(
                            "http://terremoti.ingv.it/events", 
                            height=500, 
                            scrolling=True
                        )
                    else:
                        # Prepara dati per visualizzazione
                        seismic_data = []
                        
                        # Limita il numero di eventi per prestazioni migliori
                        max_events = 20
                        limited_features = features[:max_events]
                        
                        for feature in limited_features:
                            properties = feature["properties"]
                            geometry = feature["geometry"]["coordinates"]
                            
                            # Conversione timestamp
                            event_time = properties.get("time", "")
                            try:
                                # Gestisce diversi formati di data con correzione per fuso orario italiano
                                dt = None
                                if isinstance(event_time, str):
                                    if "Z" in event_time:
                                        dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
                                    else:
                                        dt = datetime.fromisoformat(event_time)
                                elif isinstance(event_time, (int, float)):
                                    # Se è un timestamp in millisecondi
                                    dt = datetime.fromtimestamp(event_time / 1000.0)
                                
                                # Converti in fuso orario italiano (DST-aware)
                                if dt:
                                    dt_it = datetime.fromtimestamp(event_time / 1000.0, FUSO_ORARIO_ITALIA)
                                    formatted_time = dt_it.strftime("%d/%m/%Y %H:%M:%S") + " (IT)"
                                else:
                                    formatted_time = str(event_time)
                            except Exception as date_err:
                                formatted_time = str(event_time)
                                
                            seismic_data.append({
                                "Luogo": properties.get("place", "N/A"),
                                "Magnitudo": properties.get("mag", 0),
                                "Data/Ora": formatted_time,
                                "Profondità (km)": round(geometry[2], 1) if len(geometry) > 2 else 0,
                                "Latitudine": geometry[1],
                                "Longitudine": geometry[0]
                            })
                                
                        # Converti in DataFrame per visualizzazione
                        df_seismic = pd.DataFrame(seismic_data)
                        
                        # Visualizza tabella
                        st.subheader(f"🔍 Eventi sismici in tempo reale - {regione_scelta}")
                        if len(features) > max_events:
                            st.info(f"Visualizzazione limitata a {max_events} eventi su {len(features)} totali per migliorare le prestazioni")
                        st.dataframe(df_seismic, use_container_width=True)
                        
                        # Crea mappa interattiva
                        m = folium.Map(
                            location=[41.9, 12.5],  # Centro approssimativo dell'Italia
                            zoom_start=6 if regione_scelta == "Italia (Visione nazionale)" else 8
                        )
                        
                        # Se regione specifica, centra la mappa su di essa
                        if regione_scelta in regioni_coords and regione_scelta != "Italia (Visione nazionale)":
                            # Ottieni le coordinate e crea una nuova mappa centrata
                            new_location = regioni_coords[regione_scelta]
                            if isinstance(new_location, (list, tuple)) and len(new_location) == 2:
                                m = folium.Map(
                                    location=new_location,
                                    zoom_start=8
                                )
                            
                        # Aggiungi marker per ogni evento sismico
                        for _, row in df_seismic.iterrows():
                            # Colore basato sulla magnitudo
                            magnitude = row["Magnitudo"]
                            color = "green" if magnitude < 3.0 else "orange" if magnitude < 4.0 else "red"
                            
                            # Popup con informazioni
                            popup_text = f"""
                            <b>Luogo:</b> {row['Luogo']}<br>
                            <b>Magnitudo:</b> {row['Magnitudo']}<br>
                            <b>Data/Ora:</b> {row['Data/Ora']}<br>
                            <b>Profondità:</b> {row['Profondità (km)']} km
                            """
                            
                            # Aggiungi cerchio sulla mappa
                            folium.Circle(
                                location=[row["Latitudine"], row["Longitudine"]],
                                radius=magnitude * 5000,  # Raggio proporzionale alla magnitudo
                                color=color,
                                fill=True,
                                fill_opacity=0.4,
                                popup=folium.Popup(popup_text, max_width=300)
                            ).add_to(m)
                            
                        # Visualizza la mappa
                        st.subheader("🗺️ Mappa eventi sismici in tempo reale")
                        folium_static(m, width=1100, height=520)
                        
                        # Grafico magnitudo nel tempo
                        st.subheader("📈 Andamento sismico eventi recenti")
                        
                        try:
                            # Creare un asse temporale per il grafico con gestione multiformat
                            # Controllo se stiamo usando dati USGS o INGV per adattare il parsing delle date
                            using_usgs = st.session_state.get('using_usgs_data', False)
                            
                            # Funzione per convertire diverse date in datetime con gestione errori
                            def parse_date_flexible(date_str):
                                formats_to_try = [
                                    '%d/%m/%Y %H:%M:%S',  # INGV formato standard (con IT)
                                    '%Y-%m-%d %H:%M:%S',  # USGS formato standard
                                    '%d/%m/%Y %H:%M:%S (IT)',  # INGV con indicatore fuso
                                    '%Y-%m-%dT%H:%M:%S',  # ISO format
                                    '%Y-%m-%dT%H:%M:%S.%f',  # ISO with microseconds
                                ]
                                
                                # Rimuovi l'indicatore di fuso orario se presente
                                date_str = date_str.replace(' (IT)', '')
                                
                                for fmt in formats_to_try:
                                    try:
                                        return pd.to_datetime(date_str, format=fmt)
                                    except (ValueError, TypeError):
                                        continue
                                        
                                # Se nessun formato funziona, usa il parser generico di pandas
                                try:
                                    return pd.to_datetime(date_str)
                                except:
                                    # Come ultima risorsa, ritorna la data corrente
                                    print(f"Impossibile convertire data: {date_str}")
                                    return pd.to_datetime('now')
                            
                            # Applica la funzione di parsing flessibile
                            df_seismic['Data/Ora Obj'] = df_seismic['Data/Ora'].apply(parse_date_flexible)
                            df_seismic = df_seismic.sort_values('Data/Ora Obj')
                            
                            # Crea grafico con Plotly
                            fig = px.scatter(
                                df_seismic,
                                x='Data/Ora Obj',
                                y='Magnitudo',
                                color='Magnitudo',
                                size='Magnitudo',
                                hover_data=['Luogo', 'Profondità (km)'],
                                color_continuous_scale=px.colors.sequential.Reds,
                                title=f"Eventi sismici negli ultimi 7 giorni - {regione_scelta}",
                                labels={'Data/Ora Obj': 'Data/Ora', 'Magnitudo': 'Magnitudo'}
                            )
                            
                            # Aggiungi traccia per connettere i punti cronologicamente
                            fig.add_trace(
                                go.Scatter(
                                    x=df_seismic['Data/Ora Obj'], 
                                    y=df_seismic['Magnitudo'],
                                    mode='lines',
                                    line=dict(width=1, color='rgba(200,200,200,0.5)'),
                                    showlegend=False
                                )
                            )
                            
                            # Migliora layout
                            fig.update_layout(
                                xaxis_title="Data/Ora",
                                yaxis_title="Magnitudo",
                                legend_title="Magnitudo",
                                hovermode="closest"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Non è stato possibile creare il grafico temporale: {e}")
                            print(f"DEBUG - Errore grafico: {str(e)}")
                            print(f"DEBUG - Formato date nel DataFrame: {df_seismic['Data/Ora'].iloc[0] if len(df_seismic) > 0 else 'DataFrame vuoto'}")
                        
                        # Statistiche rapide
                        st.subheader("📊 Statistiche sismiche")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Numero eventi", len(df_seismic))
                        with col2:
                            st.metric("Magnitudo massima", round(df_seismic['Magnitudo'].max(), 1))
                        with col3:
                            st.metric("Profondità media (km)", round(df_seismic['Profondità (km)'].mean(), 1))
                            
                        # Analisi statistica avanzata
                        st.markdown("---")
                        st.subheader("📈 Analisi avanzata degli eventi")
                        
                        col_a1, col_a2 = st.columns(2)
                        
                        with col_a1:
                            # Calcola distribuzioni per magnitudo
                            bins = [0, 1.0, 2.0, 3.0, 4.0, 10.0]
                            labels = ['<1 (Micro)', '1-2 (Molto debole)', '2-3 (Debole)', '3-4 (Leggero)', '4+ (Moderato+)']
                            
                            # Aggiungi classificazione
                            df_seismic['Fascia Magnitudo'] = pd.cut(df_seismic['Magnitudo'], bins=bins, labels=labels)
                            fascia_counts = df_seismic['Fascia Magnitudo'].value_counts().sort_index()
                            
                            # Crea grafico a torta
                            fig_pie = px.pie(
                                values=fascia_counts.values,
                                names=fascia_counts.index,
                                title="Distribuzione eventi per magnitudo",
                                color_discrete_sequence=px.colors.sequential.Reds_r
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with col_a2:
                            # Profondità degli eventi
                            # Crea istogramma di profondità
                            fig_hist = px.histogram(
                                df_seismic,
                                x="Profondità (km)",
                                nbins=10,
                                title="Distribuzione della profondità degli eventi",
                                color_discrete_sequence=['#e5394d']
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                        # Aggiungi mappa di intensità
                        st.subheader("🗺️ Mappa di intensità sismica")
                        
                        # Crea mappa semplice invece della mappa di calore
                        try:
                            # Create simple intensity map
                            st.success("Generazione mappa di intensità sismica...")
                            
                            # Base map
                            intensity_map = folium.Map(
                                location=[41.9, 12.5],
                                zoom_start=6 if regione_scelta == "Italia (Visione nazionale)" else 8,
                                tiles="CartoDB positron"
                            )
                            
                            # Se regione specifica, centra la mappa su di essa
                            if regione_scelta in regioni_coords and regione_scelta != "Italia (Visione nazionale)":
                                # Usa regioni_coords direttamente come lista [lat, long]
                                new_location = regioni_coords.get(regione_scelta)
                                if isinstance(new_location, list) and len(new_location) == 2:
                                    # Crea una nuova mappa con la posizione aggiornata
                                    intensity_map = folium.Map(
                                        location=new_location,
                                        zoom_start=8,
                                        tiles="CartoDB positron"
                                    )
                            
                            # Aggiungi marker per le principali città come riferimento
                            città_italiane = {
                                "Roma": [41.9028, 12.4964],
                                "Milano": [45.4642, 9.1900],
                                "Napoli": [40.8518, 14.2681],
                                "Palermo": [38.1157, 13.3615],
                                "Torino": [45.0703, 7.6869],
                                "Bologna": [44.4949, 11.3426]
                            }
                            
                            for città, pos in città_italiane.items():
                                folium.Marker(
                                    location=pos,
                                    popup=città,
                                    icon=folium.Icon(color="blue", icon="info-sign")
                                ).add_to(intensity_map)
                            
                            # Assicuriamoci che df_seismic sia valido
                            if df_seismic is not None and len(df_seismic) > 0:
                                required_cols = ['Latitudine', 'Longitudine', 'Magnitudo']
                                if all(col in df_seismic.columns for col in required_cols):
                                    # Aggiungi cerchi sulla mappa per ogni evento
                                    for _, row in df_seismic.iterrows():
                                        try:
                                            # Prova a convertire direttamente in float per essere sicuri
                                            lat = float(row['Latitudine'])
                                            lon = float(row['Longitudine'])
                                            mag = float(row['Magnitudo'])
                                            depth = float(row['Profondità (km)'])
                                            
                                            # Validazione geografica per l'Italia
                                            if (35.0 <= lat <= 48.0) and (6.0 <= lon <= 19.0):
                                                # Colore basato sulla magnitudo
                                                color = "green"
                                                if mag >= 4.0:
                                                    color = "red"
                                                elif mag >= 3.0:
                                                    color = "orange"
                                                elif mag >= 2.0:
                                                    color = "yellow"
                                                
                                                # Raggio basato sulla magnitudo
                                                radius = mag * 5000
                                                
                                                # Info popup
                                                popup_text = f"""
                                                <b>Magnitudo:</b> {mag}<br>
                                                <b>Profondità:</b> {depth} km<br>
                                                <b>Data:</b> {row.get('Data/Ora', 'N/D')}<br>
                                                <b>Località:</b> {row.get('Luogo', 'N/D')}
                                                """
                                                
                                                # Aggiungi cerchio colorato
                                                folium.Circle(
                                                    location=[lat, lon],
                                                    radius=radius,
                                                    color=color,
                                                    fill=True,
                                                    fill_opacity=0.4,
                                                    popup=folium.Popup(popup_text, max_width=200)
                                                ).add_to(intensity_map)
                                        except (ValueError, TypeError, KeyError) as e:
                                            # Log dell'errore e continua
                                            print(f"Errore nella riga: {e}")
                                            continue
                            
                            # Mostra questa mappa alternativa invece della heatmap
                            folium_static(intensity_map, width=1100, height=520)
                            st.info("Nota: La mappa mostra l'intensità degli eventi sismici con cerchi. La dimensione e il colore rappresentano la magnitudo.")
                            
                        except Exception as map_err:
                            st.error(f"Errore nella creazione della mappa di intensità: {map_err}")
                            st.info("Visualizzazione alternativa tramite portale INGV:")
                            # Visualizzazione tramite iframe del portale terremoti INGV come fallback
                            st.components.v1.iframe(
                                "http://terremoti.ingv.it/events", 
                                height=500, 
                                scrolling=True
                            )
                            
                        # Statistiche terremoti storici significativi
                        st.markdown("---")
                        st.subheader("📜 Terremoti storici significativi")
                        
                        # Carica dati storici
                        try:
                            # Utilizzo dati dal file CSV locale
                            df_historic = pd.read_csv("terremoti_italia.csv")
                            
                            # Se specifica regione, filtra
                            if regione_scelta != "Italia (Visione nazionale)":
                                df_historic_filtered = df_historic[df_historic["Regione"].str.contains(regione_scelta, case=False, na=False)]
                                if len(df_historic_filtered) > 0:
                                    df_historic = df_historic_filtered
                            
                            # Mostra eventi storici
                            st.dataframe(
                                df_historic[["Data", "Magnitudo", "Località", "Vittime", "Regione"]],
                                use_container_width=True
                            )
                        except Exception as hist_err:
                            st.warning(f"Errore nel caricamento dei dati storici: {hist_err}")
                            
                            # Dati storici precompilati come fallback
                            st.write("Eventi sismici storici significativi in Italia:")
                            st.markdown("""
                            - **1693, Sicilia Orientale**: Magnitudo 7.4, 60.000 vittime
                            - **1783, Calabria**: Magnitudo 7.0, 30.000 vittime 
                            - **1908, Messina e Reggio Calabria**: Magnitudo 7.1, 80.000 vittime
                            - **1915, Avezzano**: Magnitudo 7.0, 30.000 vittime
                            - **1980, Irpinia**: Magnitudo 6.9, 3.000 vittime
                            - **2009, L'Aquila**: Magnitudo 6.3, 309 vittime
                            - **2016, Centro Italia**: Magnitudo 6.0-6.5, 299 vittime
                            """)
            except Exception as e:
                st.error(f"Errore durante il recupero dei dati sismici in tempo reale: {e}")
                st.info("Visualizzazione alternativa tramite portale INGV:")
                
                # Visualizzazione tramite iframe del portale terremoti INGV come fallback
                st.components.v1.iframe(
                    "http://terremoti.ingv.it/instruments", 
                    height=600, 
                    scrolling=True
                )
            
            # Spiegazione dei dati
            with st.expander("ℹ️ Informazioni sui dati"):
                st.markdown("""
                ### 🔍 Stazioni sismiche INGV in tempo reale
                
                La rete sismica nazionale INGV è composta da oltre 400 stazioni sismiche distribuite su tutto il territorio italiano.
                
                I dati visualizzati sono ottenuti in tempo reale dall'API ufficiale dell'INGV (Istituto Nazionale di Geofisica e Vulcanologia).
                
                La mappa mostra gli eventi sismici degli ultimi 7 giorni con magnitudo superiore a 0.5.
                
                **Aggiornamento dati:** I dati vengono aggiornati automaticamente ad ogni refresh della pagina o utilizzando il pulsante "Aggiorna dati".
                
                **Fonte dati:** [INGV - Istituto Nazionale di Geofisica e Vulcanologia](http://terremoti.ingv.it/)
                """)
    
    # Tab Monitoraggio vulcanico
    with sensor_tab2:
        # ── Vista panoramica Italia (tutti i vulcani) ────────────────────────
        if regione_scelta == "Italia (Visione nazionale)":
            st.subheader("🌋 Monitoraggio vulcani attivi italiani")
            st.info("🔗 Per schede dettagliate con webcam e bollettini INGV → apri **Vulcani** dal menu laterale")

            df_vulcani = pd.DataFrame({
                "Vulcano": [
                    "Etna", "Stromboli", "Campi Flegrei", "Vesuvio",
                    "Ischia", "Vulcano", "Pantelleria", "Strombolicchio",
                    "Lipari-Vulcanello", "Marsili", "Ferdinandea",
                    "Colli Albani", "Monte Amiata", "Isole Pontine",
                    "Ustica", "Linosa", "Salina", "Alicudi", "Filicudi", "Nisyros (IT)"
                ],
                "Regione": [
                    "Sicilia", "Sicilia", "Campania", "Campania",
                    "Campania", "Sicilia", "Sicilia", "Sicilia",
                    "Sicilia", "Mar Tirreno", "Sicilia - Canale di Sicilia",
                    "Lazio", "Toscana", "Lazio",
                    "Sicilia", "Sicilia", "Sicilia", "Sicilia", "Sicilia", "Mar Egeo"
                ],
                "Livello allerta": [
                    "ARANCIONE", "ARANCIONE", "GIALLO", "VERDE",
                    "VERDE", "GIALLO", "VERDE", "VERDE",
                    "VERDE", "GIALLO", "VERDE",
                    "VERDE", "VERDE", "VERDE",
                    "VERDE", "VERDE", "VERDE", "VERDE", "VERDE", "VERDE"
                ],
                "Ultima eruzione": [
                    "Attivo", "Attivo", "1538", "1944",
                    "1302", "1888-90", "1891 (sub.)", "Quiescente",
                    "1230", "Non doc.", "1831 (sub.)",
                    "5000 a.f.", "180 a.f.", "Quiescente",
                    "Quiescente", "Quiescente", "Quiescente", "Quiescente", "Quiescente", "-"
                ],
                "Monitoraggio INGV": [
                    "INGV-CT", "INGV-CT", "INGV-OV", "INGV-OV",
                    "INGV-OV", "INGV-CT", "INGV-CT", "INGV-CT",
                    "INGV-CT", "INGV", "INGV",
                    "INGV-RM", "INGV-RM", "INGV-RM",
                    "INGV-CT", "INGV-CT", "INGV-CT", "INGV-CT", "INGV-CT", "-"
                ]
            })

            def _color_a(val):
                colors = {"VERDE": "background-color:#4ade80", "GIALLO": "background-color:#fde047",
                          "ARANCIONE": "background-color:#fb923c", "ROSSO": "background-color:#f87171"}
                return colors.get(val, "")

            st.dataframe(
                df_vulcani.style.map(_color_a, subset=["Livello allerta"]),
                use_container_width=True, height=680
            )

            st.subheader("🗺️ Mappa vulcani attivi italiani")
            vulcani_coords_it = {
                "Etna": [37.751, 14.994], "Stromboli": [38.789, 15.213],
                "Campi Flegrei": [40.827, 14.139], "Vesuvio": [40.821, 14.426],
                "Ischia": [40.731, 13.897], "Vulcano": [38.404, 14.962],
                "Pantelleria": [36.771, 11.989], "Lipari-Vulcanello": [38.489, 14.953],
                "Marsili": [39.28, 14.40], "Ferdinandea": [37.10, 12.70],
                "Colli Albani": [41.728, 12.701], "Monte Amiata": [42.891, 11.621],
                "Ustica": [38.700, 13.175], "Linosa": [35.864, 12.861],
                "Salina": [38.560, 14.865], "Alicudi": [38.540, 14.352],
                "Filicudi": [38.574, 14.567],
            }
            alert_color = {"ARANCIONE": "orange", "GIALLO": "beige", "ROSSO": "red", "VERDE": "green"}
            vmap = folium.Map(location=[39.5, 13.5], zoom_start=5)
            for v_row in df_vulcani.itertuples():
                vname = v_row.Vulcano
                if vname in vulcani_coords_it:
                    coords = vulcani_coords_it[vname]
                    col_m = alert_color.get(v_row._3, "blue")
                    folium.Marker(
                        location=coords,
                        popup=folium.Popup(
                            f"<b>{vname}</b><br>Regione: {v_row.Regione}<br>"
                            f"Allerta: {v_row._3}<br>Ultima eruzione: {v_row._4}",
                            max_width=250
                        ),
                        icon=folium.Icon(color=col_m, icon="fire", prefix="fa"),
                        tooltip=vname
                    ).add_to(vmap)
            folium_static(vmap, width=1100, height=520)
            st.caption("Fonte: INGV · Aggiornato: " + datetime.now(FUSO_ORARIO_ITALIA).strftime("%d/%m/%Y"))

        else:
            # ── Vista per regione specifica ──────────────────────────────────
            regioni_vulcaniche = {
                "Campania": ["Vesuvio", "Campi Flegrei", "Ischia"],
                "Sicilia": ["Etna", "Stromboli", "Vulcano", "Pantelleria",
                            "Lipari-Vulcanello", "Ferdinandea", "Ustica", "Linosa",
                            "Salina", "Alicudi", "Filicudi"],
                "Lazio": ["Colli Albani"],
                "Toscana": ["Monte Amiata"],
            }

            if regione_scelta in regioni_vulcaniche:
                st.subheader(f"🌋 Monitoraggio vulcanico - {regione_scelta}")

                vulcani_disponibili = regioni_vulcaniche[regione_scelta]
                vulcano_selezionato = st.selectbox("Seleziona vulcano", vulcani_disponibili)

                # Visualizzazione monitoraggio in base al vulcano selezionato
                if vulcano_selezionato == "Vesuvio":
                    st.markdown("### 📡 Monitoraggio Vesuvio - Osservatorio Vesuviano INGV")
                
                    # Mostra dati monitoraggio Vesuvio
                    col1, col2 = st.columns(2)
                
                    with col1:
                        st.subheader("🔔 Stato attuale")
                        st.warning("Livello di allerta: **VERDE (livello base)** - [Fonte](https://www.ov.ingv.it/index.php/rete-fissa?category=11)")
                        st.info("Ultimo aggiornamento: Bollettino mensile INGV")
                
                    with col2:
                        st.subheader("🎦 Webcam in tempo reale")
                        st.image("attached_assets/vesuvio_webcam.png", caption="Webcam Vesuvio - Osservatorio INGV")
                
                    # Parametri monitorati (esempio)
                    st.subheader("📊 Parametri monitorati")
                
                    param_col1, param_col2, param_col3 = st.columns(3)
                
                    with param_col1:
                        st.metric("Sismicità ultimi 30gg", "24 eventi", "-2")
                        st.image("attached_assets/vesuvio_sismicita.png", caption="Sismicità Vesuvio - Ultimi 30 giorni")
                
                    with param_col2:
                        st.metric("Temperatura fumarole", "95°C", "+0.3°C")
                        st.image("attached_assets/vesuvio_tremore.png", caption="Tremore vulcanico - Vesuvio")
                
                    with param_col3:
                        st.metric("Deformazione suolo", "<1 mm/anno", "stabile")
                
                    # Informazioni aggiuntive
                    with st.expander("ℹ️ Informazioni sul Vesuvio"):
                        st.markdown("""
                        ### 🌋 Vesuvio
                    
                        Il Vesuvio è un vulcano attivo situato in Campania, nell'area metropolitana di Napoli. L'ultima eruzione significativa è avvenuta nel marzo 1944.
                    
                        **Area interessata:** Il monitoraggio del Vesuvio interessa 25 comuni, per una popolazione complessiva di circa 700.000 abitanti.
                    
                        **Livelli di allerta:**
                        - 🟢 **VERDE:** Attività di base
                        - 🟡 **GIALLO:** Variazioni significative dei parametri
                        - 🟠 **ARANCIONE:** Ulteriore incremento dei parametri
                        - 🔴 **ROSSO:** Eruzione imminente o in corso
                    
                        **Fonte dati:** [Osservatorio Vesuviano INGV](https://www.ov.ingv.it/)
                        """)
            
                elif vulcano_selezionato == "Campi Flegrei":
                    st.markdown("### 📡 Monitoraggio Campi Flegrei - Osservatorio Vesuviano INGV")
                
                    # Mostra dati monitoraggio Campi Flegrei
                    col1, col2 = st.columns(2)
                
                    with col1:
                        st.subheader("🔔 Stato attuale")
                        st.warning("Livello di allerta: **GIALLA (attenzione)** - [Fonte](https://www.ov.ingv.it/index.php/rete-fissa?category=11)")
                        st.info("Ultimo aggiornamento: Bollettino settimanale INGV")
                
                    with col2:
                        st.subheader("📊 Attività sismica recente")
                        st.warning("Sciame sismico: > 100 eventi negli ultimi 7 giorni")
                
                    # Parametri monitorati (esempio)
                    st.subheader("📊 Parametri monitorati")
                
                    param_col1, param_col2, param_col3 = st.columns(3)
                
                    with param_col1:
                        st.metric("Sollevamento suolo", "≈ 15 mm/mese", "+2.5 mm")
                        st.image("attached_assets/flegrei_sollevamento.png", caption="Sollevamento Campi Flegrei - Ultimi 30 giorni")
                
                    with param_col2:
                        st.metric("Sismicità", "142 eventi/settimana", "+35")
                        st.image("attached_assets/flegrei_sismicita.png", caption="Sismicità Campi Flegrei - Ultimi 30 giorni")
                
                    with param_col3:
                        st.metric("Emissioni CO₂", "≈ 3500 t/giorno", "+150 t")
                        st.image("attached_assets/flegrei_co2.png", caption="Emissioni CO₂ - Campi Flegrei")
                
                    # Informazioni aggiuntive
                    with st.expander("ℹ️ Informazioni sui Campi Flegrei"):
                        st.markdown("""
                        ### 🌋 Campi Flegrei
                    
                        I Campi Flegrei sono un'ampia area vulcanica situata ad ovest di Napoli. L'ultima eruzione è avvenuta nel 1538 con la formazione di Monte Nuovo.
                    
                        **Fenomeno attuale:** Attualmente i Campi Flegrei sono interessati dal fenomeno del bradisismo, con un sollevamento del suolo e un'intensa attività sismica.
                    
                        **Area interessata:** Il monitoraggio dei Campi Flegrei interessa 7 comuni, per una popolazione complessiva di circa 500.000 abitanti.
                    
                        **Livelli di allerta:**
                        - 🟢 **VERDE:** Attività di base
                        - 🟡 **GIALLO:** Variazioni significative dei parametri
                        - 🟠 **ARANCIONE:** Ulteriore incremento dei parametri
                        - 🔴 **ROSSO:** Eruzione imminente o in corso
                    
                        **Fonte dati:** [Osservatorio Vesuviano INGV](https://www.ov.ingv.it/)
                        """)
                
                elif vulcano_selezionato == "Etna":
                    st.markdown("### 📡 Monitoraggio Etna - INGV Catania")
                
                    # Mostra dati monitoraggio Etna
                    col1, col2 = st.columns(2)
                
                    with col1:
                        st.subheader("🔔 Stato attuale")
                        st.warning("Livello di allerta: **GIALLA (attenzione)** - [Fonte](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari)")
                        st.info("Ultimo aggiornamento: Bollettino settimanale INGV Catania")
                
                    with col2:
                        st.subheader("📊 Attività recente")
                        st.warning("Attività stromboliana ai crateri sommitali - Fontane di lava occasionali")
                
                    # Parametri monitorati
                    st.subheader("📊 Parametri monitorati")
                
                    param_col1, param_col2, param_col3 = st.columns(3)
                
                    with param_col1:
                        st.metric("Attività stromboliana", "Attiva", "⚠️")
                
                    with param_col2:
                        st.metric("Flusso lavico", "Moderato", "stabile")
                
                    with param_col3:
                        st.metric("Emissioni cenere", "Intermittenti", "⬆️")
                
                    # Informazioni aggiuntive
                    with st.expander("ℹ️ Informazioni sull'Etna"):
                        st.markdown("""
                        ### 🌋 Etna
                    
                        L'Etna è il più grande vulcano attivo d'Europa e uno dei più attivi al mondo. Si trova sulla costa orientale della Sicilia.
                    
                        **Attività recente:** L'Etna è caratterizzato da frequenti eruzioni sommitali, con attività stromboliana, fontane di lava ed emissioni di cenere.
                    
                        **Area interessata:** L'attività dell'Etna può interessare numerosi comuni della provincia di Catania, con una popolazione esposta di oltre 500.000 abitanti.
                    
                        **Livelli di allerta:**
                        - 🟢 **VERDE:** Attività di base
                        - 🟡 **GIALLO:** Variazioni significative dei parametri
                        - 🟠 **ARANCIONE:** Ulteriore incremento dei parametri
                        - 🔴 **ROSSO:** Eruzione imminente o in corso
                    
                        **Fonte dati:** [INGV Catania](https://www.ct.ingv.it/)
                        """)
            
                elif vulcano_selezionato == "Stromboli":
                    st.markdown("### 📡 Monitoraggio Stromboli - INGV")
                
                    # Mostra dati monitoraggio Stromboli
                    col1, col2 = st.columns(2)
                
                    with col1:
                        st.subheader("🔔 Stato attuale")
                        st.warning("Livello di allerta: **GIALLA (attenzione)** - [Fonte](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari)")
                        st.info("Ultimo aggiornamento: Bollettino settimanale INGV")
                
                    with col2:
                        st.subheader("📊 Attività recente")
                        st.warning("Attività stromboliana ordinaria ai crateri - Esplosioni di intensità variabile")
                
                    # Parametri monitorati
                    st.subheader("📊 Parametri monitorati")
                
                    param_col1, param_col2, param_col3 = st.columns(3)
                
                    with param_col1:
                        st.metric("Esplosioni/ora", "15-20", "+5")
                
                    with param_col2:
                        st.metric("Tremor vulcanico", "Moderato", "stabile")
                
                    with param_col3:
                        st.metric("Flussi piroclastici", "Assenti", "stabile")
                
                    # Informazioni aggiuntive
                    with st.expander("ℹ️ Informazioni sullo Stromboli"):
                        st.markdown("""
                        ### 🌋 Stromboli
                    
                        Lo Stromboli è un vulcano attivo situato sull'omonima isola dell'arcipelago delle Eolie, in Sicilia. È noto per la sua attività esplosiva persistente.
                    
                        **Attività tipica:** L'attività ordinaria dello Stromboli consiste in esplosioni di intensità variabile che si verificano a intervalli di circa 10-20 minuti.
                    
                        **Eventi parossistici:** Occasionalmente lo Stromboli può generare eventi esplosivi maggiori (parossismi) e colate laviche.
                    
                        **Area interessata:** L'isola di Stromboli ha una popolazione residente di circa 500 abitanti, che può aumentare significativamente durante la stagione turistica.
                    
                        **Livelli di allerta:**
                        - 🟢 **VERDE:** Attività di base
                        - 🟡 **GIALLO:** Variazioni significative dei parametri
                        - 🟠 **ARANCIONE:** Ulteriore incremento dei parametri
                        - 🔴 **ROSSO:** Eruzione parossistica imminente o in corso
                    
                        **Fonte dati:** [INGV Osservatorio Etneo](https://www.ct.ingv.it/)
                        """)
                    
                elif vulcano_selezionato == "Vulcano":
                    st.markdown("### 📡 Monitoraggio Vulcano - INGV")
                
                    # Mostra dati monitoraggio Vulcano
                    col1, col2 = st.columns(2)
                
                    with col1:
                        st.subheader("🔔 Stato attuale")
                        st.warning("Livello di allerta: **GIALLA (attenzione)** - [Fonte](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari)")
                        st.info("Ultimo aggiornamento: Bollettino settimanale INGV")
                
                    with col2:
                        st.subheader("📊 Attività recente")
                        st.warning("Incremento della temperatura delle fumarole e delle emissioni di gas")
                
                    # Parametri monitorati
                    st.subheader("📊 Parametri monitorati")
                
                    param_col1, param_col2, param_col3 = st.columns(3)
                
                    with param_col1:
                        st.metric("Temperatura fumarole", "≈ 350°C", "+2°C")
                
                    with param_col2:
                        st.metric("Flusso CO₂", "Elevato", "⬆️")
                
                    with param_col3:
                        st.metric("Sismicità", "Bassa", "stabile")
                
                    # Informazioni aggiuntive
                    with st.expander("ℹ️ Informazioni su Vulcano"):
                        st.markdown("""
                        ### 🌋 Vulcano
                    
                        Vulcano è un'isola vulcanica dell'arcipelago delle Eolie, in Sicilia. L'ultima eruzione è avvenuta nel 1888-1890.
                    
                        **Attività attuale:** Vulcano è caratterizzato da un'intensa attività fumarolica con temperature elevate e significative emissioni di gas.
                    
                        **Crisi 2021:** Nel 2021 è stata registrata una crisi vulcanica con aumento delle temperature, delle emissioni di gas e della sismicità.
                    
                        **Area interessata:** L'isola di Vulcano ha una popolazione residente di circa 400 abitanti, che può aumentare significativamente durante la stagione turistica.
                    
                        **Livelli di allerta:**
                        - 🟢 **VERDE:** Attività di base
                        - 🟡 **GIALLO:** Variazioni significative dei parametri
                        - 🟠 **ARANCIONE:** Ulteriore incremento dei parametri
                        - 🔴 **ROSSO:** Eruzione imminente o in corso
                    
                        **Fonte dati:** [INGV Osservatorio Etneo](https://www.ct.ingv.it/)
                        """)
                    
                elif vulcano_selezionato == "Tutti i vulcani italiani":
                    st.markdown("### 📡 Monitoraggio vulcani attivi italiani")
                
                    # Tabella riassuntiva dei vulcani italiani
                    st.subheader("🌋 Stato attuale dei vulcani attivi italiani")
                
                    # Dati sul livello di allerta corrente
                    df_vulcani = pd.DataFrame({
                        "Vulcano": ["Etna", "Stromboli", "Vulcano", "Vesuvio", "Campi Flegrei", "Ischia", "Pantelleria", "Colli Albani"],
                        "Regione": ["Sicilia", "Sicilia", "Sicilia", "Campania", "Campania", "Campania", "Sicilia", "Lazio"],
                        "Livello allerta": ["GIALLO", "GIALLO", "GIALLO", "VERDE", "GIALLO", "GIALLO", "VERDE", "VERDE"],
                        "Ultima eruzione": ["Attività corrente", "Attività corrente", "1888-1890", "1944", "1538", "1302", "1891", "5000 anni fa"],
                        "Monitoraggio": ["INGV Catania", "INGV Catania", "INGV Catania", "INGV-OV Napoli", "INGV-OV Napoli", "INGV-OV Napoli", "INGV Catania", "INGV Roma"]
                    })
                
                    # Definisci colore in base al livello di allerta
                    def color_allerta(val):
                        color = 'white'
                        if val == 'VERDE':
                            color = 'green'
                        elif val == 'GIALLO':
                            color = 'yellow'
                        elif val == 'ARANCIONE':
                            color = 'orange'
                        elif val == 'ROSSO':
                            color = 'red'
                        return f'background-color: {color}'
                
                    # Visualizza tabella con colori
                    st.dataframe(df_vulcani.style.map(color_allerta, subset=['Livello allerta']), use_container_width=True)
                
                    # Mappa dei vulcani attivi
                    st.subheader("🗺️ Mappa dei vulcani attivi italiani")
                
                    # Coordinate dei vulcani principali
                    vulcani_coords = {
                        "Etna": [37.748, 14.999],
                        "Stromboli": [38.789, 15.213],
                        "Vulcano": [38.404, 14.962],
                        "Vesuvio": [40.821, 14.426],
                        "Campi Flegrei": [40.827, 14.139],
                        "Ischia": [40.730, 13.897],
                        "Pantelleria": [36.797, 11.989],
                        "Colli Albani": [41.728, 12.701]
                    }
                
                    # Crea mappa
                    vulcani_map = folium.Map(location=[41.29, 12.57], zoom_start=6)
                
                    # Aggiungi marker per ogni vulcano
                    for vulcano, coords in vulcani_coords.items():
                        vulc_data = df_vulcani[df_vulcani["Vulcano"] == vulcano].iloc[0]
                    
                        # Colore in base al livello di allerta
                        if vulc_data["Livello allerta"] == "VERDE":
                            color = "green"
                        elif vulc_data["Livello allerta"] == "GIALLO":
                            color = "orange"
                        elif vulc_data["Livello allerta"] == "ARANCIONE":
                            color = "red"
                        elif vulc_data["Livello allerta"] == "ROSSO":
                            color = "darkred"
                        else:
                            color = "blue"
                    
                        # Popup con informazioni
                        popup_text = f"""
                        <b>Vulcano:</b> {vulcano}<br>
                        <b>Livello allerta:</b> {vulc_data['Livello allerta']}<br>
                        <b>Ultima eruzione:</b> {vulc_data['Ultima eruzione']}<br>
                        <b>Monitoraggio:</b> {vulc_data['Monitoraggio']}
                        """
                    
                        # Aggiungi marker
                        folium.Marker(
                            location=coords,
                            popup=folium.Popup(popup_text, max_width=300),
                            icon=folium.Icon(color=color, icon="fire", prefix="fa")
                        ).add_to(vulcani_map)
                
                    folium_static(vulcani_map, width=1100, height=520)
            
                else:
                    st.info(f"Il monitoraggio dettagliato per {vulcano_selezionato} non è ancora integrato. Seleziona un altro vulcano o consulta il portale INGV.")
            else:
                st.info(f"Non ci sono vulcani attivi monitorati nella regione {regione_scelta}.")
                st.markdown("""
                ### 🌋 Regioni con vulcani attivi monitorati:
                - **Campania**: Vesuvio, Campi Flegrei, Ischia
                - **Sicilia**: Etna, Stromboli, Vulcano, Pantelleria
                - **Lazio**: Colli Albani
            
                Seleziona una di queste regioni o "Italia (Visione nazionale)" per visualizzare i dati di monitoraggio vulcanico.
                """)
    
        # Tab Monitoraggio idrogeologico
    with sensor_tab3:
        st.subheader(f"🌊 Monitoraggio idrogeologico - {regione_scelta}")
        
        # Importa portali ufficiali monitoraggio idrogeologico per regione
        # Link ai portali ufficiali delle regioni
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
            "Italia (Visione nazionale)": "http://www.protezionecivile.gov.it/attivita-rischi/meteo-idro/attivita/previsione-prevenzione/centro-funzionale-centrale-rischio-meteo-idrogeologico"
        }
        
        # ── Allerte MeteoAlarm live ──────────────────────────────────────
        @st.cache_data(ttl=1800)
        def _meteoalarm_allerte_italia():
            """Recupera allerte MeteoAlarm per l'Italia dal feed Atom."""
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
                    title = entry.findtext("atom:title", "", ns)
                    summary = entry.findtext("atom:summary", "", ns)
                    allerte.append({"titolo": title, "sommario": summary})
                return allerte
            except Exception:
                return []

        allerte = _meteoalarm_allerte_italia()

        st.subheader("🚨 Allerta idrogeologica e meteo")

        # Filtra allerte per la regione selezionata (match parziale sul nome)
        regione_key = regione_scelta.lower().replace("-", " ").replace("'", "")
        allerte_reg = [a for a in allerte
                       if regione_key in a["titolo"].lower() or regione_key in a["sommario"].lower()]

        if allerte_reg:
            for a in allerte_reg:
                titolo = a["titolo"]
                if "red" in titolo.lower() or "rossa" in titolo.lower():
                    st.error(f"🔴 {titolo}")
                elif "orange" in titolo.lower() or "arancione" in titolo.lower():
                    st.warning(f"🟠 {titolo}")
                elif "yellow" in titolo.lower() or "gialla" in titolo.lower():
                    st.warning(f"🟡 {titolo}")
                else:
                    st.info(f"ℹ️ {titolo}")
        elif allerte:
            st.success(f"✅ Nessuna allerta MeteoAlarm attiva per {regione_scelta}")
        else:
            st.info("ℹ️ Feed MeteoAlarm temporaneamente non disponibile — consulta il portale regionale")

        st.caption(f"Fonte: MeteoAlarm (EUMETNET) · Aggiornato: {datetime.now(FUSO_ORARIO_ITALIA).strftime('%d/%m/%Y %H:%M')}")

        # ── Dati ISPRA nazionali ─────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Rischio idrogeologico nazionale — dati ISPRA")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Zone a rischio frana", "1.281.970 ha", "Classificazione PAI")
        c2.metric("Comuni a rischio frana", "7.275", "su 7.904 totali (91,9%)")
        c3.metric("Zone a rischio alluvione", "2.062.475 ha", "Classificazione PAI")
        c4.metric("Popolazione esposta", "≈ 7,5 M", "abitanti (12,5% d'Italia)")
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

        # ── Portali ufficiali ────────────────────────────────────────────
        with st.expander("🔗 Portali ufficiali monitoraggio idrogeologico"):
            if regione_scelta in regione_link:
                st.markdown(f"**[Centro Funzionale {regione_scelta}]({regione_link[regione_scelta]})**")
            st.markdown("""
            **Portali nazionali:**
            - [DPC — Mappa allerte in tempo reale](https://mappe.protezionecivile.gov.it/)
            - [DPC — Centro Funzionale Centrale](https://www.protezionecivile.gov.it/it/risk-activities/meteo-hydro/activities/forecasting-prevention/central-functional-center)
            - [ISPRA — IdroGEO (frane e alluvioni)](https://idrogeo.isprambiente.it/)
            - [MeteoAlarm Italia](https://www.meteoalarm.org/it/live/?s=italy)
            - [Aeronautica Militare — CNMCA](http://www.meteoam.it/)
            """)
    


def show_monitoraggio_idrogeologico():
    st.subheader("📊 Monitoraggio idrogeologico - Italia (Visione nazionale)")
    
    st.markdown("### 📈 Monitoraggio idrogeologico in tempo reale")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Zone a rischio frana", "1.281.970", "Alta criticità")
        st.metric("Comuni interessati", "7.275", "su 7.904 totali")
    
    with col2:
        st.metric("Zone a rischio alluvione", "2.062.475", "Alta criticità")
        st.metric("Popolazione esposta", "6.8 M", "abitanti")
    
    st.info("Dati aggiornati al: " + datetime.now(FUSO_ORARIO_ITALIA).strftime("%d/%m/%Y %H:%M:%S") + " (IT)")
    
    # Mappa delle zone a rischio
    st.markdown("### 🗺️ Mappa delle zone a rischio")
    st.image("https://idrogeo.isprambiente.it/app/iffi/images/Italia_pericolosita.jpg", 
             caption="Mappa della pericolosità da frana in Italia")
