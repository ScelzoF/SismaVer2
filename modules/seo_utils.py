"""
Utility per SEO e visibilità sui motori di ricerca.
Implementa generazione sitemap, metatag e strumenti di indicizzazione.
"""
import time
import streamlit as st
from datetime import datetime

def generate_sitemap_xml():
    """
    Genera un sitemap XML ottimizzato per l'indicizzazione nei motori di ricerca.
    Include tutte le pagine importanti con priorità e frequenza di aggiornamento.
    
    Returns:
        str: Contenuto XML del sitemap
    """
    # URL base dell'applicazione
    base_url = "https://sos-italia.streamlit.app"
    
    # Lista delle pagine
    pages = [
        {"url": f"{base_url}/", "priority": "1.0", "changefreq": "daily"},
        {"url": f"{base_url}/?show=monitoraggio", "priority": "0.9", "changefreq": "hourly"},
        {"url": f"{base_url}/?show=vulcani", "priority": "0.8", "changefreq": "daily"},
        {"url": f"{base_url}/?show=meteo", "priority": "0.8", "changefreq": "hourly"},
        {"url": f"{base_url}/?show=chat_enhanced", "priority": "0.7", "changefreq": "hourly"},
        {"url": f"{base_url}/?show=emergenza", "priority": "0.8", "changefreq": "weekly"},
        {"url": f"{base_url}/?show=primo_soccorso", "priority": "0.7", "changefreq": "monthly"},
        {"url": f"{base_url}/?show=segnala_evento_enhanced", "priority": "0.7", "changefreq": "daily"},
        {"url": f"{base_url}/?show=donazioni", "priority": "0.5", "changefreq": "monthly"},
        {"url": f"{base_url}/?show=note_rilascio", "priority": "0.5", "changefreq": "monthly"},
        {"url": f"{base_url}/?show=licenza", "priority": "0.4", "changefreq": "monthly"},
    ]
    
    # Data attuale
    now = datetime.now().strftime("%Y-%m-%d")
    
    # Creazione dell'XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Aggiungi ogni pagina
    for page in pages:
        xml += '  <url>\n'
        xml += f'    <loc>{page["url"]}</loc>\n'
        xml += f'    <lastmod>{now}</lastmod>\n'
        xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml += f'    <priority>{page["priority"]}</priority>\n'
        xml += '  </url>\n'
    
    xml += '</urlset>'
    
    return xml

def add_seo_metatags():
    """
    Aggiunge metatag per SEO nell'header HTML della pagina Streamlit.
    Utilizza st.markdown con unsafe_allow_html=True.
    """
    # Pagina corrente e titolo appropriato
    page = st.session_state.get("page", "home")
    titles = {
        "home": "SismaVer2 - Sistema di Monitoraggio Sismico per l'Italia",
        "monitoraggio": "Monitoraggio Sismico Nazionale in Tempo Reale | SismaVer2",
        "vulcani": "Monitoraggio Vulcani Italiani in Tempo Reale | SismaVer2",
        "meteo": "Previsioni Meteo e Allerta Italia | SismaVer2",
        "chat_enhanced": "Chat Pubblica per Emergenze | SismaVer2",
        "emergenza": "Punti di Raccolta e Vie di Fuga in Italia | SismaVer2",
        "primo_soccorso": "Guide di Primo Soccorso e Manovre Salvavita | SismaVer2",
        "segnala_evento_enhanced": "Segnalazione Eventi e Rischi | SismaVer2"
    }
    title = titles.get(page, "SismaVer2 - Sistema Nazionale di Monitoraggio e Prevenzione")
    
    # Descrizioni per le diverse pagine
    descriptions = {
        "home": "SismaVer2 è un sistema di monitoraggio sismico, vulcanico e meteorologico per l'Italia. Fornisce dati in tempo reale e strumenti per emergenze.",
        "monitoraggio": "Monitoraggio in tempo reale di tutti gli eventi sismici sul territorio italiano. Visualizza terremoti, magnitude e profondità con dati ufficiali.",
        "vulcani": "Monitoraggio dell'attività vulcanica in Italia con dati in tempo reale su Vesuvio, Campi Flegrei, Etna e Stromboli. Parametri di sismicità e deformazione.",
        "meteo": "Previsioni meteo in tempo reale per tutte le città italiane. Sistema di allerta per eventi meteorologici estremi e condizioni avverse.",
        "chat_enhanced": "Sistema di comunicazione pubblica per emergenze. Chat in tempo reale con filtri per regioni e tipologie di eventi.",
        "emergenza": "Mappa dei punti di raccolta, vie di fuga e strutture di emergenza in tutta Italia. Indicazioni sui comportamenti corretti in caso di calamità.",
        "primo_soccorso": "Guide dettagliate di primo soccorso con illustrazioni e istruzioni per manovre salvavita in caso di emergenza.",
        "segnala_evento_enhanced": "Sistema di segnalazione eventi e rischi sul territorio italiano. Contribuisci alla sicurezza della comunità."
    }
    description = descriptions.get(page, "Sistema nazionale per il monitoraggio sismico, vulcanico e meteorologico, con strumenti per la gestione delle emergenze e la sicurezza dei cittadini.")
    
    # Definisci i meta tags
    meta_tags = f"""
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="terremoti italia, monitoraggio sismico, protezione civile, allerta meteo, vulcani italia, campi flegrei, vesuvio, etna, primo soccorso, emergenze">
    <meta name="author" content="SismaVer2">
    <meta name="robots" content="index, follow">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="https://sos-italia.streamlit.app">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://sos-italia.streamlit.app/og-image.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="https://sos-italia.streamlit.app/og-image.jpg">
    <link rel="canonical" href="https://sos-italia.streamlit.app">
    """
    
    # Aggiungi i meta tags alla pagina
    st.markdown(meta_tags, unsafe_allow_html=True)

def add_search_verification():
    """
    Aggiunge i tag di verifica per i principali motori di ricerca.
    """
    verification_tags = """
    <meta name="google-site-verification" content="VerificationCodeHere" />
    <meta name="msvalidate.01" content="VerificationCodeHere" />
    <meta name="yandex-verification" content="VerificationCodeHere" />
    """
    
    st.markdown(verification_tags, unsafe_allow_html=True)

def serve_robots_txt():
    """
    Genera e restituisce il contenuto del file robots.txt.
    Da usare con st.download_button o simile.
    
    Returns:
        str: Contenuto del robots.txt
    """
    robots_content = """User-agent: *
Allow: /
Disallow: /admin/

# Sitemap location
Sitemap: https://sos-italia.streamlit.app/sitemap.xml
"""
    return robots_content

def serve_sitemap_xml():
    """
    Genera e restituisce il contenuto del sitemap.xml.
    Da usare con st.download_button o simile.
    
    Returns:
        str: Contenuto XML del sitemap
    """
    return generate_sitemap_xml()

def add_schema_markup():
    """
    Aggiunge markup strutturato JSON-LD per la comprensione semantica.
    """
    # Ottieni la pagina corrente
    page = st.session_state.get("page", "home")
    
    # Schema Organization
    organization_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "SismaVer2",
        "description": "Sistema Nazionale di Monitoraggio e Prevenzione",
        "url": "https://sos-italia.streamlit.app",
        "logo": "https://sos-italia.streamlit.app/logo.png",
        "contactPoint": {
            "@type": "ContactPoint",
            "email": "meteotorre@gmail.com",
            "contactType": "customer service"
        }
    }
    
    # Schema per pagine specifiche
    page_schemas = {
        "monitoraggio": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "Monitoraggio Sismico Nazionale",
            "description": "Monitoraggio in tempo reale di tutti gli eventi sismici sul territorio italiano.",
            "url": "https://sos-italia.streamlit.app/?show=monitoraggio"
        },
        "primo_soccorso": {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Guide di Primo Soccorso",
            "description": "Istruzioni dettagliate per manovre di primo soccorso e procedure salvavita.",
            "url": "https://sos-italia.streamlit.app/?show=primo_soccorso"
        }
    }
    
    # Ottieni lo schema appropriato
    schema = page_schemas.get(page, organization_schema)
    
    # Converti in JSON-LD
    schema_json = str(schema).replace("'", "\"")
    schema_markup = f"""
    <script type="application/ld+json">
    {schema_json}
    </script>
    """
    
    # Aggiungi alla pagina
    st.markdown(schema_markup, unsafe_allow_html=True)