import streamlit as st

def show():
    """Versione ultraleggera della Home senza chiamate esterne o elaborazioni pesanti"""
    st.title("🌍 SismaVer2 - Monitoraggio Sismico Italiano")
    
    st.write("""
    ### Benvenuto nella versione leggera dell'applicazione
    
    Questo modulo iniziale è stato ottimizzato per garantire il caricamento rapido dell'applicazione.
    
    Seleziona una sezione dalla barra laterale per accedere alle funzionalità.
    """)
    
    # Info sul sistema
    st.subheader("🔍 Informazioni sul sistema")
    
    with st.expander("Dettagli dell'applicazione"):
        st.markdown("""
        **Nome:** SismaVer2
        
        **Versione:** 2.0 (Light Edition)
        
        **Data rilascio:** Aprile 2025
        
        **Sviluppatore:** Fabio Scelzo
        
        **Contatto:** meteotorre@gmail.com
        """)
    
    st.info("Questa è la versione leggera ottimizzata dell'applicazione. Per accedere a tutte le funzionalità, seleziona i moduli dalla barra laterale.")