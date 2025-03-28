
import streamlit as st
from modules.dati_regioni_a import dati_regioni_a
from modules.dati_regioni_b import dati_regioni_b
from modules.dati_regioni_c import dati_regioni_c

dati_regioni = {}
dati_regioni.update(dati_regioni_a)
dati_regioni.update(dati_regioni_b)
dati_regioni.update(dati_regioni_c)



dati_regioni = {}


def show():
    regione_sel = st.selectbox("Seleziona la tua regione", sorted(dati_regioni.keys()))
    
    if regione_sel in dati_regioni:
        dati = dati_regioni[regione_sel]
        
        st.markdown("### 🛑 Criticità territoriali")
        st.markdown(dati["criticita"])

        st.markdown("### 📍 Punti di raccolta")
        for punto in dati["punti_raccolta"]:
            st.markdown(f"- {punto}")

        st.markdown("### 🔗 Link utili")
        for titolo, url in dati["link_utili"].items():
            st.markdown(f"- [{titolo}]({url})")

        st.markdown("### 🌧️ Rischio Idrogeologico")
        st.markdown(dati["rischio_idrogeologico"]["descrizione"])
        st.markdown(f"[Maggiori informazioni]({dati['rischio_idrogeologico']['link']})")


dati_regioni.update(dati_regioni_b)
dati_regioni.update(dati_regioni_c)
