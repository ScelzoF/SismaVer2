
import streamlit as st
import os

def show():
    # Gestione endpoint per SEO
    query_params = st.query_params
    
    # Endpoint per sitemap.xml
    if 'seo_endpoint' in query_params and query_params.get('seo_endpoint') == 'sitemap':
        try:
            from modules.seo_utils import serve_sitemap_xml
            sitemap_content = serve_sitemap_xml()
            st.download_button(
                label="Scarica Sitemap XML",
                data=sitemap_content,
                file_name="sitemap.xml",
                mime="application/xml",
                key="sitemap_download",
                help="Scarica il sitemap XML per l'indicizzazione nei motori di ricerca"
            )
            st.code(sitemap_content, language="xml")
            return
        except ImportError:
            pass
    
    # Endpoint per robots.txt
    if 'seo_endpoint' in query_params and query_params.get('seo_endpoint') == 'robots':
        try:
            from modules.seo_utils import serve_robots_txt
            robots_content = serve_robots_txt()
            st.download_button(
                label="Scarica Robots.txt",
                data=robots_content,
                file_name="robots.txt",
                mime="text/plain",
                key="robots_download",
                help="Scarica il file robots.txt per configurare i crawler"
            )
            st.code(robots_content, language="text")
            return
        except ImportError:
            pass
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
    
    st.info("""
    **ℹ️ Evoluzione dell'app originale**  
    SismaVer2 è l'evoluzione della prima versione disponibile su [sismocampania.streamlit.app](https://sismocampania.streamlit.app), 
    con estensione della copertura a tutto il territorio nazionale e numerose funzionalità avanzate.
    """)

    st.info("👨‍💻 Sviluppato da **Fabio SCELZO**")

    st.markdown("---")

    # Sezione contatti e supporto
    st.subheader("📞 Contatti e Supporto")
    st.markdown("📧 Email: meteotorre@gmail.com")
