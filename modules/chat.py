import streamlit as st
import pandas as pd
from datetime import datetime
import os
from supabase import create_client, Client
import time
import re
from streamlit_js_eval import streamlit_js_eval

def show():
    st.title("💬 Chat Pubblica")
    
    # Inizializzazione supabase - utilizziamo la sessione se la connessione è già stabilita
    if "supabase_connected" in st.session_state and st.session_state.supabase_connected:
        supabase = st.session_state.supabase_client
    else:
        # Altrimenti proviamo a connetterci
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            st.error("⚠️ Configurazione Supabase mancante. La chat non è disponibile.")
            st.info("Per attivare la chat, l'amministratore deve configurare le credenziali Supabase nelle variabili d'ambiente.")
            return
        
        try:
            supabase = create_client(supabase_url, supabase_key)
            st.session_state.supabase_client = supabase
            st.session_state.supabase_connected = True
        except Exception as e:
            st.error(f"⚠️ Errore nella connessione a Supabase: {e}")
            return
    
    # Sidebar per la chat
    st.sidebar.header("🔧 Impostazioni chat")
    
    # Gestione nickname
    if "nickname" not in st.session_state:
        # Genera nickname casuale iniziale
        import random
        st.session_state.nickname = f"Utente{random.randint(1000, 9999)}"
    
    # Gestione nickname
    nickname = st.sidebar.text_input("Nickname", value=st.session_state.nickname)
    if nickname != st.session_state.nickname:
        st.session_state.nickname = nickname
    
    # Selezione regione per filtro messaggi
    regioni_italiane = [
        "Tutte le regioni", "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
        "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
        "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige",
        "Umbria", "Valle d'Aosta", "Veneto"
    ]
    
    regione_filtro = st.sidebar.selectbox("Filtra per regione", regioni_italiane)
    
    # Geolocalizzazione per associare la posizione ai messaggi
    coords = streamlit_js_eval(
        js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
        key="geo_chat"
    )
    
    # Layout principale chat
    st.write("""
    Questa chat pubblica ti permette di comunicare con altri utenti di SismaVer2 in tutta Italia. 
    Puoi condividere informazioni, segnalazioni o richiedere supporto.
    """)
    
    # Tabs
    tab1, tab2 = st.tabs(["💬 Chat generale", "📋 Istruzioni"])
    
    with tab1:
        # Container per i messaggi
        messages_container = st.container()
        
        # Input per il nuovo messaggio
        with st.form(key="chat_form", clear_on_submit=True):
            # Selezione della regione del messaggio
            regione_msg = st.selectbox("Regione", regioni_italiane[1:])
            
            # Campo per il messaggio
            col1, col2 = st.columns([4, 1])
            with col1:
                message = st.text_area(
                "Messaggio",
                height=100,
                key="message_input",
                label_visibility="visible",
                placeholder="Scrivi il tuo messaggio qui..."
            )
            with col2:
                st.write("")
                st.write("")
                st.write("")
                submit_button = st.form_submit_button("Invia")
        
        # Gestione invio messaggio
        if submit_button and message:
            # Verifica che il messaggio non sia vuoto
            if message.strip():
                # Sanitizza il messaggio per sicurezza
                message_clean = re.sub(r'<.*?>', '', message)
                
                try:
                    # Prepara i dati del messaggio
                    timestamp = datetime.now().isoformat()
                    message_data = {
                        "nickname": nickname,
                        "message": message_clean,
                        "timestamp": timestamp,
                        "regione": regione_msg,
                    }
                    
                    # Aggiungi coordinate se disponibili
                    if coords and "lat" in coords and "lon" in coords:
                        message_data["lat"] = coords["lat"]
                        message_data["lon"] = coords["lon"]
                    
                    # Salva il messaggio localmente invece di usare Supabase
                    try:
                        # Creazione della directory se non esiste
                        os.makedirs("data", exist_ok=True)
                        local_chat_file = "data/local_chat_messages.csv"
                        
                        # Crea o aggiorna il file CSV locale
                        if not os.path.exists(local_chat_file):
                            # Crea nuovo file con intestazione
                            with open(local_chat_file, "w") as f:
                                f.write("id,nickname,message,timestamp,regione,lat,lon\n")
                        
                        # Determina un ID unico incrementale
                        message_id = 1
                        if os.path.exists(local_chat_file):
                            with open(local_chat_file, "r") as f:
                                lines = f.readlines()
                                if len(lines) > 1:  # Più di una riga (intestazione)
                                    try:
                                        last_id = int(lines[-1].split(",")[0])
                                        message_id = last_id + 1
                                    except:
                                        pass
                        
                        # Aggiunge il messaggio al file
                        with open(local_chat_file, "a") as f:
                            lat_str = str(coords.get("lat", "")) if coords and "lat" in coords else ""
                            lon_str = str(coords.get("lon", "")) if coords and "lon" in coords else ""
                            # Sanitizza i campi per il formato CSV
                            sanitized_message = message_clean.replace(",", " ").replace("\n", " ")
                            sanitized_nickname = nickname.replace(",", " ")
                            f.write(f"{message_id},{sanitized_nickname},{sanitized_message},{timestamp},{regione_msg},{lat_str},{lon_str}\n")
                        
                        st.success("Messaggio salvato con successo!")
                    except Exception as e:
                        st.error(f"Errore nel salvataggio del messaggio locale: {e}")
                
                except Exception as e:
                    st.error(f"Errore durante l'invio del messaggio: {e}")
        
        # Recupera e visualizza i messaggi da file locale
        try:
            local_chat_file = "data/local_chat_messages.csv"
            messages = []
            
            if os.path.exists(local_chat_file):
                try:
                    # Leggi tutti i messaggi dal file CSV
                    with open(local_chat_file, "r") as f:
                        lines = f.readlines()
                        
                    # Skip header
                    if len(lines) > 1:
                        for line in lines[1:]:
                            parts = line.strip().split(",")
                            if len(parts) >= 5:  # Almeno id, nickname, message, timestamp, regione
                                msg = {
                                    "id": parts[0],
                                    "nickname": parts[1],
                                    "message": parts[2],
                                    "timestamp": parts[3],
                                    "regione": parts[4],
                                }
                                # Aggiungi coordinate se presenti
                                if len(parts) > 6:
                                    try:
                                        if parts[5] and parts[5].strip():
                                            msg["lat"] = float(parts[5])
                                        else:
                                            msg["lat"] = None
                                            
                                        if parts[6] and parts[6].strip():
                                            msg["lon"] = float(parts[6])
                                        else:
                                            msg["lon"] = None
                                    except:
                                        msg["lat"] = None
                                        msg["lon"] = None
                                
                                # Filtra per regione se necessario
                                if regione_filtro == "Tutte le regioni" or msg["regione"] == regione_filtro:
                                    messages.append(msg)
                except Exception as e:
                    st.error(f"Errore nella lettura dei messaggi: {e}")
            
            if not messages:
                st.info("Nessun messaggio disponibile. Sii il primo a scrivere!")
            else:
                with messages_container:
                    st.subheader(f"Ultimi messaggi {f'- {regione_filtro}' if regione_filtro != 'Tutte le regioni' else ''}")
                    
                    # Mostra gli ultimi 100 messaggi (o meno se ce ne sono meno)
                    messages_to_display = messages[-100:] if len(messages) > 100 else messages
                    
                    # Inverti ordine per mostrare i più recenti in fondo
                    for message in reversed(messages_to_display):
                        # Formatta la data
                        try:
                            # Gestisce sia il formato ISO che datetime
                            if "T" in message["timestamp"]:
                                timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%d/%m/%Y %H:%M")
                            else:
                                timestamp = message["timestamp"]
                        except:
                            timestamp = message.get("timestamp", "Data sconosciuta")
                        
                        # Crea box messaggio
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            st.markdown(f"**{message.get('nickname', 'Anonimo')}**")
                            st.caption(f"{timestamp}")
                            st.caption(f"{message.get('regione', 'N/A')}")
                        with col2:
                            st.markdown(f"{message.get('message', '')}")
                        st.markdown("---")
        
        except Exception as e:
            st.error(f"Errore durante il recupero dei messaggi: {e}")
            st.error("Dettagli tecnici per l'amministratore:")
            st.code(str(e))
    
    with tab2:
        st.subheader("📝 Guida all'utilizzo della chat")
        st.markdown("""
        ### Come usare la chat
        1. **Inserisci il tuo nickname** nella barra laterale
        2. **Seleziona la tua regione** quando scrivi un messaggio
        3. **Scrivi il tuo messaggio** e premi "Invia"
        4. Puoi **filtrare i messaggi per regione** usando il selettore nella barra laterale
        
        ### Linee guida della community
        - Mantieni un linguaggio rispettoso e appropriato
        - Condividi informazioni veritiere e verificate
        - Evita di diffondere panico o notizie false
        - Non condividere dati personali sensibili
        - Segnala comportamenti inappropriati
        
        ### Scopo della chat
        Questa chat è pensata per:
        - Condividere informazioni su eventi sismici o vulcanici in corso
        - Richiedere supporto o informazioni
        - Segnalare situazioni di emergenza nella tua zona
        - Fornire aggiornamenti su eventi meteo estremi
        - Creare una rete di supporto tra gli utenti di SismaVer2
        
        ### Privacy
        I messaggi inviati sono pubblici e visibili a tutti gli utenti. La tua posizione esatta è utilizzata solo se accetti la geolocalizzazione, e viene usata unicamente per migliorare la contestualizzazione dei messaggi.
        """)
    
    # Aggiunta mappa messaggi se disponibili
    if regione_filtro != "Tutte le regioni":
        # Recupera messaggi con coordinate per la mappa dal file locale
        try:
            local_chat_file = "data/local_chat_messages.csv"
            geo_messages = []
            
            if os.path.exists(local_chat_file):
                # Leggi messaggi dal file CSV locale
                with open(local_chat_file, "r") as f:
                    lines = f.readlines()
                    
                # Skip header
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = line.strip().split(",")
                        if len(parts) >= 7:  # Dobbiamo avere anche lat e lon
                            # Verifica che ci siano coordinate e che la regione corrisponda
                            if parts[4] == regione_filtro and parts[5] and parts[6]:
                                try:
                                    lat = float(parts[5])
                                    lon = float(parts[6])
                                    
                                    geo_messages.append({
                                        "nickname": parts[1],
                                        "message": parts[2],
                                        "timestamp": parts[3],
                                        "regione": parts[4],
                                        "lat": lat,
                                        "lon": lon
                                    })
                                except:
                                    pass  # Skip se la conversione fallisce
            
            if geo_messages:
                # Crea DataFrame per la mappa
                map_data = []
                for msg in geo_messages:
                    map_data.append({
                        "lat": msg["lat"],
                        "lon": msg["lon"],
                        "nickname": msg.get("nickname", "Anonimo"),
                        "regione": msg.get("regione", "N/A"),
                        "timestamp": msg.get("timestamp", "")
                    })
                
                if map_data:
                    df_map = pd.DataFrame(map_data)
                    
                    # Visualizza mappa
                    st.subheader(f"🗺️ Mappa messaggi - {regione_filtro}")
                    st.map(df_map)
        
        except Exception as e:
            pass  # Silently fail for the map part
