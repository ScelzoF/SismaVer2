"""
meteoalarm_cache.py — Cache CONDIVISA MeteoAlarm per SismaVer2.

Questo modulo contiene l'UNICA funzione di fetch con cache.
Importato da home.py e rischi_allerte.py — garantisce che entrambe
le pagine mostrino SEMPRE lo stesso numero di allerte (stessa cache).
"""

import streamlit as st
import requests

_URLS = [
    "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-italy",
    "https://feeds.meteoalarm.org/api/v1/warnings/feeds-italy/",
]


@st.cache_data(ttl=120, show_spinner=False)
def fetch_meteoalarm_raw() -> bytes | None:
    """
    Fetch del feed Atom MeteoAlarm per l'Italia.
    Cache condivisa 2 minuti — usata da home.py e rischi_allerte.py.
    Chiamare questa funzione da ENTRAMBE le pagine garantisce coerenza.
    """
    for url in _URLS:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "SismaVer2/3.3"})
            if r.status_code == 200 and len(r.content) > 200:
                return r.content
        except Exception:
            pass
    return None
