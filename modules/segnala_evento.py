import streamlit as st
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import os
import json
from supabase import create_client, Client


def show():
    st.title('📢 Segnalazione Eventi')

    st.write('Usa questo modulo per segnalare eventi sismici o situazioni di emergenza nella tua zona.')

    with st.form("segnalazione_form"):
        tipo = st.selectbox(
            "Tipo di evento",
            ["Terremoto", "Frana", "Alluvione", "Altro"],
            key="tipo_evento",
            label_visibility="visible"
        )
        descrizione = st.text_area(
            "Descrizione",
            height=100,
            key="descrizione_evento",
            label_visibility="visible"
        )
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

        try:
            coords = streamlit_js_eval(
                js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
                key="geo_segnala"
            )
        except:
            st.warning("Impossibile rilevare la posizione. Assicurati di consentire l'accesso alla geolocalizzazione.")
            coords = None

        submitted = st.form_submit_button("Invia segnalazione")
        if submitted:
            # Salva la segnalazione in Supabase o localmente
            try:
                supabase_url = os.environ.get("SUPABASE_URL")
                supabase_key = os.environ.get("SUPABASE_KEY")

                if supabase_url and supabase_key:
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
                        "longitudine": lon
                    }

                    # Inserisci in Supabase
                    response = sb_client.table("segnalazioni").insert(segnalazione_data).execute()
                    if hasattr(response, 'error') and response.error:
                        raise Exception(f"Errore Supabase: {response.error}")

                    st.success("✅ Segnalazione inviata con successo al database!")

                else:
                    # Fallback con salvataggio locale
                    salva_locale(tipo, descrizione, data, ora, coords)
                    st.success("✅ Segnalazione salvata localmente!")
                    st.info("Nota: La segnalazione è stata salvata in locale poiché la connessione al database non è disponibile.")

            except Exception as e:
                # Fallback con salvataggio locale in caso di errore
                salva_locale(tipo, descrizione, data, ora, coords)
                st.success("✅ Segnalazione salvata localmente!")
                st.warning(f"Nota: Si è verificato un errore durante la connessione al database. La segnalazione è stata salvata in locale.")
                st.error(f"Dettaglio errore: {str(e)}")

def salva_locale(tipo, descrizione, data, ora, coords):
    """Salva la segnalazione in un file locale"""
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

    # Nuovo record
    new_record = {
        "id": len(existing_data) + 1,
        "tipo": tipo,
        "descrizione": descrizione,
        "timestamp": timestamp,
        "latitudine": lat,
        "longitudine": lon
    }

    # Aggiungi alla lista e salva
    existing_data.append(new_record)

    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=2)