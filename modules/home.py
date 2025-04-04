
import streamlit as st

def show():
    st.title('🌍 SismaVer2')
    
    st.markdown("""
    ### 🎯 La tua piattaforma per il monitoraggio di:
    - 🌋 Attività vulcanica in Italia
    - 🌊 Eventi sismici
    - 🌤️ Condizioni meteorologiche
    - ⚠️ Situazioni di emergenza
    """)

    # Statistiche in colonne
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vulcani monitorati", "9")
    with col2:
        st.metric("Stazioni sismiche", "500+")
    with col3:
        st.metric("Aggiornamenti", "Real-time")

    st.markdown("---")

    st.markdown("""
    ### 🔍 Caratteristiche principali
    - **Monitoraggio in tempo reale** dei principali vulcani italiani
    - **Dati sismici** aggiornati dall'INGV
    - **Previsioni meteo** precise e localizzate
    - **Chat pubblica** per segnalazioni e comunicazioni
    - **Mappe interattive** per visualizzare gli eventi
    """)

    st.info("👨‍💻 Sviluppato da **Fabio SCELZO**")

    st.markdown("---")

    # Sezione contatti e supporto
    st.subheader("📞 Contatti e Supporto")
    st.markdown("📧 Email: meteotorre@gmail.com")
