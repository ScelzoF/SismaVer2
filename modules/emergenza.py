
import streamlit as st
from modules.dati_regioni_a import dati_regioni_a
from modules.dati_regioni_b import dati_regioni_b
from modules.dati_regioni_c import dati_regioni_c

dati_regioni = {}
dati_regioni.update(dati_regioni_a)
dati_regioni.update(dati_regioni_b)
dati_regioni.update(dati_regioni_c)

regioni = [
    "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia Romagna",
    "Friuli Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche",
    "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia",
    "Toscana", "Trentino Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"
]

def show():
    st.title("🌍 Emergenza")
    regione = st.selectbox("Seleziona la tua regione", regioni)
    dati = dati_regioni.get(regione, {
        "criticita": "Contenuto in fase di aggiornamento.",
        "punti_raccolta": ["Punti di raccolta in fase di definizione."],
        "link_utili": [],
        "rischio_idrogeologico": {
            "descrizione": "Dati in aggiornamento.",
            "link": "#"
        }
    })

    st.markdown("## 🛑 Criticità territoriali")
    st.write(dati["criticita"])

    st.markdown("## 📍 Punti di raccolta")
    for punto in dati["punti_raccolta"]:
        st.markdown(f"- {punto}")

    st.markdown("## 🔗 Link utili")
    for link in dati["link_utili"]:
        st.markdown(f"- [{link}]({link})")

    st.markdown("## 🌧️ Rischio Idrogeologico in Italia")
    st.write(dati["rischio_idrogeologico"]["descrizione"])
    st.markdown(f"[Maggiori informazioni]({dati['rischio_idrogeologico']['link']})")
