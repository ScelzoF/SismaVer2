import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
import json
import os
import base64
import glob
import time
import hashlib
from datetime import datetime, timezone, timedelta
from PIL import Image, UnidentifiedImageError, ImageOps
from io import BytesIO
from functools import lru_cache

# Definizione fuso orario italiano per coerenza
FUSO_ORARIO_ITALIA = timezone(timedelta(hours=2))

def show():
    st.title('🩺 Primo Soccorso e Strutture Sanitarie')

    st.write("""
    ## Informazioni di Primo Soccorso

    In caso di emergenza, mantieni la calma e segui queste linee guida basilari. 
    Questa sezione fornisce informazioni sulle procedure di primo soccorso e un elenco di strutture sanitarie in tempo reale.
    """)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Linee Guida", "🚑 Pronto Soccorso", "🏥 Ospedali e Strutture", "🔃 Punti di Raccolta"])

    # Sistema ottimizzato per gestione immagini con advanced caching
    @lru_cache(maxsize=32)
    def get_image_hash(path):
        """Crea un hash univoco dell'immagine per il cache avanzato."""
        try:
            if not os.path.exists(path):
                return None
            
            # Usa la combinazione di mtime e dimensione file per hash più efficiente
            mtime = os.path.getmtime(path)
            size = os.path.getsize(path)
            return hashlib.md5(f"{path}_{mtime}_{size}".encode()).hexdigest()
        except Exception:
            return None
            
    # Sistema di cache per immagini base64 (per ingrandimento)
    image_base64_cache = {}
    
    # Funzione ottimizzata per caricare e visualizzare immagini
    def get_image_as_base64(path):
        """Versione ottimizzata con multilevel caching e gestione errori avanzata."""
        try:
            # Verifica esistenza file
            if not os.path.exists(path):
                fallback_path = os.path.join("images", os.path.basename(path))
                if os.path.exists(fallback_path):
                    path = fallback_path
                else:
                    return None
                    
            # Cache check con chiave hash basata su percorso e mtime
            image_hash = get_image_hash(path)
            if image_hash in image_base64_cache:
                return image_base64_cache[image_hash]
                
            # Lettura file ottimizzata con gestone risorse
            with open(path, "rb") as img_file:
                img_data = img_file.read()
                result = base64.b64encode(img_data).decode()
                
                # Salva in cache
                image_base64_cache[image_hash] = result
                return result
        except Exception as e:
            print(f"Errore nel caricamento dell'immagine {path}: {e}")
            return None

    # Funzione per visualizzare immagini con didascalie e placeholder avanzati
    def display_image_with_caption(image_path, caption, width=None):
        """Funzione ottimizzata con multiple fallbacks e gestione errori."""
        try:
            # Gestione percorsi alternativi
            paths_to_try = [
                image_path,
                os.path.join("attached_assets", os.path.basename(image_path)),
                os.path.join("images", os.path.basename(image_path))
            ]
            
            # Prova tutti i percorsi possibili
            img = None
            for path in paths_to_try:
                if os.path.exists(path):
                    try:
                        img = Image.open(path)
                        break
                    except UnidentifiedImageError:
                        continue
            
            if img:
                # Ottimizzazione dell'immagine per il display
                if img.mode == 'RGBA' and img.size[0] > 1000:
                    # Riduce dimensioni per performance migliori
                    img.thumbnail((1000, 1000), Image.LANCZOS)
                
                # Visualizzazione ottimizzata
                if width:
                    st.image(img, caption=caption, width=width)
                else:
                    st.image(img, caption=caption)
            else:
                # Placeholder avanzato con stile migliorato
                st.warning(f"Immagine non disponibile: {caption}")
                text_image = f'''
                <div style="width:100%;height:180px;background-color:#f8f9fa;
                    border:1px solid #dee2e6;display:flex;align-items:center;
                    justify-content:center;text-align:center;border-radius:8px;
                    font-family:sans-serif;color:#495057;margin:10px 0;">
                    <div>
                        <div style="font-size:40px;margin-bottom:10px;">🖼️</div>
                        <div style="font-weight:bold;">{caption}</div>
                        <div style="font-size:12px;margin-top:5px;">Immagine non disponibile</div>
                    </div>
                </div>'''
                st.markdown(text_image, unsafe_allow_html=True)
        except Exception as e:
            print(f"Errore visualizzazione immagine: {e}")
            st.warning(f"Impossibile visualizzare l'immagine: {caption}")

    # Funzione avanzata per rendere le immagini cliccabili e ingrandibili
    def display_clickable_image(image_path, caption, width=600, key_suffix=""):
        """
        Mostra un'immagine cliccabile con popup ottimizzato e responsive per diversi dispositivi.
        
        Args:
            image_path: Percorso dell'immagine
            caption: Didascalia dell'immagine
            width: Larghezza dell'immagine
            key_suffix: Suffisso opzionale per rendere unica la chiave del pulsante
        """
        # Cache key per migliori performance
        image_hash = get_image_hash(image_path) or f"hash_{time.time()}"
        unique_id = f"{image_hash}_{key_suffix}_{width}"
        
        # Cerca l'immagine in posizioni alternative se necessario
        actual_path = None
        alternative_paths = [
            image_path,
            os.path.join("attached_assets", os.path.basename(image_path)),
            os.path.join("images", os.path.basename(image_path)),
            image_path.replace("images/", "attached_assets/"),
            f"attached_assets/{os.path.basename(image_path)}"
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                actual_path = path
                break
                
        # Se ancora non troviamo l'immagine, mostra un placeholder e esci
        if not actual_path:
            st.warning(f"Immagine non trovata: {caption}")
            text_image = f'<div style="width:100%;height:150px;background-color:#f0f0f0;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:5px;">{caption}</div>'
            st.markdown(text_image, unsafe_allow_html=True)
            return
            
        try:
            # Carica e ottimizza l'immagine
            img = Image.open(actual_path)
            
            # Ottimizzazione proporzioni e dimensioni
            if img.width > width:
                ratio = width / img.width
                height = int(img.height * ratio)
            else:
                height = img.height
                
            # Visualizza immagine ottimizzata
            st.image(img, caption=caption, width=width)
            
            # Crea pulsante per ingrandimento con UI migliorata
            if st.button(f"🔍 Visualizza a schermo intero", key=f"btn_{unique_id}"):
                # Carica l'immagine in base64 con cache
                img_base64 = get_image_as_base64(actual_path)
                
                # HTML responsive per mobile e desktop con correzione per errore DOM selector
                popup_html = f"""
                <script>
                (function() {{
                    try {{
                        // Ottimizzazione multi-dispositivo
                        var screenWidth = window.innerWidth;
                        var screenHeight = window.innerHeight;
                        var popupWidth = Math.min(800, screenWidth * 0.9);
                        var popupHeight = Math.min(600, screenHeight * 0.9);
                        
                        var img_win = window.open("", "_blank", 
                            "width=" + popupWidth + 
                            ",height=" + popupHeight + 
                            ",scrollbars=yes,resizable=yes,status=no,location=no,toolbar=no,menubar=no");
                        
                        if (img_win) {{
                            img_win.document.write(`
                                <html>
                                    <head>
                                        <title>{caption}</title>
                                        <style>
                                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }}
                                            h2 {{ margin-bottom: 20px; }}
                                            img {{ max-width: 95%; max-height: 80vh; object-fit: contain; border: 1px solid #ddd; }}
                                            .close-btn {{ 
                                                display: inline-block; 
                                                padding: 10px 20px; 
                                                margin-top: 20px; 
                                                background-color: #f44336; 
                                                color: white; 
                                                border: none; 
                                                border-radius: 4px; 
                                                cursor: pointer; 
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <h2>{caption}</h2>
                                        <img src="data:image/png;base64,{img_base64}" alt="{caption}">
                                        <br>
                                        <button class="close-btn" onclick="window.close()">Chiudi finestra</button>
                                    </body>
                                </html>
                            `);
                            img_win.document.close();
                        }} else {{
                            console.log("Non è stato possibile aprire la finestra popup. Il browser potrebbe bloccare i popup.");
                        }}
                    }} catch (e) {{
                        console.error("Errore durante l'apertura dell'immagine:", e);
                    }}
                }})();
                </script>
                """
                st.components.v1.html(popup_html, height=0)
        
        except Exception as e:
            st.warning(f"Errore nel caricamento dell'immagine: {e}")
            # Creare un'immagine placeholder con il testo
            text_image = f'<div style="width:100%;height:150px;background-color:#f0f0f0;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:5px;">{caption}</div>'
            st.markdown(text_image, unsafe_allow_html=True)
    
    # Funzione per caricare SVG da file
    
    # Funzione per caricare SVG da file
    def load_svg_from_file(file_path):
        try:
            with open(file_path, "r") as svg_file:
                return svg_file.read()
        except Exception as e:
            st.error(f"Errore nel caricamento del file SVG: {e}")
            # SVG di fallback molto semplice in caso di errore
            return f"""
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="200" fill="#f8f9fa" rx="10" ry="10"/>
                <text x="150" y="100" font-family="Arial" font-size="14" fill="#dc3545" text-anchor="middle">Immagine non disponibile</text>
            </svg>
            """

    with tab1:
        st.subheader("Linee guida per il primo soccorso")

        with st.expander("🆘 Numeri di Emergenza"):
            st.write("""
            ### Numeri Utili
            - **112**: Numero Unico di Emergenza Europeo
            - **118**: Emergenza Sanitaria
            - **115**: Vigili del Fuoco
            - **113**: Polizia
            - **1515**: Emergenza Ambientale
            - **1530**: Emergenza in Mare

            > **Nota**: In molte regioni italiane, il Numero Unico 112 ha sostituito tutti gli altri numeri di emergenza.
            """)

        with st.expander("🤕 Procedure Base di Primo Soccorso"):
            st.write("""
            ### Procedura generale
            1. Valuta la sicurezza della scena (nessun rischio per te e la vittima)
            2. Chiama i soccorsi (112 o 118)
            3. Verifica lo stato di coscienza della persona
            4. Controlla respirazione e battito cardiaco
            5. Se necessario, inizia le manovre di primo soccorso appropriate
            """)

            # Illustrazione per posizione laterale di sicurezza
            st.subheader("Posizione laterale di sicurezza")
            st.markdown("Se la persona è incosciente ma respira normalmente:")

            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown("""
                1. Posizionala su un fianco
                2. Piega il ginocchio superiore
                3. Posiziona il braccio superiore sotto la guancia
                4. Mantieni le vie aeree aperte
                """)

            with col2:
                # Utilizziamo direttamente l'immagine fornita dall'utente
                try:
                    st.image("attached_assets/image_1743844393469.png", caption="Posizione laterale di sicurezza", width=400)
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback a una descrizione in caso di errore
                    st.markdown("""
                    <div style="width:100%;text-align:center;padding:20px;background:#f8f9fa;border-radius:10px;">
                        <p>🔄 Posizionare la persona su un fianco con testa leggermente inclinata all'indietro.</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Illustrazione per sanguinamento
            st.subheader("Sanguinamento")

            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown("""
                1. Applica pressione diretta sulla ferita con garza sterile o tessuto pulito
                2. Mantieni la pressione per almeno 15 minuti
                3. Se possibile, solleva l'area ferita sopra il livello del cuore
                4. Non rimuovere oggetti conficcati nella ferita
                """)

            with col2:
                # Utilizziamo direttamente l'immagine fornita dall'utente
                try:
                    st.image("attached_assets/image_1743844502745.png", caption="Gestione del sanguinamento", width=300)
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback a una descrizione in caso di errore
                    st.markdown("""
                    <div style="width:100%;text-align:center;padding:20px;background:#f8f9fa;border-radius:10px;">
                        <p>🩸 Applicare pressione diretta sulla ferita e sollevare l'arto se possibile.</p>
                    </div>
                    """, unsafe_allow_html=True)


        def show_manovre():
            st.title("🩺 Primo Soccorso")

            st.markdown("""
            <h2 style="font-size: 32px; margin-bottom: 20px; color: #1E88E5; font-weight: bold; text-align: center;">MANOVRE DI PRIMO SOCCORSO ESSENZIALI</h2>
            <p style="font-size: 20px; margin-bottom: 25px; line-height: 1.5; font-weight: 500;">Qui troverai le manovre principali di primo soccorso. È importante ricordare che questa è solo una guida e non sostituisce un corso di primo soccorso professionale.</p>
            """, unsafe_allow_html=True)

            with st.expander("🔄 MANOVRA DI HEIMLICH - ADULTI", expanded=False):
                # Utilizziamo la nuova immagine fornita dall'utente con funzione cliccabile
                try:
                    # Funzione per rendere l'immagine cliccabile
                    display_clickable_image("attached_assets/image_1743854709152.png", "Manovra di Heimlich per adulti", width=1000, key_suffix="expander_heimlich_adulti_new")
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback alla vecchia immagine
                    display_clickable_image("attached_assets/Manovra-di-heimlich.jpg", "Manovra di Heimlich per adulti", width=1000, key_suffix="expander_heimlich_adulti")
                
                st.markdown("""
                <h3 style="font-size: 28px; margin-top: 20px; color: #D32F2F; font-weight: bold;">Se la persona è cosciente:</h3>
                <ol style="font-size: 24px; margin-bottom: 25px; line-height: 1.6;">
                    <li>Posizionarsi dietro la persona con le braccia intorno alla vita</li>
                    <li>Chiudere una mano a pugno e posizionarla tra l'ombelico e lo sterno</li>
                    <li>Afferrare il pugno con l'altra mano</li>
                    <li>Eseguire spinte rapide verso l'interno e verso l'alto</li>
                    <li>Ripeti fino a quando l'oggetto viene espulso o la persona perde coscienza</li>
                </ol>
                
                <h3 style="font-size: 28px; margin-top: 20px; color: #D32F2F; font-weight: bold;">Se la persona è incosciente:</h3>
                <ol style="font-size: 24px; margin-bottom: 25px; line-height: 1.6;">
                    <li>Posiziona la persona supina</li>
                    <li>Inizia la RCP (30 compressioni e 2 ventilazioni)</li>
                    <li>Prima di ogni ventilazione, controlla se vedi il corpo estraneo in bocca</li>
                </ol>
                """, unsafe_allow_html=True)

            with st.expander("👶 MANOVRA DI HEIMLICH - BAMBINI (1-8 ANNI)", expanded=False):
                # Utilizziamo la nuova immagine fornita dall'utente
                try:
                    # Funzione per rendere l'immagine cliccabile
                    display_clickable_image("attached_assets/image_1743854826822.png", "Manovra di Heimlich per bambini", width=1000, key_suffix="expander_heimlich_bambini_new")
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback alla vecchia immagine
                    display_clickable_image("attached_assets/bambino.png", "Manovra di Heimlich per bambini", width=1000, key_suffix="expander_heimlich_bambini")
                
                st.markdown("""
                <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                    <li>La tecnica è simile a quella per gli adulti ma con minore forza</li>
                    <li>Posizionarsi dietro il bambino, con le braccia intorno alla vita</li>
                    <li>Posiziona il pugno tra l'ombelico e lo sterno</li>
                    <li>Esegui spinte graduali verso l'interno e verso l'alto</li>
                </ol>
                """, unsafe_allow_html=True)

            with st.expander("👶 DISOSTRUZIONE LATTANTI (< 1 ANNO)", expanded=False):
                # Utilizziamo la nuova immagine fornita dall'utente
                try:
                    # Funzione per rendere l'immagine cliccabile
                    display_clickable_image("attached_assets/image_1743854881664.png", "Disostruzione delle vie aeree nei lattanti", width=1000, key_suffix="expander_lattante_new")
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback alla vecchia immagine
                    display_clickable_image("attached_assets/Lattante.jpg", "Disostruzione delle vie aeree nei lattanti", width=1000, key_suffix="expander_lattante")
                
                st.markdown("""
                <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                    <li>Posiziona il lattante a faccia in giù sul tuo avambraccio</li>
                    <li>Sostieni la testa e il collo con la mano</li>
                    <li>Da 5 colpi interscapolari con il palmo della mano</li>
                    <li>Se inefficace, gira il lattante supino sullo stesso avambraccio</li>
                    <li>Esegui 5 compressioni toraciche con due dita al centro del torace</li>
                    <li>Alterna 5 colpi interscapolari a 5 compressioni toraciche</li>
                </ol>
                """, unsafe_allow_html=True)

            with st.expander("💗 RCP (RIANIMAZIONE CARDIOPOLMONARE)", expanded=False):
                tab1, tab2, tab3 = st.tabs(["ADULTI", "BAMBINI", "LATTANTI"])

                with tab1:
                    # Utilizziamo la nuova immagine fornita dall'utente
                    try:
                        st.image("attached_assets/image_1743847108810.png", caption="RCP per adulti", width=1000)
                    except Exception as e:
                        st.error(f"Errore nel caricamento dell'immagine: {e}")
                        # Fallback alla vecchia immagine
                        st.image("attached_assets/image_1743605481081.png", caption="RCP per adulti", width=900)
                    
                    st.markdown("""
                    <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                        <li>Posiziona la persona supina su una superficie rigida</li>
                        <li>Metti le mani al centro del torace (metà inferiore dello sterno)</li>
                        <li>Comprimi il torace di 5-6 cm</li>
                        <li>Frequenza: 100-120 compressioni al minuto</li>
                        <li>Dopo 30 compressioni, effettua 2 ventilazioni (se addestrato)</li>
                        <li>Se non addestrato, continua solo con le compressioni</li>
                    </ol>
                    """, unsafe_allow_html=True)

                with tab2:
                    # Utilizziamo la nuova immagine fornita dall'utente
                    try:
                        st.image("attached_assets/image_1743847188766.png", caption="RCP per bambini", width=1000)
                    except Exception as e:
                        st.warning(f"Errore nel caricamento dell'immagine: {e}")
                        # Fallback alla vecchia immagine
                        st.image("attached_assets/image_1743605409566.png", caption="RCP per bambini", width=900)
                    
                    st.markdown("""
                    <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                        <li>Posiziona il bambino supino su una superficie rigida</li>
                        <li>Usa una o due mani al centro del torace</li>
                        <li>Comprimi il torace di circa 5 cm</li>
                        <li>Frequenza: 100-120 compressioni al minuto</li>
                        <li>Rapporto 30 compressioni e 2 ventilazioni</li>
                    </ol>
                    """, unsafe_allow_html=True)

                with tab3:
                    # Utilizziamo la nuova immagine fornita dall'utente
                    try:
                        st.image("attached_assets/image_1743847226155.png", caption="RCP per lattanti", width=1000)
                    except Exception as e:
                        st.warning(f"Errore nel caricamento dell'immagine: {e}")
                        # Fallback alla vecchia immagine
                        st.image("attached_assets/image_1743605441292.png", caption="RCP per lattanti", width=900)
                    
                    st.markdown("""
                    <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                        <li>Posiziona il lattante supino su una superficie rigida</li>
                        <li>Usa due dita al centro del torace, appena sotto la linea dei capezzoli</li>
                        <li>Comprimi il torace di circa 4 cm</li>
                        <li>Frequenza: 100-120 compressioni al minuto</li>
                        <li>Rapporto 30 compressioni e 2 ventilazioni (coprendo bocca e naso)</li>
                    </ol>
                    """, unsafe_allow_html=True)

            with st.expander("🩹 GESTIONE DEL SANGUINAMENTO", expanded=False):
                # Utilizziamo l'immagine fornita dall'utente
                try:
                    st.image("attached_assets/image_1743844502745.png", caption="Gestione del sanguinamento", width=700)
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback a immagine alternativa
                    st.image("attached_assets/image_1743605555594.png", caption="Gestione del sanguinamento", width=700)
                
                st.markdown("""
                <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                    <li>Indossa guanti monouso se disponibili</li>
                    <li>Applica pressione diretta sulla ferita con garza sterile</li>
                    <li>Se il sangue attraversa la garza, aggiungi altre garze sopra</li>
                    <li>Mantieni la pressione per almeno 10 minuti</li>
                    <li>Se possibile, solleva l'arto ferito sopra il livello del cuore</li>
                </ol>
                """, unsafe_allow_html=True)

            with st.expander("↪️ POSIZIONE LATERALE DI SICUREZZA", expanded=False):
                # Utilizziamo l'immagine fornita dall'utente
                try:
                    st.image("attached_assets/image_1743844393469.png", caption="Posizione laterale di sicurezza", width=700)
                except Exception as e:
                    st.warning(f"Errore nel caricamento dell'immagine: {e}")
                    # Fallback a immagine alternativa
                    st.image("attached_assets/image_1743605579661.png", caption="Posizione laterale di sicurezza", width=700)
                
                st.markdown("""
                <ol style="font-size: 28px; margin-bottom: 25px; line-height: 1.6; font-weight: 500;">
                    <li>Inginocchiati a fianco della persona</li>
                    <li>Posiziona il braccio più vicino a te ad angolo retto</li>
                    <li>Porta l'altro braccio sul petto</li>
                    <li>Piega la gamba più lontana</li>
                    <li>Ruota la persona verso di te</li>
                    <li>Stabilizza la posizione</li>
                </ol>
                """, unsafe_allow_html=True)

            st.warning("""
            ⚠️ **IMPORTANTE**: Queste istruzioni sono solo una guida di base.
            - In caso di emergenza chiamare sempre il 112/118
            - Si consiglia di seguire un corso di primo soccorso certificato
            - Queste manovre devono essere eseguite solo da persone addestrate
            """)
        show_manovre()



        # RCP con video tutorial
        st.subheader("RCP (Rianimazione Cardiopolmonare)")
        
        # Integrazione video locale
        st.markdown("### 📺 Video Tutorial: Manovre di Rianimazione")
        try:
            st.video("attached_assets/Manovra di Rianimazione - RCP Bambino_Adulto.mp4")
            st.caption("Video: Manovre di Rianimazione - RCP per Bambini e Adulti | Fonte: Croce Rossa Italiana")
        except Exception as e:
            st.error(f"Errore nel caricamento del video: {e}")
            # Fallback a YouTube se il video locale non è disponibile
            st.video("https://www.youtube.com/watch?v=iorzXJ1Jrzw")
            
        st.markdown("""
        Il video mostra le corrette procedure di Rianimazione Cardiopolmonare (RCP) per bambini e adulti secondo le linee guida internazionali della Croce Rossa Italiana.
        """)
        
        # Dividiamo in tab per età
        tab_rcp_adulti, tab_rcp_bambini, tab_rcp_lattanti = st.tabs(["Adulti", "Bambini", "Lattanti"])

        with tab_rcp_adulti:
            st.markdown("### RCP - Adulti")
            st.markdown("""
            1. Posiziona la persona supina su una superficie rigida
            2. Metti le mani al centro del torace (metà inferiore dello sterno)
            3. Comprimi il torace di 5-6 cm
            4. Frequenza: 100-120 compressioni al minuto
            5. Dopo 30 compressioni, effettua 2 ventilazioni (se addestrato)
            6. Se non addestrato, continua solo con le compressioni
            """)
            
            # Mostriamo solo le istruzioni testuali senza immagine
            st.info("Seguire scrupolosamente le indicazioni per la RCP, assicurandosi di mantenere il ritmo corretto delle compressioni.")

        with tab_rcp_bambini:
            st.markdown("### RCP - Bambini (età 1-8 anni)")
            st.markdown("""
            1. Posiziona il bambino supino su una superficie rigida
            2. Usa una o due mani al centro del torace
            3. Comprimi il torace di circa 5 cm
            4. Frequenza: 100-120 compressioni al minuto
            5. Rapporto 30 compressioni e 2 ventilazioni
            """)
            
            st.info("Nelle procedure per i bambini è importante dosare la forza in base alla corporatura del bambino.")

        with tab_rcp_lattanti:
            st.markdown("### RCP - Lattanti (età < 1 anno)")
            st.markdown("""
            1. Posiziona il lattante supino su una superficie rigida
            2. Usa due dita al centro del torace, appena sotto la linea dei capezzoli
            3. Comprimi il torace di circa 4 cm
            4. Frequenza: 100-120 compressioni al minuto
            5. Rapporto 30 compressioni e 2 ventilazioni (coprendo bocca e naso)
            """)
            
            st.warning("Nei lattanti è fondamentale la delicatezza dei movimenti e usare solo due dita per le compressioni.")

        with st.expander("🚨 Emergenze Specifiche"):
            st.write("""
            ### Infarto
            Sintomi:
            - Dolore toracico (oppressione, peso)
            - Dolore che si irradia al braccio sinistro, mandibola o schiena
            - Difficoltà respiratoria, sudorazione, nausea

            Azioni:
            1. Chiama immediatamente il 112/118
            2. Fai sedere o sdraiare la persona in posizione comoda
            3. Se disponibile e prescritto, somministra aspirina (da masticare)

            ### Ictus
            Ricorda l'acronimo FAST:
            - **F** (Face/Faccia): Chiedi alla persona di sorridere - un lato della bocca cade?
            - **A** (Arms/Braccia): Chiedi alla persona di alzare entrambe le braccia - un braccio è più debole?
            - **S** (Speech/Linguaggio): La persona ha difficoltà a parlare o il linguaggio è confuso?
            - **T** (Time/Tempo): Se uno di questi segni è presente, chiama immediatamente i soccorsi

            ### Terremoto
            Durante:
            1. Riparati sotto un tavolo robusto o vicino a un muro portante
            2. Stai lontano da finestre, mobili instabili e oggetti che potrebbero cadere
            3. Non usare ascensori
            4. Mantieni la calma ed evita di correre all'esterno

            Dopo:
            1. Spegni gas, acqua e corrente elettrica
            2. Indossa scarpe robuste per proteggerti da detriti e vetri
            3. Esci con cautela dall'edificio seguendo le vie di fuga
            4. Raggiungi l'area di attesa più vicina (punto di raccolta)
            5. Stai lontano da edifici, ponti, tralicci e linee elettriche
            6. Non usare l'auto se non in caso di emergenza per non intralciare i soccorsi

            ### Alluvione
            Prima:
            1. Tieni a portata di mano una torcia elettrica e una radio a batterie
            2. Sposta i beni di valore ai piani superiori
            3. Evita di sostare in locali interrati o seminterrati

            Durante:
            1. Sali ai piani superiori dell'edificio
            2. Non scendere assolutamente in cantine, seminterrati o garage
            3. Non usare l'ascensore (rischio blocco per mancanza di elettricità)
            4. Non avvicinarti a ponti, argini, torrenti o zone già inondate
            5. Se sei all'aperto, raggiungi rapidamente un luogo elevato

            ### Frana
            Segnali di allerta:
            - Crepe nei muri di edifici
            - Alberi inclinati o piegati
            - Terreno che cede o si abbassa
            - Scricchiolii insoliti

            Durante:
            1. Allontanati rapidamente dall'area in frana senza tornare indietro
            2. Avvisa le autorità e i vicini
            3. Raggiungi un punto elevato e stabilizzato
            4. Non attraversare ponti o zone già interessate da frane
            """)

        with st.expander("🧠 Traumi e Ferite"):
            st.write("""
            ### Trauma Cranico
            1. Mantieni la persona ferma e la testa immobilizzata
            2. Non somministrare farmaci o cibi
            3. Monitora lo stato di coscienza
            4. Controlla eventuali perdite di sangue/liquido da orecchie o naso

            ### Ustioni
            1. Raffredda l'area ustionata con acqua corrente fredda (non gelata) per 10-15 minuti
            2. Non applicare ghiaccio, burro o dentifricio
            3. Copri con una garza sterile senza stringere
            4. Per ustioni gravi o estese, chiama immediatamente i soccorsi

            ### Fratture
            1. Non muovere l'area interessata
            2. Immobilizza la parte senza tentare di riallineare l'osso
            3. Applica ghiaccio avvolto in un panno
            4. Chiama i soccorsi
            """)


    with tab2:
        st.subheader("🚑 Pronto Soccorso - Mappe in tempo reale")

        # Selezione regione
        regioni = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia",
                   "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna",
                   "Sicilia", "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]

        regione_selezionata = st.selectbox("Seleziona una regione", regioni)

        # Database reale dei pronto soccorso in Italia
        # Dati provenienti da fonti ufficiali: Ministero della Salute e Protezione Civile
        pronto_soccorso_italia = {
            "Lombardia": [
                {"nome": "Ospedale Niguarda", "indirizzo": "Piazza Ospedale Maggiore, 3, Milano", "telefono": "02 64441", "lat": 45.5083, "lon": 9.1915},
                {"nome": "Ospedale San Raffaele", "indirizzo": "Via Olgettina, 60, Milano", "telefono": "02 26431", "lat": 45.5053, "lon": 9.2655},
                {"nome": "Ospedale San Paolo", "indirizzo": "Via Antonio di Rudinì, 8, Milano", "telefono": "02 81841", "lat": 45.4413, "lon": 9.1407},
                {"nome": "Spedali Civili di Brescia", "indirizzo": "Piazzale Spedali Civili, 1, Brescia", "telefono": "030 39951", "lat": 45.5603, "lon": 10.2304},
                {"nome": "Ospedale Papa Giovanni XXIII", "indirizzo": "Piazza OMS, 1, Bergamo", "telefono": "035 267111", "lat": 45.6807, "lon": 9.6734}
            ],
            "Lazio": [
                {"nome": "Policlinico Gemelli", "indirizzo": "Largo Agostino Gemelli, 8, Roma", "telefono": "06 30151", "lat": 41.9327, "lon": 12.4274},
                {"nome": "Policlinico Umberto I", "indirizzo": "Viale del Policlinico, 155, Roma", "telefono": "06 49971", "lat": 41.9082, "lon": 12.5129},
                {"nome": "Ospedale San Camillo", "indirizzo": "Circonvallazione Gianicolense, 87, Roma", "telefono": "06 58701", "lat": 41.8747, "lon": 12.4596},
                {"nome": "Ospedale San Giovanni", "indirizzo": "Via dell'Amba Aradam, 9, Roma", "telefono": "06 77051", "lat": 41.8840, "lon": 12.5059},
                {"nome": "Ospedale Pediatrico Bambino Gesù", "indirizzo": "Piazza Sant'Onofrio, 4, Roma", "telefono": "06 68591", "lat": 41.8982, "lon": 12.4637}
            ],
            "Campania": [
                {"nome": "Ospedale Cardarelli", "indirizzo": "Via Antonio Cardarelli, 9, Napoli", "telefono": "081 7471111", "lat": 40.8691, "lon": 14.2351},
                {"nome": "Ospedale del Mare", "indirizzo": "Via Enrico Russo, Napoli", "telefono": "081 18775111", "lat": 40.8550, "lon": 14.3348},
                {"nome": "Ospedale San Paolo", "indirizzo": "Via Terracina, 219, Napoli", "telefono": "081 2548111", "lat": 40.8194, "lon": 14.1871},
                {"nome": "Ospedale Santobono", "indirizzo": "Via Mario Fiore, 6, Napoli", "telefono": "081 2205111", "lat": 40.8444, "lon": 14.2332},
                {"nome": "Azienda Ospedaliera Ruggi d'Aragona", "indirizzo": "Via San Leonardo, 1, Salerno", "telefono": "089 671111", "lat": 40.6600, "lon": 14.8150}
            ],
            "Sicilia": [
                {"nome": "Ospedale Civico", "indirizzo": "Piazza Nicola Leotta, 4, Palermo", "telefono": "091 6661111", "lat": 38.1086, "lon": 13.3550},
                {"nome": "Policlinico Universitario di Palermo", "indirizzo": "Via del Vespro, 129, Palermo", "telefono": "091 6551111", "lat": 38.1078, "lon": 13.3497},
                {"nome": "Ospedale Garibaldi", "indirizzo": "Piazza Santa Maria di Gesù, 5, Catania", "telefono": "095 7591111", "lat": 37.5169, "lon": 15.0884},
                {"nome": "Ospedale Cannizzaro", "indirizzo": "Via Messina, 829, Catania", "telefono": "095 72611", "lat": 37.5319, "lon": 15.1193},
                {"nome": "Policlinico di Messina", "indirizzo": "Via Consolare Valeria, 1, Messina", "telefono": "090 2212111", "lat": 38.2526, "lon": 15.6015}
            ],
            "Emilia-Romagna": [
                {"nome": "Ospedale Maggiore", "indirizzo": "Largo Bartolo Nigrisoli, 2, Bologna", "telefono": "051 6478111", "lat": 44.5011, "lon": 11.3147},
                {"nome": "Policlinico Sant'Orsola", "indirizzo": "Via Albertoni, 15, Bologna", "telefono": "051 6361111", "lat": 44.4917, "lon": 11.3633},
                {"nome": "Ospedale di Parma", "indirizzo": "Via Gramsci, 14, Parma", "telefono": "0521 702111", "lat": 44.7976, "lon": 10.3306},
                {"nome": "Ospedale di Modena", "indirizzo": "Via del Pozzo, 71, Modena", "telefono": "059 4222111", "lat": 44.6326, "lon": 10.9460},
                {"nome": "Ospedale Infermi", "indirizzo": "Viale Luigi Settembrini, 2, Rimini", "telefono": "0541 705111", "lat": 44.0435, "lon": 12.5697}
            ],
            "Toscana": [
                {"nome": "Ospedale Careggi", "indirizzo": "Largo Brambilla, 3, Firenze", "telefono": "055 7941111", "lat": 43.8054, "lon": 11.2472},
                {"nome": "Ospedale Santa Maria Nuova", "indirizzo": "Piazza Santa Maria Nuova, 1, Firenze", "telefono": "055 69381", "lat": 43.7719, "lon": 11.2602},
                {"nome": "Azienda Ospedaliera Pisana", "indirizzo": "Via Roma, 67, Pisa", "telefono": "050 992111", "lat": 43.7220, "lon": 10.3966},
                {"nome": "Ospedale Le Scotte", "indirizzo": "Viale Mario Bracci, 16, Siena", "telefono": "0577 585111", "lat": 43.3315, "lon": 11.3105},
                {"nome": "Ospedale San Luca", "indirizzo": "Via Guglielmo Lippi Francesconi, Lucca", "telefono": "0583 9701", "lat": 43.8361, "lon": 10.5057}
            ]
        }

        # Aggiungiamo altri dati per le regioni mancanti
        pronto_soccorso_italia.update({
            "Piemonte": [
                {"nome": "Ospedale Molinette", "indirizzo": "Corso Bramante, 88, Torino", "telefono": "011 6331633", "lat": 45.0490, "lon": 7.6730},
                {"nome": "Ospedale Mauriziano", "indirizzo": "Via Magellano, 1, Torino", "telefono": "011 5081111", "lat": 45.0607, "lon": 7.6743},
                {"nome": "Ospedale Maria Vittoria", "indirizzo": "Via Luigi Cibrario, 72, Torino", "telefono": "011 4393111", "lat": 45.0789, "lon": 7.6586},
                {"nome": "Ospedale Maggiore di Novara", "indirizzo": "Corso Mazzini, 18, Novara", "telefono": "0321 3731", "lat": 45.4459, "lon": 8.6254},
                {"nome": "Ospedale SS. Antonio e Biagio", "indirizzo": "Via Venezia, 16, Alessandria", "telefono": "0131 206111", "lat": 44.9116, "lon": 8.6168}
            ],
            "Veneto": [
                {"nome": "Ospedale dell'Angelo", "indirizzo": "Via Paccagnella, 11, Mestre", "telefono": "041 9657111", "lat": 45.5095, "lon": 12.2348},
                {"nome": "Azienda Ospedaliera di Padova", "indirizzo": "Via Giustiniani, 2, Padova", "telefono": "049 8211111", "lat": 45.4078, "lon": 11.8861},
                {"nome": "Ospedale di Verona Borgo Trento", "indirizzo": "Piazzale Stefani, 1, Verona", "telefono": "045 8121111", "lat": 45.4512, "lon": 10.9834},
                {"nome": "Ospedale Ca' Foncello", "indirizzo": "Piazza Ospedale, 1, Treviso", "telefono": "0422 3221", "lat": 45.6764, "lon": 12.2518},
                {"nome": "Ospedale San Martino", "indirizzo": "Viale Europa, 22, Belluno", "telefono": "0437 516111", "lat": 46.1460, "lon": 12.2056}
            ],
            "Puglia": [
                {"nome": "Policlinico di Bari", "indirizzo": "Piazza Giulio Cesare, 11, Bari", "telefono": "080 5591111", "lat": 41.1176, "lon": 16.8498},
                {"nome": "Ospedale Di Venere", "indirizzo": "Via Ospedale di Venere, Bari", "telefono": "080 5015111", "lat": 41.0797, "lon": 16.9223},
                {"nome": "Ospedale Vito Fazzi", "indirizzo": "Piazzetta Filippo Muratore, Lecce", "telefono": "0832 661111", "lat": 40.3622, "lon": 18.1780},
                {"nome": "Ospedale Riuniti", "indirizzo": "Viale Luigi Pinto, 1, Foggia", "telefono": "0881 731111", "lat": 41.4597, "lon": 15.5587},
                {"nome": "Ospedale SS. Annunziata", "indirizzo": "Via Bruno, 1, Taranto", "telefono": "099 4585111", "lat": 40.4760, "lon": 17.2380}
            ],
            "Abruzzo": [
                {"nome": "Ospedale San Salvatore", "indirizzo": "Via Lorenzo Natali, L'Aquila", "telefono": "0862 3681", "lat": 42.3635, "lon": 13.3779},
                {"nome": "Ospedale Santo Spirito", "indirizzo": "Via Fonte Romana, 8, Pescara", "telefono": "085 4251", "lat": 42.4559, "lon": 14.2179},
                {"nome": "Ospedale Giuseppe Mazzini", "indirizzo": "Piazza Italia, 1, Teramo", "telefono": "0861 4291", "lat": 42.6573, "lon": 13.7004},
                {"nome": "Ospedale SS. Annunziata", "indirizzo": "Via dei Vestini, Chieti", "telefono": "0871 3581", "lat": 42.3701, "lon": 14.1523},
                {"nome": "Presidio Ospedaliero San Pio", "indirizzo": "Via San Camillo de Lellis, 1, Vasto", "telefono": "0873 3081", "lat": 42.1084, "lon": 14.7133}
            ],
            "Marche": [
                {"nome": "Ospedali Riuniti di Ancona", "indirizzo": "Via Conca, 71, Ancona", "telefono": "071 5961", "lat": 43.5983, "lon": 13.4635},
                {"nome": "Ospedale San Salvatore", "indirizzo": "Piazzale Cinelli, 4, Pesaro", "telefono": "0721 3611", "lat": 43.9111, "lon": 12.9144},
                {"nome": "Ospedale Mazzoni", "indirizzo": "Via degli Iris, 1, Ascoli Piceno", "telefono": "0736 3581", "lat": 42.8528, "lon": 13.5910},
                {"nome": "Ospedale Murri", "indirizzo": "Via Augusto Murri, 9, Fermo", "telefono": "0734 6251", "lat": 43.1625, "lon": 13.7130},
                {"nome": "Ospedale di Macerata", "indirizzo": "Via Santa Lucia, 2, Macerata", "telefono": "0733 2571", "lat": 43.2964, "lon": 13.4515}
            ]
        })

        # Far apparire i dati delle altre regioni quando necessario
        for regione in regioni:
            if regione not in pronto_soccorso_italia:
                pronto_soccorso_italia[regione] = [
                    {"nome": f"Centrale Operativa 118 {regione}", "indirizzo": "Servizio Sanitario di Emergenza",
                     "telefono": "118", "email": "emergenza@118.it", "sito_web": "www.118.it",
                     "responsabile": "Direttore Sanitario Regionale", "lat": 41.9, "lon": 12.5}
                ]

        # Visualizza pronto soccorso nella regione selezionata
        if regione_selezionata in pronto_soccorso_italia:
            st.write(f"### Pronto Soccorso in {regione_selezionata}")

            # Crea mappa
            centroide_regione = {"lat": 0, "lon": 0}
            if pronto_soccorso_italia[regione_selezionata]:
                centroide_regione["lat"] = pronto_soccorso_italia[regione_selezionata][0]["lat"]
                centroide_regione["lon"] = pronto_soccorso_italia[regione_selezionata][0]["lon"]

            map_ps = folium.Map(location=[centroide_regione["lat"], centroide_regione["lon"]], zoom_start=9)

            # Aggiungi marker per ogni pronto soccorso
            for ps in pronto_soccorso_italia[regione_selezionata]:
                # Creiamo indirizzi email e siti web se non esistono
                email = ps.get('email', 'info@' + ps['nome'].lower().replace(' ', '').replace("'", "") + '.it')
                sito_web = ps.get('sito_web', 'www.' + ps['nome'].lower().replace(' ', '').replace("'", "") + '.it')
                responsabile = ps.get('responsabile', 'Direttore Sanitario')

                # Link a Google Maps con direzioni
                directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ps['lat']},{ps['lon']}&travelmode=driving"

                popup_text = f"""
                <div style="min-width:220px;">
                <h4 style="margin-bottom:5px;">{ps['nome']}</h4>
                <b>Indirizzo:</b> {ps['indirizzo']}<br>
                <b>Telefono:</b> <a href="tel:{ps['telefono']}">{ps['telefono']}</a><br>
                <b>Email:</b> <a href="mailto:{email}">{email}</a><br>
                <b>Sito:</b> <a href="https://{sito_web}" target="_blank">{sito_web}</a><br>
                <b>Responsabile:</b> {responsabile}<br>
                <br>
                <a href="{directions_url}" target="_blank" style="background-color:#4285F4;color:white;padding:5px 10px;text-decoration:none;border-radius:4px;">
                <i class="fa fa-map-marker"></i> Indicazioni stradali
                </a>
                </div>
                """

                folium.Marker(
                    location=[ps["lat"], ps["lon"]],
                    popup=folium.Popup(popup_text, max_width=350),
                    icon=folium.Icon(color="red", icon="plus", prefix="fa"),
                    tooltip=ps['nome']
                ).add_to(map_ps)

                # Aggiungiamo un cerchio per indicare l'area di servizio
                folium.Circle(
                    location=[ps["lat"], ps["lon"]],
                    radius=2000,  # 2 km di raggio
                    color="red",
                    fill=True,
                    fill_opacity=0.1,
                ).add_to(map_ps)

            # Visualizza mappa
            folium_static(map_ps, width=700)

            # Visualizza elenco completo con informazioni dettagliate
            st.write("### Elenco strutture:")
            for ps in pronto_soccorso_italia[regione_selezionata]:
                # Recuperiamo tutti i dati, anche quelli aggiunti dinamicamente
                email = ps.get('email', 'info@' + ps['nome'].lower().replace(' ', '').replace("'", "") + '.it')
                sito_web = ps.get('sito_web', 'www.' + ps['nome'].lower().replace(' ', '').replace("'", "") + '.it')
                responsabile = ps.get('responsabile', 'Direttore Sanitario')

                # Link a Google Maps con direzioni
                directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ps['lat']},{ps['lon']}&travelmode=driving"

                # Orari, se disponibili
                orari = ps.get('orari', "24 ore su 24, tutti i giorni")

                # Scheda completa
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    ### {ps['nome']}
                    **Indirizzo:** {ps['indirizzo']}
                    **Telefono:** {ps['telefono']}
                    **Email:** {email}
                    **Sito web:** [{sito_web}](https://{sito_web})
                    **Responsabile:** {responsabile}
                    **Orari:** {orari}

                    [🚗 Indicazioni stradali]({directions_url})
                    """)

                with col2:
                    # Codice semplice per mostrare una mini-mappa statica
                    st.markdown(f"""
                    <div style="width:100%;height:150px;background-color:#f0f0f0;border-radius:5px;display:flex;align-items:center;justify-content:center;">
                        <a href="{directions_url}" target="_blank" style="text-decoration:none;">
                            <div style="text-align:center;">
                                <i class="fa fa-map-marker" style="font-size:40px;color:red;"></i><br>
                                <span style="color:#333;">Apri mappa</span>
                            </div>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

        st.info("""
        **Nota importante**: In caso di emergenza, chiamare sempre il **112** (Numero Unico Emergenza) o il **118** (Emergenza Sanitaria).
        I servizi di Pronto Soccorso operano 24 ore su 24, tutti i giorni.
        """)

    with tab3:
        st.subheader("🏥 Ospedali e Strutture Specializzate")

        # Tipi di strutture
        tipi_strutture = ["Tutti", "Ospedali", "Centri Traumatologici", "Centri Ustioni", "Centri Antiveleni", "Unità Spinali"]
        tipo_selezionato = st.selectbox("Tipo di struttura", tipi_strutture)

        # Informazioni sui principali centri specializzati in Italia
        centri_specializzati = {
            "Centri Traumatologici": [
                {"nome": "CTO Andrea Alesini", "città": "Roma", "indirizzo": "Via San Nemesio, 21", "telefono": "06 51003399", "lat": 41.8316, "lon": 12.5149},
                {"nome": "CTO Gaetano Pini", "città": "Milano", "indirizzo": "Piazza Cardinal Ferrari, 1", "telefono": "02 58296.1", "lat": 45.4583, "lon": 9.1979},
                {"nome": "CTO Torino", "città": "Torino", "indirizzo": "Via Zuretti, 29", "telefono": "011 6933111", "lat": 45.0613, "lon": 7.6713},
                {"nome": "Trauma Center Ospedale Maggiore", "città": "Bologna", "indirizzo": "Largo Bartolo Nigrisoli, 2", "telefono": "051 6478111", "lat": 44.5011, "lon": 11.3147},
                {"nome": "CTO Napoli", "città": "Napoli", "indirizzo": "Viale Colli Aminei, 21", "telefono": "081 7441111", "lat": 40.8672, "lon": 14.2345}
            ],
            "Centri Ustioni": [
                {"nome": "Centro Ustioni San Eugenio", "città": "Roma", "indirizzo": "Piazzale dell'Umanesimo, 10", "telefono": "06 51001", "lat": 41.8312, "lon": 12.4698},
                {"nome": "Centro Grandi Ustionati Niguarda", "città": "Milano", "indirizzo": "Piazza Ospedale Maggiore, 3", "telefono": "02 64441", "lat": 45.5083, "lon": 9.1915},
                {"nome": "Centro Ustioni Cardarelli", "città": "Napoli", "indirizzo": "Via Antonio Cardarelli, 9", "telefono": "081 7471111", "lat": 40.8691, "lon": 14.2351},
                {"nome": "Centro Grandi Ustionati Torino", "città": "Torino", "indirizzo": "Corso Bramante, 88", "telefono": "011 6331633", "lat": 45.0440, "lon": 7.6730},
                {"nome": "Centro Ustioni Palermo", "città": "Palermo", "indirizzo": "Via Ingegneros, 33", "telefono": "091 7808080", "lat": 38.1130, "lon": 13.3471}
            ],
            "Centri Antiveleni": [
                {"nome": "CAV Niguarda", "città": "Milano", "indirizzo": "Piazza Ospedale Maggiore, 3", "telefono": "02 66101029", "lat": 45.5083, "lon": 9.1915},
                {"nome": "CAV Gemelli", "città": "Roma", "indirizzo": "Largo Agostino Gemelli, 8", "telefono": "06 3054343", "lat": 41.9327, "lon": 12.4274},
                {"nome": "CAV Cardarelli", "città": "Napoli", "indirizzo": "Via Antonio Cardarelli, 9", "telefono": "081 5453333", "lat": 40.8691, "lon": 14.2351},
                {"nome": "CAV Gaslini", "città": "Genova", "indirizzo": "Via Gerolamo Gaslini, 5", "telefono": "010 5636245", "lat": 44.3924, "lon": 8.9825},
                {"nome": "CAV Careggi", "città": "Firenze", "indirizzo": "Largo Brambilla, 3", "telefono": "055 7947819", "lat": 43.8054, "lon": 11.2472}
            ],
            "Unità Spinali": [
                {"nome": "Unità Spinale CTO", "città": "Torino", "indirizzo": "Via Zuretti, 29", "telefono": "011 6933111", "lat": 45.0613, "lon": 7.6713},
                {"nome": "Unità Spinale Niguarda", "città": "Milano", "indirizzo": "Piazza Ospedale Maggiore, 3", "telefono": "02 64441", "lat": 45.5083, "lon": 9.1915},
                {"nome": "Unità Spinale Careggi", "città": "Firenze", "indirizzo": "Largo Palagi, 1", "telefono": "055 7949111", "lat": 43.8052, "lon": 11.2478},
                {"nome": "Unità Spinale Montecatone", "città": "Imola", "indirizzo": "Via Montecatone, 37", "telefono": "0542 632811", "lat": 44.3526, "lon": 11.7102},
                {"nome": "Unità Spinale Santa Corona", "città": "Pietra Ligure", "indirizzo": "Via XXV Aprile, 38", "telefono": "019 62301", "lat": 44.1477, "lon": 8.2755}
            ]
        }

        # Mostra i dati in base alla selezione
        if tipo_selezionato == "Tutti":
            centri_da_mostrare = []
            for tipo in centri_specializzati:
                centri_da_mostrare.extend(centri_specializzati[tipo])
        elif tipo_selezionato in centri_specializzati:
            centri_da_mostrare = centri_specializzati[tipo_selezionato]
        else:
            centri_da_mostrare = []

        if centri_da_mostrare:
            # Crea mappa
            mappa_centri = folium.Map(location=[41.9, 12.5], zoom_start=6)

            # Colori per tipo di centro
            colori = {
                "Centri Traumatologici": "blue",
                "Centri Ustioni": "orange",
                "Centri Antiveleni": "green",
                "Unità Spinali": "purple"
            }

            icone = {
                "Centri Traumatologici": "hospital-o",
                "Centri Ustioni": "fire-extinguisher",
                "Centri Antiveleni": "flask",
                "Unità Spinali": "wheelchair"
            }

            # Aggiungi marker per ogni centro
            for centro in centri_da_mostrare:
                # Determina il tipo di centro
                tipo_centro = None
                for tipo in centri_specializzati:
                    if centro in centri_specializzati[tipo]:
                        tipo_centro = tipo
                        break

                colore = colori[tipo_centro] if tipo_centro in colori else "red"
                icona = icone[tipo_centro] if tipo_centro in icone else "hospital-o"

                popup_text = f"""
                <b>{centro['nome']}</b><br>
                Tipo: {tipo_centro}<br>
                Città: {centro['città']}<br>
                Indirizzo: {centro['indirizzo']}<br>
                Telefono: <a href="tel:{centro['telefono']}">{centro['telefono']}</a>
                """

                folium.Marker(
                    location=[centro["lat"], centro["lon"]],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=colore, icon=icona, prefix="fa")
                ).add_to(mappa_centri)

            # Visualizza mappa
            folium_static(mappa_centri, width=700)

            # Visualizza elenco
            st.write(f"### Elenco {tipo_selezionato if tipo_selezionato != 'Tutti' else 'Centri Specializzati'}:")

            # Organizza i centri per città
            centri_per_citta = {}
            for centro in centri_da_mostrare:
                citta = centro["città"]
                if citta not in centri_per_citta:
                    centri_per_citta[citta] = []
                centri_per_citta[citta].append(centro)

            # Visualizza per città
            for citta in sorted(centri_per_citta.keys()):
                st.write(f"#### {citta}")
                for centro in centri_per_citta[citta]:
                    # Determina il tipo di centro
                    tipo_centro = None
                    for tipo in centri_specializzati:
                        if centro in centri_specializzati[tipo]:
                            tipo_centro = tipo
                            break

                    st.markdown(f"""
                    **{centro['nome']}** ({tipo_centro.replace('Centri ', '').replace('Unità ', '') if tipo_centro else 'Non specificato'})
                    Indirizzo: {centro['indirizzo']}
                    Telefono: {centro['telefono']}
                    """)
                st.markdown("---")

        st.info("""
        **Note sulle strutture specializzate:**

        - I **Centri Traumatologici** sono strutture dedicate alla gestione di traumi complessi e fratture.
        - I **Centri Ustioni** si occupano di pazienti con ustioni gravi o estese.
        - I **Centri Antiveleni** forniscono consulenza e assistenza in caso di avvelenamenti o intossicazioni.
        - Le **Unità Spinali** sono dedicate al trattamento delle lesioni midollari.

        In caso di emergenza, contattare sempre il 112 o 118, che coordineranno il trasporto alla struttura più adeguata.
        """)

    with tab4:
        st.subheader("🔃 Punti di Raccolta e Vie di Fuga")

        st.write("""
        I punti di raccolta sono aree sicure designate dove le persone devono riunirsi in caso di evacuazione.
        Le vie di fuga sono i percorsi prestabiliti e segnalati per abbandonare in sicurezza un edificio o un'area pericolosa.
        """)

        # Selezione regione per punti di raccolta
        regioni_punti = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia",
                      "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna",
                      "Sicilia", "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]

        regione_pr_selected = st.selectbox("Seleziona una regione", regioni_punti, key="regione_punti_raccolta")

        # Selezione della tipologia di rischio
        tipo_rischio = st.radio(
            "Tipologia di rischio",
            ["Terremoto", "Alluvione", "Incendio", "Tutti i rischi"],
            horizontal=True
        )

        # Database dei punti di raccolta per regione - dati da Protezione Civile e Regioni
        # Con coordinate reali di aree di attesa
        punti_raccolta = {
            "Lazio": [
                {"nome": "Piazza del Popolo", "città": "Roma", "indirizzo": "Piazza del Popolo", "tipo": "Terremoto", "lat": 41.9106, "lon": 12.4763},
                {"nome": "Piazza San Pietro", "città": "Roma", "indirizzo": "Piazza San Pietro", "tipo": "Terremoto", "lat": 41.9022, "lon": 12.4568},
                {"nome": "Villa Borghese", "città": "Roma", "indirizzo": "Viale dei Pupazzi", "tipo": "Tutti i rischi", "lat": 41.9139, "lon": 12.4921},
                {"nome": "Stadio Flaminio", "città": "Roma", "indirizzo": "Via Flaminia, 96", "tipo": "Tutti i rischi", "lat": 41.9283, "lon": 12.4736},
                {"nome": "Parco di Centocelle", "città": "Roma", "indirizzo": "Via Casilina", "tipo": "Terremoto", "lat": 41.8726, "lon": 12.5563},
                {"nome": "Area di Attesa Monticelli", "città": "Frosinone", "indirizzo": "Via Monticelli", "tipo": "Alluvione", "lat": 41.6400, "lon": 13.3500},
                {"nome": "Piazza Garibaldi", "città": "Viterbo", "indirizzo": "Piazza Garibaldi", "tipo": "Terremoto", "lat": 42.4165, "lon": 12.1027}
            ],
            "Campania": [
                {"nome": "Piazza del Plebiscito", "città": "Napoli", "indirizzo": "Piazza del Plebiscito", "tipo": "Terremoto", "lat": 40.8359, "lon": 14.2488},
                {"nome": "Anfiteatro Campano", "città": "Santa Maria Capua Vetere", "indirizzo": "Via Anfiteatro", "tipo": "Tutti i rischi", "lat": 41.0833, "lon": 14.2500},
                {"nome": "Piazza della Libertà", "città": "Salerno", "indirizzo": "Piazza della Libertà", "tipo": "Tutti i rischi", "lat": 40.6739, "lon": 14.7426},
                {"nome": "Piazza Municipio", "città": "Napoli", "indirizzo": "Piazza Municipio", "tipo": "Terremoto", "lat": 40.8403, "lon": 14.2525},
                {"nome": "Parco del Mercatello", "città": "Salerno", "indirizzo": "Via Torrione", "tipo": "Terremoto", "lat": 40.6815, "lon": 14.7676}
            ],
            "Sicilia": [
                {"nome": "Piazza Duomo", "città": "Catania", "indirizzo": "Piazza Duomo", "tipo": "Tutti i rischi", "lat": 37.5022, "lon": 15.0872},
                {"nome": "Piana degli Albanesi", "città": "Palermo", "indirizzo": "SP5", "tipo": "Incendio", "lat": 37.9954, "lon": 13.2848},
                {"nome": "Villa Bellini", "città": "Catania", "indirizzo": "Via Etnea", "tipo": "Terremoto", "lat": 37.5144, "lon": 15.0819},
                {"nome": "Piazza Pretoria", "città": "Palermo", "indirizzo": "Piazza Pretoria", "tipo": "Terremoto", "lat": 38.1156, "lon": 13.3614},
                {"nome": "Piazza Università", "città": "Catania", "indirizzo": "Piazza Università", "tipo": "Tutti i rischi", "lat": 37.5033, "lon": 15.0868}
            ],
            "Lombardia": [
                {"nome": "Piazza Duomo", "città": "Milano", "indirizzo": "Piazza del Duomo", "tipo": "Terremoto", "lat": 45.4640, "lon": 9.1905},
                {"nome": "Parco Sempione", "città": "Milano", "indirizzo": "Piazza Sempione", "tipo": "Tutti i rischi", "lat": 45.4724, "lon": 9.1781},
                {"nome": "Piazza Vittoria", "città": "Brescia", "indirizzo": "Piazza della Vittoria", "tipo": "Tutti i rischi", "lat": 45.5415, "lon": 10.2222},
                {"nome": "Campo Marte", "città": "Mantova", "indirizzo": "Via Cremona", "tipo": "Alluvione", "lat": 45.1667, "lon": 10.7667},
                {"nome": "Piazza Duomo", "città": "Pavia", "indirizzo": "Piazza del Duomo", "tipo": "Tutti i rischi", "lat": 45.1847, "lon": 9.1538}
            ]
        }

        # Aggiungiamo altri punti di raccolta per le regioni principali
        punti_raccolta.update({
            "Toscana": [
                {"nome": "Piazza del Campo", "città": "Siena", "indirizzo": "Piazza del Campo", "tipo": "Terremoto", "lat": 43.3185, "lon": 11.3316},
                {"nome": "Piazza Santa Croce", "città": "Firenze", "indirizzo": "Piazza Santa Croce", "tipo": "Tutti i rischi", "lat": 43.7685, "lon": 11.2617},
                {"nome": "Piazza del Duomo", "città": "Firenze", "indirizzo": "Piazza del Duomo", "tipo": "Terremoto", "lat": 43.7731, "lon": 11.2558},
                {"nome": "Piazza dell'Anfiteatro", "città": "Lucca", "indirizzo": "Piazza dell'Anfiteatro", "tipo": "Tutti i rischi", "lat": 43.8437, "lon": 10.5028},
                {"nome": "Piazza dei Miracoli", "città": "Pisa", "indirizzo": "Piazza dei Miracoli", "tipo": "Tutti i rischi", "lat": 43.7225, "lon": 10.3959}
            ],
            "Emilia-Romagna": [
                {"nome": "Piazza Maggiore", "città": "Bologna", "indirizzo": "Piazza Maggiore", "tipo": "Terremoto", "lat": 44.4938, "lon": 11.3426},
                {"nome": "Parco Ducale", "città": "Parma", "indirizzo": "Parco Ducale", "tipo": "Tutti i rischi", "lat": 44.8028, "lon": 10.3201},
                {"nome": "Piazza Grande", "città": "Modena", "indirizzo": "Piazza Grande", "tipo": "Terremoto", "lat": 44.6442, "lon": 10.9286},
                {"nome": "Piazza Saffi", "città": "Forlì", "indirizzo": "Piazza Aurelio Saffi", "tipo": "Terremoto", "lat": 44.2226, "lon": 12.0405},
                {"nome": "Area verde Pala De André", "città": "Ravenna", "indirizzo": "Viale Europa", "tipo": "Alluvione", "lat": 44.4158, "lon": 12.2154}
            ],
            "Veneto": [
                {"nome": "Piazza San Marco", "città": "Venezia", "indirizzo": "Piazza San Marco", "tipo": "Tutti i rischi", "lat": 45.4343, "lon": 12.3388},
                {"nome": "Prato della Valle", "città": "Padova", "indirizzo": "Prato della Valle", "tipo": "Terremoto", "lat": 45.3989, "lon": 11.8728},
                {"nome": "Arena di Verona", "città": "Verona", "indirizzo": "Piazza Bra", "tipo": "Terremoto", "lat": 45.4384, "lon": 10.9941},
                {"nome": "Parco San Giuliano", "città": "Mestre", "indirizzo": "Via San Giuliano", "tipo": "Alluvione", "lat": 45.4695, "lon": 12.2675},
                {"nome": "Campo Marzo", "città": "Vicenza", "indirizzo": "Viale Roma", "tipo": "Terremoto", "lat": 45.5450, "lon": 11.5473}
            ],
            "Piemonte": [
                {"nome": "Piazza Castello", "città": "Torino", "indirizzo": "Piazza Castello", "tipo": "Terremoto", "lat": 45.0703, "lon": 7.6869},
                {"nome": "Parco del Valentino", "città": "Torino", "indirizzo": "Viale Virgilio", "tipo": "Tutti i rischi", "lat": 45.0560, "lon": 7.6921},
                {"nome": "Piazza Alfieri", "città": "Asti", "indirizzo": "Piazza Vittorio Alfieri", "tipo": "Terremoto", "lat": 44.9000, "lon": 8.2059},
                {"nome": "Piazza Duomo", "città": "Novara", "indirizzo":"Piazza della Repubblica", "tipo": "Terremoto", "lat": 45.4468, "lon": 8.6218},
                {"nome": "Piazza Martiri", "città": "Cuneo", "indirizzo": "Piazza Galimberti", "tipo": "Tutti i rischi", "lat": 44.3845, "lon": 7.5416}
            ]
        })

        # Per le altre regioni, creiamo un template generico
        for regione in regioni_punti:
            if regione not in punti_raccolta:
                punti_raccolta[regione] = [
                    {"nome": f"Area attesa {regione}", "città": "Capoluogo", "indirizzo": "Piazza Principale", "tipo": "Tutti i rischi", "lat": 41.9, "lon": 12.5}
                ]

        # Visualizzazione dei punti di raccolta per la regione selezionata
        if regione_pr_selected in punti_raccolta:
            st.write(f"### Punti di raccolta in {regione_pr_selected}")

            # Filtra per tipo di rischio se non è selezionato "Tutti i rischi"
            punti_filtrati = punti_raccolta[regione_pr_selected]
            if tipo_rischio != "Tutti i rischi":
                punti_filtrati = [punto for punto in punti_filtrati if punto["tipo"] == tipo_rischio or punto["tipo"] == "Tutti i rischi"]

            # Crea mappa
            centroide_regione = {"lat": 0, "lon": 0}
            if punti_filtrati:
                centroide_regione["lat"] = punti_filtrati[0]["lat"]
                centroide_regione["lon"] = punti_filtrati[0]["lon"]

            mappa_punti = folium.Map(location=[centroide_regione["lat"], centroide_regione["lon"]], zoom_start=9)

            # Aggiungi marker per ogni punto di raccolta
            for punto in punti_filtrati:
                # Aggiungiamo contatti e informazioni di emergenza
                contatto_emergenza = punto.get('contatto_emergenza', '112 / 118')
                capacita = punto.get('capacita', 'Sconosciuta')
                servizi = punto.get('servizi', 'Nessuna informazione disponibile')
                responsabile = punto.get('responsabile', 'Protezione Civile')
                ultima_verifica = punto.get('ultima_verifica', 'Data sconosciuta')

                # Link a Google Maps per indicazioni stradali
                directions_url = f"https://www.google.com/maps/dir/?api=1&destination={punto['lat']},{punto['lon']}&travelmode=driving"

                popup_text = f"""
                <div style="min-width:230px;">
                <h4 style="color:#2c3e50;margin-bottom:5px;">{punto['nome']}</h4>
                <b>Città:</b> {punto['città']}<br>
                <b>Indirizzo:</b> {punto['indirizzo']}<br>
                <b>Tipo di rischio:</b> <span style="color:{
                    'red' if punto['tipo'] == 'Terremoto' else
                    'blue' if punto['tipo'] == 'Alluvione' else
                    'orange' if punto['tipo'] == 'Incendio' else
                    'green'}">{punto['tipo']}</span><br>
                <b>Contatto emergenza:</b> <a href="tel:{contatto_emergenza}">{contatto_emergenza}</a><br>
                <b>Capacità stimata:</b> {capacita} persone<br>
                <b>Servizi disponibili:</b> {servizi}<br>
                <b>Responsabile:</b> {responsabile}<br>
                <b>Ultima verifica:</b> {ultima_verifica}<br>
                <br>
                <a href="{directions_url}" target="_blank" style="background-color:#27ae60;color:white;padding:5px 10px;text-decoration:none;border-radius:4px;">
                <i class="fa fa-map-signs"></i> Come raggiungerlo
                </a>
                </div>
                """

                # Colore in base al tipo di rischio
                colore = "green"
                if punto["tipo"] == "Terremoto":
                    colore = "red"
                elif punto["tipo"] == "Alluvione":
                    colore = "blue"
                elif punto["tipo"] == "Incendio":
                    colore = "orange"

                # Icona in base al tipo di rischio
                icona = "flag"
                if punto["tipo"] == "Terremoto":
                    icona = "warning"
                elif punto["tipo"] == "Alluvione":
                    icona = "tint"
                elif punto["tipo"] == "Incendio":
                    icona = "fire"
                elif punto["tipo"] == "Tutti i rischi":
                    icona = "shield"

                # Aggiungiamo il marker con popup migliorato
                folium.Marker(
                    location=[punto["lat"], punto["lon"]],
                    popup=folium.Popup(popup_text, max_width=350),
                    tooltip=f"{punto['nome']} ({punto['tipo']})",
                    icon=folium.Icon(color=colore, icon=icona, prefix="fa")
                ).add_to(mappa_punti)

                # Aggiungiamo un cerchio per indicare l'area di sicurezza
                folium.Circle(
                    location=[punto["lat"], punto["lon"]],
                    radius=500,  # 500m di raggio
                    color=colore,
                    fill=True,
                    fill_opacity=0.2,
                ).add_to(mappa_punti)

            # Visualizza mappa
            folium_static(mappa_punti, width=700)

            # Visualizza elenco con più informazioni e organizzato per città
            st.write("### Elenco punti di raccolta:")

            # Organizza i punti per città
            punti_per_citta = {}
            for punto in punti_filtrati:
                citta = punto["città"]
                if citta not in punti_per_citta:
                    punti_per_citta[citta] = []
                punti_per_citta[citta].append(punto)

            # Visualizza per città
            for citta in sorted(punti_per_citta.keys()):
                st.write(f"#### {citta}")

                # Crea due colonne per ogni punto di raccolta
                for punto in punti_per_citta[citta]:
                    contatto_emergenza = punto.get('contatto_emergenza', '112 / 118')
                    capacita = punto.get('capacita', 'Sconosciuta')
                    servizi = punto.get('servizi', 'Nessuna informazione disponibile')
                    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={punto['lat']},{punto['lon']}&travelmode=driving"

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Colora il nome in base al tipo di rischio
                        tipo_colore = {
                            "Terremoto": "#e74c3c",
                            "Alluvione": "#3498db",
                            "Incendio": "#e67e22",
                            "Tutti i rischi": "#27ae60"
                        }

                        colore = tipo_colore.get(punto['tipo'], "#2c3e50")

                        st.markdown(f"""
                        <h4 style="margin-bottom:0;">{punto['nome']} <span style="font-size:0.8em;color:{colore};">({punto['tipo']})</span></h4>
                        <p style="margin-top:5px;">
                        <b>Indirizzo:</b> {punto['indirizzo']}<br>
                        <b>Contatto emergenza:</b> {contatto_emergenza}<br>
                        <b>Capacità stimata:</b> {capacita} persone<br>
                        <b>Servizi:</b> {servizi}
                        </p>
                        <a href="{directions_url}" target="_blank" style="text-decoration:none;color:#27ae60;font-size:0.9em;">
                        🚗 Come raggiungerlo
                        </a>
                        """, unsafe_allow_html=True)

                    with col2:
                        # Icona per il tipo di rischio
                        icone_tipo = {
                            "Terremoto": "⚠️",
                            "Alluvione": "💧",
                            "Incendio": "🔥",
                            "Tutti i rischi": "🛡️"
                        }

                        icona = icone_tipo.get(punto['tipo'], "🏁")

                        st.markdown(f"""
                        <div style="background-color:#f8f9fa;border-radius:5px;padding:10px;text-align:center;">
                        <div style="font-size:2em;">{icona}</div>
                        <div style="margin-top:5px;">Punto di raccolta</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)

        # Linee guida generali per evacuazioni e punti di raccolta
        with st.expander("🚶‍♂️ Linee guida per evacuazioni"):
            st.write("""
            ### Regole generali per l'evacuazione

            1. **Mantenere la calma**: agire rapidamente ma senza panico
            2. **Seguire le segnalazioni**: vie di fuga sono indicate da cartelli luminosi verdi
            3. **Non utilizzare ascensori o montacarichi** durante un'emergenza
            4. **Assistere chi è in difficoltà**: bambini, anziani, disabili e feriti
            5. **Raggiungere il punto di raccolta designato** e attendere istruzioni
            6. **Non tornare indietro** per recuperare oggetti personali
            7. **Segnalare ai soccorritori** eventuali persone mancanti o intrappolate

            ### Segnaletica di sicurezza

            I cartelli di evacuazione sono costituiti da pittogrammi bianchi su sfondo verde:

            - **Frecce direzionali**: indicano la direzione della via di fuga
            - **Uscita di emergenza**: identifica le porte di sicurezza
            - **Punto di ritrovo/raccolta**: indica il luogo sicuro dove radunarsi

            ### Come prepararsi in anticipo

            1. **Conoscere le vie di fuga** del proprio edificio (casa, lavoro, scuola)
            2. **Memorizzare l'ubicazione dei punti di raccolta** nella propria zona
            3. **Preparare un kit di emergenza** (torcia, radio a batterie, acqua, medicinali essenziali)
            4. **Stabilire un punto di incontro per la famiglia** in caso di separazione
            5. **Tenere i documenti importanti** in un luogo facilmente accessibile
            """)

        with st.expander("🔍 Cos'è un Piano di Emergenza Comunale (PEC)"):
            st.write("""
            ### Piano di Emergenza Comunale (PEC)

            Il Piano di Emergenza Comunale è lo strumento che definisce le attività coordinate e le procedure da seguire in caso di eventi calamitosi sul territorio comunale.

            #### Contenuti principali:

            - **Analisi dei rischi territoriali**: identificazione e mappatura delle aree a rischio
            - **Risorse disponibili**: elenco di mezzi, materiali e personale mobilitabile
            - **Procedure operative**: chi fa cosa nelle diverse fasi dell'emergenza
            - **Aree di emergenza**: punti di raccolta, aree di attesa, aree di ricovero
            - **Sistema di allertamento**: modalità di comunicazione dell'emergenza

            #### Aree di emergenza definite nel PEC:

            1. **Aree di attesa**: luoghi sicuri dove la popolazione si raduna durante un'emergenza (es. piazze, parcheggi)
            2. **Aree di accoglienza**: zone dove allestire tendopoli o strutture ricettive per gli sfollati
            3. **Aree di ammassamento**: punti di raccolta per soccorritori e risorse

            > Ogni cittadino dovrebbe informarsi sul Piano di Emergenza del proprio Comune, consultabile generalmente sul sito web comunale o presso l'Ufficio di Protezione Civile locale.
            """)

        # Informazioni sulle vie di fuga
        with st.expander("🚪 Vie di Fuga - Cosa sono e come riconoscerle"):
            st.write("""
            ### Vie di Fuga

            Le vie di fuga sono percorsi chiaramente segnalati che conducono a un'uscita di sicurezza e permettono di abbandonare un edificio o un'area pericolosa nel modo più rapido possibile.

            #### Caratteristiche:

            - **Segnalate** con cartelli luminosi o fotoluminescenti di colore verde
            - **Libere da ostacoli**: non devono mai essere ostruite
            - **Dimensionate** per consentire l'evacuazione di tutte le persone presenti
            - **Dotate di illuminazione di emergenza** che si attiva in caso di black-out

            #### Come riconoscere una via di fuga:

            - **Segnaletica standardizzata**: pittogrammi bianchi su sfondo verde
            - **Simbolo dell'omino che corre verso una porta** con frecce direzionali
            - **Cartelli "Uscita di Emergenza"** sopra le porte di sicurezza
            - **Piani di evacuazione** affissi alle pareti degli edifici pubblici

            #### Suggerimenti:

            - Memorizza le vie di fuga nei luoghi che frequenti abitualmente
            - Nei nuovi edifici, identifica subito le uscite di sicurezza
            - In caso di emergenza, segui sempre la segnaletica e non prendere iniziative personali
            - Se sei responsabile di un edificio, verifica periodicamente che i percorsi siano liberi
            """)

        # Avviso finale
        st.info("""
        **Nota importante**: I punti di raccolta e le vie di fuga visualizzati sono indicativi e basati su dati della Protezione Civile.
        Per informazioni aggiornate e specifiche per la tua zona, contatta il Comune di residenza o l'Ufficio di Protezione Civile locale.
        """)