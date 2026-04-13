"""
Modulo per la protezione da attacchi CSRF (Cross-Site Request Forgery) in SismaVer2.
Implementa un sistema di token per garantire che le richieste provengano solo da pagine legittime.
"""
import os
import time
import hmac
import uuid
import base64
import hashlib
import streamlit as st
from datetime import datetime, timedelta

# Chiave segreta per firmare i token (in produzione usare variabile d'ambiente)
try:
    SECRET_KEY = os.environ.get("CSRF_SECRET_KEY", str(uuid.uuid4()))
except:
    SECRET_KEY = "sisma_ver2_csrf_protection_key"  # Solo per fallback

# Tempo di validità del token in minuti
TOKEN_EXPIRY_MINUTES = 60

# Dimensione massima del pool di token usati (per prevenire memory leak)
MAX_USED_TOKENS = 1000

# Inizializzazione
if "csrf_tokens" not in st.session_state:
    st.session_state.csrf_tokens = {}
if "used_tokens" not in st.session_state:
    st.session_state.used_tokens = set()


def generate_csrf_token(action=None, user_id=None):
    """
    Genera un token CSRF (Cross-Site Request Forgery) per proteggere le form.
    
    Args:
        action (str): Azione specifica per cui il token è valido
        user_id (str): ID dell'utente per cui il token è valido
    
    Returns:
        str: Token CSRF
    """
    # Genera un ID univoco per il token
    token_id = str(uuid.uuid4())
    
    # Timestamp di scadenza
    expiry = datetime.now() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    expiry_timestamp = int(expiry.timestamp())
    
    # Costruisci payload
    payload = {
        "token_id": token_id,
        "expiry": expiry_timestamp,
        "action": action,
        "user_id": user_id
    }
    
    # Converti in stringa
    payload_str = f"{token_id}|{expiry_timestamp}"
    if action:
        payload_str += f"|{action}"
    if user_id:
        payload_str += f"|{user_id}"
    
    # Genera firma HMAC
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Token completo
    token = f"{payload_str}|{signature}"
    
    # Memorizza nella session state
    st.session_state.csrf_tokens[token_id] = {
        "token": token,
        "expiry": expiry_timestamp,
        "action": action,
        "user_id": user_id,
        "created": int(time.time())
    }
    
    return token


def verify_csrf_token(token, expected_action=None, expected_user_id=None):
    """
    Verifica che un token CSRF sia valido.
    
    Args:
        token (str): Token CSRF da verificare
        expected_action (str): Azione attesa per cui il token dovrebbe essere valido
        expected_user_id (str): ID utente atteso per cui il token dovrebbe essere valido
    
    Returns:
        bool: True se il token è valido, False altrimenti
    """
    if not token or "|" not in token:
        return False
    
    try:
        # Estrai parti del token
        parts = token.split("|")
        
        # Controlla numero minimo di parti
        if len(parts) < 3:
            return False
        
        # Estrai signature
        signature = parts[-1]
        payload_str = "|".join(parts[:-1])
        
        # Calcola firma attesa
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verifica firma (confronto sicuro)
        if not hmac.compare_digest(signature, expected_signature):
            return False
        
        # Estrai token_id e scadenza
        token_id = parts[0]
        expiry_timestamp = int(parts[1])
        
        # Verifica scadenza
        if time.time() > expiry_timestamp:
            return False
        
        # Estrai action e user_id se presenti
        action = parts[2] if len(parts) > 3 else None
        user_id = parts[3] if len(parts) > 4 else None
        
        # Verifica action se richiesto
        if expected_action and action != expected_action:
            return False
        
        # Verifica user_id se richiesto
        if expected_user_id and user_id != expected_user_id:
            return False
        
        # Verifica uso precedente (per prevenire replay attack)
        if token in st.session_state.used_tokens:
            return False
        
        # Marca token come usato
        st.session_state.used_tokens.add(token)
        
        # Limita la dimensione del pool di token usati
        if len(st.session_state.used_tokens) > MAX_USED_TOKENS:
            # Rimuovi token più vecchi
            st.session_state.used_tokens = set(list(st.session_state.used_tokens)[-MAX_USED_TOKENS:])
        
        return True
    
    except Exception as e:
        print(f"Errore nella verifica del token CSRF: {str(e)}")
        return False


def csrf_protect(func):
    """
    Decoratore per proteggere le funzioni da CSRF.
    
    Args:
        func: Funzione da proteggere
    
    Returns:
        Funzione decorata
    """
    def wrapper(*args, **kwargs):
        # Verifica se siamo in una richiesta POST
        if st.session_state.get("_is_form_submit", False):
            # Estrai token dalla form
            token = st.session_state.get("csrf_token")
            
            # Verifica token
            if not token or not verify_csrf_token(token):
                st.error("⚠️ Errore di sicurezza: token CSRF non valido.")
                return None
        
        # Esegui la funzione originale
        return func(*args, **kwargs)
    
    return wrapper


def add_csrf_token_to_form():
    """
    Aggiunge un campo nascosto con token CSRF nella form corrente.
    Da chiamare all'interno di un contesto st.form.
    
    Returns:
        str: Token CSRF generato
    """
    token = generate_csrf_token()
    
    # Memorizza nel session state
    st.session_state["csrf_token"] = token
    
    # Indicatore per csrf_protect
    st.session_state["_is_form_submit"] = True
    
    return token


def csrf_input():
    """
    Genera un campo input nascosto con token CSRF.
    Da usare in HTML personalizzato.
    
    Returns:
        str: HTML per il campo nascosto
    """
    token = generate_csrf_token()
    
    return f'<input type="hidden" name="csrf_token" value="{token}">'


def cleanup_expired_tokens():
    """
    Rimuove token scaduti dalla session state.
    """
    current_time = int(time.time())
    
    # Verifica che csrf_tokens sia inizializzato
    if "csrf_tokens" not in st.session_state:
        st.session_state.csrf_tokens = {}
        return
        
    # Filtra token non scaduti
    st.session_state.csrf_tokens = {
        token_id: token_data
        for token_id, token_data in st.session_state.csrf_tokens.items()
        if token_data["expiry"] > current_time
    }


# Chiama cleanup all'importazione del modulo se streamlit è già avviato
try:
    if "session_state" in st.__dict__:
        cleanup_expired_tokens()
except:
    pass  # Ignorato durante import iniziale