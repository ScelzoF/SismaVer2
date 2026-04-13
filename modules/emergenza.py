import streamlit as st
from modules.dati_regioni_b import dati_regioni_b
from modules.dati_regioni_c import dati_regioni_c
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import time

# Dizionario di coordinate precaricate per le principali città/regioni italiane
# per evitare chiamate API che potrebbero fallire
COORDINATES_CACHE = {
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
    "Veneto": [45.44, 12.32],
    # Principali città
    "Roma": [41.89, 12.48],
    "Milano": [45.47, 9.19],
    "Napoli": [40.83, 14.25],
    "Torino": [45.07, 7.68],
    "Palermo": [38.13, 13.34],
    "Genova": [44.41, 8.93],
    "Bologna": [44.49, 11.34],
    "Firenze": [43.77, 11.25],
    "Bari": [41.12, 16.87],
    "L'Aquila": [42.35, 13.40],
    "Perugia": [43.11, 12.39],
    "Trento": [46.07, 11.12],
    "Venezia": [45.44, 12.32],
    "Trieste": [45.65, 13.78],
    "Ancona": [43.62, 13.51],
    "Catanzaro": [38.91, 16.59],
    "Cagliari": [39.22, 9.10],
    "Potenza": [40.64, 15.80],
    "Campobasso": [41.56, 14.65]
}

# Utilizziamo cache_data per ottimizzare la geolocalizzazione
@st.cache_data(ttl=86400, show_spinner=False)  # Cache valida per 24 ore
def geocode_location(location_name):
    """
    Geocodifica le coordinate di una località con sistema di cache avanzato e fallback.
    Prima controlla nella cache interna poi usa Nominatim (OpenStreetMap) come geocoder.
    """
    # Step 1: Verifica se abbiamo la località nella nostra cache statica precaricata
    for key in COORDINATES_CACHE:
        if key.lower() in location_name.lower():
            # Ritorna le coordinate dalla cache statica
            return COORDINATES_CACHE[key][0], COORDINATES_CACHE[key][1]
    
    # Step 2: Estrai nome regione/città principale dal testo
    # Ad esempio da "Roma: Piazza del Popolo" estrae "Roma"
    main_location = location_name.split(':')[0].strip() if ':' in location_name else location_name
    
    # Verifica se il nome principale è nella cache
    if main_location in COORDINATES_CACHE:
        return COORDINATES_CACHE[main_location][0], COORDINATES_CACHE[main_location][1]
    
    # Step 3: Solo se non abbiamo trovato nulla in cache, proviamo con API esterna
    try:
        # Verifica connettività prima di procedere
        import socket
        try:
            # Test rapido di connettività a internet
            socket.create_connection(("www.google.com", 80), timeout=3)
            online = True
        except OSError:
            online = False
            
        if not online:
            # Se non c'è connessione, ritorna coordinate Italia di default
            return 41.9, 12.5
            
        # Aggiungiamo un suffisso ", Italia" per migliorare precisione localizzazione
        if not location_name.lower().endswith("italia"):
            search_name = f"{location_name}, Italia"
        else:
            search_name = location_name
            
        # Utilizzo di Nominatim (OpenStreetMap) con timeout e user-agent personalizzati
        geolocator = Nominatim(user_agent="sismaVer2-app", timeout=5)
        location = geolocator.geocode(search_name)
        
        if location:
            return location.latitude, location.longitude
        else:
            # Fallback a coordinate di default per l'Italia
            return 41.9, 12.5
    except Exception as e:
        print(f"Errore geocoding per {location_name}: {e}")
        # Coordinate di default per l'Italia in caso di errore
        return 41.9, 12.5

def show():
    st.title("🚨 Emergenza Regionale")
    st.write("Informazioni di emergenza, punti di raccolta e contatti utili per ciascuna regione italiana.")

    # Dati regioni di base con coordinates precaricate per ridurre chiamate API
    # Includendo anche coordinate precise per ogni punto di raccolta
    dati_regioni = {
        "Abruzzo": {
            "criticita": "Elevato rischio sismico in tutta la regione. Significativo rischio idrogeologico nelle aree montane e nei bacini fluviali.",
            "punti_raccolta": [
                "L'Aquila: Piazza Duomo, Villa Comunale",
                "Pescara: Piazza Italia, Parco D'Avalos",
                "Chieti: Piazza G.B. Vico, Villa Comunale",
                "Teramo: Piazza Martiri della Libertà, Parco della Scienza",
                "Avezzano: Piazza Risorgimento, Parco Torlonia"
            ],
            "punti_raccolta_coords": {
                "L'Aquila: Piazza Duomo, Villa Comunale": [42.3498, 13.3995],
                "Pescara: Piazza Italia, Parco D'Avalos": [42.4617, 14.2150],
                "Chieti: Piazza G.B. Vico, Villa Comunale": [42.3517, 14.1681],
                "Teramo: Piazza Martiri della Libertà, Parco della Scienza": [42.6589, 13.7044],
                "Avezzano: Piazza Risorgimento, Parco Torlonia": [42.0311, 13.4261]
            },
            "link_utili": {
                "Protezione Civile Abruzzo": "https://protezionecivile.regione.abruzzo.it/"
            },
            "coordinates": [42.35, 13.40]  # Coordinate precaricate per Abruzzo
        },
        "Liguria": {
            "criticita": "Rischio idrogeologico molto elevato nelle aree costiere e collinari.",
            "punti_raccolta": [
                "Genova: Piazza De Ferrari",
                "La Spezia: Piazza Europa",
                "Savona: Piazza Mameli",
                "Imperia: Piazza Dante"
            ],
            "punti_raccolta_coords": {
                "Genova: Piazza De Ferrari": [44.4077, 8.9337],
                "La Spezia: Piazza Europa": [44.1026, 9.8263],
                "Savona: Piazza Mameli": [44.3079, 8.4774],
                "Imperia: Piazza Dante": [43.8840, 8.0278]
            },
            "link_utili": {
                "Protezione Civile Liguria": "https://protezionecivile.regione.liguria.it/"
            },
            "coordinates": [44.41, 8.93]  # Coordinate precaricate per Liguria
        },
        "Lazio": {
            "criticita": "Rischio sismico significativo nelle zone interne.",
            "punti_raccolta": [
                "Roma: Piazza del Popolo",
                "Latina: Piazza del Popolo",
                "Frosinone: Piazza della Libertà",
                "Rieti: Piazza Vittorio Emanuele II",
                "Viterbo: Piazza del Plebiscito"
            ],
            "punti_raccolta_coords": {
                "Roma: Piazza del Popolo": [41.9106, 12.4756],
                "Latina: Piazza del Popolo": [41.4667, 12.9039],
                "Frosinone: Piazza della Libertà": [41.6400, 13.3425],
                "Rieti: Piazza Vittorio Emanuele II": [42.4037, 12.8563],
                "Viterbo: Piazza del Plebiscito": [42.4168, 12.1054]
            },
            "link_utili": {
                "Protezione Civile Lazio": "https://www.regione.lazio.it/protezionecivile"
            },
            "coordinates": [41.89, 12.48]  # Coordinate precaricate per Lazio
        }
    }

    # Aggiorna il dizionario dati_regioni con i dati esterni
    dati_regioni.update(dati_regioni_b)
    dati_regioni.update(dati_regioni_c)
    
    # Selezione tipo emergenza con contenuti specifici per ogni tipo
    tipo_emergenza = st.radio(
        "Seleziona il tipo di emergenza:",
        ["Tutte le emergenze", "Terremoto", "Alluvione", "Incendio"],
        horizontal=True,
        key="tipo_emergenza_radio"
    )

    # Contenuti specifici in base al tipo di emergenza selezionato
    if tipo_emergenza == "Terremoto":
        st.markdown("## 🌋 Cosa fare in caso di terremoto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚠️ Cosa fare PRIMA")
            st.markdown("""
            1. **Informati sulla classificazione sismica** del tuo comune
            2. **Verifica la vulnerabilità della tua abitazione** e rinforza parti strutturali
            3. **Prepara un kit di emergenza**: acqua, cibo non deperibile, torcia, radio a pile, medicinali
            4. **Individua i punti sicuri** dell'abitazione: muri portanti, travi, architravi
            5. **Conosci i percorsi di evacuazione** e il piano di emergenza comunale
            6. **Memorizza e tieni a portata di mano** i numeri di emergenza
            """)
            
            st.markdown("### ⚠️ Cosa fare DURANTE")
            st.markdown("""
            1. **Mantieni la calma** e resta dove sei fino al termine della scossa
            2. **Riparati sotto un tavolo robusto** o nel vano di una porta inserita in un muro portante
            3. **Allontanati da finestre, vetri, mobili pesanti**, lampadari e oggetti che potrebbero cadere
            4. **Non precipitarti fuori dalle scale** e non usare l'ascensore
            5. **Se sei all'aperto**, allontanati da edifici, alberi, lampioni, linee elettriche
            6. **In auto**, rallenta e fermati in spazi aperti, evitando ponti e cavalcavia
            """)
        
        with col2:
            st.markdown("### ⚠️ Cosa fare DOPO")
            st.markdown("""
            1. **Assicurati dello stato di salute** di chi ti è vicino, senza spostare feriti gravi
            2. **Esci con prudenza**, indossando scarpe per proteggerti da vetri rotti
            3. **Raggiungi gli spazi aperti** e i punti di raccolta indicati dal tuo comune
            4. **Evita di usare il telefono** se non per reali emergenze
            5. **Limita l'uso dell'auto** per non intralciare i mezzi di soccorso
            6. **Tieni radio o TV accese** per seguire gli aggiornamenti e le istruzioni
            7. **Evita di rientrare nell'abitazione** senza autorizzazione (rischio crolli)
            """)
            
            st.markdown("### ❌ Errori da evitare")
            st.markdown("""
            1. **NON utilizzare gli ascensori**
            2. **NON stare vicino a finestre o balconi**
            3. **NON affollare le linee telefoniche**
            4. **NON correre in modo disordinato** verso le uscite
            5. **NON usare fiamme libere** (rischio fughe di gas)
            6. **NON rientrare nelle abitazioni danneggiate** senza autorizzazione
            """)
        
        st.warning("Per informazioni più dettagliate, consulta il sito della [Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-sismico/cosa-fare)")
        
    elif tipo_emergenza == "Alluvione":
        st.markdown("## 🌊 Cosa fare in caso di alluvione")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚠️ Cosa fare PRIMA")
            st.markdown("""
            1. **Informati se la tua zona è a rischio** alluvionale
            2. **Sappi se nel tuo Comune è operativo un piano** di emergenza
            3. **Assicurati che la scuola o il luogo di lavoro ricevano le allerte**
            4. **Evita di conservare beni di valore in cantina o al piano seminterrato**
            5. **Assicurati che in caso di necessità sia possibile interrompere** l'erogazione di gas, luce e acqua
            6. **Tieni in casa copia digitale dei documenti**, una scorta di acqua potabile e cibo conservabile
            7. **Installa valvole antiriflusso** per gli scarichi d'acqua
            """)
            
            st.markdown("### ⚠️ Cosa fare DURANTE")
            st.markdown("""
            1. **Non scendere in cantine, seminterrati o garage** per mettere al sicuro beni
            2. **Non uscire per mettere al sicuro l'automobile**
            3. **Se ti trovi in un locale seminterrato o al piano terra**, sali subito ai piani superiori
            4. **Evita l'ascensore** (può bloccarsi)
            5. **Chiudi il gas e disattiva l'impianto elettrico**
            6. **Non bere acqua dal rubinetto** (potrebbe essere contaminata)
            7. **Limita l'uso del cellulare** alle effettive emergenze
            """)
        
        with col2:
            st.markdown("### ⚠️ Se sei all'aperto")
            st.markdown("""
            1. **Allontanati dalla zona allagata**: raggiungi rapidamente l'area elevata più vicina
            2. **Evita di attraversare ponti** e sottopassi
            3. **Evita di dirigersi verso pendii o scarpate** (rischio frane)
            4. **Evita di sostare vicino argini di fiumi e torrenti**
            5. **Evita sottopassi, tunnel e strade vicino argini** (rischio allagamento o frana)
            6. **Se sei in auto**, non tentare di raggiungere la destinazione; trova edifici sicuri e sopraelevati
            7. **Non percorrere strade inondate** e abbandona l'auto in difficoltà
            """)
            
            st.markdown("### ⚠️ Cosa fare DOPO")
            st.markdown("""
            1. **Segui le indicazioni delle autorità** prima di lasciare l'abitazione, usare l'auto o bere l'acqua
            2. **Non transitare lungo strade allagate**: l'acqua potrebbe nascondere voragini o tombini aperti
            3. **Fai attenzione a zone esposte a frane e smottamenti**
            4. **Pulisci e disinfetta superfici e oggetti** a contatto con acqua e fango
            5. **Indossa indumenti protettivi** durante le operazioni di pulizia
            6. **Non utilizzare apparecchiature elettriche** prima del controllo di un tecnico
            """)
        
        st.warning("Per informazioni più dettagliate, consulta il sito della [Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-idraulico/cosa-fare)")
        
    elif tipo_emergenza == "Incendio":
        st.markdown("## 🔥 Cosa fare in caso di incendio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚠️ Prevenzione incendi domestici")
            st.markdown("""
            1. **Tieni sempre sotto controllo pentole e padelle** sul fuoco
            2. **Non lasciare elettrodomestici in stand-by**
            3. **Spegni e stacca la presa degli apparecchi elettrici** quando non in uso
            4. **Non sovraccaricare le prese elettriche** 
            5. **Mantieni lontano materiale infiammabile** da fonti di calore
            6. **Non fumare a letto** o dove potresti addormentarti
            7. **Installa rilevatori di fumo** e tieni in casa un estintore
            """)
            
            st.markdown("### ⚠️ Cosa fare in caso di incendio in casa")
            st.markdown("""
            1. **Mantieni la calma e chiama subito i soccorsi** (115)
            2. **Se l'incendio è di piccola entità**, tentare di spegnerlo con l'estintore
            3. **Chiudi la porta della stanza in fiamme** e sigilla le fessure con panni bagnati
            4. **Disattiva l'energia elettrica e la valvola del gas** prima di abbandonare l'abitazione
            5. **Non aprire le finestre** delle stanze invase dal fumo (alimenterebbero l'incendio)
            6. **Se c'è fumo, copriti naso e bocca** con un panno umido e muoviti carponi
            7. **Non usare l'ascensore**, potrebbe bloccarsi o trasformarsi in una canna di aspirazione
            """)
        
        with col2:
            st.markdown("### ⚠️ Cosa fare in caso di incendio boschivo")
            st.markdown("""
            1. **Chiama subito il 115 (Vigili del Fuoco)** o il 1515 (Carabinieri Forestali)
            2. **Segnala località precisa e punto di riferimento** per facilitare intervento
            3. **Cerca una via di fuga sicura**: strada o corso d'acqua, mai in direzione del vento
            4. **Non sostare in luoghi sovrastanti l'incendio** o in zone verso cui soffia il vento
            5. **Stenditi a terra** in un luogo privo di vegetazione incendiabile
            6. **Non abbandonare l'auto**, chiudi finestrini e ventilazione e segnala presenza con clacson/fari
            7. **Non parcheggiare lungo strade di montagna** che potrebbero servire ai mezzi antincendio
            """)
            
            st.markdown("### ❌ Errori da evitare")
            st.markdown("""
            1. **NON tentare di spegnere un incendio esteso** da solo
            2. **NON usare mai acqua su apparecchiature elettriche** o impianti elettrici
            3. **NON avvicinarti a un incendio** per scattare foto o video
            4. **NON rientrare nell'edificio** fino all'autorizzazione dei Vigili del Fuoco
            5. **NON utilizzare l'ascensore** per nessun motivo
            6. **NON gettare mozziconi di sigarette** in aree vegetate o dal finestrino dell'auto
            7. **NON parcheggiare su erba secca** (il catalizzatore può incendiare la vegetazione)
            """)
        
        st.warning("Per informazioni più dettagliate, consulta il sito della [Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-incendi/cosa-fare)")
        
    else:  # "Tutte le emergenze"
        # Selettore regione
        regione_sel = st.selectbox("Seleziona la tua regione", sorted(dati_regioni.keys()))

        if regione_sel in dati_regioni:
            dati = dati_regioni[regione_sel]

            # Organizziamo il layout in due colonne per ottenere una visualizzazione migliore
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Criticità territoriali
                st.markdown("### 🛑 Criticità territoriali")
                st.markdown(dati["criticita"])

                # Punti di raccolta - Limitiamo a 5 punti per regione per ottimizzare le performance
                st.markdown("### 📍 Punti di raccolta")
                max_punti = min(5, len(dati["punti_raccolta"]))
                for i, punto in enumerate(dati["punti_raccolta"]):
                    if i < max_punti:
                        st.markdown(f"- {punto}")
                    else:
                        # Se ci sono più di 5 punti, mostriamo un messaggio
                        if i == max_punti:
                            st.info(f"Altri {len(dati['punti_raccolta']) - max_punti} punti disponibili. Consulta il sito della Protezione Civile regionale.")
                        break

                # Link utili
                st.markdown("### 🔗 Link utili")
                for titolo, url in dati["link_utili"].items():
                    st.markdown(f"- [{titolo}]({url})")

                # Numeri utili
                st.markdown("### ☎️ Numeri utili")
                st.markdown("""
                - **112** - Numero Unico Emergenze
                - **115** - Vigili del Fuoco
                - **118** - Emergenza Sanitaria
                - **1515** - Emergenza Ambientale (Carabinieri Forestali)
                - **117** - Guardia di Finanza
                - **1530** - Emergenza in Mare (Guardia Costiera)
                - **800 840 840** - Protezione Civile (numero verde)
                """)
            
            with col2:
                # Aggiungiamo una visualizzazione mappa per i punti di raccolta
                st.markdown("### 🗺️ Mappa punti di raccolta")
                
                # Ottimizzazione: verifichiamo se ci sono coordinate precaricate
                if "coordinates" in dati and dati["coordinates"]:
                    start_lat, start_lon = dati["coordinates"]
                else:
                    # Geocodifichiamo il nome della regione
                    with st.spinner("Caricamento mappa..."):
                        start_lat, start_lon = geocode_location(regione_sel)
                
                # Creiamo mappa folium centrata sulla regione
                m = folium.Map(location=[start_lat, start_lon], zoom_start=9)
                
                # Definiamo esplicitamente quanti punti mostrare (tutti fino a 5)
                max_punti = min(5, len(dati["punti_raccolta"]))
                
                # Aggiungiamo i marker alla mappa usando le coordinate precaricate
                with st.spinner("Posizionamento punti di raccolta..."):
                    added_points = 0
                    
                    # Utilizziamo prioritariamente le coordinate precaricate
                    if "punti_raccolta_coords" in dati:
                        # Se abbiamo coordinate precaricate per questa regione, usiamo quelle
                        for i, punto in enumerate(dati["punti_raccolta"]):
                            if i >= max_punti:
                                break
                                
                            punto_key = punto.strip()
                            if punto_key in dati["punti_raccolta_coords"]:
                                # Usiamo le coordinate precaricate
                                lat, lon = dati["punti_raccolta_coords"][punto_key]
                                folium.Marker(
                                    [lat, lon],
                                    popup=punto_key,
                                    tooltip=punto_key,
                                    icon=folium.Icon(color="red", icon="info-sign")
                                ).add_to(m)
                                added_points += 1
                            else:
                                # Se non abbiamo coordinate precaricate per questo punto specifico
                                # usiamo quelle della regione e spostiamo leggermente il marker
                                if "coordinates" in dati:
                                    base_lat, base_lon = dati["coordinates"]
                                    # Aggiungiamo un piccolo offset per visualizzare i punti separati
                                    offset = 0.02 * (i + 1)  # Offset proporzionale all'indice
                                    lat = base_lat + offset
                                    lon = base_lon + offset
                                    folium.Marker(
                                        [lat, lon],
                                        popup=punto_key,
                                        tooltip=punto_key,
                                        icon=folium.Icon(color="orange", icon="info-sign")
                                    ).add_to(m)
                                    added_points += 1
                    else:
                        # Fallback: se non abbiamo coordinate precaricate, creiamo marker artificiali
                        # attorno al centro della regione per assicurarci che tutti i punti siano visibili
                        for i, punto in enumerate(dati["punti_raccolta"]):
                            if i >= max_punti:
                                break
                                
                            # Calcoliamo posizioni distribuite attorno al centro regione
                            # con un pattern circolare per massimizzare la visibilità
                            import math
                            angle = (2 * math.pi / max_punti) * i
                            radius = 0.05  # ~5km di raggio
                            lat = start_lat + radius * math.sin(angle)
                            lon = start_lon + radius * math.cos(angle)
                            
                            folium.Marker(
                                [lat, lon],
                                popup=punto.strip(),
                                tooltip=punto.strip(),
                                icon=folium.Icon(color="green", icon="info-sign")
                            ).add_to(m)
                            added_points += 1
                
                # Visualizziamo la mappa con indicazione dei punti trovati
                folium_static(m, width=400, height=300)
                if added_points > 0:
                    st.success(f"{added_points} punti di raccolta visualizzati sulla mappa")
                else:
                    st.warning("Nessun punto di raccolta geolocalizzato. Consulta l'elenco testuale.")
                    
                # Espander per informazioni extra
                with st.expander("ℹ️ Come raggiungere i punti di raccolta"):
                    st.markdown("""
                    Per raggiungere il punto di raccolta più vicino in caso di emergenza:
                    
                    1. **Mantieni la calma** e segui le indicazioni delle autorità
                    2. **Utilizza Google Maps** inserendo l'indirizzo del punto di raccolta
                    3. **Evita ascensori** e scale mobili in caso di terremoto
                    4. **Spostati a piedi** se possibile, evitando di congestionare strade con veicoli
                    5. **Porta con te** i documenti d'identità e farmaci essenziali
                    
                    In caso di impossibilità a raggiungere i punti ufficiali, cerca spazi aperti lontani da edifici.
                    """)

        else:
            st.error(f"Dati non disponibili per la regione {regione_sel}")