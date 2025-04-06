"""
Utility per la moderazione dei contenuti in SismaVer2.
Implementa un sistema completo di moderazione multi-livello:
1. Moderazione basata su regole (pattern regex)
2. Analisi comportamentale degli utenti
3. Moderazione AI (OpenAI o Anthropic)
4. Protezione anti-spam e anti-flood
5. Rilevamento contenuti sensibili specifici per emergenze
"""
import re
import json
import time
import os
import hashlib
import uuid
import streamlit as st
import logging
from datetime import datetime, timedelta

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/moderation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("moderazione")

# Assicurati che la cartella logs esista
os.makedirs("logs", exist_ok=True)

# Dizionari per moderazione basata su regole
PAROLE_INAPPROPRIATE = {
    "leggero": [
        # Lista di parole estremamente volgari o offensive (caso leggero)
        r'\b(cazzo|culo|stronz[oi]|merd[ae]|vaffanculo|puttana)\b'
    ],
    "standard": [
        # Lista standard che include anche termini moderatamente inappropriati
        r'\b(cazzo|culo|stronz[oi]|merd[ae]|vaffanculo|puttana|fanculo|troia|porca|fottut[oi]|minchia|coglion[ei])\b',
        r'\b(idiota|deficiente|imbecille|scemo)\b'
    ],
    "severo": [
        # Lista completa che include anche termini leggermente inappropriati
        r'\b(cazzo|culo|stronz[oi]|merd[ae]|vaffanculo|puttana|fanculo|troia|porca|fottut[oi]|minchia|coglion[ei])\b',
        r'\b(idiota|deficiente|imbecille|scemo|stupido|maledett[oi]|dannato|boia|accidenti|diavolo|dannazione)\b',
        r'\b(odio|ammazzare|uccidere|ammazzati|ucciditi|morte|suicidati|violenza|terrorismo)\b'
    ]
}

# Contenuti sensibili o potenzialmente problematici
CONTENUTI_SENSIBILI = {
    "leggero": [
        # Solo contenuti estremamente sensibili 
        r'\b(terrorismo|bomba|attentato|strage)\b'
    ],
    "standard": [
        # Contenuti moderatamente sensibili
        r'\b(terrorismo|bomba|attentato|strage|violenza|minaccia|minaccie|intimidazione)\b',
        r'\b(fai da te|crea|costruire) +.{0,20}?(bomba|esplosivo|arma)\b'
    ],
    "severo": [
        # Praticamente qualsiasi contenuto minimamente problematico
        r'\b(terrorismo|bomba|attentato|strage|violenza|minaccia|minaccie|intimidazione)\b',
        r'\b(fai da te|crea|costruire) +.{0,20}?(bomba|esplosivo|arma)\b',
        r'\b(morte|uccidere|ammazzare|suicidio|suicidarsi|morire)\b',
        r'\b(politica|governo|ministro|partito|premier|destra|sinistra|centro)\b',
        r'\b(protesta|manifestazione|corteo|rivolta|sciopero)\b',
        r'\b(incitamento|istigazione|odio|discriminazione)\b',
        r'\b(farmaco|medicinale|cura|trattamento|terapia)\b',
    ]
}

# Pattern di spam tipici da bloccare
PATTERN_SPAM = [
    r'https?://(?!(?:www\.)?(?:ingv\.it|terremoti\.it|protezionecivilecampania\.it|iononrischio\.it))[\w\.-]+\.[a-zA-Z]{2,}',  # URL eccetto fonti ufficiali
    r'(?:viagra|cialis|levitra|farmaci|drugs|pills|[cC]asino|[bB]et|[gG]ambling|[pP]oker)',  # Spam farmaci/gioco d'azzardo
    r'(?:\+\d{8,}|\d{3,}[-.]\d{3,}[-.]\d{3,})',  # Numeri di telefono
    r'[^\s]+@[^\s]+\.[^\s]+',  # Email
    r'(.)\\1{4,}',  # Caratteri ripetuti eccessivamente
]

# Nuova categoria: rilevamento informazioni false o allarmistiche su emergenze
INFO_FALSE_EMERGENZE = [
    r'\b(terremoto|sisma|scossa).{0,30}(magnitud[eo]|scala.{0,5}richter).{0,10}([5-9]|1\d)\b',  # Terremoti di magnitudine eccessiva
    r'\b(eruzione|eruttato|lava).{0,30}(vesuvio|campi.flegrei|etna).{0,30}(imminente|nelle.prossime.ore)\b',  # Previsioni eruttive false
    r'\b(allerta|allarme|emergenza)\s+(rossa|livello\s+\d)\b.{0,50}\b(evacua|evacuer|scappa|abbandonare|lasciare)\b',  # False evacuazioni
    r'\b(confermato|ufficiale|ministero|governo|protezione\s+civile).{0,50}(evacuazione|allerta\s+rossa|emergenza\s+nazionale)\b',  # False dichiarazioni ufficiali
]

def check_spam_patterns(testo):
    """
    Verifica se il testo contiene pattern tipici di spam o scam.
    
    Args:
        testo (str): Il testo da analizzare
        
    Returns:
        tuple: (è_spam, motivo)
    """
    if not testo:
        return False, ""
    
    # Controlla pattern di spam
    for pattern in PATTERN_SPAM:
        match = re.search(pattern, testo, re.IGNORECASE)
        if match:
            return True, f"Rilevato pattern di spam: {match.group(0)}"
    
    # Controlla eccesso di maiuscole (possibile URLO o spam)
    if len(testo) > 15:
        uppercase_ratio = sum(1 for c in testo if c.isupper()) / len([c for c in testo if c.isalpha()])
        if uppercase_ratio > 0.7:  # Più del 70% in maiuscolo
            return True, "Eccesso di testo in maiuscolo"
    
    # Controlla ripetizioni eccessive dello stesso messaggio
    if len(testo) > 20:
        words = testo.split()
        if len(words) > 5:
            # Controlla ripetizioni di frasi
            for i in range(len(words) - 4):
                phrase = ' '.join(words[i:i+4])
                count = testo.lower().count(phrase.lower())
                if count > 2 and len(phrase) > 10:
                    return True, f"Ripetizione eccessiva: '{phrase}'"
    
    return False, ""

def check_false_emergency_info(testo):
    """
    Verifica se il testo contiene informazioni false o allarmistiche su emergenze.
    
    Args:
        testo (str): Il testo da analizzare
        
    Returns:
        tuple: (contiene_info_false, motivo)
    """
    if not testo:
        return False, ""
    
    # Controlla pattern di false emergenze
    for pattern in INFO_FALSE_EMERGENZE:
        match = re.search(pattern, testo, re.IGNORECASE)
        if match:
            return True, f"Possibile disinformazione su emergenze: {match.group(0)}"
    
    return False, ""

def filtra_contenuto_vietato(testo, livello="standard"):
    """
    Filtra contenuti vietati in base al livello di moderazione specificato.
    Sistema multi-livello migliorato che include:
    - Controllo linguaggio inappropriato
    - Controllo argomenti sensibili
    - Rilevamento spam e scam
    - Rilevamento disinformazione su emergenze
    
    Args:
        testo (str): Il testo da moderare
        livello (str): Livello di moderazione ('leggero', 'standard', 'severo')
    
    Returns:
        tuple: (testo_moderato, contiene_contenuto_vietato, ragione)
    """
    if not testo:
        return "", False, ""
    
    # Controlla limite lunghezza testo (max 2000 caratteri)
    if len(testo) > 2000:
        testo = testo[:1997] + "..."
        return testo, False, "Messaggio troppo lungo, è stato troncato"

    # Usa livello di moderazione corretto
    if livello not in ["leggero", "standard", "severo"]:
        livello = "standard"  # Default
    
    # Log dell'attività di moderazione
    logger.info(f"Moderazione testo ({livello}): {testo[:50]}...")
    
    # Controllo spam (prioritario)
    is_spam, spam_reason = check_spam_patterns(testo)
    if is_spam:
        logger.warning(f"Rilevato SPAM: {spam_reason} nel testo: {testo[:100]}")
        # In ogni livello di moderazione, blocca completamente lo spam
        return "", True, f"Contenuto bloccato: {spam_reason}"
    
    # Controllo disinformazione emergenza (sempre bloccata a prescindere dal livello)
    is_false_info, false_info_reason = check_false_emergency_info(testo)
    if is_false_info:
        logger.warning(f"Rilevata disinformazione emergenza: {false_info_reason} nel testo: {testo[:100]}")
        return "", True, f"Contenuto bloccato: {false_info_reason}"
    
    # Controllo parole inappropriate
    for pattern in PAROLE_INAPPROPRIATE.get(livello, []):
        if re.search(pattern, testo, re.IGNORECASE):
            # Se livello severo, blocca completamente
            if livello == "severo":
                logger.info(f"Bloccato per linguaggio inappropriato (livello severo): {testo[:100]}")
                return "", True, "Il messaggio contiene linguaggio inappropriato"
            
            # Altrimenti, sostituisci con asterischi
            testo_originale = testo
            testo = re.sub(pattern, 
                           lambda m: '*' * len(m.group(0)), 
                           testo, 
                           flags=re.IGNORECASE)
            
            if testo != testo_originale:
                logger.info(f"Applicata moderazione linguaggio: {testo_originale[:50]} -> {testo[:50]}")
    
    # Controllo contenuti sensibili
    for pattern in CONTENUTI_SENSIBILI.get(livello, []):
        if re.search(pattern, testo, re.IGNORECASE):
            # Se livello severo, blocca completamente
            if livello == "severo":
                logger.info(f"Bloccato per contenuto sensibile (livello severo): {testo[:100]}")
                return "", True, "Il messaggio contiene argomenti sensibili o inappropriati"
            
            # Per altri livelli, lascia passare ma segnala
            logger.info(f"Rilevato contenuto sensibile (livello {livello}): {testo[:100]}")
            return testo, True, "Il messaggio contiene argomenti sensibili"
    
    # Se arriviamo qui, nessuna regola è stata violata
    return testo, False, ""

def modera_con_ai(testo, user_id=None, use_cache=True):
    """
    Moderazione avanzata del testo usando AI (OpenAI o Anthropic).
    Funziona solo se l'API key è configurata.
    
    Args:
        testo (str): Il testo da moderare
        user_id (str): ID utente per cacheare risultati
        use_cache (bool): Se usare cache per risparmiare API calls
    
    Returns:
        tuple: (è_appropriato, punteggio_sicurezza, categoria_violazione, testo_moderato)
    """
    if not testo:
        return True, 0.0, "", ""
    
    # Tronca input se troppo lungo
    testo_originale = testo
    if len(testo) > 1000:
        testo = testo[:997] + "..."
    
    # Path per cache di moderazione
    cache_dir = "data/moderation_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Crea hash unico per questo contenuto
    content_hash = hashlib.md5(testo.encode()).hexdigest()
    cache_file = f"{cache_dir}/{content_hash}.json"
    
    # Controlla cache se abilitata
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                
                # Verifica validità (max 1 giorno)
                cache_time = cache_data.get("timestamp", 0)
                if time.time() - cache_time < 86400:
                    return (
                        cache_data.get("is_appropriate", True),
                        cache_data.get("score", 0.0),
                        cache_data.get("category", ""),
                        cache_data.get("moderated_text", testo_originale)
                    )
        except:
            # In caso di errore nella cache, prosegui normalmente
            pass
    
    # Prova prima con OpenAI
    try:
        import openai
        from openai import OpenAI
        
        # Verifica disponibilità delle API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # Prova a prendere dalle secrets di Streamlit
            try:
                api_key = st.secrets["OPENAI_API_KEY"]
            except:
                pass
        
        if not api_key:
            # Nessuna API key, ritorna risultato base
            return True, 0.0, "", testo_originale
        
        # Inizializza client
        client = OpenAI(api_key=api_key)
        
        # Prima usa l'API di moderazione che è più economica
        response = client.moderations.create(input=testo)
        
        if response.results and response.results[0].flagged:
            # Se flaggato, estraiamo i dettagli
            categories = response.results[0].categories
            scores = response.results[0].category_scores
            
            # Trova la categoria con score più alto
            max_category = max(scores.model_dump().items(), key=lambda x: x[1])
            category_name = max_category[0]
            category_score = max_category[1]
            
            # Verifica se è appropriato in base al punteggio
            is_appropriate = category_score < 0.8
            
            # Se non è appropriato, chiama l'API GPT per moderare
            if not is_appropriate:
                chat_response = client.chat.completions.create(
                    model="gpt-4o",  # Usa il modello più recente
                    messages=[
                        {"role": "system", "content": "Sei un sistema di moderazione che rende appropriato il contenuto. Modifica il testo solo se contiene:  volgarità, offese, contenuti espliciti, istigazione all'odio/violenza, disinformazione pericolosa. Mantieni al 100% invariato il testo se è già appropriato. Conserva significato e informazioni utili."},
                        {"role": "user", "content": testo}
                    ],
                    max_tokens=1000
                )
                moderated_text = chat_response.choices[0].message.content.strip()
            else:
                moderated_text = testo_originale
            
            # Salva in cache
            if use_cache:
                try:
                    with open(cache_file, "w") as f:
                        json.dump({
                            "is_appropriate": is_appropriate,
                            "score": category_score,
                            "category": category_name,
                            "moderated_text": moderated_text,
                            "timestamp": time.time()
                        }, f)
                except:
                    pass
            
            return is_appropriate, category_score, category_name, moderated_text
        
        # Non flaggato, tutto ok
        return True, 0.0, "", testo_originale
    
    except ImportError:
        # OpenAI non disponibile, prova con Anthropic
        try:
            import anthropic
            from anthropic import Anthropic
            
            # Verifica disponibilità delle API key
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                # Prova a prendere dalle secrets di Streamlit
                try:
                    api_key = st.secrets["ANTHROPIC_API_KEY"]
                except:
                    pass
            
            if not api_key:
                # Nessuna API key, ritorna risultato base
                return True, 0.0, "", testo_originale
            
            # Inizializza client
            client = Anthropic(api_key=api_key)
            
            # Usa Claude per valutare il contenuto
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Usa il modello più recente
                system="Sei un sistema di moderazione di contenuti che valuta se un testo rispetta le linee guida della community. Identifica linguaggio inappropriato, contenuti sensibili o problematici.",
                messages=[
                    {"role": "user", "content": f"Analizza questo testo e determina se è appropriato:\n\n{testo}\n\nRispondi in formato JSON con questi campi: is_appropriate (boolean), score (float 0-1), category (string), moderated_text (string con versione ripulita se necessario)."}
                ],
                max_tokens=1000
            )
            
            # Estrai il JSON dalla risposta
            result_text = response.content[0].text
            # Trova il JSON nella risposta
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(1))
            else:
                # Prova a trovare JSON senza markdown
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group(0))
                else:
                    # Fallback: non è stato possibile estrarre JSON
                    return True, 0.0, "", testo_originale
            
            # Salva in cache
            if use_cache:
                try:
                    with open(cache_file, "w") as f:
                        json.dump({
                            "is_appropriate": result_json.get("is_appropriate", True),
                            "score": result_json.get("score", 0.0),
                            "category": result_json.get("category", ""),
                            "moderated_text": result_json.get("moderated_text", testo_originale),
                            "timestamp": time.time()
                        }, f)
                except:
                    pass
            
            return (
                result_json.get("is_appropriate", True),
                result_json.get("score", 0.0),
                result_json.get("category", ""),
                result_json.get("moderated_text", testo_originale)
            )
        
        except ImportError:
            # Nessun servizio AI disponibile
            return True, 0.0, "", testo_originale
        except Exception as e:
            # Errore nell'uso di Anthropic
            print(f"Errore nella moderazione AI con Anthropic: {e}")
            return True, 0.0, "", testo_originale
    
    except Exception as e:
        # Errore nell'uso di OpenAI
        print(f"Errore nella moderazione AI con OpenAI: {e}")
        return True, 0.0, "", testo_originale

def integra_moderazione_contenuto(user_id, testo, livello_moderazione="standard", tipo_contenuto="messaggio"):
    """
    Funzione integrata che applica tutti i livelli di moderazione ad un singolo contenuto.
    Questo è un punto di ingresso unico per tutte le funzionalità di moderazione.
    
    Args:
        user_id (str): ID dell'utente
        testo (str): Testo da moderare
        livello_moderazione (str): Livello di moderazione ('leggero', 'standard', 'severo')
        tipo_contenuto (str): Tipo di contenuto ('messaggio', 'segnalazione')
        
    Returns:
        tuple: (testo_moderato, bloccato, messaggio, metadata)
            testo_moderato: testo dopo la moderazione
            bloccato: True se il contenuto è stato completamente bloccato
            messaggio: messaggio di spiegazione (errore o avviso)
            metadata: dizionario con metadati sulla moderazione
    """
    if not testo:
        return "", True, "Il contenuto è vuoto", {"moderated": False}
    
    # Risultati predefiniti
    is_moderated = False
    moderation_metadata = {
        "moderated": False,
        "moderation_type": None,
        "original_text": testo,
        "moderation_score": 0.0,
        "moderation_category": "",
        "is_spam": False,
        "is_duplicate": False,
        "is_rate_limited": False
    }
    
    # 1. Verifica permessi utente
    mapping_azioni = {
        "messaggio": "invia_messaggio",
        "segnalazione": "segnala_evento"
    }
    azione = mapping_azioni.get(tipo_contenuto, tipo_contenuto)
    
    is_allowed, reason = verifica_permesso_utente(user_id, azione)
    if not is_allowed:
        moderation_metadata["is_rate_limited"] = True
        return "", True, reason, moderation_metadata
    
    # 2. Verifica duplicati
    is_duplicate, dup_reason = detect_identical_content(user_id, testo, tipo_contenuto)
    if is_duplicate:
        moderation_metadata["is_duplicate"] = True
        return "", True, dup_reason, moderation_metadata
    
    # 3. Applica moderazione basata su regole
    testo_moderato, contiene_vietato, motivo = filtra_contenuto_vietato(testo, livello=livello_moderazione)
    
    # Se completamente bloccato
    if contiene_vietato and not testo_moderato:
        # Registra infrazione
        gravita = 5 if "spam" in motivo.lower() else 3
        traccia_comportamento_utente(user_id, f"{tipo_contenuto}_bloccato", gravita)
        
        moderation_metadata["moderated"] = True
        moderation_metadata["moderation_type"] = "regole"
        moderation_metadata["moderation_category"] = motivo
        
        return "", True, motivo, moderation_metadata
    
    # Se modificato ma non bloccato
    if testo_moderato != testo:
        is_moderated = True
        moderation_metadata["moderated"] = True
        moderation_metadata["moderation_type"] = "regole"
        moderation_metadata["moderation_category"] = "contenuto inappropriato"
    
    # 4. Applica moderazione AI (solo se non è già stato bloccato)
    if testo_moderato:
        is_appropriate, score, category, ai_moderated_text = modera_con_ai(
            testo_moderato, 
            user_id=user_id
        )
        
        moderation_metadata["moderation_score"] = score
        moderation_metadata["moderation_category"] = category
        
        # Se non è appropriato e punteggio alto
        if not is_appropriate and score > 0.7:
            # Casi estremi, blocca completamente
            if score > 0.9:
                # Registra infrazione grave
                traccia_comportamento_utente(user_id, f"{tipo_contenuto}_bloccato_ai", 8)
                
                moderation_metadata["moderated"] = True
                moderation_metadata["moderation_type"] = "ai"
                
                return "", True, f"Contenuto bloccato: {category}", moderation_metadata
            
            # Altrimenti usa versione moderata da AI
            testo_moderato = ai_moderated_text
            is_moderated = True
            
            # Registra infrazione moderata
            traccia_comportamento_utente(user_id, f"{tipo_contenuto}_moderato_ai", int(score * 5))
            
            moderation_metadata["moderated"] = True
            moderation_metadata["moderation_type"] = "ai"
    
    # Genera messaggio adatto
    messaggio = ""
    if is_moderated:
        if contiene_vietato:
            messaggio = motivo
        else:
            messaggio = "Il contenuto è stato moderato automaticamente."
    
    # Log finale dell'operazione
    logger.info(f"Moderazione completata per {user_id} - {tipo_contenuto}: " + 
               f"{'moderato' if is_moderated else 'passato'}")
    
    return testo_moderato, False, messaggio, moderation_metadata

def traccia_comportamento_utente(user_id, azione, gravita=0):
    """
    Tiene traccia del comportamento dell'utente per gestire moderazione basata su comportamento.
    Sistema avanzato con decadimento temporale per riabilitare utenti nel tempo.
    
    Args:
        user_id (str): ID univoco dell'utente
        azione (str): Tipo di azione (es. "messaggio_inappropriato", "spam", "segnalazione")
        gravita (int): Livello di gravità dell'infrazione (0-10)
    
    Returns:
        dict: Stato attuale dell'utente con livello di restrizione
    """
    if not user_id:
        return {"livello_restrizione": "nessuno"}
    
    # Directory per dati di moderazione
    mod_dir = "data/moderation"
    os.makedirs(mod_dir, exist_ok=True)
    
    # File utente
    user_file = f"{mod_dir}/{user_id}.json"
    
    # Dati utente
    user_data = {
        "user_id": user_id,
        "infractions": [],
        "total_score": 0,
        "restriction_level": "nessuno",
        "last_update": time.time()
    }
    
    # Carica dati esistenti se presenti
    if os.path.exists(user_file):
        try:
            with open(user_file, "r") as f:
                user_data = json.load(f)
        except:
            pass
    
    # Se è un'azione positiva, non modificare il punteggio
    if gravita <= 0:
        return user_data
    
    # Aggiungi nuova infrazione
    user_data["infractions"].append({
        "timestamp": time.time(),
        "action": azione,
        "gravity": gravita
    })
    
    # Decadimento temporale: infrazioni vecchie hanno meno peso
    total_score = 0
    now = time.time()
    recent_count = 0
    
    for infraction in user_data["infractions"]:
        # Calcola età in giorni
        age_days = (now - infraction.get("timestamp", now)) / 86400
        
        # Applicare decadimento (peso pieno se < 1 giorno, poi decade)
        decay_factor = max(0.1, min(1.0, 1.0 - (age_days * 0.1)))
        
        # Somma punteggio pesato
        score = infraction.get("gravity", 0) * decay_factor
        total_score += score
        
        # Conta infrazioni recenti (<24h)
        if age_days < 1:
            recent_count += 1
    
    # Aggiorna punteggio totale
    user_data["total_score"] = round(total_score, 2)
    user_data["recent_count"] = recent_count
    user_data["last_update"] = now
    
    # Determina livello di restrizione in base al punteggio
    if total_score > 50:
        user_data["restriction_level"] = "ban"
    elif total_score > 30:
        user_data["restriction_level"] = "limiti_severi"
    elif total_score > 15:
        user_data["restriction_level"] = "avvertimento"
    elif total_score > 5:
        user_data["restriction_level"] = "monitorato"
    else:
        user_data["restriction_level"] = "nessuno"
    
    # Salva dati aggiornati
    try:
        with open(user_file, "w") as f:
            json.dump(user_data, f, indent=2)
    except:
        pass
    
    return user_data

def check_rate_limiting(user_id, action_type):
    """
    Verifica se l'utente ha superato il rate limit per una determinata azione.
    Implementa protezione anti-flood.
    
    Args:
        user_id (str): ID dell'utente
        action_type (str): Tipo di azione (es. "messaggio", "segnalazione", "login")
        
    Returns:
        tuple: (allowed, reason)
    """
    if not user_id:
        return True, ""
    
    # Definizione limiti per tipo di azione
    limits = {
        "messaggio": {"window": 60, "max": 5},     # 5 messaggi in 60 secondi
        "segnalazione": {"window": 300, "max": 3}, # 3 segnalazioni in 5 minuti
        "login": {"window": 60, "max": 10},        # 10 tentativi in 60 secondi
        "default": {"window": 60, "max": 10}       # Limite standard per altre azioni
    }
    
    # Ottieni limiti per questa azione
    limit_config = limits.get(action_type, limits["default"])
    window_seconds = limit_config["window"]
    max_actions = limit_config["max"]
    
    # Directory per rate limiting
    rate_dir = "data/ratelimit"
    os.makedirs(rate_dir, exist_ok=True)
    
    # File per questo utente e questa azione
    rate_file = f"{rate_dir}/{user_id}_{action_type}.json"
    
    # Dati predefiniti
    rate_data = {
        "actions": [],
        "last_update": time.time()
    }
    
    # Carica dati esistenti se presenti
    if os.path.exists(rate_file):
        try:
            with open(rate_file, "r") as f:
                rate_data = json.load(f)
        except:
            # Se il file è corrotto, ricreiamo
            pass
    
    # Pulisci azioni vecchie
    now = time.time()
    rate_data["actions"] = [
        action for action in rate_data["actions"] 
        if now - action < window_seconds
    ]
    
    # Verifica se ha superato il limite
    if len(rate_data["actions"]) >= max_actions:
        wait_seconds = int(min(rate_data["actions"]) + window_seconds - now)
        logger.warning(f"Rate limit superato: {user_id} {action_type} - {len(rate_data['actions'])}/{max_actions}")
        return False, f"Hai superato il limite di azioni. Riprova tra {wait_seconds} secondi."
    
    # Aggiungi questa azione
    rate_data["actions"].append(now)
    rate_data["last_update"] = now
    
    # Salva i dati aggiornati
    try:
        with open(rate_file, "w") as f:
            json.dump(rate_data, f)
    except Exception as e:
        logger.error(f"Errore salvataggio rate limit: {e}")
    
    return True, ""

def detect_identical_content(user_id, content, content_type="messaggio"):
    """
    Rileva tentativi di postare contenuti identici o molto simili ripetutamente.
    
    Args:
        user_id (str): ID dell'utente
        content (str): Contenuto da verificare
        content_type (str): Tipo di contenuto ("messaggio" o "segnalazione")
        
    Returns:
        tuple: (is_duplicate, reason)
    """
    if not user_id or not content:
        return False, ""
    
    # Crea hash del contenuto
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Directory per tracciamento duplicati
    dup_dir = "data/duplicates"
    os.makedirs(dup_dir, exist_ok=True)
    
    # File per questo utente
    dup_file = f"{dup_dir}/{user_id}_{content_type}.json"
    
    # Dati predefiniti
    dup_data = {
        "recent_hashes": [],
        "last_update": time.time()
    }
    
    # Carica dati esistenti se presenti
    if os.path.exists(dup_file):
        try:
            with open(dup_file, "r") as f:
                dup_data = json.load(f)
        except:
            # Se il file è corrotto, ricreiamo
            pass
    
    # Pulisci hash vecchi (più di 1 ora)
    now = time.time()
    dup_data["recent_hashes"] = [
        item for item in dup_data["recent_hashes"] 
        if now - item["timestamp"] < 3600  # 1 ora
    ]
    
    # Verifica se è un duplicato
    for item in dup_data["recent_hashes"]:
        if item["hash"] == content_hash:
            logger.warning(f"Contenuto duplicato rilevato: {user_id} {content_type}")
            return True, "Hai già inviato questo stesso contenuto di recente."
    
    # Aggiungi questo hash
    dup_data["recent_hashes"].append({
        "hash": content_hash,
        "timestamp": now
    })
    dup_data["last_update"] = now
    
    # Limite numero hash memorizzati (per evitare crescita illimitata)
    if len(dup_data["recent_hashes"]) > 50:
        dup_data["recent_hashes"] = dup_data["recent_hashes"][-50:]
    
    # Salva i dati aggiornati
    try:
        with open(dup_file, "w") as f:
            json.dump(dup_data, f)
    except Exception as e:
        logger.error(f"Errore salvataggio duplicati: {e}")
    
    return False, ""

def verifica_permesso_utente(user_id, azione):
    """
    Verifica se un utente ha il permesso di eseguire un'azione.
    Sistema completo che integra:
    - Controllo restrizioni basate su comportamento
    - Rate limiting (anti-flood)
    - Prevenzione contenuti duplicati
    - Monitoraggio comportamentale
    
    Args:
        user_id (str): ID univoco dell'utente
        azione (str): Tipo di azione (es. "invia_messaggio", "segnala_evento")
    
    Returns:
        tuple: (permesso, messaggio)
    """
    if not user_id:
        return True, ""
    
    # Mappa le azioni ai tipi di rate limiting
    action_map = {
        "invia_messaggio": "messaggio",
        "segnala_evento": "segnalazione",
        "login": "login",
        "commento": "messaggio"
    }
    rate_action = action_map.get(azione, "default")
    
    # Controlla rate limiting
    is_allowed, reason = check_rate_limiting(user_id, rate_action)
    if not is_allowed:
        return False, reason
    
    # Directory per dati di moderazione
    mod_dir = "data/moderation"
    os.makedirs(mod_dir, exist_ok=True)
    user_file = f"{mod_dir}/{user_id}.json"
    
    # Se non esiste file utente, permesso concesso
    if not os.path.exists(user_file):
        return True, ""
    
    # Carica dati utente
    try:
        with open(user_file, "r") as f:
            user_data = json.load(f)
    except:
        return True, ""
    
    # Verifica restrizioni
    restriction = user_data.get("restriction_level", "nessuno")
    
    # Decadi le infrazioni vecchie
    if time.time() - user_data.get("last_update", 0) > 86400:
        # È passato più di un giorno, aggiorna il punteggio
        traccia_comportamento_utente(user_id, "refresh", 0)
        # Ricarica dati aggiornati
        try:
            with open(user_file, "r") as f:
                user_data = json.load(f)
            restriction = user_data.get("restriction_level", "nessuno")
        except:
            pass
    
    # Verifica limiti in base al livello di restrizione
    if restriction == "ban":
        logger.warning(f"Azione bloccata per utente bannato: {user_id} {azione}")
        return False, "Il tuo account è stato temporaneamente sospeso a causa di ripetute violazioni delle linee guida."
    
    if restriction == "limiti_severi":
        # Verifica se ha superato il limite di azioni per questa sessione
        recent_count = user_data.get("recent_count", 0)
        if recent_count > 5:
            logger.warning(f"Azione bloccata per utente con limiti severi: {user_id} {azione}")
            return False, "Hai raggiunto il limite di azioni permesse. Riprova più tardi."
        
        # Per utenti con limiti severi, applica rate limiting più stringente
        is_allowed, reason = check_rate_limiting(user_id, rate_action + "_restrizione")
        if not is_allowed:
            return False, reason
    
    if restriction == "avvertimento":
        return True, "Attenzione: alcuni tuoi contenuti recenti potrebbero violare le nostre linee guida."
    
    if restriction == "monitorato":
        # Nessun limite ma teniamo traccia
        logger.info(f"Utente monitorato: {user_id} esegue {azione}")
    
    # Registra questa azione per tracciamento comportamentale
    traccia_comportamento_utente(user_id, azione, 0)
    
    # Tutti gli altri casi
    return True, ""