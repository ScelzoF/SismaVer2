"""
keep_alive.py
=============
Modulo anti-ibernazione per SismaVer2.

Strategia a due livelli:
1. JavaScript lato browser: ping HTTP ogni 30s → impedisce il timeout WebSocket
   di Streamlit Community Cloud e mantiene il tab "attivo".
2. Thread background Python: ping Supabase ogni 25 minuti → impedisce la pausa
   del DB gratuito Supabase (che si addormenta dopo ~1 settimana di inattività).
"""

import streamlit as st
import threading
import time
import os


# ─── 1. JAVASCRIPT KEEP-ALIVE (lato browser) ──────────────────────────────────

KEEPALIVE_JS = """
<script>
(function() {
    // Evita di registrare più di un intervallo nella stessa scheda
    if (window._sismaver2KeepaliveActive) return;
    window._sismaver2KeepaliveActive = true;

    var PING_INTERVAL_MS = 30000; // 30 secondi

    function ping() {
        // Fa una richiesta GET al server Streamlit stesso
        // (bastano pochi byte di traffico per mantenere viva la sessione)
        fetch(window.location.href, {
            method: 'GET',
            cache: 'no-store',
            headers: { 'X-Keepalive': '1' }
        }).catch(function() {
            // Silenzioso in caso di errore di rete
        });
    }

    // Avvia subito, poi ogni 30s
    ping();
    setInterval(ping, PING_INTERVAL_MS);

    // Bonus: rileva se la tab torna in foreground dopo lungo periodo di
    // inattività e forza un ping immediato
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) { ping(); }
    });
})();
</script>
"""


def inject_keepalive_js():
    """
    Inietta nel DOM il JavaScript di keep-alive.
    Chiamare UNA SOLA VOLTA per sessione (viene gestito internamente).
    """
    if "keepalive_js_injected" not in st.session_state:
        st.markdown(KEEPALIVE_JS, unsafe_allow_html=True)
        st.session_state.keepalive_js_injected = True


# ─── 2. THREAD BACKGROUND: PING SUPABASE ──────────────────────────────────────

_supabase_ping_thread = None
_supabase_ping_lock = threading.Lock()


def _supabase_ping_loop(url: str, key: str, interval_sec: int = 1500):
    """
    Thread daemon che esegue una SELECT leggera su Supabase ogni `interval_sec`
    secondi (default 25 min) per prevenire la pausa del piano gratuito.
    """
    from supabase import create_client
    try:
        client = create_client(url, key)
    except Exception:
        return  # Se non riesce a connettersi, non fare nulla

    while True:
        try:
            # Query leggerissima: legge 1 sola riga da una tabella di sistema
            # Funziona anche se non esistono tabelle utente
            client.rpc("now").execute()
        except Exception:
            try:
                # Fallback: prova una select su una tabella qualsiasi
                client.table("chat_messages").select("id").limit(1).execute()
            except Exception:
                pass  # Ignora errori: meglio non bloccare
        time.sleep(interval_sec)


def start_supabase_keepalive(interval_sec: int = 1500):
    """
    Avvia (se non già attivo) il thread di ping Supabase.
    Legge SUPABASE_URL e SUPABASE_KEY dall'ambiente.
    Non fa nulla se le variabili non sono configurate.
    """
    global _supabase_ping_thread

    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

    if not url or not key:
        return  # Supabase non configurato, skip

    with _supabase_ping_lock:
        if _supabase_ping_thread is not None and _supabase_ping_thread.is_alive():
            return  # Thread già attivo

        _supabase_ping_thread = threading.Thread(
            target=_supabase_ping_loop,
            args=(url, key, interval_sec),
            daemon=True,
            name="supabase-keepalive"
        )
        _supabase_ping_thread.start()


# ─── 3. FUNZIONE PRINCIPALE (chiamare da app.py) ───────────────────────────────

def activate():
    """
    Attiva tutti i meccanismi anti-ibernazione.
    Chiamare all'inizio di app.py, prima del rendering del contenuto.
    """
    inject_keepalive_js()
    start_supabase_keepalive()
