"""
supabase_timeout.py
===================
Wrapper per eseguire operazioni Supabase con timeout esplicito.
Se il server non risponde entro SUPABASE_TIMEOUT secondi,
l'operazione viene abbandonata e viene restituito None.
"""

import concurrent.futures
import functools

SUPABASE_TIMEOUT = 2  # secondi — DNS morto fallisce subito


def run_with_timeout(fn, *args, timeout=SUPABASE_TIMEOUT, **kwargs):
    """
    Esegue fn(*args, **kwargs) in un thread separato.
    Restituisce (result, None) se completato nel tempo,
    oppure (None, "timeout") se scaduto.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(functools.partial(fn, *args, **kwargs))
        try:
            result = future.result(timeout=timeout)
            return result, None
        except concurrent.futures.TimeoutError:
            return None, "timeout"
        except Exception as e:
            return None, str(e)


def supabase_insert(client, table, data, timeout=SUPABASE_TIMEOUT):
    """Esegue un insert Supabase con timeout. Restituisce (response, error_str)."""
    def _insert():
        return client.table(table).insert(data).execute()
    return run_with_timeout(_insert, timeout=timeout)


def supabase_select(client, table, query_fn=None, timeout=SUPABASE_TIMEOUT):
    """
    Esegue una select Supabase con timeout.
    query_fn riceve client.table(table) e può aggiungere .select/.order/.limit
    Restituisce (response, error_str).
    """
    def _select():
        q = client.table(table)
        if query_fn:
            q = query_fn(q)
        return q.execute()
    return run_with_timeout(_select, timeout=timeout)


def create_client_safe(url, key, timeout=SUPABASE_TIMEOUT):
    """
    Crea un client Supabase con timeout sulla creazione.
    Restituisce (client, None) oppure (None, error_str).
    """
    try:
        from supabase import create_client
        result, err = run_with_timeout(create_client, url, key, timeout=timeout)
        return result, err
    except Exception as e:
        return None, str(e)
