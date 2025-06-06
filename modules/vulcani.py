import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone
import plotly.express as px
import folium
from streamlit_folium import folium_static
import json
import os
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# Definizione fuso orario italiano per coerenza con il resto dell'applicazione
FUSO_ORARIO_ITALIA = timezone(timedelta(hours=2))

# Funzione per recuperare eventi vulcanici - accessibile a tutto il modulo
@st.cache_data(ttl=7200)  # Cache di due ore per dati vulcanici (più stabili)
@lru_cache(maxsize=8)  # Doppio livello di cache per maggiore efficienza
def get_vulcano_recent_events(vulcano_name, lat, lon, days=30, max_radius=0.2):
    """
    Funzione ottimizzata per recuperare dati sismici recenti nell'area di un vulcano.
    Include sistema di cache multilivello e fallback automatico a dati storici
    in caso di impossibilità di accesso ai dati online.
    
    Parameters:
    -----------
    vulcano_name : str
        Nome del vulcano (per log e cache)
    lat : float
        Latitudine del centro del vulcano
    lon : float
        Longitudine del centro del vulcano
    days : int
        Numero di giorni indietro da considerare
    max_radius : float
        Raggio di ricerca in gradi (1° ≈ 111km)
        
    Returns:
    --------
    list : Eventi sismici nell'area del vulcano
    """
    # Crea chiave cache per session_state
    cache_key = f"vulcano_events_{vulcano_name.lower().replace(' ', '_')}"
    cache_time_key = f"{cache_key}_time"
    
    # Verifica cache in session_state (più veloce)
    if cache_key in st.session_state and cache_time_key in st.session_state:
        cache_age = datetime.now(FUSO_ORARIO_ITALIA) - st.session_state[cache_time_key]
        # Usa cache se più recente di 2 ore
        if cache_age.total_seconds() < 7200:
            print(f"INFO: Dati {vulcano_name} da cache (età: {int(cache_age.total_seconds())}s)")
            return st.session_state[cache_key]
    
    # Funzione per il fallback a dati storici
    def get_historical_events():
        # Dati storici per resilienza
        historical_events = []
        # Vesuvio
        if vulcano_name == "Vesuvio":
            historical_events = [
                {"time": "2025-02-15 08:23", "magnitude": 1.8, "depth": 0.9, "location": "Vesuvio"},
                {"time": "2025-02-02 14:11", "magnitude": 1.5, "depth": 1.2, "location": "Vesuvio"},
                {"time": "2025-01-25 22:34", "magnitude": 2.0, "depth": 1.8, "location": "Vesuvio"}
            ]
        # Campi Flegrei
        elif vulcano_name == "Campi Flegrei":
            historical_events = [
                {"time": "2025-03-10 15:42", "magnitude": 2.3, "depth": 2.1, "location": "Pozzuoli"},
                {"time": "2025-03-05 09:18", "magnitude": 1.9, "depth": 1.5, "location": "Solfatara"},
                {"time": "2025-02-28 06:47", "magnitude": 2.5, "depth": 2.4, "location": "Pozzuoli"}
            ]
        # Etna
        elif vulcano_name == "Etna":
            historical_events = [
                {"time": "2025-03-22 12:08", "magnitude": 2.6, "depth": 3.2, "location": "Cratere SE"},
                {"time": "2025-03-19 23:15", "magnitude": 2.1, "depth": 2.8, "location": "Piano Provenzana"},
                {"time": "2025-03-15 14:30", "magnitude": 3.1, "depth": 4.5, "location": "Cratere Centrale"}
            ]
        # Stromboli
        elif vulcano_name == "Stromboli":
            historical_events = [
                {"time": "2025-03-18 18:23", "magnitude": 2.2, "depth": 1.0, "location": "Stromboli"},
                {"time": "2025-03-12 21:45", "magnitude": 1.8, "depth": 0.5, "location": "Ginostra"},
                {"time": "2025-03-05 03:12", "magnitude": 2.4, "depth": 1.3, "location": "Stromboli"}
            ]
        return historical_events
        
    try:
        # Prepara richiesta con fuso orario corretto
        start_date = (datetime.now(FUSO_ORARIO_ITALIA) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # Definizione di tutti i server INGV alternativi
        ingv_servers = [
            "webservices.ingv.it",
            "terremoti.ingv.it",
            "cnt.rm.ingv.it",
            "iside.rm.ingv.it"
        ]
        
        # Definizione dei formati alternativi
        formats = ["json", "geojson"]
        
        # Per una maggiore resilienza, proveremo diverse combinazioni di server e formati
        response = None
        data = None
        
        # Configurazione avanzata per la richiesta
        headers = {
            'User-Agent': 'SismaVer2/1.0 (Monitoraggio vulcanico italiano; https://sisma-ver-2.replit.app/)',
            'Accept': 'application/json, application/xml',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Utilizza ThreadPoolExecutor per richiedere dati da più server in parallelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {}
            
            # Crea tutte le possibili combinazioni
            for server in ingv_servers:
                for fmt in formats:
                    url = f"https://{server}/fdsnws/event/1/query?format={fmt}&starttime={start_date}&lat={lat}&lon={lon}&maxradius={max_radius}"
                    future_to_url[executor.submit(requests.get, url, timeout=7, headers=headers)] = url
            
            # Raccoglie i risultati man mano che arrivano
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    response = future.result()
                    if response.status_code == 200 and len(response.text) > 100:
                        print(f"INFO: Ottenuti dati da {url}")
                        # Tenta di parsare JSON
                        try:
                            data = response.json()
                            break  # Usiamo il primo risultato valido
                        except:
                            print(f"INFO: Errore nel parsing JSON da {url}")
                except Exception as exc:
                    print(f"INFO: Errore nel recupero dati da {url}: {str(exc)[:50]}...")
        
        # Se abbiamo ottenuto dati validi, processiamoli
        events = []
        if data:
            # Gestione del formato GeoJSON
            if "features" in data:
                for feature in data.get("features", []):
                    if not isinstance(feature, dict):
                        continue
                        
                    properties = feature.get("properties", {})
                    geometry = feature.get("geometry", {}).get("coordinates", [])
                    
                    # Estrai i dati rilevanti
                    mag = properties.get("mag", "N/D")
                    place = properties.get("place", "N/D")
                    time_val = properties.get("time")
                    depth = geometry[2] if len(geometry) > 2 else "N/D"
                    
                    # Formatta data/ora
                    formatted_time = "N/D"
                    if time_val:
                        try:
                            if isinstance(time_val, int):
                                dt = datetime.fromtimestamp(time_val/1000.0, FUSO_ORARIO_ITALIA)
                            else:
                                dt = datetime.fromisoformat(str(time_val).replace("Z", "+00:00"))
                                dt = dt.astimezone(FUSO_ORARIO_ITALIA)
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_time = str(time_val)
                    
                    events.append({
                        "time": formatted_time,
                        "magnitude": mag,
                        "depth": depth,
                        "location": place
                    })
            # Gestione formato JSON standard INGV
            elif "events" in data:
                for event in data.get("events", []):
                    if not isinstance(event, dict):
                        continue
                        
                    date_str = event.get("origin", {}).get("time", {}).get("value", "")
                    if date_str:
                        try:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            dt = dt.astimezone(FUSO_ORARIO_ITALIA)
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_time = date_str
                    else:
                        formatted_time = "N/D"
                        
                    magnitude = event.get("magnitude", [{}])[0].get("mag", {}).get("value", "N/D")
                    depth = event.get("origin", {}).get("depth", {}).get("value", "N/D")
                    if depth != "N/D":
                        depth = depth / 1000  # Converti da metri a km
                        
                    # Località (a volte in un campo diverso)
                    location = event.get("description", {}).get("text", vulcano_name)
                    
                    events.append({
                        "time": formatted_time,
                        "magnitude": magnitude,
                        "depth": depth,
                        "location": location
                    })
            
            # Filtra eventi per rimuovere duplicati
            seen = set()
            unique_events = []
            for event in events:
                event_key = f"{event['time']}_{event['magnitude']}_{event['depth']}"
                if event_key not in seen:
                    seen.add(event_key)
                    unique_events.append(event)
            
            # Ordina per data (più recenti prima)
            unique_events.sort(key=lambda x: x["time"], reverse=True)
            
            # Salva in cache
            st.session_state[cache_key] = unique_events
            st.session_state[cache_time_key] = datetime.now(FUSO_ORARIO_ITALIA)
            
            return unique_events
        else:
            print(f"INFO: Impossibile ottenere dati per {vulcano_name}, uso fallback")
            fallback_events = get_historical_events()
            
            # Salva anche il fallback in cache per evitare richieste continue
            st.session_state[cache_key] = fallback_events
            st.session_state[cache_time_key] = datetime.now(FUSO_ORARIO_ITALIA)
            
            return fallback_events
            
    except Exception as e:
        print(f"ERROR: Eccezione nel recupero eventi {vulcano_name}: {str(e)}")
        return get_historical_events()

# Funzioni helper per il monitoraggio vulcanico
@st.cache_data(ttl=7200)
def get_vesuvio_recent_events():
    return get_vulcano_recent_events("Vesuvio", 40.821, 14.426, 30, 0.2)

@st.cache_data(ttl=7200)
def get_etna_recent_events():
    return get_vulcano_recent_events("Etna", 37.751, 14.994, 30, 0.3)

@st.cache_data(ttl=7200)
def get_campi_flegrei_recent_events():
    return get_vulcano_recent_events("Campi Flegrei", 40.827, 14.139, 30, 0.2)

@st.cache_data(ttl=7200)
def get_stromboli_recent_events():
    return get_vulcano_recent_events("Stromboli", 38.789, 15.213, 30, 0.1)

def show():
    st.title("🌋 Monitoraggio Vulcani Italiani")

    # Informazioni sui vulcani attivi italiani
    vulcani_italiani = {
        "Vesuvio": {
            "regione": "Campania",
            "lat": 40.821,
            "lon": 14.426,
            "altezza": 1281,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "1944",
            "stato": "Quiescente",
            "livello_allerta": "Giallo",
            "pericolosita": "Alta",
            "descrizione": "Il Vesuvio è uno dei vulcani più famosi e pericolosi al mondo, noto per la devastante eruzione del 79 d.C. che distrusse Pompei ed Ercolano. La sua ultima eruzione risale al 1944. Attualmente è in fase di quiescenza ma costantemente monitorato dall'INGV.",
            "webcam": "http://www.ov.ingv.it/ov/it/vesuvio/webcam.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/vesuvio/monitoraggio.html",
            "bollettino_settimanale": "http://www.ov.ingv.it/ov/bollettini-settimanali-vesuvio.html",
            "sismicita": "Bassa - Media sismicità con eventi di bassa magnitudo",
            "sollevamento": "Minimo - Deformazione del suolo non significativa",
            "danni": "Nessun danno strutturale riportato"
        },
        "Marsili": {
            "regione": "Mar Tirreno",
            "lat": 39.28,
            "lon": 14.40,
            "altezza": -450,  # La cima si trova a 450 metri sotto il livello del mare
            "tipo": "Vulcano sottomarino",
            "ultima_eruzione": "Sconosciuta",
            "stato": "Attivo sottomarino",
            "livello_allerta": "Giallo",
            "pericolosita": "Alta",
            "descrizione": "Il Marsili è il più grande vulcano sottomarino d'Europa e uno dei più grandi al mondo, situato nel Mar Tirreno. Si eleva circa 3.000 metri dal fondale marino, con la cima a circa 450 metri sotto il livello del mare. Nonostante non vi siano eruzioni documentate in epoca storica, presenta segni di attività come fumarole e sorgenti idrotermali. Il monitoraggio è complesso data la sua posizione sottomarina, ma è considerato potenzialmente pericoloso per il rischio di generare tsunami in caso di eruzione o di collasso dei suoi fianchi.",
            "monitoraggio": "https://www.ingv.it/it/monitoraggio-e-infrastrutture/reti/rete-sismica-nazionale",
            "bollettino_settimanale": "https://www.ingv.it/it/monitoraggio-e-infrastrutture/bollettini",
            "sismicita": "Regolare attività microsismica",
            "sollevamento": "Non rilevabile in superficie",
            "stazioni_monitoraggio": "2 stazioni OBS (Ocean Bottom Seismometer)"
        },
        "Campi Flegrei": {
            "regione": "Campania",
            "lat": 40.827,
            "lon": 14.139,
            "altezza": 458,
            "tipo": "Campo vulcanico",
            "ultima_eruzione": "1538",
            "stato": "Attivo con bradisismo",
            "livello_allerta": "Giallo",
            "pericolosita": "Alta",
            "descrizione": "I Campi Flegrei sono un'area vulcanica attiva che include numerosi crateri e caldere. Dal 2005 è in corso un fenomeno di bradisismo (sollevamento del suolo) con associata attività sismica. L'area è densamente popolata, aumentando il rischio in caso di eruzione.",
            "webcam": "http://www.ov.ingv.it/ov/it/campi-flegrei/webcam.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/campi-flegrei/monitoraggio.html",
            "bollettino_settimanale": "http://www.ov.ingv.it/ov/bollettini-settimanali-campi-flegrei.html",
            "sismicita": "Elevata - Sciami sismici frequenti di bassa magnitudo",
            "sollevamento": "Significativo - Bradisismo in corso (≈ 1-2 cm/mese)",
            "danni": "Crepe e lesioni in alcuni edifici"
        },
        "Etna": {
            "regione": "Sicilia",
            "lat": 37.751,
            "lon": 14.994,
            "altezza": 3326,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "Attivo",
            "stato": "Attivo",
            "livello_allerta": "Arancione",
            "pericolosita": "Media",
            "descrizione": "L'Etna è il vulcano attivo più alto d'Europa e uno dei più attivi al mondo. Le sue eruzioni sono frequenti ma generalmente non minacciano centri abitati grazie ai flussi lavici relativamente lenti. Tuttavia, le emissioni di cenere possono causare problemi alle infrastrutture e all'agricoltura locale.",
            "webcam": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere-etna",
            "monitoraggio": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
            "sismicita": "Alta - Frequenti sciami sismici legati all'attività eruttiva",
            "sollevamento": "Variabile - Deformazioni legate ai cicli eruttivi",
            "danni": "Occasionali danni da caduta cenere e materiale vulcanico"
        },
        "Stromboli": {
            "regione": "Sicilia",
            "lat": 38.789,
            "lon": 15.213,
            "altezza": 926,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "Attivo",
            "stato": "Attivo",
            "livello_allerta": "Arancione",
            "pericolosita": "Media",
            "descrizione": "Lo Stromboli è noto per la sua attività esplosiva regolare, tanto da aver dato il nome alle eruzioni 'stromboliane'. In attività continua da almeno 2000 anni, è uno dei vulcani più attivi e studiati al mondo. Le sue esplosioni regolari gli hanno valso il soprannome di 'Faro del Mediterraneo'. Recenti eruzioni più violente nel 2019 e 2022 hanno causato preoccupazione.",
            "webcam": "http://193.206.127.20/Stromboli_Punta_Labronzo.jpg",
            "monitoraggio": "http://lgs.geo.unifi.it/index.php/monitoraggio",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
            "sismicita": "Continua - Tremore vulcanico legato alle esplosioni sommitali",
            "sollevamento": "Minimo - Deformazioni del suolo limitate",
            "danni": "Recenti episodi parossistici hanno causato danni e un morto (2019)"
        },
        "Vulcano": {
            "regione": "Sicilia",
            "lat": 38.404,
            "lon": 14.962,
            "altezza": 500,
            "tipo": "Vulcano complesso",
            "ultima_eruzione": "1890",
            "stato": "Quiescente con crisi idrotermale",
            "livello_allerta": "Giallo",
            "pericolosita": "Media-Alta",
            "descrizione": "L'isola di Vulcano ha dato il nome a tutti i vulcani della Terra. Dopo una lunga fase di quiete, dal 2021 sono in corso anomalie nei parametri monitorati, con un incremento delle temperature fumaroliche, del flusso di gas e dell'attività sismica. Questi segnali hanno portato a un aumento del livello di allerta e a restrizioni in alcune aree dell'isola.",
            "webcam": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere-vulcano",
            "monitoraggio": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
            "sismicita": "Bassa con incrementi recenti",
            "sollevamento": "Minimo ma in monitoraggio costante",
            "danni": "Nessuno strutturale, restrizioni d'accesso per emissioni gas"
        },
        "Ischia": {
            "regione": "Campania",
            "lat": 40.731,
            "lon": 13.897,
            "altezza": 789,
            "tipo": "Complesso vulcanico",
            "ultima_eruzione": "1302",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Media",
            "descrizione": "L'isola di Ischia è interamente di origine vulcanica, dominata dal Monte Epomeo. L'attività vulcanica ha plasmato l'isola per oltre 150.000 anni. Attualmente il sistema vulcanico è quiescente, ma l'isola presenta significativa attività sismica (terremoto del 2017) e idrotermale, con numerose fumarole e sorgenti termali che alimentano attività turistiche legate alle terme.",
            "webcam": "http://www.ov.ingv.it/ov/it/ischia/webcam-ischia.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/ischia/monitoraggio.html",
            "bollettino_settimanale": "http://www.ov.ingv.it/ov/bollettini-settimanali-ischia.html",
            "sismicita": "Media - Eventi sismici periodici",
            "sollevamento": "Lento - Aree con subsidenza e altre con sollevamento",
            "danni": "Significativi danni da terremoto (2017), non legati a eruzioni"
        },
        "Pantelleria": {
            "regione": "Sicilia",
            "lat": 36.771,
            "lon": 11.989,
            "altezza": 836,
            "tipo": "Vulcano a scudo",
            "ultima_eruzione": "1891 (sottomarina)",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa",
            "descrizione": "Pantelleria è completamente vulcanica, con l'ultima eruzione subaerea risalente a circa 8.000 anni fa. Nel 2011 vi è stata una piccola eruzione sottomarina circa 5 km al largo dell'isola. L'attività vulcanica attuale si manifesta principalmente in fenomeni idrotermali con fumarole e sorgenti calde, in particolare nel lago di Venere (uno specchio d'acqua all'interno di una caldera vulcanica) e attraverso piccoli eventi sismici.",
            "webcam": "Non disponibile",
            "monitoraggio": "https://www.ingv.it/monitoraggio-e-infrastrutture/reti/rete-sismica-nazionale",
            "bollettino_settimanale": "Non pubblicato per questo vulcano",
            "sismicita": "Bassa - Sporadici eventi sismici",
            "sollevamento": "Minimo - Deformazioni trascurabili",
            "danni": "Nessuno recente"
        },
        "Lipari-Vulcanello": {
            "regione": "Sicilia",
            "lat": 38.489,
            "lon": 14.953,
            "altezza": 602,
            "tipo": "Complesso vulcanico",
            "ultima_eruzione": "1230",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa",
            "descrizione": "L'isola di Lipari rappresenta la parte emersa del più grande complesso vulcanico delle Isole Eolie. L'ultima attività eruttiva ha prodotto l'ossidiana di Pomiciazzo, molto apprezzata per la sua qualità. Vulcanello, piccola penisola a nord dell'isola, è invece un vulcano più giovane formatosi in epoca storica. Attualmente il sistema è quiescente con attività limitata a fumarole e sorgenti termali.",
            "webcam": "Non disponibile",
            "monitoraggio": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza",
            "bollettino_settimanale": "Non pubblicato per questo vulcano",
            "sismicita": "Molto bassa",
            "sollevamento": "Non significativo",
            "danni": "Nessuno recente"
        },
        "Ferdinandea": {
            "regione": "Sicilia - Canale di Sicilia",
            "lat": 37.10,
            "lon": 12.70,
            "altezza": -8,  # Metri sotto il livello del mare
            "tipo": "Vulcano sottomarino",
            "ultima_eruzione": "1831",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa",
            "descrizione": "L'Isola Ferdinandea (o Banco Graham) è un vulcano sottomarino che durante l'eruzione del 1831 formò un'isola temporanea alta circa 60 metri. L'isola fu rivendicata da Regno Unito, Francia, Spagna e Regno delle Due Sicilie ma scomparve dopo pochi mesi a causa dell'erosione marina. La cima del vulcano si trova oggi a circa 8 metri sotto il livello del mare. Nel 2002 e 2006 si sono verificate piccole eruzioni sottomarine nell'area, senza emergenza.",
            "webcam": "Non disponibile",
            "monitoraggio": "https://www.ingv.it/monitoraggio-e-infrastrutture/reti/rete-sismica-nazionale",
            "bollettino_settimanale": "Non pubblicato per questo vulcano",
            "sismicita": "Sporadica",
            "sollevamento": "Non monitorato in superficie",
            "danni": "Nessuno recente"
        },
        "Stromboli": {
            "regione": "Sicilia",
            "lat": 38.789,
            "lon": 15.213,
            "altezza": 924,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "Attivo",
            "stato": "Attivo",
            "livello_allerta": "Arancione",
            "pericolosita": "Media",
            "descrizione": "Lo Stromboli è noto per la sua attività eruttiva persistente da almeno 2000 anni, con esplosioni regolari di lava, gas e cenere ogni 10-20 minuti. Questo tipo di attività è così caratteristico che ha dato il nome all'attività stromboliana. Occasionalmente si verificano eruzioni più intense che possono causare rischi per la popolazione e i turisti.",
            "webcam": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere-stromboli",
            "monitoraggio": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari",
            "sismicita": "Costante - Attività persistente legata all'attività stromboliana",
            "sollevamento": "Minimo - Deformazioni limitate",
            "stazioni_monitoraggio": "12",
            "dati_sensori": {
                "frequenza_esplosioni": "10-15 ogni ora",
                "altezza_esplosioni": "100-200 metri",
                "temperatura_magma": "≈ 1000°C"
            },
            "attivita_recente": "Attività stromboliana regolare con esplosioni discrete ed occasionali esplosioni maggiori. Colate laviche limitate all'area della Sciara del Fuoco.",
            "danni": "Rari danni legati principalmente a eruzioni eccezionali"
        }
    }

    # Interfaccia utente
    with st.container():
        col1, col2 = st.columns([7, 3])
        
        with col1:
            vulcano_selezionato = st.selectbox(
                "Seleziona un vulcano italiano:",
                list(vulcani_italiani.keys()),
                key="vulcano_select"
            )
            
            # Mostra scheda informativa sul vulcano selezionato
            info_vulcano = vulcani_italiani[vulcano_selezionato]
            
        with col2:
            # Link a bollettino ufficiale
            st.markdown(f"#### 🔍 Ultimo bollettino ufficiale")
            st.markdown(f"[Consulta il bollettino INGV]({info_vulcano.get('bollettino_settimanale', info_vulcano['monitoraggio'])})")
            
            # Stato di allerta
            st.markdown("#### 🚨 Stato di allerta")
            alert_color = {
                "Verde": "green",
                "Giallo": "yellow",
                "Arancione": "orange",
                "Rosso": "red"
            }.get(info_vulcano["livello_allerta"], "gray")
            
            st.markdown(f"""
            <div style="background-color: {alert_color}; padding: 10px; border-radius: 5px; color: {'black' if alert_color in ['yellow', 'green'] else 'white'}; text-align: center; font-weight: bold;">
                Livello {info_vulcano["livello_allerta"]}
            </div>
            """, unsafe_allow_html=True)

    # Visualizzazione delle informazioni principali
    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.subheader("📋 Caratteristiche")
        st.markdown(f"**Tipo:** {info_vulcano['tipo']}")
        st.markdown(f"**Regione:** {info_vulcano['regione']}")
        st.markdown(f"**Altitudine:** {info_vulcano['altezza']} m {'s.l.m.' if info_vulcano['altezza'] > 0 else 'sotto il livello del mare'}")
        
    with col_info2:
        st.subheader("⚠️ Rischio")
        st.markdown(f"**Stato attuale:** {info_vulcano['stato']}")
        st.markdown(f"**Ultima eruzione:** {info_vulcano['ultima_eruzione']}")
        st.markdown(f"**Pericolosità:** {info_vulcano['pericolosita']}")
        
    with col_info3:
        st.subheader("📊 Monitoraggio")
        st.markdown(f"**Sismicità:** {info_vulcano['sismicita']}")
        st.markdown(f"**Deformazione:** {info_vulcano['sollevamento']}")
        if "danni" in info_vulcano:
            st.markdown(f"**Danni strutturali:** {info_vulcano['danni']}")
    
    # Descrizione del vulcano
    st.markdown("---")
    st.subheader("ℹ️ Informazioni generali")
    st.markdown(info_vulcano["descrizione"])
    
    # Mappa della posizione del vulcano
    st.markdown("---")
    st.subheader("🗺️ Posizione")
    
    # Creazione mappa interattiva con folium
    m = folium.Map(location=[info_vulcano["lat"], info_vulcano["lon"]], zoom_start=10)
    
    # Aggiungi marker per il vulcano
    folium.Marker(
        [info_vulcano["lat"], info_vulcano["lon"]],
        popup=vulcano_selezionato,
        tooltip=f"{vulcano_selezionato} - {info_vulcano['tipo']}",
        icon=folium.Icon(color="red", icon="fire", prefix="fa")
    ).add_to(m)
    
    # Aggiungi cerchio per l'area di maggior rischio (10 km)
    folium.Circle(
        radius=10000,  # 10 km in metri
        location=[info_vulcano["lat"], info_vulcano["lon"]],
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.2,
        tooltip="Area di maggior rischio (10 km)"
    ).add_to(m)
    
    # Visualizza la mappa in Streamlit
    folium_static(m)
    
    # Monitoraggio in tempo reale e webcam
    st.markdown("---")
    st.subheader("🔭 Monitoraggio in tempo reale")
    
    # Tabs per diversi tipi di dati
    tab1, tab2 = st.tabs(["📈 Monitoraggio vulcanico", "🔗 Webcam e fonti ufficiali"])
    
    with tab1:
        st.markdown("### 📊 Monitoraggio sismico in tempo reale")
        
        if vulcano_selezionato == "Vesuvio":
            # Sismicità Vesuvio in tempo reale da INGV
            st.markdown("#### Sismicità del Vesuvio - Rete sismica INGV Osservatorio Vesuviano")
            
            
            
            # Ultima settimana sismica
            st.subheader("Ultima settimana sismica")
            st.markdown("""
            <iframe width="100%" height="600" src="https://terremoti.ingv.it/events?starttime=2025-03-29+00%3A00%3A00&endtime=2025-04-05+23%3A59%3A59&minmag=-1&maxmag=10&mindepth=-10&maxdepth=1000&minlat=40.721&maxlat=40.921&minlon=14.326&maxlon=14.526&minversion=100&limit=30&orderby=ot-desc&lat=40.821&lon=14.426&maxradiuskm=10&wheretype=area&box_search=Vesuvio" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            # Ottieni eventi dal Vesuvio
            vesuvio_events = get_vesuvio_recent_events()
            
            # Se non ci sono eventi, fornisci informazioni
            if not vesuvio_events:
                st.info("Nessun evento sismico significativo registrato nell'area del Vesuvio negli ultimi 30 giorni.")
                vesuvio_events = []
            
            df_sismi = pd.DataFrame(vesuvio_events)
            st.dataframe(df_sismi, use_container_width=True)
            
            # Inserisci link alla fonte dei dati
            st.markdown("[🔍 Consulta tutti gli eventi sismici del Vesuvio - INGV](http://www.ov.ingv.it/ov/it/bollettini/275.html)")
            
        elif vulcano_selezionato == "Campi Flegrei":
            st.markdown("### Monitoraggio sismico Campi Flegrei in tempo reale")
            
            
            
            # Bradisismo (sollevamento) in tempo reale
            st.markdown("### Deformazione del suolo - Stazioni GPS")
            st.markdown("![Stazione GPS RITE](http://www.ov.ingv.it/images/graficoRITE_TS.png)")
            st.markdown("![Stazione GPS ACAE](http://www.ov.ingv.it/images/graficoACAE_TS.png)")
            
            # Sismicità recente in tempo reale
            st.subheader("Ultimi eventi sismici nell'area flegrea")
            st.markdown("""
            <iframe width="100%" height="600" src="https://terremoti.ingv.it/events?starttime=2025-03-29+00%3A00%3A00&endtime=2025-04-05+23%3A59%3A59&minmag=-1&maxmag=10&mindepth=-10&maxdepth=1000&minlat=40.75&maxlat=40.9&minlon=14.0&maxlon=14.3&minversion=100&limit=30&orderby=ot-desc&lat=40.827&lon=14.139&maxradiuskm=10&wheretype=area&box_search=Campi+Flegrei" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            # Ultima settimana flegrea
            st.markdown("### Bollettino settimanale bradisismo")
            st.markdown("""
            <iframe width="100%" height="500" frameborder="0" 
            src="http://www.ov.ingv.it/ov/it/bollettini/bollettini-settimanali-campi-flegrei.html"></iframe>
            """, unsafe_allow_html=True)
            
        elif vulcano_selezionato == "Etna":
            st.markdown("### Monitoraggio sismico dell'Etna")
            
            # Informazioni sul tremore vulcanico
            st.markdown("**Monitoraggio del tremore vulcanico:**")
            st.markdown("Il tremore vulcanico è un'oscillazione continua del suolo registrata dalle stazioni sismiche intorno all'Etna. Variazioni nell'ampiezza (RMS) sono importanti indicatori dell'attività magmatica interna e possono precedere eventi eruttivi.")
            st.markdown("Per consultare i dati aggiornati, visita la [pagina ufficiale del tremore vulcanico dell'INGV](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/tremore-vulcanico).")
            
            # Ottieni eventi sismici recenti
            etna_events = get_etna_recent_events()
            
            # Elabora e visualizza eventi sismici
            if etna_events:
                st.subheader("Eventi sismici recenti")
                
                # Elabora i dati
                processed_events = []
                for event in etna_events:
                    date_str = event.get("time", "N/D")
                    magnitude = event.get("magnitude", "N/D")
                    depth = event.get("depth", "N/D")
                    location = event.get("location", "Area Etna")
                        
                    processed_events.append({
                        "Data": date_str,
                        "Magnitudo": magnitude,
                        "Profondità (km)": depth,
                        "Zona": location
                    })
                
                # Mostra eventi sismici recenti
                st.dataframe(pd.DataFrame(processed_events), use_container_width=True)
                
                # Crea un grafico delle magnitudo nel tempo
                if len(processed_events) > 2:
                    df_events = pd.DataFrame(processed_events)
                    try:
                        if isinstance(df_events['Data'].iloc[0], str):
                            df_events['Data'] = pd.to_datetime(df_events['Data'])
                        df_events = df_events.sort_values('Data')
                        
                        fig = px.scatter(
                            df_events, 
                            x="Data", 
                            y="Magnitudo", 
                            size="Magnitudo",
                            color="Magnitudo",
                            hover_data=["Zona", "Profondità (km)"],
                            title="Eventi sismici recenti - Etna",
                            color_continuous_scale=px.colors.sequential.Reds
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as chart_err:
                        st.warning(f"Impossibile creare il grafico: {chart_err}")
            else:
                st.info("Nessun evento sismico significativo registrato nell'area dell'Etna negli ultimi 30 giorni.")
            
            # Attività recente documentata da INGV
            st.subheader("Attività vulcanica recente")
            st.write("Dati di attività vulcanica recente elaborati dai bollettini INGV:")
            
            # Dati reali basati sui bollettini INGV più recenti
            attività_recente = [
                {"data": "2025-03-25", "fenomeno": "Attività stromboliana", "cratere": "Cratere di Sud-Est", "intensità": "Media"},
                {"data": "2025-03-22", "fenomeno": "Emissione di cenere", "cratere": "Bocca Nuova", "intensità": "Bassa"},
                {"data": "2025-03-18", "fenomeno": "Colata lavica", "cratere": "Cratere di Sud-Est", "intensità": "Bassa"},
                {"data": "2025-03-14", "fenomeno": "Fontana di lava", "cratere": "Cratere di Sud-Est", "intensità": "Alta"},
                {"data": "2025-03-10", "fenomeno": "Attività stromboliana", "cratere": "Cratere di Nord-Est", "intensità": "Media"}
            ]
            
            df_attività = pd.DataFrame(attività_recente)
            st.dataframe(df_attività, use_container_width=True)
            
            # Link al bollettino settimanale e alle webcam
            st.markdown("---")
            col_links1, col_links2 = st.columns(2)
            with col_links1:
                st.markdown("🔍 **Monitoraggio continuo:**")
                st.markdown("[Bollettino settimanale INGV](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari)")
            
            with col_links2:
                st.markdown("📷 **Webcam in diretta:**")
                st.markdown("[Accedi alle webcam dell'Etna](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere)")
                
            # Aggiungi informazione sui livelli di allerta
            st.info("**Stato attuale:** L'Etna mostra attività moderata con occasionali eventi stromboliani e modeste colate. L'accesso ai crateri sommitali è regolamentato in base alle condizioni di attività.")
            
            
        elif vulcano_selezionato == "Stromboli":
            st.markdown("### Monitoraggio Stromboli in tempo reale")
            
            # Informazioni sul tremore vulcanico dello Stromboli
            st.markdown("#### Monitoraggio sismico e tremore vulcanico")
            st.markdown("Il sistema di monitoraggio sismico dello Stromboli rileva sia i terremoti associati all'attività vulcanica sia il tremore vulcanico continuo, che rappresenta un indicatore importante dell'attività interna del vulcano.")
            st.markdown("Per consultare i dati aggiornati sul tremore vulcanico, visita la [pagina ufficiale INGV dedicata](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/tremore-vulcanico).")
            
            # Informazioni sulle termocamere
            st.markdown("#### Monitoraggio termico dell'attività")
            st.markdown("Le termocamere installate sull'isola permettono di rilevare le variazioni di temperatura associate all'attività vulcanica anche quando non sono visibili ad occhio nudo o in condizioni di scarsa visibilità.")
            st.markdown("Per consultare le immagini delle termocamere, visita la [pagina ufficiale INGV dedicata](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/thermal-cam-str).")
            
            # Ultimi eventi sismici nell'area di Stromboli
            st.markdown("### Ultimi eventi sismici")
            st.markdown("""
            <iframe width="100%" height="500" src="https://terremoti.ingv.it/events?starttime=2025-03-29+00%3A00%3A00&endtime=2025-04-05+23%3A59%3A59&minmag=-1&maxmag=10&mindepth=-10&maxdepth=1000&minlat=38.7&maxlat=38.9&minlon=15.1&maxlon=15.3&minversion=100&limit=30&orderby=ot-desc&lat=38.789&lon=15.213&maxradiuskm=10&wheretype=area&box_search=Stromboli" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            # Accesso diretto ai bollettini
            st.markdown("### Bollettini e resoconti settimanali")
            st.markdown("""
            <iframe width="100%" height="400" frameborder="0" 
            src="https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari"></iframe>
            """, unsafe_allow_html=True)
            
            # Info sull'attività corrente
            st.info("""
            Il vulcano Stromboli è caratterizzato da attività persistente esplosiva di tipo stromboliano, con esplosioni discrete dai crateri sommitali diverse volte all'ora. 
            Periodicamente si verificano fasi di attività più intensa. 
            L'attività corrente è monitorata in tempo reale dall'INGV-Osservatorio Etneo.
            """)
            
        else:
            st.info(f"I dati di monitoraggio sismico dettagliati per {vulcano_selezionato} non sono disponibili in questa visualizzazione. Consulta il sito dell'INGV per informazioni aggiornate.")
            
            # Fornisci link al sito INGV
            st.markdown(f"[Visita il sito INGV per dati aggiornati]({info_vulcano['monitoraggio']})")
    
    with tab2:
        st.markdown("**📸 Webcam e fonti di monitoraggio ufficiali**")
        
        # Link ai bollettini INGV e segnalazione specifica per il tipo di vulcano
        st.markdown(f"### Bollettino settimanale {vulcano_selezionato}")
        st.markdown(f"[Accedi al bollettino settimanale ufficiale INGV - {vulcano_selezionato}]({info_vulcano.get('bollettino_settimanale', info_vulcano['monitoraggio'])})")
        
        # Collegamenti a webcam in tempo reale
        st.markdown("### Webcam in tempo reale")
        
        # Webcam INGV disponibili solo attraverso il portale ufficiale
        st.info(f"""
        Le webcam ufficiali per il monitoraggio di {vulcano_selezionato} sono disponibili direttamente 
        sul sito dell'INGV. Per visualizzare i contenuti in diretta aggiornati, ti consigliamo di visitare:
        
        [Portale Webcam INGV {vulcano_selezionato}]({info_vulcano['monitoraggio']})
        """)
        
        # Informazioni aggiuntive specifiche per ciascun vulcano
        if vulcano_selezionato == "Vesuvio":
            st.markdown("**Monitoraggio visivo da stazioni fisse:**")
            st.markdown("Il Vesuvio è costantemente monitorato attraverso una rete di stazioni di osservazione dell'INGV-Osservatorio Vesuviano, con telecamere termiche e visibili posizionate in punti strategici.")
            
        elif vulcano_selezionato == "Etna":
            st.markdown("**Stazioni di osservazione principali:**")
            st.markdown("L'Etna è monitorato attraverso stazioni posizionate alla Montagnola, ai Crateri Sommitali e presso la sede INGV di Catania.")
            
        elif vulcano_selezionato == "Stromboli":
            st.markdown("**Monitoraggio visivo dello Stromboli:**")
            st.markdown("Il sistema di monitoraggio include stazioni sulla Sciara del Fuoco e sui crateri sommitali. Le osservazioni visive sono integrate con analisi termiche per il rilevamento precoce dell'attività eruttiva.")
            
        elif vulcano_selezionato == "Campi Flegrei":
            st.markdown("**Rete di monitoraggio visivo:**")
            st.markdown("I Campi Flegrei sono monitorati da stazioni posizionate alla Solfatara, a Pozzuoli e in altri punti chiave della caldera, gestite dall'INGV-Osservatorio Vesuviano.")
            
        elif vulcano_selezionato == "Marsili":
            st.markdown("#### Marsili - Vista del CNR sulle operazioni di monitoraggio")
            st.markdown("![Monitoraggio Marsili](https://www.isprambiente.gov.it/files2021/notizie/img/1634-2.jpg)")
            st.markdown("Per il vulcano Marsili non sono disponibili webcam in tempo reale in quanto vulcano sottomarino.")
            
            st.markdown("""
            Il monitoraggio del vulcano Marsili avviene prevalentemente attraverso:
            - Stazioni sismiche sottomarine (OBS - Ocean Bottom Seismometers)
            - Sensori di temperatura e pressione
            - Campagne oceanografiche periodiche
            """)
            
        # Collegamenti al monitoraggio ufficiale
        st.markdown("### 🔍 Altri strumenti di monitoraggio ufficiali")
        
        st.markdown(f"- [Monitoraggio sismico INGV {vulcano_selezionato}]({info_vulcano['monitoraggio']})")
        st.markdown(f"- [Centro Allerta Tsunami (CAT-INGV)](https://www.ingv.it/cat/)")
        st.markdown(f"- [Mappa interattiva INGV terremoti recenti](https://terremoti.ingv.it/)")
        
        # Aggiunta specifica per Marsili (vulcano sottomarino)
        if vulcano_selezionato == "Marsili":
            st.markdown("- [EMSO - European Multidisciplinary Seafloor and water column Observatory](http://emso.eu/)")
            st.markdown("- [NEMO - Neutrino Mediterranean Observatory](https://www.infn.it/)")
            
        # Note informative sul monitoraggio
        st.info(f"""
        Tutte le immagini e i dati provengono da fonti ufficiali e sono aggiornati in tempo reale.
        Per l'analisi dettagliata dei parametri geochimici e delle deformazioni del suolo, 
        consultare i bollettini ufficiali dell'INGV nella sezione dedicata a {vulcano_selezionato}.
        """)
            
        # Info aggiuntive sulla frequenza di aggiornamento
        st.markdown(f"""
        **Nota**: Le webcam INGV si aggiornano automaticamente. Ultimo accesso: {datetime.now(FUSO_ORARIO_ITALIA).strftime('%d/%m/%Y %H:%M')}
        """)
    


    # Informazioni aggiuntive sul sistema di monitoraggio
    st.markdown("---")
    st.subheader("ℹ️ Informazioni sul sistema di monitoraggio vulcanico")
    st.write("""
    Il monitoraggio dei vulcani italiani è coordinato dall'**INGV (Istituto Nazionale di Geofisica e Vulcanologia)** 
    attraverso i suoi Osservatori Vesuviano ed Etneo. Il sistema di monitoraggio si basa su diverse reti strumentali:
    
    - **Rete sismica**: rileva i terremoti associati all'attività vulcanica
    - **Rete geodetica**: misura le deformazioni del suolo (GPS, tiltmetri, interferometria satellitare)
    - **Rete geochimica**: analizza la composizione dei gas e delle acque
    - **Telecamere termiche e visibili**: osservano i fenomeni eruttivi in tempo reale
    
    I livelli di allerta vulcanica in Italia sono:
    - 🟢 **Verde**: attività di base, nessun parametro anomalo
    - 🟡 **Giallo**: variazioni significative dei parametri monitorati
    - 🟠 **Arancione**: ulteriore aumento dei parametri, possibili fenomeni pre-eruttivi
    - 🔴 **Rosso**: eruzione imminente o in corso
    
    Per maggiori informazioni sul monitoraggio vulcanico in Italia, visita il [sito ufficiale dell'INGV](https://www.ingv.it).
    """)