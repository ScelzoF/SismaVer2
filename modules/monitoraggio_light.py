import streamlit as st

def show():
    """
    Versione ultraleggera del modulo di monitoraggio sismico
    senza chiamate API o elaborazioni pesanti
    """
    st.title("📡 Monitoraggio Sismico Nazionale")
    
    # Messaggio di versione leggera
    st.warning("Questa è la versione ultraleggera del modulo di monitoraggio. Stai vedendo questa pagina perché l'applicazione è stata ottimizzata per prestazioni migliori.")
    
    # Tabs per navigazione
    sensor_tab1, sensor_tab2, sensor_tab3 = st.tabs(["👁️ Monitoraggio Sismico", "🌋 Monitoraggio Vulcanico", "💧 Monitoraggio Idrogeologico"])
    
    with sensor_tab1:
        st.subheader("🔍 Monitoraggio sismico statico")
        st.info("Per accedere ai dati sismici in tempo reale, verifica la connessione a internet e riavvia l'applicazione.")
        
        # Mostra iframe del portale terremoti INGV
        st.info("Visualizzazione alternativa tramite portale INGV:")
        st.components.v1.iframe(
            "http://terremoti.ingv.it/events", 
            height=500, 
            scrolling=True
        )
    
    with sensor_tab2:
        st.subheader("🌋 Monitoraggio vulcanico statico")
        st.info("Questa sezione mostra i principali vulcani attivi italiani.")
        
        vulcani = ["Vesuvio", "Campi Flegrei", "Etna", "Stromboli", "Vulcano", "Ischia", "Colli Albani", "Pantelleria"]
        
        # Visualizzazione semplice senza dati esterni
        for vulcano in vulcani:
            st.write(f"### {vulcano}")
            st.write("Stato: 🟢 Monitoraggio di base")
    
    with sensor_tab3:
        st.subheader("💧 Monitoraggio idrogeologico")
        st.info("I dati idrogeologici in tempo reale non sono disponibili nella versione leggera.")
        
        st.write("Per dati in tempo reale, consultare:")
        st.write("- [Protezione Civile - Rischio idrogeologico](https://www.protezionecivile.gov.it/it/rischio/rischio-idraulico)")
        st.write("- [Servizio Idrografico e Mareografico Nazionale](http://www.isprambiente.gov.it/it/servizi/sistema-delle-agenzie-ambientali)")