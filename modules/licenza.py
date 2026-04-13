import streamlit as st
from PIL import Image
import os

def show():
    st.title("📜 Termini d'Uso e Diritti Riservati")
    
    # Sezione biografia dello sviluppatore
    st.header("👨‍💻 Lo Sviluppatore")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            # Percorso dell'immagine del profilo
            image_path = os.path.join("images", "fabio_scelzo.jpg")
            if os.path.exists(image_path):
                image = Image.open(image_path)
                st.image(image, width=200)
            else:
                st.error("Immagine profilo non trovata")
        except Exception as e:
            st.error(f"Errore nel caricamento dell'immagine: {e}")
    
    with col2:
        st.subheader("Fabio Scelzo")
        st.markdown("""
        Nato nel 1973, Fabio ha coltivato sin dall'infanzia una profonda passione per l'elettronica e l'informatica, che è rimasta costante attraverso gli anni, evolvendo insieme alle tecnologie.
        
        Esperto di sviluppo software e appassionato di monitoraggio ambientale, ha creato questa piattaforma per fornire uno strumento utile alla comunità, combinando competenze tecniche e interesse per il territorio. Lo sviluppo è stato potenziato dall'utilizzo delle moderne tecnologie di Intelligenza Artificiale, che hanno contribuito a migliorarne le funzionalità e l'interfaccia utente.
        
        Attualmente vive a Torre Annunziata, una città ricca di storia e tradizioni nella provincia di Napoli.
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### ❗ Diritti riservati - Fabio SCELZO

    Tutto il contenuto di questa applicazione, incluso ma non limitato a:
    - Codice sorgente
    - Grafica
    - Dati strutturati
    - Idee progettuali
    - Documentazione tecnica
    è di proprietà esclusiva di **Fabio SCELZO**.

    ### 🚫 Vietata la riproduzione
    È **vietata ogni forma di copia, distribuzione, modifica o ripubblicazione**, anche **parziale**, senza **espressa autorizzazione scritta** dell'autore.

    Qualsiasi utilizzo non autorizzato sarà considerato una violazione dei diritti intellettuali e perseguito secondo le normative vigenti.

    ### ✅ Uso personale
    L'utilizzo è consentito esclusivamente per scopi personali, informativi e non commerciali, fatta salva diversa autorizzazione.
    """)
    
    st.markdown("---")
    
    st.subheader("📋 Licenza d'uso")
    st.markdown("""
    ### Condizioni generali
    
    1. **Licenza limitata**:  
       L'utente è autorizzato a utilizzare SismaVer2 esclusivamente per scopi personali e informativi.
    
    2. **Vincoli d'uso**:  
       Non è consentito:
       - Copiare, modificare o distribuire il codice sorgente
       - Decompilare o decodificare l'applicazione
       - Rimuovere le note di copyright o i crediti
       - Utilizzare l'applicazione per scopi commerciali
       - Creare opere derivate basate su questa applicazione
    
    3. **Dati e Privacy**:  
       - I dati personali forniti dagli utenti (come posizione geografica) sono utilizzati esclusivamente per le funzionalità dell'applicazione
       - I messaggi inviati nella chat pubblica sono visibili a tutti gli utenti
       - Le segnalazioni inviate possono essere utilizzate per migliorare il servizio
    
    4. **Responsabilità**:  
       SismaVer2 fornisce informazioni a scopo informativo e non può essere ritenuto responsabile per decisioni prese in base ai dati visualizzati. In caso di emergenza, fare sempre riferimento alle comunicazioni ufficiali delle autorità competenti.
    """)
    
    st.markdown("---")
    
    st.subheader("⚠️ Disclaimer")
    st.markdown("""
    ### Limitazioni di responsabilità
    
    1. **Accuratezza dei dati**:  
       SismaVer2 si impegna a fornire informazioni accurate, ma non può garantire la totale assenza di errori o ritardi nelle informazioni provenienti da fonti terze.
    
    2. **Uso in emergenza**:  
       Questa applicazione NON sostituisce i canali ufficiali di allerta della Protezione Civile o di altre autorità competenti. In situazioni di emergenza, seguire sempre le direttive delle autorità locali.
    
    3. **Disponibilità del servizio**:  
       Non è garantita la disponibilità continua e ininterrotta del servizio. Potrebbero verificarsi momenti di manutenzione o interruzioni tecniche.
    
    4. **Danni consequenziali**:  
       L'autore non è responsabile per eventuali danni diretti, indiretti, incidentali o consequenziali derivanti dall'uso o dall'impossibilità di utilizzare SismaVer2.
    """)
    
    st.markdown("---")
    
    st.subheader("🔄 Modifiche ai termini")
    st.markdown("""
    I presenti termini d'uso possono essere modificati in qualsiasi momento a discrezione dell'autore. L'utente è invitato a consultare periodicamente questa sezione per verificare eventuali aggiornamenti.
    
    L'uso continuato dell'applicazione dopo la pubblicazione di modifiche costituisce accettazione delle stesse.
    """)
    
    st.markdown("---")
    
    st.subheader("📬 Contatti")
    st.markdown("""
    Per richieste di autorizzazione, segnalazioni di violazioni, informazioni o collaborazioni, contattare l'autore all'indirizzo email:
    
    **meteotorre@gmail.com**
    """)
    
    st.caption("Ultimo aggiornamento dei termini: Aprile 2025")
    
    st.markdown("---")
    
    with st.expander("ℹ️ Informazioni sull'applicazione"):
        st.subheader("Come funziona SismaVer2")
        
        st.markdown("""
        ### Architettura dell'applicazione
        
        SismaVer2 è costruito su un'architettura moderna e resiliente che integra diverse tecnologie:
        
        - **Frontend**: Streamlit (framework Python per applicazioni web interattive)
        - **Backend**: Sistema modulare Python con cache multi-livello
        - **Database**: Supabase per la persistenza dei dati e gestione utenti
        - **Visualizzazione dati**: Folium, Plotly e Pandas per elaborazione e visualizzazione
        - **API**: Integrazione con INGV, USGS, OpenWeatherMap e altri servizi
        
        ### Fonti dei dati
        
        L'applicazione integra dati da fonti ufficiali e autorevoli:
        
        - **Dati sismici**: INGV (Istituto Nazionale di Geofisica e Vulcanologia) con fallback a USGS
        - **Dati vulcanici**: INGV Osservatorio Vesuviano e Osservatorio Etneo
        - **Dati meteo**: OpenWeatherMap API
        - **Punti di emergenza**: Database Protezione Civile e risorse comunali
        
        ### Sistema di fallback multi-livello
        
        Per garantire la massima affidabilità, SismaVer2 implementa un sofisticato sistema di fallback:
        
        1. **Richieste multi-server**: Le richieste vengono inviate a server alternativi quando il principale non risponde
        2. **API alternative**: Utilizzo di USGS quando INGV non è raggiungibile
        3. **Cache temporanea**: I dati recenti vengono memorizzati per garantire l'accesso anche offline
        4. **Dati storici**: In ultima istanza, vengono mostrati dati storici significativi
        
        ### Aggiornamenti automatici
        
        SismaVer2 implementa un sistema di aggiornamento continuo:
        
        - **Monitoraggio sismico**: Aggiornamento automatico ogni 15 minuti
        - **Dati vulcanici**: Aggiornamento giornaliero
        - **Previsioni meteo**: Aggiornamento ogni 3 ore
        - **Segnalazioni utenti**: In tempo reale
        """)
        
        st.success("SismaVer2 è progettato per funzionare anche in condizioni di connettività limitata o instabile, garantendo l'accesso alle informazioni essenziali in ogni momento.")
        
    st.markdown("---")
    
    st.info("Per ulteriori informazioni o richieste specifiche, contattare l'autore all'indirizzo meteotorre@gmail.com")
