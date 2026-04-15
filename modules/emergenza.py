import streamlit as st
from modules.dati_regioni_a import dati_regioni_a
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
    from modules.banner_utils import banner_emergenza
    banner_emergenza()
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

    # Aggiorna il dizionario dati_regioni con tutti i dati esterni
    dati_regioni.update(dati_regioni_a)
    dati_regioni.update(dati_regioni_b)
    dati_regioni.update(dati_regioni_c)
    
    # Selezione tipo emergenza con contenuti specifici per ogni tipo
    tipo_emergenza = st.radio(
        "Seleziona il tipo di emergenza:",
        ["Tutte le emergenze", "Terremoto", "Alluvione", "Frana", "Incendio", "Maremoto/Tsunami", "Neve e Gelo", "Ondata di Calore"],
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

    elif tipo_emergenza == "Frana":
        st.markdown("## ⛰️ Cosa fare in caso di frana o smottamento")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚠️ Cosa fare PRIMA")
            st.markdown("""
            1. **Informati sul rischio idrogeologico** della tua zona tramite il sito ISPRA o della Protezione Civile regionale
            2. **Conosci i segnali precursori**: piccole crepe nel terreno, cedimenti, inclinazione di alberi e pali, rumore sordo dal sottosuolo
            3. **Evita di costruire o modificare** versanti o aree instabili senza consulenza geologica
            4. **Non ostruire canali e fossi** che regolano il deflusso dell'acqua
            5. **Prepara un piano di evacuazione** familiare e individua percorsi sicuri
            6. **Tieni sempre carico il cellulare** e iscriviti ai sistemi di allerta del tuo comune
            """)
            st.markdown("### ⚠️ Cosa fare DURANTE")
            st.markdown("""
            1. **Allontanati immediatamente** dall'area interessata: non indugiare a raccogliere oggetti
            2. **Non avvicinarti** al fronte della frana o alle aree di scorrimento
            3. **Se sei in auto**, abbandona il veicolo e allontanati a piedi in direzione perpendicolare alla frana
            4. **Segui i percorsi di evacuazione** indicati dal piano comunale
            5. **Evita ponti, sottopassi e aree vicino a fiumi** durante precipitazioni intense
            6. **Chiama il 112** e segnala con precisione la localizzazione dell'evento
            """)
        with col2:
            st.markdown("### ⚠️ Cosa fare DOPO")
            st.markdown("""
            1. **Non rientrare** nelle aree colpite senza autorizzazione delle autorità
            2. **Segnala alle autorità** eventuali danni a strade, edifici, reti di distribuzione
            3. **Non transitare** su strade interessate da frane o smottamenti
            4. **Fotografa i danni** per le pratiche assicurative e il censimento dei danni
            5. **Attendi la valutazione** dei tecnici prima di rientrare nell'abitazione
            6. **Controlla** la stabilità di muri, fondamenta e corpi idrici vicino a casa
            """)
            st.markdown("### ❌ Errori da evitare")
            st.markdown("""
            1. **NON tornare a casa** prima del via libera delle autorità
            2. **NON avvicinarti** al ciglio della frana o alle zone instabili
            3. **NON attraversare** aree allagate o coperte da detriti
            4. **NON usare candele o fiamme libere** se sospetti perdite di gas
            5. **NON ignorare** le allerte meteo in aree a rischio idrogeologico
            """)
        st.warning("Per informazioni più dettagliate, consulta il sito della [Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-idrogeologico/cosa-fare)")

    elif tipo_emergenza == "Maremoto/Tsunami":
        st.markdown("## 🌊 Cosa fare in caso di maremoto (Tsunami)")

        st.info("🇮🇹 L'Italia è esposta al rischio tsunami, in particolare le coste del Mediterraneo orientale, del Mar Tirreno meridionale e dello Stretto di Messina. Il sistema nazionale di allerta è **CAT-INGV** (Centro Allerta Tsunami).")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚠️ Segnali d'allarme naturali")
            st.markdown("""
            1. **Forte terremoto** avvertito sulla costa o in mare
            2. **Ritiro anomalo del mare**: il mare si allontana improvvisamente dalla riva
            3. **Rumore anomalo**: fragore simile a un treno o tuono proveniente dal mare
            4. **Agitazione anomala delle acque**: onde irregolari anche in assenza di vento
            5. Se avverti uno di questi segnali **non aspettare l'allerta ufficiale**: allontanati subito
            """)
            st.markdown("### ⚠️ Cosa fare PRIMA (prevenzione)")
            st.markdown("""
            1. **Informati** se la tua zona è a rischio tsunami tramite il portale CAT-INGV
            2. **Conosci le vie di evacuazione** verso zone elevate (almeno 30 m s.l.m. o 1 km dalla costa)
            3. **Iscriviti ai sistemi di allerta** del tuo comune costiero
            4. **Tieni sempre carica** la batteria del cellulare
            5. **Individua l'area elevata più vicina** raggiungibile a piedi in pochi minuti
            """)
        with col2:
            st.markdown("### ⚠️ Cosa fare DURANTE")
            st.markdown("""
            1. **Allontanati immediatamente dalla costa** appena senti un forte terremoto o l'allarme ufficiale
            2. **Raggiungi zone elevate** (almeno 30 m sopra il livello del mare o 1 km dalla riva)
            3. **Non fermarti a guardare** le onde: la prima non è mai la più pericolosa
            4. **Evita di usare l'auto** se possibile: le strade potrebbero ostruirsi
            5. **Segui le istruzioni** della Protezione Civile e delle autorità locali
            6. **Se sei in barca** in porto, allontanati in mare aperto con mare profondo
            """)
            st.markdown("### ⚠️ Cosa fare DOPO")
            st.markdown("""
            1. **Non tornare sulla costa** fino all'autorizzazione ufficiale: lo tsunami può avere più ondate
            2. **Evita zone allagate**: l'acqua può nascondere voragini, correnti e contaminanti
            3. **Non bere acqua dal rubinetto**: potrebbe essere contaminata
            4. **Segnala feriti o dispersi** al 112
            5. **Ascolta le comunicazioni** di radio, TV e Protezione Civile
            """)
        st.warning("Sistema di Allerta Tsunami nazionale: [CAT-INGV](https://www.ingv.it/cat/)")

    elif tipo_emergenza == "Neve e Gelo":
        st.markdown("## ❄️ Cosa fare in caso di neve intensa, ghiaccio e ondata di freddo")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚠️ Cosa fare PRIMA")
            st.markdown("""
            1. **Segui le previsioni meteo** e le allerte della Protezione Civile
            2. **Rifornisci scorte alimentari** e medicinali essenziali prima dell'evento
            3. **Prepara l'auto**: catene, liquido antigelo, batteria carica, coperte, torcia
            4. **Controlla il riscaldamento** domestico e fai scorta di combustibile
            5. **Proteggi le tubazioni** esposte con materiali isolanti
            6. **Libera preventivamente** balconi e gronde da accumuli d'acqua
            7. **Informa vicini e anziani** delle misure da adottare
            """)
            st.markdown("### ⚠️ Cosa fare DURANTE")
            st.markdown("""
            1. **Limita gli spostamenti** ai casi strettamente necessari
            2. **Se esci**, indossa abbigliamento a strati, guanti, berretto e scarpe antiscivolo
            3. **Fai attenzione al ghiaccio** su marciapiedi, scale e soglie
            4. **Rimuovi la neve** dal tetto e dai balconi per evitare cedimenti
            5. **Non usare generatori** di corrente o stufe a combustione in ambienti chiusi (monossido)
            6. **Controlla gli anziani e le persone sole** nel tuo condominio
            """)
        with col2:
            st.markdown("### ⚠️ Se sei in auto")
            st.markdown("""
            1. **Monta le catene** prima di affrontare strade innevate
            2. **Mantieni velocità ridotta** e distanza di sicurezza aumentata
            3. **Non sorpassare** spazzaneve o mezzi sgombraneve
            4. **Se la tua auto rimane bloccata**: rimani nel veicolo, tieni i finestrini leggermente aperti e segnala la tua presenza
            5. **Porta sempre con te**: acqua, cibo, coperta termica, caricabatterie
            """)
            st.markdown("### ⚠️ Rischio valanghe (zone montane)")
            st.markdown("""
            1. **Controlla il bollettino valanghe** (AINEVA) prima di uscire in montagna
            2. **Non transitare** su versanti a rischio dopo nevicate abbondanti o rapide variazioni termiche
            3. **Porta con te**: ARVA (apparecchio di ricerca in valanga), sonda e pala
            4. **Se sei travolto**: proteggi le vie aeree con le mani, cerca di creare uno spazio davanti al viso
            5. **Chiama il 112** appena sei in zona sicura
            """)
        st.warning("Bollettino valanghe nazionale: [AINEVA](https://www.aineva.it/)")

    elif tipo_emergenza == "Ondata di Calore":
        st.markdown("## 🌡️ Cosa fare durante un'ondata di calore")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚠️ Misure preventive")
            st.markdown("""
            1. **Segui il bollettino** del Ministero della Salute (sistema HHWWS)
            2. **Tieniti idratato**: bevi almeno 2 litri d'acqua al giorno anche senza sete
            3. **Evita uscite** nelle ore più calde (12:00–16:00)
            4. **Indossa abiti** leggeri, chiari e di cotone; proteggi testa e nuca
            5. **Oscura finestre** esposte al sole durante le ore più calde; arieggia la notte
            6. **Non lasciare** bambini, anziani o animali in auto o in ambienti non ventilati
            7. **Controlla** anziani, persone sole e malati cronici nel tuo vicinato
            """)
            st.markdown("### ⚠️ Cosa fare se stai male")
            st.markdown("""
            1. **Riconosci i segnali** del colpo di calore: pelle arrossata e calda, confusione, nausea, perdita di coscienza
            2. **Porta la persona** in un luogo fresco e ventilato
            3. **Raffredda rapidamente** il corpo: panni bagnati freddi su collo, ascelle e inguine
            4. **Chiama il 118** in caso di perdita di coscienza o sintomi gravi
            5. **Non somministrare** liquidi a una persona priva di sensi
            """)
        with col2:
            st.markdown("### ⚠️ Gruppi a rischio elevato")
            st.markdown("""
            - **Anziani over 65**: termoregolazione ridotta, spesso soli e con patologie
            - **Bambini piccoli**: soggetti a rapido surriscaldamento
            - **Persone con malattie croniche**: cardiovascolari, respiratorie, renali, psichiatriche
            - **Chi fa attività fisica all'aperto**: lavoratori agricoli, edili, sportivi
            - **Persone in condizioni di fragilità socioeconomica**: senza aria condizionata, senza rete di supporto
            """)
            st.markdown("### ⚠️ Consigli pratici")
            st.markdown("""
            1. **Utilizza piani bassi** degli edifici: il caldo sale
            2. **Fai docce o bagni** freschi (non gelidi) più volte al giorno
            3. **Evita alcol, caffè e bevande zuccherate** che disidratano
            4. **Mangia pasti leggeri**: frutta, verdura, cibi con alto contenuto d'acqua
            5. **Trascorri alcune ore** in luoghi climatizzati (centri commerciali, biblioteche)
            6. **Chiama il numero verde** 1500 (Ministero della Salute) per informazioni
            """)
        st.warning("Bollettino caldo del Ministero della Salute: [Portale Salute](https://www.salute.gov.it/portale/caldo/homeCaldo.jsp)")

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

                # Punti di raccolta con GPS navigazione
                st.markdown("### 📍 Punti di raccolta")
                _coords_dict = dati.get("punti_raccolta_coords", {})
                for punto in dati["punti_raccolta"]:
                    _pk = punto.strip()
                    _c  = _coords_dict.get(_pk)
                    if _c:
                        _g  = f"https://www.google.com/maps/dir/?api=1&destination={_c[0]},{_c[1]}&travelmode=driving"
                        _wz = f"https://waze.com/ul?ll={_c[0]},{_c[1]}&navigate=yes"
                        _am = f"https://maps.apple.com/?daddr={_c[0]},{_c[1]}&dirflg=d"
                        col_pi, col_pn = st.columns([3, 2])
                        with col_pi:
                            st.markdown(
                                '<div style="border-left:4px solid #DC2626;padding-left:10px;margin-bottom:4px;">'
                                f'<p style="margin:0;font-size:14px;">📌 <b>{_pk}</b></p>'
                                f'<p style="margin:0;font-size:11px;color:#888;font-family:monospace;">{_c[0]:.5f}, {_c[1]:.5f}</p>'
                                '</div>',
                                unsafe_allow_html=True)
                        with col_pn:
                            st.markdown(
                                '<div style="background:#fff7f7;border:1px solid #fecaca;border-radius:6px;padding:6px 10px;">'
                                '<div style="display:flex;gap:4px;flex-wrap:wrap;">'
                                f'<a href="{_g}" target="_blank" style="background:#4285F4;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap;">🗺️ GMaps</a>'
                                f'<a href="{_wz}" target="_blank" style="background:#00BCD4;color:#000;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap;">🚗 Waze</a>'
                                f'<a href="{_am}" target="_blank" style="background:#555;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap;">🍎 Maps</a>'
                                '</div></div>',
                                unsafe_allow_html=True)
                    else:
                        st.markdown(f"📌 {_pk}")
                st.caption(f"Totale punti: {len(dati['punti_raccolta'])} · Fonte: Protezione Civile")

                # Rischio idrogeologico (se presente)
                if "rischio_idrogeologico" in dati and dati["rischio_idrogeologico"]:
                    rh = dati["rischio_idrogeologico"]
                    st.markdown("### 🌧️ Rischio Idrogeologico")
                    st.markdown(rh.get("descrizione", ""))
                    if rh.get("link"):
                        st.markdown(f"[📋 Approfondisci]({rh['link']})")

                # Rischi specifici (se presenti)
                if "rischi_specifici" in dati and dati["rischi_specifici"]:
                    st.markdown("### ⚡ Rischi specifici del territorio")
                    for tipo_rischio, desc in dati["rischi_specifici"].items():
                        with st.expander(f"🔸 {tipo_rischio}"):
                            st.markdown(desc)

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
                
                # Aggiungiamo i marker alla mappa usando le coordinate precaricate
                with st.spinner("Posizionamento punti di raccolta..."):
                    added_points = 0
                    
                    # Utilizziamo prioritariamente le coordinate precaricate
                    if "punti_raccolta_coords" in dati:
                        # Mostra tutti i punti disponibili sulla mappa
                        for i, punto in enumerate(dati["punti_raccolta"]):
                            punto_key = punto.strip()
                            if punto_key in dati["punti_raccolta_coords"]:
                                lat, lon = dati["punti_raccolta_coords"][punto_key]
                                _pg  = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                                _pwz = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
                                _pam = f"https://maps.apple.com/?daddr={lat},{lon}&dirflg=d"
                                _ph  = (
                                    '<div style="min-width:220px;font-family:sans-serif;font-size:13px;">'
                                    f'<h4 style="color:#DC2626;margin:0 0 6px 0;font-size:13px;border-bottom:2px solid #DC2626;padding-bottom:3px;">📌 {punto_key}</h4>'
                                    f'<p style="margin:0 0 6px 0;font-size:11px;color:#888;font-family:monospace;">{lat:.5f}, {lon:.5f}</p>'
                                    '<div style="display:flex;gap:4px;">'
                                    f'<a href="{_pg}" target="_blank" style="background:#4285F4;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🗺️ GMaps</a>'
                                    f'<a href="{_pwz}" target="_blank" style="background:#00BCD4;color:#000;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🚗 Waze</a>'
                                    f'<a href="{_pam}" target="_blank" style="background:#555;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🍎 Maps</a>'
                                    '</div></div>'
                                )
                                folium.Marker(
                                    [lat, lon],
                                    popup=folium.Popup(_ph, max_width=280),
                                    tooltip=punto_key,
                                    icon=folium.Icon(color="red", icon="info-sign")
                                ).add_to(m)
                                added_points += 1
                            else:
                                if "coordinates" in dati:
                                    base_lat, base_lon = dati["coordinates"]
                                    offset = 0.02 * (i + 1)
                                    lat = base_lat + offset
                                    lon = base_lon + offset
                                    _pg2  = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                                    _pwz2 = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
                                    _pam2 = f"https://maps.apple.com/?daddr={lat},{lon}&dirflg=d"
                                    _ph2  = (
                                        '<div style="min-width:200px;font-family:sans-serif;font-size:13px;">'
                                        f'<h4 style="color:#D97706;margin:0 0 6px 0;font-size:13px;border-bottom:2px solid #D97706;padding-bottom:3px;">📌 {punto_key}</h4>'
                                        f'<p style="margin:0 0 2px 0;font-size:11px;color:#888;">⚠️ Coordinate approssimative</p>'
                                        '<div style="display:flex;gap:4px;margin-top:6px;">'
                                        f'<a href="{_pg2}" target="_blank" style="background:#4285F4;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🗺️ GMaps</a>'
                                        f'<a href="{_pwz2}" target="_blank" style="background:#00BCD4;color:#000;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🚗 Waze</a>'
                                        f'<a href="{_pam2}" target="_blank" style="background:#555;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🍎 Maps</a>'
                                        '</div></div>'
                                    )
                                    folium.Marker(
                                        [lat, lon],
                                        popup=folium.Popup(_ph2, max_width=260),
                                        tooltip=punto_key,
                                        icon=folium.Icon(color="orange", icon="info-sign")
                                    ).add_to(m)
                                    added_points += 1
                    else:
                        # Fallback: se non abbiamo coordinate precaricate, creiamo marker artificiali
                        # attorno al centro della regione per assicurarci che tutti i punti siano visibili
                        n_punti = len(dati["punti_raccolta"])
                        for i, punto in enumerate(dati["punti_raccolta"]):
                            # Calcoliamo posizioni distribuite attorno al centro regione
                            # con un pattern circolare per massimizzare la visibilità
                            import math
                            angle = (2 * math.pi / max(n_punti, 1)) * i
                            radius = 0.05  # ~5km di raggio
                            lat = start_lat + radius * math.sin(angle)
                            lon = start_lon + radius * math.cos(angle)
                            
                            _pf  = punto.strip()
                            _pfg  = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                            _pfwz = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
                            _pfam = f"https://maps.apple.com/?daddr={lat},{lon}&dirflg=d"
                            _pfh  = (
                                '<div style="min-width:200px;font-family:sans-serif;font-size:13px;">'
                                f'<h4 style="color:#16A34A;margin:0 0 6px 0;font-size:13px;border-bottom:2px solid #16A34A;padding-bottom:3px;">📌 {_pf}</h4>'
                                '<div style="display:flex;gap:4px;margin-top:6px;">'
                                f'<a href="{_pfg}" target="_blank" style="background:#4285F4;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🗺️ GMaps</a>'
                                f'<a href="{_pfwz}" target="_blank" style="background:#00BCD4;color:#000;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🚗 Waze</a>'
                                f'<a href="{_pfam}" target="_blank" style="background:#555;color:white;padding:4px 7px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:600;">🍎 Maps</a>'
                                '</div></div>'
                            )
                            folium.Marker(
                                [lat, lon],
                                popup=folium.Popup(_pfh, max_width=260),
                                tooltip=_pf,
                                icon=folium.Icon(color="green", icon="info-sign")
                            ).add_to(m)
                            added_points += 1
                
                # Visualizziamo la mappa con indicazione dei punti trovati
                folium_static(m, width=800, height=420)
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