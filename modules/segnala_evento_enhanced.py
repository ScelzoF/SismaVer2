"""
Modulo di segnalazione eventi migliorato con:
- Integrazione con Supabase
- Sistema di moderazione multi-livello
- Visualizzazione cronologica migliorata
- Supporto posizione precisa con mappa
"""
import streamlit as st
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import os
import json
import uuid
import time

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

# Importa client Supabase se disponibile
try:
    from supabase import create_client, Client
    supabase_available = True
except ImportError:
    supabase_available = False

def show():
    st.title('📢 Segnalazione Eventi')
    
    # Gestione utente e identificativo unico persistente
    if "user_id" not in st.session_state:
        # Genera ID utente univoco e persistente per questa sessione
        st.session_state.user_id = str(uuid.uuid4())
    
    if "moderazione_attiva" not in st.session_state:
        st.session_state.moderazione_attiva = "standard"  # Opzioni: "leggera", "standard", "severa"
    
    # Visualizziamo i due tab: Segnala e Visualizza
    tab1, tab2, tab3 = st.tabs(["✏️ Segnala evento", "🔍 Visualizza segnalazioni", "🔒 Impostazioni"])
    
    with tab1:
        st.write('Usa questo modulo per segnalare eventi sismici o situazioni di emergenza nella tua zona.')
        
        # Inizializza connessione Supabase se disponibile
        supabase = None
        if supabase_available:
            supabase_url = os.environ.get("SUPABASE_URL", "https://hqrdtuktmkemaitrusxw.supabase.co")
            supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhxcmR0dWt0bWtlbWFpdHJ1c3h3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2Mzc2NDMsImV4cCI6MjA1ODIxMzY0M30.SDYaTicz0dWnocfa6oB7_QhB5f3ExRLTaCqtAHkQUgE")
            
            if supabase_url and supabase_key:
                try:
                    supabase = create_client(supabase_url, supabase_key)
                    st.success("✅ Connesso a Supabase per la persistenza dei dati")
                except Exception as e:
                    st.error(f"Errore nella connessione a Supabase: {e}")
            else:
                st.info("⚠️ Configurazione Supabase non disponibile. Le segnalazioni saranno salvate localmente.")
        
        with st.form("segnalazione_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tipo = st.selectbox(
                    "Tipo di evento",
                    ["Terremoto", "Frana", "Alluvione", "Incendio", "Emergenza sanitaria", "Rischio idrogeologico", "Altro"],
                    key="tipo_evento",
                    label_visibility="visible"
                )
                
                # Nuova selezione per gravità
                gravita = st.select_slider(
                    "Gravità dell'evento",
                    options=["Basso", "Medio", "Alto", "Critico"],
                    value="Medio",
                    key="gravita_evento",
                    label_visibility="visible"
                )
                
                # Selezione regione e comune
                regioni_italiane = [
                    "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
                    "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
                    "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige",
                    "Umbria", "Valle d'Aosta", "Veneto"
                ]
                
                regione = st.selectbox("Regione", regioni_italiane, index=0)
                comune = st.text_input("Comune", placeholder="Inserisci il comune")
                
            with col2:
                data = st.date_input("Data evento", value=datetime.now(), format="DD/MM/YYYY")
                ora = st.time_input("Ora evento", value=datetime.now().time())
                
                # Permette inserimento contatto (opzionale)
                contatto = st.text_input(
                    "Contatto (opzionale)",
                    placeholder="Email o numero di telefono per verifiche",
                    help="Sarà visibile solo ai moderatori e potrà essere usato per verificare la segnalazione"
                )
            
            # Campo descrizione a larghezza piena
            descrizione = st.text_area(
                "Descrizione",
                placeholder="Descrivi brevemente l'evento, la situazione e gli effetti osservati...",
                height=120
            )
            
            # Geolocalizzazione
            try:
                coords = streamlit_js_eval(
                    js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
                    key="geo_segnalazioni"
                )
                
                if coords and isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                    st.success(f"📍 Posizione rilevata: {coords['lat']:.4f}, {coords['lon']:.4f}")
                else:
                    st.warning("⚠️ Posizione non disponibile. La segnalazione avrà meno precisione.")
                    coords = None
            except:
                st.warning("⚠️ Impossibile ottenere la posizione. Assicurati di permettere l'accesso alla geolocalizzazione.")
                coords = None
            
            invia = st.form_submit_button("📤 Invia segnalazione")
        
        if invia:
            # Verifica permessi utente
            permesso, messaggio_permesso = verifica_permesso_utente(st.session_state.user_id, "segnala_evento")
            if not permesso:
                st.error(f"⚠️ {messaggio_permesso}")
                st.stop()
            elif messaggio_permesso:
                st.warning(messaggio_permesso)
            
            # Validazione campi
            if not descrizione or not comune:
                st.error("⚠️ Descrizione e Comune sono campi obbligatori.")
                st.stop()
            
            # Applica il sistema di moderazione integrato
            description_to_send, bloccato, motivo_moderazione, metadata = integra_moderazione_contenuto(
                user_id=st.session_state.user_id,
                testo=descrizione,
                livello_moderazione=st.session_state.moderazione_attiva,
                tipo_contenuto="segnalazione"
            )
            
            # Se il contenuto è completamente bloccato
            if bloccato:
                st.error(f"⚠️ La segnalazione non può essere inviata: {motivo_moderazione}")
                st.stop()
            
            # Estrai informazioni dalla moderazione
            is_moderated = metadata.get("moderated", False)
            moderation_level = metadata.get("moderation_type", "")
            moderation_score = metadata.get("moderation_score", 0.0)
            original_description = metadata.get("original_text", descrizione)
            
            # Mostra avviso se è stato moderato ma non bloccato
            if is_moderated and motivo_moderazione:
                st.warning(f"⚠️ {motivo_moderazione}")
            
            # Formatta i dati dell'evento
            data_ora = datetime.combine(data, ora)
            
            # Salva i dati dell'evento
            if supabase is not None:
                try:
                    # Prepara i dati per Supabase
                    segnalazione_data = {
                        "tipo": tipo,
                        "descrizione": description_to_send,
                        "data_ora": data_ora.isoformat(),
                        "regione": regione,
                        "comune": comune,
                        "gravita": gravita,
                        "user_id": st.session_state.user_id,
                        "contatto": contatto if contatto else None,
                        "is_moderated": is_moderated,
                        "moderation_level": moderation_level,
                        "moderation_score": moderation_score,
                    }
                    
                    # Aggiungi la descrizione originale se è stata moderata
                    if is_moderated:
                        segnalazione_data["original_description"] = original_description
                    
                    # Aggiungi coordinate se disponibili
                    if coords and isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                        segnalazione_data["lat"] = coords["lat"]
                        segnalazione_data["lon"] = coords["lon"]
                    
                    # Invia a Supabase
                    response = supabase.table("event_reports").insert(segnalazione_data).execute()
                    
                    if hasattr(response, 'error') and response.error:
                        st.error(f"Errore nel salvataggio: {response.error}")
                        # Fallback a salvataggio locale
                        salva_locale(tipo, description_to_send, data, ora, coords, gravita, regione, comune, contatto)
                    else:
                        if is_moderated:
                            st.success("Segnalazione salvata con moderazione automatica!")
                        else:
                            st.success("Segnalazione salvata con successo!")
                        
                except Exception as e:
                    st.error(f"Errore nell'invio a Supabase: {e}")
                    # Fallback a salvataggio locale
                    salva_locale(tipo, description_to_send, data, ora, coords, gravita, regione, comune, contatto)
            else:
                # Salvataggio locale
                salva_locale(tipo, description_to_send, data, ora, coords, gravita, regione, comune, contatto)
                if is_moderated:
                    st.success("Segnalazione salvata localmente con moderazione automatica!")
                else:
                    st.success("Segnalazione salvata localmente!")
            
            # Visualizza bottone per tornare alla lista
            if st.button("Visualizza tutte le segnalazioni"):
                st.session_state.view_tab = "segnalazioni"
                st.rerun()
    
    with tab2:
        st.write("### 🗒️ Segnalazioni recenti")
        
        # Filtri per le segnalazioni
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro per tipo di evento
            tipi_eventi = ["Tutti i tipi", "Terremoto", "Frana", "Alluvione", "Incendio", "Emergenza sanitaria", "Rischio idrogeologico", "Altro"]
            filtro_tipo = st.selectbox("Filtra per tipo", tipi_eventi)
        
        with col2:
            # Filtro per regione
            regioni_filtro = ["Tutte le regioni", "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
                             "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
                             "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige",
                             "Umbria", "Valle d'Aosta", "Veneto"]
            filtro_regione = st.selectbox("Filtra per regione", regioni_filtro)
        
        with col3:
            # Filtro per gravità
            gravita_filtro = ["Tutte", "Basso", "Medio", "Alto", "Critico"]
            filtro_gravita = st.selectbox("Filtra per gravità", gravita_filtro)
        
        # Aggiunge un refresh button
        if st.button("🔄 Aggiorna segnalazioni"):
            st.rerun()
        
        # Se disponibile Supabase, carica da lì, altrimenti da file locale
        if supabase_available:
            try:
                supabase_url = os.environ.get("SUPABASE_URL", "https://hqrdtuktmkemaitrusxw.supabase.co")
                supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhxcmR0dWt0bWtlbWFpdHJ1c3h3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2Mzc2NDMsImV4cCI6MjA1ODIxMzY0M30.SDYaTicz0dWnocfa6oB7_QhB5f3ExRLTaCqtAHkQUgE")
                
                if supabase_url and supabase_key:
                    try:
                        supabase = create_client(supabase_url, supabase_key)
                        
                        # Verifica che la tabella esista prima di usarla
                        try:
                            # Costruisci la query con i filtri
                            query = supabase.table("event_reports").select("*").order("data_ora", desc=True)
                            
                            # Applica filtri se selezionati
                            if filtro_tipo != "Tutti i tipi":
                                query = query.eq("tipo", filtro_tipo)
                            
                            if filtro_regione != "Tutte le regioni":
                                query = query.eq("regione", filtro_regione)
                            
                            if filtro_gravita != "Tutte":
                                query = query.eq("gravita", filtro_gravita)
                            
                            # Esegui la query
                            response = query.limit(50).execute()
                            
                            # Processa i risultati
                            if hasattr(response, 'data') and response.data:
                                segnalazioni = response.data
                                st.success(f"Caricate {len(segnalazioni)} segnalazioni da Supabase")
                                
                                # Importa Folium per la mappa
                                try:
                                    import folium
                                    from streamlit_folium import folium_static
                                    from folium.plugins import MarkerCluster
                                    
                                    # Filtra segnalazioni con coordinate
                                    geo_events = [e for e in segnalazioni 
                                               if e.get("lat") is not None and e.get("lon") is not None]
                                    
                                    if geo_events:
                                        st.subheader("🗺️ Mappa delle segnalazioni")
                                        
                                        # Calcola il centro della mappa come media delle coordinate
                                        avg_lat = sum([e["lat"] for e in geo_events]) / len(geo_events)
                                        avg_lon = sum([e["lon"] for e in geo_events]) / len(geo_events)
                                        
                                        # Crea mappa
                                        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
                                        
                                        # Aggiungi cluster di marker
                                        marker_cluster = MarkerCluster().add_to(m)
                                        
                                        # Mappa gravità a colori
                                        gravita_colors = {
                                            "Basso": "green",
                                            "Medio": "blue",
                                            "Alto": "orange",
                                            "Critico": "red"
                                        }
                                        
                                        # Aggiungi marker per ogni segnalazione
                                        for e in geo_events:
                                            try:
                                                ts = datetime.fromisoformat(e["data_ora"].replace("Z", "+00:00"))
                                                timestamp_str = ts.strftime("%d/%m/%Y %H:%M")
                                            except:
                                                timestamp_str = str(e.get("data_ora", "Data sconosciuta"))
                                            
                                            # Personalizza l'icona in base alla gravità
                                            icon_color = gravita_colors.get(e.get("gravita", "Medio"), "blue")
                                            
                                            # Aggiungi marker al cluster
                                            folium.Marker(
                                                [e["lat"], e["lon"]],
                                                popup=f"""<b>{e["tipo"]}</b> ({e["gravita"]})<br>
                                                       {e["comune"]}, {e["regione"]}<br>
                                                       {timestamp_str}<br>
                                                       {e["descrizione"]}""",
                                                tooltip=f"{e['tipo']} - {e['comune']}",
                                                icon=folium.Icon(color=icon_color, icon="info-sign", prefix="fa")
                                            ).add_to(marker_cluster)
                                        
                                        # Mostra la mappa
                                        folium_static(m, width=700)
                                
                                except ImportError:
                                    st.warning("📦 Librerie per mappe non installate (folium, streamlit-folium)")
                                
                                # Tabella segnalazioni
                                st.subheader("📋 Elenco segnalazioni")
                                
                                # Converti in DataFrame per visualizzazione
                                df_segnalazioni = pd.DataFrame(segnalazioni)
                                
                                # Formatta le date per visualizzazione
                                if "data_ora" in df_segnalazioni.columns:
                                    df_segnalazioni["data_ora"] = pd.to_datetime(df_segnalazioni["data_ora"])
                                    df_segnalazioni["data_ora"] = df_segnalazioni["data_ora"].dt.strftime("%d/%m/%Y %H:%M")
                                
                                # Seleziona e riordina colonne per visualizzazione
                                display_columns = ["tipo", "gravita", "comune", "regione", "data_ora", "descrizione"]
                                display_columns = [col for col in display_columns if col in df_segnalazioni.columns]
                                
                                # Rinomina colonne per visualizzazione
                                column_names = {
                                    "tipo": "Tipo",
                                    "gravita": "Gravità",
                                    "comune": "Comune",
                                    "regione": "Regione",
                                    "data_ora": "Data e ora",
                                    "descrizione": "Descrizione"
                                }
                                
                                # Mostra dataframe
                                st.dataframe(
                                    df_segnalazioni[display_columns].rename(columns=column_names),
                                    use_container_width=True,
                                    hide_index=True
                                )
                            else:
                                st.info("Nessuna segnalazione trovata con i filtri selezionati.")
                                # Fallback al caricamento locale
                                carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
                        
                        except Exception as e:
                            st.warning(f"Errore nell'accesso alla tabella event_reports: {e}")
                            st.info("Creazione automatica della tabella in corso...")
                            
                            # Suggerisci la creazione della tabella
                            st.code("""
CREATE TABLE public.event_reports (
    id BIGSERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,
    descrizione TEXT NOT NULL,
    data_ora TIMESTAMPTZ DEFAULT NOW(),
    regione TEXT NOT NULL,
    comune TEXT NOT NULL,
    gravita TEXT DEFAULT 'Medio',
    lat FLOAT,
    lon FLOAT,
    user_id TEXT,
    contatto TEXT,
    is_moderated BOOLEAN DEFAULT false,
    moderation_level TEXT,
    moderation_score FLOAT,
    original_description TEXT
);

-- Indici per migliorare le performance
CREATE INDEX idx_event_reports_data_ora ON public.event_reports(data_ora);
CREATE INDEX idx_event_reports_regione ON public.event_reports(regione);
CREATE INDEX idx_event_reports_tipo ON public.event_reports(tipo);
CREATE INDEX idx_event_reports_gravita ON public.event_reports(gravita);
                            """, language="sql")
                            
                            # Fallback al caricamento locale
                            carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
                    
                    except Exception as e:
                        st.error(f"Errore nella connessione a Supabase: {e}")
                        # Fallback al caricamento locale
                        carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
                else:
                    # Fallback al caricamento locale
                    carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
            
            except Exception as e:
                st.error(f"Errore nell'inizializzazione di Supabase: {e}")
                # Fallback al caricamento locale
                carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
        else:
            # Se Supabase non è disponibile, carica segnalazioni locali
            carica_segnalazioni_locali(filtro_tipo, filtro_regione, filtro_gravita)
    
    with tab3:
        # Sezione impostazioni
        st.subheader("🔒 Sistema di moderazione")
        
        # Spiegazione dei livelli di moderazione
        st.markdown("""
        SismaVer2 utilizza un sistema di moderazione multi-livello per mantenere le segnalazioni accurate e sicure:
        
        1. **Moderazione automatica**: Filtra linguaggio inappropriato e contenuti sensibili
        2. **Moderazione AI** (se disponibile): Analisi avanzata dei contenuti potenzialmente problematici
        3. **Verifica manuale**: Segnalazioni critiche possono essere verificate dal team di moderazione
        """)
        
        # Impostiamo sempre il livello su severo senza possibilità di modifica
        st.session_state.moderazione_attiva = "severo"
        
        st.success(f"Il sistema di moderazione è impostato al livello massimo (severo) per garantire segnalazioni accurate e sicure.")
        
        # Spiegazione del livello severo
        st.markdown("""
        Il livello **Severo** garantisce:
        - Moderazione rigorosa di ogni segnalazione
        - Rilevamento avanzato di contenuti inappropriati
        - Protezione completa contro false segnalazioni
        - Verifica automatica dell'affidabilità del contenuto
        - Monitoraggio continuo dei comportamenti utente
        """)
        

        
        st.info("Nota: Le segnalazioni che violano le linee guida possono essere moderate o bloccate dal sistema automatico.")
        
        # Informazioni sulla persistenza dati
        st.subheader("💾 Persistenza dati")
        
        st.markdown("""
        SismaVer2 offre due modalità di salvataggio delle segnalazioni:
        
        1. **Persistenza online**: Le segnalazioni vengono salvate nel database Supabase e sono accessibili da qualsiasi dispositivo
        2. **Salvataggio locale**: Backup automatico delle segnalazioni sul dispositivo in uso (fallback)
        """)
        
        if supabase_available:
            st.success("✅ Persistenza online configurata correttamente")
        else:
            st.warning("⚠️ Persistenza online non disponibile. Le segnalazioni vengono salvate solo localmente.")

def salva_locale(tipo, descrizione, data, ora, coords, gravita="Medio", regione="", comune="", contatto=""):
    """Salva la segnalazione in un file locale con i nuovi campi"""
    # Formato data e ora
    data_str = data.strftime("%Y-%m-%d")
    ora_str = ora.strftime("%H:%M")
    
    # Crea un ID univoco per la segnalazione
    event_id = f"local_{int(time.time())}_{hash(descrizione) % 10000}"
    
    # Crea un dizionario con tutti i dettagli
    segnalazione = {
        "id": event_id,
        "tipo": tipo,
        "descrizione": descrizione,
        "data": data_str,
        "ora": ora_str,
        "data_ora": f"{data_str} {ora_str}",
        "gravita": gravita,
        "regione": regione,
        "comune": comune,
        "contatto": contatto,
        "timestamp": datetime.now().isoformat()
    }
    
    # Aggiungi coordinate se disponibili
    if coords and isinstance(coords, dict) and "lat" in coords and "lon" in coords:
        segnalazione["lat"] = coords["lat"]
        segnalazione["lon"] = coords["lon"]
    
    # Carica segnalazioni esistenti
    segnalazioni = []
    try:
        if os.path.exists("data/segnalazioni.json"):
            with open("data/segnalazioni.json", "r") as f:
                segnalazioni = json.load(f)
    except Exception as e:
        st.error(f"Errore nel caricamento delle segnalazioni esistenti: {e}")
    
    # Assicura che segnalazioni sia una lista
    if not isinstance(segnalazioni, list):
        segnalazioni = []
    
    # Aggiungi la nuova segnalazione
    segnalazioni.append(segnalazione)
    
    # Salva il file aggiornato
    try:
        # Crea la directory se non esiste
        os.makedirs("data", exist_ok=True)
        
        with open("data/segnalazioni.json", "w") as f:
            json.dump(segnalazioni, f, indent=2)
            
        st.success("✅ Segnalazione salvata localmente")
        return True
    except Exception as e:
        st.error(f"⚠️ Errore nel salvataggio: {e}")
        return False

def carica_segnalazioni_locali(filtro_tipo="Tutti i tipi", filtro_regione="Tutte le regioni", filtro_gravita="Tutte"):
    """Carica e visualizza le segnalazioni salvate localmente con supporto filtri"""
    try:
        if os.path.exists("data/segnalazioni.json"):
            with open("data/segnalazioni.json", "r") as f:
                segnalazioni = json.load(f)
            
            # Verifica che segnalazioni sia una lista
            if not isinstance(segnalazioni, list):
                st.warning("Il file delle segnalazioni non è nel formato corretto.")
                return
            
            # Applica filtri
            if filtro_tipo != "Tutti i tipi":
                segnalazioni = [s for s in segnalazioni if s.get("tipo") == filtro_tipo]
            
            if filtro_regione != "Tutte le regioni":
                segnalazioni = [s for s in segnalazioni if s.get("regione") == filtro_regione]
            
            if filtro_gravita != "Tutte":
                segnalazioni = [s for s in segnalazioni if s.get("gravita") == filtro_gravita]
            
            if not segnalazioni:
                st.info("Nessuna segnalazione trovata con i filtri selezionati.")
                return
            
            # Ordina per data e ora (più recenti prima)
            try:
                segnalazioni.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            except:
                pass  # In caso di errore nell'ordinamento, mantieni l'ordine originale
            
            st.success(f"Caricate {len(segnalazioni)} segnalazioni locali")
            
            # Importa Folium per la mappa
            try:
                import folium
                from streamlit_folium import folium_static
                from folium.plugins import MarkerCluster
                
                # Filtra segnalazioni con coordinate
                geo_events = [e for e in segnalazioni 
                           if "lat" in e and "lon" in e and e["lat"] is not None and e["lon"] is not None]
                
                if geo_events:
                    st.subheader("🗺️ Mappa delle segnalazioni locali")
                    
                    # Calcola il centro della mappa come media delle coordinate
                    avg_lat = sum([e["lat"] for e in geo_events]) / len(geo_events)
                    avg_lon = sum([e["lon"] for e in geo_events]) / len(geo_events)
                    
                    # Crea mappa
                    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
                    
                    # Aggiungi cluster di marker
                    marker_cluster = MarkerCluster().add_to(m)
                    
                    # Mappa gravità a colori
                    gravita_colors = {
                        "Basso": "green",
                        "Medio": "blue",
                        "Alto": "orange",
                        "Critico": "red"
                    }
                    
                    # Aggiungi marker per ogni segnalazione
                    for e in geo_events:
                        # Personalizza l'icona in base alla gravità
                        icon_color = gravita_colors.get(e.get("gravita", "Medio"), "blue")
                        
                        # Aggiungi marker al cluster
                        folium.Marker(
                            [e["lat"], e["lon"]],
                            popup=f"""<b>{e["tipo"]}</b> ({e.get("gravita", "Medio")})<br>
                                   {e.get("comune", "")}, {e.get("regione", "")}<br>
                                   {e.get("data_ora", "")}<br>
                                   {e["descrizione"]}""",
                            tooltip=f"{e['tipo']} - {e.get('comune', 'Località')}",
                            icon=folium.Icon(color=icon_color, icon="info-sign", prefix="fa")
                        ).add_to(marker_cluster)
                    
                    # Mostra la mappa
                    folium_static(m, width=700)
            
            except ImportError:
                st.warning("📦 Librerie per mappe non installate (folium, streamlit-folium)")
            
            # Visualizza come DataFrame per tabella organizzata
            df_segnalazioni = pd.DataFrame(segnalazioni)
            
            # Seleziona colonne da mostrare
            display_columns = ["tipo", "gravita", "comune", "regione", "data_ora", "descrizione"]
            display_columns = [col for col in display_columns if col in df_segnalazioni.columns]
            
            # Rinomina colonne per visualizzazione
            column_names = {
                "tipo": "Tipo",
                "gravita": "Gravità",
                "comune": "Comune",
                "regione": "Regione",
                "data_ora": "Data e ora",
                "descrizione": "Descrizione"
            }
            
            # Se manca data_ora ma ci sono data e ora, combinale
            if "data_ora" not in df_segnalazioni.columns and "data" in df_segnalazioni.columns and "ora" in df_segnalazioni.columns:
                df_segnalazioni["data_ora"] = df_segnalazioni["data"] + " " + df_segnalazioni["ora"]
                if "data_ora" not in display_columns:
                    display_columns.append("data_ora")
            
            # Colonne da visualizzare
            available_columns = [col for col in display_columns if col in df_segnalazioni.columns]
            
            # Mostra dataframe
            if not available_columns:
                st.error("Nessuna colonna valida disponibile per la visualizzazione.")
            else:
                st.dataframe(
                    df_segnalazioni[available_columns].rename(columns={col: column_names.get(col, col) for col in available_columns}),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Nessuna segnalazione locale disponibile.")
    
    except Exception as e:
        st.error(f"⚠️ Errore nel caricamento delle segnalazioni: {e}")
        st.info("Se il problema persiste, prova a creare manualmente la directory 'data' e un file 'segnalazioni.json' vuoto con [].")