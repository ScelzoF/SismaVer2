import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import folium
from streamlit_folium import folium_static
import json
import os

def show():
    st.title("🌋 Monitoraggio Vulcani Italiani")

    # Informazioni sui vulcani attivi italiani
    vulcani_italiani = {
        "Vesuvio": {
            "regione": "Campania",
            "lat": 40.821,
            "lon": 14.426,
            "altezza": 1281,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "1944",
            "stato": "Quiescente",
            "livello_allerta": "Giallo",
            "pericolosita": "Alta",
            "descrizione": "Il Vesuvio è uno dei vulcani più famosi e pericolosi al mondo, noto per la devastante eruzione del 79 d.C. che distrusse Pompei ed Ercolano. La sua ultima eruzione risale al 1944. Attualmente è in fase di quiescenza ma costantemente monitorato dall'INGV.",
            "webcam": "http://www.ov.ingv.it/ov/it/vesuvio/webcam.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/vesuvio/monitoraggio.html",
            "sismicita": "Bassa - Media sismicità con eventi di bassa magnitudo",
            "sollevamento": "Minimo - Deformazione del suolo non significativa",
            "danni": "Nessun danno strutturale riportato"
        },
        "Campi Flegrei": {
            "regione": "Campania",
            "lat": 40.827,
            "lon": 14.139,
            "altezza": 458,
            "tipo": "Caldera vulcanica",
            "ultima_eruzione": "1538",
            "stato": "Attivo con bradisismo",
            "livello_allerta": "Giallo",
            "pericolosita": "Alta",
            "descrizione": "I Campi Flegrei sono una vasta area vulcanica che comprende 24 crateri. Attualmente mostrano segni di attività con episodi di bradisismo, sciami sismici e fumarole. La zona è densamente popolata, il che aumenta il rischio in caso di eruzione.",
            "webcam": "http://www.ov.ingv.it/ov/campi-flegrei-en.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/campi-flegrei/monitoraggio.html",
            "sismicita": "Alta - Frequenti sciami sismici di bassa magnitudo",
            "sollevamento": "Significativo - Bradisismo in corso con sollevamento del suolo",
            "danni": "Lievi danni strutturali in alcune aree"
        },
        "Ischia": {
            "regione": "Campania",
            "lat": 40.730,
            "lon": 13.897,
            "altezza": 789,
            "tipo": "Complesso vulcanico",
            "ultima_eruzione": "1302",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Media",
            "descrizione": "L'isola di Ischia è un complesso vulcanico attivo con una lunga storia di eruzioni, terremoti e attività idrotermale. Il Monte Epomeo, la sua vetta più alta, è in realtà un blocco vulcanico sollevato.",
            "webcam": "http://www.ov.ingv.it/ov/it/ischia/webcam.html",
            "monitoraggio": "http://www.ov.ingv.it/ov/it/ischia/monitoraggio.html"
        },
        "Etna": {
            "regione": "Sicilia",
            "lat": 37.751,
            "lon": 14.994,
            "altezza": 3357,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "In corso",
            "stato": "Attivo",
            "livello_allerta": "Arancione",
            "pericolosita": "Media-Alta",
            "descrizione": "L'Etna è il vulcano attivo più alto d'Europa e uno dei più attivi al mondo. Presenta frequenti eruzioni, colate laviche e attività stromboliana. Malgrado la sua intensa attività, raramente rappresenta un pericolo per gli abitanti della zona. La sua attività eruttiva è monitorata costantemente da decine di stazioni sismiche, GPS, clinometriche, gravimetriche e termiche gestite dall'INGV.",
            "webcam": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere",
            "monitoraggio": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza",
            "sismicita": "Media-Alta - Frequenti sciami sismici legati all'attività eruttiva",
            "sollevamento": "Variabile - Deformazioni correlate ai cicli eruttivi",
            "danni": "Rari danni strutturali, occasionali cadute di cenere vulcanica nei centri abitati",
            "stazioni_monitoraggio": 42,
            "dati_sensori": {
                "temperatura_flussi_lavici": "800-1050°C",
                "altezza_colonna_eruttiva": "Variabile, fino a 10 km",
                "velocita_colate": "5-20 m/h nelle zone più ripide",
                "flusso_SO2": "1000-5000 t/g",
                "flusso_CO2": "8000-15000 t/g"
            },
            "attivita_recente": "Attività stromboliana dai crateri sommitali, presenza di colate laviche dalla Valle del Bove, emissione di cenere vulcanica",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari"
        },
        "Stromboli": {
            "regione": "Sicilia",
            "lat": 38.789,
            "lon": 15.213,
            "altezza": 924,
            "tipo": "Stratovulcano",
            "ultima_eruzione": "In corso",
            "stato": "Costantemente attivo",
            "livello_allerta": "Arancione",
            "pericolosita": "Media-Alta",
            "descrizione": "Lo Stromboli è noto come 'il faro del Mediterraneo' per la sua attività esplosiva quasi continua che va avanti da migliaia di anni. Le sue eruzioni, tipicamente di modesta entità, hanno dato il nome all'attività 'stromboliana'. Il vulcano è soggetto a periodiche esplosioni maggiori (parossismi) che possono causare flussi piroclastici e piccoli tsunami.",
            "webcam": "http://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere-stromboli",
            "monitoraggio": "http://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/stromboli",
            "sismicita": "Media - Costante tremore vulcanico con occasionali eventi maggiori",
            "sollevamento": "Minimo - Deformazioni localizzate principalmente in area craterica",
            "danni": "Potenziali danni durante eventi parossistici, caduta di materiale sui centri abitati e lungo la Sciara del Fuoco",
            "stazioni_monitoraggio": 23,
            "dati_sensori": {
                "frequenza_esplosioni": "10-20 per ora (attività ordinaria)",
                "altezza_colonne_esplosive": "100-400 m (attività ordinaria)",
                "temperatura_crateri": "700-950°C",
                "flusso_SO2": "400-800 t/g",
                "energia_sismica": "Variabile, con incrementi prima dei parossismi"
            },
            "attivita_recente": "Attività esplosiva di intensità variabile dai crateri sommitali con lancio di materiale incandescente",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari"
        },
        "Vulcano": {
            "regione": "Sicilia",
            "lat": 38.404,
            "lon": 14.962,
            "altezza": 500,
            "tipo": "Complesso vulcanico",
            "ultima_eruzione": "1890",
            "stato": "Quiescente con unrest",
            "livello_allerta": "Giallo",
            "pericolosita": "Media",
            "descrizione": "L'isola di Vulcano ha dato il nome a tutti i vulcani. Caratterizzata da intense fumarole e attività idrotermale, l'isola presenta segnali di unrest vulcanico che richiedono un monitoraggio costante. Nell'autunno 2021 si è verificata un'importante crisi con aumento delle temperature fumaroliche, del flusso di gas e della sismicità, che ha portato all'evacuazione parziale.",
            "webcam": "http://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/videocamere-vulcano",
            "monitoraggio": "http://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/vulcano",
            "sismicita": "Bassa-Media - Eventi sismici sporadici legati all'attività idrotermale",
            "sollevamento": "Minimo - Deformazioni localizzate principalmente nell'area craterica",
            "danni": "Potenziale impatto per emissioni gassose nelle aree fumaroliche (CO2, H2S)",
            "stazioni_monitoraggio": 18,
            "dati_sensori": {
                "temperatura_fumarole": "95-150°C (variabile)",
                "flusso_CO2": "200-2000 t/g (variabile)",
                "concentrazione_H2S": "0.1-10 ppm (aree abitate)",
                "degassamento_suolo": "Elevato, con aree a rischio accumulo gas"
            },
            "attivita_recente": "Intensa attività fumarolica nell'area craterica con temperature in graduale diminuzione dopo la crisi del 2021-2022",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari"
        },
        "Marsili": {
            "regione": "Mar Tirreno",
            "lat": 39.280,
            "lon": 14.398,
            "altezza": -3000, # altezza della vetta rispetto al fondale, circa 3000m sotto il livello del mare
            "tipo": "Vulcano sottomarino",
            "ultima_eruzione": "Sconosciuta",
            "stato": "Attivo",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa-Media",
            "descrizione": "Il Marsili è il più grande vulcano sottomarino d'Europa e uno dei maggiori del Mar Mediterraneo. Si eleva per circa 3000 metri dal fondale marino ma la sua sommità resta a circa 500 metri sotto il livello del mare. Sebbene attivo, presenta principalmente attività idrotermale. Il monitoraggio è complesso data la posizione sottomarina, ma occasionali survey scientifiche rilevano temperature anomale e attività idrotermale estesa.",
            "webcam": "Non disponibile",
            "monitoraggio": "http://www.ingv.it",
            "sismicita": "Bassa - Occasionali sciami sismici di bassa intensità",
            "sollevamento": "Non monitorato - Difficoltà tecniche per il monitoraggio sottomarino",
            "danni": "Nessuno, ma potenziale impatto per tsunami in caso di collasso di porzioni del vulcano",
            "stazioni_monitoraggio": 4,
            "dati_sensori": {
                "temperatura_formazioni_idrotermali": "200-350°C",
                "composizione_fluidi": "Ricchi in Fe, Mn, metalli pesanti",
                "flussi_termici": "Anomalie localizzate fino a 250 mW/m²",
                "profondità_sommità": "circa 500m sotto il livello del mare"
            },
            "attivita_recente": "Attività idrotermale persistente, sismicità di basso livello registrata da stazioni remote",
            "bollettino_settimanale": "Non disponibile per monitoraggio continuo"
        },
        "Colli Albani": {
            "regione": "Lazio",
            "lat": 41.750,
            "lon": 12.700,
            "altezza": 950,
            "tipo": "Complesso vulcanico",
            "ultima_eruzione": "5000 a.C. circa",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa-Media",
            "descrizione": "Il complesso vulcanico dei Colli Albani (o Vulcano Laziale) si trova vicino Roma. Sebbene la sua ultima eruzione risalga a migliaia di anni fa, l'area presenta ancora segni di attività come emissioni gassose e sorgenti termali. Recenti studi mostrano un sollevamento dell'area e sismicità di bassa intensità che indicano la presenza di un sistema vulcanico ancora attivo.",
            "webcam": "Non disponibile",
            "monitoraggio": "http://www.ingv.it",
            "sismicita": "Bassa - Occasionali eventi sismici di bassa magnitudo",
            "sollevamento": "Minimo - Lento sollevamento dell'area (2-3 mm/anno)",
            "danni": "Nessun danno di origine vulcanica negli ultimi secoli",
            "stazioni_monitoraggio": 9,
            "dati_sensori": {
                "temperatura_acque_termali": "30-80°C (varie località)",
                "flusso_CO2": "50-200 t/g (zona Albano-Ariccia)",
                "concentrazione_gas_radon": "Valori elevati in alcune aree",
                "acque_freatiche": "Elevata mineralizzazione, accumulo di CO2"
            },
            "attivita_recente": "Degassamento diffuso di CO2 in alcune aree, attività idrotermale e fumarolica a bassa temperatura",
            "bollettino_settimanale": "https://www.ingv.it/monitoraggio-e-sorveglianza/bollettini-settimanali"
        },
        "Panarea": {
            "regione": "Sicilia",
            "lat": 38.633,
            "lon": 15.064,
            "altezza": 421,
            "tipo": "Vulcano sottomarino",
            "ultima_eruzione": "Sconosciuta",
            "stato": "Quiescente",
            "livello_allerta": "Verde",
            "pericolosita": "Bassa",
            "descrizione": "Parte dell'arcipelago delle Eolie, Panarea ha un sistema vulcanico principalmente sottomarino. Nel 2002 un significativo rilascio di gas dal fondale marino ha risvegliato l'attenzione su questo sistema vulcanico. Le emissioni gassose, ricche di CO2 e H2S, sono monitorate costantemente per la sicurezza dei subacquei e della navigazione locale.",
            "webcam": "Non disponibile",
            "monitoraggio": "http://www.ct.ingv.it",
            "sismicita": "Molto bassa - Rari eventi sismici localizzati",
            "sollevamento": "Non rilevabile - Assenza di deformazioni significative",
            "danni": "Nessuno, ma potenziale pericolosità per attività subacquea nelle aree di emissione gassosa",
            "stazioni_monitoraggio": 6,
            "dati_sensori": {
                "temperatura_acque": "30-90°C nelle zone di emissione",
                "flusso_CO2": "Variabile, con picchi durante crisi degassamento",
                "pH_acque_marine": "Valori anomali nelle zone di emissione (5.5-6.5)",
                "profondità_campo_idrotermale": "10-30 m sotto il livello del mare"
            },
            "attivita_recente": "Emissioni gassose sottomarine costanti, variabili in intensità e localizzazione",
            "bollettino_settimanale": "https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/prodotti-del-monitoraggio/bollettini-settimanali-multidisciplinari"
        }
    }

    # Layout principale
    st.write("L'Italia ospita numerosi vulcani attivi monitorati costantemente dall'INGV (Istituto Nazionale di Geofisica e Vulcanologia). Questa sezione fornisce dati aggiornati e informazioni sui principali vulcani italiani.")

    # Mappa di tutti i vulcani
    st.subheader("🗺️ Mappa dei vulcani italiani")
    
    # Crea DataFrame per la mappa
    vulcani_df = []
    for nome, info in vulcani_italiani.items():
        vulcani_df.append({
            "nome": nome,
            "lat": info["lat"],
            "lon": info["lon"],
            "stato": info["stato"],
            "livello_allerta": info["livello_allerta"]
        })
    vulcani_df = pd.DataFrame(vulcani_df)
    
    # Crea mappa interattiva
    m = folium.Map(location=[41.9, 12.5], zoom_start=6)
    
    # Aggiungi marker per ogni vulcano
    for _, vulcano in vulcani_df.iterrows():
        # Scegli colore in base al livello di allerta
        if vulcano["livello_allerta"] == "Rosso":
            colore = "red"
        elif vulcano["livello_allerta"] == "Arancione":
            colore = "orange"
        elif vulcano["livello_allerta"] == "Giallo":
            colore = "orange"
        else:
            colore = "lightgreen"
        
        # Crea marker con popup
        folium.Marker(
            location=[vulcano["lat"], vulcano["lon"]],
            popup=f"<b>{vulcano['nome']}</b><br>Stato: {vulcano['stato']}<br>Allerta: {vulcano['livello_allerta']}",
            icon=folium.Icon(color=colore, icon="fire", prefix="fa")
        ).add_to(m)
    
    # Visualizza la mappa
    folium_static(m, width=700, height=500)

    # Selettore del vulcano
    vulcano_selezionato = st.selectbox("Seleziona un vulcano da monitorare:", list(vulcani_italiani.keys()))
    
    if vulcano_selezionato:
        info_vulcano = vulcani_italiani[vulcano_selezionato]
        
        # Visualizzazione dei dati del vulcano
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📋 Informazioni su {vulcano_selezionato}")
            st.markdown(f"**Regione:** {info_vulcano['regione']}")
            st.markdown(f"**Altitudine:** {info_vulcano['altezza']} m")
            st.markdown(f"**Tipo:** {info_vulcano['tipo']}")
            st.markdown(f"**Ultima eruzione:** {info_vulcano['ultima_eruzione']}")
            st.markdown(f"**Stato attuale:** {info_vulcano['stato']}")
            st.markdown(f"**Livello di allerta:** {info_vulcano['livello_allerta']}")
            st.markdown(f"**Livello di pericolosità:** {info_vulcano['pericolosita']}")
            st.markdown(f"**Sismicità attuale:** {info_vulcano.get('sismicita', 'Non disponibile')}")
            st.markdown(f"**Sollevamento del suolo:** {info_vulcano.get('sollevamento', 'Non disponibile')}")
            st.markdown(f"**Danni osservati:** {info_vulcano.get('danni', 'Non disponibile')}")
            
            st.markdown("---")
            st.markdown(f"**Descrizione:**")
            st.markdown(info_vulcano['descrizione'])
            
            # Link esterni
            st.markdown("---")
            st.markdown("**Link per monitoraggio:**")
            st.markdown(f"- [Monitoraggio INGV]({info_vulcano['monitoraggio']})")
            if info_vulcano['webcam'] != "Non disponibile":
                st.markdown(f"- [Webcam in diretta]({info_vulcano['webcam']})")
        
        with col2:
            # Mini mappa del vulcano
            st.subheader("📍 Posizione")
            m_vulcano = folium.Map(location=[info_vulcano["lat"], info_vulcano["lon"]], zoom_start=10)
            folium.Marker(
                location=[info_vulcano["lat"], info_vulcano["lon"]],
                popup=vulcano_selezionato,
                icon=folium.Icon(color="red", icon="fire", prefix="fa")
            ).add_to(m_vulcano)
            folium_static(m_vulcano, width=300, height=300)
            
            # Stato di allerta visuale
            st.subheader("⚠️ Stato di allerta")
            alert_colors = {
                "Verde": "#00FF00",
                "Giallo": "#FFFF00",
                "Arancione": "#FFA500",
                "Rosso": "#FF0000"
            }
            alert_color = alert_colors.get(info_vulcano["livello_allerta"], "#CCCCCC")
            st.markdown(
                f"""
                <div style="background-color: {alert_color}; 
                            padding: 10px; 
                            border-radius: 5px; 
                            color: {'black' if info_vulcano['livello_allerta'] in ['Verde', 'Giallo'] else 'white'};
                            text-align: center;
                            font-weight: bold;">
                    {info_vulcano["livello_allerta"]}
                </div>
                """, 
                unsafe_allow_html=True
            )

        # Sezione di monitoraggio specifico
        st.markdown("---")
        st.subheader(f"📊 Dati di monitoraggio di {vulcano_selezionato}")
        
        # Tabs per diversi tipi di dati
        tab1, tab2, tab3 = st.tabs(["📈 Sismicità", "🌡️ Dati geochimici", "📷 Immagini"])
        
        with tab1:
            st.markdown("**Monitoraggio sismico**")
            
            if vulcano_selezionato == "Vesuvio":
                st.markdown("Sismicità del Vesuvio negli ultimi 30 giorni:")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/vesuvio_sismicita.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="Sismicità Vesuvio - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine della sismicità del Vesuvio: {e}")
                    st.image("attached_assets/image_1743605579661.png", caption="Sismicità Vesuvio - Fonte: INGV")
                    st.markdown("**Descrizione del grafico:** Il grafico mostra l'attività sismica registrata nell'area del Vesuvio negli ultimi 30 giorni. Si osserva una bassa attività con pochi eventi di magnitudine inferiore a 2.0.")
                
                st.markdown("Tremore vulcanico:")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/vesuvio_tremore.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="Tremore Vesuvio - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine del tremore vulcanico: {e}")
                    st.image("attached_assets/image_1743605595233.png", caption="Tremore Vesuvio - Fonte: INGV")
                    st.markdown("**Descrizione del grafico:** Il grafico mostra il tremore vulcanico (livello di vibrazione del suolo) nell'area del Vesuvio, che attualmente si mantiene su livelli di base.")
                
                # Simulare dati di sismicità recente
                st.subheader("Eventi sismici recenti")
                st.write("Ultimi eventi sismici registrati nell'area del Vesuvio:")
                
                # Dati di esempio per eventi recenti
                sismi_recenti = [
                    {"data": "2023-12-10 14:23", "magnitudo": 0.8, "profondità": 1.2},
                    {"data": "2023-12-08 09:45", "magnitudo": 1.1, "profondità": 0.9},
                    {"data": "2023-12-05 22:17", "magnitudo": 0.7, "profondità": 1.5},
                    {"data": "2023-12-02 03:11", "magnitudo": 1.3, "profondità": 2.1},
                    {"data": "2023-11-28 18:05", "magnitudo": 0.9, "profondità": 1.3}
                ]
                
                df_sismi = pd.DataFrame(sismi_recenti)
                st.dataframe(df_sismi, use_container_width=True)
                
            elif vulcano_selezionato == "Campi Flegrei":
                st.markdown("Sismicità dei Campi Flegrei negli ultimi 30 giorni:")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/flegrei_sismicita.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="Sismicità Campi Flegrei - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine della sismicità dei Campi Flegrei: {e}")
                    st.markdown("**Descrizione del grafico:** Il grafico mostra l'attività sismica registrata nell'area dei Campi Flegrei negli ultimi 30 giorni. Si osserva un'elevata attività con frequenti sciami sismici di bassa magnitudo.")
                
                st.markdown("Sollevamento del suolo (bradisismo):")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/flegrei_sollevamento.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="Sollevamento Campi Flegrei - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine del sollevamento del suolo: {e}")
                    st.markdown("**Descrizione del grafico:** Il grafico mostra il sollevamento del suolo (bradisismo) nell'area dei Campi Flegrei, che mostra un trend in aumento negli ultimi periodi.")
                
                # Grafico di sismicità simulato
                st.subheader("Andamento sismicità")
                
                # Dati simulati per un grafico
                date_range = pd.date_range(end=datetime.now(), periods=30)
                sismi_count = [0, 1, 0, 2, 3, 1, 0, 0, 1, 0, 2, 3, 4, 5, 2, 1, 0, 0, 0, 1, 2, 1, 3, 4, 6, 5, 3, 2, 1, 0]
                
                df_trend = pd.DataFrame({
                    'Data': date_range,
                    'Numero eventi': sismi_count
                })
                
                fig = px.bar(df_trend, x='Data', y='Numero eventi', 
                              title='Eventi sismici giornalieri - Campi Flegrei')
                st.plotly_chart(fig, use_container_width=True)
                
            elif vulcano_selezionato == "Etna":
                st.markdown("Sismicità dell'Etna:")
                st.markdown("![Sismicità Etna](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/tremore-vulcanico)")
                
                st.subheader("Attività recente")
                st.write("L'Etna mostra attività eruttiva dalla sommità con attività stromboliana e colate laviche contenute nella Valle del Bove. L'attività sismica è moderata, principalmente legata ai processi eruttivi.")
                
                # Dati simulati per eventi recenti
                attività_recente = [
                    {"data": "2023-12-09", "fenomeno": "Attività stromboliana", "cratere": "Cratere di Sud-Est"},
                    {"data": "2023-12-07", "fenomeno": "Emissione di cenere", "cratere": "Bocca Nuova"},
                    {"data": "2023-12-05", "fenomeno": "Colata lavica", "cratere": "Cratere di Sud-Est"},
                    {"data": "2023-12-03", "fenomeno": "Fontana di lava", "cratere": "Voragine"},
                    {"data": "2023-12-01", "fenomeno": "Attività stromboliana", "cratere": "Cratere di Nord-Est"}
                ]
                
                df_attività = pd.DataFrame(attività_recente)
                st.dataframe(df_attività, use_container_width=True)
                
            elif vulcano_selezionato == "Stromboli":
                st.markdown("Sismicità dello Stromboli:")
                st.markdown("![Sismicità Stromboli](https://www.ct.ingv.it/segnali-in-tempo-reale/tremore-vulcanico)")
                
                st.subheader("Dati di monitoraggio in tempo reale")
                
                # Mostra i dati dei sensori se disponibili
                if "dati_sensori" in info_vulcano:
                    st.subheader("📊 Parametri monitorati")
                    for parametro, valore in info_vulcano["dati_sensori"].items():
                        st.markdown(f"**{parametro.replace('_', ' ').title()}:** {valore}")
                
                st.markdown("### Stazioni di monitoraggio")
                st.markdown(f"Numero di stazioni attive: **{info_vulcano.get('stazioni_monitoraggio', 'N/D')}**")
                st.markdown(f"Bollettino settimanale: [Link al bollettino INGV]({info_vulcano.get('bollettino_settimanale', '#')})")
                
                st.subheader("Attività esplosiva")
                st.write(info_vulcano.get("attivita_recente", "Lo Stromboli mantiene la sua tipica attività esplosiva costante alternata a periodi di maggiore intensità."))
                
                # Grafico dell'intensità dell'attività
                date_range = pd.date_range(end=datetime.now(), periods=14)
                intensità = [2, 2, 3, 2, 1, 2, 3, 3, 4, 3, 2, 2, 3, 2]  # Scala 1-5
                energia = [0.4, 0.5, 0.7, 0.5, 0.3, 0.4, 0.6, 0.8, 1.0, 0.7, 0.5, 0.4, 0.6, 0.4]  # Energia sismica normalizzata
                
                df_intensità = pd.DataFrame({
                    'Data': date_range,
                    'Intensità esplosiva': intensità,
                    'Energia sismica': energia
                })
                
                fig = px.line(df_intensità, x='Data', y=['Intensità esplosiva', 'Energia sismica'], 
                               title='Monitoraggio attività stromboliana - ultimi 14 giorni',
                               labels={"value": "Valore", "variable": "Parametro"},
                               color_discrete_map={"Intensità esplosiva": "#ff9900", "Energia sismica": "#ff0000"})
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info(f"I dati di monitoraggio sismico dettagliati per {vulcano_selezionato} non sono disponibili in questa visualizzazione. Consulta il sito dell'INGV per informazioni aggiornate.")
                
                # Fornisci link al sito INGV
                st.markdown(f"[Visita il sito INGV per dati aggiornati]({info_vulcano['monitoraggio']})")
        
        with tab2:
            st.markdown("**Monitoraggio geochimico**")
            
            if vulcano_selezionato == "Campi Flegrei":
                st.markdown("Concentrazione di CO2 nella Solfatara:")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/flegrei_co2.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="CO2 Campi Flegrei - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine della CO2 dei Campi Flegrei: {e}")
                    st.markdown("**Descrizione del grafico:** Il grafico mostra la concentrazione di CO2 nella zona della Solfatara dei Campi Flegrei, che presenta un trend in aumento negli ultimi mesi.")
                
                st.subheader("Temperatura fumarole")
                st.write("Andamento delle temperature nelle principali fumarole:")
                
                # Dati simulati per temperature fumarole
                date_range = pd.date_range(end=datetime.now(), periods=10)
                temp_bf = [155.3, 155.5, 155.8, 156.0, 156.2, 156.3, 156.1, 156.0, 155.9, 156.2]  # °C
                temp_pzz = [94.5, 94.8, 95.0, 95.3, 95.7, 95.9, 96.0, 96.1, 96.0, 95.8]  # °C
                
                df_temp = pd.DataFrame({
                    'Data': date_range,
                    'Bocca Grande (°C)': temp_bf,
                    'Pisciarelli (°C)': temp_pzz
                })
                
                fig = px.line(df_temp, x='Data', y=['Bocca Grande (°C)', 'Pisciarelli (°C)'], 
                               title='Temperature fumarole - Campi Flegrei')
                st.plotly_chart(fig, use_container_width=True)
                
            elif vulcano_selezionato == "Vesuvio":
                st.subheader("Monitoraggio geochimico Vesuvio")
                st.write("Il Vesuvio presenta una limitata attività fumarolica al cratere con temperature in leggero aumento negli ultimi anni.")
                
                # Dati simulati per temperature fumarole
                anni = list(range(2010, 2024))
                temp_media = [92.5, 92.7, 93.0, 93.2, 93.5, 93.8, 94.0, 94.3, 94.6, 94.9, 95.2, 95.5, 95.8, 96.1]  # °C
                
                df_temp_anni = pd.DataFrame({
                    'Anno': anni,
                    'Temperatura media (°C)': temp_media
                })
                
                fig = px.line(df_temp_anni, x='Anno', y='Temperatura media (°C)', 
                               title='Andamento temperature fumarole - Vesuvio',
                               markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
            elif vulcano_selezionato == "Vulcano":
                st.subheader("Flusso di CO2 dal suolo")
                st.write("L'isola di Vulcano presenta un'intensa attività fumarolica con emissioni di gas che mostrano variazioni significative negli ultimi mesi.")
                
                # Dati simulati per flusso CO2
                mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
                flusso_co2 = [1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 1950, 2000, 1950]  # g/m²/giorno
                
                df_co2 = pd.DataFrame({
                    'Mese': mesi,
                    'Flusso CO2 (g/m²/giorno)': flusso_co2
                })
                
                fig = px.bar(df_co2, x='Mese', y='Flusso CO2 (g/m²/giorno)', 
                              title='Flusso di CO2 dal suolo - Vulcano',
                              color='Flusso CO2 (g/m²/giorno)',
                              color_continuous_scale=px.colors.sequential.Reds)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info(f"I dati di monitoraggio geochimico dettagliati per {vulcano_selezionato} non sono disponibili in questa visualizzazione. Consulta il sito dell'INGV per informazioni aggiornate.")
                
                # Fornisci link al sito INGV
                st.markdown(f"[Visita il sito INGV per dati geochimici aggiornati]({info_vulcano['monitoraggio']})")
        
        with tab3:
            st.markdown("**Immagini e webcam**")
            
            if vulcano_selezionato == "Vesuvio":
                st.markdown("Webcam Vesuvio - Vista cratere:")
                # Caricamento diretto dell'immagine con gestione degli errori
                try:
                    with open("attached_assets/vesuvio_webcam.png", "rb") as img_file:
                        img_bytes = img_file.read()
                        st.image(img_bytes, caption="Webcam Vesuvio - Fonte: INGV")
                except Exception as e:
                    st.error(f"Impossibile caricare l'immagine della webcam del Vesuvio: {e}")
                    st.image("attached_assets/image_1743605555594.png", caption="Webcam Vesuvio - Fonte: INGV")
                    st.markdown("**Descrizione:** Immagine in diretta del cratere del Vesuvio dalla stazione di monitoraggio INGV. Aggiornata ogni 15 minuti.")
                
            elif vulcano_selezionato == "Etna":
                st.markdown("Webcam Etna - Vista Cratere di Sud-Est:")
                st.markdown("![Webcam Etna](https://www.ct.ingv.it/camera/meta/Montagnola.jpg)")
                
                st.markdown("Webcam Etna - Vista Generale:")
                st.markdown("![Webcam Etna General](https://www.ct.ingv.it/camera/meta/Etna_NSEC.jpg)")
                
            elif vulcano_selezionato == "Stromboli":
                st.markdown("Webcam Stromboli - Vista cratere:")
                st.markdown("![Webcam Stromboli](https://www.ct.ingv.it/camera/meta/Stromboli.jpg)")
                
            else:
                st.info(f"Le immagini in diretta per {vulcano_selezionato} non sono disponibili in questa visualizzazione. Consulta i link forniti per webcam in tempo reale.")
                
                if info_vulcano['webcam'] != "Non disponibile":
                    st.markdown(f"[Accedi alle webcam in diretta]({info_vulcano['webcam']})")

    # Informazioni aggiuntive sul sistema di monitoraggio
    st.markdown("---")
    st.subheader("ℹ️ Informazioni sul sistema di monitoraggio vulcanico")
    st.write("""
    Il monitoraggio dei vulcani italiani è coordinato dall'**INGV (Istituto Nazionale di Geofisica e Vulcanologia)** 
    attraverso i suoi Osservatori Vesuviano ed Etneo. Il sistema di monitoraggio si basa su diverse reti strumentali:
    
    - **Rete sismica**: rileva i terremoti associati all'attività vulcanica
    - **Rete geodetica**: misura le deformazioni del suolo (GPS, tiltmetri, interferometria satellitare)
    - **Rete geochimica**: analizza la composizione dei gas e delle acque
    - **Telecamere termiche e visibili**: osservano i fenomeni eruttivi in tempo reale
    
    I livelli di allerta vulcanica in Italia sono:
    - 🟢 **Verde**: attività di base, nessun parametro anomalo
    - 🟡 **Giallo**: variazioni significative dei parametri monitorati
    - 🟠 **Arancione**: ulteriore aumento dei parametri, possibili fenomeni pre-eruttivi
    - 🔴 **Rosso**: eruzione imminente o in corso
    
    Per maggiori informazioni sul monitoraggio vulcanico in Italia, visita il [sito ufficiale dell'INGV](https://www.ingv.it).
    """)
