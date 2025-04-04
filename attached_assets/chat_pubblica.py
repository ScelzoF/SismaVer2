def show():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    import os
    from supabase import create_client, Client
    import time
    import re
    from streamlit_js_eval import streamlit_js_eval

    st.title("💬 Chat Pubblica")
    
    # Inizializzazione supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("⚠️ Configurazione Supabase mancante. La chat non è disponibile.")
        st.info("Per attivare la chat, è necessario configurare le credenziali Supabase nelle variabili d'ambiente.")
        
        # Form per inserimento manuale delle credenziali (temporaneo)
        with st.form("supabase_form"):
            st.write("Inserisci manualmente le credenziali Supabase:")
            supabase_url_input = st.text_input("URL Supabase", placeholder="https://your-project.supabase.co")
            supabase_key_input = st.text_input("Chiave API Supabase", type="password")
            submit = st.form_submit_button("Connetti")
            
            if submit and supabase_url_input and supabase_key_input:
                supabase_url = supabase_url_input
                supabase_key = supabase_key_input
                st.success("Credenziali inserite correttamente")
                st.info("Queste credenziali saranno valide solo per questa sessione")
                st.rerun()
        
        if not supabase_url or not supabase_key:
            return
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Verifica che la tabella chat_messages esista
        try:
            response = supabase.table("chat_messages").select("count", count="exact").execute()
            # Se arriviamo qui, la tabella esiste
        except Exception as e:
            st.error(f"⚠️ La tabella chat_messages non esiste o non è accessibile: {e}")
            st.info("La chat pubblica richiede una tabella 'chat_messages' nel database Supabase.")
            st.code("""
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    regione TEXT NOT NULL,
    lat FLOAT,
    lon FLOAT
);
            """, language="sql")
            return
            
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
    try:
        coords = streamlit_js_eval(
            js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
            key="geo_chat"
        )
    except:
        coords = None
    
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
        
        # Caricamento dei messaggi
        def load_messages():
            try:
                # Filtro per regione se selezionata
                if regione_filtro != "Tutte le regioni":
                    response = supabase.table("chat_messages").select("*").eq("regione", regione_filtro).order("timestamp", desc=True).limit(50).execute()
                else:
                    response = supabase.table("chat_messages").select("*").order("timestamp", desc=True).limit(50).execute()
                
                if hasattr(response, 'data'):
                    messages = response.data
                    return sorted(messages, key=lambda x: x["timestamp"])
                else:
                    return []
            except Exception as e:
                st.error(f"Errore nel caricamento dei messaggi: {e}")
                return []
        
        # Visualizzazione messaggi
        with messages_container:
            messages = load_messages()
            
            if not messages:
                st.info("📭 Nessun messaggio disponibile. Sii il primo a scrivere!")
            else:
                for msg in messages:
                    # Formattazione timestamp
                    try:
                        ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                        timestamp_str = ts.strftime("%d/%m/%Y %H:%M")
                    except:
                        timestamp_str = msg.get("timestamp", "Data sconosciuta")
                    
                    # Visualizzazione messaggi con stile
                    st.markdown(f"""
                    <div style='background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:10px;'>
                        <strong>{msg["nickname"]}</strong> <small>({msg["regione"]} - {timestamp_str})</small><br>
                        {msg["message"]}
                    </div>
                    """, unsafe_allow_html=True)
        
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
                    if coords and isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                        message_data["lat"] = coords["lat"]
                        message_data["lon"] = coords["lon"]
                    
                    # Invia a Supabase
                    response = supabase.table("chat_messages").insert(message_data).execute()
                    if hasattr(response, 'error') and response.error:
                        st.error(f"Errore nell'invio: {response.error}")
                    else:
                        st.success("Messaggio inviato!")
                        time.sleep(0.5)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Errore nell'invio del messaggio: {e}")
        
        # Aggiornamento automatico
        if st.button("🔄 Aggiorna messaggi"):
            st.rerun()
            
        st.info("I messaggi non si aggiornano automaticamente. Clicca 'Aggiorna messaggi' per caricare i nuovi messaggi.")
    
    with tab2:
        st.subheader("📋 Istruzioni per l'utilizzo della chat")
        
        st.markdown("""
        Questa chat è pensata per:
        - Condividere informazioni su eventi sismici o vulcanici in corso
        - Segnalare condizioni meteo estreme nella tua zona
        - Chiedere o offrire supporto in caso di emergenza
        - Scambiare esperienze e consigli con altri utenti
        
        ### Regole della chat
        1. **Rispetta gli altri utenti** - Sii cortese e rispettoso nelle tue interazioni
        2. **Verifica le informazioni** - Cerca di condividere solo informazioni verificate e affidabili
        3. **Protezione dati personali** - Non condividere informazioni personali sensibili
        4. **In caso di emergenza** - Per emergenze reali, contatta sempre il numero unico di emergenza 112
        
        ### Funzionalità
        - **Filtro per regione**: Seleziona una regione specifica nella barra laterale per visualizzare solo i messaggi relativi
        - **Nickname**: Puoi modificare il tuo nickname nella barra laterale
        - **Geolocalizzazione**: Se consenti l'accesso alla tua posizione, questa verrà associata ai tuoi messaggi (utile in caso di segnalazioni specifiche)
        
        Per segnalazioni tecniche o problemi relativi alla chat, contatta l'amministratore.
        """)