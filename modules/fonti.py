def show():
    import streamlit as st
    
    st.title('📚 Fonti')
    
    st.markdown("""
    ## Fonti ufficiali dei dati
    
    SismaVer2 utilizza esclusivamente fonti ufficiali e autorevoli per garantire l'affidabilità dei dati visualizzati. Di seguito sono elencate le principali fonti utilizzate nella piattaforma:
    
    ### 🌍 Dati sismici
    
    - **[INGV - Istituto Nazionale di Geofisica e Vulcanologia](https://www.ingv.it)**  
      Fonte primaria per dati sismici e vulcanici sul territorio italiano. Il Centro Nazionale Terremoti dell'INGV monitora costantemente l'attività sismica in Italia.
      
    - **[USGS - United States Geological Survey](https://earthquake.usgs.gov)**  
      Fonte per dati sismici globali. USGS fornisce dati in tempo reale su terremoti a livello mondiale.
    
    ### 🌋 Monitoraggio vulcanico
    
    - **[Osservatorio Vesuviano (INGV-OV)](http://www.ov.ingv.it/)**  
      Centro di monitoraggio dei vulcani campani (Vesuvio, Campi Flegrei, Ischia).
      
    - **[INGV Catania](https://www.ct.ingv.it/)**  
      Centro di monitoraggio dei vulcani siciliani (Etna, Stromboli, Vulcano).
      
    - **[INGV Vulcani](https://www.ingv.it/it/vulcani/)**  
      Sezione dell'INGV dedicata a tutti i vulcani italiani.
    
    ### 🌤️ Dati meteorologici
    
    - **[OpenWeather API](https://openweathermap.org/)**  
      Fonte per dati meteorologici in tempo reale e previsioni.
      
    - **[Aeronautica Militare - Servizio Meteorologico](http://www.meteoam.it/)**  
      Fonte secondaria per dati e previsioni meteorologiche sul territorio italiano.
    
    ### 🚨 Protezione Civile
    
    - **[Dipartimento della Protezione Civile](http://www.protezionecivile.gov.it/)**  
      Fonte per informazioni su rischi, piani di emergenza e gestione delle emergenze a livello nazionale.
      
    - **Protezioni Civili Regionali**  
      Fonti per informazioni specifiche a livello regionale sui piani di emergenza e punti di raccolta.
    
    ### 🔍 Ricerca e pubblicazioni scientifiche
    
    - **Bollettini dell'INGV**  
      Rapporti settimanali e mensili sullo stato dei vulcani e sull'attività sismica in Italia.
      
    - **Pubblicazioni scientifiche peer-reviewed**  
      Studi e ricerche sui fenomeni sismici e vulcanici italiani pubblicati su riviste scientifiche internazionali.
    """)
    
    st.markdown("---")
    
    st.subheader("🔄 Aggiornamento dei dati")
    st.markdown("""
    - I dati sismici sono aggiornati in tempo quasi reale, con latenza variabile in base alla fonte:
      - INGV: da pochi minuti a circa un'ora dall'evento
      - USGS: da pochi minuti a poche ore dall'evento
      
    - I dati vulcanici vengono aggiornati con frequenza variabile:
      - Parametri di monitoraggio: da tempo reale a aggiornamenti giornalieri
      - Report e bollettini: settimanalmente o mensilmente
      
    - I dati meteorologici sono aggiornati in tempo reale tramite l'API di OpenWeather
    
    - Le informazioni di emergenza sono aggiornate periodicamente in base ai dati ufficiali della Protezione Civile
    """)
    
    st.markdown("---")
    
    st.subheader("📊 Metodologie di elaborazione")
    st.markdown("""
    SismaVer2 elabora i dati grezzi ottenuti dalle fonti ufficiali per presentarli in forma accessibile:
    
    1. **Acquisizione** - I dati vengono acquisiti tramite API pubbliche o scraping di siti ufficiali
    
    2. **Validazione** - I dati vengono verificati per confermare la loro validità e completezza
    
    3. **Normalizzazione** - I dati provenienti da fonti diverse vengono uniformati per garantire coerenza
    
    4. **Visualizzazione** - I dati vengono rappresentati graficamente per favorire la comprensione
    
    5. **Contestualizzazione** - I dati vengono arricchiti con informazioni di contesto per facilitarne l'interpretazione
    """)
    
    st.markdown("---")
    
    st.caption("Le fonti sono costantemente verificate e aggiornate per garantire la massima affidabilità delle informazioni.")
