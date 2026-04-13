"""
Modulo per l'esportazione dell'applicazione SismaVer2 in formato HTML statico.
Genera una versione del sito che può essere hostata su qualsiasi servizio web statico.
"""
import os
import re
import json
import shutil
import hashlib
import streamlit as st
from datetime import datetime

# Importa il modulo di sicurezza
from modules.security import sanitize_input, generate_csrf_token, secure_headers

# Directory di export
EXPORT_DIR = "export_html"

# Elenco delle pagine da esportare
PAGES = [
    {"name": "home", "title": "Home", "description": "Dashboard principale SismaVer2"},
    {"name": "monitoraggio", "title": "Monitoraggio Sismico", "description": "Monitoraggio attività sismica in Italia"},
    {"name": "vulcani", "title": "Vulcani", "description": "Monitoraggio attività vulcanica in Italia"},
    {"name": "meteo", "title": "Meteo", "description": "Previsioni meteo e allerte"},
    {"name": "emergenza", "title": "Emergenza", "description": "Protocolli e informazioni per emergenze"},
    {"name": "primo_soccorso", "title": "Primo Soccorso", "description": "Guide al primo soccorso"},
    {"name": "licenza", "title": "Licenza", "description": "Informazioni sulla licenza"}
]


def generate_html_template(title, description, content, page_name):
    """
    Genera il template HTML base per una pagina.
    
    Args:
        title (str): Titolo della pagina
        description (str): Descrizione per i meta tag
        content (str): Contenuto HTML della pagina
        page_name (str): Nome della pagina per link attivi
    
    Returns:
        str: Template HTML completo
    """
    # Calcola la data attuale per il footer
    current_year = datetime.now().year
    
    # Costruisci il menu di navigazione
    nav_items = ""
    for page in PAGES:
        active_class = "active" if page["name"] == page_name else ""
        nav_items += f'<li class="{active_class}"><a href="{page["name"]}.html">{page["title"]}</a></li>\n'
    
    # Genera il template HTML
    template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - SismaVer2</title>
    <meta name="description" content="{description}">
    {secure_headers()}
    
    <!-- Metatag SEO -->
    <meta property="og:title" content="{title} - SismaVer2">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://sisma-ver2.it/{page_name}.html">
    <meta property="og:image" content="assets/images/logo.png">
    <meta name="twitter:card" content="summary_large_image">
    
    <!-- Preload risorse critiche -->
    <link rel="preload" href="assets/styles/main.css" as="style">
    <link rel="preload" href="assets/scripts/main.js" as="script">
    
    <!-- Favicon -->
    <link rel="icon" href="assets/images/favicon.ico">
    <link rel="apple-touch-icon" href="assets/images/apple-touch-icon.png">
    
    <!-- Fogli di stile -->
    <link rel="stylesheet" href="assets/styles/main.css">
    <link rel="stylesheet" href="assets/styles/responsive.css">
    
    <!-- Integrazione PWA (Progressive Web App) -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#0066cc">
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">
                <a href="index.html">
                    <img src="assets/images/logo.png" alt="SismaVer2 Logo">
                </a>
            </div>
            <nav class="main-nav">
                <ul>
                    {nav_items}
                </ul>
            </nav>
            <div class="mobile-menu-toggle">
                <span></span><span></span><span></span>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <h1 class="page-title">{title}</h1>
            <div class="content">
                {content}
            </div>
        </div>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-logo">
                    <img src="assets/images/logo-footer.png" alt="SismaVer2 Logo">
                </div>
                <div class="footer-links">
                    <h3>Naviga</h3>
                    <ul>
                        {nav_items}
                    </ul>
                </div>
                <div class="footer-contact">
                    <h3>Contatti</h3>
                    <p>Email: <a href="mailto:meteotorre@gmail.com">meteotorre@gmail.com</a></p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {current_year} SismaVer2. Tutti i diritti riservati.</p>
                <p>SismaVer2 è un'evoluzione dell'app originale <a href="https://sismocampania.streamlit.app" target="_blank">SismoCampania</a>.</p>
            </div>
        </div>
    </footer>

    <!-- Script -->
    <script src="assets/scripts/main.js"></script>
    <script src="assets/scripts/{page_name}.js"></script>
    
    <!-- Protezione contro XSS -->
    <script>
        // Genera CSRF token per le form
        const csrfToken = '{generate_csrf_token()}';
        
        // Sanitizza input utente
        function sanitizeInput(text) {{
            return text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }}
        
        // Aggiungi token CSRF a tutte le form
        document.addEventListener('DOMContentLoaded', () => {{
            document.querySelectorAll('form').forEach(form => {{
                const tokenInput = document.createElement('input');
                tokenInput.type = 'hidden';
                tokenInput.name = 'csrf_token';
                tokenInput.value = csrfToken;
                form.appendChild(tokenInput);
            }});
        }});
    </script>

    <!-- Analytics (opzionale) -->
    <!-- <script async src="https://www.googletagmanager.com/gtag/js?id=UA-XXXXXXXX-X"></script> -->
</body>
</html>"""
    
    return template


def create_css_files():
    """
    Crea i file CSS necessari per il sito statico.
    
    Returns:
        bool: True se creati con successo
    """
    css_dir = os.path.join(EXPORT_DIR, "assets", "styles")
    os.makedirs(css_dir, exist_ok=True)
    
    # File CSS principale
    main_css = """
/* Reset CSS */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
}

/* Header */
header {
    background-color: #0066cc;
    color: white;
    padding: 1rem 0;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.logo img {
    height: 50px;
}

.main-nav ul {
    display: flex;
    list-style: none;
}

.main-nav li {
    margin-left: 1.5rem;
}

.main-nav a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.main-nav a:hover {
    color: #cce5ff;
}

.main-nav li.active a {
    color: #ffcc00;
    font-weight: 700;
}

.mobile-menu-toggle {
    display: none;
}

/* Main content */
main {
    padding: 2rem 0;
    min-height: 70vh;
}

.page-title {
    margin-bottom: 1.5rem;
    color: #0066cc;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0.5rem;
}

.content {
    background: white;
    border-radius: 5px;
    padding: 2rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* Cards per informazioni */
.card {
    background: white;
    border-radius: 5px;
    padding: 1rem;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}

.card-title {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
    color: #0066cc;
}

.card-emergency {
    border-left: 4px solid #ff3333;
}

/* Buttons */
.btn {
    display: inline-block;
    background: #0066cc;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: background 0.3s;
}

.btn:hover {
    background: #0055aa;
}

.btn-danger {
    background: #dc3545;
}

.btn-danger:hover {
    background: #bb2d3b;
}

.btn-success {
    background: #28a745;
}

.btn-success:hover {
    background: #218838;
}

/* Alert boxes */
.alert {
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    border-radius: 4px;
}

.alert-info {
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}

.alert-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeeba;
    color: #856404;
}

.alert-danger {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5rem;
}

table th,
table td {
    padding: 0.75rem;
    border: 1px solid #dee2e6;
    text-align: left;
}

table th {
    background: #f8f9fa;
    font-weight: 600;
}

table tr:nth-child(even) {
    background: #f8f9fa;
}

/* Form elements */
form {
    margin-bottom: 1.5rem;
}

.form-group {
    margin-bottom: 1rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

input[type="text"],
input[type="email"],
input[type="tel"],
input[type="number"],
select,
textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-family: inherit;
    font-size: 1rem;
}

textarea {
    min-height: 100px;
}

/* Footer */
footer {
    background: #303030;
    color: #f8f9fa;
    padding: 2rem 0 1rem;
}

.footer-content {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}

.footer-logo img {
    height: 40px;
}

.footer-links h3,
.footer-contact h3 {
    margin-bottom: 1rem;
    color: #cce5ff;
}

.footer-links ul {
    list-style: none;
}

.footer-links a {
    color: #f8f9fa;
    text-decoration: none;
    display: block;
    margin-bottom: 0.5rem;
}

.footer-links a:hover {
    color: #cce5ff;
}

.footer-contact a {
    color: #cce5ff;
    text-decoration: none;
}

.footer-bottom {
    border-top: 1px solid #555;
    padding-top: 1rem;
    text-align: center;
    font-size: 0.9rem;
}

/* Utilities */
.text-center {
    text-align: center;
}

.text-danger {
    color: #dc3545;
}

.text-success {
    color: #28a745;
}

.text-info {
    color: #17a2b8;
}

.mb-1 {
    margin-bottom: 0.5rem;
}

.mb-2 {
    margin-bottom: 1rem;
}

.mb-3 {
    margin-bottom: 1.5rem;
}

.mt-3 {
    margin-top: 1.5rem;
}

/* Griglia per layout */
.row {
    display: flex;
    flex-wrap: wrap;
    margin-right: -15px;
    margin-left: -15px;
}

.col-12 {
    flex: 0 0 100%;
    max-width: 100%;
    padding: 0 15px;
}

.col-6 {
    flex: 0 0 50%;
    max-width: 50%;
    padding: 0 15px;
}

.col-4 {
    flex: 0 0 33.333333%;
    max-width: 33.333333%;
    padding: 0 15px;
}

.col-3 {
    flex: 0 0 25%;
    max-width: 25%;
    padding: 0 15px;
}

/* Mappa */
.map-container {
    height: 400px;
    width: 100%;
    margin-bottom: 1.5rem;
}

/* Tabs */
.tabs {
    margin-bottom: 1.5rem;
}

.tab-nav {
    display: flex;
    list-style: none;
    border-bottom: 1px solid #dee2e6;
}

.tab-nav-item {
    padding: 0.5rem 1rem;
    cursor: pointer;
    margin-bottom: -1px;
}

.tab-nav-item.active {
    border: 1px solid #dee2e6;
    border-bottom: 1px solid white;
    border-radius: 4px 4px 0 0;
    font-weight: 500;
}

.tab-content {
    padding: 1rem 0;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-danger {
    background: #dc3545;
    color: white;
}

.badge-warning {
    background: #ffc107;
    color: #212529;
}

.badge-info {
    background: #17a2b8;
    color: white;
}

.badge-success {
    background: #28a745;
    color: white;
}

/* Image gallery */
.gallery {
    display: flex;
    flex-wrap: wrap;
    margin: 0 -5px;
}

.gallery-item {
    flex: 0 0 calc(33.333333% - 10px);
    margin: 5px;
    position: relative;
}

.gallery-item img {
    width: 100%;
    height: auto;
    border-radius: 4px;
    display: block;
}

.gallery-caption {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 0.5rem;
    font-size: 0.9rem;
    opacity: 0;
    transition: opacity 0.3s;
}

.gallery-item:hover .gallery-caption {
    opacity: 1;
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000;
    justify-content: center;
    align-items: center;
}

.modal.active {
    display: flex;
}

.modal-content {
    background: white;
    padding: 1.5rem;
    border-radius: 5px;
    max-width: 500px;
    width: 100%;
    position: relative;
}

.modal-close {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 1.5rem;
    cursor: pointer;
    color: #aaa;
}

.modal-close:hover {
    color: #333;
}

.modal-header {
    margin-bottom: 1rem;
}

.modal-footer {
    margin-top: 1.5rem;
    text-align: right;
}
"""
    
    # File CSS per responsive design
    responsive_css = """
/* Responsive Styles */
@media (max-width: 1200px) {
    .container {
        max-width: 960px;
    }
}

@media (max-width: 992px) {
    .container {
        max-width: 720px;
    }
    
    .footer-content {
        flex-direction: column;
    }
    
    .footer-logo, .footer-links, .footer-contact {
        margin-bottom: 1.5rem;
    }
}

@media (max-width: 768px) {
    .container {
        max-width: 540px;
    }
    
    .mobile-menu-toggle {
        display: block;
        cursor: pointer;
    }
    
    .mobile-menu-toggle span {
        display: block;
        width: 25px;
        height: 3px;
        margin: 5px 0;
        background: white;
    }
    
    .main-nav {
        display: none;
        position: absolute;
        top: 70px;
        left: 0;
        right: 0;
        background: #0066cc;
        padding: 1rem;
    }
    
    .main-nav.active {
        display: block;
    }
    
    .main-nav ul {
        flex-direction: column;
    }
    
    .main-nav li {
        margin: 0.5rem 0;
    }
    
    .col-6, .col-4, .col-3 {
        flex: 0 0 100%;
        max-width: 100%;
    }
    
    .gallery-item {
        flex: 0 0 calc(50% - 10px);
    }
    
    .tab-nav {
        flex-wrap: wrap;
    }
    
    .tab-nav-item {
        flex-grow: 1;
        text-align: center;
    }
}

@media (max-width: 576px) {
    .gallery-item {
        flex: 0 0 100%;
    }
    
    header, footer {
        text-align: center;
    }
    
    .logo, .mobile-menu-toggle {
        margin-bottom: 1rem;
    }
}

/* Print styles */
@media print {
    header, footer, .mobile-menu-toggle {
        display: none;
    }
    
    body {
        font-size: 12pt;
        background: white;
        color: black;
    }
    
    .container {
        width: 100%;
        max-width: none;
    }
    
    .content {
        box-shadow: none;
        padding: 0;
    }
    
    a {
        text-decoration: none;
        color: black;
    }
    
    a[href]:after {
        content: " (" attr(href) ")";
    }
    
    .card {
        border: 1px solid #ddd;
        box-shadow: none;
    }
    
    .map-container {
        page-break-inside: avoid;
    }
}
"""
    
    try:
        # Scrivi file CSS
        with open(os.path.join(css_dir, "main.css"), "w") as f:
            f.write(main_css)
        
        with open(os.path.join(css_dir, "responsive.css"), "w") as f:
            f.write(responsive_css)
        
        return True
    except Exception as e:
        st.error(f"Errore nella creazione dei file CSS: {str(e)}")
        return False


def create_js_files():
    """
    Crea i file JavaScript necessari per il sito statico.
    
    Returns:
        bool: True se creati con successo
    """
    js_dir = os.path.join(EXPORT_DIR, "assets", "scripts")
    os.makedirs(js_dir, exist_ok=True)
    
    # File JS principale
    main_js = """
// Funzioni comuni per tutte le pagine

// Gestione del menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (mobileMenuToggle && mainNav) {
        mobileMenuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
        });
    }
    
    // Gestore delle tabs
    const tabNavItems = document.querySelectorAll('.tab-nav-item');
    if (tabNavItems.length > 0) {
        tabNavItems.forEach(item => {
            item.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                const tabContent = document.querySelector(`.tab-pane[data-tab="${tabId}"]`);
                
                // Rimuovi classe active da tutti i tab nav e content
                document.querySelectorAll('.tab-nav-item').forEach(navItem => {
                    navItem.classList.remove('active');
                });
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                });
                
                // Aggiungi classe active al tab cliccato
                this.classList.add('active');
                if (tabContent) {
                    tabContent.classList.add('active');
                }
            });
        });
    }
    
    // Gestore delle modali
    const modalTriggers = document.querySelectorAll('[data-modal]');
    if (modalTriggers.length > 0) {
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                const modalId = this.getAttribute('data-modal');
                const modal = document.getElementById(modalId);
                
                if (modal) {
                    modal.classList.add('active');
                }
            });
        });
        
        // Chiusura modale
        const modalCloses = document.querySelectorAll('.modal-close');
        modalCloses.forEach(close => {
            close.addEventListener('click', function() {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.classList.remove('active');
                }
            });
        });
        
        // Chiudi modale cliccando all'esterno
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('active');
                }
            });
        });
    }
    
    // Protezione XSS per gli input
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('input', function() {
            this.value = sanitizeInput(this.value);
        });
    });
});

// Controlla se è supportata geolocalizzazione
function isGeolocationSupported() {
    return 'geolocation' in navigator;
}

// Ottieni posizione utente
function getUserLocation(callback) {
    if (!isGeolocationSupported()) {
        console.error('Geolocalizzazione non supportata dal browser');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        position => {
            const location = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            callback(location);
        },
        error => {
            console.error('Errore nella geolocalizzazione:', error.message);
            callback(null);
        }
    );
}

// Formatta data
function formatDate(date) {
    if (!date) return '';
    
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// Aggiungi alert dinamici
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || document.createElement('div');
    if (!alertContainer.classList.contains('alert-container')) {
        alertContainer.className = 'alert-container';
        document.querySelector('main').prepend(alertContainer);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = message;
    
    // Aggiungi pulsante chiusura
    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.className = 'alert-close';
    closeBtn.addEventListener('click', function() {
        alert.remove();
    });
    
    alert.prepend(closeBtn);
    alertContainer.appendChild(alert);
    
    // Auto-chiusura dopo 5 secondi per info e success
    if (type === 'info' || type === 'success') {
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Cookie consent
function initCookieConsent() {
    if (localStorage.getItem('cookie_consent') !== 'true') {
        const consentBanner = document.createElement('div');
        consentBanner.className = 'cookie-banner';
        consentBanner.innerHTML = `
            <p>Questo sito utilizza cookie per migliorare la tua esperienza. 
            <a href="privacy.html">Privacy Policy</a></p>
            <button id="cookie-accept" class="btn btn-sm">Accetta</button>
        `;
        
        document.body.appendChild(consentBanner);
        
        document.getElementById('cookie-accept').addEventListener('click', function() {
            localStorage.setItem('cookie_consent', 'true');
            consentBanner.remove();
        });
    }
}

// Chiama l'inizializzazione del cookie consent
initCookieConsent();

// PWA service worker (se supportato)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/service-worker.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            }, function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}
"""
    
    # File JS per ogni pagina
    home_js = """
// Script specifico per la home page
document.addEventListener('DOMContentLoaded', function() {
    // Placeholder per dati sismici recenti (in produzione, caricati da API)
    const recentEarthquakes = [
        { magnitude: 3.2, location: "Costa Siciliana", date: "2025-04-04T10:15:00", depth: 10 },
        { magnitude: 2.5, location: "Provincia di Roma", date: "2025-04-03T22:45:00", depth: 15 },
        { magnitude: 4.1, location: "Costa Calabra", date: "2025-04-03T14:30:00", depth: 25 },
        { magnitude: 1.8, location: "Provincia di Napoli", date: "2025-04-02T08:20:00", depth: 5 },
        { magnitude: 3.5, location: "Provincia di L'Aquila", date: "2025-04-01T18:10:00", depth: 12 }
    ];
    
    // Renderizza lista terremoti recenti
    const earthquakeContainer = document.getElementById('recent-earthquakes');
    if (earthquakeContainer) {
        let html = '';
        
        recentEarthquakes.forEach(quake => {
            // Determina classe di colore per magnitudine
            let magnitudeClass = 'text-info';
            if (quake.magnitude >= 4) {
                magnitudeClass = 'text-danger';
            } else if (quake.magnitude >= 3) {
                magnitudeClass = 'text-warning';
            }
            
            html += `
                <div class="card mb-2">
                    <div class="row">
                        <div class="col-3">
                            <span class="magnitude ${magnitudeClass}">${quake.magnitude.toFixed(1)}</span>
                        </div>
                        <div class="col-9">
                            <div class="quake-info">
                                <strong>${quake.location}</strong><br>
                                <small>${formatDate(quake.date)} - Prof: ${quake.depth} km</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        earthquakeContainer.innerHTML = html;
    }
    
    // Placeholder per meteo (in produzione, caricato da API)
    const weatherData = {
        city: "Roma",
        temperature: 22,
        description: "Soleggiato",
        humidity: 65,
        wind: 8
    };
    
    // Renderizza widget meteo
    const weatherWidget = document.getElementById('weather-widget');
    if (weatherWidget) {
        weatherWidget.innerHTML = `
            <div class="weather-card">
                <h3>${weatherData.city}</h3>
                <div class="weather-main">
                    <span class="temperature">${weatherData.temperature}°C</span>
                    <span class="description">${weatherData.description}</span>
                </div>
                <div class="weather-details">
                    <div>Umidità: ${weatherData.humidity}%</div>
                    <div>Vento: ${weatherData.wind} km/h</div>
                </div>
            </div>
        `;
    }
});
"""
    
    monitoraggio_js = """
// Script per la pagina di monitoraggio sismico
document.addEventListener('DOMContentLoaded', function() {
    // Inizializza mappa sismica se il container esiste
    const mapContainer = document.getElementById('earthquake-map');
    if (mapContainer) {
        // Carica la mappa usando Leaflet (assicurarsi di includere Leaflet nei link CSS/JS)
        const map = L.map('earthquake-map').setView([41.9, 12.5], 6);
        
        // Aggiungi layer OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Placeholder per dati sismici (in produzione, caricati da API)
        const earthquakeData = [
            { magnitude: 3.2, location: "Costa Siciliana", lat: 38.1, lng: 15.6, date: "2025-04-04T10:15:00", depth: 10 },
            { magnitude: 2.5, location: "Provincia di Roma", lat: 41.9, lng: 12.5, date: "2025-04-03T22:45:00", depth: 15 },
            { magnitude: 4.1, location: "Costa Calabra", lat: 39.3, lng: 16.3, date: "2025-04-03T14:30:00", depth: 25 },
            { magnitude: 1.8, location: "Provincia di Napoli", lat: 40.8, lng: 14.3, date: "2025-04-02T08:20:00", depth: 5 },
            { magnitude: 3.5, location: "Provincia di L'Aquila", lat: 42.3, lng: 13.4, date: "2025-04-01T18:10:00", depth: 12 }
        ];
        
        // Aggiungi marker per ogni terremoto
        earthquakeData.forEach(quake => {
            // Dimensione marker basata su magnitudine
            const radius = Math.max(5, quake.magnitude * 3);
            
            // Colore basato su magnitudine
            let color = '#3388ff'; // Blu per bassa magnitudo
            if (quake.magnitude >= 4) {
                color = '#dc3545'; // Rosso per alta magnitudo
            } else if (quake.magnitude >= 3) {
                color = '#ffc107'; // Giallo per media magnitudo
            }
            
            // Crea marker circolare
            const marker = L.circleMarker([quake.lat, quake.lng], {
                radius: radius,
                fillColor: color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);
            
            // Aggiungi popup con informazioni
            marker.bindPopup(`
                <strong>M ${quake.magnitude.toFixed(1)}</strong><br>
                ${quake.location}<br>
                Data: ${formatDate(quake.date)}<br>
                Profondità: ${quake.depth} km
            `);
        });
        
        // Aggiorna la mappa
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }
});
"""
    
    try:
        # Scrivi file JS principali
        with open(os.path.join(js_dir, "main.js"), "w") as f:
            f.write(main_js)
        
        with open(os.path.join(js_dir, "home.js"), "w") as f:
            f.write(home_js)
        
        with open(os.path.join(js_dir, "monitoraggio.js"), "w") as f:
            f.write(monitoraggio_js)
        
        # Crea file JS base per altre pagine
        for page in PAGES:
            if page["name"] not in ["home", "monitoraggio"]:
                with open(os.path.join(js_dir, f"{page['name']}.js"), "w") as f:
                    f.write(f"// Script per la pagina {page['title']}")
        
        return True
    except Exception as e:
        st.error(f"Errore nella creazione dei file JavaScript: {str(e)}")
        return False


def create_pwa_files():
    """
    Crea i file necessari per la Progressive Web App (PWA).
    
    Returns:
        bool: True se creati con successo
    """
    try:
        # Crea manifest.json
        manifest = {
            "name": "SismaVer2 - Monitoraggio Ambientale",
            "short_name": "SismaVer2",
            "description": "Monitoraggio sismico, vulcanico e meteorologico per l'Italia",
            "start_url": "/index.html",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#0066cc",
            "icons": [
                {
                    "src": "assets/images/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "assets/images/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        
        with open(os.path.join(EXPORT_DIR, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Crea service-worker.js
        service_worker = """
// Service Worker for SismaVer2 PWA
const CACHE_NAME = 'sisma-ver2-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/assets/styles/main.css',
  '/assets/styles/responsive.css',
  '/assets/scripts/main.js',
  '/assets/images/logo.png'
];

// Installazione Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Gestione fetch
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - restituisci risposta dalla cache
        if (response) {
          return response;
        }
        return fetch(event.request)
          .then(response => {
            // Verifica se la risposta è valida
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clona la risposta
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
              
            return response;
          });
      })
  );
});

// Attivazione e pulizia cache vecchie
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
"""
        
        with open(os.path.join(EXPORT_DIR, "service-worker.js"), "w") as f:
            f.write(service_worker)
        
        return True
    except Exception as e:
        st.error(f"Errore nella creazione dei file PWA: {str(e)}")
        return False


def create_web_config_files():
    """
    Crea file di configurazione per hosting web.
    
    Returns:
        bool: True se creati con successo
    """
    try:
        # .htaccess per Apache
        htaccess = """
# Abilita mod_rewrite
RewriteEngine On

# Redirect a HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Compressione GZIP
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/x-javascript application/json
</IfModule>

# Cache control
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpg "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType text/html "access plus 1 day"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType application/pdf "access plus 1 month"
  ExpiresByType text/x-javascript "access plus 1 month"
  ExpiresByType application/x-shockwave-flash "access plus 1 month"
  ExpiresDefault "access plus 1 week"
</IfModule>

# Protezione directory
Options -Indexes

# Blocca accesso a file critici
<FilesMatch "^(\.htaccess|\.htpasswd|\.git|\.env|config\.json)$">
  Order Allow,Deny
  Deny from all
</FilesMatch>

# Assicurati che i file .html vengano serviti come HTML
AddType text/html .html

# Impostazione pagina 404 personalizzata
ErrorDocument 404 /404.html

# Headers di sicurezza
<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set X-XSS-Protection "1; mode=block"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  Header set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;"
</IfModule>
"""
        
        # web.config per IIS
        web_config = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="HTTP to HTTPS redirect" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{HTTPS}" pattern="off" ignoreCase="true" />
          </conditions>
          <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
        </rule>
      </rules>
    </rewrite>
    <staticContent>
      <clientCache cacheControlMode="UseMaxAge" cacheControlMaxAge="30.00:00:00" />
      <mimeMap fileExtension=".json" mimeType="application/json" />
      <mimeMap fileExtension=".webp" mimeType="image/webp" />
      <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
    </staticContent>
    <httpProtocol>
      <customHeaders>
        <add name="X-Content-Type-Options" value="nosniff" />
        <add name="X-Frame-Options" value="SAMEORIGIN" />
        <add name="X-XSS-Protection" value="1; mode=block" />
        <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
        <add name="Content-Security-Policy" value="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;" />
      </customHeaders>
    </httpProtocol>
    <httpErrors errorMode="Custom">
      <remove statusCode="404" />
      <error statusCode="404" path="/404.html" responseMode="File" />
    </httpErrors>
  </system.webServer>
</configuration>
"""
        
        # robots.txt
        robots_txt = """
User-agent: *
Allow: /

Sitemap: https://sisma-ver2.it/sitemap.xml
"""
        
        # sitemap.xml
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
        for page in PAGES:
            sitemap_xml += f"""  <url>
    <loc>https://sisma-ver2.it/{page['name']}.html</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{1.0 if page['name'] == 'home' else 0.8}</priority>
  </url>
"""
        sitemap_xml += "</urlset>"
        
        # Scrittura file
        with open(os.path.join(EXPORT_DIR, ".htaccess"), "w") as f:
            f.write(htaccess)
        
        with open(os.path.join(EXPORT_DIR, "web.config"), "w") as f:
            f.write(web_config)
        
        with open(os.path.join(EXPORT_DIR, "robots.txt"), "w") as f:
            f.write(robots_txt)
        
        with open(os.path.join(EXPORT_DIR, "sitemap.xml"), "w") as f:
            f.write(sitemap_xml)
        
        # Pagina 404
        page_404 = generate_html_template(
            "Pagina non trovata", 
            "La pagina richiesta non è stata trovata",
            """
            <div class="error-container text-center">
                <h1 class="error-code">404</h1>
                <h2 class="error-message">Pagina non trovata</h2>
                <p>La pagina che stai cercando potrebbe essere stata rimossa, rinominata o temporaneamente non disponibile.</p>
                <a href="index.html" class="btn mt-3">Torna alla home</a>
            </div>
            """,
            "404"
        )
        
        with open(os.path.join(EXPORT_DIR, "404.html"), "w") as f:
            f.write(page_404)
        
        return True
    except Exception as e:
        st.error(f"Errore nella creazione dei file di configurazione web: {str(e)}")
        return False


def copy_assets():
    """
    Copia le immagini e altri asset necessari.
    
    Returns:
        bool: True se copiati con successo
    """
    try:
        # Crea directory per immagini
        img_dir = os.path.join(EXPORT_DIR, "assets", "images")
        os.makedirs(img_dir, exist_ok=True)
        
        # Identifica le immagini da copiare
        assets_to_copy = [
            # Immagini dal progetto originale
            {"src": "images/logo.png", "dest": "assets/images/logo.png"},
            {"src": "images/logo-footer.png", "dest": "assets/images/logo-footer.png"},
            {"src": "images/favicon.ico", "dest": "assets/images/favicon.ico"},
        ]
        
        # TODO: Sostituire con immagini reali dal progetto
        # Per ora creiamo placeholder
        placeholder_img = os.path.join(img_dir, "placeholder.png")
        with open(placeholder_img, "w") as f:
            f.write("Placeholder for image")
        
        # Copia icone per PWA
        shutil.copy(placeholder_img, os.path.join(img_dir, "icon-192x192.png"))
        shutil.copy(placeholder_img, os.path.join(img_dir, "icon-512x512.png"))
        
        # Copia logo
        shutil.copy(placeholder_img, os.path.join(img_dir, "logo.png"))
        shutil.copy(placeholder_img, os.path.join(img_dir, "logo-footer.png"))
        shutil.copy(placeholder_img, os.path.join(img_dir, "favicon.ico"))
        
        return True
    except Exception as e:
        st.error(f"Errore nella copia degli asset: {str(e)}")
        return False


def convert_streamlit_content(module_name, content_func):
    """
    Converte il contenuto di una pagina Streamlit in HTML.
    Questa è una funzione semplificata e richiede adattamenti specifici
    per ogni modulo e componente Streamlit.
    
    Args:
        module_name (str): Nome del modulo
        content_func (callable): Funzione che genera il contenuto Streamlit
    
    Returns:
        str: Contenuto HTML
    """
    # Questa è una funzione di esempio che dovrebbe essere adattata 
    # per convertire specifici widget Streamlit in HTML
    
    # Placeholder per il contenuto della pagina home
    if module_name == "home":
        return """
        <div class="row">
            <div class="col-12 mb-3">
                <div class="alert alert-info">
                    <strong>SismaVer2</strong> è un sistema di monitoraggio ambientale nazionale che fornisce 
                    informazioni in tempo reale su eventi sismici, vulcanici e condizioni meteorologiche.
                    Questo è un'evoluzione dell'app originale <a href="https://sismocampania.streamlit.app" target="_blank">SismoCampania</a>.
                </div>
            </div>
            
            <div class="col-6">
                <div class="card">
                    <h2 class="card-title">Ultimi eventi sismici</h2>
                    <div id="recent-earthquakes">
                        <!-- Popolato via JavaScript -->
                        <div class="loading-spinner">Caricamento...</div>
                    </div>
                    <a href="monitoraggio.html" class="btn mt-3">Monitoraggio completo</a>
                </div>
            </div>
            
            <div class="col-6">
                <div class="card">
                    <h2 class="card-title">Meteo</h2>
                    <div id="weather-widget">
                        <!-- Popolato via JavaScript -->
                        <div class="loading-spinner">Caricamento...</div>
                    </div>
                    <a href="meteo.html" class="btn mt-3">Previsioni dettagliate</a>
                </div>
            </div>
            
            <div class="col-12 mt-3">
                <div class="card card-emergency">
                    <h2 class="card-title">Emergenze e protocolli</h2>
                    <p>In caso di emergenza, consulta i protocolli e le informazioni utili:</p>
                    <div class="row">
                        <div class="col-4">
                            <a href="emergenza.html" class="btn btn-danger">Protocolli di emergenza</a>
                        </div>
                        <div class="col-4">
                            <a href="primo_soccorso.html" class="btn">Guide al primo soccorso</a>
                        </div>
                        <div class="col-4">
                            <a href="#" class="btn" data-modal="emergency-numbers">Numeri utili</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modale numeri di emergenza -->
        <div id="emergency-numbers" class="modal">
            <div class="modal-content">
                <span class="modal-close">&times;</span>
                <div class="modal-header">
                    <h2>Numeri di emergenza</h2>
                </div>
                <div class="modal-body">
                    <ul>
                        <li><strong>112</strong> - Numero Unico Emergenze</li>
                        <li><strong>115</strong> - Vigili del Fuoco</li>
                        <li><strong>118</strong> - Emergenza Sanitaria</li>
                        <li><strong>1500</strong> - Emergenze Sanitarie Pubbliche</li>
                        <li><strong>117</strong> - Guardia di Finanza</li>
                        <li><strong>1530</strong> - Emergenze in Mare</li>
                    </ul>
                </div>
            </div>
        </div>
        """
    
    # Placeholder per il contenuto della pagina monitoraggio
    elif module_name == "monitoraggio":
        return """
        <div class="row">
            <div class="col-12 mb-3">
                <div class="tabs">
                    <ul class="tab-nav">
                        <li class="tab-nav-item active" data-tab="sismico">Sismico</li>
                        <li class="tab-nav-item" data-tab="idrogeologico">Idrogeologico</li>
                    </ul>
                    
                    <div class="tab-content">
                        <div class="tab-pane active" data-tab="sismico">
                            <div class="map-container" id="earthquake-map"></div>
                            
                            <div class="card mb-3">
                                <h3 class="card-title">Filtri</h3>
                                <div class="row">
                                    <div class="col-4">
                                        <label for="magnitude-filter">Magnitudo minima</label>
                                        <select id="magnitude-filter" class="form-control">
                                            <option value="0">Tutte</option>
                                            <option value="2">≥ 2.0</option>
                                            <option value="3">≥ 3.0</option>
                                            <option value="4">≥ 4.0</option>
                                        </select>
                                    </div>
                                    <div class="col-4">
                                        <label for="date-filter">Periodo</label>
                                        <select id="date-filter" class="form-control">
                                            <option value="7">Ultima settimana</option>
                                            <option value="30">Ultimo mese</option>
                                            <option value="90">Ultimi 3 mesi</option>
                                            <option value="365">Ultimo anno</option>
                                        </select>
                                    </div>
                                    <div class="col-4">
                                        <label for="region-filter">Regione</label>
                                        <select id="region-filter" class="form-control">
                                            <option value="all">Tutte</option>
                                            <option value="nord">Nord Italia</option>
                                            <option value="centro">Centro Italia</option>
                                            <option value="sud">Sud Italia</option>
                                            <option value="isole">Isole</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3 class="card-title">Statistiche</h3>
                                <div class="row">
                                    <div class="col-3 text-center">
                                        <div class="stat-box">
                                            <div class="stat-value">125</div>
                                            <div class="stat-label">Eventi ultimi 7 giorni</div>
                                        </div>
                                    </div>
                                    <div class="col-3 text-center">
                                        <div class="stat-box">
                                            <div class="stat-value">4.1</div>
                                            <div class="stat-label">Magnitudo massima</div>
                                        </div>
                                    </div>
                                    <div class="col-3 text-center">
                                        <div class="stat-box">
                                            <div class="stat-value">15.3</div>
                                            <div class="stat-label">Profondità media (km)</div>
                                        </div>
                                    </div>
                                    <div class="col-3 text-center">
                                        <div class="stat-box">
                                            <div class="stat-value">42</div>
                                            <div class="stat-label">Eventi significativi (M≥2.5)</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-pane" data-tab="idrogeologico">
                            <h3>Monitoraggio Idrogeologico</h3>
                            <p>Questa sezione mostra le informazioni relative al rischio idrogeologico in Italia.</p>
                            
                            <div class="alert alert-warning">
                                <strong>Attenzione!</strong> Seleziona una regione per visualizzare le allerte idrogeologiche attive.
                            </div>
                            
                            <!-- Placeholder per la mappa idrogeologica -->
                            <div class="map-container">
                                <img src="assets/images/placeholder.png" alt="Mappa idrogeologica" style="width: 100%; height: 400px; object-fit: cover;">
                            </div>
                            
                            <!-- Placeholder per i dati idrogeologici -->
                            <div class="card mt-3">
                                <h3 class="card-title">Allerte attive</h3>
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Regione</th>
                                            <th>Livello</th>
                                            <th>Tipo</th>
                                            <th>Valido fino al</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Liguria</td>
                                            <td><span class="badge badge-warning">Arancione</span></td>
                                            <td>Idrogeologico</td>
                                            <td>05/04/2025 20:00</td>
                                        </tr>
                                        <tr>
                                            <td>Emilia-Romagna</td>
                                            <td><span class="badge badge-warning">Arancione</span></td>
                                            <td>Idraulico</td>
                                            <td>05/04/2025 23:59</td>
                                        </tr>
                                        <tr>
                                            <td>Calabria</td>
                                            <td><span class="badge badge-danger">Rossa</span></td>
                                            <td>Temporali</td>
                                            <td>06/04/2025 14:00</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Include Leaflet per la mappa -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        """
    
    # Placeholder per altre pagine
    else:
        return f"""
        <div class="row">
            <div class="col-12">
                <div class="alert alert-info">
                    <strong>Contenuto in costruzione</strong> - Questa pagina ({module_name}) è in fase di sviluppo.
                </div>
                <div class="card">
                    <h2 class="card-title">Informazioni su {module_name}</h2>
                    <p>Qui sarà disponibile il contenuto della pagina {module_name}.</p>
                </div>
            </div>
        </div>
        """


def export_page(page_name, title, description):
    """
    Esporta una singola pagina come HTML statico.
    
    Args:
        page_name (str): Nome della pagina
        title (str): Titolo della pagina
        description (str): Descrizione della pagina
    
    Returns:
        bool: True se esportata con successo
    """
    try:
        # Import dinamico del modulo
        try:
            module = __import__(f"modules.{page_name}", fromlist=["show"])
            content_func = module.show
        except (ImportError, AttributeError):
            # Se non esiste il modulo specifico, usa placeholder
            content_func = None
        
        # Converti contenuto Streamlit in HTML
        html_content = convert_streamlit_content(page_name, content_func)
        
        # Genera HTML completo
        html_page = generate_html_template(title, description, html_content, page_name)
        
        # Determina il nome del file
        file_name = "index.html" if page_name == "home" else f"{page_name}.html"
        
        # Salva il file
        with open(os.path.join(EXPORT_DIR, file_name), "w") as f:
            f.write(html_page)
        
        return True
    except Exception as e:
        st.error(f"Errore nell'esportazione della pagina {page_name}: {str(e)}")
        return False


def create_security_headers():
    """
    Crea un file con gli header di sicurezza per vari server web.
    
    Returns:
        bool: True se creato con successo
    """
    try:
        content = """# Security Headers per SismaVer2

# Apache (.htaccess)
<IfModule mod_headers.c>
  # Previene MIME-sniffing
  Header set X-Content-Type-Options "nosniff"
  
  # Previene Clickjacking
  Header set X-Frame-Options "SAMEORIGIN"
  
  # Abilita protezione XSS per browser legacy
  Header set X-XSS-Protection "1; mode=block"
  
  # Controlla informazioni trasmesse con referer
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  
  # Content Security Policy
  Header set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;"
  
  # Feature Policy/Permissions Policy
  Header set Permissions-Policy "geolocation=self, camera=(), microphone=(), payment=()"
  
  # HTTP Strict Transport Security (attiva solo su HTTPS)
  Header set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
</IfModule>

# Nginx (nginx.conf)
# server {
#   # Previene MIME-sniffing
#   add_header X-Content-Type-Options "nosniff" always;
#   
#   # Previene Clickjacking
#   add_header X-Frame-Options "SAMEORIGIN" always;
#   
#   # Abilita protezione XSS per browser legacy
#   add_header X-XSS-Protection "1; mode=block" always;
#   
#   # Controlla informazioni trasmesse con referer
#   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
#   
#   # Content Security Policy
#   add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;" always;
#   
#   # Feature Policy/Permissions Policy
#   add_header Permissions-Policy "geolocation=self, camera=(), microphone=(), payment=()" always;
#   
#   # HTTP Strict Transport Security (attiva solo su HTTPS)
#   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
# }

# IIS (web.config)
# <system.webServer>
#   <httpProtocol>
#     <customHeaders>
#       <add name="X-Content-Type-Options" value="nosniff" />
#       <add name="X-Frame-Options" value="SAMEORIGIN" />
#       <add name="X-XSS-Protection" value="1; mode=block" />
#       <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
#       <add name="Content-Security-Policy" value="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;" />
#       <add name="Permissions-Policy" value="geolocation=self, camera=(), microphone=(), payment=()" />
#       <add name="Strict-Transport-Security" value="max-age=31536000; includeSubDomains; preload" />
#     </customHeaders>
#   </httpProtocol>
# </system.webServer>

# Configurazione per Netlify (_headers)
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;
  Permissions-Policy: geolocation=self, camera=(), microphone=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
"""
        
        # Scrivi file con security headers
        with open(os.path.join(EXPORT_DIR, "security_headers.txt"), "w") as f:
            f.write(content)
        
        # Per Netlify
        with open(os.path.join(EXPORT_DIR, "_headers"), "w") as f:
            f.write("""/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self' https://*.streamlit.app;
  Permissions-Policy: geolocation=self, camera=(), microphone=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
""")
        
        return True
    except Exception as e:
        st.error(f"Errore nella creazione degli header di sicurezza: {str(e)}")
        return False


def export_html():
    """
    Esporta l'intera applicazione come sito web HTML statico.
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Crea directory di export
        if os.path.exists(EXPORT_DIR):
            shutil.rmtree(EXPORT_DIR)
        os.makedirs(EXPORT_DIR)
        
        st.info("Esportazione HTML in corso...")
        
        # Crea struttura di directory
        os.makedirs(os.path.join(EXPORT_DIR, "assets", "styles"), exist_ok=True)
        os.makedirs(os.path.join(EXPORT_DIR, "assets", "scripts"), exist_ok=True)
        os.makedirs(os.path.join(EXPORT_DIR, "assets", "images"), exist_ok=True)
        
        # Crea file di supporto
        create_css_files()
        create_js_files()
        create_pwa_files()
        create_web_config_files()
        create_security_headers()
        copy_assets()
        
        # Esporta ogni pagina
        for page in PAGES:
            export_page(page["name"], page["title"], page["description"])
        
        # Crea README con istruzioni
        with open(os.path.join(EXPORT_DIR, "README.md"), "w") as f:
            f.write(f"""# SismaVer2 - Versione HTML Statica

Questa è la versione HTML statica di SismaVer2, esportata il {datetime.now().strftime('%d/%m/%Y')}.

## Istruzioni per l'hosting

### Opzione 1: Server web (Apache, Nginx, IIS)
1. Carica tutti i file su un server web
2. Configura il server web per utilizzare gli header di sicurezza (vedi `security_headers.txt`)
3. Assicurati che il server web supporti HTTPS

### Opzione 2: Hosting statico (GitHub Pages, Netlify, Vercel)
1. Carica i file su un repository GitHub
2. Configura GitHub Pages, Netlify o Vercel per il deployment
3. Per Netlify, il file `_headers` è già configurato per la sicurezza

## Struttura dei file
- `index.html`: Pagina principale
- `assets/`: Contiene CSS, JavaScript e immagini
- `*.html`: Altre pagine dell'applicazione
- `manifest.json` e `service-worker.js`: Supporto PWA
- `robots.txt` e `sitemap.xml`: SEO

## Modifiche e aggiornamenti
Questa versione statica non può aggiornare i dati in tempo reale come la versione Streamlit.
Per aggiornamenti, è necessario modificare il codice sorgente e rigenerare l'HTML.

## Sicurezza
Questa versione include numerose misure di sicurezza:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- Protezione XSS e CSRF
- Sanitizzazione input
- Headers di sicurezza

Per qualsiasi domanda o assistenza, contatta: meteotorre@gmail.com
""")
        
        return True, f"Applicazione esportata con successo in {EXPORT_DIR}/"
    
    except Exception as e:
        return False, f"Errore nell'esportazione: {str(e)}"


def check_export_compatibility():
    """
    Verifica la compatibilità dell'applicazione con l'esportazione HTML.
    
    Returns:
        tuple: (is_compatible, issues)
    """
    issues = []
    
    # Controlla dipendenze che potrebbero non funzionare in HTML statico
    problematic_deps = [
        "streamlit", "st.", "st_", "session_state", 
        "experimental_", "streamlit-folium", "supabase"
    ]
    
    # Lista moduli da controllare
    modules_to_check = []
    for page in PAGES:
        module_path = f"modules/{page['name']}.py"
        if os.path.exists(module_path):
            modules_to_check.append(module_path)
    
    # Controlla i moduli
    for module_path in modules_to_check:
        try:
            with open(module_path, "r") as f:
                content = f.read()
                
                for dep in problematic_deps:
                    if dep in content:
                        issues.append(f"Il modulo {module_path} utilizza {dep} che non è compatibile con HTML statico")
        except:
            issues.append(f"Impossibile leggere il modulo {module_path}")
    
    # Controlla presenza di database
    if "supabase" in str(issues) or "sqlite" in str(issues) or "database" in str(issues):
        issues.append("L'applicazione utilizza un database, che richiederà un backend per funzionare in HTML statico")
    
    is_compatible = len(issues) == 0
    
    return is_compatible, issues


def show():
    """
    Mostra l'interfaccia per l'esportazione HTML.
    """
    st.title("Esportazione HTML SismaVer2")
    
    st.write("""
    Questo modulo permette di esportare l'applicazione SismaVer2 come un sito web HTML statico,
    ottimizzato per la sicurezza e le prestazioni.
    """)
    
    st.subheader("Verifica compatibilità")
    
    is_compatible, issues = check_export_compatibility()
    
    if is_compatible:
        st.success("✅ L'applicazione sembra compatibile con l'esportazione HTML")
    else:
        st.warning("⚠️ Sono stati rilevati potenziali problemi di compatibilità")
        st.write("I seguenti problemi potrebbero richiedere adattamenti:")
        for issue in issues:
            st.write(f"- {issue}")
    
    st.subheader("Opzioni di esportazione")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_images = st.checkbox("Includi immagini", value=True)
        export_js = st.checkbox("Includi JavaScript interattivo", value=True)
        export_pwa = st.checkbox("Supporto PWA", value=True)
        export_security = st.checkbox("Implementa misure di sicurezza", value=True)
    
    with col2:
        export_seo = st.checkbox("Ottimizzazione SEO", value=True)
        export_analytics = st.checkbox("Includi Google Analytics", value=False)
        export_hosting = st.checkbox("File di configurazione per hosting", value=True)
        export_fallback = st.checkbox("Versione fallback per browser vecchi", value=False)
    
    st.subheader("Informazioni aggiuntive")
    
    site_name = st.text_input("Nome sito", "SismaVer2 - Monitoraggio Ambientale")
    site_description = st.text_area("Descrizione sito", "Sistema di monitoraggio sismico, vulcanico e meteorologico per l'Italia")
    contact_email = st.text_input("Email di contatto", "meteotorre@gmail.com")
    
    if st.button("Esporta HTML"):
        with st.spinner("Esportazione in corso..."):
            success, message = export_html()
            
            if success:
                st.success(message)
                st.info(f"L'applicazione è stata esportata nella directory: {EXPORT_DIR}/")
                st.info("Per utilizzare il sito, carica i file su un server web o servizio di hosting statico.")
                
                # Crea un file .zip con l'export
                zip_path = f"{EXPORT_DIR}.zip"
                shutil.make_archive(EXPORT_DIR, 'zip', EXPORT_DIR)
                
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Scarica ZIP",
                        data=f,
                        file_name="sisma_ver2_html.zip",
                        mime="application/zip"
                    )
            else:
                st.error(message)
    
    st.subheader("Note importanti")
    
    st.info("""
    L'esportazione HTML statica ha le seguenti limitazioni:
    
    1. **Dati statici**: I dati in tempo reale dovranno essere aggiornati manualmente o tramite API JavaScript
    2. **Funzionalità interattive**: Alcune funzionalità interattive di Streamlit potrebbero non funzionare
    3. **Database**: Le funzionalità che richiedono un database necessiteranno di un backend separato
    
    Per massimizzare la compatibilità:
    - Separa chiaramente la logica di presentazione dalla logica di business
    - Usa JavaScript per la logica client-side
    - Considera l'utilizzo di API serverless per i dati dinamici
    """)


if __name__ == "__main__":
    show()