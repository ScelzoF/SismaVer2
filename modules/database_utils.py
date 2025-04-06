"""
Utility per operazioni sicure su database in SismaVer2.
Implementa protezioni contro SQL injection e altre vulnerabilità.
"""
import os
import re
import time
import json
import hashlib
import streamlit as st
from datetime import datetime, timedelta
import traceback

# Import del modulo di sicurezza
from modules.security import sanitize_input, sanitize_sql, log_security_event

# Determina se usare Supabase o SQLite in base alla configurazione
try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        USE_SUPABASE = True
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        USE_SUPABASE = False
except (ImportError, Exception):
    USE_SUPABASE = False

# Fallback a SQLite se Supabase non è disponibile
if not USE_SUPABASE:
    try:
        import sqlite3
        # Crea directory per database
        os.makedirs("data", exist_ok=True)
        # Percorso del database SQLite
        SQLITE_DB_PATH = "data/sisma_ver2.db"
    except ImportError:
        # Fallback a file JSON se SQLite non è disponibile
        os.makedirs("data", exist_ok=True)
        

# Cache di query per limitare attacchi DoS
query_cache = {}
# Limite richieste per minuto per utente
RATE_LIMIT = 60
# Timestamp delle richieste per utente
request_timestamps = {}
# Liste nere IP
blacklisted_ips = set()


def init_database():
    """
    Inizializza la connessione al database e le tabelle necessarie.
    
    Returns:
        bool: True se inizializzato con successo
    """
    if USE_SUPABASE:
        return True
    else:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            
            # Crea tabelle (SQLite)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                message TEXT NOT NULL,
                regione TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                is_emergency BOOLEAN DEFAULT 0,
                is_moderated BOOLEAN DEFAULT 0,
                moderation_level TEXT,
                moderation_score REAL,
                original_message TEXT,
                lat REAL,
                lon REAL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                descrizione TEXT NOT NULL,
                data TEXT NOT NULL,
                ora TEXT NOT NULL,
                regione TEXT,
                comune TEXT,
                gravita TEXT,
                contatto TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                is_moderated BOOLEAN DEFAULT 0,
                moderation_level TEXT,
                moderation_score REAL,
                lat REAL,
                lon REAL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                gravity INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                ip_address TEXT,
                user_id TEXT,
                details TEXT,
                severity TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore inizializzazione database: {str(e)}")
            return False


def rate_limit_check(user_id, action_type="query"):
    """
    Verifica se l'utente ha superato il rate limit.
    
    Args:
        user_id (str): ID dell'utente
        action_type (str): Tipo di azione
    
    Returns:
        bool: True se può procedere, False se ha superato il limite
    """
    # Genera chiave univoca per utente e azione
    key = f"{user_id}_{action_type}"
    
    # Ottieni timestamp corrente
    current_time = time.time()
    
    # Inizializza se non esiste
    if key not in request_timestamps:
        request_timestamps[key] = []
    
    # Filtra le richieste negli ultimi 60 secondi
    request_timestamps[key] = [ts for ts in request_timestamps[key] if current_time - ts <= 60]
    
    # Verifica il numero di richieste
    if len(request_timestamps[key]) >= RATE_LIMIT:
        # Registra tentativo di DoS
        log_security_event(f"Rate limit superato per {user_id}", "WARNING")
        
        # Aggiungi alla lista nera se supera 2x il limite
        if len(request_timestamps[key]) >= RATE_LIMIT * 2:
            blacklisted_ips.add(user_id)
            log_security_event(f"IP aggiunto alla lista nera: {user_id}", "CRITICAL")
        
        return False
    
    # Aggiungi la richiesta corrente
    request_timestamps[key].append(current_time)
    
    return True


def is_blacklisted(user_id):
    """
    Verifica se un utente è nella lista nera.
    
    Args:
        user_id (str): ID dell'utente
    
    Returns:
        bool: True se è nella lista nera
    """
    return user_id in blacklisted_ips


def execute_query(query, params=None, cache_ttl=0, user_id=None):
    """
    Esegue una query SQL in modo sicuro, con protezione da SQL injection.
    
    Args:
        query (str): Query SQL parametrizzata
        params (tuple/dict): Parametri per la query
        cache_ttl (int): Tempo di cache in secondi (0 = no cache)
        user_id (str): ID dell'utente
    
    Returns:
        dict/list: Risultato della query
    """
    # Sanitizza la query
    if query:
        # Verifica presenza di commenti/procedure dannose
        if re.search(r';\s*--', query) or re.search(r'EXEC\s+', query, re.IGNORECASE):
            log_security_event(f"Tentativo di SQL injection: {query}", "CRITICAL")
            return {"error": "Query non autorizzata"}
    
    # Verifica lista nera
    if user_id and is_blacklisted(user_id):
        log_security_event(f"Tentativo di accesso da IP in lista nera: {user_id}", "WARNING")
        return {"error": "Accesso non autorizzato"}
    
    # Verifica rate limit
    if user_id and not rate_limit_check(user_id):
        return {"error": "Troppe richieste. Riprova più tardi."}
    
    # Genera chiave cache
    cache_key = None
    if cache_ttl > 0:
        param_str = json.dumps(params) if params else ""
        cache_key = hashlib.md5(f"{query}_{param_str}".encode()).hexdigest()
        
        # Controlla cache
        if cache_key in query_cache:
            cache_time, cache_result = query_cache[cache_key]
            if time.time() - cache_time < cache_ttl:
                return cache_result
    
    # Esegui query
    try:
        if USE_SUPABASE:
            # Esecuzione con Supabase
            if query.lower().startswith("select"):
                # Query di selezione
                if "chat_messages" in query.lower():
                    response = supabase.table("chat_messages").select("*").execute()
                elif "event_reports" in query.lower():
                    response = supabase.table("event_reports").select("*").execute()
                elif "user_actions" in query.lower():
                    response = supabase.table("user_actions").select("*").execute()
                else:
                    return {"error": "Tabella non supportata"}
                
                if hasattr(response, 'data'):
                    result = response.data
                else:
                    result = []
            
            elif query.lower().startswith("insert"):
                # Query di inserimento
                if "chat_messages" in query.lower():
                    response = supabase.table("chat_messages").insert(params).execute()
                elif "event_reports" in query.lower():
                    response = supabase.table("event_reports").insert(params).execute()
                elif "user_actions" in query.lower():
                    response = supabase.table("user_actions").insert(params).execute()
                else:
                    return {"error": "Tabella non supportata"}
                
                if hasattr(response, 'data'):
                    result = response.data
                else:
                    result = {"success": True}
            
            else:
                # Altri tipi di query non supportati
                log_security_event(f"Tipo di query non supportato: {query}", "WARNING")
                return {"error": "Tipo di query non supportato"}
        
        else:
            # Esecuzione con SQLite
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.lower().startswith("select"):
                # Query di selezione
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            else:
                # Query di modifica
                conn.commit()
                result = {"success": True, "affected_rows": cursor.rowcount}
            
            conn.close()
        
        # Aggiorna cache
        if cache_key is not None:
            query_cache[cache_key] = (time.time(), result)
        
        return result
    
    except Exception as e:
        # Log dettagliato per debugging
        error_msg = f"Errore nell'esecuzione della query: {str(e)}"
        stack_trace = traceback.format_exc()
        log_security_event(f"{error_msg}\nQuery: {query}\nParams: {params}\n{stack_trace}", "ERROR")
        
        return {"error": error_msg}


def save_message(message_data, user_id=None):
    """
    Salva un messaggio nel database in modo sicuro.
    
    Args:
        message_data (dict): Dati del messaggio
        user_id (str): ID dell'utente
    
    Returns:
        dict: Risultato dell'operazione
    """
    # Sanitizza tutti i dati in input
    sanitized_data = {}
    for key, value in message_data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_input(value)
        else:
            sanitized_data[key] = value
    
    # Aggiungi timestamp
    if "timestamp" not in sanitized_data:
        sanitized_data["timestamp"] = datetime.now().isoformat()
    
    # Aggiungi user_id
    if user_id and "user_id" not in sanitized_data:
        sanitized_data["user_id"] = user_id
    
    if USE_SUPABASE:
        try:
            # Inserisci in Supabase
            response = supabase.table("chat_messages").insert(sanitized_data).execute()
            if hasattr(response, 'error') and response.error:
                return {"error": f"Errore nell'invio: {response.error}"}
            else:
                return {"success": True, "message": "Messaggio inviato!"}
        except Exception as e:
            error_msg = f"Errore nel salvataggio del messaggio: {str(e)}"
            log_security_event(error_msg, "ERROR")
            return {"error": error_msg}
    
    else:
        # Costruisci query parametrizzata per SQLite
        columns = ", ".join(sanitized_data.keys())
        placeholders = ", ".join(["?" for _ in sanitized_data])
        
        query = f"INSERT INTO chat_messages ({columns}) VALUES ({placeholders})"
        params = tuple(sanitized_data.values())
        
        return execute_query(query, params, user_id=user_id)


def save_event_report(report_data, user_id=None):
    """
    Salva una segnalazione evento nel database in modo sicuro.
    
    Args:
        report_data (dict): Dati della segnalazione
        user_id (str): ID dell'utente
    
    Returns:
        dict: Risultato dell'operazione
    """
    # Sanitizza tutti i dati in input
    sanitized_data = {}
    for key, value in report_data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_input(value)
        else:
            sanitized_data[key] = value
    
    # Aggiungi timestamp
    if "timestamp" not in sanitized_data:
        sanitized_data["timestamp"] = datetime.now().isoformat()
    
    # Aggiungi user_id
    if user_id and "user_id" not in sanitized_data:
        sanitized_data["user_id"] = user_id
    
    if USE_SUPABASE:
        try:
            # Inserisci in Supabase
            response = supabase.table("event_reports").insert(sanitized_data).execute()
            if hasattr(response, 'error') and response.error:
                return {"error": f"Errore nell'invio: {response.error}"}
            else:
                return {"success": True, "message": "Segnalazione inviata!"}
        except Exception as e:
            error_msg = f"Errore nel salvataggio della segnalazione: {str(e)}"
            log_security_event(error_msg, "ERROR")
            return {"error": error_msg}
    
    else:
        # Costruisci query parametrizzata per SQLite
        columns = ", ".join(sanitized_data.keys())
        placeholders = ", ".join(["?" for _ in sanitized_data])
        
        query = f"INSERT INTO event_reports ({columns}) VALUES ({placeholders})"
        params = tuple(sanitized_data.values())
        
        return execute_query(query, params, user_id=user_id)


def track_user_action(user_id, action_type, action_details=None, gravity=0):
    """
    Registra un'azione utente per tracciamento comportamentale.
    
    Args:
        user_id (str): ID dell'utente
        action_type (str): Tipo di azione
        action_details (str): Dettagli dell'azione
        gravity (int): Gravità dell'azione (0-10)
    
    Returns:
        dict: Risultato dell'operazione
    """
    if not user_id:
        return {"error": "User ID è richiesto"}
    
    # Sanitizza input
    action_type = sanitize_input(action_type)
    if action_details:
        action_details = sanitize_input(action_details)
    
    # Valida gravità
    gravity = min(max(int(gravity), 0), 10)
    
    data = {
        "user_id": user_id,
        "action_type": action_type,
        "action_details": action_details,
        "gravity": gravity,
        "timestamp": datetime.now().isoformat()
    }
    
    if USE_SUPABASE:
        try:
            # Inserisci in Supabase
            response = supabase.table("user_actions").insert(data).execute()
            return {"success": True}
        except Exception as e:
            error_msg = f"Errore nel tracciamento azione: {str(e)}"
            log_security_event(error_msg, "ERROR")
            return {"error": error_msg}
    
    else:
        # Costruisci query parametrizzata per SQLite
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        
        query = f"INSERT INTO user_actions ({columns}) VALUES ({placeholders})"
        params = tuple(data.values())
        
        return execute_query(query, params)


def get_user_actions_count(user_id, action_type=None, hours=24):
    """
    Recupera il conteggio delle azioni di un utente nelle ultime ore.
    
    Args:
        user_id (str): ID dell'utente
        action_type (str): Tipo di azione da filtrare
        hours (int): Ore precedenti da considerare
    
    Returns:
        int: Numero di azioni
    """
    if not user_id:
        return 0
    
    # Calcola timestamp da cui iniziare
    start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    if USE_SUPABASE:
        try:
            # Query Supabase
            query = supabase.table("user_actions").select("id").eq("user_id", user_id).gte("timestamp", start_time)
            
            if action_type:
                query = query.eq("action_type", action_type)
            
            response = query.execute()
            
            if hasattr(response, 'data'):
                return len(response.data)
            else:
                return 0
                
        except Exception as e:
            log_security_event(f"Errore nel recupero azioni utente: {str(e)}", "ERROR")
            return 0
    
    else:
        # Query SQLite
        query = "SELECT COUNT(*) as count FROM user_actions WHERE user_id = ? AND timestamp >= ?"
        params = [user_id, start_time]
        
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
        
        except Exception as e:
            log_security_event(f"Errore nel recupero azioni utente: {str(e)}", "ERROR")
            return 0


def get_user_gravity_sum(user_id, hours=24):
    """
    Calcola la somma della gravità delle azioni di un utente nelle ultime ore.
    
    Args:
        user_id (str): ID dell'utente
        hours (int): Ore precedenti da considerare
    
    Returns:
        int: Somma della gravità
    """
    if not user_id:
        return 0
    
    # Calcola timestamp da cui iniziare
    start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    if USE_SUPABASE:
        try:
            # Query su Supabase
            # Nota: Supabase non supporta SUM direttamente, dobbiamo recuperare tutti i dati
            response = supabase.table("user_actions").select("gravity").eq("user_id", user_id).gte("timestamp", start_time).execute()
            
            if hasattr(response, 'data'):
                return sum(item.get("gravity", 0) for item in response.data)
            else:
                return 0
                
        except Exception as e:
            log_security_event(f"Errore nel calcolo gravità utente: {str(e)}", "ERROR")
            return 0
    
    else:
        # Query SQLite
        query = "SELECT SUM(gravity) as total FROM user_actions WHERE user_id = ? AND timestamp >= ?"
        params = [user_id, start_time]
        
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else 0
        
        except Exception as e:
            log_security_event(f"Errore nel calcolo gravità utente: {str(e)}", "ERROR")
            return 0


def get_user_restriction_level(user_id):
    """
    Determina il livello di restrizione per un utente in base al suo comportamento.
    
    Args:
        user_id (str): ID dell'utente
    
    Returns:
        tuple: (level, reason)
            level: 0=nessuno, 1=avviso, 2=limitato, 3=sospeso
            reason: motivo della restrizione
    """
    if not user_id:
        return 0, ""
    
    # Recupera metriche utente
    actions_24h = get_user_actions_count(user_id, hours=24)
    gravity_sum_24h = get_user_gravity_sum(user_id, hours=24)
    
    # Recupera azioni specifiche
    spam_actions = get_user_actions_count(user_id, action_type="spam", hours=24)
    inappropriate_actions = get_user_actions_count(user_id, action_type="messaggio_inappropriato", hours=24)
    blocked_actions = get_user_actions_count(user_id, action_type="messaggio_bloccato", hours=48)
    
    # Verifica lista nera
    if is_blacklisted(user_id):
        return 3, "Il tuo account è stato temporaneamente sospeso a causa di attività sospette."
    
    # Logica di decisione
    if blocked_actions >= 3:
        return 3, "Il tuo account è stato temporaneamente sospeso a causa di ripetute violazioni delle linee guida."
    
    if gravity_sum_24h >= 30 or inappropriate_actions >= 5:
        return 2, "Hai raggiunto il limite di azioni permesse. Riprova tra qualche ora."
    
    if gravity_sum_24h >= 15 or spam_actions >= 3:
        return 1, "Attenzione: alcuni tuoi contenuti recenti potrebbero violare le linee guida della community."
    
    # Nessuna restrizione
    return 0, ""


def clear_old_cache():
    """
    Pulisce la cache vecchia per evitare memory leak.
    """
    global query_cache
    
    # Mantieni solo cache degli ultimi 5 minuti
    current_time = time.time()
    query_cache = {k: v for k, v in query_cache.items() if current_time - v[0] < 300}


# Inizializza il database all'importazione del modulo
init_database()