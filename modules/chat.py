def show():
    import streamlit as st
    import pandas as pd
    from datetime import datetime, timezone, timedelta
    
    # Configura il fuso orario italiano
    ora_legale = True  # Imposta manualmente in base al periodo dell'anno
    FUSO_ORARIO_ITALIA = timezone(timedelta(hours=2 if ora_legale else 1))
    import os
    import json
    import time
    import re
    import uuid
    from streamlit_js_eval import streamlit_js_eval

    # Import Supabase
    try:
        from supabase import create_client, Client
    except ImportError:
        st.error("📦 Libreria Supabase non installata")
        st.info("Esegui 'pip install supabase' per installare la libreria")
        return

    st.title("💬 Chat Pubblica - SismaVer2")

    # Inizializzazione supabase con valori predefiniti
    supabase_url = os.environ.get("SUPABASE_URL", "https://hqrdtuktmkemaitrusxw.supabase.co")
    supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhxcmR0dWt0bWtlbWFpdHJ1c3h3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2Mzc2NDMsImV4cCI6MjA1ODIxMzY0M30.SDYaTicz0dWnocfa6oB7_QhB5f3ExRLTaCqtAHkQUgE")

    # Messaggio informativo sullo stato delle API
    if supabase_url and supabase_key:
        st.success("✅ Connessione al database Supabase configurata.")
    else:
        try:
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
            st.success("✅ Connessione al database Supabase configurata via secrets.")
        except:
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
                # Mostra istruzioni per la configurazione di Supabase
                st.subheader("🚀 Configurazione Supabase")
                st.markdown("""
                Per configurare la chat:

                1. Crea un account gratuito su [Supabase](https://supabase.com)
                2. Crea un nuovo progetto
                3. Vai su Project Settings > API
                4. Copia l'URL e la chiave API (anon/public)
                5. Esegui questo script SQL sull'editor SQL di Supabase:
                """)

                st.code("""
CREATE TABLE public.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    regione TEXT NOT NULL,
    lat FLOAT,
    lon FLOAT,
    user_id TEXT,
    is_emergency BOOLEAN DEFAULT false
);

-- Indici per migliorare le performance
CREATE INDEX idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX idx_chat_messages_regione ON public.chat_messages(regione);

-- Politiche di sicurezza Row Level Security (RLS)
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Politica: chiunque può leggere i messaggi
CREATE POLICY "Tutti possono leggere i messaggi" 
ON public.chat_messages FOR SELECT 
USING (true);

-- Politica: solo l'utente che ha creato il messaggio può modificarlo o eliminarlo
CREATE POLICY "Gli utenti possono modificare i propri messaggi" 
ON public.chat_messages FOR UPDATE 
USING (auth.uid()::text = user_id);

CREATE POLICY "Gli utenti possono eliminare i propri messaggi" 
ON public.chat_messages FOR DELETE 
USING (auth.uid()::text = user_id);

-- Politica: chiunque può inserire nuovi messaggi
CREATE POLICY "Tutti possono inserire messaggi" 
ON public.chat_messages FOR INSERT 
WITH CHECK (true);
                """, language="sql")

                st.markdown("""
                6. Configura le variabili d'ambiente nel tuo .env file o nelle impostazioni di Replit
                ```
                SUPABASE_URL=your-project-url
                SUPABASE_KEY=your-anon-key
                ```
                """)

                return

    try:
        # Verifica validità URL prima di creare client
        if not supabase_url.startswith("https://"):
            st.error(f"URL Supabase non valido: {supabase_url}")
            st.info("L'URL deve iniziare con 'https://'")
            return

        # Creazione client con gestione errori
        try:
            supabase = create_client(supabase_url, supabase_key)
            st.success(f"Connesso a Supabase: {supabase_url}")
        except Exception as e:
            st.error(f"Errore nella creazione del client Supabase: {e}")
            return

        # Verifica che la tabella chat_messages esista
        try:
            response = supabase.table("chat_messages").select("count", count="exact").limit(1).execute()
            # Se arriviamo qui, la tabella esiste
        except Exception as e:
            st.error(f"⚠️ La tabella chat_messages non esiste o non è accessibile: {e}")
            st.info("La chat pubblica richiede una tabella 'chat_messages' nel database Supabase.")
            st.code("""
CREATE TABLE public.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    regione TEXT NOT NULL,
    lat FLOAT,
    lon FLOAT,
    user_id TEXT,
    is_emergency BOOLEAN DEFAULT false
);

-- Indici per migliorare le performance
CREATE INDEX idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX idx_chat_messages_regione ON public.chat_messages(regione);
            """, language="sql")
            return

    except Exception as e:
        st.error(f"⚠️ Errore nella connessione a Supabase: {e}")
        return

    # Gestione utente e identificativo unico persistente
    if "user_id" not in st.session_state:
        # Genera ID utente univoco e persistente per questa sessione
        st.session_state.user_id = str(uuid.uuid4())

    # Gestione nickname (senza generazione automatica)
    if "nickname" not in st.session_state:
        st.session_state.nickname = ""  # Inizializzato come vuoto, l'utente deve inserirlo
    
    # Impostazioni della chat in orizzontale
    st.write("### 🔧 Impostazioni chat")
    
    # Prima riga: Nickname e Regione di filtro
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Input nickname (richiesto)
        nickname = st.text_input("👤 Il tuo nome", value=st.session_state.nickname, placeholder="Inserisci il tuo nome")
        if nickname != st.session_state.nickname:
            st.session_state.nickname = nickname
    
    # Selezione regione per filtro messaggi
    regioni_italiane = [
        "Tutte le regioni", "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
        "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
        "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige",
        "Umbria", "Valle d'Aosta", "Veneto"
    ]
    
    with col2:
        regione_filtro = st.selectbox("🗺️ Filtra per regione", regioni_italiane)
    
    with col3:
        mostra_emergenze = st.checkbox("🚨 Evidenzia emergenze", value=True)
    
    # Seconda riga: Altre opzioni
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_messaggi = st.slider("📊 Numero messaggi", min_value=10, max_value=100, value=50, step=10)
    
    with col2:
        ordine_desc = st.checkbox("🔄 Ordine cronologico inverso", value=False)
    
    # Linea divisoria
    st.markdown("---")

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
    Puoi condividere informazioni, segnalazioni o richiedere supporto in tempo reale.
    """)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🗺️ Mappa messaggi", "📋 Istruzioni"])

    with tab1:
        # Container per i messaggi
        messages_container = st.container()

        # Caricamento dei messaggi con la funzione
        @st.cache_data(ttl=15, show_spinner=False)  # Cache 15 secondi
        def load_messages(regione_filtro="Tutte le regioni", limit=50, descending=False):
            try:
                # Costruisci la query base
                query = supabase.table("chat_messages").select("*")

                # Filtro per regione se selezionata
                if regione_filtro != "Tutte le regioni":
                    query = query.eq("regione", regione_filtro)

                # Ordina per timestamp
                if descending:
                    query = query.order("timestamp", desc=True)
                else:
                    query = query.order("timestamp")

                # Limita i risultati
                response = query.limit(limit).execute()

                if hasattr(response, 'data'):
                    return response.data
                else:
                    return []
            except Exception as e:
                st.error(f"Errore nel caricamento dei messaggi: {e}")
                return []

        # Visualizzazione messaggi
        with messages_container:
            messages = load_messages(regione_filtro, num_messaggi, ordine_desc)

            # Modifica per la visualizzazione se l'ordine è invertito
            if not ordine_desc:
                messages = messages  # Già nell'ordine corretto

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

                    # Determina se è un messaggio di emergenza
                    is_emergency = msg.get("is_emergency", False)

                    # Stile base per tutti i messaggi
                    background_color = "#f0f2f6"  # Default
                    border_color = "#e6e6e6"      # Default

                    # Modifica lo stile per i messaggi di emergenza
                    if is_emergency and mostra_emergenze:
                        background_color = "#ffecec"  # Rosso chiaro
                        border_color = "#ff8080"      # Rosso più intenso

                    # Determina se è un messaggio dell'utente corrente
                    is_own_message = msg.get("user_id") == st.session_state.user_id
                    if is_own_message:
                        background_color = "#e6f3ff"  # Blu chiaro per messaggi propri
                        border_color = "#b3d9ff"      # Blu più intenso

                    # Visualizzazione messaggi con stile personalizzato
                    st.markdown(f"""
                    <div style='background-color:{background_color}; padding:10px; 
                         border-radius:5px; margin-bottom:10px; border-left:4px solid {border_color};'>
                        <strong>{msg["nickname"]}</strong> 
                        <small>({msg["regione"]} - {timestamp_str})</small>
                        {" 🚨 " if is_emergency and mostra_emergenze else ""}
                        {" (tu) " if is_own_message else ""}<br>
                        {msg["message"]}
                    </div>
                    """, unsafe_allow_html=True)

                # Opzione per caricare più messaggi
                if len(messages) == num_messaggi:
                    st.button("Carica più messaggi", key="load_more")

        # Input per il nuovo messaggio
        with st.form(key="chat_form", clear_on_submit=True):
            # Layout form
            col1, col2 = st.columns([3, 1])

            with col1:
                # Campo per il messaggio
                message = st.text_area(
                    "Scrivi un messaggio",
                    height=100,
                    key="message_input",
                    placeholder="Condividi informazioni o richiedi supporto..."
                )

            with col2:
                # Selezione della regione del messaggio
                regione_msg = st.selectbox("Regione", regioni_italiane[1:])
                # Opzione per segnalare emergenza
                is_emergency = st.checkbox("🚨 Segnala come emergenza")

            # Pulsante di invio
            submit_button = st.form_submit_button("Invia messaggio")

        # Gestione invio messaggio
        if submit_button and message:
            # Verifica che il nome utente sia stato inserito
            if not nickname or nickname.strip() == "":
                st.error("⚠️ Devi inserire il tuo nome prima di inviare un messaggio. Inseriscilo nel campo 'Il tuo nome' in alto.")
                st.stop()
            
            # Verifica che il messaggio non sia vuoto
            if message.strip():
                # Sanitizza il messaggio per sicurezza
                message_clean = re.sub(r'<.*?>', '', message)

                try:
                    # Prepara i dati del messaggio
                    message_data = {
                        "nickname": nickname,
                        "message": message_clean,
                        "regione": regione_msg,
                        "user_id": st.session_state.user_id,
                        "is_emergency": is_emergency,
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
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 Aggiorna messaggi", key="refresh"):
                # Ricarica i messaggi senza tentare di invalidare la cache
                # dalla funzione (che non è una funzione di cache Streamlit)
                st.rerun()

        with col2:
            st.write("Ultimo aggiornamento: " + datetime.now(FUSO_ORARIO_ITALIA).strftime("%H:%M:%S") + " (IT)")

        st.info("I messaggi non si aggiornano automaticamente. Clicca 'Aggiorna messaggi' per caricare i nuovi messaggi.")

    with tab2:
        st.subheader("🗺️ Mappa delle segnalazioni")

        # Mappa con folium per visualizzare i messaggi geolocalizzati
        try:
            import folium
            from streamlit_folium import folium_static

            # Recupera i messaggi con coordinate per la mappa
            response = supabase.table("chat_messages").select("*") \
                              .not_.is_("lat", "null") \
                              .not_.is_("lon", "null") \
                              .order("timestamp", desc=True) \
                              .limit(100) \
                              .execute()

            geo_messages = response.data if hasattr(response, 'data') else []

            # Crea la mappa centrata sull'Italia
            m = folium.Map(location=[42.0, 12.0], zoom_start=5.5)

            # Aggiungi marker per ogni messaggio
            for msg in geo_messages:
                if "lat" in msg and "lon" in msg and msg["lat"] and msg["lon"]:
                    # Determina il colore del marker in base al tipo di messaggio
                    color = "red" if msg.get("is_emergency", False) else "blue"

                    # Formatta il timestamp
                    try:
                        ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                        timestamp_str = ts.strftime("%d/%m/%Y %H:%M")
                    except:
                        timestamp_str = msg.get("timestamp", "Data sconosciuta")

                    # Crea popup con informazioni
                    popup_html = f"""
                    <div style="width:200px">
                    <b>{msg["nickname"]}</b> ({timestamp_str})<br>
                    <i>{msg["regione"]}</i><br>
                    {msg["message"]}
                    </div>
                    """

                    # Aggiungi il marker
                    folium.Marker(
                        location=[msg["lat"], msg["lon"]],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{msg['nickname']} - {msg['regione']}",
                        icon=folium.Icon(color=color)
                    ).add_to(m)

            # Mostra la mappa
            if geo_messages:
                folium_static(m, width=700)
                st.caption("Mappa delle segnalazioni con geolocalizzazione")
            else:
                st.info("Nessun messaggio con informazioni di geolocalizzazione disponibile.")
                st.write("I messaggi appariranno sulla mappa quando gli utenti condivideranno la propria posizione.")

        except Exception as e:
            st.error(f"Errore nella visualizzazione della mappa: {e}")

    with tab3:
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

        ### Funzionalità avanzate
        - **Nome utente**: È necessario inserire il tuo nome nelle impostazioni in alto prima di inviare messaggi
        - **Filtro per regione**: Seleziona una regione specifica per visualizzare solo i messaggi relativi
        - **Geolocalizzazione**: Se consenti l'accesso alla tua posizione, questa verrà associata ai tuoi messaggi per visualizzarli sulla mappa
        - **Segnalazioni di emergenza**: Utilizza l'opzione "Segnala come emergenza" solo per situazioni di reale pericolo o allerta
        - **Mappa delle segnalazioni**: Visualizza la distribuzione geografica dei messaggi con coordinate associate
        - **Aggiornamento manuale**: I messaggi non si aggiornano automaticamente, usa il pulsante "Aggiorna messaggi"

        Per segnalazioni tecniche o problemi relativi alla chat, contatta l'amministratore del sistema.
        """)