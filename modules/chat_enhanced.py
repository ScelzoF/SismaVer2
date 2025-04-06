"""
Modulo di chat pubblica SismaVer2 migliorato con:
- Auto-aggiornamento in tempo reale
- Sistema di moderazione multi-livello (base, AI, comportamentale)
- Organizzazione storico avanzata
- Integrazione Supabase ottimizzata
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import time
import re
import uuid
import os
import json
from streamlit_js_eval import streamlit_js_eval

# Importa modulo di moderazione
try:
    from modules.moderation_utils import (
        integra_moderazione_contenuto,
        filtra_contenuto_vietato, 
        modera_con_ai, 
        traccia_comportamento_utente,
        verifica_permesso_utente,
        detect_identical_content,
        check_rate_limiting
    )
except ImportError:
    st.error("⚠️ Modulo di moderazione non disponibile. Funzionalità di moderazione limitate.")
    # Implementazione fallback semplificata
    def integra_moderazione_contenuto(user_id, testo, livello_moderazione="standard", tipo_contenuto="messaggio"):
        return testo, False, "", {"moderated": False}
    
    def filtra_contenuto_vietato(testo, livello="standard"):
        return testo, False, ""
    
    def modera_con_ai(testo, user_id=None, use_cache=True):
        return True, 0.0, "non disponibile", testo
    
    def traccia_comportamento_utente(user_id, azione, gravita=0):
        return {"livello_restrizione": "nessuno"}
    
    def verifica_permesso_utente(user_id, azione):
        return True, ""
        
    def detect_identical_content(user_id, content, content_type="messaggio"):
        return False, ""
        
    def check_rate_limiting(user_id, action_type):
        return True, ""

# Configura il fuso orario italiano
ora_legale = True  # Imposta manualmente in base al periodo dell'anno
FUSO_ORARIO_ITALIA = timezone(timedelta(hours=2 if ora_legale else 1))

def show():
    st.title("💬 Chat Pubblica - SismaVer2")
    
    # Import Supabase
    try:
        from supabase import create_client, Client
    except ImportError:
        st.error("📦 Libreria Supabase non installata")
        st.info("Esegui 'pip install supabase' per installare la libreria")
        return

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
            st.info("Per attivare la chat, è necessario configurare le credenziali Supabase.")
            
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
    is_emergency BOOLEAN DEFAULT false,
    is_moderated BOOLEAN DEFAULT false,
    moderation_level TEXT,
    moderation_score FLOAT,
    original_message TEXT
);

-- Indici per migliorare le performance
CREATE INDEX idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX idx_chat_messages_regione ON public.chat_messages(regione);
CREATE INDEX idx_chat_messages_user_id ON public.chat_messages(user_id);
CREATE INDEX idx_chat_messages_is_emergency ON public.chat_messages(is_emergency);

-- Tabella per la moderazione della chat
CREATE TABLE public.chat_moderation (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    infraction_score FLOAT DEFAULT 0,
    infractions_count INTEGER DEFAULT 0,
    last_infraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    restriction_level TEXT DEFAULT 'none',
    notes TEXT
);

CREATE INDEX idx_chat_moderation_user_id ON public.chat_moderation(user_id);

-- Politiche di sicurezza Row Level Security (RLS)
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_moderation ENABLE ROW LEVEL SECURITY;

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

-- Politiche per la tabella di moderazione
CREATE POLICY "Solo gli amministratori possono leggere moderazioni"
ON public.chat_moderation FOR SELECT
USING (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));

CREATE POLICY "Solo gli amministratori possono inserire moderazioni"
ON public.chat_moderation FOR INSERT
WITH CHECK (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));

CREATE POLICY "Solo gli amministratori possono aggiornare moderazioni"
ON public.chat_moderation FOR UPDATE
USING (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));
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
    is_emergency BOOLEAN DEFAULT false,
    is_moderated BOOLEAN DEFAULT false,
    moderation_level TEXT,
    moderation_score FLOAT,
    original_message TEXT
);
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
    
    # Gestione dello stato di autoaggiornamento
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False
    
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    if "moderazione_attiva" not in st.session_state:
        st.session_state.moderazione_attiva = "standard"  # Opzioni: "leggera", "standard", "severa"
    
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
        ordine_desc = st.checkbox("🔄 Ordine cronologico inverso", value=True)
    
    with col3:
        # Toggle per attivare/disattivare l'autoaggiornamento
        auto_refresh = st.checkbox("⏱️ Auto-aggiornamento", value=st.session_state.auto_refresh, 
                                help="Aggiorna automaticamente i messaggi ogni 15 secondi")
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
    
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
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🗺️ Mappa messaggi", "📋 Istruzioni", "🔒 Moderazione"])

    with tab1:
        # Container per i messaggi
        messages_container = st.container()

        # Funzione di caricamento messaggi senza cache
        def _load_messages_inner(regione_filtro="Tutte le regioni", limit=50, descending=True):
            """Funzione interna per caricare i messaggi da Supabase"""
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
        
        # Applica la cache alla funzione per poter usare load_messages.clear()
        load_messages = st.cache_data(ttl=15, show_spinner=False)(_load_messages_inner)

        # Verifica se è necessario un aggiornamento automatico
        current_time = time.time()
        if st.session_state.auto_refresh and (current_time - st.session_state.last_refresh) > 15:  # 15 secondi
            st.session_state.last_refresh = current_time
            # Forza l'invalidazione della cache
            load_messages.clear()
            st.rerun()

        # Visualizzazione messaggi
        with messages_container:
            messages = load_messages(regione_filtro, num_messaggi, ordine_desc)

            if not messages:
                st.info("📭 Nessun messaggio disponibile. Sii il primo a scrivere!")
            else:
                # Raggruppa messaggi per utente e vicini nel tempo
                grouped_messages = []
                current_group = None
                prev_user_id = None
                prev_nickname = None
                prev_regione = None
                prev_time = None
                
                for msg in messages:
                    # Formattazione timestamp
                    try:
                        ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                        timestamp_obj = ts
                        timestamp_str = ts.strftime("%d/%m/%Y %H:%M")
                    except:
                        timestamp_obj = datetime.now()
                        timestamp_str = msg.get("timestamp", "Data sconosciuta")
                    
                    current_user_id = msg.get("user_id", "")
                    current_nickname = msg.get("nickname", "")
                    current_regione = msg.get("regione", "")
                    is_emergency = msg.get("is_emergency", False)
                    
                    # Inizia un nuovo gruppo se:
                    # 1. È il primo messaggio
                    # 2. Il messaggio è di un utente diverso
                    # 3. È passato più di 5 minuti dall'ultimo messaggio dello stesso utente
                    # 4. La regione è diversa
                    # 5. Lo stato di emergenza è diverso
                    
                    time_diff = (timestamp_obj - prev_time).total_seconds() > 300 if prev_time else True
                    
                    # Verifica se è necessario creare un nuovo gruppo di messaggi
                    need_new_group = (
                        prev_user_id != current_user_id or 
                        prev_nickname != current_nickname or 
                        prev_regione != current_regione or 
                        time_diff or
                        current_group is None or
                        is_emergency != current_group.get("is_emergency", False)
                    )
                    
                    # Se serve un nuovo gruppo
                    if need_new_group:
                        # Salva il gruppo precedente se esiste
                        if current_group:
                            grouped_messages.append(current_group)
                        
                        # Crea un nuovo gruppo
                        current_group = {
                            "user_id": current_user_id,
                            "nickname": current_nickname,
                            "regione": current_regione,
                            "is_emergency": is_emergency,
                            "first_timestamp": timestamp_obj,
                            "last_timestamp": timestamp_obj,
                            "first_timestamp_str": timestamp_str,
                            "last_timestamp_str": timestamp_str,
                            "messages": []
                        }
                    
                    # Verifica se il messaggio è stato moderato
                    is_moderated = msg.get("is_moderated", False)
                    moderation_info = ""
                    if is_moderated:
                        moderation_level = msg.get("moderation_level", "")
                        if moderation_level:
                            moderation_info = f"[Moderato: {moderation_level}]"
                    
                    # Aggiungi il messaggio al gruppo corrente
                    current_group["messages"].append({
                        "text": msg["message"],
                        "timestamp": timestamp_obj,
                        "timestamp_str": timestamp_str,
                        "is_moderated": is_moderated,
                        "moderation_info": moderation_info
                    })
                    
                    # Aggiorna il timestamp dell'ultimo messaggio nel gruppo
                    current_group["last_timestamp"] = timestamp_obj
                    current_group["last_timestamp_str"] = timestamp_str
                    
                    # Aggiorna le variabili per il confronto con il prossimo messaggio
                    prev_user_id = current_user_id
                    prev_nickname = current_nickname
                    prev_regione = current_regione
                    prev_time = timestamp_obj
                
                # Aggiungi l'ultimo gruppo se esiste
                if current_group:
                    grouped_messages.append(current_group)
                
                # Visualizza i gruppi di messaggi
                for group in grouped_messages:
                    # Stile base per tutti i messaggi
                    background_color = "#f0f2f6"  # Default
                    border_color = "#e6e6e6"      # Default
                    
                    # Modifica lo stile per i messaggi di emergenza
                    if group["is_emergency"] and mostra_emergenze:
                        background_color = "#ffecec"  # Rosso chiaro
                        border_color = "#ff8080"      # Rosso più intenso
                    
                    # Determina se è un messaggio dell'utente corrente
                    is_own_message = group["user_id"] == st.session_state.user_id
                    if is_own_message:
                        background_color = "#e6f3ff"  # Blu chiaro per messaggi propri
                        border_color = "#b3d9ff"      # Blu più intenso
                    
                    # Informazioni sull'intestazione del gruppo
                    header = f"<strong>{group['nickname']}</strong> <small>({group['regione']}"
                    
                    # Aggiungi intervallo di tempo se più messaggi nello stesso gruppo
                    if len(group["messages"]) > 1:
                        header += f" - dal {group['first_timestamp_str']} al {group['last_timestamp_str']}"
                    else:
                        header += f" - {group['first_timestamp_str']}"
                    
                    header += ")</small>"
                    
                    if group["is_emergency"] and mostra_emergenze:
                        header += " 🚨"
                    
                    if is_own_message:
                        header += " (tu)"
                    
                    # Costruisci il contenuto dei messaggi
                    messages_content = ""
                    for i, msg in enumerate(group["messages"]):
                        # Mostra timestamp per ogni messaggio solo se ci sono più messaggi
                        time_info = ""
                        if len(group["messages"]) > 1:
                            time_info = f"<small style='color: #888;'>{msg['timestamp_str']}</small> "
                        
                        # Mostra info moderazione
                        mod_info = f"<small style='color: #666;'>{msg['moderation_info']}</small> " if msg['moderation_info'] else ""
                        
                        # Separatore tra messaggi
                        separator = "<hr style='margin: 5px 0; border-color: rgba(0,0,0,0.1);'>" if i > 0 else ""
                        
                        messages_content += f"{separator}<div>{time_info}{mod_info}{msg['text']}</div>"
                    
                    # Visualizzazione messaggi con stile personalizzato
                    st.markdown(
                        f"<div style='background-color:{background_color}; padding:10px; "
                        f"border-radius:5px; margin-bottom:10px; border-left:4px solid {border_color};'>"
                        f"{header}<br>{messages_content}</div>",
                        unsafe_allow_html=True)

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
            
            # Verifica permessi utente
            permesso, messaggio_permesso = verifica_permesso_utente(st.session_state.user_id, "invia_messaggio")
            if not permesso:
                st.error(f"⚠️ {messaggio_permesso}")
                st.stop()
            elif messaggio_permesso:
                st.warning(messaggio_permesso)
            
            # Verifica che il messaggio non sia vuoto
            if message.strip():
                # Applica il sistema di moderazione integrato
                message_to_send, bloccato, motivo_moderazione, metadata = integra_moderazione_contenuto(
                    user_id=st.session_state.user_id,
                    testo=message,
                    livello_moderazione=st.session_state.moderazione_attiva,
                    tipo_contenuto="messaggio"
                )
                
                # Se il contenuto è completamente bloccato
                if bloccato:
                    st.error(f"⚠️ Il messaggio non può essere inviato: {motivo_moderazione}")
                    st.stop()
                
                # Estrai informazioni dalla moderazione
                is_moderated = metadata.get("moderated", False)
                moderation_level = metadata.get("moderation_type", "")
                moderation_score = metadata.get("moderation_score", 0.0)
                original_message = metadata.get("original_text", message)
                
                # Mostra avviso se è stato moderato ma non bloccato
                if is_moderated and motivo_moderazione:
                    st.warning(f"⚠️ {motivo_moderazione}")
                
                try:
                    # Prepara i dati del messaggio
                    message_data = {
                        "nickname": nickname,
                        "message": message_to_send,
                        "regione": regione_msg,
                        "user_id": st.session_state.user_id,
                        "is_emergency": is_emergency,
                        "is_moderated": is_moderated,
                        "moderation_level": moderation_level,
                        "moderation_score": moderation_score,
                    }
                    
                    # Aggiungi il messaggio originale se è stato moderato
                    if is_moderated:
                        message_data["original_message"] = original_message
                    
                    # Aggiungi coordinate se disponibili
                    if coords and isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                        message_data["lat"] = coords["lat"]
                        message_data["lon"] = coords["lon"]

                    # Invia a Supabase
                    response = supabase.table("chat_messages").insert(message_data).execute()

                    if hasattr(response, 'error') and response.error:
                        st.error(f"Errore nell'invio: {response.error}")
                    else:
                        if is_moderated:
                            st.success("Messaggio inviato con moderazione automatica!")
                        else:
                            st.success("Messaggio inviato!")
                        # Invalidate cache to see new message
                        load_messages.clear()
                        time.sleep(0.5)
                        st.rerun()

                except Exception as e:
                    st.error(f"Errore nell'invio del messaggio: {e}")

        # Aggiornamento automatico
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 Aggiorna messaggi", key="refresh"):
                # Force cache invalidation
                load_messages.clear()
                st.session_state.last_refresh = time.time()
                st.rerun()

        with col2:
            refresh_status = "Attivo" if st.session_state.auto_refresh else "Disattivato"
            st.write(f"Auto-aggiornamento: {refresh_status}")
            st.write("Ultimo aggiornamento: " + datetime.now(FUSO_ORARIO_ITALIA).strftime("%H:%M:%S") + " (IT)")

        if st.session_state.auto_refresh:
            st.info("I messaggi si aggiornano ogni 15 secondi automaticamente.")
        else:
            st.info("Attiva l'auto-aggiornamento per vedere i nuovi messaggi in tempo reale.")

    with tab2:
        # Mappa delle chat
        st.subheader("🗺️ Distribuzione messaggi")
        
        # Importa Folium per la mappa
        try:
            import folium
            from streamlit_folium import folium_static
            from folium.plugins import MarkerCluster
            
            # Filtra messaggi con coordinate
            geo_messages = [m for m in load_messages(regione_filtro="Tutte le regioni", limit=200) 
                          if m.get("lat") is not None and m.get("lon") is not None]
            
            if not geo_messages:
                st.info("Nessun messaggio con posizione disponibile")
            else:
                # Calcola il centro della mappa come media delle coordinate
                avg_lat = sum([m["lat"] for m in geo_messages]) / len(geo_messages)
                avg_lon = sum([m["lon"] for m in geo_messages]) / len(geo_messages)
                
                # Crea mappa
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
                
                # Aggiungi cluster di marker
                marker_cluster = MarkerCluster().add_to(m)
                
                # Aggiungi marker per ogni messaggio
                for msg in geo_messages:
                    ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                    timestamp_str = ts.strftime("%d/%m/%Y %H:%M")
                    
                    # Personalizza l'icona in base al tipo di messaggio
                    icon_color = "red" if msg.get("is_emergency") else "blue"
                    icon_name = "exclamation" if msg.get("is_emergency") else "info-sign"
                    
                    # Aggiungi marker al cluster
                    folium.Marker(
                        [msg["lat"], msg["lon"]],
                        popup=f"<b>{msg['nickname']}</b><br>{msg['regione']} - {timestamp_str}<br>{msg['message']}",
                        tooltip=f"{msg['nickname']} - {msg['regione']}",
                        icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                    ).add_to(marker_cluster)
                
                # Mostra la mappa
                folium_static(m, width=700)
                
                st.info(f"Visualizzati {len(geo_messages)} messaggi con posizione")
        
        except ImportError:
            st.error("📦 Librerie per mappe non installate (folium, streamlit-folium)")
            st.info("Esegui 'pip install folium streamlit-folium' per attivare questa funzionalità")

    with tab3:
        # Istruzioni
        st.subheader("📋 Istruzioni per la chat")
        
        st.markdown("""
        ### Come usare la chat pubblica
        
        1. **Inserisci il tuo nome** nel campo 'Il tuo nome' in alto
        2. **Seleziona la tua regione** dal menu a discesa quando scrivi un messaggio
        3. **Scrivi il tuo messaggio** nel campo di testo
        4. **Attiva l'opzione 'Segnala come emergenza'** solo per comunicazioni urgenti
        5. **Clicca 'Invia messaggio'** per pubblicare il tuo messaggio
        
        ### Funzionalità aggiuntive
        
        - **Filtra per regione**: Visualizza solo i messaggi relativi a una specifica regione
        - **Evidenzia emergenze**: Mette in risalto le segnalazioni di emergenza
        - **Numero messaggi**: Regola il numero di messaggi visualizzati
        - **Ordine cronologico**: Cambia l'ordine di visualizzazione dei messaggi
        - **Auto-aggiornamento**: Attiva l'aggiornamento automatico ogni 15 secondi
        
        ### Linee guida per l'utilizzo
        
        - Sii rispettoso verso gli altri utenti
        - Condividi solo informazioni veritiere e verificabili
        - Usa la funzione 'Emergenza' solo per situazioni realmente urgenti
        - Non condividere dati personali sensibili
        - Segnala eventuali abusi all'indirizzo meteotorre@gmail.com
        """)
        
    with tab4:
        # Sezione moderazione
        st.subheader("🔒 Sistema di moderazione")
        
        # Spiegazione dei livelli di moderazione
        st.markdown("""
        SismaVer2 utilizza un sistema di moderazione multi-livello per mantenere la chat sicura e rispettosa:
        
        1. **Moderazione automatica**: Filtra linguaggio inappropriato e contenuti sensibili
        2. **Moderazione AI** (se disponibile): Analisi avanzata dei contenuti potenzialmente problematici
        3. **Tracciamento comportamentale**: Monitora e limita comportamenti problematici ripetuti
        """)
        
        # Impostiamo sempre il livello su severo senza possibilità di modifica
        st.session_state.moderazione_attiva = "severo"
        
        st.success(f"Il sistema di moderazione è impostato al livello massimo (severo) per garantire una comunicazione sicura e rispettosa.")
        
        # Spiegazione del livello severo
        st.markdown("""
        Il livello **Severo** garantisce:
        - Moderazione rigorosa di ogni messaggio
        - Rilevamento avanzato di contenuti inappropriati
        - Protezione completa contro spam e abusi
        - Blocco automatico di parole e frasi potenzialmente offensive
        - Monitoraggio continuo dei comportamenti utente
        """)
        
        st.info("Nota: I messaggi che violano le linee guida possono essere moderati o bloccati dal sistema automatico.")