
import streamlit as st
from datetime import datetime

def show():
    from modules.banner_utils import banner_note_rilascio
    banner_note_rilascio()
    
    st.write("Questa pagina contiene la cronologia delle versioni e i dettagli sugli aggiornamenti dell'applicazione.")
    
    st.markdown("""
    ## Versione attuale: 2.9.7 (Aprile 2026)
    
    SismaVer2 è un'applicazione in costante evoluzione, sviluppata con l'obiettivo di fornire un sistema 
    completo di monitoraggio e prevenzione per il territorio italiano.
    
    L'applicazione integra dati in tempo reale da fonti ufficiali, offrendo un servizio affidabile 
    e aggiornato per tutti i cittadini, con copertura nazionale e funzionalità avanzate.
    """)
    
    # Timeline delle versioni con componente visivo
    with st.container():
        st.subheader("Cronologia delle versioni")

        # Versione 2.9.7 — NUOVA
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#059669; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.7</h3>
                <p>Aprile 2026</p>
                <span style="font-size:11px; background:#047857; padding:2px 6px; border-radius:3px;">ATTUALE</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.7 (Aprile 2026)
            #### Fix critico — Banner HTML su Streamlit Cloud

            - 🐛 **Bug critico risolto** — Il banner mostrava l'HTML grezzo come codice invece di renderizzarlo. Causa: l'f-string multiriga aveva 8+ spazi di rientro, interpretati dal parser Markdown di Streamlit come **blocco di codice** (regola: 4+ spazi iniziali = code block)
            - 🔧 **banner_utils.py riscritto** — L'HTML viene ora costruito come stringa concatenata compatta senza rientri, garantendo rendering corretto sia in locale che su Streamlit Cloud
            - ✅ **Testato** — Banner renderizzati correttamente con gradiente, emoji, titolo e sottotitolo su tutti i 15 preset tematici
            """)

        st.markdown("---")

        # Versione 2.9.6
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.6</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.6 (Aprile 2026)
            #### Audit completo — Fix coerenza, GPS centri specializzati, pulizia UI

            - 🔧 **margin-top:-12px rimosso** — I sottotitoli in Home, Allerte e Qualità Aria non avevano più il `st.title()` sopra (sostituito dal banner): rimosso lo stacco negativo orfano per evitare sovrapposizioni visive
            - 🏛️ **GPS Centri Specializzati** — Anche i Centri Specializzati (tab3 Primo Soccorso) ora hanno 3 pulsanti navigazione (GMaps, Waze, Apple Maps) sia nel popup mappa che nella lista con card strutturata e coordinate GPS visibili
            - 🩺 **st.title() rimosso da show_manovre()** — Eliminato titolo ridondante nella funzione Manovre di Primo Soccorso
            - 💬 **chat.py / segnala_evento.py aggiornati** — Banner sostituisce st.title() in tutti i moduli
            - ✅ **Zero st.title() residui** — Tutti i moduli usano banner tematizzati come intestazione principale
            """)

        st.markdown("---")

        # Versione 2.9.5
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.5</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.5 (Aprile 2026)
            #### Navigazione GPS completa — Punti raccolta e ospedali

            - 🗺️ **GPS Navigazione multi-app** — Ogni punto di raccolta e ospedale ora ha 3 pulsanti di navigazione diretta: **Google Maps**, **Waze**, **Apple Maps**. Link calcolati su coordinate GPS reali
            - 📍 **Coordinate GPS visibili** — Le coordinate (lat, lon) appaiono in ogni card della lista e nel popup della mappa, in formato monospace copiabile
            - 🎨 **Card punti raccolta redesigned** — Nuova struttura con barra colorata per tipo rischio (rosso=terremoto, blu=alluvione, arancio=incendio, verde=tuttirischi), badge tipo, contatto cliccabile, sezione navigazione separata
            - 🏥 **Card ospedali PS redesigned** — Stessa struttura per gli ospedali del Pronto Soccorso con bordo rosso, GPS e 3 link navigazione
            - 🗺️ **Popup mappa migliorati** — Popup Folium per punti raccolta e ospedali riscritti con tabella info + 3 pulsanti navigazione colorati
            """)

        st.markdown("---")

        # Versione 2.9.4
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.4</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.4 (Aprile 2026)
            #### Banner visivi tematizzati per tutte le 15 sezioni

            - 🎨 **Nuovo modulo banner_utils.py** — Funzione `render_banner()` con gradiente colorato, emoji grande, titolo, sottotitolo e watermark di sfondo semi-trasparente
            - 🖼️ **15 sezioni con banner** — Home (blu navy), Monitoraggio (indaco + badge LIVE), Vulcani (rosso), Allerte (arancio + badge LIVE), Meteo (oceano), Qualità Aria (verde), Numeri Utili (teal), Chat (viola), Emergenza (rosso), Primo Soccorso (fucsia), Segnala (ambra), Donazioni (verde oliva), Fonti (grafite), Note di Rilascio (blu), Licenza (grigio)
            - ✅ **st.title() rimossi** — Tutti i 15 moduli ora usano il banner come intestazione visiva principale
            """)

        st.markdown("---")

        # Versione 2.9.3
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.3</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.3 (Aprile 2026)
            #### Fix critico Chat, footer versione, log moderazione robusto

            - 🔧 **Fix log moderazione (Streamlit Cloud)** — Riscritta logica di inizializzazione del FileHandler: prima verifica scrittura file con `open(..., "a")` test, poi aggiunge il FileHandler. Elimina `[Errno 2] No such file or directory` che bloccava il caricamento della Chat su Streamlit Cloud
            - 📋 **Footer versione corretto** — Footer aggiornato da 2.8.0 a 2.9.3 (era rimasto all'aggiornamento precedente)
            - 📋 **Note di rilascio aggiornate** — Aggiunte voci v2.9.1 (ottimizzazione immagini) e v2.9.2 (mappe full-width) al changelog
            """)

        st.markdown("---")

        # Versione 2.9.2
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.2</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.2 (Aprile 2026)
            #### Mappe full-width nei moduli Chat, Meteo, Vulcani, Segnalazioni

            - 🗺️ **Chat e Chat Enhanced** — Mappe Folium portate a width=1100px (era 700px)
            - 🗺️ **Segnala Evento e Segnala Evento Enhanced** — Mappe a width=1100px
            - 🌤️ **Meteo** — Mappa radar e allerte a width=1100px, colonne a 500px
            - 🌋 **Vulcani** — Mappa singolo vulcano a width=1100px (era 820px)
            """)

        st.markdown("---")

        # Versione 2.9.1
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.1</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.1 (Aprile 2026)
            #### Ottimizzazione immagini — conversione PNG→JPEG, risparmio -95%

            - 🖼️ **5 immagini PNG → JPEG** — Convertiti: `image_1743847188766`, `image_1743847226155`, `image_1743854826822`, `image_1743854881664`, `bambino`. Risparmio da 1.5MB a 68KB per i file più grandi (-95%)
            - ⚡ **Caricamento più rapido** — Immagini Primo Soccorso (RCP, bambini) e decorative ottimizzate per connessioni lente
            """)

        st.markdown("---")

        # Versione 2.9.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.9.0</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.9.0 (Aprile 2026)
            #### Primo Soccorso — completamento totale database regionale, fix mappe e deduplicazione

            - 🏥 **Pronto Soccorso — 20 regioni complete** — Aggiunti ospedali per tutte le 9 regioni mancanti: Basilicata (San Carlo Potenza, Madonna delle Grazie Matera), Calabria (Pugliese-Ciaccio, Bianchi-Melacrino-Morelli, AO Cosenza), Friuli-VG (Cattinara Trieste, SM Misericordia Udine, San Giovanni di Dio Gorizia), Liguria (San Martino Genova, Gaslini, Sant'Andrea La Spezia, San Paolo Savona), Molise (Cardarelli Campobasso, Veneziale Isernia), Sardegna (Brotzu, AOU Cagliari, SS Annunziata Sassari, San Francesco Nuoro), Trentino-AA (Santa Chiara Trento, Ospedale Bolzano, Merano), Umbria (SM Misericordia Perugia, Santa Maria Terni), Valle d'Aosta (Umberto Parini Aosta)
            - 🗺️ **Mappe Primo Soccorso full-width** — Tutte e 3 le mappe ora a width=1000px: Pronto Soccorso (tab2), Centri Specializzati (tab3), Punti Raccolta (tab4). Eliminato spazio bianco
            - 🔁 **Deduplicazione sezione RCP** — Rimosso blocco testo-only RCP ridondante dopo `show_manovre()` che già mostra le stesse istruzioni con immagini e video tutorial
            - 🏛️ **Ospedali nel tab Centri Specializzati** — Aggiunto filtro "Ospedali" con 14 policlinici universitari e ospedali principali da Nord a Sud
            - 📍 **Punti raccolta — coordinate reali** — Coordinate reali per tutte le regioni. Eliminato fallback `lat=41.9, lon=12.5` (centro Italia generico)
            """)

        st.markdown("---")

        # Versione 2.8.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#2563eb; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.8.0</h3>
                <p>Aprile 2026</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            ### Versione 2.8.0 (Aprile 2026)
            #### Bug fix massicci, vulcani completi, mappe full-width, MeteoAlarm in italiano

            - 🌋 **Vulcani — dropdown completo** — Aggiunti 7 vulcani mancanti: Colli Albani, Monte Amiata, Ustica, Linosa, Salina, Alicudi, Filicudi. Rimosso Stromboli duplicato. Totale: 16 vulcani nel dropdown con schede dettagliate
            - 🗺️ **Mappe full-width** — Tutte le mappe Folium ora usano width=1100px (era 400-780px): sismico, intensità, vulcani, emergenza, vulcano singolo. Niente più spazio bianco a destra
            - 🇮🇹 **MeteoAlarm in italiano** — Aggiunte 50+ traduzioni automatiche EN→IT. "Yellow Thunderstorm Warning issued for Italy - Sardegna" → "Allerta Gialla Temporali — Sardegna". Tutti i livelli, tutti i tipi di allerta, tutte le regioni
            - 🔧 **Fix log moderazione** — Path log dinamico relativo al file (non più hardcoded `/mount/src/...`). Fallback automatico a stdout su filesystem read-only (Streamlit Cloud)
            - 🔧 **Fix previsioni meteo** — Rimosso `forecast_cols undefined` nell'interfaccia OpenWeather: intestazione "Previsioni 5 giorni" e colonne ora definite prima del caricamento dati
            - 🎨 **Fix qualità aria** — Corretto `KeyError: _color` nella funzione di stile tabella. Ora usa `color_map` via indice invece di colonna già droppata dal DataFrame
            """)

        st.markdown("---")

        # Versione 2.7.0
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("""
            <div style="background-color:#7C3AED; color:white; padding:10px; border-radius:5px; text-align:center;">
                <h3>v2.7.0</h3>
                <p>Aprile 2026</p>
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
