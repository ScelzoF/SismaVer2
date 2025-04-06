import streamlit as st
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import os
import json
from supabase import create_client, Client


def show():
    st.title('📢 Segnalazione Eventi')
    
    # Visualizziamo i due tab: Segnala e Visualizza
    tab1, tab2 = st.tabs(["✏️ Segnala evento", "🔍 Visualizza segnalazioni"])
    
    with tab1:
        st.write('Usa questo modulo per segnalare eventi sismici o situazioni di emergenza nella tua zona.')
        
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
                    "Livello di gravità",
                    options=["Basso", "Medio", "Alto", "Critico"],
                    value="Medio",
                    key="gravita_evento"
                )
                
                # Indico regione e provincia
                regioni_italiane = [
                    "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
                    "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
                    "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige",
                    "Umbria", "Valle d'Aosta", "Veneto"
                ]
                regione = st.selectbox("Regione", regioni_italiane, key="regione_evento")
                
                comune = st.text_input("Comune", key="comune_evento", placeholder="Inserisci il comune")
            
            with col2:
                descrizione = st.text_area(
                    "Descrizione",
                    height=100,
                    key="descrizione_evento",
                    placeholder="Descrivi brevemente cosa sta accadendo...",
                    label_visibility="visible"
                )
                
                # Dati temporali in un'unica colonna
                data = st.date_input(
                    "Data",
                    datetime.now(),
                    key="data_evento",
                    label_visibility="visible"
                )
                ora = st.time_input(
                    "Ora",
                    datetime.now(),
                    key="ora_evento",
                    label_visibility="visible"
                )
            
            # Contatto opzionale
            contatto = st.text_input("Contatto (opzionale)", key="contatto_evento", 
                                  placeholder="Lascia un contatto per eventuali aggiornamenti")
            
            # Geolocalizzazione automatica
            st.info("📍 La tua posizione verrà rilevata automaticamente se consenti l'accesso alla geolocalizzazione.")
            
            try:
                coords = streamlit_js_eval(
                    js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
                    key="geo_segnala"
                )
            except:
                st.warning("⚠️ Impossibile rilevare la posizione. Assicurati di consentire l'accesso alla geolocalizzazione.")
                coords = None

            submitted = st.form_submit_button("Invia segnalazione")
            if submitted:
                # Verifico se la descrizione è vuota
                if not descrizione.strip():
                    st.error("⚠️ La descrizione non può essere vuota. Inserisci una descrizione dell'evento.")
                    st.stop()
                
                # Verifico se il comune è vuoto
                if not comune.strip():
                    st.error("⚠️ Il campo comune non può essere vuoto. Inserisci il comune dell'evento.")
                    st.stop()
                
                # Salva la segnalazione in Supabase o localmente
                try:
                    supabase_url = os.environ.get("SUPABASE_URL")
                    supabase_key = os.environ.get("SUPABASE_KEY")

                    if not supabase_url or not supabase_key:
                        raise ValueError("SUPABASE_URL or SUPABASE_KEY environment variable not set.")

                    # Ensure HTTPS
                    if not supabase_url.startswith("https://"):
                        supabase_url = "https://" + supabase_url

                    sb_client = create_client(supabase_url, supabase_key)

                    # Data per Supabase
                    timestamp = datetime.combine(data, ora).strftime("%d/%m/%Y %H:%M")

                    # Posizione dell'utente, se disponibile
                    lat = None
                    lon = None
                    if coords and isinstance(coords, dict):
                        lat = coords.get('lat')
                        lon = coords.get('lon')

                    # Dati da inviare
                    segnalazione_data = {
                        "tipo": tipo,
                        "descrizione": descrizione,
                        "timestamp": timestamp,
                        "latitudine": lat,
                        "longitudine": lon,
                        "gravita": gravita,
                        "regione": regione,
                        "comune": comune,
                        "contatto": contatto
                    }

                    # Inserisci in Supabase
                    response = sb_client.table("segnalazioni").insert(segnalazione_data).execute()
                    if response.error:
                        raise Exception(f"Errore Supabase: {response.error}")

                    st.success("✅ Segnalazione inviata con successo al database!")
                    
                    # Aggiungo badge di conferma
                    st.markdown(f"""
                    <div style="background-color:#d4edda; color:#155724; padding:15px; border-radius:5px; margin-top:10px; text-align:center;">
                        <h3>📢 Segnalazione registrata</h3>
                        <p>Tipo: {tipo} ({gravita})<br>
                        Località: {comune}, {regione}<br>
                        Data e ora: {timestamp}</p>
                    </div>
                    """, unsafe_allow_html=True)

                except ValueError as e:
                    st.error(f"⚠️ Errore di configurazione: {e}")
                except Exception as e:
                    # Fallback con salvataggio locale in caso di errore
                    salva_locale(tipo, descrizione, data, ora, coords, gravita, regione, comune, contatto)
                    st.warning("⚠️ Nota: Si è verificato un errore durante la connessione al database. La segnalazione è stata salvata in locale.")
                    st.success("✅ Segnalazione salvata localmente!")
                    st.error(f"Dettaglio errore: {str(e)}")
    
    with tab2:
        st.subheader("🔍 Segnalazioni registrate")
        
        # Pulsanti per scegliere la visualizzazione
        col1, col2 = st.columns([1, 1])
        
        with col1:
            view_option = st.radio("Visualizza", ["Elenco", "Mappa"], horizontal=True)
        
        with col2:
            try:
                # Filtro per tipo di evento
                filter_tipo = st.multiselect("Filtra per tipo", 
                                           ["Tutti i tipi", "Terremoto", "Frana", "Alluvione", "Incendio", 
                                            "Emergenza sanitaria", "Rischio idrogeologico", "Altro"], 
                                           default=["Tutti i tipi"])
            except:
                filter_tipo = ["Tutti i tipi"]
        
        try:
            # Tenta di caricare le segnalazioni da Supabase
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                if not supabase_url.startswith("https://"):
                    supabase_url = "https://" + supabase_url
                    
                sb_client = create_client(supabase_url, supabase_key)
                response = sb_client.table("segnalazioni").select("*").order("timestamp", desc=True).execute()
                
                if hasattr(response, 'data'):
                    segnalazioni = response.data
                    
                    # Filtra per tipo se necessario
                    if "Tutti i tipi" not in filter_tipo and filter_tipo:
                        segnalazioni = [s for s in segnalazioni if s.get("tipo") in filter_tipo]
                    
                    if not segnalazioni:
                        st.info("🔍 Nessuna segnalazione trovata con i filtri selezionati.")
                    else:
                        if view_option == "Elenco":
                            for idx, s in enumerate(segnalazioni):
                                # Definisci il colore del box in base alla gravità
                                gravita = s.get("gravita", "Medio")
                                color_map = {
                                    "Basso": "#e6f3ff",  # Blu chiaro
                                    "Medio": "#fff3cd",  # Giallo chiaro
                                    "Alto": "#ffe6cc",   # Arancione chiaro
                                    "Critico": "#f8d7da"  # Rosso chiaro
                                }
                                color = color_map.get(gravita, "#f8f9fa")
                                
                                border_map = {
                                    "Basso": "#cce5ff",  # Blu
                                    "Medio": "#ffeeba",  # Giallo
                                    "Alto": "#ffc107",   # Arancione
                                    "Critico": "#dc3545"  # Rosso
                                }
                                border = border_map.get(gravita, "#dee2e6")
                                
                                tipo_emoji = {
                                    "Terremoto": "🔴",
                                    "Frana": "🟤",
                                    "Alluvione": "🌊",
                                    "Incendio": "🔥",
                                    "Emergenza sanitaria": "🏥",
                                    "Rischio idrogeologico": "💧",
                                    "Altro": "⚠️"
                                }
                                emoji = tipo_emoji.get(s.get("tipo", "Altro"), "⚠️")
                                
                                st.markdown(f"""
                                <div style="background-color:{color}; padding:15px; border-radius:5px; 
                                          margin-bottom:15px; border-left:4px solid {border};">
                                    <h4>{emoji} {s.get("tipo", "N/A")} - {s.get("comune", "N/A")}, {s.get("regione", "N/A")}</h4>
                                    <p><strong>Data:</strong> {s.get("timestamp", "N/A")}</p>
                                    <p><strong>Descrizione:</strong> {s.get("descrizione", "N/A")}</p>
                                    <p><strong>Gravità:</strong> {gravita}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        elif view_option == "Mappa":
                            # Visualizzazione mappa
                            try:
                                import folium
                                from streamlit_folium import folium_static
                                
                                # Filtriamo solo le segnalazioni con coordinate
                                geo_segnalazioni = [s for s in segnalazioni if s.get("latitudine") and s.get("longitudine")]
                                
                                if not geo_segnalazioni:
                                    st.info("🗺️ Nessuna segnalazione con coordinate disponibile.")
                                else:
                                    # Crea mappa centrata sull'Italia
                                    m = folium.Map(location=[42.0, 12.0], zoom_start=5.5)
                                    
                                    # Colori per tipo di evento
                                    tipo_color = {
                                        "Terremoto": "red",
                                        "Frana": "orange",
                                        "Alluvione": "blue",
                                        "Incendio": "darkred",
                                        "Emergenza sanitaria": "green",
                                        "Rischio idrogeologico": "darkblue",
                                        "Altro": "gray"
                                    }
                                    
                                    # Aggiungi marker per ogni segnalazione
                                    for s in geo_segnalazioni:
                                        color = tipo_color.get(s.get("tipo", "Altro"), "gray")
                                        
                                        # Popup HTML
                                        popup_html = f"""
                                        <div style="width:250px;">
                                        <h4>{s.get("tipo", "N/A")} - {s.get("comune", "N/A")}</h4>
                                        <p><strong>Data:</strong> {s.get("timestamp", "N/A")}</p>
                                        <p><strong>Descrizione:</strong> {s.get("descrizione", "N/A")}</p>
                                        <p><strong>Gravità:</strong> {s.get("gravita", "N/A")}</p>
                                        </div>
                                        """
                                        
                                        folium.Marker(
                                            location=[s.get("latitudine"), s.get("longitudine")],
                                            popup=folium.Popup(popup_html, max_width=300),
                                            tooltip=f"{s.get('tipo')} - {s.get('comune')}",
                                            icon=folium.Icon(color=color)
                                        ).add_to(m)
                                    
                                    folium_static(m, width=700)
                                    st.caption("Mappa delle segnalazioni con geolocalizzazione")
                            
                            except Exception as e:
                                st.error(f"Errore nella visualizzazione della mappa: {e}")
                                st.info("Visualizzo segnalazioni in formato elenco...")
                                # Visualizza come elenco in caso di errore
                                for s in segnalazioni:
                                    st.write(f"**{s.get('tipo')}** - {s.get('timestamp')}")
                                    st.write(f"*{s.get('descrizione')}*")
                                    st.write("---")
                else:
                    st.info("🔍 Nessuna segnalazione trovata nel database.")
            else:
                raise ValueError("Credenziali Supabase non configurate")
        except Exception as e:
            st.info("📋 Visualizzo segnalazioni salvate localmente:")
            # Carica e visualizza segnalazioni locali
            carica_segnalazioni_locali()


def salva_locale(tipo, descrizione, data, ora, coords, gravita="Medio", regione="", comune="", contatto=""):
    """Salva la segnalazione in un file locale con i nuovi campi"""
    # Crea il percorso per i dati
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    # Percorso del file per le segnalazioni
    file_path = os.path.join(data_dir, "segnalazioni_locali.json")

    # Carica le segnalazioni esistenti o crea una lista vuota
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            # Se il file è corrotto, inizia da capo
            existing_data = []

    # Crea il record per la nuova segnalazione
    timestamp = datetime.combine(data, ora).strftime("%d/%m/%Y %H:%M")

    # Posizione dell'utente, se disponibile
    lat = None
    lon = None
    if coords and isinstance(coords, dict):
        lat = coords.get('lat')
        lon = coords.get('lon')

    # Nuovo record con campi aggiuntivi
    new_record = {
        "id": len(existing_data) + 1,
        "tipo": tipo,
        "descrizione": descrizione,
        "timestamp": timestamp,
        "latitudine": lat,
        "longitudine": lon,
        "gravita": gravita,
        "regione": regione,
        "comune": comune,
        "contatto": contatto
    }

    # Aggiungi alla lista e salva
    existing_data.append(new_record)

    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=2)
        
def carica_segnalazioni_locali():
    """Carica e visualizza le segnalazioni salvate localmente"""
    # Percorso del file per le segnalazioni
    data_dir = os.path.join(os.getcwd(), "data")
    file_path = os.path.join(data_dir, "segnalazioni_locali.json")
    
    if not os.path.exists(file_path):
        st.info("📭 Nessuna segnalazione locale disponibile.")
        return
    
    try:
        with open(file_path, "r") as f:
            segnalazioni = json.load(f)
        
        if not segnalazioni:
            st.info("📭 Nessuna segnalazione locale disponibile.")
            return
            
        # Visualizza le segnalazioni in ordine inverso (più recenti prima)
        for s in reversed(segnalazioni):
            # Definisci il colore del box in base alla gravità
            gravita = s.get("gravita", "Medio")
            color_map = {
                "Basso": "#e6f3ff",  # Blu chiaro
                "Medio": "#fff3cd",  # Giallo chiaro
                "Alto": "#ffe6cc",   # Arancione chiaro
                "Critico": "#f8d7da"  # Rosso chiaro
            }
            color = color_map.get(gravita, "#f8f9fa")
            
            border_map = {
                "Basso": "#cce5ff",  # Blu
                "Medio": "#ffeeba",  # Giallo
                "Alto": "#ffc107",   # Arancione
                "Critico": "#dc3545"  # Rosso
            }
            border = border_map.get(gravita, "#dee2e6")
            
            tipo_emoji = {
                "Terremoto": "🔴",
                "Frana": "🟤",
                "Alluvione": "🌊",
                "Incendio": "🔥",
                "Emergenza sanitaria": "🏥",
                "Rischio idrogeologico": "💧",
                "Altro": "⚠️"
            }
            emoji = tipo_emoji.get(s.get("tipo", "Altro"), "⚠️")
            
            # Informazioni sulla località
            comune = s.get("comune", "N/A")
            regione = s.get("regione", "N/A")
            localita = f"{comune}, {regione}" if comune != "N/A" and regione != "N/A" else "Località non specificata"
            
            st.markdown(f"""
            <div style="background-color:{color}; padding:15px; border-radius:5px; 
                      margin-bottom:15px; border-left:4px solid {border};">
                <h4>{emoji} {s.get("tipo", "N/A")} - {localita}</h4>
                <p><strong>Data:</strong> {s.get("timestamp", "N/A")}</p>
                <p><strong>Descrizione:</strong> {s.get("descrizione", "N/A")}</p>
                <p><strong>Gravità:</strong> {gravita}</p>
                {f'<p><strong>Contatto:</strong> {s.get("contatto")}</p>' if s.get("contatto") else ''}
            </div>
            """, unsafe_allow_html=True)
            
        # Pulsante per cancellare tutte le segnalazioni locali
        if st.button("🗑️ Cancella tutte le segnalazioni locali"):
            with open(file_path, "w") as f:
                json.dump([], f)
            st.success("✅ Tutte le segnalazioni locali sono state cancellate.")
            st.rerun()
            
    except Exception as e:
        st.error(f"Errore nel caricamento delle segnalazioni locali: {e}")
        # Se il file è corrotto, offri la possibilità di resettarlo
        if st.button("🔄 Resetta file segnalazioni"):
            with open(file_path, "w") as f:
                json.dump([], f)
            st.success("✅ File segnalazioni resettato.")
            st.rerun()