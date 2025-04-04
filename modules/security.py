"""
Modulo per la sicurezza dell'applicazione SismaVer2.
Implementa protezioni contro attacchi XSS, CSRF, SQL Injection, DDoS e altri.
"""
import re
import hashlib
import time
import hmac
import base64
import uuid
import streamlit as st
import os
from datetime import datetime, timedelta

# Impostazioni di sicurezza generali
MAX_REQUESTS_PER_MINUTE = 60  # Limite di richieste al minuto per prevenire DDoS
TOKEN_EXPIRY_MINUTES = 60     # Scadenza dei token di sicurezza

# Chiave segreta per firmare token (in produzione usare variabile d'ambiente)
try:
    SECRET_KEY = os.environ.get("SECURITY_SECRET_KEY", str(uuid.uuid4()))
except:
    SECRET_KEY = "sisma_ver2_security_key_default"  # Solo per backup


def sanitize_input(text):
    """
    Sanitizza l'input dell'utente per prevenire attacchi XSS.
    Rimuove tag HTML e caratteri potenzialmente dannosi.
    
    Args:
        text (str): Testo da sanitizzare
    
    Returns:
        str: Testo sanitizzato
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Rimuovi tag HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Converti caratteri speciali
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;')
                .replace('/', '&#x2F;'))
    
    return text


def sanitize_json_field(field_value):
    """
    Sanitizza un campo da inserire in JSON per prevenire JSON injection.
    
    Args:
        field_value: Valore da sanitizzare
        
    Returns:
        Valore sanitizzato
    """
    if isinstance(field_value, str):
        # Sanitizza stringhe
        field_value = sanitize_input(field_value)
        # Previeni JSON injection
        field_value = field_value.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
    
    return field_value


def sanitize_sql(query_part):
    """
    Sanitizza parti di query SQL per prevenire SQL injection.
    Nota: da usare solo per casi specifici, preferire sempre parametrizzazione.
    
    Args:
        query_part (str): Parte di query da sanitizzare
    
    Returns:
        str: Parte di query sanitizzata
    """
    if not query_part or not isinstance(query_part, str):
        return ""
    
    # Rimuovi caratteri dannosi
    query_part = re.sub(r'[;\'"\\]', '', query_part)
    
    # Lista di parole chiave SQL da bloccare
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 
        'UNION', 'SELECT', 'EXEC', 'EXECUTE', '--', '/*', '*/'
    ]
    
    # Controlla e blocca parole chiave pericolose
    query_upper = query_part.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            # Log tentativo di SQL injection
            log_security_event(f"Tentativo di SQL injection bloccato: {query_part}")
            return ""
    
    return query_part


def generate_csrf_token():
    """
    Genera un token CSRF per proteggere dai Cross-Site Request Forgery.
    
    Returns:
        str: Token CSRF
    """
    if 'csrf_token' not in st.session_state:
        token = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        
        # Crea token firmato
        payload = f"{token}|{expiry.timestamp()}"
        signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        st.session_state.csrf_token = f"{payload}|{signature}"
    
    return st.session_state.csrf_token


def verify_csrf_token(token):
    """
    Verifica che un token CSRF sia valido.
    
    Args:
        token (str): Token CSRF da verificare
    
    Returns:
        bool: True se il token è valido, False altrimenti
    """
    if not token or '|' not in token:
        return False
    
    try:
        # Estrai parti del token
        payload, signature = token.rsplit('|', 1)
        
        # Verifica firma
        expected_signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False
        
        # Verifica scadenza
        token_id, expiry_timestamp = payload.split('|')
        expiry = datetime.fromtimestamp(float(expiry_timestamp))
        
        if datetime.now() > expiry:
            return False
        
        # Verifica contro replay attack
        if 'used_tokens' not in st.session_state:
            st.session_state.used_tokens = set()
        
        if token in st.session_state.used_tokens:
            return False
        
        # Segna token come usato
        st.session_state.used_tokens.add(token)
        return True
    
    except Exception as e:
        log_security_event(f"Errore verifica CSRF: {str(e)}")
        return False


def rate_limit_check(user_id=None, action="generic"):
    """
    Verifica che l'utente non superi il rate limit per prevenire DDoS.
    
    Args:
        user_id (str): ID dell'utente
        action (str): Tipo di azione
    
    Returns:
        bool: True se l'utente può procedere, False se ha superato il limite
    """
    # Identificatore utente (IP o ID)
    identifier = user_id or st.session_state.get("user_id", "anonymous")
    
    # Chiave univoca per questa azione
    rate_key = f"rate_limit_{identifier}_{action}"
    
    # Inizializza contatori se necessario
    if rate_key not in st.session_state:
        st.session_state[rate_key] = {"count": 0, "reset_time": time.time() + 60}
    
    # Verifica se è tempo di reset
    if time.time() > st.session_state[rate_key]["reset_time"]:
        st.session_state[rate_key] = {"count": 0, "reset_time": time.time() + 60}
    
    # Incrementa contatore
    st.session_state[rate_key]["count"] += 1
    
    # Verifica limite
    if st.session_state[rate_key]["count"] > MAX_REQUESTS_PER_MINUTE:
        log_security_event(f"Rate limit superato: {identifier}, azione: {action}")
        return False
    
    return True


def hash_password(password, salt=None):
    """
    Genera hash sicuro per password con salt.
    
    Args:
        password (str): Password da hashare
        salt (str): Salt opzionale
    
    Returns:
        tuple: (hash, salt)
    """
    if not salt:
        salt = os.urandom(32).hex()
    
    # Genera hash con PBKDF2 (SHA256)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # Numero iterazioni
    )
    
    return base64.b64encode(key).decode('utf-8'), salt


def verify_password(password, stored_hash, salt):
    """
    Verifica che una password corrisponda all'hash memorizzato.
    
    Args:
        password (str): Password da verificare
        stored_hash (str): Hash memorizzato
        salt (str): Salt utilizzato
    
    Returns:
        bool: True se la password è corretta
    """
    hash_to_check, _ = hash_password(password, salt)
    return hmac.compare_digest(hash_to_check, stored_hash)


def encrypt_data(data, key=None):
    """
    Cripta dati sensibili.
    Versione semplificata - in produzione usare librerie crittografiche standard.
    
    Args:
        data (str): Dati da criptare
        key (str): Chiave di criptaggio
    
    Returns:
        str: Dati criptati
    """
    if not key:
        key = SECRET_KEY
    
    # Implementazione di base per demo
    # In produzione utilizzare librerie come cryptography.fernet
    return base64.b64encode(
        hashlib.sha256(key.encode()).digest()[:16] + 
        data.encode('utf-8')
    ).decode('utf-8')


def decrypt_data(encrypted_data, key=None):
    """
    Decripta dati sensibili.
    Versione semplificata - in produzione usare librerie crittografiche standard.
    
    Args:
        encrypted_data (str): Dati criptati
        key (str): Chiave di criptaggio
    
    Returns:
        str: Dati decriptati
    """
    if not key:
        key = SECRET_KEY
    
    try:
        # Implementazione di base per demo
        data = base64.b64decode(encrypted_data.encode('utf-8'))
        return data[16:].decode('utf-8')
    except:
        return None


def log_security_event(message, severity="INFO"):
    """
    Registra eventi di sicurezza in un log.
    
    Args:
        message (str): Messaggio da loggare
        severity (str): Livello di gravità
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Crea cartella log se non esiste
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Path del file di log
    log_file = os.path.join(log_dir, "security.log")
    
    # Ottieni indirizzo IP o identificativo utente
    user_id = st.session_state.get("user_id", "unknown")
    
    # Scrivi nel file di log
    try:
        with open(log_file, "a") as f:
            f.write(f"{timestamp} [{severity}] - User: {user_id} - {message}\n")
    except Exception as e:
        # Fallback se non si può scrivere su file
        print(f"Errore scrittura log: {str(e)}")
        pass


def secure_headers():
    """
    Imposta header di sicurezza per la pagina web.
    Utilizzabile in HTML statico.
    
    Returns:
        str: Codice HTML con meta tag di sicurezza
    """
    return """
    <meta http-equiv="Content-Security-Policy" 
        content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; 
                 style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; 
                 img-src 'self' data: https:; 
                 connect-src 'self' https://*.streamlit.app;">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="SAMEORIGIN">
    <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
    <meta http-equiv="Permissions-Policy" content="geolocation=*, camera=(), microphone=()">
    """


def apply_security_headers():
    """
    Applica header di sicurezza alla pagina Streamlit.
    """
    st.markdown(secure_headers(), unsafe_allow_html=True)


def secure_database_query(query, params=None):
    """
    Esegue query database in modo sicuro con parametrizzazione.
    Questo è un modello di implementazione - l'implementazione effettiva
    dipenderà dalla libreria database utilizzata.
    
    Args:
        query (str): Query SQL parametrizzata
        params (tuple/dict): Parametri per la query
    
    Returns:
        risultato della query
    """
    # Esempio di implementazione
    # In un'applicazione reale, questo utilizzerebbe
    # la connessione al database effettiva
    
    # Verifica SQL injection nella query
    if not query or re.search(r';\s*--', query):
        log_security_event("Tentativo di SQL injection rilevato", "CRITICAL")
        return None
    
    # Verifica rate limit
    if not rate_limit_check(action="database_query"):
        return None
    
    # Preferire sempre parametrizzazione invece di concatenamento
    # return db_connection.execute(query, params)
    
    # Placeholder per dimostrazione
    return {"success": True, "message": "Query eseguita con parametrizzazione"}


def export_to_static_html():
    """
    Prepara l'applicazione per l'esportazione in HTML statico.
    Aggiunge misure di sicurezza appropriate per siti statici.
    
    Returns:
        str: HTML con misure di sicurezza
    """
    html_template = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SismaVer2 - Monitoraggio Rischi Ambientali</title>
        {secure_headers()}
        <link rel="stylesheet" href="styles.css">
        <!-- Subresource Integrity per i file esterni -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js" 
                integrity="sha384-+QBLMBjBW/SnpXBw+jhJ4+uYqJSoYSQnxdmqq8E7US9JZOmRJkIZ9zWwKrVf54K0"
                crossorigin="anonymous"></script>
    </head>
    <body>
        <header>
            <!-- Header content -->
        </header>
        
        <main>
            <!-- Main content - populated by separate script -->
            <div id="app-content"></div>
        </main>
        
        <footer>
            <!-- Footer content -->
        </footer>
        
        <!-- Script con Subresource Integrity -->
        <script src="app.js" integrity="sha384-[HASH_PLACEHOLDER]" crossorigin="anonymous"></script>
        
        <!-- Script di protezione XSS -->
        <script>
            // Sanitizzazione input
            function sanitizeInput(text) {{
                return text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            }}
            
            // CSRF token per le form
            const csrfToken = '{generate_csrf_token()}';
            
            // Aggiunge token a tutte le form
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
    </body>
    </html>
    """
    
    return html_template


# Utility per validazione input
def validate_coordinates(lat, lon):
    """
    Valida che le coordinate siano nel formato corretto.
    
    Args:
        lat (float): Latitudine
        lon (float): Longitudine
    
    Returns:
        bool: True se le coordinate sono valide
    """
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        # Verifica range coordinate
        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
            return True
        return False
    except:
        return False


def validate_email(email):
    """
    Valida che una email sia nel formato corretto.
    
    Args:
        email (str): Email da validare
    
    Returns:
        bool: True se l'email è valida
    """
    if not email or not isinstance(email, str):
        return False
    
    # Pattern semplificato per email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone):
    """
    Valida che un numero di telefono sia nel formato corretto.
    
    Args:
        phone (str): Numero di telefono da validare
    
    Returns:
        bool: True se il numero è valido
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Rimuovi spazi e caratteri non numerici
    phone_clean = re.sub(r'\D', '', phone)
    
    # Verifica lunghezza (numeri italiani)
    return 8 <= len(phone_clean) <= 13


def secure_file_upload(uploaded_file):
    """
    Gestisce l'upload di file in modo sicuro.
    
    Args:
        uploaded_file: File caricato con st.file_uploader
    
    Returns:
        tuple: (is_safe, file_path o error_message)
    """
    if not uploaded_file:
        return False, "Nessun file caricato"
    
    # Verifica estensione
    file_name = uploaded_file.name
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.csv']
    
    if not any(file_name.lower().endswith(ext) for ext in allowed_extensions):
        return False, "Tipo di file non consentito"
    
    # Verifica dimensione (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size > max_size:
        return False, "File troppo grande (max 5MB)"
    
    try:
        # Genera nome file sicuro
        secure_filename = hashlib.md5(
            (file_name + str(time.time())).encode()
        ).hexdigest() + os.path.splitext(file_name)[1]
        
        # Percorso di salvataggio
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, secure_filename)
        
        # Salva il file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Registra l'evento
        log_security_event(f"File caricato: {secure_filename} (originale: {file_name})")
        
        return True, file_path
    
    except Exception as e:
        log_security_event(f"Errore upload file: {str(e)}", "ERROR")
        return False, f"Errore durante l'upload: {str(e)}"