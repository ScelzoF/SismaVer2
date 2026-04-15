
import streamlit as st
from datetime import datetime

def show():
    st.title("📋 Note di Rilascio - SismaVer2")
    
    st.write("Questa pagina contiene la cronologia delle versioni e i dettagli sugli aggiornamenti dell'applicazione.")
    
    st.markdown("""
    ## Versione attuale: 2.7.0 (Aprile 2026)
    
    SismaVer2 è un'applicazione in costante evoluzione, sviluppata con l'obiettivo di fornire un sistema 
    completo di monitoraggio e prevenzione per il territorio italiano.
    
    L'applicazione integra dati in tempo reale da fonti ufficiali, offrendo un servizio affidabile 
    e aggiornato per tutti i cittadini, con copertura nazionale e funzionalità avanzate.
    """)
    
    # Timeline delle versioni con componente visivo
    with st.container():
        st.subheader("Cronologia delle versioni")

        # Versione 2.7.0 — NUOVA
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#7C3AED; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.7.0</h3>
                <p>Aprile 2026</p>
                <span style="font-size:11px; background:#6D28D9; padding:2px 6px; border-radius:3px;">ATTUALE</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.7.0 (Aprile 2026)
            #### Audit completo, nuove sezioni, auto-refresh nativo, qualità aria

            - 🌬️ **Nuova sezione "Qualità dell'Aria"** — Indice AQI europeo (EEA) per 20 città italiane, basato su Open-Meteo/Copernicus CAMS. Nessuna API key richiesta. PM10, PM2.5, NO₂, O₃, CO, SO₂. Auto-refresh ogni 30 min
            - 📞 **Nuova sezione "Numeri Utili"** — Tutti i numeri di emergenza nazionali (112, 118, 115, 113, 117, 1530, 116117...) e regionali della Protezione Civile, centri antiveleni, codici triage PS, app ufficiali
            - 🏠 **Home migliorata** — Feed RSS notizie della Protezione Civile in tempo reale, barra emergenza fissa (112/118/115/113), metriche corrette (20+ vulcani, 20 città aria)
            - 🌋 **Vulcani — visione Italia** — Tabella completa con 20 vulcani (aggiunto Marsili, Ferdinandea, Lipari-Vulcanello, Ustica, Linosa, Salina, Alicudi, Filicudi, Monte Amiata, Colli Albani); rimosso selectbox inutile; mappa folium con tutti i marker
            - 🌊 **Idrogeologico** — Aggiunte metriche ISPRA (1.28M ha frane, 2.06M ha alluvioni, 7.5M abitanti esposti) e link mappa interattiva IdroGEO, prima completamente assenti
            - 📍 **Punti raccolta** — Rimosso limite di 5 punti: ora mostra tutti i punti per ogni regione sia in lista che sulla mappa
            - ⚡ **Auto-refresh nativo** — `streamlit-autorefresh` sostituisce la vecchia logica session_state: Home (5 min), Allerte (2 min), Monitoraggio sismico (5 min), Vulcani (30 min), Qualità Aria (30 min)
            - 🔵 **TTL sismico ridotto** — Cache dati sismici in monitoraggio.py: 1800s→300s (da 30 min a 5 min)
            - 🔍 **SEO migliorato** — Meta description, keywords, Open Graph, rimosso placeholder codice Google
            - 📜 **Licenza** — Anno footer ora dinamico (`datetime.now().year`), mai più hardcoded
            """)

        st.markdown("---")

        # Versione 2.6.0 — precedente
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#1565C0; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.6.0</h3>
                <p>Aprile 2026</p>
                <span style="font-size:11px; background:#0D47A1; padding:2px 6px; border-radius:3px;">PRECEDENTE</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.6.0 (Aprile 2026)
            #### Dashboard allerte live, tsunami in vulcani, fonti aggiornate

            - 📊 **Nuova sezione "Allerte e Rischi"** — Dashboard live con allerta tsunami (EMSC), sismica (INGV), vulcanica (7 vulcani), meteo (MeteoAlarm) e rischio idrogeologico (ISPRA/DPC), auto-refresh ogni 2 minuti
            - 🌊 **Indicatore tsunami in Vulcani** — Ogni scheda vulcano mostra ora lo stato live del Mediterraneo: nessun evento / sorveglianza / allerta, basato su EMSC (M≥5.5, ultime 24h)
            - 🌧️ **Idrogeologico live** — Il tab "🌊 Idrogeologico" in Monitoraggio mostra allerte MeteoAlarm reali per la regione selezionata, non più dati statici
            - 📚 **Nuova sezione "Fonti dei Dati"** — Pagina dedicata con tutte le fonti ufficiali usate (INGV, EMSC, CAT-INGV, Open-Meteo, MeteoAlarm, ISPRA, DPC) e frequenza di aggiornamento
            - 🕐 **Ora legale completata** — Corretto timezone hardcoded UTC+2 anche in meteo.py, chat_backend.py e nella conversione timestamp di monitoraggio.py
            - ⚙️ **Compatibilità Streamlit Cloud** — Rimosso port fisso dal config.toml (Streamlit Cloud usa 8501 di default)
            - 🔄 **Keepalive automatico** — GitHub Action che pinga sos-italia.streamlit.app ogni 6 ore per evitare la pausa automatica
            """)

        st.markdown("---")

        # Versione 2.5.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#4CAF50; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.5.0</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.5.0 (Aprile 2026)
            #### Emergenze complete, Home live, fix fuso orario

            - 🏠 **Home live** — Ultimi 5 terremoti INGV in tempo reale e stato attività vulcanica (7 giorni) direttamente nella schermata principale
            - 🚨 **Emergenze nazionali complete** — Aggiunte sezioni mancanti: Frana/Smottamento, Maremoto/Tsunami, Neve e Gelo, Ondata di Calore (ora 8 tipi di emergenza)
            - 🗺️ **Tutte le 20 regioni in Emergenza** — Corretta importazione mancante di 5 regioni (Toscana, Sicilia, Sardegna, Puglia, Molise) che non comparivano nella selezione
            - 📍 **Coordinate punti raccolta** — Aggiunte coordinate GPS precise per tutte le regioni italiane
            - 🌧️ **Rischio idrogeologico e rischi specifici** — Ora visibili nell'interfaccia per ogni regione
            - 🕐 **Ora legale automatica** — Rimosso fuso orario hardcoded UTC+2 in monitoraggio.py, vulcani.py e chat_enhanced.py
            - 📅 **Dati fallback vulcani aggiornati** — Date fallback aggiornate ad Aprile 2026
            - 🧹 **Dati puliti** — Eliminati duplicati tra file regionali
            """)

        st.markdown("---")

        # Versione 2.3.3
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#4CAF50; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.3.3</h3>
                <p>6 Aprile 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.3.3 (6 Aprile 2025)
            #### Ottimizzazioni e miglioramenti
            
            - 🔄 **Contatore visite univoco** - Implementato sistema di tracciamento visite basato su IP
            - 🛡️ **Sicurezza migliorata** - Ottimizzata la gestione delle sessioni e protezione CSRF
            - 📊 **Cache avanzata** - Migliorato sistema di cache per i dati sismici
            - ⚡ **Performance** - Ottimizzato il caricamento delle pagine e gestione della memoria
            - 🔐 **Privacy** - Implementato hashing degli IP per la privacy degli utenti
            """)
            
        st.markdown("---")
        
        # Versione 2.3.2
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#9C27B0; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.3.2</h3>
                <p>4 Aprile 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.3.2 (4 Aprile 2025)
            #### Resilienza dei dati e correzioni bug
            
            - 🌐 **Fallback USGS** - Implementato sistema automatico di fallback a USGS
            - 📊 **Grafici migliorati** - Risolto il problema di visualizzazione dei grafici temporali
            - 🧩 **Compatibilità formati** - Supporto per diversi formati di dati tra le varie fonti
            - 🔄 **Ripristino automatico** - Sistema di ripristino automatico fonte dati principale
            - 📱 **Esperienza utente** - Migliorati i messaggi informativi all'utente
            """)
            
        st.markdown("---")
        
        # Versione 2.3.1
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#1E88E5; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.3.1</h3>
                <p>15 Marzo 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.3.1 (15 Marzo 2025)
            #### Miglioramenti nella resilienza e nell'esperienza utente
            
            - 🔧 **Sistema di cache avanzato** - Ottimizzato il sistema di cache con fallback multipli
            - 🌐 **API resilient** - Migliorata la resilienza nelle API con server alternativi
            - 🕒 **Fuso orario automatico** - Implementato calcolo automatico dell'ora legale italiana
            - 📈 **Monitoraggio vulcanico** - Migliorato il monitoraggio vulcanico in tempo reale
            - 🩺 **Primo soccorso interattivo** - Nuova sezione di primo soccorso con contenuti interattivi
            """)
            
        st.markdown("---")
        
        # Versione 2.2.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#43A047; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.2.0</h3>
                <p>1 Marzo 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.2.0 (1 Marzo 2025)
            #### Espansione delle funzionalità e miglioramenti UX
            
            - 🆘 **Punti di emergenza** - Aggiunta sezione punti di emergenza con mappa interattiva
            - 🌦️ **Meteo migliorato** - Ottimizzata visualizzazione dati meteo con radar
            - 💬 **Chat pubblica** - Implementata chat pubblica con filtri regionali
            - 🔍 **Design responsivo** - Migliorata accessibilità e design mobile
            """)
            
        st.markdown("---")
            
        # Versione 2.1.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#FB8C00; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.1.0</h3>
                <p>1 Febbraio 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.1.0 (1 Febbraio 2025)
            #### Espansione delle funzionalità core
            
            - 🔄 **Monitoraggio avanzato** - Sistema di monitoraggio con cache e resilienza
            - 🗺️ **Mappe regionali** - Mappe interattive per tutte le regioni
            - 📱 **Ottimizzazione mobile** - Migliorato supporto dispositivi mobili
            - 🌋 **Modulo vulcani** - Implementato modulo vulcani con dati in tempo reale
            """)
            
        st.markdown("---")
            
        # Versione 2.0.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#E53935; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.0.0</h3>
                <p>Gennaio 2025</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            ### Versione 2.0.0 (Gennaio 2025)
            #### Rilascio iniziale
            
            - 🚀 **Rilascio iniziale** - Prima release pubblica di SismaVer2
            - 🇮🇹 **Copertura nazionale** - Supporto per tutte le regioni italiane
            - 🔔 **Fonti ufficiali** - Integrazione con fonti ufficiali nazionali
            - 📊 **Dashboard rischi** - Dashboard di monitoraggio con visualizzazione dati
            """)
    
    with st.expander("Informazioni sull'applicazione"):
        st.markdown("""
        ## Informazioni sull'applicazione
        
        ### Scopo del progetto
        SismaVer2 è stato sviluppato per fornire uno strumento unificato e affidabile per:
        
        - **Monitoraggio continuo** dei rischi naturali sul territorio italiano
        - **Informazione tempestiva** ai cittadini su eventi potenzialmente pericolosi
        - **Educazione** sulla prevenzione e gestione delle emergenze
        - **Aggregazione** di dati da fonti ufficiali in un'unica interfaccia
        
        ### Architettura del sistema
        L'applicazione è costruita su un'architettura modulare che garantisce:
        
        - **Resilienza**: sistema di fallback multipli per alta disponibilità
        - **Scalabilità**: gestione efficiente di numerosi utenti simultanei
        - **Aggiornamento continuo**: dati aggiornati in tempo reale
        - **Persistenza**: storage sicuro per segnalazioni e interazioni utenti
        """)
        
    st.info("Per segnalare bug o suggerire nuove funzionalità, contatta lo sviluppatore all'indirizzo meteotorre@gmail.com")
